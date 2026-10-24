from datetime import datetime, timedelta


def avaliar_atualidade(
    forecast_origin: datetime,
    target_time: datetime,
    now: datetime,
    *,
    mode: str,
    max_age: timedelta,
) -> dict:
    """
    Retorna exatamente:
        allowed: bool
        state: str
        age_seconds: float
        reason: str

    Modos aceitos:
        historical_replay
        operational
    """
    for name, value in (
        ("forecast_origin", forecast_origin),
        ("target_time", target_time),
        ("now", now),
    ):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{name} deve conter fuso horário.")
    if mode not in ("historical_replay", "operational"):
        raise ValueError(f"Modo desconhecido: {mode}")
    if max_age < timedelta(0):
        raise ValueError("max_age não pode ser negativo.")
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
            True, "current", "Previsão atual para apresentação operacional."
        )
    return {
        "allowed": allowed,
        "state": state,
        "age_seconds": age_seconds,
        "reason": reason,
    }


if __name__ == "__main__":
    from datetime import timezone

    utc = timezone.utc
    now = datetime(2026, 10, 14, 21, 38, tzinfo=utc)
    cases = [
        (
            "pedido histórico / reprodução",
            datetime(2026, 8, 1, 5, tzinfo=utc),
            datetime(2026, 8, 2, 5, tzinfo=utc),
            "historical_replay",
        ),
        (
            "mesmo pedido / operação",
            datetime(2026, 8, 1, 5, tzinfo=utc),
            datetime(2026, 8, 2, 5, tzinfo=utc),
            "operational",
        ),
        (
            "origem recente / operação",
            now - timedelta(hours=1),
            now + timedelta(hours=23),
            "operational",
        ),
        (
            "origem antiga, alvo futuro / operação",
            now - timedelta(hours=3),
            now + timedelta(hours=21),
            "operational",
        ),
        (
            "origem futura / operação",
            now + timedelta(minutes=1),
            now + timedelta(hours=24, minutes=1),
            "operational",
        ),
    ]
    for name, origin, target, mode in cases:
        result = avaliar_atualidade(
            origin, target, now, mode=mode, max_age=timedelta(hours=2)
        )
        print(name, "=>", result)
