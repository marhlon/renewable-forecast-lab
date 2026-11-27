"""M04: artefato candidato com vento e inferência com entradas sem alvo.

Destino: src/renewable_forecast/weather_artifact.py.
replay reproduz uma emissão histórica; fit salva; predict apenas recarrega.
Reusa a tabela e os parâmetros da ablação. Não promove o modelo a produção.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import platform
import subprocess
import sys

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from renewable_forecast.weather_ablation import HGB_PARAMS, load_model_frame
from renewable_forecast.weather_asof import utc_timestamp


RELEASE = "2026.10.01-artifact-1"
REQUEST_FIELDS = {
    "forecast_origin", "target_time", "history_end",
    "weather_latest_available_at", "id_ons_conjunto", "weather_model", "features",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def select_training_rows(frame: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    """1. Treinar requer rótulos disponíveis ANTES de começar a emissão."""
    eligible = (
        (frame["forecast_origin"] < origin)
        & (frame["target_available_at"] < origin)
    )
    train = frame.loc[eligible].copy()
    if train.empty:
        raise ValueError("Não há rótulos de treino disponíveis antes desta emissão.")
    return train


def make_request(frame: pd.DataFrame, source: dict, origin: pd.Timestamp) -> dict:
    """2. Exportar somente X e seus relógios. O alvo não entra no pedido."""
    selected = frame.loc[frame["forecast_origin"].eq(origin)]
    if len(selected) != 1:
        raise ValueError("A emissão deve existir uma única vez na tabela de entrada.")
    row = selected.iloc[0]
    request = {
        key: utc_timestamp(row[key]).isoformat()
        for key in ("forecast_origin", "target_time", "history_end", "weather_latest_available_at")
    }
    request.update({
        "id_ons_conjunto": str(row["id_ons_conjunto"]),
        "weather_model": str(row["weather_model"]),
        "features": {name: float(row[name]) for name in source["model_feature_columns"]},
    })
    return request


def read_manifest(model_dir: Path) -> dict:
    manifest = json.loads((model_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("release") != RELEASE:
        raise ValueError("Versão do contrato do artefato diferente da versão deste módulo.")
    if sha256(model_dir / "model.joblib") != manifest["model_sha256"]:
        raise ValueError("O modelo difere do hash registrado no manifesto.")
    if manifest["versions"]["sklearn"] != sklearn.__version__:
        raise ValueError("Recarregue o artefato na mesma versão de scikit-learn usada para treiná-lo.")
    return manifest


def fit_artifact(input_dir: Path, model_dir: Path, origin: pd.Timestamp, threads: int = 2) -> dict:
    frame, source = load_model_frame(input_dir)
    train = select_training_rows(frame, origin)
    columns = source["model_feature_columns"]
    signature = {
        "source_frame_sha256": sha256(input_dir / "model_frame.csv"),
        "source_metadata_sha256": sha256(input_dir / "metadata.json"),
        "training_cutoff": origin.isoformat(),
        "feature_columns": columns,
        "estimator_params": HGB_PARAMS,
        "code_sha256": sha256(Path(__file__)),
    }
    manifest_path = model_dir / "manifest.json"
    if manifest_path.exists():
        existing = read_manifest(model_dir)
        if any(existing.get(key) != value for key, value in signature.items()):
            raise ValueError("A pasta contém outro ajuste. Use uma saída própria para o novo corte.")
        print(f"Artefato compatível reutilizado: {model_dir.resolve()}", flush=True)
        return existing
    if (model_dir / "model.joblib").exists():
        raise ValueError("Existe um modelo sem manifesto nesta pasta; use uma nova pasta de saída.")

    print(f"Treino elegível: {len(train)}/{len(frame)}; excluídas: {len(frame) - len(train)}", flush=True)
    print(f"Último rótulo disponível: {train.target_available_at.max()}", flush=True)
    model = HistGradientBoostingRegressor(**HGB_PARAMS)
    with threadpool_limits(limits=threads):
        model.fit(train[columns], train["target_generation"])
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "model.joblib"
    joblib.dump(model, model_path, compress=3)
    manifest = {
        "release": RELEASE,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "candidate_historical_replay; not independent final evaluation",
        "model_promotion": False,
        **signature,
        "model_sha256": sha256(model_path),
        "training_rows": len(train),
        "excluded_rows": len(frame) - len(train),
        "train_origin_start": train.forecast_origin.min().isoformat(),
        "train_origin_end": train.forecast_origin.max().isoformat(),
        "latest_train_label_available_at": train.target_available_at.max().isoformat(),
        "training_rule": "forecast_origin < cutoff AND target_available_at < cutoff",
        "horizon_hours": source["horizon_hours"],
        "availability_delay_hours": source["availability_delay_hours"],
        "conjunto": source["conjunto"],
        "weather_model": str(frame.weather_model.iloc[0]),
        "prediction_floor": 0.0,
        "calibration": "none",
        "generation_timezone_hypothesis": source["generation_timezone_hypothesis"],
        "generation_timezone_verified": source["generation_timezone_verified"],
        "generation_interval_semantics": source["generation_interval_semantics"],
        "generation_availability_is_assumed": source["generation_availability_is_assumed"],
        "weather_availability_is_assumed": True,
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__},
    }
    write_json(manifest_path, manifest)
    print(f"Modelo salvo: {model_path.resolve()}", flush=True)
    return manifest

def validate_wind_geometry(features: dict) -> None:
    """Exige hypot(u_mean, v_mean) <= speed_mean + 1e-8, com chaves exatas."""
    if not isinstance(features, dict):
        raise ValueError("As features de vento devem estar em um dicionário.")
    names = ("wind_speed_mean_ms", "wind_u_mean_ms", "wind_v_mean_ms")
    values = []
    for name in names:
        if name not in features:
            raise ValueError(f"Feature de vento ausente: {name}")
        value = features[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Feature de vento não numérica ou não finita: {name}")
        try:
            number = float(value)
        except OverflowError as exc:
            raise ValueError(f"Feature de vento não finita: {name}") from exc
        if not np.isfinite(number):
            raise ValueError(f"Feature de vento não finita: {name}")
        values.append(number)
    speed, u, v = values

    if speed < 0:
        raise ValueError(f"A velocidade escalar média do vento (wind_speed_mean_ms) não pode ser negativa: {speed}")

    # hypot admite componentes negativas e evita quadrados intermediários grandes.
    vector_magnitude = float(np.hypot(u, v))
    if vector_magnitude - speed > 1e-8:
        raise ValueError(
            f"Inconsistência geométrica do vento: a intensidade vetorial média ({vector_magnitude:.4f} m/s) "
            f"não pode exceder a velocidade escalar média ({speed:.4f} m/s) em mais de 1e-8."
        )


def validate_request(request: dict, manifest: dict) -> pd.DataFrame:
    """3. Validar relógios e nomes; reconstruir X na ordem usada no treino."""
    if not isinstance(request, dict) or set(request) != REQUEST_FIELDS:
        raise ValueError("Pedido inválido: use somente os campos do contrato, sem target_generation.")
    features = request["features"]
    columns = manifest["feature_columns"]
    if not isinstance(features, dict) or set(features) != set(columns):
        raise ValueError("Features ausentes ou adicionais; o pedido deve conter exatamente as 32 entradas.")
    for name, value in features.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
            raise ValueError(f"Feature não numérica ou não finita: {name}")

    # Validação física e geométrica das variáveis de vento
    validate_wind_geometry(features)

    origin = utc_timestamp(request["forecast_origin"])
    target = utc_timestamp(request["target_time"])
    history_end = utc_timestamp(request["history_end"])
    weather_available = utc_timestamp(request["weather_latest_available_at"])
    if origin != origin.floor("h") or target != origin + pd.Timedelta(hours=manifest["horizon_hours"]):
        raise ValueError("O alvo deve corresponder ao horizonte do artefato e à emissão horária.")
    if history_end + pd.Timedelta(hours=manifest["availability_delay_hours"]) != origin:
        raise ValueError("O histórico não respeita o atraso de geração do artefato.")
    if weather_available > origin:
        raise ValueError("Meteorologia ainda indisponível na emissão.")
    if origin < utc_timestamp(manifest["training_cutoff"]):
        raise ValueError("Não use o artefato para prever antes do seu corte de treino.")
    if utc_timestamp(manifest["latest_train_label_available_at"]) >= origin:
        raise ValueError("Um rótulo de treino não estava disponível antes desta emissão.")
    if request["id_ons_conjunto"] != manifest["conjunto"] or request["weather_model"] != manifest["weather_model"]:
        raise ValueError("Conjunto ou modelo meteorológico difere do contrato de treino.")
    
    return pd.DataFrame([[float(features[name]) for name in columns]], columns=columns)


def predict_artifact(model_dir: Path, request_path: Path, output_path: Path, threads: int = 2) -> dict:
    manifest = read_manifest(model_dir)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    X = validate_request(request, manifest)
    # Carregamento de um artefato local produzido pelo próprio projeto.
    model = joblib.load(model_dir / "model.joblib")
    if list(model.feature_names_in_) != manifest["feature_columns"]:
        raise ValueError("As features do modelo diferem do manifesto.")
    with threadpool_limits(limits=threads):
        prediction = max(float(model.predict(X)[0]), manifest["prediction_floor"])
    if not np.isfinite(prediction):
        raise ValueError("O modelo produziu uma previsão não finita.")
    result = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": manifest["scope"], "model_promotion": False,
        **{key: request[key] for key in REQUEST_FIELDS - {"features"}},
        "horizon_hours": manifest["horizon_hours"],
        "availability_delay_hours": manifest["availability_delay_hours"],
        "prediction_mwmed": prediction,
        "persistence_prediction_mwmed": float(X["lag_1h"].iloc[0]),
        "feature_count": len(X.columns),
        "target_present_in_request": False,
        "model_retrained": False,
        "training_rows": manifest["training_rows"],
        "latest_train_label_available_at": manifest["latest_train_label_available_at"],
        "model_sha256": manifest["model_sha256"],
        "request_sha256": sha256(request_path),
        "generation_timezone_hypothesis": manifest["generation_timezone_hypothesis"],
        "generation_timezone_verified": manifest["generation_timezone_verified"],
        "generation_availability_is_assumed": manifest["generation_availability_is_assumed"],
        "weather_availability_is_assumed": manifest["weather_availability_is_assumed"],
    }
    write_json(output_path, result)
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
    print(f"Previsão salva: {output_path.resolve()}", flush=True)
    return result


def replay(input_dir: Path, origin: pd.Timestamp, output_dir: Path, threads: int = 2) -> None:
    frame, source = load_model_frame(input_dir)
    request = make_request(frame, source, origin)
    model_dir = output_dir / "model"
    manifest = fit_artifact(input_dir, model_dir, origin, threads)
    validate_request(request, manifest)
    request_path = output_dir / "request.json"
    prediction_path = output_dir / "prediction.json"
    write_json(request_path, request)
    print(f"Pedido sem alvo: {request_path.resolve()}", flush=True)
    print("Abrindo outro processo: apenas load + predict, sem fit.", flush=True)
    subprocess.run([
        sys.executable, "-u", "-m", "renewable_forecast.weather_artifact", "predict",
        "--model-dir", str(model_dir.resolve()), "--request", str(request_path.resolve()),
        "--output", str(prediction_path.resolve()), "--threads", str(threads),
    ], check=True)
    print("Reprodução histórica concluída. Alvo excluído do pedido; sem nova avaliação de desempenho.", flush=True)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"weather_artifact {RELEASE} | {Path(__file__).resolve()}")
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("fit", "replay"):
        p = modes.add_parser(mode)
        p.add_argument("--input-dir", type=Path, required=True)
        p.add_argument("--forecast-origin", required=True)
        p.add_argument("--model-dir" if mode == "fit" else "--output-dir", type=Path, required=True)
        p.add_argument("--threads", type=int, default=2)
    p = modes.add_parser("predict")
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--request", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.threads < 1:
        parser.error("threads deve ser positivo.")
    if args.mode == "fit":
        fit_artifact(args.input_dir, args.model_dir, utc_timestamp(args.forecast_origin), args.threads)
    elif args.mode == "replay":
        replay(args.input_dir, utc_timestamp(args.forecast_origin), args.output_dir, args.threads)
    else:
        predict_artifact(args.model_dir, args.request, args.output, args.threads)


if __name__ == "__main__":
    main()
