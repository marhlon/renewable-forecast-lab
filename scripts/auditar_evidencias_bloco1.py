"""Auditoria em leitura dos recibos e do registro, sem carregar modelos."""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from evidencias_bloco1 import ROOT, BASE, sha, dump, receipt

OLD = ROOT/"docs/roadmap_m00_m09/auditoria_m08_m09.json"
REG = ROOT/"reports/registry/CJU_BA5EIGT/h24_event_registry_v1/51cb4456d07d4f01b8b20f32e4ed1f78"


def inspect(path, expected):
    record = {"path":str(path.relative_to(ROOT)), "expected_sha256":expected}
    try:
        record["actual_sha256"] = sha(path)
        record["status"] = "match" if record["actual_sha256"] == expected else "mismatch"
    except PermissionError:
        record["status"] = "permission_denied"
    except FileNotFoundError:
        record["status"] = "missing"
    return record


def review_units():
    prior = json.loads(OLD.read_text(encoding="utf-8"))
    for item, prefix, filename in (("M08-01","M08.","auditoria_brutos.json"),
                                   ("M09-01","M09.2","auditoria_transformer.json")):
        rows = []
        for run in prior["runs"]:
            if not run["label"].startswith(prefix):
                continue
            for category in ("outputs","inputs","current_code","current_author_file"):
                entries = run.get(category,[])
                if isinstance(entries,dict):
                    entries = [entries]
                for entry in entries:
                    if "expected_sha256" in entry:
                        rows.append({"run":run["run_id_in_receipt"], "category":category,
                                     **inspect(ROOT/entry["path"],entry["expected_sha256"])})
        outputs = [r for r in rows if r["category"] == "outputs"]
        changes = [r for r in rows if r["category"] in {"current_code","current_author_file"} and r["status"]!="match"]
        detail = {"item":item, "method":"read bytes/SHA256; no torch/pickle import",
                  "checks":rows, "counts":dict(Counter(r["status"] for r in rows)),
                  "historical_outputs_intact":bool(outputs) and all(r["status"]=="match" for r in outputs),
                  "current_code_discrepancies":changes,
                  "independent_reproduction":False, "autonomy_certified":False}
        dump(BASE/item/filename,detail)
        (BASE/item/"parecer.md").write_text(
            "# Revisão técnica de integridade — "+item+"\n\n"
            "Revisão assistida executada por Codex, em 25/11/2026. Conferência em leitura das listas fixadas no inventário anterior. "
            "Os hashes de saídas foram recalculados; não houve treino, inferência ou recarga de pickle/checkpoint.\n\n"
            f"Saídas históricas íntegras: {detail['historical_outputs_intact']}. "
            f"Declarações de código atual divergentes: {len(changes)} (podem repetir caminhos entre runs).\n\n"
            "A versão atual e a executada no passado não são intercambiáveis quando os hashes diferem. "
            "Sem o código histórico exato, não se declara reprodução integral a partir da árvore atual. "
            "A documentação desta diferença encerra a auditoria de preservação; não apaga o aceite antigo nem certifica aprendizagem. "
            "Antes de uma nova execução, registrar a versão atual como outra identidade. Nenhum arquivo histórico foi restaurado ou alterado.\n",
            encoding="utf-8")
        receipt(item, {"output_hashes_match":detail["historical_outputs_intact"],
                       "version_discrepancies_disclosed":True},
                code=[Path(__file__).resolve()],inputs=[OLD],details={"current_code_discrepancy_declarations":len(changes)})
        print(item, detail["counts"])
        if not detail["historical_outputs_intact"]:
            raise ValueError("Saída histórica ausente ou alterada; não validar o item.")


def registry():
    records=[]
    with (REG/"versions.csv").open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            for name, digest in json.loads(row["files_json"]).items():
                records.append(inspect(REG/"registry/versions"/row["version_id"]/name,digest))
    ok = len(records)==8 and all(r["status"]=="match" for r in records)
    dump(BASE/"M06-01/inventario_registry.json", {"records":records,"counts":dict(Counter(r["status"] for r in records)),
         "all_expected_hashes_match":ok,"read_only":True,
         "restored_files":False,"deserialized_model":False,
         "interpretation":"Hashes lidos quando permitido; acesso negado não é ausência. Se leitura externa ao sandbox coincidir, a limitação observada é de acesso nesse contexto."})
    (BASE/"M06-01/parecer.md").write_text(
        "# Inventário do registro local\n\n"
        "Auditoria assistida por Codex em 25/11/2026, somente leitura. As identidades esperadas vieram de versions.csv; "
        "modelos foram tratados como bytes, sem desserialização. Nenhum arquivo foi restaurado, movido ou apagado.\n\n"
        f"Oito hashes esperados coincidem: {ok}. Contagens: {dict(Counter(r['status'] for r in records))}. "
        "Um resultado permission_denied limita a conferência e não pode ser convertido em missing. "
        "O status Git obtido sob acesso restrito também não prova perda. Ver resultado da leitura autorizada fora do sandbox, quando existente.\n",
        encoding="utf-8")
    receipt("M06-01",{"all_expected_hashes_match":ok,"no_restore_or_deserialization":True},
            code=[Path(__file__).resolve()],inputs=[REG/"versions.csv"])
    print("M06-01",dict(Counter(r["status"] for r in records)))
    return 0 if ok else 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry",action="store_true")
    args=p.parse_args()
    return registry() if args.registry else review_units()


if __name__=="__main__":
    raise SystemExit(main())
