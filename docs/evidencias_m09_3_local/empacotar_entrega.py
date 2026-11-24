"""Reúne a entrega M09.3 e confere cada membro do ZIP após a gravação."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
RUN_ID = "20261117T213329Z_3b201a01"
BASELINE_ID = "20261115T170309Z_90a6625f"
RUN = ROOT / "reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado" / RUN_ID
BASELINE = ROOT / "reports/neural/CJU_BA5EIGT/m08_3_gru" / BASELINE_ID


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    archive = ROOT / "entrega_m09_3_pre_treinado_20261117.zip"
    if archive.exists():
        raise FileExistsError(f"Entrega existente preservada: {archive}")
    protocol = read_json(RUN / "protocol.json")
    result = read_json(RUN / "resultado.json")
    assert result["completed"] is True
    assert sha(ROOT / "notebooks/m09_alinhamento_autoral.py") == protocol["authorship_sha256"]
    audit = read_json(EVIDENCE / "auditoria_resultados.json")
    assert audit["verified"] is True and audit["data_checks_passed"] is True

    python = r"C:\Users\marhl\miniconda3\envs\renewable-forecast\python.exe"
    author = "notebooks/m09_alinhamento_autoral.py"
    record = {
        "schema": "renewcast-m09-3-execution-record-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "observed_process_results_and_generated_protocol",
        "note": "Registro dos comandos observados. Não é transcrição bruta do terminal.",
        "working_directory": str(ROOT),
        "recorded_paths_use_forward_slashes": True,
        "run_id": RUN_ID,
        "baseline_run_id": BASELINE_ID,
        "commands_observed": [
            {
                "purpose": "Conferência integrada sem inferência",
                "argv": [python, "notebooks/laboratorio_pre_treinado.py", "--autoria", author, "--verificar"],
                "exit_code": 0,
                "verification_groups_passed": 5,
                "output_directory": "reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado/20261117T213319Z_983deae2",
            },
            {
                "purpose": "Inferência autoral completa em Windows/CPU",
                "argv": [python, "scripts/executar_m09_3.py", "--autoria", author, "--offline",
                         "--baseline-run-dir", BASELINE.relative_to(ROOT).as_posix()],
                "exit_code": 0,
                "output_directory": RUN.relative_to(ROOT).as_posix(),
            },
            {
                "purpose": "Testes adicionais do alinhamento",
                "argv": [python, "-m", "unittest", "discover", "-s", "tests", "-p",
                         "test_m09_alinhamento_autoral.py", "-v"],
                "exit_code": 0,
                "tests_run": 10,
                "tests_passed": 10,
            },
            {
                "purpose": "Abrir o relatório no aplicativo padrão do Windows",
                "powershell_command": "Invoke-Item -LiteralPath '" + str(RUN / "relatorio.html") + "'",
                "exit_code": 0,
                "visual_browser_inspection": False,
                "note": "Abertura solicitada ao Windows. Automação visual indisponível nesta sessão.",
            },
        ],
        "authorship_sha256": protocol["authorship_sha256"],
        "protocol_sha256": sha(RUN / "protocol.json"),
        "resultado_sha256": sha(RUN / "resultado.json"),
        "audit_sha256": sha(EVIDENCE / "auditoria_resultados.json"),
        "tests_source_sha256": sha(ROOT / "tests/test_m09_alinhamento_autoral.py"),
        "environment_reused": True,
        "snapshot_reused": True,
        "network_downloads_in_this_execution": False,
        "vendor_warning": "Aviso de depreciação de past_key_values em dependência; execução concluída com código 0.",
    }
    (EVIDENCE / "registro_execucao.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    readme = ROOT / "LEIA_ENTREGA_M09_3_20261117.md"
    readme.write_text(
        """# Entrega M09.3 — alinhamento e comparação pré-treinada

A função `notebooks/m09_alinhamento_autoral.py` está implementada e foi usada
na execução Windows `20261117T213329Z_3b201a01`. Passaram cinco grupos da
conferência integrada e dez testes de unidade. O alinhamento usa timestamps:
h24 com atraso d2 exige passo 26, índice 25.

Comece pela [explicação passo a passo](docs/Explicacao_M09_3_Passo_a_Passo.md)
e pelo [parecer integrado](reports/parecer_m09_pre_treinado.md).
O [relatório HTML](reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado/20261117T213329Z_3b201a01/relatorio.html)
reúne as dez variantes e os alvos. O comando de abertura foi enviado ao Windows;
a inspeção visual do navegador não estava disponível nesta sessão.

