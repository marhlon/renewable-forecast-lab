"""Exporte a versão conhecida do cadastro sem inventar vigência histórica."""
import csv
import json
import subprocess
import sys
from pathlib import Path
from evidencias_bloco1 import ROOT, BASE, dump, receipt, sha
sys.path.insert(0,str(ROOT/"src"))
from renewable_forecast.asset_registry_history import selecionar_cadastro_causal

def main():
    source=ROOT/"data/reference/CJU_BA5EIGT/asset_registry.csv"
    metadata=ROOT/"data/reference/CJU_BA5EIGT/metadata.json"
    info=json.loads(metadata.read_text(encoding="utf-8"))
    known=max(s["fetched_at_utc"] for s in info["sources"].values())
    records=[]
    with source.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            records.append({"asset_id":row["id_ons_usina"],"version":sha(source)[:16],
                "valid_from":None,"valid_to":None,"known_from":known,"known_to":None,
                "historical_validity_verified":False,"source_sha256":sha(source),
                "payload":row})
    out=BASE/"M04-04"
    with (out/"cadastro_versionado.csv").open("w",encoding="utf-8-sig",newline="") as f:
        fields=["asset_id","version","valid_from","valid_to","known_from","known_to","historical_validity_verified","source_sha256"]
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows({k:r[k] for k in fields} for r in records)
    # O snapshot foi consultado em setembro; não é retroativamente conhecido em julho.
    historical=selecionar_cadastro_causal(records,instante="2026-07-01T00:00:00Z",conhecido_em="2026-07-01T00:00:00Z")
    assert historical==[]
    test=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-p","test_asset_registry_history.py","-v"],
                        cwd=ROOT,capture_output=True,text=True,encoding="utf-8")
    (out/"testes.log").write_text(test.stdout+test.stderr,encoding="utf-8")
    if test.returncode:
        raise RuntimeError("Contraprovas cadastrais falharam.")
    (out/"fontes.md").write_text(
        "# Cadastro preservado, vigência não comprovada\n\n"
        "Snapshot local: data/reference/CJU_BA5EIGT/asset_registry.csv; fontes e consultas em metadata.json. "
        f"Conhecimento de todas as fontes não anterior a {known}. "
        "As datas de relacionamento descrevem vínculos; não comprovam a vigência histórica conjunta de capacidade/coordenadas. "
        "valid_from/valid_to ficam vazios deliberadamente, em vez de assumir a data do relacionamento para todos os atributos.\n\n"
        "A seleção bitemporal foi construída e passou nas contraprovas. "
        "O snapshot não é elegível para decisões históricas de julho e continua sem homologação de vigência.\n",
        encoding="utf-8")
    (out/"parecer.md").write_text(
        "# Revisão assistida do cadastro bitemporal\n\n"
        "Codex, 25/11/2026. Implementação e seis contraprovas executadas em Python, sem Docker e sem consulta nova ao cadastro. "
        f"Foram exportados {len(records)} registros com identidade do snapshot e conhecimento observável. "
        "O mecanismo preserva consultas passadas quando surge uma versão futura e exclui vigência não comprovada. "
        "A comprovação das versões cadastrais históricas continua pendente de fonte externa; este item não recebe aceite operacional.\n",
        encoding="utf-8")
    receipt("M04-04",{"unit_tests_exit_code":test.returncode,"historical_snapshot_selected":len(historical),
            "unknown_validity_excluded":True},code=[Path(__file__).resolve(),ROOT/"src/renewable_forecast/asset_registry_history.py"],
            inputs=[source,metadata],details={"rows":len(records),"historical_validity_verified":False})
    print("M04-04: bitemporal implementado; 6 testes passaram; 15 registros preservados; vigência histórica pendente.")

if __name__=="__main__":
    main()
