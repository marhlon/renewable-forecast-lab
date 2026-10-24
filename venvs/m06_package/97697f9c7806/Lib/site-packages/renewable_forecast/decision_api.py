"""M06: decisão sobre p_event e inferência opcional do classificador salvo.

/decisions recebe p_event; /predict-decision recebe features e calcula p_event.
Uso: python -m renewable_forecast.decision_api --policy CAMINHO/policy.json --model-dir PASTA
"""
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Body, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
import uvicorn

from renewable_forecast.event_artifact import (
    EventPredictRequest, EventPredictionResponse, EventRuntime,
)


RELEASE = "2026.10.04-decision-api-3"
Method = Literal["historical_frequency", "logistic_weather", "hgb_weather_classifier"]
Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False, strict=True)]
SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class SelectedRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    method: Method
    threshold: Probability
    alarms: int = Field(ge=0, strict=True)
    cost_total: float = Field(ge=0, allow_inf_nan=False)
    precision: Probability | None
    recall: Probability | None


class DecisionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"]
    policy_id: str = Field(min_length=1)
    status: Literal["development"]
    conjunto: Literal["CJU_BA5EIGT"]
    horizon_hours: Literal[24]
    availability_delay_hours: Literal[2]
    drop_mw: Literal[22.77]
    event_reference: Literal["last_available_generation"]
    cost_fp: float = Field(ge=0, allow_inf_nan=False)
    cost_fn: float = Field(ge=0, allow_inf_nan=False)
    max_alarms_on_selection: int = Field(ge=0, strict=True)
    selection_rows: int = Field(gt=0, strict=True)
    capacity_enforced_at_runtime: Literal[False]
    source_predictions_sha256: SHA256
    selected: SelectedRule

    @model_validator(mode="after")
    def selection_is_feasible(self):
        if self.selected.alarms > min(self.max_alarms_on_selection, self.selection_rows):
            raise ValueError("A regra exportada viola a capacidade no desenvolvimento.")
        return self


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conjunto: Literal["CJU_BA5EIGT"]
    method: Method
    forecast_origin: AwareDatetime
    history_end: AwareDatetime
    target_time: AwareDatetime
    drop_threshold_mwmed: float = Field(gt=0, allow_inf_nan=False, strict=True)
    p_event: Probability


class DecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policy_id: str
    policy_sha256: SHA256
    mode: Literal["development_replay"]
    method: Method
    forecast_origin: AwareDatetime
    target_time: AwareDatetime
    p_event: Probability
    threshold: Probability
    alarm: bool
    capacity_enforced_at_runtime: Literal[False]


def decidir(request: DecisionRequest, policy: DecisionPolicy, policy_sha256: str) -> DecisionResponse:
    """Regra pura: contrato temporal + identidade do evento + p >= limiar."""
    if request.method != policy.selected.method:
        raise ValueError("O método recebido difere do método selecionado na política.")
    if request.drop_threshold_mwmed != policy.drop_mw:
        raise ValueError("A probabilidade recebida usa outro limiar físico de queda.")
    origin = request.forecast_origin.astimezone(timezone.utc)
    target = request.target_time.astimezone(timezone.utc)
    history = request.history_end.astimezone(timezone.utc)
    if target - origin != timedelta(hours=policy.horizon_hours):
        raise ValueError("target_time deve ser forecast_origin + 24 horas.")
    if origin - history != timedelta(hours=policy.availability_delay_hours):
        raise ValueError("history_end deve ser forecast_origin - 2 horas neste contrato.")
    return DecisionResponse(
        policy_id=policy.policy_id, policy_sha256=policy_sha256,
        mode="development_replay", method=request.method,
        forecast_origin=origin, target_time=target, p_event=request.p_event,
        threshold=policy.selected.threshold,
        alarm=request.p_event >= policy.selected.threshold,
        capacity_enforced_at_runtime=False,
    )


def create_app(policy_path: Path, model_dir: Path | None = None, threads: int = 2) -> FastAPI:
    """Carrega uma política validada uma vez; mudanças exigem reiniciar o serviço."""
    raw = policy_path.read_bytes()
    policy = DecisionPolicy.model_validate_json(raw)
    policy_sha256 = hashlib.sha256(raw).hexdigest()
    app = FastAPI(title="Renewcast — API local de decisão", version=RELEASE)
    runtime = EventRuntime(model_dir, policy.model_dump(mode="json"), policy_sha256, threads) if model_dir else None
    inference_examples = None
    if model_dir is not None and (model_dir / "example_request.json").is_file():
        import json
        inference_examples = {"features_reais": {
            "summary": "32 features históricas; probabilidade calculada pelo servidor",
            "value": json.loads((model_dir / "example_request.json").read_text(encoding="utf-8")),
        }}
    # Exemplos didáticos compatíveis com a política carregada; não são nova inferência.
    origin_example = datetime(2026, 7, 11, 6, tzinfo=timezone.utc)
    at_threshold = {
        "conjunto": policy.conjunto,
        "method": policy.selected.method,
        "forecast_origin": origin_example.isoformat(),
        "history_end": (origin_example - timedelta(hours=policy.availability_delay_hours)).isoformat(),
        "target_time": (origin_example + timedelta(hours=policy.horizon_hours)).isoformat(),
        "drop_threshold_mwmed": policy.drop_mw,
        "p_event": policy.selected.threshold,
    }
    examples = {
        "no_limiar": {
            "summary": "Válido: probabilidade igual ao limiar — alarme verdadeiro",
            "description": "Probabilidade didática para demonstrar p >= threshold; não é previsão recalculada.",
            "value": at_threshold,
        },
        "probabilidade_invalida": {
            "summary": "Inválido: p_event=1.2 — rejeição HTTP 422 esperada",
            "value": {**at_threshold, "p_event": 1.2},
        },
    }

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc):
        # Evita reproduzir valores inválidos (NaN/Inf) no próprio JSON de erro.
        errors = [{k: err[k] for k in ("loc", "msg", "type")} for err in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.get("/health")
    async def health():
        return {"status": "ok", "release": RELEASE, "policy_id": policy.policy_id,
                "model_loaded": runtime is not None}

    @app.get("/policy", response_model=DecisionPolicy)
    async def get_policy():
        return policy

    @app.post("/decisions", response_model=DecisionResponse)
    async def post_decision(request: DecisionRequest = Body(..., openapi_examples=examples)):
        try:
            return decidir(request, policy, policy_sha256)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/model")
    async def get_model():
        if runtime is None:
            raise HTTPException(status_code=503, detail="Inicie o servidor com --model-dir para habilitar inferência.")
        return {k: runtime.manifest[k] for k in (
            "model_id", "model_sha256", "training_cutoff", "latest_train_label_available_at",
            "training_rows", "training_events", "feature_columns", "classes", "scope", "versions",
        )}

    @app.post("/predict-decision", response_model=EventPredictionResponse)
    async def predict_decision(request: EventPredictRequest = Body(..., openapi_examples=inference_examples)):
        if runtime is None:
            raise HTTPException(status_code=503, detail="Nenhum classificador carregado; informe --model-dir.")
        try:
            return runtime.predict(request)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port deve estar entre 1 e 65535.")
    if args.threads < 1:
        parser.error("threads deve ser positivo.")
    app = create_app(args.policy, args.model_dir, args.threads)
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
