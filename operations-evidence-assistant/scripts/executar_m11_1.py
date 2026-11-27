"""Entrada M11.1: usa o ambiente Chronos já preparado ou um ambiente isolado."""
from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
EXPECTED = {"torch":"2.7.1+cpu", "transformers":"4.49.0", "tokenizers":"0.21.1", "safetensors":"0.5.3"}
sys.path.insert(0, str(BASE / "src"))
from opevid.amostragem import conferir_picker, selecionar_token_top_k


def load_picker(path):
    if path is None:
        return selecionar_token_top_k
    if not path.is_file() or path.suffix.casefold() != ".py":
        raise ValueError(f"Salve primeiro seu módulo .py: {path}")
    spec = importlib.util.spec_from_file_location("m11_1_amostragem_autoral", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func = getattr(module, "selecionar_token_top_k", None)
    if not callable(func):
        raise ValueError("Defina selecionar_token_top_k no seu módulo autoral.")
    return func


def bin_python(base):
    return base / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def tem_versoes(interpreter):
    if not interpreter.is_file():
        return False
    code = ("from importlib.metadata import version; import json; print(json.dumps({k:version(k) "
            f"for k in {tuple(EXPECTED)!r}" + "}))")
    try:
        proc = subprocess.run([str(interpreter), "-c", code], text=True, capture_output=True, timeout=12)
        return proc.returncode == 0 and json.loads(proc.stdout) == EXPECTED
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def preparar(isolado):
    exe = bin_python(isolado)
    if not exe.exists():
        print(f"Criando ambiente privado: {isolado}", flush=True)
        venv.EnvBuilder(with_pip=True).create(isolado)
    if not tem_versoes(exe):
        subprocess.run([str(exe), "-m", "pip", "install", "--only-binary=:all:", "torch==2.7.1+cpu",
                        "--index-url", "https://download.pytorch.org/whl/cpu"], check=True)
        subprocess.run([str(exe), "-m", "pip", "install", "--only-binary=:all:", "-r",
                        str(BASE / "docs/m11_1/requirements.lock.txt")], check=True)
        subprocess.run([str(exe), "-m", "pip", "check"], check=True)
    return exe


def configure_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autoria", type=Path, help="Arquivo .py com selecionar_token_top_k.")
    parser.add_argument("--verificar", action="store_true", help="Só contas pequenas, sem pesos ou PyTorch.")
    parser.add_argument("--model-dir", type=Path, help="Snapshot completo já disponível, em leitura.")
    parser.add_argument("--output-dir", type=Path, default=BASE / "reports/m11_1")
    parser.add_argument("--python", type=Path, help="Use um interpretador que já tenha as versões fixadas.")
    parser.add_argument("--preparar-ambiente", action="store_true", help="Se necessário, instale em .venvs/m11_1_smol.")
    return parser


def main(argv=None):
    args = configure_parser().parse_args(argv)
    path = args.autoria.resolve() if args.autoria else None
    if args.verificar:
        n = conferir_picker(load_picker(path))
        print(f"{n} contraprovas passaram; nenhum modelo carregado.")
        return 0
    if path is not None and not path.is_file():
        raise ValueError(f"Salve seu arquivo antes de executar: {path}")
    private = ROOT / ".venvs/m11_1_smol"
    if args.python:
        exe = args.python.absolute()
        if not tem_versoes(exe):
            raise ValueError(f"O intérprete indicado não contém as versões do laboratório: {exe}")
    else:
        candidates = [bin_python(ROOT / ".venvs/m09_3_chronos"), bin_python(private), Path(sys.executable)]
        exe = next((p for p in candidates if tem_versoes(p)), None)
        if exe is None and args.preparar_ambiente:
            exe = preparar(private)
        if exe is None or not tem_versoes(exe):
            raise ValueError("Ambiente M09.3 não encontrado ou incompatível. Repita com --preparar-ambiente "
                             "para criar só o ambiente privado M11.1; não instale no Conda.")
    cmd = [str(exe), str(BASE / "scripts/laboratorio_m11_1.py"), "--output-dir", str(args.output_dir.resolve())]
    if path:
        cmd += ["--autoria", str(path)]
    if args.model_dir:
        cmd += ["--model-dir", str(args.model_dir.resolve())]
    print(f"Interpretador: {exe}", flush=True)
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", HF_HUB_OFFLINE="1",
               TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    env.pop("PYTHONPATH", None)
    return subprocess.run(cmd, env=env, check=False).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, NotImplementedError, subprocess.CalledProcessError) as exc:
        print(f"M11.1: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
