"""M10.3: regra causal e avaliação por início de alarme em grade regular."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

CHANNELS = ("channel_50", "channel_51", "channel_52")
NS_PER_MINUTE = 60 * 10**9


def iniciar_alarmes(escores, utilizavel, *, limiar, consecutivos):
    """True só no primeiro instante que confirma cada sequência utilizável."""
    scores = np.asarray(escores, dtype=float)
    valid = np.asarray(utilizavel)
    if scores.ndim != 1 or valid.shape != scores.shape or valid.dtype != bool:
        raise ValueError("Esperados vetores 1D: escore numérico e utilizavel booleano.")
    if (isinstance(consecutivos, (bool, np.bool_)) or not isinstance(consecutivos, (int, np.integer))
            or consecutivos < 1):
        raise ValueError("consecutivos deve ser um inteiro positivo.")
    if not np.isfinite(limiar) or not np.isfinite(scores[valid]).all():
        raise ValueError("O limiar e os escores utilizáveis devem ser finitos.")
    high = valid & (scores >= limiar)
    i = np.arange(len(high))
    last_reset = np.maximum.accumulate(np.where(high, -1, i))
    return high & (i - last_reset == consecutivos)


def conferir_autoria(func):
    """Testa confirmação, reset, igualdade, prefixo e sequência de comprimento 1."""
    score = np.array([.8, .8, .9, np.nan, .9, .8, .1, .9, np.nan, .9, .9])
    valid = np.isfinite(score)
    for a in (score, valid):
        a.setflags(write=False)
    ideal = np.zeros(len(score), dtype=bool)
    ideal[[1, 5, 10]] = True
    got = conferir_saida(func, score, valid, .8, 2)
    np.testing.assert_array_equal(got, ideal, err_msg="Fixture: confirme no segundo ponto, sem antecipar nem repetir.")
    np.testing.assert_array_equal(conferir_saida(func, score[:9], valid[:9], .8, 2), got[:9],
                                  err_msg="O mesmo prefixo deve produzir as mesmas decisões.")
    across = np.asarray([True, True, False, True, True])
    np.testing.assert_array_equal(
        conferir_saida(func, np.ones(5), across, 1., 1),
        [True, False, False, True, False],
        err_msg="Com 1 leitura, dispare na primeira da sequência; respeite utilizavel mesmo com escore finito.",
    )


def conferir_saida(func, scores, valid, threshold, k):
    args = [a.view() for a in (scores, valid)]
    for a in args:
        a.setflags(write=False)
    got = np.asarray(func(*args, limiar=threshold, consecutivos=k))
    if got.dtype != bool or got.shape != valid.shape:
        raise ValueError("A função deve devolver um vetor booleano com uma posição por instante.")
    return got


def utc_index(values):
    return pd.DatetimeIndex(pd.to_datetime(values, format="ISO8601", utc=True)).astype("datetime64[ns, UTC]")


@dataclass(frozen=True)
class Intervalo:
    channel: str
    start_ns: int
    end_ns: int
    left: int
    right: int

    def contains(self, i):
        return self.left <= i < self.right


class Avaliador:
    """Prepara a união de intervalos por ID; nunca entrega rótulos à regra de alarme."""

    def __init__(self, timestamps, valid, events, *, step_seconds):
        self.t = utc_index(timestamps)
        self.ns = self.t.asi8
        self.valid = np.asarray(valid, dtype=bool)
        if (not len(self.t) or self.valid.shape != (len(self.t),) or self.t.hasnans
                or not np.all(np.diff(self.ns) == step_seconds * 10**9)):
            raise ValueError("Preserve a grade inteira e ordenada; não descarte linhas de lacuna.")
        self.step_seconds = step_seconds
        self.ignore = np.zeros(len(self.t), dtype=bool)
        self.anomaly = np.zeros(len(self.t), dtype=bool)
        self.intervals = {}
        cats = {"Anomaly", "Rare Event", "Communication Gap"}
        if (events[["ID", "Channel", "Category", "StartTime", "EndTime"]].isna().any().any()
                or not set(events.Channel).issubset(CHANNELS)
                or not set(events.Category).issubset(cats)
                or events.groupby("ID").Category.nunique().gt(1).any()):
            raise ValueError("Anotações inconsistentes no período.")
        starts, ends = utc_index(events.StartTime), utc_index(events.EndTime)
        if starts.hasnans or ends.hasnans or (starts > ends).any():
            raise ValueError("Intervalo de anotação inválido.")
        left = np.searchsorted(self.ns, starts.asi8, side="left")
        right = np.searchsorted(self.ns, ends.asi8, side="right")
        for pos, row in enumerate(events.itertuples(index=False)):
            span = Intervalo(row.Channel, starts[pos].value, ends[pos].value, int(left[pos]), int(right[pos]))
            if row.Category == "Anomaly":
                self.intervals.setdefault(str(row.ID), []).append(span)
                self.anomaly[span.left:span.right] = True
            else:
                self.ignore[span.left:span.right] = True

        self.eligible = self.valid & ~self.ignore
        self.nominal = self.eligible & ~self.anomaly
        self.nominal_days = float(self.nominal.sum() * step_seconds / 86400)
        self.observable = {eid: any(self.eligible[s.left:s.right].any() for s in spans)
                           for eid, spans in self.intervals.items()}
        self.first_annotation = {eid: min(s.start_ns for s in spans) for eid, spans in self.intervals.items()}

    def avaliar(self, starts, *, details=False):
        starts = np.asarray(starts)
        if starts.shape != self.valid.shape or starts.dtype != bool or (starts & ~self.valid).any():
            raise ValueError("Inícios de alarme fora do contrato da grade.")
        first = {}
        counts = {"atribuido": 0, "repetido_no_evento": 0, "sem_anotacao": 0, "ignorado_categoria": 0}
        alarms = []
        for i in np.flatnonzero(starts):
            eid = None
            if self.ignore[i]:
                status = "ignorado_categoria"
            elif not self.anomaly[i]:
                status = "sem_anotacao"
            else:
                matches = [(s.end_ns, key) for key, spans in self.intervals.items()
                           if key not in first for s in spans if s.contains(i)]
                if matches:
                    _, eid = min(matches)
                    first[eid] = int(i)
                    status = "atribuido"
                else:
                    status = "repetido_no_evento"
            counts[status] += 1
            if details:
                alarms.append({"instante_utc": self.t[i].isoformat(), "classe": status, "id_atribuido": eid})
        delays = {eid: (int(self.ns[i]) - self.first_annotation[eid]) / NS_PER_MINUTE for eid, i in first.items()}
        observed = sum(self.observable.values())
        n = len(self.intervals)
        audited_starts = int(starts.sum()) - counts["ignorado_categoria"]
        summary = {
            "instantes_na_grade": len(self.t), "instantes_utilizaveis": int(self.valid.sum()),
            "ids_anomalia": n, "ids_observaveis": observed,
            "ids_nao_observaveis": n - observed, "ids_detectados": len(first),
            "recall_observaveis": len(first) / observed if observed else None,
            "recall_todos_ids": len(first) / n if n else None,
            "precisao_por_inicio_avaliavel": len(first) / audited_starts if audited_starts else None,
            "alarmes_total": int(starts.sum()), "alarmes_atribuidos": counts["atribuido"],
            "alarmes_repetidos_no_evento": counts["repetido_no_evento"],
            "alarmes_sem_anotacao": counts["sem_anotacao"],
            "alarmes_ignorados_categoria": counts["ignorado_categoria"],
            "exposicao_sem_anotacao_dias_equivalentes": self.nominal_days,
            "taxa_sem_anotacao_por_dia": counts["sem_anotacao"] / self.nominal_days if self.nominal_days else None,
            "atraso_mediano_min": float(np.median(list(delays.values()))) if delays else None,
            "atraso_p90_min": float(np.quantile(list(delays.values()), .9)) if delays else None,
        }
        if not details:
            return summary
        events = []
        for eid, spans in sorted(self.intervals.items()):
            state = "detectado" if eid in first else ("perdido" if self.observable[eid] else "nao_observavel")
            events.append({"id": eid, "estado": state, "inicio_anotado_utc": pd.Timestamp(
                self.first_annotation[eid], unit="ns", tz="UTC").isoformat(),
                "primeiro_alarme_utc": self.t[first[eid]].isoformat() if eid in first else None,
                "atraso_min": delays.get(eid), "anotacoes_canal_intervalo": len(spans)})
        channels = []
        for channel in CHANNELS:
            per_id = {eid: [s for s in spans if s.channel == channel]
                      for eid, spans in self.intervals.items() if any(s.channel == channel for s in spans)}
            seen = {eid for eid, spans in per_id.items()
                    if any(self.eligible[s.left:s.right].any() for s in spans)}
            hits = {eid for eid in seen if eid in first and any(s.contains(first[eid]) for s in per_id[eid])}
            channels.append({"canal_anotado": channel, "ids_anotados": len(per_id),
                             "ids_observaveis": len(seen), "ids_primeiro_alarme_no_intervalo": len(hits),
                             "fracao_entre_observaveis": len(hits) / len(seen) if seen else None})
        return summary, events, alarms, channels
