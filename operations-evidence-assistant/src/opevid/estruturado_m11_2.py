"""Relatório auditável: decodificação JSON, esquema, fidelidade e fallback."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from opevid.contrato import decidir


DecimalText = Annotated[str, Field(min_length=1, max_length=32, pattern=r"^(?:0(?:\.[0-9]+)?|1(?:\.0+)?)$")]
CaseId = Annotated[str, Field(min_length=1, max_length=48, pattern=r"^[a-z0-9_]+$")]
Ref = Literal["usable", "k", "cutoff", "s1", "s2"]
Reason = Literal["unavailable", "below", "pair_below", "no_pair", "single_met", "pair_met",
                 "incident_detected", "physical_cause"]
Code = Literal["BELOW", "ISOLATED", "ELIGIBLE", "INSUFFICIENT"]
NUMERIC = ("cutoff", "s1", "s2")
MAX_CHARS = 4096


class Relatorio(BaseModel):
    """Campos obrigatórios; observações ausentes usam null, sem omitir a chave."""
    model_config = ConfigDict(strict=True, extra="forbid")
    id: CaseId
    code: Code
    cutoff: DecimalText
    s1: DecimalText | None
    s2: DecimalText | None
    reason: Reason
    refs: Annotated[list[Ref], Field(max_length=8)]


class Fonte(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    id: CaseId
    cutoff: DecimalText
    s1: DecimalText | None
    s2: DecimalText | None
    usable: bool
    k: int


def esperado_da_fonte(raw):
    src = Fonte.model_validate(raw).model_dump()
    k, s1, s2, usable = (src[x] for x in ("k", "s1", "s2", "usable"))
    if k not in (1, 2) or (not usable and (s1 is not None or s2 is not None)):
        raise ValueError(f"Disponibilidade ou regra inconsistente na fonte {src['id']}.")
    if usable and s1 is None:
        raise ValueError(f"Falta o pico em fonte utilizável {src['id']}.")
    code = decidir(src)
    if code == "INSUFFICIENT":
        reason, refs = "unavailable", ["usable"]
    elif code == "BELOW":
        reason, refs = "below", ["s1", "cutoff"]
    elif code == "ISOLATED":
        reason = "no_pair" if s2 is None else "pair_below"
        refs = ["k", "s1", "s2", "cutoff"]
    elif k == 1:
        reason, refs = "single_met", ["k", "s1", "cutoff"]
    else:
        reason, refs = "pair_met", ["k", "s2", "cutoff"]
    return {"id": src["id"], "code": code, **{key:src[key] for key in NUMERIC}, "reason": reason, "refs": refs}


def conferir_fidelidade(candidato, esperado):
    """Ambos já têm o mesmo esquema; devolve todas as divergências detectadas."""
    errors = []
    if candidato["id"] != esperado["id"]:
        errors.append("id_divergente")
    if candidato["code"] != esperado["code"]:
        errors.append("classe_divergente")
    for key in NUMERIC:
        got, want = candidato[key], esperado[key]
        if (got is None or want is None) and got is not want:
            errors.append(f"numero_divergente:{key}")
        elif got is not None and Decimal(got) != Decimal(want):
            errors.append(f"numero_divergente:{key}")
    if candidato["reason"] != esperado["reason"]:
        errors.append("razao_sem_suporte")
    refs = set(candidato["refs"])
    required = set(esperado["refs"])
    if len(refs) != len(candidato["refs"]):
        errors.append("citacao_repetida")
    errors += [f"citacao_ausente:{key}" for key in sorted(required-refs)]
    errors += [f"citacao_extra:{key}" for key in sorted(refs-required)]
    return errors


class JsonInvalido(ValueError):
    pass


def pares_unicos(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise JsonInvalido("chave_duplicada")
        result[k] = v
    return result


def constante_invalida(value):
    raise JsonInvalido("constante_nao_json")


def explicar(payload):
    """Template controlado: a correspondência com a fonte vem antes da explicação."""
    description = {
        "unavailable": "Registro indisponível para aplicar a regra.",
        "below": "O pico ficou abaixo do corte.",
        "pair_below": "O pico chegou ao corte; o melhor par ficou abaixo.",
        "no_pair": "O pico chegou ao corte; faltou um par utilizável.",
        "single_met": "O pico chegou ao corte para uma leitura.",
        "pair_met": "O melhor par chegou ao corte para duas leituras.",
    }
    return description[payload["reason"]]


def aplicar_autoria(func, got, want):
    a, b = deepcopy(got), deepcopy(want)
    issues = func(a, b)
    if a != got or b != want:
        raise ValueError("A autoria modificou os dados do relatório ou a referência.")
    if (type(issues) is not list or any(type(e) is not str for e in issues)
            or len(set(issues)) != len(issues)):
        raise ValueError("Retorne uma lista de strings, sem repetições.")
    return sorted(issues)


def avaliar_resposta(texto, fonte, func=conferir_fidelidade):
    want = esperado_da_fonte(fonte)
    stage = "json_invalido"
    errors = []
    parsed = None
    try:
        if len(texto) > MAX_CHARS:
            raise JsonInvalido("resposta_excede_limite")
        raw = json.loads(texto, object_pairs_hook=pares_unicos, parse_constant=constante_invalida)
    except JsonInvalido as exc:
        errors = [str(exc)]
    except (ValueError, RecursionError):
        errors = ["json_malformado"]
    else:
        try:
            parsed = Relatorio.model_validate(raw).model_dump()
        except ValidationError as exc:
            stage = "esquema_invalido"
            errors = sorted(":".join((str(item["type"]), ".".join(map(str,item["loc"]))))
                            for item in exc.errors(include_url=False, include_context=False, include_input=False))
        else:
            errors = aplicar_autoria(func, parsed, want)
            if func is not conferir_fidelidade and errors != sorted(conferir_fidelidade(parsed, want)):
                raise ValueError(f"Validação autoral diverge no caso {fonte['id']}: {errors!r}.")
            stage = "divergencia" if errors else "fiel"
    # A publicação usa números originais e texto controlado até quando a proposta confere.
    final = {"origem": "conferido" if stage == "fiel" else "fallback", **want,
             "explicacao": explicar(want)}
    return {"etapa": stage, "erros": errors, "candidato": parsed, "publicado": final}
