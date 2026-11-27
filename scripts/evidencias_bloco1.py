"""Recibos de execuções locais do bloco 1; não certificam autonomia."""
from __future__ import annotations
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/fechamento_m00_m09"


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def protocol(item, description, inputs=(), criteria=()):
    out = BASE / item
    out.mkdir(parents=True, exist_ok=True)
    target = out / "protocolo.json"
    if not target.exists():
        dump(target, {"schema":"renewcast-bloco1-protocol-v1", "item":item,
             "created_at_utc":datetime.now(timezone.utc).isoformat(),
             "client_date":"2026-11-25", "description":description,
             "inputs":{str(Path(p).relative_to(ROOT)):sha(p) for p in inputs},
             "criteria":list(criteria), "historical_runs_preserved":True,
             "independent_student_response":False})
    return out


def receipt(item, checks, *, code=(), inputs=(), human_pending=False, details=None):
    out = BASE/item
    if not (out/"protocolo.json").is_file():
        raise ValueError("Grave o protocolo antes da execução.")
    dump(out/"resultado.json", {"schema":"renewcast-bloco1-result-v1", "item":item,
         "executed_at_utc":datetime.now(timezone.utc).isoformat(), "client_date":"2026-11-25",
         "python":platform.python_version(), "os":platform.system(),
         "checks":checks, "details":details or {}, "assisted_implementation":True,
         "human_assessment_pending":human_pending, "operational_approval":False,
         "inputs_sha256":{str(Path(p).relative_to(ROOT)):sha(p) for p in inputs},
         "code_sha256":{str(Path(p).relative_to(ROOT)):sha(p) for p in code},
         "output_sha256":{p.name:sha(p) for p in out.iterdir()
                          if p.is_file() and p.name!="resultado.json"}})
