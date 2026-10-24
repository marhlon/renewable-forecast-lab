"""M07.1: executa a transformação em Docker, sem instalar Spark no Conda.

Execute na raiz: python scripts/executar_m07_spark.py
Autoria: python scripts/executar_m07_spark.py --autoria
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT / "data/interim/CJU_BA5EIGT_hourly.parquet"
RUN_ROOT = PROJECT / "reports/scale/CJU_BA5EIGT/m07_1"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run(command, log, capture=False):
    with log.open("a", encoding="utf-8") as f:
        f.write("\n" + subprocess.list2cmdline(command) + "\n")
        f.flush()
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace")
        pieces = []
        for line in process.stdout:
            f.write(line)
            f.flush()
            if capture:
                pieces.append(line)
            else:
                print(line, end="", flush=True)
        code = process.wait()
    if code:
        raise RuntimeError(f"Comando terminou com código {code}. Consulte {log}")
    return "".join(pieces)


def bind(source, target, readonly=True):
    source = str(Path(source).resolve())
    if "," in source:
        raise ValueError("Use um caminho sem vírgulas para o bind mount Docker.")
    return ["--mount", f"type=bind,source={source},target={target}" + (",readonly" if readonly else "")]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--autoria", action="store_true")
    parser.add_argument("--shuffle-partitions", type=int, choices=range(1, 33), default=2, metavar="1..32")
    args = parser.parse_args(argv)
    source = args.input.resolve()
    if not source.is_file():
        parser.error(f"Série horária não encontrada: {source}. Informe --input com o arquivo existente.")
    if not shutil.which("docker"):
        parser.error("Docker não encontrado. Abra o Docker Desktop usado em M06.")
    context = PROJECT / "infra/m07_spark"
    required = [context / "Dockerfile", context / "requirements.txt",
                PROJECT / "tools/m07_transformacao.py", PROJECT / "notebooks/transformacao_spark.py"]
    for p in required:
        if not p.is_file():
            parser.error(f"Arquivo do pacote ausente: {p}")
    # Verificação estática: não importa PySpark no ambiente Conda.
    if args.autoria:
        import ast
        print(f"Arquivo de autoria: {required[-1].resolve()}", flush=True)
        tree = ast.parse(required[-1].read_text(encoding="utf-8-sig"))
        sql = next((n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "SQL_AUTORAL" for t in n.targets)), None)
        if sql is None or (isinstance(sql, ast.Constant) and not sql.value):
            parser.error(f"SQL_AUTORAL está ausente/vazio no arquivo salvo: {required[-1].resolve()}. "
                         "Salve a edição nesse caminho antes de executar --autoria.")
    mode = "autoria" if args.autoria else "guiado"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    output = RUN_ROOT / run_id
    output.mkdir(parents=True, exist_ok=False)
    log = output / "pipeline.log"
    before = digest(source)
    context_hash = hashlib.sha256((digest(required[0]) + digest(required[1])).encode()).hexdigest()
    image_tag = "renewcast-spark-m07:" + context_hash[:12]
    try:
        ostype = run(["docker", "info", "--format", "{{.OSType}}"], log, capture=True).strip()
        if ostype != "linux":
            raise RuntimeError("Selecione contêineres Linux no Docker Desktop.")
        print("M07.1: série horária existente; PySpark 4.0.1 e DuckDB 1.4.1; 2 CPUs/3 GiB.", flush=True)
        print("Primeiro build baixa Java e Spark (centenas de MB); os seguintes reutilizam o cache.", flush=True)
        run(["docker", "build", "--platform", "linux/amd64", "-t", image_tag, str(context)], log)
        image_info = json.loads(run(["docker", "image", "inspect", image_tag], log, capture=True))[0]
        image_id = image_info["Id"]
        write_json(output / "image.json", image_info)
        # O codec Zstd extrai uma biblioteca nativa em /tmp. A montagem precisa
        # permitir seu carregamento executável; a raiz continua somente leitura.
        command = ["docker", "run", "--rm", "--pull", "never", "--platform", "linux/amd64",
                   "--cpus", "2", "--memory", "3g", "--pids-limit", "512", "--network", "none",
                   "--hostname", "renewcast-spark", "--add-host", "renewcast-spark:127.0.0.1",
                   "--read-only", "--tmpfs", "/tmp:rw,exec,nosuid,nodev,size=512m", "--cap-drop", "ALL",
                   "--security-opt", "no-new-privileges"]
        command += bind(source, "/inputs/geracao.parquet")
        command += bind(PROJECT / "tools", "/work/tools")
        command += bind(PROJECT / "notebooks", "/work/notebooks")
        command += bind(output, "/output", readonly=False)
        command += [image_id, "--input", "/inputs/geracao.parquet", "--output", "/output/results",
                    "--shuffle-partitions", str(args.shuffle_partitions)]
        if args.autoria:
            command += ["--author", "/work/notebooks/transformacao_spark.py"]
        run(command, log)
        verification = output / "results/verification.json"
        data = json.loads(verification.read_text(encoding="utf-8"))
        if data.get("verified") is not True or data["source"]["source_sha256"] != before or digest(source) != before:
            raise RuntimeError("Recibo ou preservação da entrada divergente.")
        for name, expected in data["output_sha256"].items():
            p = (verification.parent / name).resolve()
            if not p.is_relative_to(verification.parent.resolve()) or digest(p) != expected:
                raise RuntimeError(f"Saída divergente: {name}")
        host = {"schema": "renewcast-m07-host-v1", "verified": True, "run_id": run_id, "mode": mode,
                "source_file": str(source), "source_sha256": before, "source_preserved": True,
                "image_id": image_id, "context_sha256": context_hash,
                "verification_sha256": digest(verification), "pipeline_sha256": digest(log),
                "image_inspection_sha256": digest(output / "image.json"),
                "controller_sha256": digest(__file__), "author_implementation_executed": args.autoria}
        write_json(output / "host_verification.json", host)
        write_json(RUN_ROOT / "latest_run.json", {"run_id": run_id, "directory": str(output),
                    "host_verification_sha256": digest(output / "host_verification.json")})
        print(f"Concluído: {mode}; entrada preservada; hashes conferidos.")
        print(f"Pasta Windows: {output}")
        print(f"Planos, tabelas e tempos: {output / 'results/real'}")
    except Exception as exc:
        write_json(output / "failure.json", {"type": type(exc).__name__, "detail": str(exc)})
        print(f"Falha: {exc}\nEvidências preservadas: {output}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
