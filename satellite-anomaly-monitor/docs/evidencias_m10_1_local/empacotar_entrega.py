"""Reúne código, dados identificados e evidências da entrega M10.1."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile


PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT.parent
EVIDENCE = Path(__file__).resolve().parent
RUN_ID = "20261118T203614Z_7e13daae"
RUN = PROJECT / "reports/m10_1" / RUN_ID


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    archive = ROOT / "entrega_m10_1_telemetria_20261118.zip"
    if archive.exists():
        raise FileExistsError(f"Entrega existente preservada: {archive}")
    result = read_json(RUN / "resultado.json")
    audit = read_json(EVIDENCE / "auditoria_resultados.json")
    assert result["completed"] and audit["verified"]
    assert result["authorship_sha256"] == sha(PROJECT / "notebooks/m10_sincronizacao_autoral.py")
    original = EVIDENCE / "executar_m10_1_antes_ajuste_resolucao.py"
    record = {
        "schema": "satmon-m10-1-execution-record-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_type": "observed_process_results_and_saved_logs",
        "working_directory": str(ROOT),
        "python_executable": r"C:\Users\marhl\miniconda3\envs\renewable-forecast\python.exe",
        "contract_check": {"exit_code": 0, "groups_passed": 5,
            "run_id": "20261118T202955Z_34b6fa2e", "log": "conferencia_autoral.log"},
        "unit_tests": {"exit_code": 0, "tests_passed": 10,
            "command": "python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_sincronizacao_autoral.py -v",
            "test_source_sha256": sha(PROJECT / "tests/test_m10_sincronizacao_autoral.py")},
        "failed_execution": {"exit_code": 1, "run_id": "20261118T203124Z_62f4fd1a",
            "log": "execucao_autoral_falha_resolucao.log",
            "failure": "Same grid instants, but Series.equals rejected us/ns dtype mismatch in pandas 3.0.5."},
        "completed_execution": {"exit_code": 0, "run_id": RUN_ID, "log": "execucao_autoral.log",
            "command": "python satellite-anomaly-monitor/scripts/executar_m10_1.py --autoria satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py"},
        "compatibility_fix": {"path": "satellite-anomaly-monitor/scripts/executar_m10_1.py",
            "change": "Cast the generated UTC grid to datetime64[ns, UTC] before synchronization and equality check.",
            "original_backup": original.relative_to(PROJECT).as_posix(),
            "original_sha256": sha(original), "current_sha256": result["code_sha256"]["runner"],
            "small_reproduction_observed": {"pandas": "3.0.5", "same_instants": True,
                "result_dtype": "datetime64[ns, UTC]", "original_grid_dtype": "datetime64[us, UTC]",
                "equals_before_normalization": False, "equals_after_normalization": True}},
        "authorship_sha256": result["authorship_sha256"],
        "resultado_sha256": sha(RUN / "resultado.json"),
        "audit_sha256": sha(EVIDENCE / "auditoria_resultados.json"),
        "source_sha256": result["source_spec_sha256"],
        "environment_installed_or_modified": False,
        "data_downloaded_in_this_task": False,
        "models_trained": False,
        "open_report": {"command": "Invoke-Item -LiteralPath '" + str(RUN / "relatorio.html") + "'",
            "exit_code": 0, "visual_browser_inspection": False},
    }
    (EVIDENCE / "registro_execucao.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    readme = PROJECT / "LEIA_ENTREGA_M10_1.md"
    readme.write_text("""# Entrega M10.1 — grade causal de telemetria

A implementação está em `notebooks/m10_sincronizacao_autoral.py`. A execução
Windows `20261118T203614Z_7e13daae` usou esse arquivo e terminou com código zero.
Passaram cinco grupos de conferência, dez testes adicionais e a comparação
integral com a referência. A auditoria por searchsorted confere os arquivos
salvos sem importar o sincronizador.

