"""Confere os artefatos reais e registra a documentacao sem repetir calculos."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    result_path = HERE / "resultado.json"
    result = load_json(result_path)
    if "documentation_finalization" in result:
        raise FileExistsError("Documentacao ja finalizada; revisar antes de alterar o recibo")
    assert result["completed"] and result["verification_execution"]["exit_code"] == 0
    assert sha(HERE / "protocolo.json") == result["protocol_sha256"]
    assert sha(HERE / "aplicar_custos.py") == result["code_sha256"]
    for name, expected in result["output_sha256"].items():
        assert sha(HERE / name) == expected, name
    assert len(rows(HERE / "custos.csv")) == 36
    alarm_rows = rows(HERE / "custos_alarmes.csv")
    assert len(alarm_rows) == 66
    for row in alarm_rows:
        tp, fp, fn, tn = (int(row[name]) for name in ("tp", "fp", "fn", "tn"))
        assert tp + fp + fn + tn == int(row["rows"])
        assert tp + fn == int(row["events"])
        cost = float(row["cost_fp"]) * fp + float(row["cost_fn"]) * fn
        assert abs(cost - float(row["relative_cost_total"])) < 1e-12
        assert abs(cost / int(row["rows"]) - float(row["relative_cost_per_emission"])) < 1e-12
    clinic = ROOT / result["clinic_run"]
    assert len(rows(clinic / "perdas_blocos_24h.csv")) == 252
    assert sha(clinic / "resultado.json") == result["clinic_result_sha256"]
    for name, expected in result["clinic_output_hashes"].items():
        assert sha(clinic / name) == expected
    docs = [HERE / "parecer.md", HERE / "respostas.md", ROOT / "docs/roadmap_m00_m09/Bloco_2_Decisao_Risco.md"]
    links = 0
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target:
                continue
            assert (doc.parent / target).resolve().exists(), (doc, target)
            links += 1
    for name in ["parecer.md", "respostas.md", "protocolo.json", "adendo_verificacao.json",
                 "aplicar_custos.py", "executar_verificacao.py", "finalizar_documentacao.py"]:
        result["output_sha256"][name] = sha(HERE / name)
    result["documentation_finalization"] = {
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "Documentation and artifact audit only; no clinical, model or cost execution repeated",
        "files": [{"path": doc.relative_to(ROOT).as_posix(), "sha256": sha(doc)} for doc in docs],
        "cost_rows_checked": 36, "alarm_rows_arithmetic_checked": 66,
        "block_rows_checked": 252, "local_document_links_checked": links,
        "original_policy_context": {
            "path": "reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json",
            "sha256": sha(ROOT / "reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json"),
            "role": "Read-only explanatory context; not an input to calculated cost rules",
        },
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"completed": True, "cost_rows": 36, "alarm_rows": 66,
                      "block_rows": 252, "local_links": links}, ensure_ascii=True))


if __name__ == "__main__":
    main()
