"""M06: persistência e inferência do classificador h24 de eventos.

CLI: python -m renewable_forecast.event_artifact --help
O ajuste ocorre nesta CLI. EventRuntime carrega uma vez e somente prevê.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

import joblib
import numpy as np
import pandas as pd
import sklearn
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits


RELEASE = "2026.10.04-event-artifact-1"
FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]


class EventPredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conjunto: Literal["CJU_BA5EIGT"]
    forecast_origin: AwareDatetime
    history_end: AwareDatetime
    target_time: AwareDatetime
    weather_latest_available_at: AwareDatetime
    weather_model: str = Field(min_length=1)
    features: dict[str, FiniteNumber]


class EventPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["development_inference"]
    model_id: str
    model_sha256: str
    manifest_sha256: str
    policy_id: str
    policy_sha256: str
    method: Literal["hgb_weather_classifier"]
    forecast_origin: AwareDatetime
    target_time: AwareDatetime
    history_end: AwareDatetime
    weather_latest_available_at: AwareDatetime
    drop_threshold_mwmed: float
    last_available_generation: float
    event_generation_at_or_below_mwmed: float
    p_event: Probability
    threshold: Probability
    alarm: bool
    feature_count: int
    estimator_executed: Literal[True]
    model_retrained: Literal[False]
    capacity_enforced_at_runtime: Literal[False]
    availability_is_assumed: Literal[True]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def canonical_hash(value) -> str:
    """Identidade lógica: ordem das chaves/espaços/quebras de linha não alteram o hash."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def utc(value) -> datetime:
    ts = pd.Timestamp(value)
    if pd.isna(ts) or ts.tzinfo is None:
        raise ValueError("Timestamp deve ser preenchido e informar o fuso.")
    return ts.tz_convert("UTC").to_pydatetime()


