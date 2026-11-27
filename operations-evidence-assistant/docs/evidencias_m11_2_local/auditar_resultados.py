"""Audita a execução M11.2 com biblioteca padrão, sem Pydantic ou inferência.

Reconta as etapas, confere publicações contra as fontes das tentativas,
implementa o esquema estrito observado e verifica as 16 contraprovas.
Não importa projeto/cache privado, não chama LLM e não lê a referência.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re


BASE = Path(__file__).resolve().parents[2]
RUN = BASE / "reports/m11_2/20261125T000415Z_b376eb6f"
OUTPUT = Path(__file__).with_name("auditoria_resultados.json")
PLAN = BASE / "docs/m11_2/protocolo.json"
SOURCE_FIELDS = ("id", "k", "usable", "cutoff", "s1", "s2")
FIELDS = ("id", "code", "cutoff", "s1", "s2", "reason", "refs")
CODES = ("BELOW", "ISOLATED", "ELIGIBLE", "INSUFFICIENT")
REASONS = ("unavailable", "below", "pair_below", "no_pair", "single_met", "pair_met", "incident_detected", "physical_cause")
REFS = ("usable", "k", "cutoff", "s1", "s2")
DECIMAL_PATTERN = r"^(?:0(?:\.[0-9]+)?|1(?:\.0+)?)$"
ID_PATTERN = r"^[a-z0-9_]+$"
EXPLANATIONS = {
    "unavailable": "Registro indisponível para aplicar a regra.",
    "below": "O pico ficou abaixo do corte.",
    "pair_below": "O pico chegou ao corte; o melhor par ficou abaixo.",
    "no_pair": "O pico chegou ao corte; faltou um par utilizável.",
    "single_met": "O pico chegou ao corte para uma leitura.",
    "pair_met": "O melhor par chegou ao corte para duas leituras.",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def same(actual, expected, name):
    require(math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-10), f"Número divergente: {name}")


def expected_from_source(source):
    require(set(source) == set(SOURCE_FIELDS), "Campos da fonte diferentes do contrato.")
    require(type(source["id"]) is str and 1 <= len(source["id"]) <= 48 and re.fullmatch(ID_PATTERN, source["id"]), "ID inválido na fonte.")
    require(type(source["k"]) is int and source["k"] in (1, 2) and type(source["usable"]) is bool, "Regra ou disponibilidade inválida.")
    for key in ("cutoff", "s1", "s2"):
        value = source[key]
        require(value is None and key != "cutoff" or type(value) is str and 1 <= len(value) <= 32 and re.fullmatch(DECIMAL_PATTERN, value), f"Decimal inválido na fonte: {key}")
    usable, k = source["usable"], source["k"]
    require(usable or source["s1"] is None and source["s2"] is None, "Indisponível não equivale a zero.")
    require(not usable or source["s1"] is not None, "Fonte utilizável sem pico.")
    require(k != 1 or source["s2"] is None, "k1 não admite melhor par.")
    if source["s2"] is not None:
        require(Decimal(source["s2"]) <= Decimal(source["s1"]), "Par supera pico na fonte.")
    if not usable:
        code, reason, refs = "INSUFFICIENT", "unavailable", ["usable"]
    elif Decimal(source["s1"]) < Decimal(source["cutoff"]):
        code, reason, refs = "BELOW", "below", ["s1", "cutoff"]
    elif k == 2 and (source["s2"] is None or Decimal(source["s2"]) < Decimal(source["cutoff"])):
        code = "ISOLATED"
        reason = "no_pair" if source["s2"] is None else "pair_below"
        refs = ["k", "s1", "s2", "cutoff"]
    elif k == 1:
        code, reason, refs = "ELIGIBLE", "single_met", ["k", "s1", "cutoff"]
    else:
        code, reason, refs = "ELIGIBLE", "pair_met", ["k", "s2", "cutoff"]
    return {"id": source["id"], "code": code, **{key: source[key] for key in ("cutoff", "s1", "s2")}, "reason": reason, "refs": refs}


class InvalidJson(ValueError):
    pass


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidJson("chave_duplicada")
        result[key] = value
    return result


def invalid_constant(value):
    raise InvalidJson("constante_nao_json")


def schema_errors(raw):
    if type(raw) is not dict:
        return ["model_type:"]
    errors = [f"missing:{key}" for key in FIELDS if key not in raw]
    errors += [f"extra_forbidden:{key}" for key in raw if key not in FIELDS]
    for key in FIELDS:
        if key not in raw:
            continue
        value = raw[key]
        if key in ("id", "cutoff", "s1", "s2"):
            if value is None and key in ("s1", "s2"):
                continue
            if type(value) is not str:
                errors.append(f"string_type:{key}")
            elif len(value) < 1:
                errors.append(f"string_too_short:{key}")
            elif len(value) > (48 if key == "id" else 32):
                errors.append(f"string_too_long:{key}")
            elif not re.fullmatch(ID_PATTERN if key == "id" else DECIMAL_PATTERN, value):
                errors.append(f"string_pattern_mismatch:{key}")
        elif key in ("code", "reason"):
            if type(value) is not str or value not in (CODES if key == "code" else REASONS):
                errors.append(f"literal_error:{key}")
        else:
            if type(value) is not list:
                errors.append("list_type:refs")
            elif len(value) > 8:
                errors.append("too_long:refs")
            else:
                errors.extend(f"literal_error:refs.{i}" for i, item in enumerate(value) if type(item) is not str or item not in REFS)
    return sorted(errors)


def fidelity(candidate, expected):
    errors = []
    if candidate["id"] != expected["id"]:
        errors.append("id_divergente")
    if candidate["code"] != expected["code"]:
        errors.append("classe_divergente")
    for key in ("cutoff", "s1", "s2"):
        actual, wanted = candidate[key], expected[key]
        if actual is None or wanted is None:
            different = actual is not wanted
        else:
            different = Decimal(actual) != Decimal(wanted)
        if different:
            errors.append(f"numero_divergente:{key}")
    if candidate["reason"] != expected["reason"]:
        errors.append("razao_sem_suporte")
    refs, required = set(candidate["refs"]), set(expected["refs"])
    if len(refs) != len(candidate["refs"]):
        errors.append("citacao_repetida")
    errors.extend(f"citacao_ausente:{key}" for key in sorted(required - refs))
    errors.extend(f"citacao_extra:{key}" for key in sorted(refs - required))
    return sorted(errors)


def assess(text, source):
    expected = expected_from_source(source)
    parsed = None
    try:
        if len(text) > 4096:
            raise InvalidJson("resposta_excede_limite")
        raw = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=invalid_constant)
    except InvalidJson as exc:
        stage, errors = "json_invalido", [str(exc)]
    except (ValueError, RecursionError):
        stage, errors = "json_invalido", ["json_malformado"]
    else:
        errors = schema_errors(raw)
        if errors:
            stage = "esquema_invalido"
        else:
            parsed = {key: raw[key] for key in FIELDS}
            errors = fidelity(parsed, expected)
            stage = "divergencia" if errors else "fiel"
    final = {"origem": "conferido" if stage == "fiel" else "fallback", **expected,
             "explicacao": EXPLANATIONS[expected["reason"]]}
    return {"etapa": stage, "erros": errors, "candidato": parsed, "publicado": final}


def summarize(attempts, part, prompt):
    selected = [row for row in attempts if row["particao"] == part and row["prompt"] == prompt]
    stages = Counter(row["etapa"] for row in selected)
    typed = stages["fiel"] + stages["divergencia"]
    return {"particao": part, "prompt": prompt, "casos": len(selected),
        "json_ok": len(selected) - stages["json_invalido"], "esquema_ok": typed, "fiel": stages["fiel"],
        "fiel_entre_esquema": stages["fiel"] / typed if typed else None,
        "fallback": sum(r["publicado"]["origem"] == "fallback" for r in selected),
        "publicado_conferido": len(selected), "tokens_entrada": sum(r["tokens_entrada"] for r in selected),
        "tokens_novos": sum(r["tokens_novos"] for r in selected)}


def audit(run):
    report, plan = read_json(run / "resultado.json"), read_json(PLAN)
    require(report["schema"] == "opevid-m11-2-result-v1" and report["completed"] is True and report["run_id"] == run.name, "Execução incompleta.")
    require(report["mode"] == "cpu_fp32_greedy" and report["threads"] == plan["threads"] == 2 and report["treino"] is False and report["operational_approval"] is False, "Escopo diferente.")
    checked_hashes = {}

    def check_hash(path, expected):
        actual = sha(path)
        require(actual == expected, f"SHA-256 divergente: {path}")
        checked_hashes[path.relative_to(BASE).as_posix()] = actual

    check_hash(PLAN, report["protocol_sha256"])
    paths = {"dev": BASE / "data/casos_m11_1.json", "reservado": BASE / "data/m11_2/reservado.json", "model_lock": BASE / "model/model_lock.json"}
    for key, path in paths.items():
        check_hash(path, report["inputs_sha256"][key])
    require(report["inputs_sha256"]["dev"] == plan["dev_sha256"] and report["inputs_sha256"]["reservado"] == plan["reserved_sha256"], "Insumos diferentes do protocolo.")
    lock = read_json(paths["model_lock"])
    require(report["model_revision"] == plan["model_revision"] == lock["revision"] and report["model_weights_sha256"] == lock["files"]["model.safetensors"]["sha256"], "Modelo diferente.")
    check_hash(BASE / "notebooks/m11_2_fidelidade_autoral.py", report["autor_sha256"])
    delivery = read_json(BASE / "docs/m11_2/manifesto_entrega.json")
    for name, expected in report["code_sha256"].items():
        check_hash(BASE / name, expected)
        require(delivery["sha256"][f"operations-evidence-assistant/{name}"] == expected, f"Script/core alterado desde a distribuição: {name}")
    for relative in ("docs/m11_2/protocolo.json", "docs/m11_2/requirements.lock.txt"):
        check_hash(BASE / relative, delivery["sha256"][f"operations-evidence-assistant/{relative}"])
    for line in (BASE / "docs/m11_2/requirements.lock.txt").read_text().splitlines():
        if line.strip():
            package, expected = line.split("==")
            if package in report["versions"]:
                require(report["versions"][package] == expected, f"Versão incompatível: {package}")
    for name, expected in report["output_sha256"].items():
        check_hash(run / name, expected)
    decision_path = run / "decisao_prompt.json"
    check_hash(decision_path, report["decision_sha256"])
    decision = read_json(decision_path)
    schema = read_json(run / "esquema.json")
    require(schema["additionalProperties"] is False and set(schema["required"]) == set(schema["properties"]) == set(FIELDS), "Esquema de saída mudou.")
    require(schema["properties"]["code"]["enum"] == list(CODES) and schema["properties"]["reason"]["enum"] == list(REASONS), "Domínios de código/razão diferentes.")
    require(schema["properties"]["refs"]["maxItems"] == 8 and schema["properties"]["refs"]["items"]["enum"] == list(REFS), "Domínio de citações diferente.")
    dev_sources = {case["id"]: {key: case[key] for key in SOURCE_FIELDS} for case in read_json(paths["dev"])}
    with (run / "tentativas.jsonl").open(encoding="utf-8") as stream:
        attempts = [json.loads(line) for line in stream if line.strip()]
    require(len(attempts) == report["tentativas_geradas"] == 18, "Número de tentativas diferente.")
    variants = plan["variants"]
    require(variants == ["zero_shot", "um_exemplo"] and plan["no_retries_or_repair"] is True and plan["reserved_is_synthetic"] is True, "Plano alterado.")
    seen, reserved_sources = set(), {}
    for row in attempts:
        key = row["particao"], row["prompt"], row["id"]
        require(key not in seen, "Tentativa repetida ou retry.")
        seen.add(key)
        source = row["fonte"]
        require(row["id"] == source["id"] and row["prompt"] in variants, "Tentativa e fonte não correspondem.")
        if row["particao"] == "desenvolvimento":
            require(source == dev_sources[row["id"]], "Fonte DEV foi alterada.")
        else:
            require(row["particao"] == "reservado" and row["prompt"] == decision["prompt"] and row["id"] not in dev_sources, "Reservado executou outro prompt ou reutilizou ID DEV.")
            require(row["id"] not in reserved_sources, "ID reservado repetido.")
            reserved_sources[row["id"]] = source
        require(len(row["mensagens"]) == 2 and [m["role"] for m in row["mensagens"]] == ["system", "user"], "Papéis do prompt alterados.")
        user = row["mensagens"][1]["content"]
        actual_record, _ = json.JSONDecoder().raw_decode(user.rsplit("Record: ", 1)[1])
        require(actual_record == source, "Prompt renderizado trocou algum dado da fonte.")
        reassessed = assess(row["texto"], source)
        for field in ("etapa", "erros", "candidato", "publicado"):
            require(row[field] == reassessed[field], f"Recontagem independente divergiu em {row['particao']}/{row['id']}/{row['prompt']}: {field}; esperado {reassessed[field]!r}, recebido {row[field]!r}")
        require(type(row["tokens_entrada"]) is type(row["tokens_novos"]) is int and row["tokens_entrada"] > 0 and 1 <= row["tokens_novos"] <= plan["new_tokens"], "Contagem de tokens inválida.")
        require(row["tokens_entrada"] + plan["new_tokens"] <= plan["context_limit"] and math.isfinite(row["tempo_geracao_ms"]) and row["tempo_geracao_ms"] > 0, "Orçamento ou tempo inválido.")
        require(row["parada"] in ("eos", "limite_novos_tokens") and (row["parada"] == "eos" or row["tokens_novos"] == plan["new_tokens"]), "Parada escalar incoerente.")
    require(len(dev_sources) == len(reserved_sources) == 6 and set(seen) == {("desenvolvimento", variant, eid) for variant in variants for eid in dev_sources} | {("reservado", decision["prompt"], eid) for eid in reserved_sources}, "Coortes ou pareamento incompletos.")
    attempt_csv = csv_rows(run / "tentativas.csv")
    require(len(attempt_csv) == len(attempts), "CSV de tentativas incompleto.")
    for compact, row in zip(attempt_csv, attempts):
        for field in ("particao", "id", "prompt", "etapa", "parada"):
            require(compact[field] == row[field], f"CSV de tentativas divergiu: {field}")
        for field in ("tokens_entrada", "tokens_novos", "tempo_geracao_ms"):
            same(compact[field], row[field], field)
        require(compact["erros"] == "|".join(row["erros"]) and compact["origem_publicada"] == row["publicado"]["origem"], "CSV alterou erros ou rota.")
    metrics = [summarize(attempts, "desenvolvimento", variant) for variant in variants]
    winner = min(metrics, key=lambda m: (-m["fiel"], -m["esquema_ok"], m["tokens_novos"], variants.index(m["prompt"])))["prompt"]
    require(winner == decision["prompt"] == report["prompt_escolhido"], "Escolha não reproduziu o critério exclusivamente DEV.")
    require(decision["desenvolvimento"] == metrics and decision["criterios"] == plan["selection"] and decision["run_id"] == run.name and decision["selecao_em"] == "desenvolvimento", "Recibo de seleção divergente.")
    require(decision["input_dev_sha256"] == plan["dev_sha256"] and decision["protocol_sha256"] == report["protocol_sha256"] and decision["prompt_code_sha256"] == report["code_sha256"]["src/opevid/prompts_m11_2.py"], "Cadeia da seleção divergente.")
    require(decision["reservado_lido_antes"] is False and report["reservado_lido_depois_de_congelar"] is True and report["reservado_sintetico"] is True, "Declaração de congelamento alterada.")
    metrics.append(summarize(attempts, "reservado", winner))
    require(metrics == report["metricas"], "Métricas do recibo divergentes.")
    metric_csv = csv_rows(run / "metricas.csv")
    require(len(metric_csv) == len(metrics) == 3, "CSV de métricas incompleto.")
    for compact, metric in zip(metric_csv, metrics):
        for key, value in metric.items():
            if value is None:
                require(compact[key] == "", f"Razão indefinida virou número: {key}")
            elif isinstance(value, str):
                require(compact[key] == value, f"Métrica textual alterada: {key}")
            else:
                same(compact[key], value, key)
    fixtures = read_json(run / "contraprovas.json")
    require(len(fixtures) == report["contraprovas"] == 16 and len({row["teste"] for row in fixtures}) == 16, "Contraprovas incompletas.")
    for row in fixtures:
        assessed = assess(row["texto"], row["fonte"])
        for key, value in assessed.items():
            require(row[key] == value, f"Contraprova divergente: {row['teste']}.{key}")
    typed = sum(row["etapa"] in ("fiel", "divergencia") for row in attempts)
    require(typed == report["tentativas_tipadas_avaliadas_pelo_validador"] and report["comparou_autoria_com_referencia"] is True, "Contagem da validação autoral divergente.")
    frozen = datetime.fromisoformat(decision["congelado_em"])
    require(frozen.tzinfo is not None, "Congelamento sem fuso.")
    final_file_time = datetime.fromtimestamp((run / "tentativas.jsonl").stat().st_mtime, tz=timezone.utc)
    require(frozen <= final_file_time and sha(decision_path) == report["decision_sha256"], "Ordem de artefatos ou hash congelado divergente.")
    example = next(row for row in attempts if row["particao"] == "desenvolvimento" and row["prompt"] == "zero_shot" and row["id"] == "renewcast_replay")
    differences = []
    for eid in dev_sources:
        paired = {row["prompt"]: row for row in attempts if row["particao"] == "desenvolvimento" and row["id"] == eid}
        differences.append({"id": eid, "extra_input_tokens_with_example": paired["um_exemplo"]["tokens_entrada"] - paired["zero_shot"]["tokens_entrada"]})
    return {"schema": "opevid-m11-2-independent-audit-v1", "verified": True,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(), "run_id": run.name,
        "run_directory": run.relative_to(BASE).as_posix(),
        "method": "Standard-library audit of the completed run: strict JSON, explicit schema fields, Decimal fidelity, source-exact publication and independent DEV-only selection. No Pydantic/cache/project import or inference.",
        "checks": {"input_output_protocol_code_author_hashes": True, "eighteen_unique_attempts_and_frozen_reserved_prompt": True,
            "independent_json_schema_fidelity_stages": True, "source_exact_final_fields_and_controlled_explanation": True,
            "csv_and_json_metrics_routes_tokens_recounted": True, "development_only_selection_recomputed": True,
            "sixteen_contraprovas_reassessed": True, "frozen_decision_hash_preserved": True},
        "checked_hashes": checked_hashes, "metrics_recomputed": metrics, "chosen_prompt_recomputed": winner,
        "real_typed_attempt_count": typed, "contraprova_stage_counts": dict(Counter(row["etapa"] for row in fixtures)),
        "published_routes": dict(Counter(row["publicado"]["origem"] for row in attempts)),
        "published_source_exact_count": len(attempts), "extra_input_tokens_by_case": differences,
        "development_example": {key: example[key] for key in ("id", "prompt", "texto", "etapa", "erros", "candidato", "fonte", "publicado")},
        "freeze_evidence": {"frozen_at_utc": frozen.isoformat(), "decision_sha256": sha(decision_path),
            "reserved_read_before_freeze_declared": decision["reservado_lido_antes"],
            "final_attempts_file_mtime_utc": final_file_time.isoformat(), "first_reserved_read_timestamp_available": False,
            "limit": "The runner orders freeze before the reserved read; persisted hashes/declarations and file order do not independently timestamp the first read."},
        "limits": {"llm_inference_repeated": False, "pydantic_or_private_cache_imported": False,
            "full_pydantic_engine_equivalence_certified": False, "manual_schema_checked_only_for_recorded_cases": True,
            "original_reserved_content_reparsed": False, "original_reserved_sha256_verified": True,
            "reserved_sources_checked_from_completed_attempts": True, "tokenization_or_eos_ids_reproduced": False,
            "all_attempts_generated_before_auditor_read_outputs": True,
            "reference_artifacts_read": False, "benchmark_repeated": False, "production_validity_established": False,
            "note": "Frozen reserved is synthetic. Published fallback correctness is deterministic-system behavior, not LLM fidelity. Stop reasons/token budgets are scalar checks because output token IDs are not persisted."}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=RUN)
    args = parser.parse_args()
    result = audit(args.run_dir.resolve())
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Auditoria aprovada: 18 tentativas, 16 contraprovas e publicações exatas; prompt {result['chosen_prompt_recomputed']}.")
    print(f"JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
