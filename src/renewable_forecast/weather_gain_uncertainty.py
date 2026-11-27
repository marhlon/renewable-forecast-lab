"""Incerteza exploratoria de previsoes salvas; nao treina modelos.

O ganho e abs(alvo - historico) - abs(alvo - historico_meteorologia).
Positivo favorece historia+meteorologia. Os deltas permanecem pareados por
emissao; blocos circulares nunca atravessam folds. Cada replica preserva o
tamanho de cada fold, e o agregado usa pesos n/soma(n).

Completa a fonte local truncada (M02-05, com assistencia Codex). A sequencia
original completa de E42/E47 nao foi recuperada; esta implementacao nao promete
reproduzir os intervalos historicos bit a bit. Nao transforma desenvolvimento
explorado em teste independente nem corrige selecao previa de modelos.

Referencia de metodo registrada no projeto:
https://bashtage.github.io/arch/bootstrap/generated/arch.bootstrap.CircularBlockBootstrap.html
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from numbers import Integral, Number
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = (
    "forecast_origin", "fold", "target_generation",
    "hgb_history", "hgb_history_weather",
)
VALUE_COLUMNS = ("target_generation", "hgb_history", "hgb_history_weather")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _integer(value: object, name: str, minimum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} deve ser inteiro, sem booleanos.")
    if value < minimum:
        raise ValueError(f"{name} deve ser >= {minimum}.")
    return int(value)


def _validate_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    """Valida tambem chamadas diretas a summarize; nao altera a entrada."""
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("As previsoes devem ser um DataFrame.")
    if frame.columns.duplicated().any():
        raise ValueError("Nomes de colunas duplicados sao ambiguos.")
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")
    if frame.empty or frame[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("As previsoes pareadas devem estar preenchidas.")
    result = frame.copy(deep=True)
    if any(isinstance(value, Number) for value in result["forecast_origin"]):
        raise ValueError("Emissoes numericas sem unidade temporal sao ambiguas.")
    try:
        result["forecast_origin"] = pd.to_datetime(
            result["forecast_origin"], utc=True, errors="raise", format="mixed"
        )
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError("As emissoes devem ser timestamps validos.") from error
    if result["forecast_origin"].isna().any():
        raise ValueError("As emissoes devem estar preenchidas.")
    if result["forecast_origin"].duplicated().any():
        raise ValueError("Ha emissoes duplicadas.")
    for column in VALUE_COLUMNS:
        if any(isinstance(value, (bool, np.bool_, complex)) for value in result[column]):
            raise ValueError("Alvos e previsoes devem ser numeros reais, sem booleanos.")
        try:
            result[column] = pd.to_numeric(result[column], errors="raise").astype(float)
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError("Alvos e previsoes devem ser numeros reais.") from error
    numeric = result[list(VALUE_COLUMNS)].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Alvos e previsoes devem ser finitos.")
    if any(isinstance(value, (bool, np.bool_, complex)) for value in result["fold"]):
        raise ValueError("Os folds devem ser inteiros positivos, sem booleanos.")
    try:
        folds = pd.to_numeric(result["fold"], errors="raise")
        if not np.isfinite(folds.to_numpy(dtype=float)).all():
            raise ValueError("Os folds devem ser finitos.")
        if not ((folds >= 1) & (folds % 1 == 0)).all():
            raise ValueError("Os folds devem ser inteiros positivos.")
        if (folds >= 2**63).any():
            raise ValueError("Os folds excedem o inteiro de 64 bits.")
        result["fold"] = folds.astype("int64")
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError("Os folds devem ser inteiros positivos de 64 bits.") from error
    result = result.sort_values("forecast_origin").reset_index(drop=True)
    if not result["fold"].is_monotonic_increasing:
        raise ValueError("Os folds devem formar blocos temporais ordenados.")
    for fold, part in result.groupby("fold", sort=True):
        if len(part) < 2 or not part["forecast_origin"].diff().iloc[1:].eq(
            pd.Timedelta(hours=1)
        ).all():
            raise ValueError(f"Fold {fold}: exige emissoes horarias sem lacunas.")
    delta = (
        (result["target_generation"] - result["hgb_history"]).abs()
        - (result["target_generation"] - result["hgb_history_weather"]).abs()
    )
    # Subtrair numeros finitos extremos ainda pode gerar overflow.
    if not np.isfinite(delta.to_numpy(dtype=float)).all():
        raise ValueError("Os deltas de erro devem ser finitos.")
    if "delta_absolute_error" in result:
        try:
            saved_delta = pd.to_numeric(result["delta_absolute_error"], errors="raise")
            delta_valid = np.isfinite(saved_delta.to_numpy(dtype=float)).all()
            delta_valid = delta_valid and np.allclose(
                delta, saved_delta, rtol=1e-10, atol=1e-10
            )
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError("O delta gravado deve ser numerico e finito.") from error
        if not delta_valid:
            raise ValueError("O delta gravado diverge das previsoes pareadas.")
    result["delta_absolute_error"] = delta
    return result


def load_predictions(path: Path) -> pd.DataFrame:
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream), [])
    if len(header) != len(set(header)):
        raise ValueError("O CSV tem nomes de colunas duplicados.")
    return _validate_predictions(pd.read_csv(path, encoding="utf-8-sig"))


def circular_means(
    values: np.ndarray, block_hours: int, repetitions: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Reamostra um unico fold, retornando n valores por replica.

    Exemplo: n=5, bloco=2, inicios [4, 1, 3] produzem indices
    [4, 0, 1, 2, 3]; o sexto indice e descartado. O retorno ao inicio
    pertence sempre ao mesmo vetor/fold, nunca ao fold vizinho.
    """
    values = np.asarray(values)
    if values.ndim != 1 or values.size < 2 or values.dtype.kind not in "iuf":
        raise ValueError("values deve ser vetor real com pelo menos dois elementos.")
    values = values.astype(float, copy=False)
    if not np.isfinite(values).all():
        raise ValueError("values deve conter somente numeros finitos.")
    block_hours = _integer(block_hours, "block_hours", 1)
    repetitions = _integer(repetitions, "repetitions", 1)
    if block_hours >= values.size:
        raise ValueError("block_hours deve ser menor que o tamanho do fold.")
    if not isinstance(rng, np.random.Generator):
        raise ValueError("rng deve ser um numpy.random.Generator local.")
    n = values.size
    blocks = (n + block_hours - 1) // block_hours
    means = np.empty(repetitions, dtype=float)
    # Limita os indices temporarios; o tamanho dos lotes nao muda os sorteios.
    batch_size = max(1, min(256, 1_000_000 // (blocks * block_hours)))
    for first in range(0, repetitions, batch_size):
        last = min(first + batch_size, repetitions)
        starts = rng.integers(0, n, size=(last - first, blocks))
        indices = (starts[:, :, None] + np.arange(block_hours)) % n
        indices = indices.reshape(last - first, -1)[:, :n]
        with np.errstate(over="ignore", invalid="ignore"):
            means[first:last] = values[indices].mean(axis=1)
    if not np.isfinite(means).all():
        raise ValueError("A media reamostrada nao e finita; valores excedem a faixa numerica.")
    return means


def summarize(
    frame: pd.DataFrame, *, block_hours: list[int], repetitions: int, seed: int
) -> pd.DataFrame:
    """Estima ganho e IC percentil nominal95% por fold e agregado ponderado.

    Cada (seed, comprimento de bloco, fold) define um fluxo local de sorteios.
    Assim, reordenar os blocos pedidos nao muda o resultado de cada bloco.
    A fracao bootstrap <=0 e descritiva: nao e p-valor de teste de hipotese.
    """
    repetitions = _integer(repetitions, "repetitions", 1000)
    seed = _integer(seed, "seed", 0)
    if isinstance(block_hours, (str, bytes)):
        raise ValueError("block_hours deve ser uma sequencia de inteiros.")
    try:
        lengths = [_integer(value, "block_hours", 1) for value in block_hours]
    except TypeError as error:
        raise ValueError("block_hours deve ser uma sequencia de inteiros.") from error
    if not lengths or len(set(lengths)) != len(lengths):
        raise ValueError("Informe comprimentos de bloco distintos e nao vazios.")
    validated = _validate_predictions(frame)
    groups = list(validated.groupby("fold", sort=True))
    smallest = min(len(part) for _, part in groups)
    if any(value >= smallest for value in lengths):
        raise ValueError("Cada bloco deve ter entre 1 e n-1 horas do menor fold.")
    total = len(validated)
    rows = []

    def row(part, replicas, length, fold):
        low, high = np.quantile(replicas, [0.025, 0.975], method="linear")
        return {
            "scope": "aggregate" if fold is None else "fold",
            "fold": fold,
            "block_hours": length,
            "n": len(part),
            "mae_history_mwmed": float(
                (part["target_generation"] - part["hgb_history"]).abs().mean()
            ),
            "mae_history_weather_mwmed": float(
                (part["target_generation"] - part["hgb_history_weather"]).abs().mean()
            ),
            "mean_gain_mwmed": float(part["delta_absolute_error"].mean()),
            "bootstrap_mean_gain_mwmed": float(replicas.mean()),
            "ci95_low_mwmed": float(low),
            "ci95_high_mwmed": float(high),
            "bootstrap_fraction_nonpositive": float(np.mean(replicas <= 0)),
            "confidence_level": 0.95,
            "repetitions": repetitions,
            "seed": seed,
        }

    for length in lengths:
        aggregate_replicas = np.zeros(repetitions, dtype=float)
        for fold, part in groups:
            rng = np.random.default_rng(np.random.SeedSequence([seed, length, int(fold)]))
            replicas = circular_means(
                part["delta_absolute_error"].to_numpy(dtype=float),
                length, repetitions, rng,
            )
            rows.append(row(part, replicas, length, int(fold)))
            aggregate_replicas += replicas * (len(part) / total)
        rows.append(row(validated, aggregate_replicas, length, None))
    result = pd.DataFrame(rows)
    result["fold"] = result["fold"].astype("Int64")
    estimates = [
        "mae_history_mwmed", "mae_history_weather_mwmed", "mean_gain_mwmed",
        "bootstrap_mean_gain_mwmed", "ci95_low_mwmed", "ci95_high_mwmed",
    ]
    if not np.isfinite(result[estimates].to_numpy(dtype=float)).all():
        raise ValueError("As estimativas nao sao finitas; valores excedem a faixa numerica.")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True, help="CSV de previsoes pareadas.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Pasta para summary.csv e receipt.json novos.")
    parser.add_argument("--block-hours", type=int, nargs="+", default=[6, 24, 48])
    parser.add_argument("--repetitions", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args_list = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(args_list)
    started = datetime.now(timezone.utc).isoformat()
    timer = perf_counter()
    try:
        source = args.predictions.resolve(strict=True)
        output_dir = args.output_dir.resolve()
        csv_path, receipt_path = output_dir / "summary.csv", output_dir / "receipt.json"
        if csv_path.exists() or receipt_path.exists():
            raise ValueError("A saida ja existe; escolha uma nova pasta para preservar o recibo.")
        before = sha256(source)
        frame = load_predictions(source)
        summary = summarize(
            frame, block_hours=args.block_hours, repetitions=args.repetitions, seed=args.seed
        )
        if sha256(source) != before:
            raise ValueError("O arquivo de entrada mudou durante a execucao.")
        output_dir.mkdir(parents=True, exist_ok=True)
        with csv_path.open("x", encoding="utf-8", newline="") as stream:
            summary.to_csv(stream, index=False, float_format="%.17g")
        receipt = {
            "schema": "renewcast-weather-gain-bootstrap-result-v1",
            "completed": True,
            "exit_code": 0,
            "started_at_utc": started,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": perf_counter() - timer,
            "command": [sys.executable, "-m", "renewable_forecast.weather_gain_uncertainty", *args_list],
            "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "platform": platform.platform()},
            "input": {"path": str(source), "bytes": source.stat().st_size, "sha256": before, "preserved": True},
            "code": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__))},
            "parameters": {"block_hours": args.block_hours, "repetitions": args.repetitions, "seed": args.seed, "confidence_level": 0.95},
            "method": "paired circular block bootstrap, stratified by fold, weighted by fold n; percentile interval, linear quantiles",
            "rng_stream": "numpy SeedSequence([seed, block_hours, fold]); independent local generators",
            "gain_definition": "abs(target_generation-hgb_history) - abs(target_generation-hgb_history_weather), MWmed",
            "rows_input": len(frame),
            "fold_counts": {str(int(fold)): len(part) for fold, part in frame.groupby("fold", sort=True)},
            "forecast_origin_start": frame["forecast_origin"].min().isoformat(),
            "forecast_origin_end": frame["forecast_origin"].max().isoformat(),
            "rows_summary": len(summary),
            "output_sha256": {"summary.csv": sha256(csv_path)},
            "models_trained": False,
            "models_refitted": False,
            "independent_holdout_certified": False,
            "physical_timezone_verified": False,
            "scope": "Conditional exploratory uncertainty on supplied saved predictions and fixed folds; selection and future generalization are not corrected.",
            "timestamp_interpretation": "Timestamps parsed as UTC; naive timestamps are assumed UTC, without verification of their physical meaning.",
            "nonpositive_fraction_is_p_value": False,
        }
        with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        print(f"Resumo: {csv_path}\nRecibo: {receipt_path}")
        return 0
    except (ValueError, TypeError, OSError, UnicodeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