class EventRuntime:
    """Carrega um artefato próprio e confiável; não consulta treino nem chama fit."""

    def __init__(self, model_dir: Path, policy: dict, policy_sha256: str, threads: int = 2):
        if isinstance(threads, bool) or not isinstance(threads, int) or threads < 1:
            raise ValueError("threads deve ser inteiro positivo.")
        self.threads, self.lock = threads, Lock()
        manifest_path, model_path = model_dir / "manifest.json", model_dir / "model.joblib"
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        m = self.manifest
        if m.get("release") != RELEASE:
            raise ValueError("Versão de manifesto incompatível com event_artifact.")
        if m["policy_contract_sha256"] != canonical_hash(policy):
            raise ValueError("A política não corresponde à vinculada ao artefato.")
        if policy["selected"]["method"] != "hgb_weather_classifier":
            raise ValueError("Esta integração exige a política HGB selecionada.")
        for name in ("conjunto", "horizon_hours", "availability_delay_hours", "drop_mw"):
            if m[name] != policy[name]:
                raise ValueError(f"Contrato do modelo e política divergem em {name}.")
        for name, current in (("sklearn", sklearn.__version__), ("numpy", np.__version__),
                              ("pandas", pd.__version__), ("joblib", joblib.__version__)):
            if m["versions"][name] != current:
                raise ValueError(f"Versão de {name} difere do treino. Use o mesmo ambiente do artefato.")
        if sha256(model_path) != m["model_sha256"]:
            raise ValueError("model.joblib difere do hash registrado; carregamento interrompido.")
        self.columns = m["feature_columns"]
        if len(self.columns) != 32 or len(set(self.columns)) != 32:
            raise ValueError("Manifesto exige 32 nomes únicos de features.")
        if set(self.columns) & {"p_event", "event_drop", "target_generation", "target_available_at"}:
            raise ValueError("Manifesto contém alvo ou saída como feature.")
        # joblib é carregado somente depois da conferência, para artefatos gerados localmente.
        self.model = joblib.load(model_path)
        if not isinstance(self.model, HistGradientBoostingClassifier):
            raise ValueError("O artefato não contém o classificador HGB esperado.")
        if list(self.model.feature_names_in_) != self.columns:
            raise ValueError("Nomes/ordem do modelo diferem do manifesto.")
        classes = list(self.model.classes_)
        if set(classes) != {0, 1}:
            raise ValueError("Classificador deve conter as classes 0 e 1.")
        self.positive_index = classes.index(1)
        self.policy, self.policy_sha256 = policy, policy_sha256
        self.manifest_sha256 = sha256(manifest_path)

    def feature_matrix(self, request: EventPredictRequest) -> pd.DataFrame:
        """Reconstrói X pelo contrato de treino, independentemente da ordem do JSON."""
        m = self.manifest
        received, expected = set(request.features), set(self.columns)
        if received != expected:
            raise ValueError(f"Features incompatíveis. Ausentes: {sorted(expected-received)}; adicionais: {sorted(received-expected)}.")
        origin, target, history, weather = [
            value.astimezone(timezone.utc) for value in (
                request.forecast_origin, request.target_time, request.history_end,
                request.weather_latest_available_at,
            )
        ]
        if origin.minute or origin.second or origin.microsecond:
            raise ValueError("forecast_origin deve estar alinhado à hora.")
        if target != origin + timedelta(hours=m["horizon_hours"]):
            raise ValueError("target_time deve ser forecast_origin + 24 horas.")
        if history != origin - timedelta(hours=m["availability_delay_hours"]):
            raise ValueError("history_end deve ser forecast_origin - 2 horas.")
        if weather > origin:
            raise ValueError("Meteorologia ainda indisponível na emissão.")
        if origin < utc(m["training_cutoff"]) or utc(m["latest_train_label_available_at"]) >= origin:
            raise ValueError("O artefato usa rótulos posteriores ao corte permitido para esta emissão.")
        if request.conjunto != m["conjunto"] or request.weather_model != m["weather_model"]:
            raise ValueError("Conjunto ou modelo meteorológico incompatível com o artefato.")
        return pd.DataFrame([[request.features[c] for c in self.columns]], columns=self.columns)

    def predict(self, request: EventPredictRequest) -> EventPredictionResponse:
        X = self.feature_matrix(request)
        # Contexto de threads compartilhado: serializar esta pequena API local.
        with self.lock, threadpool_limits(limits=self.threads):
            p_event = float(self.model.predict_proba(X)[0, self.positive_index])
        threshold = float(self.policy["selected"]["threshold"])
        origin = request.forecast_origin.astimezone(timezone.utc)
        return EventPredictionResponse(
            mode="development_inference", model_id=self.manifest["model_id"],
            model_sha256=self.manifest["model_sha256"], manifest_sha256=self.manifest_sha256,
            policy_id=self.policy["policy_id"], policy_sha256=self.policy_sha256,
            method="hgb_weather_classifier", forecast_origin=origin,
            target_time=request.target_time, history_end=request.history_end,
            weather_latest_available_at=request.weather_latest_available_at,
            drop_threshold_mwmed=self.policy["drop_mw"],
            last_available_generation=request.features["lag_1h"],
            event_generation_at_or_below_mwmed=request.features["lag_1h"] - self.policy["drop_mw"],
            p_event=p_event, threshold=threshold, alarm=p_event >= threshold,
            feature_count=len(self.columns), estimator_executed=True, model_retrained=False,
            capacity_enforced_at_runtime=False, availability_is_assumed=True,
        )


