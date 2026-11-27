"""Registre protocolos prévios e saídas reais das demonstrações M02."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports/fechamento_m00_m09"
SOURCES = (
    "notebooks/_fundamentos_evidencias.py",
    "notebooks/laboratorio_probabilidade.py",
    "notebooks/laboratorio_regressao_fundamentos.py",
    "docs/roadmap_m00_m09/Fundamentos_Quantitativos.md",
    "docs/roadmap_m00_m09/Avaliacao_Fundamentos.md",
    "tests/test_fundamentos_quantitativos.py",
)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare_protocol(output_root, item, design):
    """Não calcula resultados nem consome números aleatórios."""
    directory = Path(output_root).resolve() / item
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "protocolo.json"
    content = {
        "schema": "m02-fundamentos-protocol-v1",
        "item": item,
        "synthetic_only": True,
        "purpose": "Demonstração quantitativa; nenhum benchmark histórico é treinado ou reajustado.",
        "assistance": "Construção e execução assistidas; autonomia depende de resposta e revisão humanas.",
        "design": design,
        "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
    }
    if target.exists():
        previous = json.loads(target.read_text(encoding="utf-8"))
        comparable = {key: value for key, value in previous.items() if key != "frozen_at_utc"}
        if comparable != content:
            raise ValueError(f"Protocolo existente difere do código/desenho: {target}. Use outro --output-root.")
        return target
    if any(directory.iterdir()):
        raise ValueError(f"Pasta não vazia sem protocolo: {directory}. Não será sobrescrita.")
    content["frozen_at_utc"] = now()
    with target.open("x", encoding="utf-8") as handle:
        json.dump(content, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    return target


class Execution:
    def __init__(self, protocol):
        self.protocol = Path(protocol)
        self.directory = self.protocol.parent
        other = [p.name for p in self.directory.iterdir() if p.name != "protocolo.json"]
        if other:
            raise ValueError(f"Há saídas preservadas em {self.directory}: {other}. Use outro --output-root.")
        self.started = now()
        self.input_sha = sha(self.protocol)
        self.plan = json.loads(self.protocol.read_text(encoding="utf-8"))
        if datetime.fromisoformat(self.plan["frozen_at_utc"]) > datetime.fromisoformat(self.started):
            raise ValueError("O protocolo deve anteceder a execução.")

    def finish(self, results, checks):
        if sha(self.protocol) != self.input_sha:
            raise ValueError("O protocolo mudou durante a execução.")
        if not checks or any(value is not True for value in checks.values()):
            raise ValueError(f"Conferência numérica falhou: {checks}")
        receipt = {
            "schema": "m02-fundamentos-result-v1",
            "item": self.plan["item"],
            "completed": True,
            "synthetic_data": True,
            "os": platform.system(),
            "python": sys.version.split()[0],
            "versions": {name: version(name) for name in ("numpy", "scipy")},
            "protocol_frozen_at_utc": self.plan["frozen_at_utc"],
            "execution_started_at_utc": self.started,
            "execution_finished_at_utc": now(),
            "protocol_frozen_before_execution": True,
            "protocol_unchanged_after_execution": True,
            "input_sha256": {"protocolo.json": self.input_sha},
            "source_sha256": self.plan["source_sha256"],
            "output_sha256": {p.name: sha(p) for p in sorted(self.directory.iterdir()) if p.is_file()},
            "checks": checks,
            "results": results,
            "execution_responsibility": "Codex: implementação e demonstração assistidas.",
            "formative_status": "aguarda_resposta_e_revisao_humana",
            "learning_validated": False,
            "operational_approval": False,
            "benchmark_retrained": False,
        }
        write_json(self.directory / "resultado.json", receipt)
        print(f"{self.plan['item']}: {len(checks)} conferências aprovadas; {self.directory}")
        return receipt
