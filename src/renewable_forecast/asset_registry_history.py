"""Seleção cadastral por vigência física e conhecimento disponível na origem."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone


def _utc(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp deve ser texto ISO com fuso.")
    try:
        stamp = datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise ValueError("Timestamp ISO inválido.") from exc
    if stamp.tzinfo is None:
        raise ValueError("Timestamp sem fuso não pode ser comparado.")
    return stamp.astimezone(timezone.utc)


def selecionar_cadastro_causal(registros, *, instante, conhecido_em):
    """Devolva cópias das versões elegíveis; vigência não comprovada é excluída.

    Intervalos são fechados à esquerda e abertos à direita. Uma correção com
    known_from posterior à origem não altera a resposta daquela origem.
    """
    valid_at, as_of = _utc(instante), _utc(conhecido_em)
    selected, seen = {}, set()
    for row in registros:
        if not isinstance(row, dict):
            raise ValueError("Registro cadastral deve ser dict.")
        required = {"asset_id","version","valid_from","valid_to","known_from",
                    "known_to","historical_validity_verified"}
        if not required <= row.keys():
            raise ValueError("Registro cadastral incompleto.")
        if any(not isinstance(row[k],str) or not row[k] for k in ("asset_id","version")):
            raise ValueError("Identidade e versão devem ser textos não vazios.")
        key = (row["asset_id"],row["version"])
        if key in seen:
            raise ValueError("Identidade/versão repetida.")
        seen.add(key)
        known_start = _utc(row["known_from"])
        known_end = _utc(row["known_to"]) if row["known_to"] is not None else None
        valid_start = _utc(row["valid_from"]) if row["valid_from"] is not None else None
        valid_end = _utc(row["valid_to"]) if row["valid_to"] is not None else None
        if type(row["historical_validity_verified"]) is not bool:
            raise ValueError("A confirmação de vigência deve ser booleana.")
        if known_end is not None and known_end <= known_start:
            raise ValueError("Intervalo de conhecimento inválido.")
        if valid_end is not None and (valid_start is None or valid_end <= valid_start):
            raise ValueError("Intervalo de vigência inválido.")
        if row["historical_validity_verified"] and valid_start is None:
            raise ValueError("Vigência confirmada exige valid_from documentado.")
        if not row["historical_validity_verified"]:
            continue
        if not (valid_start <= valid_at and (valid_end is None or valid_at < valid_end)):
            continue
        if not (known_start <= as_of and (known_end is None or as_of < known_end)):
            continue
        old = selected.get(row["asset_id"])
        if old is not None and known_start == old[0]:
            raise ValueError("Versões elegíveis empatam no tempo de conhecimento.")
        if old is None or known_start > old[0]:
            selected[row["asset_id"]] = (known_start,deepcopy(row))
    return [selected[key][1] for key in sorted(selected)]
