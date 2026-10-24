"""Confere recibo, release e wheels antes de produzir orçamento. Sem parecer automático."""
from __future__ import annotations
import argparse
import csv
from email.parser import BytesParser
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

PROJECT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def child(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Caminho fora da pasta esperada: {name}")
    return path


def check_files(root, hashes):
    for name, digest in hashes.items():
        path = child(root, name)
        if not path.is_file() or sha(path) != digest:
            raise ValueError(f"Hash ou arquivo inválido: {path}")


def load_bundle(project):
    release_root = project / "dist/event_service"
    pointer = read_json(release_root / "latest_release.json")
    release = child(release_root, pointer["directory"])
    if sha(release / "release.json") != pointer["release_sha256"]:
        raise ValueError("O manifesto não corresponde ao ponteiro de release.")
    manifest = read_json(release / "release.json")
    run_pointer = read_json(project / "reports/packaging/CJU_BA5EIGT/h24_event_v1/latest_run.json")
    run = Path(run_pointer["directory"])
    if not run.is_absolute() or not run.is_dir():
        raise ValueError("A pasta da reprodução deve existir e ser absoluta.")
    verification = run / "verification.json"
    if sha(verification) != run_pointer["verification_sha256"]:
        raise ValueError("O recibo não corresponde ao ponteiro da reprodução.")
    receipt = read_json(verification)
    if receipt.get("verified") is not True:
        raise ValueError("A reprodução não está aprovada no recibo.")
    if (receipt["release_id"] != manifest["release_id"] or
            receipt["release_manifest_sha256"] != sha(release / "release.json")):
        raise ValueError("Os ponteiros latest_release e latest_run identificam distribuições diferentes.")
    check_files(release, manifest["files_sha256"])
    check_files(run, receipt["output_sha256"])
    response = read_json(run / "response.json")
    reference = read_json(release / "reference_response.json")
    delta = abs(float(response["p_event"]) - float(reference["p_event"]))
    if (not math.isfinite(delta) or delta > 1e-12 or receipt["absolute_difference"] != delta
            or receipt["valid_request_status"] != 200 or receipt["invalid_request_status"] != 422
            or receipt["model_sha256"] != manifest["model_sha256"]
            or response["model_sha256"] != manifest["model_sha256"]
            or response["policy_sha256"] != manifest["policy_sha256"]):
        raise ValueError("Resposta, identidades ou resultado da reprodução são inconsistentes.")
    observed_wheels = {p.name for p in (release / "wheelhouse").glob("*.whl")}
    expected_wheels = {Path(name).name for name in manifest["files_sha256"] if name.startswith("wheelhouse/") and name.endswith(".whl")}
    if observed_wheels != expected_wheels:
        raise ValueError("Wheelhouse contém arquivos adicionados ou removidos após a captura.")
    total = sum((release / "wheelhouse" / name).stat().st_size for name in observed_wheels)
    if total <= 0 or total != receipt["wheelhouse_bytes"] or len(observed_wheels) != receipt["dependency_count_including_service"]:
        raise ValueError("Quantidade/tamanho dos wheels divergem do recibo.")
    return release, manifest, run, receipt


def wheel_metadata(path):
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise ValueError(f"METADATA ambíguo em {path}")
        data = BytesParser().parsebytes(archive.read(names[0]))
    return {"name": canonical(data["Name"]), "version": data["Version"],
            "requires_dist": data.get_all("Requires-Dist", []),
            "requires_python": data.get("Requires-Python")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=PROJECT)
    args = parser.parse_args()
    release, manifest, run, receipt = load_bundle(args.project_dir.resolve())
    wheels = sorted((release / "wheelhouse").glob("*.whl"), key=lambda p: (-p.stat().st_size, p.name))
    total = sum(p.stat().st_size for p in wheels)
    rows = [{"arquivo": p.name, "bytes": p.stat().st_size,
             "participacao_pct": 100 * p.stat().st_size / total} for p in wheels]
    output = run / "autoria_revisada"
    output.mkdir(exist_ok=True)
    with (output / "orcamento_distribuicao.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    write_json(output / "dependencias_wheels.json", {p.name: wheel_metadata(p) for p in wheels})
    write_json(output / "conferencia.json", {
        "release_id": manifest["release_id"], "run_id": receipt["run_id"],
        "verification_sha256": sha(run / "verification.json"),
        "release_sha256": sha(release / "release.json"),
        "audit_code_sha256": sha(Path(__file__)), "wheel_count": len(rows),
        "total_bytes": total, "total_mib": total / 1024**2,
        "top5_pct": sum(row["participacao_pct"] for row in rows[:5]),
        "human_opinion_generated": False,
    })
    print(f"Conferidos recibo, release e wheels: {len(rows)} arquivos; {total / 1024**2:.2f} MiB.")
    print(f"Top 5: {sum(row['participacao_pct'] for row in rows[:5]):.2f}%.")
    print(f"Evidências: {output}")
    print("Seu parecer original foi preservado; revise suas conclusões usando estes metadados.")


if __name__ == "__main__":
    main()
