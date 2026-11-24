"""M07.2: planejador autoral e chamada sobre o resultado do laboratorio Delta.

Salvar em notebooks/planejar_recalculo_temporal.py.
Executar na raiz: python notebooks/planejar_recalculo_temporal.py
A funcao preserva a logica enviada pelo aluno, com validacao de fuso.
A chamada de conferencia foi acrescentada pelo professor. Somente leitura;
nao abre Spark, nao altera Delta e nao cria novos relatorios.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Set


def planejar_recalculo(
    instantes: Iterable[datetime],
    *,
    horizonte: int,
    atraso: int,
    janela: int,
) -> Dict[str, Set[datetime]]:
    """Calcula origens potencialmente afetadas, sem recortar dataset ou treino.

    Para cada medicao corrigida t:
    historico = {t+d}; media = {t+d, ..., t+d+w-1}; alvo = {t-h}.
    Todas as datas pertencem ao eixo sem fuso usado neste laboratorio.
    """
    for nome, val, min_val in (
        ("horizonte", horizonte, 1), ("janela", janela, 1), ("atraso", atraso, 0)
    ):
        if isinstance(val, bool) or not isinstance(val, int) or val < min_val:
            raise ValueError(f"{nome} deve ser inteiro >= {min_val}, nao booleano.")

    historico: Set[datetime] = set()
    media: Set[datetime] = set()
    alvo: Set[datetime] = set()
    instantes_unicos = set(instantes)
    for t in instantes_unicos:
        if not isinstance(t, datetime):
            raise TypeError("Todos os instantes devem ser objetos datetime.")
        if t.tzinfo is not None:
            raise ValueError("Os instantes devem estar sem fuso, no eixo do laboratorio.")
        historico.add(t + timedelta(hours=atraso))
        for k in range(janela):
            media.add(t + timedelta(hours=atraso + k))
        alvo.add(t - timedelta(hours=horizonte))
    return {
        "historico": historico,
        "media": media,
        "alvo": alvo,
        "todas": historico | media | alvo,
    }


def conferir_execucao(run_dir: Path) -> None:
    """Confronta os quatro conjuntos com as mudancas medidas no CSV existente.

    Este confronto exato vale para a unica revisao positiva do laboratorio.
    Em lotes genericos, correcões podem se cancelar: o plano e conservador.
    """
    run_dir = run_dir.resolve()
    conclusion_path = run_dir / "conclusao.json"
    snapshot_path = run_dir / "snapshot_treino.json"
    impact_path = run_dir / "impacto_correcao.csv"
    for path in (conclusion_path, snapshot_path, impact_path):
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo do laboratorio nao encontrado: {path}")
    conclusion = json.loads(conclusion_path.read_text(encoding="utf-8-sig"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    if conclusion.get("schema") != "renewcast-delta-lab-v1" or conclusion.get("completed") is not True:
        raise ValueError("conclusao.json nao identifica um laboratorio Delta concluido.")
    if snapshot.get("schema") != "renewcast-training-snapshot-v1":
        raise ValueError("snapshot_treino.json possui schema desconhecido.")
    increment = float(conclusion["incremento_mwmed"])
    if not math.isfinite(increment) or increment <= 0 or conclusion.get("correcao_simulada") is not True:
        raise ValueError("Esta conferencia espera a revisao positiva simulada da aula.")

    corrected_time = datetime.fromisoformat(conclusion["instante_corrigido"])
    plan = planejar_recalculo(
        [corrected_time],
        horizonte=snapshot["horizon_hours"],
        atraso=snapshot["availability_delay_hours_assumed"],
        janela=snapshot["window_hours"],
    )
    columns = {
        "historico": "delta_historico_mwmed",
        "media": "delta_media_mwmed",
        "alvo": "delta_alvo_mwmed",
    }
    observed = {name: set() for name in plan}
    training = set()
    with impact_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"forecast_origin", "pertence_ao_treino", *columns.values()}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("impacto_correcao.csv nao tem as colunas esperadas da aula.")
        for row in reader:
            origin = datetime.fromisoformat(row["forecast_origin"])
            if origin.tzinfo is not None or origin in observed["todas"]:
                raise ValueError("CSV com origem duplicada ou fora do eixo sem fuso.")
            changed = False
            for name, column in columns.items():
                delta = float(row[column])
                if not math.isfinite(delta):
                    raise ValueError(f"Delta nao finito na origem {origin}: {column}")
                if abs(delta) > 1e-9:
                    observed[name].add(origin)
                    changed = True
            if not changed:
                raise ValueError(f"Linha sem mudanca no CSV de impacto: {origin}")
            observed["todas"].add(origin)
            belongs = row["pertence_ao_treino"].strip().lower()
            if belongs not in {"true", "false"}:
                raise ValueError("pertence_ao_treino deve conter True ou False.")
            if belongs == "true":
                training.add(origin)

    for name in plan:
        if plan[name] != observed[name]:
            missing = sorted(plan[name] - observed[name])
            extra = sorted(observed[name] - plan[name])
            raise ValueError(f"{name}: previstas ausentes no CSV={missing}; inesperadas={extra}")
    if len(observed["todas"]) != conclusion["origens_com_mudanca"]:
        raise ValueError("Quantidade de origens diverge de conclusao.json.")
    if len(training) != conclusion["linhas_treino_com_mudanca"]:
        raise ValueError("Quantidade de linhas de treino diverge de conclusao.json.")

    print(f"Comparando a funcao com: {impact_path}")
    for name in plan:
        print(f"{name}: {len(plan[name])} origens; conjunto igual ao CSV")
    print("\nOrigem               historico  media  alvo  pertence_ao_treino")
    for origin in sorted(plan["todas"]):
        flags = ["sim" if origin in plan[name] else "nao" for name in columns]
        print(f"{origin:%Y-%m-%d %H:%M}    {flags[0]:>3}      {flags[1]:>3}   {flags[2]:>3}       "
              f"{'sim' if origin in training else 'nao'}")
    print(f"\nConferencia aprovada: {len(plan['todas'])} origens; {len(training)} pertencem ao treino.")
    print("Somente leitura: nenhum Spark, MERGE ou treino executado.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / "reports/scale/CJU_BA5EIGT/m07_2_delta",
        help="Pasta exata da execucao Delta a conferir.",
    )
    args = parser.parse_args(argv)
    try:
        conferir_execucao(args.run_dir)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Erro: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
