"""Seleciona quantis no instante do alvo, a partir do fim de cada histórico."""

from datetime import datetime

import numpy as np


def _timestamps_sem_fuso(values, batch, name):
    raw = np.asarray(values)
    if raw.shape != (batch,):
        raise ValueError(f"{name} deve ter um timestamp por exemplo.")
    if raw.dtype.kind not in ("M", "O", "U"):
        raise ValueError(f"{name} deve conter timestamps, não valores numéricos.")
    if raw.dtype.kind != "M":
        for value in raw:
            if isinstance(value, (str, np.str_)):
                try:
                    value = datetime.fromisoformat(str(value))
                except ValueError as error:
                    raise ValueError(f"Timestamp inválido em {name}.") from error
            if getattr(value, "tzinfo", None) is not None and value.utcoffset() is not None:
                raise ValueError("Os timestamps devem permanecer no mesmo eixo sem fuso.")
    try:
        result = np.asarray(raw, dtype="datetime64[ns]")
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"Timestamps inválidos em {name}.") from error
    if np.isnat(result).any():
        raise ValueError(f"{name} não pode conter NaT.")
    return result


def alinhar_quantis(forecast, quantile_levels, history_end, target_times):
    """Forecast [B,Q,P] para lead, índice e P10/P50/P90 [B], sem mutações."""
    forecast = np.asarray(forecast, dtype=np.float64)
    levels = np.asarray(quantile_levels, dtype=np.float64)
    if forecast.ndim != 3 or min(forecast.shape) <= 0:
        raise ValueError("forecast deve ter shape [B,Q,P], com dimensões positivas.")
    batch, quantiles, steps = forecast.shape
    if levels.shape != (quantiles,):
        raise ValueError("quantile_levels deve ter um nível por coluna do eixo Q.")
    if not np.isfinite(forecast).all() or not np.isfinite(levels).all():
        raise ValueError("Previsões e níveis devem ser finitos.")
    if ((levels <= 0) | (levels >= 1)).any() or (np.diff(levels) <= 0).any():
        raise ValueError("Os níveis devem ser distintos, crescentes e estar em (0,1).")

    ends = _timestamps_sem_fuso(history_end, batch, "history_end")
    targets = _timestamps_sem_fuso(target_times, batch, "target_times")
    ns_per_hour = 3_600_000_000_000
    leads = []
    # Inteiros Python evitam overflow ao subtrair dois timestamps em nanossegundos.
    for end, target in zip(ends.astype(np.int64), targets.astype(np.int64)):
        difference = int(target) - int(end)
        if difference <= 0 or difference % ns_per_hour:
            raise ValueError("O alvo deve estar horas inteiras depois do fim do histórico.")
        leads.append(difference // ns_per_hour)
    lead_hours = np.asarray(leads, dtype=np.int64)
    # O índice zero representa history_end + 1h, e não o próprio history_end.
    index_zero_based = lead_hours - 1
    if (index_zero_based >= steps).any():
        raise ValueError("A trajetória prevista não alcança todos os alvos.")

    result = {"lead_hours": lead_hours, "index_zero_based": index_zero_based}
    rows = np.arange(batch)
    for name, level in (("p10", 0.1), ("p50", 0.5), ("p90", 0.9)):
        matches = np.flatnonzero(np.isclose(levels, level, rtol=0, atol=1e-12))
        if len(matches) != 1:
            raise ValueError(f"O nível {level} deve aparecer uma única vez.")
        result[name] = forecast[rows, int(matches[0]), index_zero_based]
    return result
