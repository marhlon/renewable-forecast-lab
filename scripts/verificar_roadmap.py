"""Confira a consistência do roadmap e de suas evidências locais.

Uma verificação documental aprovada não comprova autonomia nem operação real.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import sys


MODULOS = tuple(f"M{i:02d}" for i in range(10))
ESTADOS = ("planejado", "em_execucao", "aguarda_revisao", "validado", "bloqueado")
PORTOES = ("engenharia", "formacao", "operacao", "ampliacao")
BLOCOS = {1: (1, 2, 3), 2: (4, 5, 6), 3: (7, 8, 9)}
AVISO = "Consistência documental não comprova autonomia nem operação real."
ROOT = Path(__file__).resolve().parents[1]


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"chave JSON repetida: {key}")
        result[key] = value
    return result


def validate_backlog(data, root, gate=None, bloco=None, exigir_fechamento=False):
    """Devolva {valid, errors, summary}; leia evidências sem modificar o backlog."""
    errors = []
    root = Path(root).resolve()

    def error(where, message):
        errors.append(f"{where}: {message}")

    def text(value, where):
        if not isinstance(value, str) or not value.strip():
            error(where, "exige texto não vazio")
            return False
        return True

    def iso_date(value, where):
        try:
            if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError
            date.fromisoformat(value)
        except ValueError:
            error(where, "exige data ISO YYYY-MM-DD válida")

    def sequence(value, where, *, nonempty=False):
        if not isinstance(value, list) or (nonempty and not value):
            error(where, "exige lista" + (" não vazia" if nonempty else ""))
            return []
        return value

    def local_path(value, where, *, exists=False, file=False):
        if not text(value, where):
            return None
        normalized = value.replace("\\", "/")
        parts = normalized.split("/")
        if (normalized.startswith("/") or PureWindowsPath(value).drive
                or ".." in parts or ":" in normalized or "\x00" in normalized
                or not any(part not in ("", ".") for part in parts)):
            error(where, "exige caminho relativo ao projeto, sem travessia ou URI")
            return None
        try:
            path = (root / normalized).resolve()
            if not path.is_relative_to(root):
                error(where, "caminho ou link resolve fora da raiz do projeto")
                return None
            if (exists and not path.exists()) or (file and not path.is_file()):
                error(where, "arquivo/caminho não encontrado")
            return path
        except (OSError, ValueError, RuntimeError) as exc:
            error(where, f"caminho inacessível ({type(exc).__name__})")
            return None

    if not root.is_dir():
        error("root", "diretório do projeto não encontrado")
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["backlog: exige objeto JSON"], "summary": {}, "warning": AVISO}
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
        error("schema_version", "exige versão 1")
    iso_date(data.get("updated_at"), "updated_at")
    scope = sequence(data.get("scope"), "scope", nonempty=True)
    if scope != list(MODULOS):
        error("scope", "exige M00 a M09, nessa ordem e sem duplicatas")
    if gate is not None and gate not in PORTOES:
        error("gate", "portão desconhecido")
    valid_block = bloco is None or (type(bloco) is int and bloco in BLOCOS)
    if not valid_block:
        error("bloco", "exige inteiro 1, 2 ou 3, ou None")
    if type(exigir_fechamento) is not bool:
        error("exigir_fechamento", "exige booleano")
    if exigir_fechamento and (bloco is None or not valid_block):
        error("exigir_fechamento", "exige --bloco 1, 2 ou 3")

    items = sequence(data.get("items"), "items", nonempty=True)
    records = {}
    rows = []
    for index, item in enumerate(items):
        label = f"items[{index}]"
        if not isinstance(item, dict):
            error(label, "exige objeto")
            continue
        rows.append(item)
        item_id = item.get("id")
        if not isinstance(item_id, str) or not re.fullmatch(r"M0[0-9]-[0-9]{2}", item_id):
            error(label + ".id", "exige identificador Mxx-NN no escopo M00–M09")
        else:
            label = item_id
            if item_id in records:
                error(label, "ID repetido")
            records[item_id] = item
        module = item.get("modulo")
        if module not in MODULOS:
            error(label + ".modulo", "módulo fora do escopo")
        elif isinstance(item_id, str) and not item_id.startswith(module + "-"):
            error(label + ".modulo", "não coincide com o prefixo do ID")
        if type(item.get("etapa")) is not int or not 1 <= item["etapa"] <= 9:
            error(label + ".etapa", "exige inteiro de 1 a 9")
        for field in ("titulo", "natureza", "constatacao"):
            text(item.get(field), label + "." + field)
        if item.get("estado") not in ESTADOS:
            error(label + ".estado", "estado desconhecido")
        gates = sequence(item.get("portoes"), label + ".portoes", nonempty=True)
        if any(value not in PORTOES for value in gates) or len(set(map(str, gates))) != len(gates):
            error(label + ".portoes", "exige portões conhecidos, sem duplicatas")
        deps = sequence(item.get("depende_de"), label + ".depende_de")
        if any(not isinstance(dep, str) for dep in deps) or len(set(map(str, deps))) != len(deps):
            error(label + ".depende_de", "exige IDs sem duplicatas")
        base = sequence(item.get("evidencias_base"), label + ".evidencias_base")
        for i, path in enumerate(base):
            local_path(path, f"{label}.evidencias_base[{i}]", exists=True)
        outputs = sequence(item.get("entregaveis"), label + ".entregaveis", nonempty=True)
        output_paths = []
        for i, path in enumerate(outputs):
            resolved = local_path(path, f"{label}.entregaveis[{i}]", file=item.get("estado") == "validado")
            if resolved is not None:
                output_paths.append(resolved)

        criteria = sequence(item.get("criterios"), label + ".criterios", nonempty=True)
        criterion_ids = set()
        for i, criterion in enumerate(criteria):
            where = f"{label}.criterios[{i}]"
            if not isinstance(criterion, dict):
                error(where, "exige objeto")
                continue
            cid = criterion.get("id")
            if not isinstance(cid, str) or not re.fullmatch(r"C[1-9][0-9]*", cid):
                error(where + ".id", "exige identificador C1, C2, ...")
            elif cid in criterion_ids:
                error(where + ".id", "critério repetido")
            else:
                criterion_ids.add(cid)
            text(criterion.get("descricao"), where + ".descricao")
            if type(criterion.get("atendido")) is not bool:
                error(where + ".atendido", "exige booleano")

        evidence = sequence(item.get("evidencias"), label + ".evidencias")
        hashed_paths = set()
        for i, record in enumerate(evidence):
            where = f"{label}.evidencias[{i}]"
            if not isinstance(record, dict):
                error(where, "exige objeto")
                continue
            path = local_path(record.get("path"), where + ".path", file=True)
            text(record.get("kind"), where + ".kind")
            digest = record.get("sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
                error(where + ".sha256", "exige SHA-256 hexadecimal")
            elif path is not None and path.is_file():
                try:
                    with path.open("rb") as handle:
                        actual = hashlib.file_digest(handle, "sha256").hexdigest()
                    if actual != digest.lower():
                        error(where + ".sha256", "hash diverge do arquivo")
                    else:
                        hashed_paths.add(path)
                except OSError as exc:
                    error(where + ".path", f"arquivo inacessível ({type(exc).__name__})")

        review = item.get("revisao")
        review_path = None
        if "revisao" not in item:
            error(label + ".revisao", "campo obrigatório; use null enquanto pendente")
        elif review is not None:
            if not isinstance(review, dict):
                error(label + ".revisao", "exige objeto ou null")
            else:
                text(review.get("responsavel"), label + ".revisao.responsavel")
                iso_date(review.get("data"), label + ".revisao.data")
                review_path = local_path(review.get("parecer"), label + ".revisao.parecer", file=True)
                if review.get("decisao") != "aprovado":
                    error(label + ".revisao.decisao", "exige aprovado ou revisão null")
        block = item.get("bloqueio")
        if "bloqueio" not in item:
            error(label + ".bloqueio", "campo obrigatório; use null quando não houver bloqueio")
        elif block is not None:
            if not isinstance(block, dict):
                error(label + ".bloqueio", "exige objeto ou null")
            else:
                text(block.get("motivo"), label + ".bloqueio.motivo")
                text(block.get("condicao_desbloqueio"), label + ".bloqueio.condicao_desbloqueio")
        if item.get("estado") == "bloqueado" and not isinstance(block, dict):
            error(label + ".bloqueio", "item bloqueado exige motivo e condição de desbloqueio")
        if item.get("estado") == "validado":
            if block is not None:
                error(label + ".bloqueio", "validado exige bloqueio null")
            if not criteria or any(not isinstance(c, dict) or c.get("atendido") is not True for c in criteria):
                error(label + ".criterios", "validado exige todos os critérios atendidos")
            if not evidence:
                error(label + ".evidencias", "validado exige evidência")
            if not isinstance(review, dict) or review.get("decisao") != "aprovado":
                error(label + ".revisao", "validado exige revisão aprovada")
            if review_path is None or review_path not in hashed_paths:
                error(label + ".revisao.parecer", "parecer precisa constar nas evidências com hash válido")
            for path in output_paths:
                if path not in hashed_paths:
                    error(label + ".entregaveis", f"entrega sem evidência com hash válido: {path.relative_to(root)}")

    covered = {row.get("modulo") for row in rows if isinstance(row.get("modulo"), str)}
    if set(MODULOS) - covered:
        error("items", "faltam módulos: " + ", ".join(sorted(set(MODULOS) - covered)))
    graph = {}
    for item_id, row in records.items():
        deps = row.get("depende_de") if isinstance(row.get("depende_de"), list) else []
        graph[item_id] = [dep for dep in deps if isinstance(dep, str) and dep in records]
        for dep in deps:
            if not isinstance(dep, str) or dep not in records:
                error(item_id + ".depende_de", f"ID não encontrado: {dep!r}")
            elif row.get("estado") == "validado" and records[dep].get("estado") != "validado":
                error(item_id + ".depende_de", f"dependência ainda não validada: {dep}")
    visited, active = set(), set()

    def walk(node):
        if node in active:
            error("depende_de", f"ciclo envolvendo {node}")
            return
        if node in visited:
            return
        active.add(node)
        for dep in graph[node]:
            walk(dep)
        active.remove(node)
        visited.add(node)

    for item_id in graph:
        walk(item_id)
    if bloco is None:
        scoped_rows = rows
        scoped_stages = list(range(1, 10))
    elif valid_block:
        scoped_stages = list(BLOCOS[bloco])
        scoped_rows = [row for row in rows if type(row.get("etapa")) is int and row["etapa"] in scoped_stages]
    else:
        scoped_rows, scoped_stages = [], []
    scoped_ids = {row.get("id") for row in scoped_rows if isinstance(row.get("id"), str)}
    pending_block = [row.get("id") for row in scoped_rows if row.get("estado") != "validado"] if bloco is not None else []
    if exigir_fechamento is True and bloco is not None and valid_block:
        if not scoped_rows:
            error("exigir_fechamento", f"bloco {bloco} não tem itens cadastrados")
        elif pending_block:
            error("exigir_fechamento", f"bloco {bloco} pendente: " + ", ".join(map(str, pending_block)))
    pending_gate = []
    if gate in PORTOES:
        selected = [row for row in scoped_rows if isinstance(row.get("portoes"), list) and gate in row["portoes"]]
        if not selected and (bloco is None or gate == "engenharia"):
            error("gate", f"portão {gate} não tem itens cadastrados no recorte solicitado")
        pending_gate = [row.get("id") for row in selected if row.get("estado") != "validado"]
        if pending_gate:
            error("gate", f"portão {gate} pendente: " + ", ".join(map(str, pending_gate)))
    counts = Counter(row.get("estado") for row in scoped_rows if isinstance(row.get("estado"), str))
    summary = {
        "total": len(scoped_rows),
        "total_global": len(rows),
        "bloco": bloco,
        "etapas_do_bloco": scoped_stages,
        "itens_no_bloco": [row.get("id") for row in scoped_rows],
        "por_estado": {state: counts[state] for state in ESTADOS},
        "por_modulo": {module: sum(row.get("modulo") == module for row in scoped_rows) for module in MODULOS},
        "exigir_fechamento": exigir_fechamento,
        "pendentes_no_bloco": pending_block,
        "gate": gate,
        "itens_no_gate": [row.get("id") for row in scoped_rows
            if gate is not None and isinstance(row.get("portoes"), list) and gate in row["portoes"]],
        "pendencias_fora_do_gate": [row.get("id") for row in scoped_rows
            if gate is not None and isinstance(row.get("portoes"), list) and gate not in row["portoes"]
            and row.get("estado") != "validado"],
        "pendentes_no_gate": pending_gate,
        "prontos_para_iniciar": [item_id for item_id, row in records.items()
            if item_id in scoped_ids and row.get("estado") == "planejado" and isinstance(row.get("depende_de"), list)
            and all(isinstance(dep, str) and dep in records and records[dep].get("estado") == "validado"
                    for dep in row["depende_de"])],
    }
    return {"valid": not errors, "errors": errors, "summary": summary, "warning": AVISO}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Raiz do projeto.")
    parser.add_argument("--backlog", type=Path, default=Path("config/roadmap_m00_m09.json"))
    parser.add_argument("--output", type=Path, help="Grava somente o sumário da verificação em JSON.")
    parser.add_argument("--gate", choices=PORTOES, help="Exige todos os itens desse portão validados.")
    parser.add_argument("--bloco", type=int, choices=tuple(BLOCOS), help="Resume 1: etapas 1–3; 2: 4–6; 3: 7–9. A estrutura inteira continua sendo verificada.")
    parser.add_argument("--exigir-fechamento", action="store_true", help="Exige --bloco e todos os seus itens validados, incluindo pendências humanas e externas.")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    backlog = args.backlog if args.backlog.is_absolute() else root / args.backlog
    try:
        data = json.loads(backlog.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_keys)
        report = validate_backlog(data, root, args.gate, args.bloco, args.exigir_fechamento)
    except (OSError, ValueError, RecursionError) as exc:
        data = None
        report = {"valid": False, "errors": [f"backlog: {exc}"], "summary": {}, "warning": AVISO}
    report["schema"] = "renewcast-roadmap-verification-v1"
    report["backlog"] = str(backlog.resolve())
    if args.output:
        output = args.output if args.output.is_absolute() else root / args.output
        try:
            output = output.resolve()
            if not output.is_relative_to(root):
                raise ValueError("--output deve ficar dentro da raiz do projeto")
            if output == backlog.resolve():
                raise ValueError("--output não pode sobrescrever o backlog")
            protected = set()
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                for item in data["items"]:
                    if not isinstance(item, dict):
                        continue
                    names = []
                    for field in ("entregaveis", "evidencias_base"):
                        if isinstance(item.get(field), list):
                            names.extend(item[field])
                    if isinstance(item.get("evidencias"), list):
                        names.extend(e.get("path") for e in item["evidencias"] if isinstance(e, dict))
                    if isinstance(item.get("revisao"), dict):
                        names.append(item["revisao"].get("parecer"))
                    for name in names:
                        if isinstance(name, str):
                            protected.add((root / name.replace("\\", "/")).resolve())
            if output in protected:
                raise ValueError("--output não pode sobrescrever entradas, entregas ou evidências")
            if output.exists():
                if any(path.exists() and output.samefile(path) for path in protected | {backlog.resolve()}):
                    raise ValueError("--output aponta para uma entrada ou evidência por outro nome")
                previous = json.loads(output.read_text(encoding="utf-8-sig"))
                if not isinstance(previous, dict) or previous.get("schema") != report["schema"]:
                    raise ValueError("--output existente não é um sumário deste verificador; escolha outro caminho")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"Falha ao gravar sumário: {exc}", file=sys.stderr)
            return 1
    print("Roadmap consistente." if report["valid"] else "Roadmap com pendências de validação.")
    if report["summary"]:
        print(json.dumps(report["summary"], ensure_ascii=False))
    for message in report["errors"]:
        print("- " + message)
    print(AVISO)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
