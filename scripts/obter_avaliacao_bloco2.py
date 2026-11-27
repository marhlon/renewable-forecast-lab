"""Sela o estudo e obtém o mês ONS predefinido, sem substituir dados históricos.

O selo cobre código, modelos e política. Download e seleção da usina só são
permitidos depois dele; o recibo não afirma disponibilidade histórica da fonte.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/fechamento_m00_m09/bloco2_engenharia"
RAW = ROOT / "data/raw/bloco2_locked/geracao_2026_10.parquet"
DATA = BASE / "dados_avaliacao"
SEAL = BASE / "congelamento_avaliacao.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def verify():
    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    for entry in seal["files"]:
        if digest(ROOT/entry["path"]) != entry["sha256"]:
            raise ValueError(f"Arquivo mudou depois do congelamento: {entry['path']}")
    return seal


def freeze(extra_files):
    if SEAL.exists() or RAW.exists() or DATA.exists():
        raise FileExistsError("Selo/dados já existem; não reescrever a ordem histórica.")
    fixed = ["scripts/obter_avaliacao_bloco2.py", "notebooks/bloco2_modelagem_core.py",
        "notebooks/selecao_atributos_temporal.py", "notebooks/explicacao_local.py",
        "notebooks/bloco2_risco_core.py", "notebooks/bloco2_validacao_risco.py",
        "tests/test_bloco2_risco.py", "tests/test_bloco2_modelagem.py",
        "reports/fechamento_m00_m09/bloco2_engenharia/protocolo_integrado.json",
        "reports/fechamento_m00_m09/bloco2_engenharia/M03-03/point_bundle.joblib"]
    paths = sorted(set(fixed+extra_files))
    # Os arquivos adicionais são os modelos e a política já ajustados.
    if not any("M05" in p and p.endswith(".joblib") for p in paths):
        raise ValueError("Declare o bundle M05 ajustado com --arquivo.")
    if not any("politica_congelada" in p for p in paths):
        raise ValueError("Declare a política congelada com --arquivo.")
    entries=[]
    for rel in paths:
        path = (ROOT/rel).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f"Arquivo não local ou ausente: {rel}")
        entries.append({"path":path.relative_to(ROOT).as_posix(),"sha256":digest(path),"bytes":path.stat().st_size})
    save(SEAL, {"schema":"renewcast-bloco2-freeze-v1","created_at_utc":now(),
        "evaluation_month":"2026-10","raw_evaluation_present":False,"files":entries,
        "operational_approval":False,"changes_require_new_study":True})
    print(f"Congelados {len(entries)} arquivos; dados de outubro ainda ausentes.")


def get_bytes(url, limit):
    req=Request(url,headers={"User-Agent":"Renewcast-reproducible-research/1.0"})
    with urlopen(req,timeout=90) as response:
        data=response.read(limit+1)
        if len(data)>limit: raise ValueError("Resposta excedeu limite de tamanho predefinido.")
        return data, {"resolved_url":response.url,"headers":dict(response.headers.items())}


def download():
    seal=verify()
    if RAW.exists() or DATA.exists():
        raise FileExistsError("Arquivo/recibo já existe; não baixar novamente nem substituir snapshot.")
    plan=json.loads((BASE/"protocolo_integrado.json").read_text(encoding="utf-8"))
    url=plan["evaluation"]["metadata_api"]
    metadata_bytes,meta_http=get_bytes(url,2*1024**2)
    metadata=json.loads(metadata_bytes)
    if metadata.get("success") is not True: raise ValueError("CKAN não confirmou o recurso.")
    resource=metadata["result"]
    if resource["id"]!="6edb2f1a-5772-44f1-8dad-6180b20bf130" or resource["format"].lower()!="parquet":
        raise ValueError("Identidade/formato do recurso divergem do protocolo.")
    content,http=get_bytes(resource["url"],32*1024**2)
    if content[:4]!=b"PAR1" or content[-4:]!=b"PAR1": raise ValueError("Resposta não é Parquet.")
    RAW.parent.mkdir(parents=True,exist_ok=True)
    RAW.write_bytes(content)
    DATA.mkdir(parents=True,exist_ok=False)
    save(DATA/"fonte_ckan.json",metadata)
    receipt={"schema":"renewcast-bloco2-source-v1","downloaded_at_utc":now(),
        "freeze_created_at_utc":seal["created_at_utc"],"freeze_sha256":digest(SEAL),
        "metadata_api":url,"metadata_http":meta_http,"data_http":http,
        "resource_url":resource["url"],"resource_page":plan["evaluation"]["resource_page"],
        "raw_path":RAW.relative_to(ROOT).as_posix(),"raw_sha256":digest(RAW),"raw_bytes":len(content),
        "snapshot_caveat":"Snapshot obtido agora; revisões e disponibilidade histórica na origem não comprovadas.",
        "operational_approval":False,"extraction_status":"pending"}
    save(DATA/"fonte.json",receipt)
    extract(receipt)


def extract(receipt=None):
    import numpy as np
    import pandas as pd
    verify()
    receipt=receipt or json.loads((DATA/"fonte.json").read_text(encoding="utf-8"))
    if digest(RAW)!=receipt["raw_sha256"]: raise ValueError("Bruto foi alterado.")
    out=DATA/"geracao_CJU_BA5EIGT_2026_10.parquet"
    if out.exists(): raise FileExistsError("Recorte existente; não reescrever.")
    raw=pd.read_parquet(RAW)
    if not {"id_ons","din_instante","val_geracao"}.issubset(raw.columns):
        raise ValueError(f"Esquema não atende ao contrato: {raw.columns.tolist()}")
    frame=raw.loc[raw["id_ons"].eq("CJU_BA5EIGT"),["din_instante","val_geracao"]].copy()
    frame["din_instante"]=pd.to_datetime(frame["din_instante"],utc=True).dt.tz_localize(None)
    frame["val_geracao"]=pd.to_numeric(frame["val_geracao"],errors="raise")
    frame=frame.sort_values("din_instante").reset_index(drop=True)
    expected=pd.date_range("2026-10-01", "2026-10-31 23:00",freq="h")
    if not pd.DatetimeIndex(frame["din_instante"]).equals(expected):
        raise ValueError("Usina não contém exatamente 744 horas únicas de outubro; avaliação interrompida.")
    if not np.isfinite(frame["val_geracao"]).all(): raise ValueError("Geração nula/infinita: não imputar.")
    frame.to_parquet(out,index=False)
    receipt.update({"extraction_status":"validated","filtered_path":out.relative_to(ROOT).as_posix(),
        "filtered_sha256":digest(out),"filtered_rows":len(frame),"columns":frame.columns.tolist(),
        "first_timestamp":str(frame["din_instante"].min()),"last_timestamp":str(frame["din_instante"].max()),
        "source_total_rows":len(raw),"source_columns":raw.columns.tolist(),
        "negative_generation_rows":int(frame["val_geracao"].lt(0).sum()),"extracted_at_utc":now()})
    save(DATA/"fonte.json",receipt)
    print(json.dumps({"filtered_path":receipt["filtered_path"],"rows":len(frame),"sha256":receipt["filtered_sha256"]}))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["congelar","verificar","baixar","extrair"])
    p.add_argument("--arquivo",action="append",default=[])
    args=p.parse_args()
    if args.action=="congelar": freeze(args.arquivo)
    elif args.action=="verificar": print(f"Selo conferido: {len(verify()['files'])} arquivos.")
    elif args.action=="baixar": download()
    else: extract()


if __name__=="__main__": main()
