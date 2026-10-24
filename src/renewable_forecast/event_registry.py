"""M06: registro local de artefatos e alias ativo com histórico transacional.

O registro conserva cópias verificadas. Ativar muda o estado desejado; processos
que já carregaram um modelo precisam reiniciar. Não há novo ajuste de estimador.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import uuid

from renewable_forecast.event_artifact import (
    EventPredictRequest, EventRuntime, canonical_hash, sha256,
)

RELEASE = "2026.10.07-event-registry-1"
FILES = ("model.joblib", "manifest.json", "example_request.json", "policy.json")


class RegistryConflict(ValueError):
    """O estado mudou desde a leitura do operador; a escrita foi recusada."""


def now():
    return datetime.now(timezone.utc).isoformat()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", value):
        raise ValueError("Identificador inválido para versão/alias.")
    return value


def initialize(registry: Path):
    registry = Path(registry).resolve()
    registry.mkdir(parents=True, exist_ok=True)
    database = registry / "registry.sqlite"
    if database.exists():
        # Não acrescenta tabelas do exercício a um banco de outro aplicativo.
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as con:
            tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "registry_meta" not in tables or con.execute("SELECT release FROM registry_meta").fetchall() != [(RELEASE,)]:
                raise ValueError("O caminho contém um banco que não pertence a este registro.")
    (registry / "versions").mkdir(exist_ok=True)
    with sqlite3.connect(database) as con:
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript("""
            CREATE TABLE IF NOT EXISTS registry_meta (release TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS versions (
                version_id TEXT PRIMARY KEY, bundle_sha256 TEXT NOT NULL,
                model_sha256 TEXT NOT NULL, policy_sha256 TEXT NOT NULL,
                manifest_sha256 TEXT NOT NULL, files_json TEXT NOT NULL,
                training_cutoff TEXT NOT NULL, registered_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS aliases (
                alias TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES versions(version_id),
                generation INTEGER NOT NULL CHECK(generation>0), activation_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS deployments (
                activation_id TEXT PRIMARY KEY, alias TEXT NOT NULL,
                generation INTEGER NOT NULL CHECK(generation>0),
                action TEXT NOT NULL CHECK(action IN ('activate','rollback')),
                from_version TEXT REFERENCES versions(version_id),
                to_version TEXT NOT NULL REFERENCES versions(version_id),
                to_bundle_sha256 TEXT NOT NULL, reason TEXT NOT NULL,
                evidence_request_ids_json TEXT NOT NULL, committed_at TEXT NOT NULL,
                UNIQUE(alias,generation)
            );
        """)
        rows = con.execute("SELECT release FROM registry_meta").fetchall()
        if rows and rows != [(RELEASE,)]:
            raise ValueError("Banco de registro possui outra versão de contrato.")
        con.execute("INSERT OR IGNORE INTO registry_meta VALUES (?)", (RELEASE,))
    return registry


@contextmanager
def connection(registry: Path, *, write=False):
    path = (Path(registry) / "registry.sqlite").resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Registro ausente: {path}")
    con = sqlite3.connect(path.as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys=ON")
        if [row[0] for row in con.execute("SELECT release FROM registry_meta")] != [RELEASE]:
            raise ValueError("Contrato do registro incompatível.")
        if write:
            con.execute("BEGIN IMMEDIATE")
        yield con
        if write:
            con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


def version_record(registry, version_id):
    identifier(version_id)
    with connection(registry) as con:
        row = con.execute("SELECT * FROM versions WHERE version_id=?", (version_id,)).fetchone()
    if row is None:
        raise ValueError(f"Versão não registrada: {version_id}")
    return dict(row)


def verify_version(registry, version_id):
    record = version_record(registry, version_id)
    folder = Path(registry) / "versions" / version_id
    expected = json.loads(record["files_json"])
    if set(expected) != set(FILES):
        raise ValueError("Contrato de arquivos da versão inválido.")
    actual = {name: sha256(folder / name) for name in FILES}
    if actual != expected or canonical_hash(actual) != record["bundle_sha256"]:
        raise ValueError(f"Integridade da versão {version_id} reprovada.")
    if any(actual[name] != record[column] for name, column in (
        ("model.joblib", "model_sha256"), ("manifest.json", "manifest_sha256"), ("policy.json", "policy_sha256"),
    )):
        raise ValueError("Metadados da versão divergem dos arquivos registrados.")
    return record, folder


def smoke_check(folder, *, threads=2):
    # Reutiliza o contrato atual, inclusive versões de bibliotecas e disponibilidade.
    from renewable_forecast.decision_api import DecisionPolicy
    policy = DecisionPolicy.model_validate_json((folder / "policy.json").read_bytes())
    runtime = EventRuntime(folder, policy.model_dump(mode="json"), sha256(folder / "policy.json"), threads)
    request = EventPredictRequest.model_validate_json((folder / "example_request.json").read_bytes())
    return runtime.predict(request).model_dump(mode="json")


def register_version(registry, version_id, model_dir, policy_path, *, threads=2):
    """Mesmo identificador + mesmos bytes é idempotente; sobrescrita é recusada."""
    identifier(version_id)
    registry = Path(registry).resolve()
    model_dir, policy_path = Path(model_dir), Path(policy_path)
    sources = {name: model_dir / name for name in FILES if name != "policy.json"}
    sources["policy.json"] = policy_path
    original = {name: sha256(path) for name, path in sources.items()}
    bundle_hash = canonical_hash(original)
    with connection(registry) as con:
        existing = con.execute("SELECT bundle_sha256 FROM versions WHERE version_id=?", (version_id,)).fetchone()
    if existing:
        if existing[0] != bundle_hash:
            raise RegistryConflict("Versão existente tem outros bytes; use um novo identificador.")
        verify_version(registry, version_id)
        return version_record(registry, version_id)
    stage = Path(tempfile.mkdtemp(prefix=".register-", dir=registry))
    destination = registry / "versions" / version_id
    try:
        for name, source in sources.items():
            shutil.copyfile(source, stage / name)
        if {name: sha256(stage / name) for name in FILES} != original:
            raise ValueError("Os arquivos mudaram durante a cópia.")
        smoke_check(stage, threads=threads)
        manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
        with connection(registry, write=True) as con:
            if con.execute("SELECT 1 FROM versions WHERE version_id=?", (version_id,)).fetchone():
                raise RegistryConflict("Outra escrita registrou esta versão; consulte o registro.")
            if destination.exists():
                raise RegistryConflict("Pasta da versão já existe; não será sobrescrita.")
            stage.rename(destination)
            con.execute("INSERT INTO versions VALUES (?,?,?,?,?,?,?,?)", (
                version_id, bundle_hash, original["model.joblib"], original["policy.json"],
                original["manifest.json"], json.dumps(original, sort_keys=True),
                manifest["training_cutoff"], now(),
            ))
        return version_record(registry, version_id)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    # Se o processo cair entre rename e commit, a pasta órfã não é ativável:
    # não existe versão no banco. O comando nunca a reaproveita silenciosamente.


def active_version(registry, alias="active"):
    identifier(alias)
    with connection(registry) as con:
        row = con.execute("""
            SELECT a.*,v.bundle_sha256,v.model_sha256,v.policy_sha256,v.manifest_sha256
            FROM aliases a JOIN versions v USING(version_id) WHERE a.alias=?
        """, (alias,)).fetchone()
    return dict(row) if row else None


def switch_version(registry, version_id, *, expected_generation, reason, alias="active", action="activate", evidence_request_ids=(), threads=2):
    """Compare-and-swap: alias e histórico são gravados na mesma transação."""
    identifier(alias); identifier(version_id)
    if isinstance(expected_generation, bool) or not isinstance(expected_generation, int) or expected_generation < 0:
        raise ValueError("expected_generation deve ser inteiro não negativo.")
    if not isinstance(reason, str) or not reason.strip() or action not in {"activate", "rollback"}:
        raise ValueError("Informe motivo e ação válidos.")
    evidence_request_ids = list(evidence_request_ids)
    if any(not isinstance(x, str) or not re.fullmatch(r"[0-9a-f]{32}", x) for x in evidence_request_ids):
        raise ValueError("Evidências devem conter request_ids válidos.")
    record, folder = verify_version(registry, version_id)
    smoke_check(folder, threads=threads)
    # Pré-carregamento não promove nada: uma falha encerra antes da transação.
    with connection(registry, write=True) as con:
        current = con.execute("SELECT * FROM aliases WHERE alias=?", (alias,)).fetchone()
        generation = current["generation"] if current else 0
        if generation != expected_generation:
            raise RegistryConflict(f"Geração esperada {expected_generation}; atual {generation}. Nenhuma alteração aplicada.")
        previous = current["version_id"] if current else None
        if previous == version_id:
            raise RegistryConflict("A versão já está ativa; nenhuma nova transição foi criada.")
        if action == "rollback":
            last = con.execute("SELECT from_version FROM deployments WHERE alias=? AND generation=?", (alias, generation)).fetchone()
            if not last or last[0] != version_id:
                raise ValueError("Rollback deve restaurar a versão anterior ao estado atual.")
        # Confere bytes novamente antes do commit; arquivos são locais e controlados.
        if {name: sha256(folder / name) for name in FILES} != json.loads(record["files_json"]):
            raise ValueError("A versão mudou durante a preparação.")
        activation_id = uuid.uuid4().hex
        con.execute("INSERT INTO deployments VALUES (?,?,?,?,?,?,?,?,?,?)", (
            activation_id, alias, generation + 1, action, previous, version_id,
            record["bundle_sha256"], reason.strip(), json.dumps(evidence_request_ids), now(),
        ))
        con.execute("""INSERT INTO aliases VALUES (?,?,?,?) ON CONFLICT(alias) DO UPDATE SET
            version_id=excluded.version_id,generation=excluded.generation,activation_id=excluded.activation_id
        """, (alias, version_id, generation + 1, activation_id))
    return {"alias": alias, "version_id": version_id, "generation": generation + 1,
            "activation_id": activation_id, "bundle_sha256": record["bundle_sha256"]}


def rollback(registry, *, expected_generation, reason, alias="active", evidence_request_ids=(), threads=2):
    with connection(registry) as con:
        row = con.execute("SELECT from_version FROM deployments WHERE alias=? AND generation=?", (alias, expected_generation)).fetchone()
    if not row or row[0] is None:
        raise ValueError("Não há versão anterior para restaurar nesta geração.")
    return switch_version(registry, row[0], expected_generation=expected_generation, reason=reason,
                          alias=alias, action="rollback", evidence_request_ids=evidence_request_ids, threads=threads)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    register = commands.add_parser("register")
    register.add_argument("--version", required=True)
    register.add_argument("--model-dir", type=Path, required=True)
    register.add_argument("--policy", type=Path, required=True)
    for name in ("activate", "rollback"):
        cmd = commands.add_parser(name)
        if name == "activate":
            cmd.add_argument("--version", required=True)
        cmd.add_argument("--expected-generation", type=int, required=True)
        cmd.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    if args.command == "register":
        initialize(args.registry)
        result = register_version(args.registry, args.version, args.model_dir, args.policy)
    elif args.command == "status":
        result = active_version(args.registry)
    elif args.command == "activate":
        result = switch_version(args.registry, args.version, expected_generation=args.expected_generation, reason=args.reason)
    else:
        result = rollback(args.registry, expected_generation=args.expected_generation, reason=args.reason)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
