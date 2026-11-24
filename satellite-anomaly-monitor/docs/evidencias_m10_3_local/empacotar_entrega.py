"""Reúne a rodada M10.3 concluída sem executar novamente a avaliação."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile


PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT.parent
EVIDENCE = Path(__file__).resolve().parent
RUN_ID = "20261123T195301Z_332fb306"
RUN = PROJECT / "reports/m10_3" / RUN_ID
M102 = PROJECT / "reports/m10_2/20261119T101049Z_253ff59f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    archive = ROOT / "entrega_m10_3_alarmes_20261123.zip"
    if archive.exists():
        raise FileExistsError(f"Entrega existente preservada: {archive}")
    result = read_json(RUN / "resultado.json")
    audit = read_json(EVIDENCE / "auditoria_resultados.json")
    assert result["completed"] and audit["verified"]
    assert sha(PROJECT / "notebooks/m10_3_alarme_autoral.py") == result["authorship_sha256"]
    original_code = {}
    with zipfile.ZipFile(ROOT / "rodada_m10_3_alarmes.zip") as source_zip:
        for relative in ("scripts/executar_m10_3.py", "src/satmon/alarmes_m10_3.py"):
            identity = hashlib.sha256(source_zip.read("satellite-anomaly-monitor/" + relative)).hexdigest()
            assert identity == sha(PROJECT / relative)
            original_code[relative] = identity

    record = {
        "schema": "satmon-m10-3-execution-record-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "working_directory": str(ROOT),
        "python_executable": r"C:\Users\marhl\miniconda3\envs\renewable-forecast\python.exe",
        "laboratory_executions_in_this_task": 1,
        "laboratory": {"exit_code": 0, "run_id": RUN_ID,
            "command": "python satellite-anomaly-monitor/scripts/executar_m10_3.py --autoria satellite-anomaly-monitor/notebooks/m10_3_alarme_autoral.py",
            "log": "execucao_autoral.log"},
        "unit_tests": {"exit_code": 0, "passed": 10,
            "command": "python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_3_alarme_autoral.py -v",
            "source_sha256": sha(PROJECT / "tests/test_m10_3_alarme_autoral.py")},
        "authorship_sha256": result["authorship_sha256"],
        "resultado_sha256": sha(RUN / "resultado.json"),
        "frozen_policy_sha256": result["politica_sha256"],
        "audit_sha256": sha(EVIDENCE / "auditoria_resultados.json"),
        "runner_and_core_match_original_zip": original_code,
        "source_m10_2_run_id": result["source_run_id"],
        "original_forest_reconstructed_by_laboratory": result["reconstituicao_floresta_usou_somente_ajuste_original"],
        "max_development_score_reconstruction_delta": result["max_delta_escore_dev_para_pontuar_teste"],
        "audit_replayed_only_frozen_policy_on_test": True,
        "alternative_policy_executed_on_test": False,
        "environment_versions": result["versions"],
        "open_report": {"exit_code": 0,
            "command": "Invoke-Item -LiteralPath '" + str(RUN / "relatorio.html") + "'",
            "visual_browser_inspection": False},
        "packages_installed": False, "data_downloaded": False,
    }
    (EVIDENCE / "registro_execucao.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    readme = PROJECT / "LEIA_ENTREGA_M10_3_20261123.md"
    readme.write_text("""# Entrega M10.3 — inícios de alarme e transferência temporal

A [função](notebooks/m10_3_alarme_autoral.py) foi usada na execução Windows
`20261123T195301Z_332fb306`. O laboratório foi executado uma vez, a partir
do M10.2 `20261119T101049Z_253ff59f` preservado. Passaram os exemplos do
runner, a comparação em todas as candidatas de desenvolvimento e na política
congelada do teste, além de dez testes adicionais.

Leia a [resposta preenchida](docs/m10_3/Resposta_M10_3.md), com a função e
os três itens pedidos, e o [guia](docs/m10_3/Explicacao_Passo_a_Passo.md).
O [relatório HTML](reports/m10_3/20261123T195301Z_332fb306/relatorio.html)
e o [resultado.json](reports/m10_3/20261123T195301Z_332fb306/resultado.json)
identificam a política e as métricas locais.

A política escolhida detectou 3/8 IDs no desenvolvimento e 0/8 no teste.
O maior escore utilizável do teste ficou abaixo do limiar, sem qualquer
cruzamento. Precisão e atraso ficaram indefinidos. O resultado foi preservado;
nenhum limiar alternativo ou ablação foi executado no teste nesta entrega.

## Conferir sem nova avaliação ou ajuste

Na raiz `C:\\renewable-forecast-lab`, com o ambiente existente ativo:

```powershell
python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_3_alarme_autoral.py -v
python satellite-anomaly-monitor/docs/evidencias_m10_3_local/auditar_resultados.py
```

A auditoria recalcula as candidatas apenas no desenvolvimento e faz o
replay da política congelada no teste, usando os escores persistidos.
Não reconstitui a floresta. O laboratório original reconstituiu somente
essa floresta com o ajuste de 2004–2007 e verificou os escores no desenvolvimento.

## Conteúdo e rastreabilidade

O ZIP reúne função, respostas, explicação, testes, código, protocolo e
dados da rodada, além da execução M10.2 fixada e de suas dependências
locais para conferir os arquivos. Não inclui ambiente Python instalado.
A atribuição dos dados ESA permanece nas aulas e na proveniência.
O manifesto `ENTREGA_M10_3_SHA256.json` identifica os membros incluídos,
exceto o próprio manifesto. Os arquivos das execuções foram preservados.

A abertura do HTML foi solicitada ao Windows; não houve inspeção visual
automatizada do navegador. A auditoria registra seus limites: hashes e
cronologia de gravação não são um log independente da primeira leitura do
teste, nem comprovam latência física ou completude das anotações.
""", encoding="utf-8-sig")

    files = [readme, PROJECT / "notebooks/m10_3_alarme_autoral.py",
        PROJECT / "tests/test_m10_3_alarme_autoral.py", PROJECT / "tests/test_m10_3_alarmes.py",
        PROJECT / "scripts/executar_m10_3.py", PROJECT / "src/satmon/alarmes_m10_3.py",
        PROJECT / "src/satmon/__init__.py", PROJECT / "docs/COMECE_M10_3.md",
        PROJECT / "scripts/executar_m10_2.py", PROJECT / "src/satmon/detectores_m10_2.py",
        PROJECT / "notebooks/m10_2_pca_autoral.py", RUN.parent / "latest_run.json"]
    for folder in (PROJECT / "docs/m10_3", PROJECT / "data/reference/esa_mission1_m10_2",
                   PROJECT / "data/reference/esa_mission1_m10_3", RUN, M102, EVIDENCE):
        files += sorted(p for p in folder.iterdir() if p.is_file())
    files = sorted(set(files))
    assert all(p.is_file() and p.is_relative_to(PROJECT) for p in files)
    manifest = {"schema": "satmon-delivery-sha256-v1", "run_id": RUN_ID,
        "files": {p.relative_to(ROOT).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in files}}
    manifest_path = PROJECT / "ENTREGA_M10_3_SHA256.json"
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
