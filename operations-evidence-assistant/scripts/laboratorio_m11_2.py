"""Compara prompts no desenvolvimento, congela um, então avalia o reservado."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from html import escape
from importlib.metadata import version
import importlib.util
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
from uuid import uuid4

BASE=Path(__file__).resolve().parents[1]
PLAN=BASE/"docs/m11_2/protocolo.json"
DEV=BASE/"data/casos_m11_1.json"
RESERVED=BASE/"data/m11_2/reservado.json"
MODEL_LOCK=BASE/"model/model_lock.json"

sys.path.insert(0,str(BASE/"src"))
from opevid.modelo_local import REV, obter_snapshot, sha


def dump(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def rows_csv(path, rows):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def textos(prompt_id, caso, records, evaluate, messages, func):
    input_messages = messages(prompt_id,caso)
    generated=records(input_messages)
    score=evaluate(generated["texto"],caso,func)
    return {"particao":None,"id":caso["id"],"prompt":prompt_id,"mensagens":input_messages,"fonte":caso,**generated,**score}


def read_cases(path, expected, evidence_validator):
    if sha(path)!=expected:
        raise ValueError(f"Insumo diferente do protocolo congelado: {path.name}.")
    case_rows=json.loads(path.read_bytes())
    result=[]
    for row in case_rows:
        raw={k:row[k] for k in ("id","k","usable","cutoff","s1","s2")}
        evidence_validator(raw)
        result.append(raw)
    if not result or len({c["id"] for c in result})!=len(result):
        raise ValueError("IDs repetidos ou conjunto vazio.")
    return result


def make_generate(plan, snapshot):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(plan["threads"])
    torch.set_num_interop_threads(1)
    tk=AutoTokenizer.from_pretrained(snapshot, trust_remote_code=False,local_files_only=True,use_fast=True)
    net=AutoModelForCausalLM.from_pretrained(snapshot,use_safetensors=True,trust_remote_code=False,local_files_only=True,
            torch_dtype=torch.float32,attn_implementation="eager").cpu().eval()
    config_eos=net.generation_config.eos_token_id
    eos={config_eos} if isinstance(config_eos,int) else set(config_eos)
    budget=min(plan["context_limit"],net.config.max_position_embeddings)

    @torch.inference_mode()
    def generate(messages):
        tokens=tk.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
        if len(tokens)+plan["new_tokens"]>budget:
            raise ValueError(f"Orçamento excedido: {len(tokens)} + {plan['new_tokens']} > {budget}; sem truncamento.")
        x=torch.tensor([tokens],dtype=torch.long)
        start=perf_counter()
        y=net.generate(input_ids=x, attention_mask=torch.ones_like(x), do_sample=False,
                       max_new_tokens=plan["new_tokens"],pad_token_id=tk.pad_token_id,
                       use_cache=True)[0,len(tokens):].tolist()
        ms=1000*(perf_counter()-start)
        return {"texto":tk.decode(y,skip_special_tokens=True,clean_up_tokenization_spaces=False),
                "tokens_entrada":len(tokens),"tokens_novos":len(y),"tempo_geracao_ms":ms,
                "parada":"eos" if y[-1] in eos else "limite_novos_tokens"}
    return generate


def resumo(rows, part, variant):
    t=[r["etapa"] for r in rows]
    json_count=sum(x!="json_invalido" for x in t)
    schema=sum(x in {"divergencia","fiel"} for x in t)
    faithful=t.count("fiel")
    return {"particao":part,"prompt":variant,"casos":len(t),"json_ok":json_count,"esquema_ok":schema,
            "fiel":faithful,"fiel_entre_esquema":faithful/schema if schema else None,
            "fallback":sum(r["publicado"]["origem"]=="fallback" for r in rows),
            "publicado_conferido":len(t),"tokens_entrada":sum(r["tokens_entrada"] for r in rows),
            "tokens_novos":sum(r["tokens_novos"] for r in rows)}


def escolha(metrics,variants):
    rank=lambda v:(-v["fiel"],-v["esquema_ok"],v["tokens_novos"],variants.index(v["prompt"]))
    return min(metrics,key=rank)["prompt"]


def page(path, run_id, totals, attempts, fixtures, decision):
    def tab(records,cols):
        content="<tr>"+"".join(f"<th>{escape(col)}</th>" for col in cols)+"</tr>"
        for r in records:
            content+="<tr>"+"".join(f"<td>{escape(str(r[col]) if r[col] is not None else '—')}</td>" for col in cols)+"</tr>"
        return "<div><table>"+content+"</table></div>"
    head='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>M11.2 — Relatório e evidência</title>
<style>body{font:16px/1.5 system-ui;max-width:1120px;margin:2rem auto;padding:0 20px;color:#173045}
td,th{padding:.48rem;border:1px solid #cdd8de}table{border-collapse:collapse;font-size:14px}div{overflow:auto}
th{background:#e9f4f4;text-align:left}code,pre{white-space:pre-wrap;background:#f1f4f6}pre{padding:.7rem;overflow-wrap:anywhere}summary{cursor:pointer}</style>
<h1>M11.2 — JSON, esquema e fidelidade</h1>
<p>Os números abaixo contam propostas brutas; fallback é resposta em código. O reservado é sintético, e somente
o prompt escolhido no desenvolvimento foi executado nele.</p>'''
    cols=("particao","prompt","casos","json_ok","esquema_ok","fiel","fallback","publicado_conferido","tokens_entrada","tokens_novos")
    result=[head,tab(totals,cols),f"<p>Prompt congelado: <b>{escape(decision['prompt'])}</b>. Execução: {escape(run_id)}.</p>",
            "<h2>Contraprovas fora da avaliação dos prompts</h2>",tab(fixtures,("teste","etapa","erros")),
            "<h2>Tentativas em desenvolvimento</h2><p>Clique para comparar uma saída bruta com a resposta publicada.</p>"]
    for a in attempts:
        if a["particao"]!="desenvolvimento":
            continue
        label=f"{a['id']} · {a['prompt']} · {a['etapa']}"
        compact=json.dumps(a["publicado"],ensure_ascii=False,indent=2)
        result.append(f"<details><summary>{escape(label)}</summary><p>Erros: {escape(', '.join(a['erros'])) or '—'}</p>"
                      f"<pre>{escape(a['texto'])}</pre><pre>{escape(compact)}</pre></details>")
    result.append("<p>O código final repete a regra determinística; os 100% publicados não representam acerto do LLM. "
                  "O relatório HTML não expõe as tentativas individuais do reservado; os arquivos locais as preservam. "
                  "Nenhum comando ou alarme é acionado.</p>")
    path.write_text("\n".join(result)+"\n",encoding="utf-8")


def get_func(path, default):
    if path is None:
        return default
    spec=importlib.util.spec_from_file_location("m11_2_fidelidade_autoral",path)
    if spec is None or spec.loader is None:
        raise ValueError("Módulo autoral não carregável.")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn=getattr(mod,"conferir_fidelidade",None)
    if not callable(fn):
        raise ValueError("Defina conferir_fidelidade no seu arquivo .py.")
    return fn


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autoria",type=Path)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--model-dir",type=Path)
    parser.add_argument("--pydantic-dir",type=Path)
    parser.add_argument("--verificar",action="store_true")
    args=parser.parse_args(argv)
    if args.pydantic_dir:
        sys.path.insert(0,str(args.pydantic_dir))
    from opevid.estruturado_m11_2 import avaliar_resposta, conferir_fidelidade, esperado_da_fonte, Relatorio
    from opevid.contraprovas_m11_2 import exercitar
    from opevid.prompts_m11_2 import mensagens, VARIANTES

    fn=get_func(args.autoria,conferir_fidelidade)
    fixtures=exercitar(fn)
    print(f"{len(fixtures)} contraprovas aprovadas (JSON, esquema, fidelidade e saída final).",flush=True)
    if args.verificar:
        return 0
    plan=json.loads(PLAN.read_bytes())
    if (plan["schema"]!="opevid-m11-2-protocol-v1" or plan["model_revision"]!=REV or tuple(plan["variants"])!=VARIANTES
            or plan["selection"]!=["max_fiel","max_esquema_ok","min_novos_tokens","ordem_fixa_do_protocolo"]
            or not plan["reserved_is_synthetic"] or not plan["no_retries_or_repair"]):
        raise ValueError("Protocolo não corresponde à rodada.")
    dev=read_cases(DEV,plan["dev_sha256"],esperado_da_fonte)
    local=args.model_dir or BASE/".cache/m11_1"/REV
    snapshot,lock=obter_snapshot(MODEL_LOCK,local,baixar=args.model_dir is None)
    print("Rodando SmolLM2 FP32, 2 threads, greedy. Mesmos casos e orçamento nos dois prompts.",flush=True)
    infer=make_generate(plan,snapshot)
    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    out=args.output_dir.resolve()/run_id
    out.mkdir(parents=True,exist_ok=False)
    by={"zero_shot":[],"um_exemplo":[]}
    attempts=[]
    checker_calls=0
    for i,case in enumerate(dev):
        variants=VARIANTES if i%2==0 else tuple(reversed(VARIANTES))
        for prompt in variants:
            result=textos(prompt,case,infer,avaliar_resposta,mensagens,fn)
            result["particao"]="desenvolvimento"
            attempts.append(result)
            by[prompt].append(result)
            checker_calls+=result["etapa"] in {"fiel","divergencia"}
            print(f"Dev {case['id']} | {prompt}: {result['etapa']}",flush=True)
    metrics=[resumo(by[v],"desenvolvimento",v) for v in VARIANTES]
    winner=escolha(metrics,VARIANTES)
    decision={
        "schema":"opevid-m11-2-prompt-lock-v1","run_id":run_id,"prompt":winner,
        "selecao_em":"desenvolvimento","criterios":plan["selection"],"desenvolvimento":metrics.copy(),
        "input_dev_sha256":plan["dev_sha256"],"protocol_sha256":sha(PLAN),
        "prompt_code_sha256":sha(BASE/"src/opevid/prompts_m11_2.py"),"reservado_lido_antes":False,
        "congelado_em":datetime.now(timezone.utc).isoformat(),
    }
    lock_path=out/"decisao_prompt.json"
    dump(lock_path,decision)
    locked_sha=sha(lock_path)
    chosen=json.loads(lock_path.read_bytes())["prompt"]
    print(f"Prompt {chosen} congelado. Lendo reservado sintético só agora.",flush=True)
    reserved=read_cases(RESERVED,plan["reserved_sha256"],esperado_da_fonte)
    if {r["id"] for r in dev}&{r["id"] for r in reserved}:
        raise ValueError("Os IDs de desenvolvimento e reservado se sobrepõem.")
    hold=[]
    for case in reserved:
        result=textos(chosen,case,infer,avaliar_resposta,mensagens,fn)
        result["particao"]="reservado"
        hold.append(result)
        checker_calls+=result["etapa"] in {"fiel","divergencia"}
        print(f"Reservado {case['id']}: {result['etapa']}",flush=True)
    attempts.extend(hold)
    metrics.append(resumo(hold,"reservado",chosen))
    if sha(lock_path)!=locked_sha:
        raise ValueError("O arquivo de escolha mudou durante o reservado.")
    rows_csv(out/"metricas.csv",metrics)
    rows_csv(out/"tentativas.csv",[{**{k:r[k] for k in (
        "particao","id","prompt","etapa","tokens_entrada","tokens_novos","parada","tempo_geracao_ms")},
        "erros":"|".join(r["erros"]),"origem_publicada":r["publicado"]["origem"]} for r in attempts])
    with (out/"tentativas.jsonl").open("w",encoding="utf-8",newline="\n") as f:
        for r in attempts:
            f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+"\n")
    dump(out/"contraprovas.json",fixtures)
    dump(out/"esquema.json",Relatorio.model_json_schema())
    page(out/"relatorio.html",run_id,metrics,attempts,fixtures,decision)
    receipt={"schema":"opevid-m11-2-result-v1","run_id":run_id,"completed":True,
        "os":platform.system(),"python":sys.version.split()[0],"versions":{name:version(name) for name in (
            "torch","transformers","tokenizers","pydantic","pydantic-core")},
        "mode":"cpu_fp32_greedy","threads":plan["threads"],"model_revision":REV,
        "model_weights_sha256":lock["files"]["model.safetensors"]["sha256"],"protocol_sha256":sha(PLAN),
        "inputs_sha256":{"dev":plan["dev_sha256"],"reservado":plan["reserved_sha256"],"model_lock":sha(MODEL_LOCK)},
        "decision_sha256":locked_sha,"prompt_escolhido":chosen,
        "autor_sha256":sha(args.autoria) if args.autoria else None,"contraprovas":len(fixtures),
        "tentativas_tipadas_avaliadas_pelo_validador":checker_calls,"comparou_autoria_com_referencia":args.autoria is not None,
        "tentativas_geradas":len(attempts),"reservado_lido_depois_de_congelar":True,
        "reservado_sintetico":True,"treino":False,"operational_approval":False,
        "metricas":metrics,"output_sha256":{p.name:sha(p) for p in out.iterdir() if p.is_file()},
        "code_sha256":{name:sha(BASE/name) for name in [
            "scripts/executar_m11_2.py","scripts/laboratorio_m11_2.py",
            "src/opevid/estruturado_m11_2.py","src/opevid/contraprovas_m11_2.py","src/opevid/prompts_m11_2.py"]},
    }
    dump(out/"resultado.json",receipt)
    print("Partição | Prompt | JSON | Esquema | Fiel | Fallback")
    for m in metrics:
        print(f"{m['particao']} | {m['prompt']} | {m['json_ok']}/{m['casos']} | "
              f"{m['esquema_ok']}/{m['casos']} | {m['fiel']}/{m['casos']} | {m['fallback']}/{m['casos']}")
    print(f"Relatório: {out/'relatorio.html'}",flush=True)
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (OSError,ValueError,NotImplementedError) as exc:
        print(f"M11.2: {exc}",file=sys.stderr)
        raise SystemExit(1) from None