Leia a [explicação passo a passo](docs/Explicacao_M10_1_Passo_a_Passo.md) e
o [parecer com as quatro respostas](reports/parecer_m10_1.md).
O [relatório HTML](reports/m10_1/20261118T203614Z_7e13daae/relatorio.html),
o [resultado.json](reports/m10_1/20261118T203614Z_7e13daae/resultado.json)
e o [perfil dos canais](reports/m10_1/20261118T203614Z_7e13daae/perfil_canais.csv)
identificam a execução completa.

## Repetir no ambiente existente

Na raiz `C:\\renewable-forecast-lab`, com `renewable-forecast` ativo:

```powershell
python satellite-anomaly-monitor/scripts/executar_m10_1.py --autoria satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py --verificar
python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_sincronizacao_autoral.py -v
python satellite-anomaly-monitor/docs/evidencias_m10_1_local/auditar_resultados.py
```

Uma nova execução anual usa o mesmo comando sem `--verificar`. Ela cria outra
pasta e atualiza `latest_run.json`. A auditoria desta entrega fixa o run acima;
o ponteiro precisa corresponder ao run auditado, ou a verificação interrompe.

## O que foi preservado

Foram incluídos os CSVs derivados e os metadados fornecidos, com atribuição
e hashes da fonte, além do código e das saídas da execução concluída.
Não há download, novo ambiente ou treinamento nesses comandos.

O executor recebeu um ajuste de compatibilidade no pandas 3: a grade é
explicitamente UTC/ns, evitando confundir igualdade dos instantes com a
diferença de resolução us/ns. O backup anterior e o log da primeira tentativa
estão em `docs/evidencias_m10_1_local`. As datas e a regra causal permanecem
as mesmas.

`ENTREGA_M10_1_SHA256.json` identifica todos os membros do ZIP, exceto o próprio
manifesto. Os arquivos da execução não foram editados. As contagens de
frescor não comprovam funcionamento normal e nenhum detector foi treinado.
O checksum do arquivo público completo de 3,8 GB continua não verificado,
conforme `data/reference/esa_mission1_2007/source.json`.
""", encoding="utf-8-sig")

    files = [readme, PROJECT / "LEIA_M10_1.md",
        PROJECT / "notebooks/m10_sincronizacao_autoral.py",
        PROJECT / "tests/test_m10_sincronizacao_autoral.py",
        PROJECT / "scripts/executar_m10_1.py",
        PROJECT / "src/satmon/temporal.py", PROJECT / "src/satmon/__init__.py",
        PROJECT / "docs/Aula_M10_1_Contrato_Telemetria.md",
        PROJECT / "docs/Explicacao_M10_1_Passo_a_Passo.md",
        PROJECT / "reports/parecer_m10_1.md", RUN.parent / "latest_run.json",
        RUN.parent / "20261118T202955Z_34b6fa2e/conferencia.json"]
    files += sorted(p for p in RUN.iterdir() if p.is_file())
    files += sorted(p for p in (PROJECT / "data/reference/esa_mission1_2007").iterdir() if p.is_file())
    files += sorted(p for p in EVIDENCE.iterdir() if p.is_file() and p.suffix in {".py", ".json", ".log"})
    files = sorted(set(files))
    assert all(p.is_file() and p.is_relative_to(PROJECT) for p in files)
    manifest = {"schema": "satmon-delivery-sha256-v1", "run_id": RUN_ID,
        "files": {p.relative_to(ROOT).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in files}}
    manifest_path = PROJECT / "ENTREGA_M10_1_SHA256.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files + [manifest_path]:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for name, entry in manifest["files"].items():
            content = bundle.read(name)
            assert len(content) == entry["bytes"] and hashlib.sha256(content).hexdigest() == entry["sha256"], name
        assert bundle.read(manifest_path.relative_to(ROOT).as_posix()) == manifest_path.read_bytes()
    print(f"ZIP conferido: {archive.name}; {len(files) + 1} arquivos; {archive.stat().st_size} bytes")
    print(f"SHA256: {sha(archive)}")


if __name__ == "__main__":
    main()
