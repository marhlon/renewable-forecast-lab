"""M06: leitura do benchmark e autoria da escolha sob latencia e vazao.

Executar: python notebooks/analise_concorrencia.py
Depois implementar escolher_concorrencia e executar com --autoria.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
RUN_ROOT = PROJECT / "reports/performance/CJU_BA5EIGT/h24_event_concurrency_v1"


def escolher_concorrencia(fases: list[dict], teto_ms: float, fracao: float) -> dict:
    """Implementa a decisão de concorrência com base na elegibilidade de latência/falhas

    e maximização de vazão útil retida.
    """
    concorrencias = (1, 4, 8)
    agrupado = {c: [] for c in concorrencias}
    for r in fases:
        c = int(r["concurrency"])
        if c in agrupado:
            agrupado[c].append(r)

    elegiveis = {}
    piores_p95 = {}

    for c in concorrencias:
        rodadas = agrupado[c]
        if len(rodadas) != 3:
            continue
        
        e_elegivel = True
        p95_list = []
        vazao_list = []
        
        for r in rodadas:
            failed = r.get("failed")
            p95 = r.get("p95_correct_ms")
            vazao = r.get("correct_per_second")
            
            # 1. Critério de elegibilidade: zero falhas e P95 <= teto_ms nas 3 rodadas
            if failed is None or failed != 0:
                e_elegivel = False
            if p95 is None or not math.isfinite(p95) or p95 > teto_ms:
                e_elegivel = False
            if vazao is None or not math.isfinite(vazao):
                e_elegivel = False
            
            if p95 is not None and math.isfinite(p95):
                p95_list.append(p95)
            if vazao is not None and math.isfinite(vazao):
                vazao_list.append(vazao)

        if p95_list:
            piores_p95[c] = max(p95_list)
        
        # 2. Calcular mediana da vazão útil para os elegíveis
        if e_elegivel and len(vazao_list) == 3:
            elegiveis[c] = statistics.median(vazao_list)

    # Caso nenhuma opção seja elegível
    if not elegiveis:
        return {
            "concurrency": None,
            "reason": f"Nenhum nível de concorrência cumpriu o critério de zero falhas e P95 <= {teto_ms:.1f} ms em todas as 3 rodadas."
        }

    # 3. Identificar a melhor mediana e filtrar as que atingem a fração mínima
    melhor_mediana = max(elegiveis.values())
    alvo_vazao = fracao * melhor_mediana

    escolhida = None
    for c in sorted(elegiveis.keys()):
        if elegiveis[c] >= alvo_vazao:
            escolhida = c
            break

    mediana_esc = elegiveis[escolhida]
    pior_p95_esc = piores_p95[escolhida]

    reason = (
        f"Concorrência {escolhida} escolhida por ser a menor opção elegível que alcançou pelo menos "
        f"{fracao*100:.0f}% da melhor mediana de vazão útil ({melhor_mediana:.2f} req/s). "
        f"Apresentou mediana de vazão de {mediana_esc:.2f} req/s e pior P95 de {pior_p95_esc:.2f} ms "
        f"(respeitando o limite de {teto_ms:.0f} ms)."
    )

    return {
        "concurrency": escolhida,
        "reason": reason
    }


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def carregar(run_dir=None):
    if run_dir is None:
        pointer = json.loads((RUN_ROOT / "latest_run.json").read_text(encoding="utf-8"))
        run_dir = Path(pointer["directory"])
        if not run_dir.is_absolute() or sha(run_dir / "verification.json") != pointer["verification_sha256"]:
            raise ValueError("Ponteiro de execucao invalido.")
    run_dir = Path(run_dir).resolve()
    receipt = json.loads((run_dir / "verification.json").read_text(encoding="utf-8"))
    if receipt.get("schema") != "renewcast-concurrency-receipt-v1" or receipt.get("measurement_complete") is not True:
        raise ValueError("A medicao nao esta completa. Leia failure.json/pipeline.log.")
    for name, expected in receipt["output_sha256"].items():
        path = (run_dir / name).resolve()
        if not path.is_relative_to(run_dir) or sha(path) != expected:
            raise ValueError(f"Evidencia alterada: {name}")
    with (run_dir / "summary.csv").open(encoding="utf-8", newline="") as handle:
        raw = list(csv.DictReader(handle))
    phases = [{k: None if value == "" else float(value) for k, value in row.items()} for row in raw]
    keys = [(row["round"], row["concurrency"]) for row in phases]
    if len(keys) != 9 or set(keys) != {(r, c) for r in (1, 2, 3) for c in (1, 4, 8)}:
        raise ValueError("Sao necessarias nove fases distintas: tres rodadas por concorrencia.")
    protocol = json.loads((run_dir / "protocol.json").read_text(encoding="utf-8"))
    for row in phases:
        if row["attempts"] != protocol["calls_per_phase"] or row["correct_200"] + row["failed"] != row["attempts"]:
            raise ValueError("Contagens nao reconciliadas.")
    return run_dir, phases, protocol


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--autoria", action="store_true")
    args = parser.parse_args(argv)
    run_dir, phases, protocol = carregar(args.run_dir)
    print(f"Execucao: {run_dir}")
    print("rodada clientes corretas falhas vazao_correta/s p50_ms p95_ms")
    for row in sorted(phases, key=lambda r: (r["round"], r["concurrency"])):
        p50 = "indefinido" if row["p50_correct_ms"] is None else f"{row['p50_correct_ms']:.2f}"
        p95 = "indefinido" if row["p95_correct_ms"] is None else f"{row['p95_correct_ms']:.2f}"
        print(f"{int(row['round']):6} {int(row['concurrency']):8} {int(row['correct_200']):8} {int(row['failed']):6} "
              f"{row['correct_per_second']:15.2f} {p50:>6} {p95:>6}")
    if args.autoria:
        rules = protocol["exploratory_rule"]
        try:
            choice = escolher_concorrencia(phases, rules["p95_ms_max"], rules["throughput_retained_fraction"])
        except NotImplementedError as exc:
            parser.error(str(exc))
        if not isinstance(choice, dict) or set(choice) != {"concurrency", "reason"}:
            raise ValueError("Retorne exatamente concurrency e reason.")
        if choice["concurrency"] is not None and (type(choice["concurrency"]) is not int or choice["concurrency"] not in (1, 4, 8)):
            raise ValueError("concurrency deve ser 1, 4, 8 ou None.")
        if not isinstance(choice["reason"], str) or not choice["reason"].strip():
            raise ValueError("Fundamente a decisao em reason.")
        output = run_dir / "autoria"
        output.mkdir(exist_ok=True)
        result = {"source_verification_sha256": sha(run_dir / "verification.json"),
                  "code_sha256": sha(Path(__file__)), "choice": choice,
                  "rules": rules, "operational_policy_approved": False,
                  "review_status": "format_checked_semantics_pending_teacher_review"}
        (output / "decisao.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps(choice, ensure_ascii=False, indent=2))
        print(f"Formato conferido; a logica sera revisada. Salvo: {output / 'decisao.json'}")
    else:
        print("Proxima autoria: implementar escolher_concorrencia; executar com --autoria e escrever parecer_concorrencia.md.")
        print("Nao use media dos P95 como P95 agregado. O protocolo e local, fechado e com um pedido repetido.")


if __name__ == "__main__":
    main()
