"""Registra as nove entregas aplicadas, preservando critérios anteriores.

Executar somente depois da revisão integrada e da auditoria dos artefatos.
As exigências prospectivas são mantidas no monitoramento operacional M06-05.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"reports/fechamento_m00_m09/bloco2_engenharia"
IDS=["M02-06","M02-07","M02-08","M03-01","M03-02","M03-03","M05-01","M05-02","M05-03"]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path): return path.relative_to(ROOT).as_posix()
def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def main():
    config=ROOT/"config/roadmap_m00_m09.json"
    original=config.read_bytes()
    data=json.loads(original)
    snapshot=BASE/"cadastro_antes_alteracao.json"
    if snapshot.exists(): raise FileExistsError("Migração já registrada; preservar histórico.")
    review=ROOT/"docs/roadmap_m00_m09/Revisao_Engenharia_Bloco2.md"
    report=ROOT/"docs/roadmap_m00_m09/Relatorio_Engenharia_Bloco2.md"
    for path in [review,report,BASE/"auditoria_artefatos.json"]:
        if not path.is_file(): raise FileNotFoundError(path)
    audit=json.loads((BASE/"auditoria_artefatos.json").read_text(encoding="utf-8"))
    if audit.get("valid") is not True: raise ValueError("Auditoria dos artefatos precisa estar aprovada.")
    titles={"M02-06":"Aplicar perdas, custos e decisões sobre previsões preservadas",
        "M02-07":"Aplicar a análise estatística a outro horizonte",
        "M02-08":"Executar e interpretar o bootstrap horário pareado",
        "M03-01":"Documentar baselines, disponibilidade e seleção temporal",
        "M03-02":"Explicar previsões locais e medir sensibilidade ao fundo",
        "M03-03":"Selecionar grupos de atributos e avaliar artefato congelado",
        "M05-01":"Avaliar intervalos congelados em snapshot posterior ao ajuste",
        "M05-02":"Calibrar probabilidades e avaliar política causal congelada",
        "M05-03":"Avaliar a rampa de uma hora como alvo distinto"}
    for item in data["items"]:
        ident=item["id"]
        if ident not in IDS: continue
        folder=BASE/ident
        for name in ["protocolo.json","resultado.json","parecer.md"]:
            if not (folder/name).is_file(): raise FileNotFoundError(folder/name)
        item["historico_bloco2"]={k:deepcopy(item.get(k)) for k in ["titulo","natureza","estado","constatacao","portoes","entregaveis","criterios","evidencias","revisao","bloqueio"]}
        item["historico_bloco2"]["snapshot"]=rel(snapshot)
        item["titulo"]=titles[ident]
        item["natureza"]="entrega_de_engenharia"
        item["estado"]="validado"
        item["constatacao"]="Código, execução e análise técnica conferidos em rodada separada; escopo retrospectivo e limites documentados. Não certifica autonomia pessoal nem operação."
        item["portoes"]=["engenharia"]
        item["modo_entrega"]="engenharia_aplicada"
        item["human_response_required"]=False
        item["independent_learning_certified"]=False
        item["operational_approval"]=False
        for c in item["criterios"]:
            c["atendido"]=True
            c["descricao"]=c["descricao"].replace("registrar revisão das respostas","registrar análise e revisão técnicas fornecidas").replace("Defender a decisão sem copiar a conclusão histórica; uma resposta assistida não certifica autonomia.","Explicar a decisão no outro horizonte com os seus números, sem transferir automaticamente a conclusão histórica; solução técnica fornecida não certifica autonomia.")
        if ident=="M05-01":
            item["criterios"][0]["descricao"]="Congelar código e calibrador antes de obter o snapshot reservado, posterior ao ajuste; avaliar cobertura, largura e pinball sem alterar o teste. Não equivale a coleta prospectiva ao vivo."
        if ident=="M05-02":
            item["criterios"][1]["descricao"]="Fixar custo, capacidade causal e limiar antes da obtenção do snapshot reservado; avaliar sem recalibrar; cobertura de intervalos não prova calibração de classe."
        paths=sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() not in [".log",".pyc"] and "__pycache__" not in p.parts)
        common=[review,report,BASE/"protocolo_integrado.json",BASE/"congelamento_avaliacao.json",BASE/"dados_avaliacao/fonte.json",BASE/"verificacao_core_risco.json",BASE/"execucao_fonte.json",BASE/"auditoria_artefatos.json",ROOT/"scripts/auditar_entrega_bloco2.py",ROOT/"scripts/obter_avaliacao_bloco2.py"]
        sources={"M02-06":["notebooks/clinica_decisao_forecast.py","docs/roadmap_m00_m09/Bloco_2_Decisao_Risco.md"],
            "M02-07":["reports/statistical_audit.md","docs/roadmap_m00_m09/Bloco_2_Bootstrap.md"],
            "M02-08":["src/renewable_forecast/weather_gain_uncertainty.py","docs/roadmap_m00_m09/Bloco_2_Bootstrap.md"],
            "M03-01":["docs/model_card.md","notebooks/selecao_atributos_temporal.py"],
            "M03-02":["notebooks/explicacao_local.py","tests/test_bloco2_modelagem.py"],
            "M03-03":["notebooks/selecao_atributos_temporal.py","notebooks/bloco2_modelagem_core.py","tests/test_bloco2_modelagem.py"],
            "M05-01":["notebooks/bloco2_validacao_risco.py","notebooks/bloco2_risco_core.py","tests/test_bloco2_risco.py"],
            "M05-02":["notebooks/bloco2_validacao_risco.py","notebooks/bloco2_risco_core.py","tests/test_bloco2_risco.py"],
            "M05-03":["notebooks/bloco2_validacao_risco.py","notebooks/bloco2_modelagem_core.py","tests/test_bloco2_risco.py"]}
        paths=sorted(set(paths+common+[ROOT/p for p in sources[ident]]))
        item["entregaveis"]=[rel(p) for p in paths if p.parent==folder and p.suffix in [".json",".md",".csv"]]
        item["evidencias"]=[{"path":rel(p),"sha256":sha(p),"kind":"entrega_e_revisao_aplicadas_bloco2"} for p in paths]
        item["revisao"]={"responsavel":"Codex — integração e revisão técnica assistida do agente principal","data":"2026-11-25","parecer":rel(review),"decisao":"aprovado"}
        item["bloqueio"]=None
    monitor=next(i for i in data["items"] if i["id"]=="M06-05")
    monitor["historico_pre_bloco2"]={"criterios":monitor["criterios"].copy(),"depende_de":monitor["depende_de"].copy(),"snapshot":rel(snapshot)}
    monitor["depende_de"]+= [i for i in ["M05-01","M05-02"] if i not in monitor["depende_de"]]
    monitor["criterios"] += [
        {"id":"C3","descricao":"Origem M05-01: em janela prospectiva ao vivo predefinida, observar cobertura, largura, tamanho amostral e quebras de intervalos congelados com chegadas reais e alvos conciliados. Snapshot histórico não encerra este critério.","atendido":False},
        {"id":"C4","descricao":"Origem M05-02: monitorar prospectivamente Brier, confiabilidade, prevalência e custo/taxa de alarmes da política congelada, com capacidade em runtime e reação documentada. Calibração retrospectiva não encerra este critério.","atendido":False}]
    data["modo_de_execucao"]["bloco_ativo"]=2
    data["modo_de_execucao"]["blocos_engenharia_concluidos"]=[1,2]
    data["modo_de_execucao"]["proximo_bloco_planejado"]=3
    data["modo_de_execucao"]["nota_bloco2"]="Nove entregas aplicadas; requisitos prospectivos de M05 preservados como C3/C4 de M06-05 no portão operacional. Os 45 IDs foram mantidos."
    snapshot.write_bytes(original)
    dump(config,data)
    dump(BASE/"migracao_cadastro.json",{"date":"2026-11-25","items":IDS,"preserved_item_count":len(data["items"]),"previous_registry_path":rel(snapshot),"previous_registry_sha256":sha(snapshot),"new_registry_sha256":sha(config),"operational_requirements_retained_at":"M06-05/C3 e C4","independent_learning_certified":False,"operational_approval":False})
    print("Cadastro atualizado: nove entregas de engenharia; operação prospectiva continua pendente.")


if __name__=="__main__": main()
