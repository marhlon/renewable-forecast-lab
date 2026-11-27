"""Bloco 3: contratos locais, consumo causal e transação incremental.

Não infere disponibilidade histórica: available_at é uma hipótese explícita.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA_VERSION = "bloco3-v1"
SOURCE_SHA256 = "55314b5a072a838d0ae4bd4543b940f1cfd3b7c78143f461a33aa05516e1617d"
FEATURES = ["lag2", "lag3", "lag24", "mean6", "hour_sin", "hour_cos", "series_code"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def logical_hash(frame: pd.DataFrame) -> str:
    """Conteúdo canônico, independente da codificação física do Parquet."""
    table = frame.copy()
    if len(table):
        table = table.sort_values(list(table.columns), kind="stable", na_position="last")
    raw = table.to_csv(index=False, lineterminator="\n", float_format="%.17g", date_format="%Y-%m-%dT%H:%M:%S.%f")
    return hashlib.sha256(raw.encode()).hexdigest()


def immutable_bronze(source: Path, destination: Path, expected_sha=SOURCE_SHA256) -> dict:
    digest = sha256(source)
    if digest != expected_sha:
        raise ValueError("A fonte não coincide com o snapshot declarado")
    target = destination / digest / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if sha256(target) != digest:
            raise ValueError("Bronze alterada: não sobrescrever")
        reused = True
    else:
        temporary = target.with_suffix(".pending")
        shutil.copyfile(source, temporary)
        if sha256(temporary) != digest:
            raise ValueError("Cópia bronze não conferida")
        os.replace(temporary, target)
        reused = False
    return {"path": str(target), "sha256": digest, "bytes": target.stat().st_size, "reused": reused}


def make_silver(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"id_ons", "din_instante", "val_geracao", "nom_tipousina", "nom_usina"}
    if required - set(raw):
        raise ValueError(f"Schema ausente: {sorted(required - set(raw))}")
    data = raw.copy().reset_index(drop=True)
    data["source_row"] = np.arange(len(data), dtype=np.int64)
    data["event_time"] = pd.to_datetime(data.din_instante, errors="coerce")
    data["series_id"] = data.id_ons.astype("string").str.strip()
    data["generation_mw"] = pd.to_numeric(data.val_geracao, errors="coerce")
    reason = pd.Series("", index=data.index, dtype="string")
    rules = {
        "missing_series": data.series_id.isna() | data.series_id.eq(""),
        "invalid_time": data.event_time.isna(),
        "not_hourly": data.event_time.notna() & data.event_time.ne(data.event_time.dt.floor("h")),
        "invalid_generation": ~np.isfinite(data.generation_mw),
        "negative_generation": data.generation_mw.lt(0),
        "duplicate_key": data.duplicated(["series_id", "event_time"], keep=False) & data.series_id.notna(),
    }
    for name, mask in rules.items():
        reason.loc[mask] = reason.loc[mask] + name + ";"
    data["quarantine_reason"] = reason
    data["available_at"] = data.event_time + pd.Timedelta(hours=2)
    clean = data.loc[reason.eq("")].sort_values(["series_id", "event_time"]).reset_index(drop=True)
    quarantine = data.loc[reason.ne("")].reset_index(drop=True)
    return clean, quarantine


def select_series(raw: pd.DataFrame) -> pd.DataFrame:
    """Seleção só por cadastro e timestamps, antes de olhar valores/previsões."""
    wind = raw.loc[raw.nom_tipousina.str.contains("EOL", na=False) & raw.id_ons.notna()]
    meta = wind.groupby("id_ons", sort=True).agg(rows=("din_instante", "size"), timestamps=("din_instante", "nunique"), name=("nom_usina", "first"))
    meta = meta.loc[(meta.rows == 744) & (meta.timestamps == 744)]
    meta = meta.loc[~meta.index.isin(["CJU_BA5EIGT", "CJUBA5EIGT"])]
    if len(meta) < 4:
        raise ValueError("Menos de quatro séries elegíveis por metadata")
    return meta.iloc[:4].reset_index().rename(columns={"id_ons": "series_id"})


def causal_gold(silver: pd.DataFrame, series: list[str]) -> pd.DataFrame:
    """Join exato por série/tempo, com disponibilidade de cada contribuição.

    Nunca usa shift por posição: lacunas não viram vizinhos temporais.
    O alvo só participa da avaliação/ajuste após sua disponibilidade.
    """
    outputs = []
    for code, sid in enumerate(series):
        data = silver.loc[silver.series_id.eq(sid)].set_index("event_time").sort_index()
        if data.index.has_duplicates:
            raise ValueError("Chave duplicada na silver")
        times = pd.date_range(data.index.min(), data.index.max(), freq="h")
        frame = pd.DataFrame({"series_id": sid, "forecast_origin": times})
        frame["series_code"] = code
        def observed(offset):
            event = times - pd.Timedelta(hours=offset)
            values = data.generation_mw.reindex(event).to_numpy()
            availability = data.available_at.reindex(event).to_numpy()
            valid = pd.notna(availability) & (availability <= times.to_numpy())
            return np.where(valid, values, np.nan)
        for k in [2, 3, 24]:
            frame[f"lag{k}"] = observed(k)
        history = np.column_stack([observed(k) for k in range(2, 8)])
        frame["mean6"] = np.mean(history, axis=1)  # requer as seis observações
        frame["hour_sin"] = np.sin(2*np.pi*times.hour/24)
        frame["hour_cos"] = np.cos(2*np.pi*times.hour/24)
        frame["target_time"] = times + pd.Timedelta(hours=1)
        frame["label_available_at"] = data.available_at.reindex(frame.target_time).to_numpy()
        frame["target"] = data.generation_mw.reindex(frame.target_time).to_numpy()
        outputs.append(frame)
    return pd.concat(outputs, ignore_index=True)


class IncrementalStore:
    """Commit por ponteiro atômico: estágio sem commit é ignorado no recovery.

    Payload idêntico permite replay. Conflito de mesma chave falha fechado.
    Não representa broker/distribuição/chegada real de produção.
    """
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.state_file = directory / "state.json"

    def state(self):
        if not self.state_file.exists():
            return {"version": 0, "batches": {}, "table": None}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def table(self):
        state = self.state()
        return pd.read_parquet(self.directory / state["table"]) if state["table"] else pd.DataFrame()

    def apply(self, batch_id: str, frame: pd.DataFrame, *, fail_before_commit=False) -> dict:
        state = self.state()
        digest = logical_hash(frame)
        if batch_id in state["batches"]:
            if state["batches"][batch_id] != digest:
                raise ValueError("Batch id reutilizado com conteúdo diferente")
            return {"action": "replay_noop", "version": state["version"], "rows": len(self.table())}
        old = self.table()
        combined = pd.concat([old, frame], ignore_index=True) if len(old) else frame.copy()
        unique = combined.drop_duplicates().copy()
        if unique.duplicated(["series_id", "event_time"]).any():
            raise ValueError("Conflito no upsert: chave repetida com payload distinto")
        unique = unique.sort_values(["series_id", "event_time"]).reset_index(drop=True)
        version = state["version"] + 1
        table_name = f"snapshot_{version:03d}_{logical_hash(unique)[:12]}.parquet"
        unique.to_parquet(self.directory / table_name, index=False)
        if fail_before_commit:
            raise RuntimeError("falha injetada após estágio e antes de commit")
        state.update(version=version, table=table_name)
        state["batches"][batch_id] = digest
        temp = self.state_file.with_suffix(".pending")
        write_json(temp, state)
        os.replace(temp, self.state_file)
        return {"action": "committed", "version": version, "rows": len(unique), "logical_hash": logical_hash(unique)}
