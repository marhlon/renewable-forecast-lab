"""Audita artefatos M11.1 sem carregar modelo, executar forwards ou benchmark.

Somente biblioteca padrão: hashes, Decimal, decodificação ByteLevel estática,
trilhas parciais e aritmética das medidas já persistidas.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import median


BASE = Path(__file__).resolve().parents[2]
RUN = BASE / "reports/m11_1/20261124T182345Z_2a298bc9"
REVISION = "12fd25f77366fa6b3b4b768ec3050bf629380bac"
SNAPSHOT = BASE / ".cache/m11_1" / REVISION
OUTPUT = Path(__file__).with_name("auditoria_resultados.json")
CODES = {"BELOW", "ISOLATED", "ELIGIBLE", "INSUFFICIENT"}
PROBES = ("Geração caiu; corte 0,719944.", "Geracao caiu; corte 0,719944.",
          "Geração caiu; corte 0.719944.", "An alarm is rejected.\nStatus:", "An alarm is allowed.\nStatus:")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def same(actual, expected, name):
    require(math.isclose(float(actual), float(expected), rel_tol=1e-11, abs_tol=1e-10), f"Valor divergente: {name}")


def boolean(value):
    require(value in ("True", "False"), f"Booleano CSV inválido: {value!r}")
    return value == "True"


def optional_number(value):
    return None if value in (None, "") else float(value)


def decide(case):
    if case["usable"] is False:
        return "INSUFFICIENT"
    require(case["usable"] is True and type(case["k"]) is int and case["k"] in (1, 2), "Caso com contrato inválido.")
    def number(value):
        require(isinstance(value, str), "Os decimais devem ser preservados como texto.")
        result = Decimal(value)
        require(result.is_finite() and 0 <= result <= 1, "Decimal fora do contrato.")
        return result
    cutoff, s1 = number(case["cutoff"]), number(case["s1"])
    s2 = number(case["s2"]) if case["s2"] is not None else None
    if s1 < cutoff:
        return "BELOW"
    if case["k"] == 2 and (s2 is None or s2 < cutoff):
        return "ISOLATED"
    return "ELIGIBLE"


def first_code(text):
    line = next((line.strip() for line in text.splitlines() if line.strip()), None)
    return line if line in CODES else None


def byte_decoder():
    present = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
    characters = present[:]
    next_extra = 256
    for value in range(256):
        if value not in present:
            present.append(value)
            characters.append(next_extra)
            next_extra += 1
    return dict(zip(map(chr, characters), present))


def partial_probabilities(trace, temperature):
    """Limites top8; quatro logits omitidos têm peso <= ao quarto conhecido."""
    top = trace["top4"]
    logits = [row["logit"] for row in top]
    weights = [math.exp((value - logits[0]) / temperature) for value in logits]
    lower_total = math.fsum(weights)
    upper_total = lower_total + 4 * weights[-1]
    chosen = trace["id_escolhido"]
    selected_rank = next((i for i, item in enumerate(top) if item["id"] == chosen), None)
    u = trace["u"]
    if selected_rank is None:
        possible = u >= lower_total / upper_total - 1e-14
        guaranteed = False
    else:
        before, through = math.fsum(weights[:selected_rank]), math.fsum(weights[:selected_rank + 1])
        possible = before / upper_total - 1e-14 <= u < through / lower_total + 1e-14
        guaranteed = before / lower_total <= u < through / upper_total
    require(possible, "Escolha incompatível mesmo com os limites dos quatro logits omitidos.")
    return {"selected_id": chosen, "u": u, "temperature": temperature,
        "top1_id": top[0]["id"], "top1_probability_lower_bound": 1 / upper_total,
        "top1_probability_upper_bound": 1 / lower_total,
        "selected_rank_in_saved_top4": None if selected_rank is None else selected_rank + 1,
        "choice_possible_from_partial_trace": possible, "choice_guaranteed_by_partial_bounds": guaranteed,
        "exact_top8_probability_available": False}


def audit(run, snapshot):
    report = read_json(run / "resultado.json")
    lock_path = BASE / "model/model_lock.json"
    lock = read_json(lock_path)
    delivery = read_json(BASE / "docs/m11_1/manifesto_entrega.json")
    require(report["schema"] == "opevid-m11-1-result-v1" and report["completed"] and report["run_id"] == run.name, "Resultado incompleto.")
    require(lock["schema"] == "opevid-m11-1-model-lock-v1" and lock["revision"] == report["model"]["revision"] == REVISION, "Snapshot diferente.")
    require(lock["repository"] == report["model"]["repository"] and report["training"] is False and report["operational_approval"] is False, "Origem ou escopo diferente.")
    checked_hashes = {}

    def check_hash(path, expected):
        digest = sha(path)
        require(digest == expected, f"SHA-256 divergente: {path}")
        label = path.relative_to(BASE).as_posix() if path.is_relative_to(BASE) else str(path)
        checked_hashes[label] = digest

    check_hash(lock_path, report["model"]["lock_sha256"])
    for relative in ("model/model_lock.json", "docs/m11_1/requirements.lock.txt"):
        check_hash(BASE / relative, delivery["sha256"][f"operations-evidence-assistant/{relative}"])
    check_hash(BASE / "data/casos_m11_1.json", report["case_set_sha256"])
    check_hash(BASE / "notebooks/m11_1_amostragem_autoral.py", report["author_sha256"])
    for path, expected in report["code_sha256"].items():
        check_hash(BASE / path, expected)
    for name, expected in report["output_sha256"].items():
        check_hash(run / name, expected)
    require(len(lock["files"]) == 7, "Quantidade de arquivos do snapshot diferente.")
    for name, identity in lock["files"].items():
        path = snapshot / name
        require(path.is_file() and path.stat().st_size == identity["bytes"], f"Snapshot ausente ou tamanho divergente: {name}")
        check_hash(path, identity["sha256"])
    require(report["model"]["weights_sha256"] == lock["files"]["model.safetensors"]["sha256"], "Pesos diferentes no recibo.")
    for line in (BASE / "docs/m11_1/requirements.lock.txt").read_text().splitlines():
        if line.strip():
            package, expected = line.split("==")
            if package in report["versions"]:
                require(report["versions"][package] == expected, f"Versão diferente do lock: {package}")
    require(report["versions"]["torch"] == "2.7.1+cpu" and report["threads"] == 2, "PyTorch ou número de threads diferente.")

    config, gen_config = read_json(snapshot / "config.json"), read_json(snapshot / "generation_config.json")
    tokenizer = read_json(snapshot / "tokenizer.json")
    vocabulary = {int(i): piece for piece, i in tokenizer["model"]["vocab"].items()}
    special = set()
    for entry in tokenizer["added_tokens"]:
        vocabulary[entry["id"]] = entry["content"]
        if entry["special"]:
            special.add(entry["id"])
    decoder = byte_decoder()

    def decode(ids, *, skip_special=False):
        data = bytearray()
        for token_id in ids:
            require(type(token_id) is int and 0 <= token_id < config["vocab_size"], "ID fora do vocabulário.")
            if skip_special and token_id in special:
                continue
            data.extend(decoder[c] for c in vocabulary[token_id])
        return bytes(data).decode("utf-8", errors="replace")

    for key in ("hidden_size", "vocab_size"):
        require(config[key] == report["model"][key], f"Configuração divergente: {key}")
    require(config["max_position_embeddings"] == report["model"]["model_max_position_embeddings"] and report["model"]["local_context_limit"] == 512, "Orçamento ou contexto diferente.")
    embeddings = read_json(run / "embeddings.json")
    token_rows = rows(run / "tokens.csv")
    probe_ids, norms = {}, {}
    for j, expected_text in enumerate(PROBES):
        metadata = embeddings["probes"][j]
        require(metadata["probe"] == j and metadata["texto"] == expected_text and metadata["round_trip"] is True, "Probe incorreto.")
        selected = [r for r in token_rows if int(r["probe"]) == j]
        require([int(r["posicao"]) for r in selected] == list(range(len(selected))), "Posições de tokens fora de ordem.")
        ids = [int(r["token_id"]) for r in selected]
        probe_ids[j] = ids
        require(metadata["tokens"] == len(ids) and metadata["caracteres"] == len(expected_text) and metadata["bytes_utf8"] == len(expected_text.encode()), "Contagem de texto/token inválida.")
        require(metadata["forma_embeddings"] == [1, len(ids), config["hidden_size"]], "Shape de embedding inválido.")
        require(decode(ids) == expected_text, "ByteLevel não reconstruiu probe inteiro.")
        for item, token_id in zip(selected, ids):
            require(item["peca_bpe"] == vocabulary[token_id] and item["decode_individual"] == decode([token_id]), "Peça ou decode individual divergente.")
            norm = float(item["norma_vetor_entrada"])
            require(math.isfinite(norm) and norm >= 0, "Norma inválida.")
            if token_id in norms:
                same(norm, norms[token_id], "Norma do mesmo embedding de entrada")
            norms[token_id] = norm
    require(len(probe_ids[0]) == len(probe_ids[2]), "Os dois probes decimais deveriam ser comparáveis por posição.")
    separator = [{"position_zero_based": i, "comma_id": a, "dot_id": b,
                  "comma_piece": vocabulary[a], "dot_piece": vocabulary[b]}
                 for i, (a, b) in enumerate(zip(probe_ids[0], probe_ids[2])) if a != b]
    require(len(separator) == 1 and separator[0]["comma_piece"] == "," and separator[0]["dot_piece"] == ".", "Mudança decimal inesperada.")
    contextual = embeddings["contraprova_contexto"]
    require(probe_ids[3][-1] == probe_ids[4][-1] == contextual["token_id"] and vocabulary[contextual["token_id"]] == contextual["mesmo_token_final"], "Token final diferente na contraprova.")
    require(contextual["delta_max_entrada"] == 0 and contextual["delta_max_contextual"] > 0 and -1 <= contextual["cosseno_contextual"] <= 1, "Contraprova contextual incoerente.")

    cases = read_json(BASE / "data/casos_m11_1.json")
    require(len(cases) == report["deterministic_rule_cases"] == 6 and len({c["id"] for c in cases}) == 6, "Conjunto de casos diferente.")
    case_map = {c["id"]: c for c in cases}
    expected_codes = {c["id"]: decide(c) for c in cases}
    baseline = rows(run / "baseline_regra.csv")
    require(len(baseline) == 6, "Baseline incompleto.")
    for row, case in zip(baseline, cases):
        require(row == {"id": case["id"], "tipo": case["tipo"], "origem": case["origem"], "regra_python": expected_codes[case["id"]]}, "Baseline diverge de Decimal.")
    generated = rows(run / "geracoes.csv")
    traces = read_json(run / "trilha_tokens.json")
    require(set(traces["prompts_renderizados"]) == set(case_map), "Prompts incompletos.")
    for case in cases:
        prompt = traces["prompts_renderizados"][case["id"]]
        record, _ = json.JSONDecoder().raw_decode(prompt.split("Record: ", 1)[1])
        require(record == {k: case[k] for k in ("usable", "k", "cutoff", "s1", "s2")}, "Registro renderizado alterou um campo.")
    require(len(generated) == len(traces["geracoes"]) == 19, "Quantidade de gerações diferente do protocolo medido.")
    eos = gen_config["eos_token_id"]
    ends = {eos} if isinstance(eos, int) else set(eos)
    full, sampling, trace_map, partial = [], [], {}, []
    sampling_decisions = 0
    initial_top4 = None
    for row, trace in zip(generated, traces["geracoes"]):
        ident = row["id"]
        temperature, seed = optional_number(row["temperatura"]), optional_number(row["semente"])
        require(ident == trace["id"] and row["precisao"] == trace["precisao"] and row["modo"] == trace["modo"] and int(row["teto_novos"]) == trace["teto_novos"] and temperature == trace["temperatura"] and seed == trace["semente"], "Linha e trilha não correspondem.")
        key = (ident, row["precisao"], row["modo"], int(row["teto_novos"]), temperature, seed)
        require(key not in trace_map, "Geração repetida.")
        trace_map[key] = trace
        ids = trace["novos_ids"]
        require(len(ids) == int(row["novos_tokens"]) and 1 <= len(ids) <= trace["teto_novos"], "Quantidade de IDs gerados incorreta.")
        require(decode(ids, skip_special=True) == row["texto"], "Texto não reproduz IDs persistidos via ByteLevel.")
        require(int(row["entrada_tokens"]) + int(row["teto_novos"]) <= report["model"]["local_context_limit"], "Geração excedeu orçamento.")
        if row["parada"] == "eos":
            require(ids[-1] in ends and not any(i in ends for i in ids[:-1]), "EOS não encerrou na primeira ocorrência.")
        else:
            require(row["parada"] == "limite_novos_tokens" and len(ids) == trace["teto_novos"] and not any(i in ends for i in ids), "Parada por orçamento incoerente.")
        require(float(row["tempo_decode_total_ms"]) >= float(row["ttft_ms_inclui_selecao"]) > 0, "Tempos de geração inválidos.")
        code = first_code(row["texto"])
        require(row["esperado"] == expected_codes[ident] and row["tipo"] == case_map[ident]["tipo"] and (row["codigo"] or None) == code, "Código ou caso alterado.")
        require(boolean(row["codigo_valido"]) == (code is not None) and boolean(row["codigo_correto"]) == (code == expected_codes[ident]), "Classificação automática divergente.")
        if row["modo"] == "greedy" and int(row["teto_novos"]) == 36:
            full.append(row)
        is_sampling = row["modo"] == "top_k"
        rng = random.Random(int(seed)) if is_sampling else None
        require(len(trace["dois_primeiros_passos"]) == min(2, len(ids)), "Trilha inicial incompleta.")
        for position, step in enumerate(trace["dois_primeiros_passos"]):
            require(step["passo"] == position + 1 and step["id_escolhido"] == ids[position], "Escolha inicial diverge dos IDs.")
            top = step["top4"]
            require(len(top) == 4 and len({x["id"] for x in top}) == 4 and top == sorted(top, key=lambda x: (-x["logit"], x["id"])), "Top4 fora de ordem.")
            for item in top:
                require(math.isfinite(item["logit"]) and item["peca"] == vocabulary[item["id"]], "Logit ou peça da trilha inválida.")
            if is_sampling:
                require(step["u"] == rng.random(), "Uniforme diferente da semente persistida.")
                bounds = partial_probabilities(step, temperature)
                if position == 0:
                    partial.append({"seed": int(seed), **bounds})
                    signature = [(x["id"], x["logit"]) for x in top]
                    if initial_top4 is not None:
                        require(signature == initial_top4, "O primeiro prefixo amostrado mudou seus logits.")
                    initial_top4 = signature
            else:
                require(step["u"] is None and step["id_escolhido"] == top[0]["id"], "Greedy não escolheu a primeira alternativa.")
        if is_sampling:
            require(ident == "satmon_sem52" and row["precisao"] == "fp32" and int(row["teto_novos"]) == 36, "Amostragem fora do caso fixado.")
            sampling.append(row)
            sampling_decisions += len(ids)
    require({(float(r["temperatura"]), int(r["semente"])) for r in sampling} == {(t, s) for t in (.35, 1.2) for s in (17, 29, 41)} and len(sampling) == 6, "Combinações de temperatura/semente incompletas.")
    require(sampling_decisions == report["top_k_real_decisions_checked"] and report["small_sampling_checks"] == 6 and report["authorship_checked_on_real_logits"] is True, "Contagem ou declaração de comparação autoral divergente.")
    require(report["greedy_generate_ids_agree"] is True, "Conferência com generate não declarada.")
    short_key = ("satmon_sem52", "fp32", "greedy", 6, None, None)
    long_key = ("satmon_sem52", "fp32", "greedy", 36, None, None)
    require(trace_map[long_key]["novos_ids"][:6] == trace_map[short_key]["novos_ids"], "Orçamento curto mudou o prefixo greedy.")
    summary = {}
    for precision in ("fp32", "int8_linear"):
        selected = [row for row in full if row["precisao"] == precision]
        require({row["id"] for row in selected} == set(case_map) and len(selected) == 6, "Pareamento greedy incompleto.")
        summary[precision] = {"n": len(selected), "codigos_validos": sum(boolean(r["codigo_valido"]) for r in selected),
                              "codigos_corretos": sum(boolean(r["codigo_correto"]) for r in selected)}
    require(summary == report["greedy_cases"], "Resumo greedy divergente.")
    different = sum(trace_map[(ident, "fp32", "greedy", 36, None, None)]["novos_ids"] != trace_map[(ident, "int8_linear", "greedy", 36, None, None)]["novos_ids"] for ident in case_map)
    require(different == report["paired_greedy_different_tokens_cases"], "Mudanças pareadas de IDs divergentes.")
    preflight = report["preflight"]
    require(preflight["entrada_tokens"] + preflight["pedidos_novos_tokens"] > preflight["limite"] == 512 and preflight["rejeitado_antes_de_inferir"] is True, "Contraprova de orçamento inválida.")

    benchmark = rows(run / "benchmark.csv")
    quant = report["quantizacao"]
    require(quant["status"] == "medida" and len(benchmark) == 6 and quant["rodadas_por_variante"] == 3 and quant["warmup_por_variante"] == 1, "Benchmark pareado incompleto.")
    forced = traces["trajetoria_forcada_ids"]
    require(len(forced) == 17 and decode(forced) == "ISOLATED\nThe peak reaches the cutoff, but no pair confirms an alarm.", "Trajetória fixa diferente.")
    for repetition in (1, 2, 3):
        pair = sorted((r for r in benchmark if int(r["rodada"]) == repetition), key=lambda r: int(r["ordem_na_rodada"]))
        require([r["precisao"] for r in pair] == (["fp32", "int8_linear"] if repetition % 2 else ["int8_linear", "fp32"]), "Ordem pareada diferente.")
        for row in pair:
            require(int(row["tokens_prompt"]) == preflight["entrada_tokens"] == 239 and int(row["tokens_trajetoria"]) == len(forced), "Trabalho do benchmark diferente.")
            prefill, total = float(row["prefill_ms"]), float(row["total_ms"])
            require(total > prefill > 0, "Tempo do benchmark inválido.")
            same(row["tokens_decode_s"], (len(forced) - 1) * 1000 / (total - prefill), "Vazão com N-1 forwards")
    medians = {p: {k: median(float(r[k]) for r in benchmark if r["precisao"] == p)
                   for k in ("prefill_ms", "total_ms", "tokens_decode_s")} for p in summary}
    for precision in medians:
        for key in medians[precision]:
            same(quant["medianas"][precision][key], medians[precision][key], "Mediana pareada")
    fp_bytes, int_bytes = quant["state_dict_fp32_bytes"], quant["state_dict_int8_bytes"]
    require(type(fp_bytes) is type(int_bytes) is int and 0 < int_bytes < fp_bytes, "Tamanhos declarados inválidos.")
    reduction = 100 * (1 - int_bytes / fp_bytes)
    same(quant["reducao_relativa_pct"], reduction, "Redução do state_dict")
    require(quant["embedding_e_lm_head_fp32"] is True and quant["motor"] in quant["motores_torch"] and 0 < quant["pesos_nas_lineares_convertidas"] < quant["fp32_parametros_unicos"] and quant["lineares_convertidas"] > 0, "Declaração de quantização incoerente.")
    invalid_full = [{"id": r["id"], "precision": r["precisao"], "expected": r["esperado"],
                     "first_nonempty_line": next((line.strip() for line in r["texto"].splitlines() if line.strip()), ""), "text": r["texto"]}
                    for r in full if not boolean(r["codigo_valido"])]
    return {"schema": "opevid-m11-1-independent-audit-v1", "verified": True,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(), "run_id": run.name,
        "run_directory": run.relative_to(BASE).as_posix(),
        "method": "Standard-library persisted-artifact audit: Decimal, static ByteLevel decoding, partial probability bounds and scalar benchmark arithmetic. No model/tokenizer API, forward, sampling library, benchmark or download executed.",
        "checks": {"output_case_code_author_model_lock_requirement_hashes": True, "all_seven_snapshot_files_sha256": True,
            "token_ids_static_bytelevel_roundtrip_and_shapes": True, "decimal_separator_and_context_probe_scalars": True,
            "six_case_decimal_decisions_and_greedy_counts": True, "generation_ids_text_budget_stop_consistency": True,
            "six_sampling_combinations_rng_and_partial_trace_bounds": True, "short_long_greedy_prefix": True,
            "six_paired_benchmark_rows_equal_work_and_medians": True, "state_dict_size_ratios_and_percentages": True},
        "checked_hashes": checked_hashes, "model_file_count_verified": len(lock["files"]),
        "decimal_separator_changes": separator, "token_probe_summary": embeddings["probes"],
        "context_embedding_contraproof_recorded": contextual,
        "expected_codes_recomputed_with_decimal": expected_codes, "greedy_summary_recomputed": summary,
        "paired_greedy_different_token_sequences": different, "generation_count": len(generated),
        "stop_reason_counts": {reason: sum(r["parada"] == reason for r in generated) for reason in ("eos", "limite_novos_tokens")},
        "sampled_decisions_count_reconciled": sampling_decisions, "first_step_partial_probability_bounds": partial,
        "sampling_valid_but_wrong": [r for r in sampling if boolean(r["codigo_valido"]) and not boolean(r["codigo_correto"])],
        "short_greedy": next(r for r in generated if r["id"] == "satmon_sem52" and r["modo"] == "greedy" and int(r["teto_novos"]) == 6),
        "invalid_greedy_outputs": invalid_full, "benchmark_medians_recomputed": medians,
        "serialized_state_sizes": {"fp32_bytes_recorded": fp_bytes, "int8_bytes_recorded": int_bytes,
            "fp32_mib": fp_bytes / 2**20, "int8_mib": int_bytes / 2**20, "relative_reduction_percent": reduction,
            "fp32_over_int8_ratio": fp_bytes / int_bytes},
        "median_total_time_reduction_percent": 100 * (1 - medians["int8_linear"]["total_ms"] / medians["fp32"]["total_ms"]),
        "median_decode_throughput_gain_percent": 100 * (medians["int8_linear"]["tokens_decode_s"] / medians["fp32"]["tokens_decode_s"] - 1),
        "synthetic_exact_top2_probabilities": {str(t): {"p_id1": 1 / (1 + math.exp(-1 / t)),
            "p_id2": math.exp(-1 / t) / (1 + math.exp(-1 / t)), "choice_at_u_0_8": 1 if .8 < 1 / (1 + math.exp(-1 / t)) else 2} for t in (1., .5)},
        "limits": {"llm_forward_or_generation_repeated": False, "benchmark_repeated": False,
            "all_real_top8_decisions_independently_recomputed": False,
            "full_logits_or_top8_not_persisted": True, "runner_declared_real_logit_checks": report["top_k_real_decisions_checked"],
            "embedding_context_vectors_recomputed": False, "greedy_generate_api_comparison_repeated": False,
            "prompts_retokenized": False, "serialized_sizes_independently_remeasured": False,
            "temporary_state_dict_files_were_not_persisted": True, "ram_peak_measured": False,
            "production_validity_established": False,
            "note": "Model hashes and persisted scalars support the recorded experiment. Top4 yields only bounds for top8. Runtime vector/quantization assertions are not re-executed; fixed-work medians and six cases do not establish production latency or truth of reasons."}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=RUN)
    parser.add_argument("--model-dir", type=Path, default=SNAPSHOT)
    args = parser.parse_args()
    result = audit(args.run_dir.resolve(), args.model_dir.resolve())
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Auditoria aprovada: seis casos e seis medidas pareadas; run {result['run_id']}.")
    print(f"JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