def build_artifact(input_dir: Path, policy_path: Path, output_dir: Path, origin, threads=2):
    """Um ajuste de desenvolvimento, com corte por disponibilidade e exportação de X."""
    from renewable_forecast.decision_api import DecisionPolicy
    from renewable_forecast.weather_ablation import load_model_frame
    from renewable_forecast.weather_events import CLASSIFIER_PARAMS, build_event_labels

    policy = DecisionPolicy.model_validate_json(policy_path.read_bytes()).model_dump(mode="json")
    if policy["selected"]["method"] != "hgb_weather_classifier":
        raise ValueError("A política deve selecionar hgb_weather_classifier.")
    if threads < 1:
        raise ValueError("threads deve ser positivo.")
    frame, source = load_model_frame(input_dir)
    origin = utc(origin)
    for name in ("conjunto", "horizon_hours", "availability_delay_hours"):
        if source[name] != policy[name]:
            raise ValueError(f"Tabela e política divergem em {name}.")
    selected = frame.loc[frame.forecast_origin.eq(origin)]
    if len(selected) != 1:
        raise ValueError("A emissão deve existir uma única vez em model_frame.csv.")
    row = selected.iloc[0]
    columns = source["model_feature_columns"]
    signature = {
        "source_frame_sha256": sha256(input_dir / "model_frame.csv"),
        "source_metadata_sha256": sha256(input_dir / "metadata.json"),
        "training_cutoff": origin.isoformat(), "feature_columns": columns,
        "estimator_params": CLASSIFIER_PARAMS, "policy_contract_sha256": canonical_hash(policy),
        "artifact_code_sha256": sha256(Path(__file__)),
    }
    if (output_dir / "manifest.json").exists():
        runtime = EventRuntime(output_dir, policy, sha256(policy_path), threads)
        if any(runtime.manifest.get(k) != v for k, v in signature.items()):
            raise ValueError("A pasta contém outro ajuste. Escolha uma nova saída.")
        if not (output_dir / "example_request.json").is_file():
            raise ValueError("Artefato incompleto: falta example_request.json.")
        print(f"Artefato compatível reutilizado: {output_dir.resolve()}")
        return runtime.manifest
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("A saída contém arquivos; use uma pasta nova para preservar o experimento.")

    eligible = (frame.forecast_origin < origin) & (frame.target_available_at < origin)
    train = frame.loc[eligible].copy()
    if train.empty:
        raise ValueError("Não há rótulos disponíveis antes do corte.")
    y = build_event_labels(train, policy["drop_mw"])["event_drop"].to_numpy()
    if set(np.unique(y)) != {0, 1}:
        raise ValueError("O treino deve conter as classes 0 e 1.")
    model = HistGradientBoostingClassifier(**CLASSIFIER_PARAMS)
    print(f"Ajustando HGB: {len(train)}/{len(frame)} linhas; {int(y.sum())} eventos; {len(columns)} features.", flush=True)
    with threadpool_limits(limits=threads):
        model.fit(train[columns], y)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "model.joblib"
    joblib.dump(model, model_path, compress=3)
    model_hash = sha256(model_path)
    manifest = {
        "release": RELEASE, "model_id": f"CJU_BA5EIGT-h24-event-{model_hash[:12]}",
        **signature, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_sha256": model_hash, "training_rows": len(train), "training_events": int(y.sum()),
        "excluded_rows": len(frame)-len(train),
        "latest_train_label_available_at": train.target_available_at.max().isoformat(),
        "train_origin_start": train.forecast_origin.min().isoformat(),
        "train_origin_end": train.forecast_origin.max().isoformat(),
        "training_rule": "forecast_origin < cutoff AND target_available_at < cutoff",
        "conjunto": policy["conjunto"], "horizon_hours": policy["horizon_hours"],
        "availability_delay_hours": policy["availability_delay_hours"], "drop_mw": policy["drop_mw"],
        "weather_model": str(row["weather_model"]), "classes": [int(c) for c in model.classes_],
        "event_definition": "lag_1h - target_generation >= 22.77; endpoint, not any drop during next24h",
        "scope": "engineering integration using historical features and post-hoc development policy; no new performance evaluation",
        "model_promotion": False, "availability_is_assumed": True,
        "policy_selection_is_retrospective": True,
        "generation_timezone_hypothesis": source["generation_timezone_hypothesis"],
        "generation_timezone_verified": source["generation_timezone_verified"],
        "generation_interval_semantics": source["generation_interval_semantics"],
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__},
    }
    write_json(output_dir / "manifest.json", manifest)
    request = EventPredictRequest(
        conjunto=policy["conjunto"], weather_model=str(row["weather_model"]),
        **{k: row[k] for k in ("forecast_origin", "history_end", "target_time", "weather_latest_available_at")},
        features={name: float(row[name]) for name in columns},
    )
    write_json(output_dir / "example_request.json", request.model_dump(mode="json"))
    print(f"Último rótulo disponível: {manifest['latest_train_label_available_at']}")
    print(f"Corte: {origin.isoformat()}; alvo do exemplo: {request.target_time.isoformat()}")
    print(f"Artefato e pedido sem alvo salvos: {output_dir.resolve()}")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--forecast-origin", required=True)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    build_artifact(args.input_dir, args.policy, args.output_dir, args.forecast_origin, args.threads)


if __name__ == "__main__":
    main()
