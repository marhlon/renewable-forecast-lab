"""Geração local, inspeção do vocabulário e comparação pareada FP32/INT8."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from html import escape
from importlib.metadata import version
import json
from pathlib import Path
import platform
import random
from statistics import median
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import uuid4

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from executar_m11_1 import BASE, load_picker
from opevid.amostragem import (cabe_no_contexto, candidatos_top_k, conferir_picker,
                              peso_top_k, selecionar_token_top_k)
from opevid.contrato import decidir, ler_codigo
from opevid.modelo_local import REV, obter_snapshot, sha

CASE_PATH = BASE / "data/casos_m11_1.json"
LOCK_PATH = BASE / "model/model_lock.json"
CONTEXT_LIMIT = 512
FULL = 36
SHORT = 6
TEMPERATURES = (.35, 1.2)
SEEDS = (17, 29, 41)
TOP_K = 8
TOKENS_PROBE = (
    "Geração caiu; corte 0,719944.",
    "Geracao caiu; corte 0,719944.",
    "Geração caiu; corte 0.719944.",
    "An alarm is rejected.\nStatus:",
    "An alarm is allowed.\nStatus:",
)
SYSTEM = "You write evidence-based monitoring notes. Use only the supplied record. Do not infer a physical cause."


def escrever_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def escrever_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def ids_do_caso(tokenizer, caso):
    info = {k: caso[k] for k in ("usable", "k", "cutoff", "s1", "s2")}
    info = json.dumps(info, ensure_ascii=False, separators=(",", ":"))
    prompt = (
        "Classify the record using exactly one code on the first line and a short reason on the second.\n"
        "Use these rules in order:\n"
        "INSUFFICIENT: usable is false.\n"
        "BELOW: usable is true and s1 < cutoff.\n"
        "ISOLATED: s1 >= cutoff, k is 2, and s2 is null or s2 < cutoff.\n"
        "ELIGIBLE: s1 >= cutoff and k is 1, or k is 2 and s2 >= cutoff.\n"
        "ELIGIBLE means the rule can confirm a reading sequence; it does not identify a detected incident.\n"
        f"Record: {info}"
    )
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    ids = tokenizer.encode(text, add_special_tokens=False)
    direct = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    if ids != direct:
        raise ValueError("Renderização e tokenização do chat não coincidem.")
    return ids, text


def medir_representacoes(model, tokenizer, out):
    pieces, texts = [], []
    last = []
    for j, text in enumerate(TOKENS_PROBE):
        token_ids = tokenizer.encode(text, add_special_tokens=False)
        decoded = tokenizer.decode(token_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if decoded != text:
            raise ValueError("O tokenizer não reconstruiu o texto de controle.")
        tokens = torch.tensor([token_ids], dtype=torch.long)
        emb = model.get_input_embeddings()(tokens)
        texts.append({"probe": j, "texto": text, "caracteres": len(text), "bytes_utf8": len(text.encode("utf-8")),
                      "tokens": len(token_ids), "forma_embeddings": list(emb.shape), "round_trip": True})
        for pos, i in enumerate(token_ids):
            pieces.append({"probe": j, "posicao": pos, "token_id": i, "peca_bpe": tokenizer.convert_ids_to_tokens(i),
                           "decode_individual": tokenizer.decode([i], clean_up_tokenization_spaces=False),
                           "norma_vetor_entrada": float(emb[0, pos].norm())})
        if j >= 3:
            contextual = model(tokens, output_hidden_states=True, use_cache=False, logits_to_keep=1)
            last.append((token_ids[-1], emb[0, -1], contextual.hidden_states[-1][0, -1]))
    ida, a, ha = last[0]
    idb, b, hb = last[1]
    input_delta = float((a-b).abs().max())
    final_delta = float((ha-hb).abs().max())
    if ida != idb or input_delta != 0 or final_delta <= 0:
        raise ValueError("O mesmo token final deveria ter entrada igual e representação contextual distinta.")
    result = {"mesmo_token_final": tokenizer.convert_ids_to_tokens(ida), "token_id": ida,
              "delta_max_entrada": input_delta, "delta_max_contextual": final_delta,
              "cosseno_contextual": float(torch.nn.functional.cosine_similarity(ha, hb, dim=0))}
    escrever_csv(out / "tokens.csv", pieces)
    escrever_json(out / "embeddings.json", {"probes": texts, "contraprova_contexto": result})
    return texts, result


def decode(model, tokenizer, ids, *, limite, max_new, ends, modo, picker=None, temperatura=None, semente=None):
    if not cabe_no_contexto(len(ids), max_new, limite):
        raise ValueError(f"Orçamento excedido: {len(ids)} de entrada + {max_new} novos > {limite}.")
    if modo not in {"greedy", "top_k"}:
        raise ValueError("Decodificação desconhecida.")
    new, trail = [], []
    rng = random.Random(semente) if modo == "top_k" else None
    cache = None
    next_input = torch.tensor([ids], dtype=torch.long)
    start = perf_counter()
    first_at = None
    reason = "limite_novos_tokens"
    for step in range(max_new):
        calc = model(next_input, use_cache=True, past_key_values=cache, logits_to_keep=1)
        cache = calc.past_key_values
        logits = calc.logits[0, -1]
        if step < 2:
            top_trace = candidatos_top_k(tuple(logits.tolist()), 4)
        if rng is None:
            choice = int(logits.argmax().item())
            u = None
        else:
            u = rng.random()
            values = tuple(logits.tolist())
            choice = picker(values, temperatura=temperatura, k=TOP_K, u=u)
            if type(choice) is not int or choice != selecionar_token_top_k(values, temperatura=temperatura, k=TOP_K, u=u):
                raise ValueError(f"A autoria divergiu da referência com logits reais no passo {step}.")
        if first_at is None:
            first_at = perf_counter()
        new.append(choice)
        if step < 2:
            trail.append({
                "passo": step+1, "u": u, "id_escolhido": choice,
                "top4": [{"id": i, "peca": tokenizer.convert_ids_to_tokens(i), "logit": float(logits[i])}
                         for i in top_trace],
            })
        if choice in ends:
            reason = "eos"
            break
        next_input = torch.tensor([[choice]], dtype=torch.long)
    elapsed = perf_counter()-start
    return {
        "entrada_tokens": len(ids), "novos_tokens": len(new), "teto_novos": max_new,
        "parada": reason, "ttft_ms_inclui_selecao": 1000*(first_at-start),
        "tempo_decode_total_ms": 1000*elapsed, "texto": tokenizer.decode(
            new, skip_special_tokens=True, clean_up_tokenization_spaces=False),
        "ids": new, "trilha": trail,
    }


def mesma_trajetoria(model, ids, forced):
    """Roda o mesmo prefill e o mesmo número de forwards de um token."""
    assert len(forced) >= 2
    x = torch.tensor([ids], dtype=torch.long)
    start = perf_counter()
    calc = model(x, use_cache=True, logits_to_keep=1)
    prefill = perf_counter()-start
    # O primeiro logit da extensão sai no prefill. Restam N−1 passos.
    for i in forced[:-1]:
        calc = model(torch.tensor([[i]], dtype=torch.long), past_key_values=calc.past_key_values,
                     use_cache=True, logits_to_keep=1)
    total = perf_counter()-start
    return {"tokens_prompt": len(ids), "tokens_trajetoria": len(forced),
            "prefill_ms": 1000*prefill, "total_ms": 1000*total,
            "tokens_decode_s": (len(forced)-1)/(total-prefill)}


def medir_quantizacao(model, base_case, input_ids, forced, out):
    supported = torch.backends.quantized.supported_engines
    engine = next((e for e in ("x86", "fbgemm", "onednn") if e in supported), None)
    with TemporaryDirectory(prefix="tamanho_pesos_", dir=out) as tmp:
        path = Path(tmp)/"state.pt"
        torch.save(model.state_dict(), path)
        fp32_size = path.stat().st_size
        path.unlink()
        if engine is None:
            return None, [], {
                "status": "backend_indisponivel", "motores_torch": list(supported),
                "state_dict_fp32_bytes": fp32_size,
            }
        torch.backends.quantized.engine = engine
        nomes = {name for name, m in model.named_modules() if isinstance(m, torch.nn.Linear)
                 and name != "lm_head"}
        original = sum(model.get_submodule(name).weight.numel() for name in nomes)
        count = sum(p.numel() for p in model.parameters())
        start = perf_counter()
        quant = torch.ao.quantization.quantize_dynamic(model, qconfig_spec=nomes, dtype=torch.qint8, inplace=False)
        elapsed = perf_counter()-start
        replacements = {name for name, m in quant.named_modules()
                        if isinstance(m, torch.ao.nn.quantized.dynamic.Linear)}
        if nomes != replacements or not nomes or any(
                quant.get_submodule(name).weight().dtype != torch.qint8 for name in nomes):
            raise ValueError("Não foi possível comprovar a conversão das camadas esperadas.")
        if quant.lm_head.weight.dtype != torch.float32 or quant.get_input_embeddings().weight.dtype != torch.float32:
            raise ValueError("Cabeça e embeddings devem continuar FP32.")
        torch.save(quant.state_dict(), path)
        q_size = path.stat().st_size
    models = {"fp32": model, "int8_linear": quant}
    warm_ids = input_ids[base_case]
    for m in models.values():
        mesma_trajetoria(m, warm_ids, forced[:3])
    rows = []
    for rep in range(1, 4):
        ordered = list(models) if rep % 2 else list(reversed(models))
        for execution_order, p in enumerate(ordered, start=1):
            rows.append({"precisao": p, "rodada": rep, "ordem_na_rodada": execution_order,
                         **mesma_trajetoria(models[p], warm_ids, forced)})
    return quant, rows, {
        "status": "medida", "motor": engine, "motores_torch": list(supported),
        "fp32_parametros_unicos": count, "pesos_nas_lineares_convertidas": original,
        "lineares_convertidas": len(nomes), "embedding_e_lm_head_fp32": True,
        "state_dict_fp32_bytes": fp32_size, "state_dict_int8_bytes": q_size,
        "reducao_relativa_pct": 100*(1-q_size/fp32_size), "conversao_ms_fora_da_medicao": 1000*elapsed,
        "caso_bench": base_case, "rodadas_por_variante": 3, "warmup_por_variante": 1,
        "medianas": {p: {key: median(r[key] for r in rows if r["precisao"]==p)
                        for key in ("prefill_ms","total_ms","tokens_decode_s")} for p in models},
    }


def avaliar_caso(case, result):
    tag = ler_codigo(result["texto"])
    return {"id": case["id"], "tipo": case["tipo"], "esperado": decidir(case),
            "codigo": tag, "codigo_valido": tag is not None, "codigo_correto": tag == decidir(case),
            **{k: v for k,v in result.items() if k not in {"trilha", "ids"}}}


def pagina(out, samples, bench, text_probes, context, result):
    def tabela(records, names):
        names = tuple(names)
        head = "".join(f"<th>{escape(k)}</th>" for k in names)
        body = "".join("<tr>"+"".join(f"<td>{escape(f'{x[k]:.4f}' if isinstance(x[k], float) else str(x[k]))}</td>"
                                      for k in names)+"</tr>" for x in records)
        return "<div class='table'><table><thead><tr>"+head+"</tr></thead><tbody>"+body+"</tbody></table></div>"
    partes = [
        """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>M11.1 — Geração local</title>
