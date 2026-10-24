"""Regra temporal de Marlon Alves Bomfim, promovida do exercício para o cliente.

A ordem das decisões foi preservada. A integração acrescenta validação de tipos
e normalização UTC para comparar instantes, inclusive em mudanças de offset.
Nenhuma decisão deste módulo aprova o modelo para uso operacional.
"""
from datetime import datetime, timedelta, timezone


POLICY_VERSION = "renewcast-presentation-time-v1"


def avaliar_atualidade(
    forecast_origin: datetime,
    target_time: datetime,
    now: datetime,
    *,
    mode: str,
    max_age: timedelta,
) -> dict:
    for name, value in (
        ("forecast_origin", forecast_origin),
        ("target_time", target_time),
        ("now", now),
    ):
        if not isinstance(value, datetime):
            raise ValueError(f"{name} deve ser datetime.")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{name} deve conter fuso horário.")
    if mode not in ("historical_replay", "operational"):
        raise ValueError(f"Modo desconhecido: {mode}")
    if not isinstance(max_age, timedelta) or max_age < timedelta(0):
        raise ValueError("max_age deve ser timedelta não negativo.")

    forecast_origin = forecast_origin.astimezone(timezone.utc)
    target_time = target_time.astimezone(timezone.utc)
    now = now.astimezone(timezone.utc)
    if target_time <= forecast_origin:
        raise ValueError("target_time deve ser posterior a forecast_origin.")

    age_seconds = (now - forecast_origin).total_seconds()
    if mode == "historical_replay":
        allowed, state, reason = (
            True, "historical_replay", "Permitido para reprodução histórica."
        )
    elif forecast_origin > now:
        allowed, state, reason = (
            False, "future_origin", "A origem da previsão está no futuro."
        )
    elif target_time <= now:
        allowed, state, reason = (
            False, "target_elapsed", "O horário alvo já foi atingido."
        )
    elif age_seconds > max_age.total_seconds():
        allowed, state, reason = (
            False, "stale_origin", "A origem excede a idade máxima de apresentação."
        )
    else:
        allowed, state, reason = (
            True, "current", "Previsão atual segundo a regra temporal de apresentação."
        )
    return {"allowed": allowed, "state": state, "age_seconds": age_seconds, "reason": reason}
