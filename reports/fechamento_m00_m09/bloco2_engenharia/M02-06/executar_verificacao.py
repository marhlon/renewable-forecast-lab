"""Registra o protocolo da verificacao, executa uma vez e preserva o log real."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen_path = HERE / "adendo_verificacao.json"
    if frozen_path.exists():
        raise FileExistsError("A verificacao ja foi protocolada; nao repetir automaticamente")
    command = [sys.executable, str(HERE / "aplicar_custos.py"), "--clinic-dir",
               str(HERE / "clinica/20261125T162028Z_f0f4439d")]
    frozen = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Execucao unica da verificacao independente e aplicacao dos custos de eventos ja definidos no protocolo original",
        "protocol_sha256": sha(HERE / "protocolo.json"),
        "code_sha256": sha(HERE / "aplicar_custos.py"),
        "wrapper_sha256": sha(Path(__file__)),
        "command": command,
        "new_training_or_inference": False,
        "new_analytic_scenarios": False,
        "clinic_rerun": False,
    }
    frozen_path.write_text(json.dumps(frozen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    finished = datetime.now(timezone.utc).isoformat()
    log_path = HERE / "execucao_verificacao.log"
    log_path.write_text("COMMAND " + json.dumps(command, ensure_ascii=False) + "\nEXIT "
                        + str(completed.returncode) + "\nSTDOUT\n" + completed.stdout
                        + "\nSTDERR\n" + completed.stderr, encoding="utf-8")
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    if completed.returncode:
        return completed.returncode
    result_path = HERE / "resultado.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["verification_execution"] = {
        "command": command, "exit_code": completed.returncode,
        "finished_at_utc": finished,
        "adendo_sha256": sha(frozen_path), "wrapper_sha256": sha(Path(__file__)),
        "log_sha256": sha(log_path),
    }
    result["output_sha256"]["execucao_verificacao.log"] = sha(log_path)
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
