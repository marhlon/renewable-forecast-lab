"""Contraprovas pequenas de causalidade, quarentena e commit atômico."""
import numpy as np
import pandas as pd
import pytest

from renewable_forecast.bloco3_data import IncrementalStore, causal_gold, logical_hash, make_silver


def example():
    times = pd.date_range("2026-10-01", periods=40, freq="h")
    return pd.DataFrame({"id_ons": np.repeat(["a", "b"], 40), "din_instante": list(times)*2,
                         "val_geracao": np.r_[np.arange(40), 1000+np.arange(40)].astype(float),
                         "nom_usina": "test", "nom_tipousina": "EOL"})


def test_exact_lags_do_not_cross_series_or_fill_gaps():
    data, _ = make_silver(example())
    gold = causal_gold(data, ["a", "b"])
    a = gold.query("series_id == 'a'").iloc[30]
    b = gold.query("series_id == 'b'").iloc[30]
    assert a.lag2 == 28 and b.lag2 == 1028 and a.target == 31
    changed = data.copy()
    changed.loc[changed.series_id.eq("b"), "generation_mw"] = -999
    pd.testing.assert_frame_equal(gold.query("series_id == 'a'"), causal_gold(changed, ["a", "b"]).query("series_id == 'a'"))
    removed = data.loc[~(data.series_id.eq("a") & data.event_time.eq(pd.Timestamp("2026-10-02 04:00")))]
    assert np.isnan(causal_gold(removed, ["a", "b"]).query("series_id == 'a'").iloc[30].lag2)


def test_availability_and_future_mutation():
    data, _ = make_silver(example())
    data.loc[data.event_time.eq(pd.Timestamp("2026-10-02 04:00")), "available_at"] += pd.Timedelta(hours=3)
    gold = causal_gold(data, ["a"])
    assert np.isnan(gold.iloc[30].lag2)
    data.loc[data.event_time.ge(pd.Timestamp("2026-10-02 05:00")), "generation_mw"] = 999
    assert gold.iloc[30].lag24 == causal_gold(data, ["a"]).iloc[30].lag24
    assert gold.iloc[30].lag3 == causal_gold(data, ["a"]).iloc[30].lag3


def test_label_purge_is_strict_at_cutoff():
    data, _ = make_silver(example())
    gold = causal_gold(data, ["a"])
    cutoff = pd.Timestamp("2026-10-02")
    train = gold.label_available_at.lt(cutoff)
    assert gold.loc[train, "forecast_origin"].max() == pd.Timestamp("2026-10-01 20:00")
    assert not train.loc[21]  # origem 21h, label disponível exatamente à meia-noite


def test_quarantine_duplicate_invalid_negative_and_nonhour():
    raw = example().iloc[:6].copy()
    raw.loc[1, "id_ons"] = None
    raw.loc[2, "val_geracao"] = -1
    raw.loc[3, "val_geracao"] = np.inf
    raw.loc[4, "din_instante"] += pd.Timedelta(minutes=1)
    raw = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    clean, bad = make_silver(raw)
    assert len(clean) == 1 and len(bad) == 6
    assert bad.quarantine_reason.str.contains("duplicate_key").sum() == 2


def test_failed_commit_replay_and_conflicting_payload(tmp_path):
    data, _ = make_silver(example())
    store = IncrementalStore(tmp_path)
    store.apply("first", data.iloc[:40])
    old = logical_hash(store.table())
    with pytest.raises(RuntimeError):
        store.apply("second", data.iloc[40:], fail_before_commit=True)
    assert logical_hash(IncrementalStore(tmp_path).table()) == old
    store.apply("second", data.iloc[40:])
    assert logical_hash(store.table()) == logical_hash(data)
    assert store.apply("second", data.iloc[40:])["action"] == "replay_noop"
    invalid = data.iloc[[0]].copy()
    invalid["generation_mw"] += 3
    with pytest.raises(ValueError):
        store.apply("conflict", invalid)
