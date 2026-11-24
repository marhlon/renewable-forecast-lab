"""Empacota a rodada M10.2 já executada, sem ajustar detectores novamente."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile


PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT.parent
EVIDENCE = Path(__file__).resolve().parent
RUN_ID = "20261119T101049Z_253ff59f"
RUN = PROJECT / "reports/m10_2" / RUN_ID


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    archive = ROOT / "entrega_m10_2_detectores_20261119.zip"
    if archive.exists():
        raise FileExistsError(f"Entrega existente preservada: {archive}")
    result = read_json(RUN / "resultado.json")
    audit = read_json(EVIDENCE / "auditoria_resultados.json")
    assert result["completed"] and audit["verified"]
    assert sha(PROJECT / "notebooks/m10_2_pca_autoral.py") == result["authorship_sha256"]
    original_code = {}
    with zipfile.ZipFile(ROOT / "rodada_m10_2_detectores.zip") as source_zip:
        for relative in ("scripts/executar_m10_2.py", "src/satmon/detectores_m10_2.py"):
            identity = hashlib.sha256(source_zip.read("satellite-anomaly-monitor/" + relative)).hexdigest()
            assert identity == sha(PROJECT / relative)
            original_code[relative] = identity
    record = {
        "schema": "satmon-m10-2-execution-record-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "working_directory": str(ROOT),
        "python_executable": r"C:\Users\marhl\miniconda3\envs\renewable-forecast\python.exe",
        "laboratory_executions_in_this_task": 1,
        "laboratory": {"exit_code": 0, "run_id": RUN_ID,
            "command": "python satellite-anomaly-monitor/scripts/executar_m10_2.py --autoria satellite-anomaly-monitor/notebooks/m10_2_pca_autoral.py",
            "log": "execucao_autoral.log", "small_geometric_checks": 2},
        "unit_tests": {"exit_code": 0, "passed": 8,
            "command": "python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_2_pca_autoral.py -v",
            "source_sha256": sha(PROJECT / "tests/test_m10_2_pca_autoral.py")},
        "authorship_sha256": result["authorship_sha256"],
        "resultado_sha256": sha(RUN / "resultado.json"),
        "audit_sha256": sha(EVIDENCE / "auditoria_resultados.json"),
        "code_sha256": result["code_sha256"],
        "runner_and_core_match_original_zip": original_code,
        "max_pca_difference_vs_sklearn": result["max_pca_difference_vs_sklearn"],
        "environment_versions": result["versions"],
        "open_report": {"exit_code": 0,
            "command": "Invoke-Item -LiteralPath '" + str(RUN / "relatorio.html") + "'",
            "visual_browser_inspection": False},
        "new_packages_installed": False,
        "data_downloaded": False,
        "threshold_selected": False,
        "reserved_period_used": False,
    }
    (EVIDENCE / "registro_execucao.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    readme = PROJECT / "LEIA_ENTREGA_M10_2_20261119.md"
    readme.write_text("""# Entrega M10.2 — reconstrução PCA e comparação dos detectores

A [função](notebooks/m10_2_pca_autoral.py) foi usada na execução Windows
`20261119T101049Z_253ff59f`. A rodada completa foi executada uma vez.
Passaram duas contas geométricas e a comparação dos resíduos com a biblioteca,
além de oito testes adicionais. A diferença máxima foi 3,73 × 10⁻¹⁴.

A entrega escrita está em [Resposta_M10_2.md](docs/m10_2/Resposta_M10_2.md):
função, caso real com percentis, sensibilidade ao ID dominante e conta de
transferência. O [guia passo a passo](docs/m10_2/Explicacao_Passo_a_Passo.md)
explica o percurso entre as aulas e as operações matriciais.

O [relatório HTML](reports/m10_2/20261119T101049Z_253ff59f/relatorio.html) e o
[resultado.json](reports/m10_2/20261119T101049Z_253ff59f/resultado.json)
preservam as saídas locais. A solicitação de abertura foi enviada ao Windows;
não houve inspeção visual automatizada do navegador.

## Conferir os arquivos sem ajustar novamente

Na raiz `C:\\renewable-forecast-lab`, com o ambiente existente ativo:

```powershell
python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_2_pca_autoral.py -v
python satellite-anomaly-monitor/docs/evidencias_m10_2_local/auditar_resultados.py
```

A auditoria lê a rodada fixa e recalcula coortes, resíduos, rankings, AP e
coberturas. Ela não ajusta detectores. Os escores persistidos da floresta
permitem recalcular sua avaliação; as árvores não foram exportadas como
checkpoint por este laboratório.

## Conteúdo

O ZIP contém a função, a resposta, o guia, os testes, as aulas e os códigos
originais usados no laboratório, o recorte identificado de dados e as saídas
completas desta execução. O manifesto `ENTREGA_M10_2_SHA256.json` identifica
cada arquivo incluído, exceto o próprio manifesto. Os arquivos da execução
não foram editados. O pacote complementa o projeto e usa NumPy, pandas e
scikit-learn do ambiente existente.

As anotações e a grade têm limitações descritas nas aulas e no protocolo da
fonte. AP é ranking por instante; nenhum limiar foi escolhido e o período
reservado não foi utilizado. A clínica de decisão do Renewcast é material
de revisão e não é insumo desta rodada.
""", encoding="utf-8-sig")
    files = [readme, PROJECT / "notebooks/m10_2_pca_autoral.py",
        PROJECT / "tests/test_m10_2_pca_autoral.py",
        PROJECT / "scripts/executar_m10_2.py",
        PROJECT / "src/satmon/detectores_m10_2.py", PROJECT / "src/satmon/__init__.py",
        PROJECT / "docs/COMECE_M10_2.md", RUN.parent / "latest_run.json"]
    files += sorted(p for p in (PROJECT / "docs/m10_2").iterdir() if p.is_file())
    files += sorted(p for p in (PROJECT / "data/reference/esa_mission1_m10_2").iterdir() if p.is_file())
    files += sorted(p for p in RUN.iterdir() if p.is_file())
    files += sorted(p for p in EVIDENCE.iterdir() if p.is_file() and p.suffix in {".py", ".json", ".log"})
    files = sorted(set(files))
    assert all(p.is_file() and p.is_relative_to(PROJECT) for p in files)
    manifest = {"schema": "satmon-delivery-sha256-v1", "run_id": RUN_ID,
        "files": {p.relative_to(ROOT).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in files}}
    manifest_path = PROJECT / "ENTREGA_M10_2_SHA256.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files + [manifest_path]:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for name, entry in manifest["files"].items():
            data = bundle.read(name)
            assert len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"], name
        assert bundle.read(manifest_path.relative_to(ROOT).as_posix()) == manifest_path.read_bytes()
    print(f"ZIP conferido: {archive.name}; {len(files) + 1} arquivos; {archive.stat().st_size} bytes")
    print(f"SHA256: {sha(archive)}")


if __name__ == "__main__":
    main()
