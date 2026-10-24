"""Incerteza exploratoria do ganho pareado, com blocos dentro de cada fold.

Nao refaz treino nem transforma o desenvolvimento em teste final independente.
Implementacao NumPy do bootstrap circular: blocos de tamanho fixo, com retorno
do fim ao inicio do MESMO fold. Referencia de metodo:
https://bashtage.github.io/arch/bootstrap/generated/arch.bootstrap.CircularBlockBootstrap.html
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_predictions(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = [
        "forecast_origin", "fold", "target_generation",
        "hgb_history", "hgb_history_weather",
    ]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")
    if frame.empty or frame[required].isna().any().any():
        raise ValueError("As previsoes pareadas devem estar preenchidas.")
    frame["forecast_origin"] = pd.to_datetime(
        frame["forecast_origin"], utc=True, errors="raise"
    )
    if frame["forecast_origin"].duplicated().any():
        raise ValueError("Ha emissoes duplicadas.")
    numeric = frame[["target_generation", "hgb_history", "hgb_history_weather"]]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Alvos e previsoes devem ser finitos.")
    folds = pd.to_numeric(frame["fold"], errors="raise")
    if not ((folds >= 1) & (folds % 1 == 0)).all():
        raise ValueError("Os folds devem ser inteiros positivos.")
    frame["fold"] = folds.astype(int)
    frame = frame.sort_values("forecast_origin").reset_index(drop=True)
    if not frame["fold"].is_monotonic_increasing:
        raise ValueError("Os folds devem formar blocos temporais ordenados.")
    for fold, part in frame.groupby("fold", sort=True):
        if len(part) < 2 or not part["forecast_origin"].diff().iloc[1:].eq(
            pd.Timedelta(hours=1)
        ).all():
            raise ValueError(f"Fold {fold}: exige emissoes horarias sem lacunas.")
    delta = (
        (frame["target_generation"] - frame["hgb_history"]).abs()
        - (frame["target_generation"] - frame["hgb_history_weather"]).abs()
    )
    if "delta_absolute_error" in frame and not np.allclose(
        delta, frame["delta_absolute_error"], rtol=1e-10, atol=1e-10
    ):
        raise ValueError("O delta gravado diverge das previsoes pareadas.")
    frame["delta_absolute_error"] = delta
    return frame


def circular_means(
    values: np.ndarray, block_hours: int, repetitions: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Reamostra blocos consecutivos, preservando n observacoes por replica."""
    n = len(values)
    blocks = (n + block_hours - 1) // block_hours
    means = np.empty(repetitions, dtype=float)
    # Lotes limitam memoria; nao alteram a sequencia de sorteios.
    for first in range(0, repetitions, 256):
        last = min(first + 256, repetitions)
        starts = rng.integers(0, n, size=(last - first, blocks))
        indices = (starts[:, :, None] + np.arange(block_hours)) % n
        indices = indices.reshape(last - first, -1)[:, :n]
        means[first:last] = values[indices].mean(axis=1)
    return means


def summarize(
    frame: pd.DataFrame, *, block_hours: list[int], repetitions: int, seed: int
) -> pd.DataFrame:
    groups = list(frame.groupby("fold", sort=True))
    if repetitions < 1000 or seed < 0:
        raise ValueError("Use pelo menos 1000 replicas e semente nao negativa.")
    smallest = min(len(part) for _, part in groups)
    if not block_hours or any(b < 1 or b >= smallest for b in block_hours):
        raise ValueError("Cada bloco deve ter entre 1 e n-1 horas do menor fold.")
    rows = []

