"""Consolida verificações já executadas; não treina, publica ou executa CI."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/fechamento_m00_m09/bloco3_engenharia"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    expected = {
        "verificacao_roadmap_global.json": True,
        "verificacao_gate_engenharia.json": True,
        "verificacao_regressao_bloco1.json": True,
        "verificacao_regressao_bloco2.json": True,
        "verificacao_gate_operacao.json": False,
        "verificacao_fechamento_integral.json": False,
    }
    checks = {name: read(BASE / name) for name in expected}
    for name, valid in expected.items():
        assert checks[name]["valid"] is valid, (name, checks[name]["errors"])
    global_check = checks["verificacao_roadmap_global.json"]
    assert global_check["summary"]["por_estado"]["validado"] == 35
    assert global_check["summary"]["por_estado"]["bloqueado"] == 10
    block = checks["verificacao_gate_engenharia.json"]["summary"]
    assert block["por_estado"]["validado"] == 12
    open_ids = [f"M06-{n:02d}" for n in range(4, 10)]
    assert block["pendencias_fora_do_gate"] == open_ids
    assert checks["verificacao_fechamento_integral.json"]["summary"]["pendentes_no_bloco"] == open_ids
    assert checks["verificacao_regressao_bloco1.json"]["summary"]["por_estado"]["validado"] == 14
    assert checks["verificacao_regressao_bloco2.json"]["summary"]["por_estado"]["validado"] == 9

    registry = read(ROOT / "config/roadmap_m00_m09.json")
    before = read(BASE / "cadastro_antes_alteracao.json")
    items = {item["id"]: item for item in registry["items"]}
    old = {item["id"]: item for item in before["items"]}
    assert set(items) == set(old) and len(items) == 45
    for identifier in block["itens_no_bloco"]:
        item = items[identifier]
        history = item["historico_bloco3"]
        for key, value in history.items():
            if key != "snapshot":
                assert value == old[identifier].get(key), (identifier, key)
        assert item["depende_de"] == old[identifier]["depende_de"]
    for identifier in open_ids:
        assert items[identifier]["criterios"] == old[identifier]["criterios"]
    assert all(not c["atendido"] for c in items["M06-05"]["criterios"] if c["id"] in {"C3", "C4"})

    remote_path = BASE / "M06-02/execucao_ci_remoto.json"
    remote = read(remote_path)
    assert remote["exit_code"] == 0
    remote_text = remote_path.read_text(encoding="utf-8")
    for run_id in ("45889419488", "45889590759"):
        assert run_id in remote_text
    new_audit = BASE / "auditoria_com_ci_remoto.json"
    assert read(new_audit)["valid"] is True
    repeated = sorted((BASE / "reverificacoes").glob("*.json"))[-1]
    assert read(repeated)["valid"] is True
    original_audit = read(BASE / "auditoria_bloco3.json")
    assert sha(BASE / "auditar_bloco3_antes_ci_remoto.py.txt") == original_audit["audit_code_sha256"]

    links = []
    docs = ROOT / "docs/roadmap_m00_m09"
    for name in ["Relatorio_Engenharia_Bloco3.md", "Bloco_3_Execucao.md", "Revisao_Engenharia_Bloco3.md", "Revisao_CI_Remoto_Bloco3.md"]:
        document = docs / name
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            path = unquote(target.strip("<>").split("#", 1)[0])
            assert (document.parent / path).resolve().exists(), (name, target)
            links.append({"doc": name, "target": target})

    closure_path = BASE / "fechamento_bloco3.json"
    closure = read(closure_path)
    assert (BASE / "fechamento_antes_ci_remoto.json").exists()
    closure.update({
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "fully_validated_engineering_ids": 12,
        "operational_open_ids": open_ids,
        "registry_validated": 35,
        "registry_blocked": 10,
        "github_remote_ci": True,
        "github_runs": {
            "negative_control": "https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889419488",
            "corrected": "https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889590759",
        },
        "remote_CI_same16tests_passed": True,
        "remote_receipt_sha256": sha(remote_path),
        "current_registry_sha256": sha(ROOT / "config/roadmap_m00_m09.json"),
        "audit_with_remote_ci_sha256": sha(new_audit),
        "latest_reverification": str(repeated.relative_to(ROOT)).replace("\\", "/"),
        "latest_reverification_sha256": sha(repeated),
        "main_merged": False,
        "deployed": False,
        "document_links_verified": len(links),
        "document_links": links,
        "verification_sha256": {name: sha(BASE / name) for name in expected},
        "previous_closure_preserved": "reports/fechamento_m00_m09/bloco3_engenharia/fechamento_antes_ci_remoto.json",
    })
    (docs / "estado_atual.json").write_bytes((BASE / "verificacao_roadmap_global.json").read_bytes())
    closure_path.write_text(json.dumps(closure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "registry": {"validated": 35, "blocked": 10}, "block3": {"validated": 12, "open": 6}, "local_links": len(links), "models_executed": False, "network_accessed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
