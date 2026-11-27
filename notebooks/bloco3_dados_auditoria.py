"""Auditoria pós-execução; não ajusta modelos nem muda protocolos congelados."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
from renewable_forecast.bloco3_data import SOURCE_SHA256, sha256, write_json

BASE = ROOT / "reports/fechamento_m00_m09/bloco3_engenharia"
IDS = ["M07-01", "M07-02", "M07-03", "M05-05"]


def audit():
    results = {}
    frozen_checks = []
    for item in IDS:
        protocol = json.loads((BASE / item / "protocolo.json").read_text(encoding="utf-8"))
        results[item] = json.loads((BASE / item / "resultado.json").read_text(encoding="utf-8"))
        assert pd.Timestamp(protocol["frozen_at_utc"]) < pd.Timestamp(results[item]["executed_at_utc"])
        for path, expected in protocol["code_sha256_before_execution"].items():
            actual = sha256(ROOT / path)
            assert actual == expected, path
            frozen_checks.append({"item": item, "path": path, "sha256": actual, "matches": True})
    layers = results["M07-01"]
    assert sha256(ROOT / "data/raw/bloco2_locked/geracao_2026_10.parquet") == SOURCE_SHA256
    assert sha256(Path(layers["bronze"]["path"])) == SOURCE_SHA256
    assert layers["outputs"]["silver"]["rows"] + layers["outputs"]["quarantine"]["rows"] == 537384
    assert all(layers["idempotency"].values())
    physical_checks = []
    for layer, output in layers["outputs"].items():
        target = ROOT / output["path"]
        assert sha256(target) == output["sha256"]
        assert sha256(target) == sha256(target.with_name(f"{layer}_reprocessed.parquet"))
        assert output["physical_idempotent"]
        physical_checks.append({"layer": layer, "sha256": output["sha256"], "reprocessed_matches": True})
    incremental = results["M07-03"]
    for key in ["state_equals_reference", "gold_equals_reference", "failed_commit_unchanged", "conflicting_payload_rejected", "late_feature_masked", "no_cross_series"]:
        assert incremental[key], key
    scale = results["M07-02"]
    assert scale["trials"] == 18 and len(scale["equivalence"]) == 9
    assert all(x["equivalent"] for x in scale["equivalence"])
    assert scale["all_rss_under_512mib"]
    predictions = pd.read_csv(BASE / "M05-05/previsoes_pareadas.csv")
    paired = []
    columns = ["series_id", "forecast_origin", "target_time", "label_available_at", "target"]
    for split, frame in predictions.groupby("split"):
        groups = {model: group.sort_values(columns[:2])[columns].reset_index(drop=True)
                  for model, group in frame.groupby("model")}
        pd.testing.assert_frame_equal(groups["global_hgb"], groups["local_hgb"])
        pd.testing.assert_frame_equal(groups["global_hgb"], groups["persistence"])
        assert not groups["global_hgb"].duplicated(columns[:2]).any()
        paired.append({"split": split, "origins_each_model": len(groups["global_hgb"]), "identical_keys_targets_availability": True})
    model = results["M05-05"]
    assert model["cohorts"] == {"train": 1332, "validation": 576, "test": 956}
    assert model["strict_label_purge"]
    assert pd.Timestamp(model["train_max_label_available"]) < pd.Timestamp("2026-10-16")
    assert sha256(BASE / "M05-05/global_hgb.joblib") == model["model_artifact_sha256"]
    write_json(BASE / "M07-01/auditoria_pos_execucao.json", {
        "executed_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "responsible": "Codex — auditoria de código, arquivos e coortes após execução",
        "frozen_code_checks": frozen_checks, "physical_reprocessing_checks": physical_checks,
        "paired_predictions": paired, "source_unchanged": True,
        "incremental_checks": "seis condições verificadas verdadeiras",
        "scale_checks": "18 trials, 9 pares equivalentes e RSS amostrado abaixo de 512 MiB",
        "training_label_purge": True, "model_artifact_hash_matches": True,
        "auditor_sha256": sha256(Path(__file__)),
        "scope": "conferência local pós-execução; não é CI remoto, revisão humana ou prova operacional",
    })
    body = "# Bloco 3 — engenharia de dados e modelo global\n\n"
    body += "Protocolos anteriores a execução, código/modelos fixos e dados reais preservados. Soluções fornecidas e executadas por Codex; sem exigir provas do usuário ou certificar autonomia pessoal.\n\n"
    for item in IDS:
        text = (BASE / item / "parecer.md").read_text(encoding="utf-8")
        body += text.replace("# Parecer de engenharia —", f"## {item} —").replace("\n## ", "\n### ") + "\n\n"
    body += "Artefatos: reports/fechamento_m00_m09/bloco3_engenharia/{M07-01,M07-02,M07-03,M05-05}. Cada pasta tem protocolo, resultado, parecer e manifesto SHA256; a auditoria pós-execução está em M07-01. Os CSVs mantêm métricas, recursos e previsões pareadas. Cadastro e portões operacionais são conferidos na revisão integrada do bloco. Nenhum serviço externo foi ativado por esta trilha.\n"
    (ROOT / "docs/roadmap_m00_m09/Bloco_3_Dados.md").write_text(body, encoding="utf-8")
    for item in IDS:
        paths = sorted(p for p in (BASE / item).rglob("*") if p.is_file() and p.name != "manifesto_sha256.json")
        write_json(BASE / item / "manifesto_sha256.json", {
            "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "files": [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path), "bytes": path.stat().st_size} for path in paths],
        })
    print(json.dumps({"frozen_checks":len(frozen_checks), "physical_checks":len(physical_checks), "paired":paired, "all_checks_passed":True, "doc_sha256":sha256(ROOT / "docs/roadmap_m00_m09/Bloco_3_Dados.md")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    audit()