Nos mesmos 168 alvos, Chronos P50 obteve MAE 31,340738 MWmed, contra
32,323956 do HGB: redução de 3,041763%. O RMSE piorou e o viés diminuiu.
O intervalo bruto P10–P90 cobriu 135/168 alvos, com largura média de
83,595237 MWmed. A conclusão é de desenvolvimento; não houve promoção operacional.

## Conferência no projeto existente

```powershell
Set-Location C:\\renewable-forecast-lab
conda activate renewable-forecast
python -m unittest discover -s tests -p test_m09_alinhamento_autoral.py -v
python docs/evidencias_m09_3_local/auditar_resultados.py
```

O script de auditoria só lê e recalcula artefatos; não executa o modelo.
O JSON de auditoria e o registro de comandos ficam em
`docs/evidencias_m09_3_local`. Os scripts dos gráficos também estão nessa pasta.

Para nova inferência usando o ambiente privado e o snapshot já existentes:

```powershell
python scripts/executar_m09_3.py --autoria --offline --baseline-run-dir reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f
```

## Conteúdo e integridade

O ZIP contém a função, testes, aula, guia, parecer, gráficos, códigos do
laboratório, entradas e baselines usados na conferência, além dos resultados
completos desta execução. `ENTREGA_M09_3_SHA256.json` registra a identidade
de cada arquivo incluído. Nenhum resultado de execução foi editado.

Este é um pacote complementar ao projeto. O ambiente `.venvs` e os pesos
binários do modelo permanecem no projeto local e não estão duplicados no ZIP.
O model card, a configuração e a identidade dos pesos estão incluídos.
Uma pasta vazia extraída do ZIP não terá ambiente e pesos para executar
inferência offline. O modo padrão da auditoria exige o snapshot local completo.

Não extraia este pacote sobre trabalhos posteriores sem comparar os arquivos.
Os ponteiros `latest_run.json` refletem o estado desta entrega.
""",
        encoding="utf-8-sig",
    )

    files = [
        readme,
        ROOT / author,
        ROOT / "tests/test_m09_alinhamento_autoral.py",
        ROOT / "docs/Aula_M09_3_Pre_Treinado.md",
        ROOT / "docs/Explicacao_M09_3_Passo_a_Passo.md",
        ROOT / "reports/parecer_m09_pre_treinado.md",
        ROOT / "docs/model_source_m09_3.json",
        ROOT / "docs/requirements_m09_3.lock.txt",
        RUN.parent / "latest_run.json",
    ]
    files += sorted(p for p in RUN.iterdir() if p.is_file())
    files += [BASELINE / name for name in protocol["baseline_hashes"]]
    files += [ROOT / "dist/databricks/CJU_BA5EIGT/m07_3" / name for name in protocol["input_sha256"]]
    files += [ROOT / "notebooks" / name for name in protocol["code_sha256"] if name != "executar_m09_3.py"]
    files += [ROOT / "scripts/executar_m09_3.py"]
    files += sorted(p for p in EVIDENCE.iterdir() if p.is_file() and p.suffix in {".py", ".json", ".png"})
    standalone = RUN.parent / "20261117T213319Z_983deae2/conferencia.json"
    files.append(standalone)
    snapshot = ROOT / "models/pretrained/chronos-bolt-tiny" / protocol["model"]["revision"]
    files += [snapshot / "README.md", snapshot / "config.json"]
    files = sorted(set(files))
    for path in files:
        assert path.is_file(), path
        assert path.is_relative_to(ROOT), path

    manifest = {
        "schema": "renewcast-delivery-sha256-v1",
        "run_id": RUN_ID,
        "files": {
            p.relative_to(ROOT).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in files
        },
        "excludes": [".venvs", "model.safetensors"],
    }
    manifest_path = ROOT / "ENTREGA_M09_3_SHA256.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files + [manifest_path]:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for name, identity in manifest["files"].items():
            data = bundle.read(name)
            assert len(data) == identity["bytes"]
            assert hashlib.sha256(data).hexdigest() == identity["sha256"], name
        assert bundle.read(manifest_path.name) == manifest_path.read_bytes()
    print(f"ZIP conferido: {archive.name}; {len(files) + 1} arquivos; {archive.stat().st_size} bytes")
    print(f"SHA256: {sha(archive)}")


if __name__ == "__main__":
    main()