<style>body{font:16px/1.5 system-ui;max-width:1120px;margin:2rem auto;padding:0 20px;color:#163047}
table{border-collapse:collapse;font-size:14px}td,th{padding:.5rem;border:1px solid #c8d7e0;white-space:pre-wrap}
th{background:#e7f3f3}.table{overflow:auto}code{background:#edf4f7;padding:1px 4px}.note{background:#eff5f7;padding:.8rem}</style>
<h1>M11.1 — O que seu modelo gerou de fato?</h1>
<p>Mesmas seis evidências, regra Python verificável e geração autoregressiva local. O código da primeira linha é o
único campo julgado automaticamente; a razão em texto continua sujeita à revisão.</p>""",
        "<h2>Entrada: texto, tokens e vetores</h2>",
        tabela(text_probes, ("probe","texto","caracteres","bytes_utf8","tokens","forma_embeddings")),
        f"<p>Token final id {context['token_id']}: diferença de entrada {context['delta_max_entrada']:.4g}; "
        f"diferença após as camadas {context['delta_max_contextual']:.4g}.</p>",
        "<h2>Saídas brutas (greedy, com todos os casos)</h2>",
        tabela([r for r in samples if r["modo"]=="greedy" and r["teto_novos"]==FULL],
            ("id","precisao","esperado","codigo","codigo_correto","novos_tokens","parada","texto")),
        "<h2>Uma evidência, orçamentos e decodificações diferentes</h2>",
        tabela([r for r in samples if r["modo"]=="top_k" or r["teto_novos"]==SHORT],
            ("id","modo","temperatura","semente","esperado","codigo","novos_tokens","parada","texto")),
        "<h2>Comparação de execução com trajetória fixada</h2>",
        tabela(bench, ("precisao","rodada","tokens_prompt","tokens_trajetoria","prefill_ms","total_ms","tokens_decode_s")) if bench
            else "<p>Backend INT8 indisponível nesta máquina; não há comparação pareada.</p>",
        "<p class='note'>Tamanho do state_dict não mede RAM. Tempo de carregar, baixar e converter fica fora da "
        "comparação com trajetória fixa. Seis casos explorados não constituem teste de produção. Nenhuma saída é "
        "usada para comandar equipamentos ou alterar alarmes.</p>",
        f"<p>Execução: <code>{escape(result['run_id'])}</code>. Dados completos: <code>resultado.json</code>, "
        "<code>geracoes.csv</code>, <code>trilha_tokens.json</code>, <code>benchmark.csv</code> se disponível.</p>",
    ]
    (out/"relatorio.html").write_text("\n".join(partes)+"\n",encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autoria", type=Path)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    picker = load_picker(args.autoria)
    tiny = conferir_picker(picker)
    snapshot = args.model_dir or BASE / ".cache/m11_1" / REV
    snapshot, lock = obter_snapshot(LOCK_PATH, snapshot, baixar=args.model_dir is None)
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    print("Carregando SmolLM2 em CPU. Sem API externa ou ajuste de pesos.", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, use_fast=True, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(snapshot, use_safetensors=True, local_files_only=True,
                 trust_remote_code=False, torch_dtype=torch.float32, attn_implementation="eager").cpu().eval()
    id_end = model.generation_config.eos_token_id
    ends = {id_end} if isinstance(id_end, int) else set(id_end)
    limit = min(CONTEXT_LIMIT, model.config.max_position_embeddings)
    cases = json.loads(CASE_PATH.read_bytes())
    case_id = "satmon_sem52"
    case_focus = next(r for r in cases if r["id"]==case_id)
    inputs = {r["id"]: ids_do_caso(tokenizer,r) for r in cases}
    ids = {k:v[0] for k,v in inputs.items()}
    i_focus = ids[case_id]
    if not all(cabe_no_contexto(len(x), FULL, limit) for x in ids.values()):
        raise ValueError("Caso do protocolo excedeu o orçamento.")
    guard = {"entrada_tokens": len(i_focus), "pedidos_novos_tokens": limit-len(i_focus)+1, "limite": limit}
    # Passar modelo None garante que a recusa ocorra antes do forward.
    try:
        decode(None, None, i_focus, limite=limit, max_new=guard["pedidos_novos_tokens"], ends=ends, modo="greedy")
    except ValueError as ex:
        guard.update(rejeitado_antes_de_inferir=True,motivo=str(ex))
    else:
        raise ValueError("O teste de excesso deveria ter sido recusado.")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{ts}_{uuid4().hex[:8]}"
    out = args.output_dir.resolve()/run_id
    out.mkdir(parents=True,exist_ok=False)
    samples, traces = [], []
    comparisons = 0

    def testar(m, precision, case, mode, new, t=None, seed=None):
        nonlocal comparisons
        g = decode(m, tokenizer, ids[case["id"]], limite=limit, max_new=new, ends=ends, modo=mode,
                   picker=picker, temperatura=t, semente=seed)
        if mode=="top_k":
            comparisons += len(g["ids"])
        samples.append({"precisao": precision,"modo": mode,"temperatura": t,"semente": seed,**avaliar_caso(case,g)})
        traces.append({"id":case["id"],"precisao":precision,"modo":mode,"teto_novos":new,
                       "temperatura":t,"semente":seed,"novos_ids":g["ids"],"dois_primeiros_passos":g["trilha"]})
        return g

    with torch.inference_mode():
        token_texts, ctx = medir_representacoes(model, tokenizer, out)
        print("Tokens e embeddings conferidos. Testando decodificação, orçamento e sementes.", flush=True)
        initial = testar(model,"fp32",case_focus,"greedy",SHORT)
        x = torch.tensor([i_focus],dtype=torch.long)
        official = model.generate(input_ids=x,attention_mask=torch.ones_like(x),do_sample=False,
                                  max_new_tokens=SHORT,pad_token_id=tokenizer.pad_token_id)[0,len(i_focus):].tolist()
        if official != initial["ids"]:
            raise ValueError("O greedy manual divergiu da API generate na contraprova.")
        for t in TEMPERATURES:
            for seed in SEEDS:
                testar(model,"fp32",case_focus,"top_k",FULL,t,seed)
        print("Quantização: comparando a mesma trajetória (3 rodadas aquecidas por variante).",flush=True)
        forced = tokenizer.encode("ISOLATED\nThe peak reaches the cutoff, but no pair confirms an alarm.",
                                  add_special_tokens=False)
        quant, bench, q_metrics = medir_quantizacao(model,case_id,ids,forced,out)
        for j,c in enumerate(cases):
            pair = [("fp32",model)]
            if quant is not None:
                pair.append(("int8_linear",quant))
            for label, m in (pair if j % 2 == 0 else reversed(pair)):
                testar(m,label,c,"greedy",FULL)
            print("Caso conferido:", c["id"], flush=True)
    write_case = [{"id": c["id"], "tipo": c["tipo"], "origem": c["origem"],"regra_python": decidir(c)} for c in cases]
    escrever_csv(out/"baseline_regra.csv",write_case)
    escrever_csv(out/"geracoes.csv",samples)
    if bench:
        escrever_csv(out/"benchmark.csv",bench)
    escrever_json(out/"trilha_tokens.json",{"prompts_renderizados": {k:v[1] for k,v in inputs.items()},
                   "trajetoria_forcada_ids": forced,"geracoes":traces})
    full = [r for r in samples if r["modo"]=="greedy" and r["teto_novos"]==FULL]
    resumo = {}
    for label in sorted({r["precisao"] for r in full}):
        rr=[r for r in full if r["precisao"]==label]
        resumo[label]={"n":len(rr),"codigos_validos":sum(r["codigo_valido"] for r in rr),
                       "codigos_corretos":sum(r["codigo_correto"] for r in rr)}
    fp = {r["id"]:r["novos_ids"] for r in traces if r["modo"]=="greedy" and r["teto_novos"]==FULL and r["precisao"]=="fp32"}
    q = {r["id"]:r["novos_ids"] for r in traces if r["modo"]=="greedy" and r["precisao"]=="int8_linear"}
    receipt = {
        "schema":"opevid-m11-1-result-v1","run_id":run_id,"completed":True,
        "model": {"repository":lock["repository"],"revision":REV,"license":lock["license"],
                  "weights_sha256":lock["files"]["model.safetensors"]["sha256"],
                  "lock_sha256":sha(LOCK_PATH),"local_context_limit":limit,
                  "model_max_position_embeddings":model.config.max_position_embeddings,
                  "hidden_size":model.config.hidden_size,"vocab_size":model.config.vocab_size},
        "versions":{pkg:version(pkg) for pkg in ("torch","transformers","tokenizers","safetensors")},
        "python":sys.version.split()[0],"os":platform.system(),"arch":platform.machine(),"threads":torch.get_num_threads(),
        "author_sha256":sha(args.autoria) if args.autoria else None,"small_sampling_checks":tiny,
        "top_k_real_decisions_checked":comparisons,
        "authorship_checked_on_real_logits":args.autoria is not None,"greedy_generate_ids_agree":True,"preflight":guard,
        "case_set_sha256":sha(CASE_PATH),"deterministic_rule_cases":len(cases),"greedy_cases":resumo,
        "paired_greedy_different_tokens_cases":sum(fp[k]!=q[k] for k in q) if q else None,
        "quantizacao":q_metrics,"systems":"6 casos de desenvolvimento/ensino, não teste externo",
        "training":False,"operational_approval":False,
        "code_sha256":{p.relative_to(BASE).as_posix():sha(p) for p in (Path(__file__),
           BASE/"scripts/executar_m11_1.py",BASE/"src/opevid/amostragem.py",
           BASE/"src/opevid/contrato.py",BASE/"src/opevid/modelo_local.py")},
    }
    pagina(out,samples,bench,token_texts,ctx,receipt)
    receipt["output_sha256"]={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    escrever_json(out/"resultado.json",receipt)
    print("Greedy, código correto:",{k:f"{v['codigos_corretos']}/{v['n']}" for k,v in resumo.items()},flush=True)
    print("INT8:",q_metrics["status"],flush=True)
    print(f"Relatório: {out/'relatorio.html'}",flush=True)
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, NotImplementedError) as ex:
        print(f"M11.1: {ex}",file=sys.stderr)
        raise SystemExit(1) from None
