"""Audite em leitura a entrega de engenharia do bloco 2, sem carregar modelos.

Confere recibos/bytes, precedencia dos protocolos e do congelamento sobre o
download, e a coorte retrospectiva de outubro. Nao executa experimentos nem
certifica autonomia pessoal, fonte point-in-time, shadow ou operacao.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("reports/fechamento_m00_m09/bloco2_engenharia")
IDS = ("M02-06", "M02-07", "M02-08", "M03-01", "M03-02", "M03-03", "M05-01", "M05-02", "M05-03")
DIGEST = re.compile(r"[a-fA-F0-9]{64}\Z")
ROOT_DIRS = {"reports", "docs", "scripts", "notebooks", "src", "tests", "config", "dist", "data"}
HASH_MAPS = {"input_sha256", "input_hashes", "output_sha256", "outputs", "code", "code_sha256",
             "files", "frozen_method_sha256", "prior_construction_evidence_sha256"}
PROTOCOL_DATES = ("registered_at_utc", "created_at_utc", "created_at", "registered_at")
START_DATES = ("started_at_utc", "started_at", "start_at_utc")
END_DATES = ("completed_at_utc", "completed_at", "finished_at_utc", "finished_at")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"chave JSON repetida: {key}")
        result[key] = value
    return result


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique_keys)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp ausente ou nao textual")
    normalized = value.strip().replace(" UTC", "+00:00").replace("Z", "+00:00")
    stamp = datetime.fromisoformat(normalized)
    if stamp.tzinfo is None:
        raise ValueError("timestamp de execucao sem offset explicito")
    return stamp.astimezone(timezone.utc)


def first_time(data, keys):
    for key in keys:
        if key in data:
            return timestamp(data[key])
    raise ValueError("nenhum timestamp em " + ", ".join(keys))


def csv_time(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp.astimezone(timezone.utc)


def resolve_local(root, name, parent):
    if not isinstance(name, str) or not name or "\x00" in name:
        raise ValueError("caminho vazio ou invalido")
    normalized = name.replace("\\", "/")
    path = Path(normalized)
    if ".." in path.parts or "://" in normalized:
        raise ValueError("travessia ou URI nao permitida")
    if path.is_absolute():
        resolved = path.resolve()
    elif path.parts[0] in ROOT_DIRS:
        resolved = (root / path).resolve()
    else:
        resolved = (parent / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("caminho fora da raiz da auditoria")
    return resolved


def check_cohort(rows):
    """Exige a grade comum exata; contagem isolada nao basta."""
    expected = [datetime(2026,10,2,1,tzinfo=timezone.utc)+timedelta(hours=i) for i in range(695)]
    origins = [csv_time(row["forecast_origin"]) for row in rows]
    if origins != expected:
        raise ValueError("origens nao coincidem com as 695 horas Oct02_01..Oct31_00 exclusivo")
    if any("target_time" in row and csv_time(row["target_time"])-origin != timedelta(hours=24)
           for row, origin in zip(rows, origins)):
        raise ValueError("alvo h24 incoerente")
    if any("history_end" in row and origin-csv_time(row["history_end"]) != timedelta(hours=2)
           for row, origin in zip(rows, origins)):
        raise ValueError("fim do historico incoerente")
    return origins


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))


def bool_cell(value):
    if value in ("True","true","1",True):
        return True
    if value in ("False","false","0",False):
        return False
    raise ValueError("celula booleana invalida")


class Audit:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.checks = []
        self.notes = []
        self.checked_hashes = set()
        self.documents = {}

    def check(self, condition, where, detail):
        self.checks.append({"where":where, "passed":bool(condition), "detail":detail})
        return bool(condition)

    def attempt(self, where, function):
        try:
            return function()
        except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError, StopIteration) as exc:
            self.check(False, where, f"{type(exc).__name__}: {exc}")
            return None

    def read(self, path):
        data = self.attempt(str(path.relative_to(self.root)), lambda:load_json(path))
        if data is not None:
            self.documents[path] = data
        return data

    def hash(self, name, expected, parent, where):
        if not isinstance(expected, str) or not DIGEST.fullmatch(expected):
            self.check(False, where, "digest SHA-256 invalido")
            return
        def work():
            path = resolve_local(self.root,name,parent)
            key = (path,expected.lower())
            if key in self.checked_hashes:
                return
            self.checked_hashes.add(key)
            actual = sha(path)
            self.check(actual == expected.lower(), where,
                       f"{path.relative_to(self.root).as_posix()}: {actual}")
        self.attempt(where,work)

    def hash_declarations(self, data, parent, where):
        """Adapta listas/mapeamentos presentes nos recibos, sem desserializar artefatos."""
        if isinstance(data,list):
            for i,value in enumerate(data):
                self.hash_declarations(value,parent,f"{where}[{i}]")
            return
        if not isinstance(data,dict):
            return
        if isinstance(data.get("path"),str) and isinstance(data.get("sha256"),str):
            # A clinica registra a origem externa como proveniencia, e sua copia
            # dentro do repositorio e conferida pelo campo copiado/manifestos.
            if ":" in data["path"] and not Path(data["path"]).resolve().is_relative_to(self.root):
                self.notes.append({"where":where,"not_read_external_provenance":data["path"]})
            else:
                self.hash(data["path"],data["sha256"],parent,where+".sha256")
        if isinstance(data.get("copied_to"),str) and isinstance(data.get("copy_sha256"),str):
            self.hash(data["copied_to"],data["copy_sha256"],parent,where+".copy_sha256")
        for key in ("source","integrated_protocol","point_bundle"):
            if isinstance(data.get(key),str) and isinstance(data.get(key+"_sha256"),str):
                self.hash(data[key],data[key+"_sha256"],parent,where+"."+key+"_sha256")
        for key,value in data.items():
            location = f"{where}.{key}"
            if key in HASH_MAPS and isinstance(value,dict) and not {"path","sha256"}.issubset(value):
                for name,digest in value.items():
                    if isinstance(digest,str) and DIGEST.fullmatch(digest):
                        self.hash(name,digest,parent,location+"."+name)
            # Explicit paired fields with a supplied path.
            if key.endswith("_path") and isinstance(value,str):
                hash_key = key[:-5]+"_sha256"
                if isinstance(data.get(hash_key),str):
                    self.hash(value,data[hash_key],parent,where+"."+hash_key)
            self.hash_declarations(value,parent,location)

    def no_operation_claim(self, data, where):
        if isinstance(data,list):
            for i,value in enumerate(data):
                self.no_operation_claim(value,f"{where}[{i}]")
        elif isinstance(data,dict):
            for key,value in data.items():
                if key in {"operational_approval", "operational_policy_approved", "live_shadow_executed",
                           "independent_user_authorship_certified", "independent_user_performance_claimed"}:
                    self.check(value is False,f"{where}.{key}","entrega local nao deve alegar operacao/autonomia")
                self.no_operation_claim(value,f"{where}.{key}")

    def item(self, item_id):
        folder = self.root / BASE / item_id
        for name in ["protocolo.json","resultado.json","parecer.md"]:
            self.check((folder/name).is_file(),item_id+"."+name,"artefato obrigatorio presente")
        if not all((folder/name).is_file() for name in ["protocolo.json","resultado.json","parecer.md"]):
            return
        protocol = self.read(folder/"protocolo.json")
        result = self.read(folder/"resultado.json")
        if not isinstance(protocol,dict) or not isinstance(result,dict):
            return
        self.check(len((folder/"parecer.md").read_text(encoding="utf-8-sig").strip())>80,
                   item_id+".parecer","parecer contem interpretacao atribuida")
        for path in sorted(folder.rglob("*.json")):
            data = self.documents.get(path)
            if data is None:
                data = self.read(path)
            if data is not None:
                self.hash_declarations(data,path.parent,path.relative_to(self.root).as_posix())
                self.no_operation_claim(data,item_id+"/"+path.name)
        if "protocol_sha256" in result:
            self.hash("protocolo.json",result["protocol_sha256"],folder,item_id+".protocol_sha256")
        if result.get("completed") is not None:
            self.check(result["completed"] is True,item_id+".completed","recibo concluido")
        if "exit_code" in result:
            self.check(result["exit_code"] == 0,item_id+".exit_code","comando terminou com zero")
        # Schema adapters: documents have no execution start of their own.
        if item_id == "M03-01":
            execution = self.read(self.root/BASE/"M03-03/ajuste_receipt.json")
        elif item_id == "M03-03":
            execution = self.read(folder/"ajuste_receipt.json")
        elif item_id.startswith("M05-"):
            execution = next((entry for entry in result.get("executions",[])
                              if "--ajustar" in entry.get("command",[])),None)
            self.check(execution is not None,item_id+".fit_receipt","comando de ajuste real registrado")
        else:
            execution = result
        if execution:
            def before():
                registered = first_time(protocol,PROTOCOL_DATES)
                started = first_time(execution,START_DATES)
                self.check(registered<started,item_id+".protocol_before_execution",f"{registered.isoformat()} < {started.isoformat()}")
                end = first_time(execution,END_DATES)
                self.check(started<=end,item_id+".execution_clock","inicio antecede fim")
            self.attempt(item_id+".temporal_order",before)
        if item_id.startswith("M02-0") and item_id in {"M02-07","M02-08"}:
            self.bootstrap(folder,result,item_id)
        elif item_id == "M02-06":
            self.costs(folder,protocol,result)
        elif item_id.startswith("M03-"):
            self.point_model(item_id,folder,protocol,result)
        elif item_id.startswith("M05-"):
            self.risk(item_id,folder,protocol,result)

    def risk(self,item_id,folder,protocol,result):
        self.check(result.get("evaluation_performed") is True,item_id+".evaluation_performed","avaliacao concluida")
        for field in ["training_during_evaluation","recalibration_during_evaluation","policy_reselection_during_evaluation",
                      "snapshot_is_historically_point_in_time","live_shadow_demonstrated"]:
            self.check(result.get(field) is False,item_id+"."+field,"sem ajuste no teste, disponibilidade historica ou shadow alegados")
        self.check(result.get("evaluation_origins")==695,item_id+".evaluation_origins","695 origens declaradas")
        self.check(result.get("weekly_rows")==[168,168,168,168,23],item_id+".weeks","quatro semanas e parcial23")
        self.check(result.get("calibration_rows")==312 and result.get("policy_rows")==360,item_id+".calibration_policy","coortes312/360 separadas")
        freeze=self.documents.get(folder/"freeze.json") or self.read(folder/"freeze.json")
        fit_protocol=self.documents.get(folder/"protocolo_ajuste.json") or self.read(folder/"protocolo_ajuste.json")
        if freeze:
            self.hash("freeze.json",result["freeze_sha256"],folder,item_id+".freeze_sha256")
        if freeze and fit_protocol:
            def order():
                registered=first_time(protocol,PROTOCOL_DATES)
                fit_registered=first_time(fit_protocol,PROTOCOL_DATES)
                frozen=first_time(freeze,("frozen_at_utc",))
                self.check(registered<=fit_registered<frozen,item_id+".fit_protocol_order","plano e detalhe do ajuste precedem freeze")
            self.attempt(item_id+".fit_protocol_order",order)
        def cohort():
            with (folder/"predicoes_avaliacao.csv").open(encoding="utf-8-sig",newline="") as stream:
                rows=list(csv.DictReader(stream))
            origins=check_cohort(rows)
            if item_id=="M05-03":
                self.check(all(csv_time(row["ramp_label_available_at"])-origin==timedelta(hours=3)
                               for row,origin in zip(rows,origins)),item_id+".ramp_availability","rotulo de rampa horario disponivel em origem+3h")
            self.check(True,item_id+".october_cohort",f"{len(origins)} origens exatas verificadas no CSV")
        self.attempt(item_id+".october_cohort",cohort)
        for execution in result.get("executions",[]):
            self.check(execution.get("exit_code")==0,item_id+".execution_exit","comando de fase concluido com zero")
            if execution.get("log") and execution.get("log_sha256"):
                self.hash(execution["log"],execution["log_sha256"],folder,item_id+".execution_log")
        if item_id=="M05-02":
            def budget():
                with (folder/"orcamento_diario.csv").open(encoding="utf-8-sig",newline="") as stream:
                    rows=list(csv.DictReader(stream))
                self.check(bool(rows) and all(int(row["alarms"])<=6 and int(row["budget"])==6 for row in rows),
                           item_id+".daily_budget","capacidade causal de seis por dia respeitada")
            self.attempt(item_id+".daily_budget",budget)
        if item_id=="M05-01":
            uncertainty=protocol.get("coverage_bootstrap",{})
            self.check(uncertainty.get("repetitions")==2000 and uncertainty.get("seed")==17
                       and uncertainty.get("paired_raw_cqr_indices") is True,
                       item_id+".coverage_uncertainty_prefixed","2000 replicas pareadas seed17 previstas antes dos dados")
            rows=read_csv(folder/"incerteza_cobertura.csv")
            self.check(len(rows)==3 and all(int(r["block_hours"])==24 and int(r["bootstrap_repetitions"])==2000
                       and int(r["seed"])==17 and float(r["lower_percentile_2p5"])<=float(r["upper_percentile_97p5"]) for r in rows),
                       item_id+".coverage_uncertainty_summary","tres resumos condicionais com parametros fixados; sorteios nao repetidos")
        self.attempt(item_id+".metric_arithmetic",lambda:self.risk_metrics(item_id,folder))

    def risk_metrics(self,item_id,folder):
        """Reconciliacao aritmetica dos CSVs; nao refaz previsoes/calibracao."""
        predictions=read_csv(folder/"predicoes_avaliacao.csv")
        def reconcile(metric_rows,calculation):
            for row in metric_rows:
                start,end=csv_time(row["origin_min"]),csv_time(row["origin_max"])
                part=[p for p in predictions if start<=csv_time(p["forecast_origin"])<=end]
                calculated=calculation(part,row["method"])
                self.check(len(part)==int(row["n"]),f"{item_id}.{row['period']}.{row['method']}.n","contagem reconciliada")
                for field,value in calculated.items():
                    expected=float(row[field])
                    self.check(math.isfinite(value) and math.isclose(value,expected,rel_tol=1e-11,abs_tol=1e-9),
                               f"{item_id}.{row['period']}.{row['method']}.{field}",f"calculado={value:.17g}; salvo={expected:.17g}")
        if item_id=="M05-01":
            def interval(part,method):
                cols=("raw_p10","raw_p50","raw_p90") if method=="raw_sorted" else ("cqr_lower","cqr_median","cqr_upper")
                targets=[float(p["y24"]) for p in part]
                q=[[float(p[c]) for c in cols] for p in part]
                self.check(all(a<=b<=c for a,b,c in q),item_id+".quantile_order","extremos e mediana ordenados")
                covered=sum(lo<=y<=hi for y,(lo,_,hi) in zip(targets,q))/len(part)
                width=sum(hi-lo for lo,_,hi in q)/len(part)
                pinball=[sum(max(tau*(y-v[j]),(tau-1)*(y-v[j])) for y,v in zip(targets,q))/len(part) for j,tau in enumerate([.1,.5,.9])]
                score=sum(hi-lo+10*max(lo-y,0)+10*max(y-hi,0) for y,(lo,_,hi) in zip(targets,q))/len(part)
                return {"coverage":covered,"width":width,"interval_score":score,"pinball_p10":pinball[0],"pinball_p50":pinball[1],"pinball_p90":pinball[2],"pinball_mean":sum(pinball)/3}
            reconcile(read_csv(folder/"metricas_intervalos.csv"),interval)
        elif item_id=="M05-02":
            def probability(part,method):
                y=[int(p["event_26h"]) for p in part]
                p=[float(p["p_"+method]) for p in part]
                if not all(value in (0,1) for value in y) or not all(0<=value<=1 for value in p):
                    raise ValueError("rotulo/probabilidade invalido")
                return {"positives":sum(y),"prevalence":sum(y)/len(y),"brier":sum((a-b)**2 for a,b in zip(y,p))/len(y)}
            reconcile(read_csv(folder/"metricas_probabilidades.csv"),probability)
            def alarm(part,method):
                pairs=[(bool(int(p["event_26h"])),bool_cell(p["alarm_"+method])) for p in part]
                tp=sum(y and a for y,a in pairs); fp=sum(not y and a for y,a in pairs)
                fn=sum(y and not a for y,a in pairs); tn=sum(not y and not a for y,a in pairs)
                return {"tp":tp,"fp":fp,"fn":fn,"tn":tn,"alarms":tp+fp,"cost":fp+4*fn,"cost_per_origin":(fp+4*fn)/len(part)}
            reconcile(read_csv(folder/"metricas_alarmes.csv"),alarm)
            policy=load_json(folder/"politica_congelada.json")
            counts={}; expected=[]
            for row in predictions:
                day=csv_time(row["forecast_origin"]).date()
                decision=(policy["threshold"] is not None and float(row["p_platt_calibrated"])>=policy["threshold"] and counts.get(day,0)<6)
                if decision: counts[day]=counts.get(day,0)+1
                expected.append(decision)
            self.check(expected==[bool_cell(p["alarm_frozen_calibrated_policy"]) for p in predictions],
                       item_id+".causal_policy_reconciliation","primeiros seis elegiveis, limiar congelado; nenhuma ordenacao futura do dia")
            self.check(all(int(p["event_26h"])==int(float(p["last_observed"])-float(p["y24"])>=22.77) for p in predictions),
                       item_id+".event_label","evento26h corresponde aos endpoints gravados")
        else:
            def regression(part,method):
                errors=[float(p["ramp_down_1h"])-float(p["prediction_"+method]) for p in part]
                return {"mae":sum(abs(e) for e in errors)/len(errors),"rmse":math.sqrt(sum(e*e for e in errors)/len(errors)),"bias_observed_minus_predicted":sum(errors)/len(errors)}
            reconcile(read_csv(folder/"metricas_regressao_rampa.csv"),regression)

    def bootstrap(self,folder,result,item_id):
        for name in ["bootstrap.csv","bootstrap_vs_persistencia.csv"]:
            def work():
                with (folder/name).open(encoding="utf-8-sig",newline="") as stream:
                    rows=list(csv.DictReader(stream))
                self.check(len(rows)==12,item_id+"."+name,"12 resumos: tres folds e agregado por bloco")
                self.check({int(r["block_hours"]) for r in rows}=={6,24,48},item_id+".blocks","todos os blocos fixados publicados")
                self.check(all(int(r["repetitions"])==5000 and int(r["seed"])==42 for r in rows),item_id+".parameters","5000 replicas, seed42")
            self.attempt(item_id+"."+name,work)
        self.check(result.get("untouched_holdout") is False,item_id+".not_holdout","previsoes historicas examinadas")
        self.check(result.get("nonpositive_bootstrap_fraction_is_p_value") is False,item_id+".not_pvalue","fracao bootstrap nao e p-valor")

    def costs(self,folder,protocol,result):
        self.check(result.get("verification_execution",{}).get("exit_code")==0,"M02-06.verification","verificacao real com exit zero")
        mappings = [("clinic_output_hashes",self.root/result["clinic_run"]),
                    ("source_m09_output_hashes",self.root/protocol["source_run"]),
                    ("source_event_output_hashes",self.root/protocol["source_event_study"])]
        for key,parent in mappings:
            for name,digest in result.get(key,{}).items():
                self.hash(name,digest,parent,"M02-06."+key+"."+name)
        self.hash("aplicar_custos.py",result["code_sha256"],folder,"M02-06.code_sha256")
        self.hash("resultado.json",result["clinic_result_sha256"],self.root/result["clinic_run"],"M02-06.clinic_result")
        self.hash("notebooks/clinica_decisao_forecast.py",result["clinic_code_sha256"],folder,"M02-06.clinic_code")
        self.check(result.get("generation_cohort",{}).get("rows")==168,"M02-06.generation_cohort","168 pares da clinica")
        self.check(result.get("event_cohort",{}).get("rows_per_method")==504,"M02-06.event_cohort","504 eventos por metodo, coorte separada")

    def point_model(self,item_id,folder,protocol,result):
        if item_id == "M03-02":
            self.hash("notebooks/explicacao_local.py",result["code_sha256"],folder,item_id+".code_sha256")
            self.hash("point_bundle.joblib",result["bundle_sha256"],self.root/BASE/"M03-03",item_id+".bundle_sha256")
            self.check(result["max_additivity_error_mw"]<1e-8,item_id+".additivity","soma das atribuicoes reproduz a previsao")
        if item_id == "M03-03":
            if result.get("adjustment_receipt") and result.get("adjustment_sha256"):
                self.hash(result["adjustment_receipt"],result["adjustment_sha256"],folder,item_id+".adjustment_receipt")
            if result.get("review_sha256"):
                self.hash("parecer.md",result["review_sha256"],folder,item_id+".review_sha256")
            manifest = self.read(folder/"selection_manifest.json")
            if manifest:
                self.hash("point_bundle.joblib",manifest["bundle_sha256"],folder,item_id+".bundle_sha256")
                self.check(manifest.get("evaluation_opened") is False,item_id+".selection_closed_test","manifesto de selecao antecede abertura do teste")
            self.check((folder/"evaluation_receipt.json").is_file(),item_id+".evaluation_receipt","avaliacao congelada de outubro presente")
            if (folder/"evaluation_receipt.json").is_file():
                evaluation=self.documents.get(folder/"evaluation_receipt.json") or self.read(folder/"evaluation_receipt.json")
                if evaluation:
                    self.check(evaluation.get("execution")=="first_frozen_october_evaluation_no_refit",item_id+".no_refit","recibo identifica aplicacao sem ajuste")
                    addendum=self.documents.get(folder/"adendo_execucao_avaliacao.json") or self.read(folder/"adendo_execucao_avaliacao.json")
                    if addendum:
                        self.check(addendum.get("exit_code")==0 and addendum.get("observed_execution_count")==1
                                   and "--avaliar" in addendum.get("command",[]),item_id+".evaluation_command","comando real e zero observado em chamada unica; adendo posterior identificado")
                        self.check(first_time(addendum,START_DATES)==first_time(evaluation,START_DATES)
                                   and first_time(addendum,END_DATES)==first_time(evaluation,END_DATES),
                                   item_id+".addendum_times","adendo preserva horarios internos do recibo sem inventar inicio externo")
            path=folder/"predicoes_evaluation.csv"
            def cohort():
                with path.open(encoding="utf-8-sig",newline="") as stream:
                    rows=list(csv.DictReader(stream))
                origins=check_cohort(rows)
                self.check(True,item_id+".october_cohort",f"{len(origins)} origens exatas; alvo+24, historico-2")
                for metric,column in [("selected_metrics","prediction"),("study_metrics","study_prediction"),("persistence_metrics","last_observed")]:
                    mae=sum(abs(float(row["y24"])-float(row[column])) for row in rows)/len(rows)
                    expected=float(evaluation[metric]["mae"])
                    self.check(math.isclose(mae,expected,rel_tol=1e-12,abs_tol=1e-10),item_id+"."+metric+".mae",f"MAE recomputado={mae:.17g}; recibo={expected:.17g}")
            self.attempt(item_id+".october_cohort",cohort)

    def registry(self):
        path=self.root/"config/roadmap_m00_m09.json"
        data=self.read(path)
        if not data:
            return
        items={item["id"]:item for item in data["items"]}
        snapshot=self.read(self.root/BASE/"cadastro_antes_alteracao.json")
        previous={item["id"]:item for item in snapshot["items"]} if snapshot else {}
        self.check(len(items)==45 and set(items)==set(previous),"registry.original_ids","45 IDs historicos preservados")
        engineering={item["id"] for item in data["items"] if item["etapa"] in (4,5,6) and "engenharia" in item["portoes"]}
        self.check(engineering==set(IDS),"registry.engineering_scope","nove entregas aplicadas no bloco2")
        for item_id in IDS:
            item=items[item_id]
            self.check(item["estado"]=="validado" and "engenharia" in item["portoes"],item_id+".registry","validado apenas no escopo aplicado")
            if item_id in previous:
                history=item.get("historico_bloco2",{})
                fields=("titulo","natureza","estado","constatacao","portoes","entregaveis","criterios","evidencias","revisao","bloqueio")
                self.check(all(history.get(key)==previous[item_id].get(key) for key in fields),
                           item_id+".embedded_history_equals_snapshot","historico integral anterior preservado sem mutacao dos criterios")
        for item_id in ["M05-01","M05-02"]:
            self.check("operacao" not in items[item_id]["portoes"],item_id+".gate_separation","aceite retrospectivo separado da operacao")
            history=items[item_id].get("historico_bloco2",{})
            self.check("operacao" in history.get("portoes",[]),item_id+".history","portao operacional anterior preservado")
        pending=items["M06-05"]
        self.check("operacao" in pending["portoes"] and pending["estado"]!="validado","M06-05.operation_open","continuidade operacional ainda pendente")
        self.check({"M05-01","M05-02"}.issubset(set(pending["depende_de"])),"M06-05.origin_dependencies","pendencias prospectivas vinculadas aos M05")
        criteria={c["id"]:c for c in pending["criterios"]}
        for cid,origin in [("C3","M05-01"),("C4","M05-02")]:
            criterion=criteria.get(cid,{})
            self.check(criterion.get("atendido") is False and origin in json.dumps(criterion,ensure_ascii=False),
                       "M06-05."+cid,"criterio externo nao atendido e origem rastreavel")

    def freeze_download(self,freeze_path,download_path):
        if freeze_path is None or download_path is None:
            self.check(False,"freeze_download","--freeze e --download-receipt obrigatorios na auditoria final")
            return
        freeze=self.read(freeze_path)
        download=self.read(download_path)
        if not freeze or not download:
            return
        self.hash_declarations(freeze,freeze_path.parent,"integrated_freeze")
        self.hash_declarations(download,download_path.parent,"october_download")
        # The source snapshot can be retrospective; this only verifies access order.
        def order():
            frozen=first_time(freeze,("frozen_at_utc","frozen_at","created_at_utc","created_at"))
            downloaded=first_time(download,("downloaded_at_utc",))
            extracted=first_time(download,("extracted_at_utc",))
            self.check(frozen<downloaded<=extracted,"freeze_download.order",f"freeze={frozen.isoformat()}; recebido={downloaded.isoformat()}; extraido={extracted.isoformat()}")
            self.check(freeze.get("raw_evaluation_present") is False,"freeze_download.raw_absent","selo registra ausencia do bruto antes de obter")
            self.check(download.get("extraction_status")=="validated" and download.get("filtered_rows")==744,
                       "freeze_download.source_contract","recorte744horas validado pelo extrator congelado")
            self.check(download.get("freeze_sha256")==sha(freeze_path),"freeze_download.freeze_hash","fonte referencia o selo exato")
            self.check(timestamp(download["freeze_created_at_utc"])==frozen,"freeze_download.freeze_timestamp","fonte referencia horario do mesmo selo")
            self.notes.append({"where":"freeze_download","download_request_start_not_persisted":True,
                "interpretation":"ordem corroborada por selo/recebimento/extracao e codigo congelado que verifica selo antes da rede; sem inventar inicio HTTP"})
            for item_id in ["M03-03","M05-01","M05-02","M05-03"]:
                folder=self.root/BASE/item_id
                path=folder/("evaluation_receipt.json" if item_id=="M03-03" else "resultado.json")
                result=self.documents.get(path) or self.read(path)
                if not result:
                    continue
                evaluation=(result.get("evaluation",result) if item_id=="M03-03" else
                            next(entry for entry in result["executions"] if "--avaliar" in entry["command"]))
                begin=first_time(evaluation,START_DATES)
                self.check(extracted<=begin,item_id+".evaluation_after_download",f"{extracted.isoformat()} <= {begin.isoformat()}")
                if item_id.startswith("M05-"):
                    local=self.documents.get(folder/"freeze.json") or self.read(folder/"freeze.json")
                    self.check(first_time(local,("frozen_at_utc",))<=frozen,item_id+".freeze_before_global","bundle/politica local congelados antes do selo conjunto")
        self.attempt("freeze_download.order",order)
        self.no_operation_claim(freeze,"freeze")
        self.no_operation_claim(download,"download")


def self_test():
    """Contraprovas do auditor: rejeicoes que impedem falsos aceites."""
    passed=[]
    def rejects(name,function):
        try:
            function()
        except (ValueError,KeyError):
            passed.append(name)
        else:
            raise AssertionError(name+": entrada invalida aceita")
    rejects("duplicate_json_key",lambda:json.loads('{"x":1,"x":2}',object_pairs_hook=unique_keys))
    rejects("naive_execution_clock",lambda:timestamp("2026-11-25T19:00:00"))
    with tempfile.TemporaryDirectory(prefix="renewcast_audit_bloco2_") as name:
        root=Path(name).resolve()
        path=root/"evidence.txt"
        path.write_text("evidence",encoding="utf-8")
        rejects("path_traversal",lambda:resolve_local(root,"../outside.txt",root))
        audit=Audit(root)
        audit.hash("evidence.txt","0"*64,root,"wrong_hash")
        if len(audit.checks)!=1 or audit.checks[0]["passed"]:
            raise AssertionError("hash adulterado nao reprovado")
        passed.append("changed_evidence_hash")
        schema=Audit(root)
        schema.hash_declarations({"code":{"path":"evidence.txt","sha256":sha(path)}},root,"code_record")
        if len(schema.checks)!=1 or not schema.checks[0]["passed"]:
            raise AssertionError("registro path/sha256 confundido com mapa de nomes")
        passed.append("path_digest_record_schema")
        audit.no_operation_claim({"operational_approval":True},"claim")
        if audit.checks[-1]["passed"]:
            raise AssertionError("aprovacao operacional falsa nao reprovada")
        passed.append("false_operation_claim")
    start=datetime(2026,10,2,1,tzinfo=timezone.utc)
    rows=[{"forecast_origin":(start+timedelta(hours=i)).isoformat()} for i in range(695)]
    assert len(check_cohort(rows))==695
    rows[-1]=dict(rows[0])
    rejects("695_rows_with_duplicate_and_missing_hour",lambda:check_cohort(rows))
    assert timestamp("2026-11-25 19:15:12 UTC")==timestamp("2026-11-25T19:15:12+00:00")
    passed.append("explicit_utc_formats")
    print(json.dumps({"self_test":True,"passed":passed,"count":len(passed),"experiments_run":False},ensure_ascii=False))
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--items",nargs="+",choices=IDS,default=list(IDS),help="Itens a auditar; padrao: nove entregas.")
    parser.add_argument("--freeze",type=Path,help="Recibo integrado selado antes do download de outubro.")
    parser.add_argument("--download-receipt",type=Path,help="Recibo real do download do snapshot de outubro.")
    parser.add_argument("--check-registry",action="store_true",help="Confere migracao engenharia/operacao apos cadastro consolidado.")
    parser.add_argument("--output",type=Path,help="Grava relatorio em arquivo NOVO dentro de --root; nunca sobrescreve.")
    parser.add_argument("--self-test",action="store_true",help="Executa apenas contraprovas pequenas do auditor em pasta temporaria.")
    args=parser.parse_args(argv)
    if args.self_test:
        return self_test()
    started=datetime.now(timezone.utc).isoformat()
    audit=Audit(args.root)
    for item_id in args.items:
        audit.attempt(item_id,lambda item_id=item_id:audit.item(item_id))
    def resolve_argument(path):
        return None if path is None else resolve_local(audit.root,str(path),audit.root)
    if set(args.items)==set(IDS):
        audit.freeze_download(resolve_argument(args.freeze),resolve_argument(args.download_receipt))
    if args.check_registry:
        audit.registry()
    errors=[row for row in audit.checks if not row["passed"]]
    report={"schema":"renewcast-bloco2-engineering-delivery-audit-v1",
        "completed":True,"valid":not errors,"exit_code":int(bool(errors)),
        "started_at_utc":started,"completed_at_utc":datetime.now(timezone.utc).isoformat(),
        "command":[sys.executable,str(Path(__file__).resolve()),*(sys.argv[1:] if argv is None else argv)],
        "auditor_sha256":sha(__file__),"items":args.items,"checks_count":len(audit.checks),
        "hash_declarations_checked":len(audit.checked_hashes),"errors":errors,"checks":audit.checks,"notes":audit.notes,
        "files_read_sha256":{p.relative_to(audit.root).as_posix():sha(p) for p in sorted(audit.documents)},
        "experiment_execution":False,"model_deserialization":False,"operational_approval":False,
        "independent_user_authorship_certified":False,
        "warning":"Auditoria documental local; outubro e avaliacao retrospectiva apos congelamento, nao coleta prospectiva ou shadow."}
    if args.output:
        try:
            output=resolve_argument(args.output)
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open("x",encoding="utf-8",newline="\n") as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False)
                stream.write("\n")
        except (OSError,ValueError) as exc:
            print(f"Nao foi possivel gravar relatorio novo: {exc}",file=sys.stderr)
            return 2
    print(json.dumps({key:report[key] for key in ["valid","exit_code","items","checks_count","hash_declarations_checked","errors","warning"]},ensure_ascii=False))
    return report["exit_code"]


if __name__=="__main__":
    raise SystemExit(main())
