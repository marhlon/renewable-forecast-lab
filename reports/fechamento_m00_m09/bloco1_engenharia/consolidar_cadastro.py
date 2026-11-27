"""Consolidação única do modo de engenharia autorizado em 25/11/2026.

Não executa modelos nem aprova operação. O snapshot anterior deve continuar
idêntico ao cadastro corrente; o script recusa reaplicar a decisão silenciosamente.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
TARGET=ROOT/"config/roadmap_m00_m09.json"
SNAPSHOT=BASE/"cadastro_antes_alteracao.json"
REVIEW="docs/roadmap_m00_m09/Revisao_Engenharia_Bloco1.md"
REPORT="docs/roadmap_m00_m09/Relatorio_Engenharia_Bloco1.md"
LINEAGE="docs/roadmap_m00_m09/Origem_Dados_e_Previsoes.md"

APPLIED={
 "M00-01": ("Formalizar o fluxo e a adaptação temporal",
   ["Rastrear o fluxo existente e documentar origem, histórico, alvo, janela e disponibilidade da configuração aplicada.",
    "Conferir os relógios da adaptação e registrar o que muda no contrato, sem reidentificar o modelo h+1 como modelo h+12."]),
 "M01-01": ("Conferir JOIN, nulos, duplicidades e janelas SQL",
   ["Fornecer e executar as consultas dos casos controlados, com reconciliação SQL/pandas e contas de referência.",
    "Documentar granularidade, quarentena, calendário parcial, zeros, médias nulas e LAG por entidade."]),
 "M01-02": ("Executar e reconciliar o diagnóstico SQL do mês real",
   ["Fixar o recorte e preservar fonte, calendário e identidade antes da análise aplicada.",
    "Reconciliar o mês inteiro em SQL/pandas e aplicar a janela antes do filtro com contexto anterior; publicar contagens, médias e limites."]),
 "M02-01": ("Aplicar probabilidade condicional e distribuições",
   ["Executar a tabela de contingência e Bayes com conferência racional dos totais e da probabilidade.",
    "Documentar taxa-base, unidade, distribuição e dependência e separar o cenário calculado de uma avaliação operacional."]),
 "M02-02": ("Calcular estimativas e intervalos com seus pressupostos",
   ["Derivar e executar média, variância, erro-padrão, IC da média e intervalo de previsão, com conferência analítica.",
    "Conferir o cenário AR1 e explicar a diferença entre contagem de linhas e tamanho efetivo, sem atribuir a dependência sintética ao ONS."]),
 "M02-03": ("Aplicar hipóteses e controle de múltiplas comparações",
   ["Preservar hipótese, efeito mínimo e regras fixadas antes do cálculo; executar o teste sobre os blocos fornecidos.",
    "Separar as duas famílias de perguntas, aplicar Bonferroni e publicar decisões e limites sem fabricar as horas ausentes."]),
 "M02-04": ("Conferir regressão, gradiente e estabilidade",
   ["Conferir OLS/Ridge, shapes, equações, gradiente e o fator nλ contra contas analíticas.",
    "Executar passos predefinidos de taxa, conferir posto/direção nula e documentar limites de inferência e generalização."]),
 "M07-04": ("Consolidar a análise técnica do plano e da medição",
   ["Preservar as correções E108 e fornecer a análise aplicada da janela, versionamento, cronômetro e broadcast.",
    "Delimitar o que o plano inicial e os tempos permitem afirmar, sem repetir Spark/Databricks ou atribuir a análise ao usuário."])
}
PRIOR={"M02-05","M04-01","M06-01","M08-01","M09-01","M09-03"}

def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()
def relative(path):
    return path.relative_to(ROOT).as_posix()
def main():
    if TARGET.read_bytes()!=SNAPSHOT.read_bytes():
        raise ValueError("Cadastro já mudou desde o snapshot. Rever o diff; não reaplicar automaticamente.")
    for path in (ROOT/REVIEW,ROOT/REPORT,ROOT/LINEAGE,BASE/"modo_entrega.json",BASE/"fontes_manifesto.json"):
        if not path.is_file():
            raise FileNotFoundError(path)
    data=json.loads(TARGET.read_text(encoding="utf-8"))
    for item in data["items"]:
        if item["id"] not in APPLIED and item["id"] not in PRIOR:
            continue
        item["historico_antes_modo_engenharia"]={
            "estado":item["estado"],"titulo":item["titulo"],"natureza":item["natureza"],
            "portoes":deepcopy(item["portoes"]),"criterios":deepcopy(item["criterios"]),
            "entregaveis":deepcopy(item["entregaveis"]),"revisao":deepcopy(item["revisao"]),
            "evidencias":deepcopy(item["evidencias"]),
            "snapshot":"reports/fechamento_m00_m09/bloco1_engenharia/cadastro_antes_alteracao.json"
        }
        if item["id"] in APPLIED:
            folder=BASE/item["id"]
            receipt=json.loads((folder/"resultado.json").read_text(encoding="utf-8"))
            if receipt.get("completed") is not True or receipt.get("exit_code",0)!=0:
                raise ValueError("Aplicação sem conclusão executada: "+item["id"])
            item["titulo"], descriptions=APPLIED[item["id"]]
            item["natureza"]="execucao_aplicada" if item["id"].startswith(("M01","M02")) else "analise_tecnica"
            item["criterios"]=[{"id":"C"+str(i+1),"descricao":text,"atendido":True}
                              for i,text in enumerate(descriptions)]
            item["entregaveis"]=[relative(p) for p in sorted(folder.iterdir()) if p.is_file()]
            item["constatacao"]="Aplicação e solução técnica executadas, com protocolo, resultado e conferências; não exige resposta do usuário."
            evidence_paths=set(item["entregaveis"])
        else:
            if item["estado"]!="validado" or not all(c["atendido"] for c in item["criterios"]):
                raise ValueError("Entrega prévia não estava validada: "+item["id"])
            evidence_paths={record["path"] for record in item["evidencias"]}|set(item["entregaveis"])
        item["estado"]="validado"
        item["portoes"]=list(dict.fromkeys("engenharia" if gate=="formacao" else gate for gate in item["portoes"]))
        if "engenharia" not in item["portoes"]: item["portoes"].append("engenharia")
        item["modo_entrega"]="engenharia_aplicada"
        item["human_response_required"]=False
        item["independent_learning_certified"]=False
        item["bloqueio"]=None
        item["revisao"]={"responsavel":"Codex — revisão técnica de engenharia","data":"2026-11-25",
                         "parecer":REVIEW,"decisao":"aprovado"}
        evidence_paths.update([REVIEW,REPORT,LINEAGE,
             "reports/fechamento_m00_m09/bloco1_engenharia/fontes_manifesto.json",
             "reports/fechamento_m00_m09/bloco1_engenharia/modo_entrega.json"])
        if item["id"] in {"M00-01","M01-01","M01-02","M07-04"}:
            evidence_paths.add("docs/roadmap_m00_m09/Diagnostico_SQL_Aplicado.md")
        if item["id"] in {"M02-01","M02-02","M02-03","M02-04"}:
            evidence_paths.add("docs/roadmap_m00_m09/Fundamentos_Aplicados_Resultados.md")
        item["evidencias"]=[{"path":p,"sha256":sha(ROOT/p),"kind":"entrega_ou_revisao_de_engenharia"}
                           for p in sorted(evidence_paths)]
    data["updated_at"]="2026-11-25"
    data["modo_de_execucao"]={
        "perfil":"engenharia_aplicada","bloco_ativo":1,"human_exercises_required":False,
        "authorization":"reports/fechamento_m00_m09/bloco1_engenharia/modo_entrega.json",
        "engineering_gate":"engenharia","operational_gate":"operacao",
        "learning_certification":"não realizada; critérios anteriores preservados como histórico"}
    data["regras"]["portoes"]["engenharia"]="Entregas aplicadas de código, execução e análise; não exige exercícios do usuário e não aprova operação."
    data["regras"]["assistencia"]="Soluções podem ser fornecidas integralmente para a entrega de engenharia; atribuição e limites preservados, sem certificar autoria pessoal."
    temp=TARGET.with_suffix(".json.new")
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(TARGET)
    output={"schema":"renewcast-engineering-mode-consolidation-v1",
        "recorded_at_utc":datetime.now(timezone.utc).isoformat(),
        "previous_backlog_sha256":sha(SNAPSHOT),"new_backlog_sha256":sha(TARGET),
        "script_sha256":sha(Path(__file__)),"engineering_item_count":len(APPLIED)+len(PRIOR),
        "operational_blocks_preserved":["M04-02","M04-03","M04-04","M04-05"],
        "independent_learning_certified":False,"models_trained":False}
    (BASE/"consolidacao.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False))
if __name__=="__main__":
    main()
