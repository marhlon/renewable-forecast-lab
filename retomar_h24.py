r"""Retoma o experimento h24 no projeto existente, parando no primeiro erro.

Extraia junto com a pasta h24_20261001 na raiz renewable-forecast-lab.
Executar: python .\retomar_h24.py
Somente verificar a instalação: python .\retomar_h24.py --check-only
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys


RELEASE = "2026.10.01-h24"
SOURCE_SHA256 = "d09375f57f7efdd9f5268bf4acbcfd4555249132666c8b0df39a14d866fda6c4"
MODULES = ("weather_history", "weather_training", "weather_ablation")


def check_module_paths(project: Path) -> None:
    """Consulta o mesmo interpretador que executará as três etapas."""
    probe = (
        "import importlib.util, json; "
        f"names={MODULES!r}; "
        "print(json.dumps({n: importlib.util.find_spec('renewable_forecast.'+n).origin for n in names}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], cwd=project, text=True,
        capture_output=True, check=True,
    )
    loaded = json.loads(result.stdout)
    for name, actual in loaded.items():
        expected = project / "src" / "renewable_forecast" / f"{name}.py"
        if actual is None or Path(actual).resolve() != expected.resolve():
            raise ValueError(
                f"{name} foi localizado em {actual}; esperado: {expected}. "
                "Confira a instalação editável neste ambiente antes de continuar."
            )
    print(f"Módulo localizado: {loaded['weather_history']}", flush=True)


def install_weather_history(project: Path) -> None:
    source = project / "h24_20261001" / "weather_history.py"
    target = project / "src" / "renewable_forecast" / "weather_history.py"
    payload = source.read_bytes()
    if hashlib.sha256(payload).hexdigest() != SOURCE_SHA256:
        raise ValueError("O módulo do pacote difere da versão conferida. Extraia novamente o ZIP completo.")
    ast.parse(payload, filename=str(source))
    if not target.is_file():
        raise FileNotFoundError(f"Módulo do projeto não localizado: {target}")
    if target.read_bytes() != payload:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = project / "backups" / "h24_20261001" / f"weather_history_{stamp}.py"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        shutil.copyfile(source, target)
        print(f"Cópia anterior preservada: {backup}", flush=True)
    # Evita reutilizar bytecode do módulo substituído; só remove seu cache padrão.
    Path(importlib.util.cache_from_source(str(target))).unlink(missing_ok=True)
    print(f"Módulo conferido e aplicado: {target}", flush=True)


def check_loaded_release(project: Path) -> None:
    prefix = [sys.executable, "-m", "renewable_forecast.weather_history"]
    version = subprocess.run(
        [*prefix, "--version"], cwd=project, text=True,
        capture_output=True, check=True,
    )
    if f"weather_history {RELEASE}" not in version.stdout:
        raise ValueError(f"Versão carregada inesperada: {version.stdout.strip()}")
    help_result = subprocess.run(
        [*prefix, "--help"], cwd=project, text=True,
        capture_output=True, check=True,
    )
    for flag in ("--horizon-hours", "--cache-only"):
        if flag not in help_result.stdout:
            raise ValueError(f"A interface carregada não reconhece {flag}.")
    print(version.stdout.strip(), flush=True)
    print("Interface confirmada: --horizon-hours e --cache-only.", flush=True)


def pipeline_steps():
    weather = "data/interim/weather/CJU_BA5EIGT/july_development_h24"
    modeling = "data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development"
    reports = "reports/weather_ablation/CJU_BA5EIGT/july_development_h24"
    return [
        ("1/3: selecionar e agregar meteorologia h24", "weather_history", [
            "--registry", "data/reference/CJU_BA5EIGT/asset_registry.csv",
            "--origin-start", "2026-07-01T06:00:00Z",
            "--origin-end", "2026-08-01T05:00:00Z",
            "--run-root", "data/external/weather/CJU_BA5EIGT",
            "--output-dir", weather, "--horizon-hours", "24", "--cache-only",
        ]),
        ("2/3: integrar geração e vento", "weather_training", [
            "--generation", "data/interim/CJU_BA5EIGT_hourly.parquet",
            "--weather-dir", f"{weather}/h24_spatial_sample",
            "--conjunto", "CJU_BA5EIGT",
            "--generation-timezone", "America/Sao_Paulo",
            "--horizon-hours", "24", "--availability-delay-hours", "2",
            "--output-dir", modeling,
        ]),
        ("3/3: comparar os dois HGB nos três folds", "weather_ablation", [
            "--input-dir", modeling, "--output-dir", reports,
            "--n-splits", "3", "--test-size-hours", "168",
        ]),
    ]


def run_pipeline(project: Path) -> None:
    for title, module, arguments in pipeline_steps():
        print(f"\n{title}", flush=True)
        command = [sys.executable, "-u", "-m", f"renewable_forecast.{module}", *arguments]
        print(subprocess.list2cmdline(command), flush=True)
        # Falha de uma etapa impede imediatamente a execução da seguinte.
        subprocess.run(command, cwd=project, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    try:
        print(f"Python: {sys.executable}", flush=True)
        if sys.version_info[:2] != (3, 12):
            raise ValueError("O projeto requer Python 3.12. Ative o ambiente renewable-forecast.")
        for relative in (
            "pyproject.toml", "h24_20261001/weather_history.py",
            "data/reference/CJU_BA5EIGT/asset_registry.csv",
            "data/interim/CJU_BA5EIGT_hourly.parquet",
        ):
            if not (project / relative).is_file():
                raise FileNotFoundError(f"Arquivo necessário ausente: {project / relative}")
        check_module_paths(project)
        install_weather_history(project)
        check_loaded_release(project)
        if args.check_only:
            print("Instalação conferida; experimento não iniciado.", flush=True)
            return 0
        run_pipeline(project)
        print("\nExperimento h24 concluído.", flush=True)
        print(f"Relatórios: {project / 'reports/weather_ablation/CJU_BA5EIGT/july_development_h24'}")
        print("Enviar: summary.csv, fold_metrics.csv, folds.csv, predictions.csv, protocol.json e metadata.json.")
        return 0
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, end="", flush=True)
        if exc.stderr:
            print(exc.stderr, end="", file=sys.stderr, flush=True)
        print(f"\nINTERROMPIDO: comando terminou com código {exc.returncode}. Etapas seguintes não executadas.", file=sys.stderr)
        return exc.returncode or 1
    except (OSError, ValueError, SyntaxError) as exc:
        print(f"\nINTERROMPIDO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
