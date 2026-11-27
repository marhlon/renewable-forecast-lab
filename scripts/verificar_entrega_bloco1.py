"""Confira os artefatos já executados do bloco 1 sem repetir laboratórios."""
from pathlib import Path
import json
import hashlib

ROOT=Path(__file__).resolve().parents[1]
FIELDS=("output_sha256","deliverables_sha256","source_sha256","code_sha256",
        "inputs_sha256","input_sha256","historical_inputs_sha256")
def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()
def main():
    data=json.loads((ROOT/"config/roadmap_m00_m09.json").read_text(encoding="utf-8"))
    checked=[]; failures=[]
    for item in data["items"]:
        if item["etapa"]>3: continue
        original=ROOT/"reports/fechamento_m00_m09"/item["id"]/"resultado.json"
        receipts={original, *(ROOT/p for p in item["entregaveis"]
                   if Path(p).name=="resultado.json" or Path(p).name.endswith("_resultado.json"))}
        for receipt in sorted(receipts):
            if not receipt.is_file():
                failures.append({"item":item["id"],"missing":str(receipt.relative_to(ROOT))})
                continue
            folder=receipt.parent
            r=json.loads(receipt.read_text(encoding="utf-8"))
            for field in FIELDS:
                records=r.get(field)
                if not isinstance(records,dict): continue
                for name,want in records.items():
                    if not isinstance(want,str) or len(want)!=64: continue
                    # pyproject.toml é declarado pelos recibos como arquivo da raiz.
                    # Os demais basenames (protocolo.json, executar.py etc.) são locais ao recibo.
                    path=ROOT/name if ("/" in name or "\\" in name or name=="pyproject.toml") else folder/name
                    try:
                        got=digest(path)
                        ok=got==want
                    except OSError as e:
                        got=type(e).__name__; ok=False
                    result={"item":item["id"],"receipt":str(receipt.relative_to(ROOT)),
                            "field":field,"path":str(path.relative_to(ROOT)),
                            "expected":want,"actual":got,"match":ok}
                    checked.append(result)
                    if not ok: failures.append(result)
        for name in item["entregaveis"]:
            if not (ROOT/name).is_file():
                failures.append({"item":item["id"],"missing_deliverable":name})
    output={"schema":"renewcast-bloco1-artifact-review-v1","checked_hash_declarations":len(checked),
            "all_match":not failures,"failures":failures,"checks":checked,
            "method":"Read existing receipts and bytes; no lab/model/test reexecution."}
    target=ROOT/"docs/roadmap_m00_m09/conferencia_artefatos_bloco1.json"
    target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:output[k] for k in ("checked_hash_declarations","all_match","failures")},ensure_ascii=False))
    return 0 if not failures else 1
if __name__=="__main__":
    raise SystemExit(main())
