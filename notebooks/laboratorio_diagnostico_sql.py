"""Demonstração SQLite/pandas e preparação de prova real, sem treino ou Spark."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sqlite3
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/fechamento_m00_m09"
SOURCE = ROOT / "dist/databricks/CJU_BA5EIGT/m07_3"
ITEMS = ("M00-01", "M01-01", "M01-02", "M07-04")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def records(frame):
    return frame.astype(object).where(frame.notna(), None).to_dict(orient="records")


def demonstracao():
    observations = [
        ("A", "2027-01-01T00:00:00", 0), ("A", "2027-01-01T01:00:00", 12),
        ("A", "2027-01-01T03:00:00", None), ("A", "2027-01-03T00:00:00", 30),
        ("A", "2027-01-03T01:00:00", 40), ("A", "2027-01-03T01:00:00", 45),
        ("A", "2027-01-04T00:00:00", None), ("A", "2027-01-04T01:00:00", None),
        ("B", "2027-01-01T00:00:00", 100), ("B", "2027-01-01T02:00:00", 200),
        ("B", "2027-01-04T00:00:00", 0),
    ]
    source = pd.DataFrame(observations, columns=["id_ons", "din_instante", "val_geracao"])
    source.insert(0, "record_id", range(1, len(source) + 1))
    original = source.copy(deep=True)
    days = pd.DataFrame([(s, f"2027-01-{d:02d}") for s in ("A", "B") for d in range(1, 5)],
                        columns=["id_ons", "dia"])
    hours = pd.date_range("2027-01-01", "2027-01-05", freq="h", inclusive="left")
    grid = pd.DataFrame([(s, t.isoformat()) for s in ("A", "B") for t in hours],
                        columns=["id_ons", "din_instante"])
    sql_path = REPORTS / "M01-01/consultas.sql"
    with sqlite3.connect(":memory:") as con:
        source.to_sql("fonte", con, index=False)
        days.to_sql("dias", con, index=False)
        grid.to_sql("grade", con, index=False)
        con.executescript(sql_path.read_text(encoding="utf-8-sig"))
        left = pd.read_sql_query("SELECT * FROM diario_left ORDER BY id_ons,dia", con)
        inner = pd.read_sql_query("SELECT * FROM diario_inner ORDER BY id_ons,dia", con)
        quarantine = pd.read_sql_query("SELECT * FROM quarentena ORDER BY record_id", con)
        sparse = pd.read_sql_query("SELECT * FROM lag_esparso ORDER BY id_ons,din_instante", con)
        complete = pd.read_sql_query("SELECT * FROM lag_grade ORDER BY id_ons,din_instante", con)

    duplicate = source.duplicated(["id_ons", "din_instante"], keep=False)
    clean = source.loc[~duplicate].copy()
    clean["dia"] = clean.din_instante.str.slice(0, 10)
    summary = clean.groupby(["id_ons", "dia"], as_index=False).agg(
        horas_presentes=("record_id", "size"), horas_validas=("val_geracao", "count"),
        media_mwmed=("val_geracao", "mean"))
    pandas_result = days.merge(summary, on=["id_ons", "dia"], how="left", validate="one_to_one")
    for column in ("horas_presentes", "horas_validas"):
        pandas_result[column] = pandas_result[column].fillna(0).astype(int)
    pandas_result["cobertura"] = pandas_result.horas_validas / 24.0
    expected = pd.DataFrame([
        ("A", "2027-01-01", 3, 2, 6.0), ("A", "2027-01-02", 0, 0, None),
        ("A", "2027-01-03", 1, 1, 30.0), ("A", "2027-01-04", 2, 0, None),
        ("B", "2027-01-01", 2, 2, 150.0), ("B", "2027-01-02", 0, 0, None),
        ("B", "2027-01-03", 0, 0, None), ("B", "2027-01-04", 1, 1, 0.0),
    ], columns=["id_ons", "dia", "horas_presentes", "horas_validas", "media_mwmed"])
    expected["cobertura"] = expected.horas_validas / 24.0
    pd.testing.assert_frame_equal(left, expected, check_dtype=False, rtol=0, atol=1e-12)
    pd.testing.assert_frame_equal(left, pandas_result, check_dtype=False, rtol=0, atol=1e-12)
    assert len(left) == 8 and len(inner) == 5
    assert quarantine.record_id.tolist() == source.loc[duplicate, "record_id"].tolist()
    assert len(quarantine) == 2 and quarantine.val_geracao.tolist() == [40.0, 45.0]
    a3 = sparse.loc[sparse.id_ons.eq("A") & sparse.din_instante.eq("2027-01-01T03:00:00")].iloc[0]
    assert a3.instante_anterior == "2027-01-01T01:00:00" and a3.valor_linha_anterior == 12
    on_grid = complete.loc[complete.id_ons.eq("A") & complete.din_instante.eq("2027-01-01T03:00:00")].iloc[0]
    assert pd.isna(on_grid.valor_hora_anterior) and on_grid.registro_hora_anterior == 0
    assert on_grid.registro_presente == 1
    b_first = sparse.loc[sparse.id_ons.eq("B")].iloc[0]
    assert pd.isna(b_first.instante_anterior) and pd.isna(b_first.valor_linha_anterior)
    assert len(complete) == 192
    pd.testing.assert_frame_equal(source, original)
    checks = ["sql_vs_conta_manual", "sql_vs_pandas", "left_vs_inner", "quarentena_integral",
              "lag_linha_diferente_de_hora", "lag_na_grade_preserva_lacuna", "particao_por_serie",
              "cardinalidade_da_grade", "fonte_preservada"]
    return {"kind": "demonstracao_sintetica_resolvida_assistida", "passed": True,
            "checks": checks, "source_rows": len(source), "clean_rows": len(clean),
            "quarantine_rows": len(quarantine), "daily_left_rows": len(left), "daily_inner_rows": len(inner),
            "hourly_grid_rows": len(complete), "daily_reference": records(left)}, left


def preparar_recorte():
    folder = REPORTS / "M01-02"
    manifest_path, path = SOURCE / "manifesto_entrada.json", SOURCE / "geracao.parquet"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_hash = sha(path)
    assert source_hash == manifest["files"]["geracao.parquet"]["sha256"]
    frame = pd.read_parquet(path, columns=["din_instante", "val_geracao"])
    assert len(frame) == manifest["generation_rows"] == 8760
    dates = pd.to_datetime(frame.din_instante, errors="raise")
    if dates.isna().any() or dates.dt.tz is not None:
        raise ValueError("Este recorte exige os rótulos originais sem fuso e sem NaT.")
    first, last = dates.min(), dates.max()
    first_month = first.to_period("M").to_timestamp()
    if first > first_month:
        first_month += pd.DateOffset(months=1)
    start, end = first_month + pd.DateOffset(months=2), first_month + pd.DateOffset(months=3)
    if last + pd.Timedelta(hours=1) < end:
        raise ValueError("A fonte não cobre o terceiro mês completo definido no adendo.")
    protocol_path = folder / "protocolo_recorte.json"
    selection = {"schema": "renewcast-sql-real-slice-v1", "registered_at_utc": datetime.now(timezone.utc).isoformat(),
                 "rule": "terceiro mês civil completo; regra prévia no adendo, sem seleção por diagnóstico",
                 "source": path.relative_to(ROOT).as_posix(), "source_sha256": source_hash,
                 "manifest_sha256": sha(manifest_path), "source_rows": len(frame),
                 "source_min": first.isoformat(), "source_max": last.isoformat(),
                 "start_inclusive": start.isoformat(), "end_exclusive": end.isoformat(),
                 "id_ons": manifest["conjunto"], "timezone_assigned": False,
                 "predictive_test_selection": False, "independent_query_executed": False}
    if protocol_path.exists():
        old = json.loads(protocol_path.read_text(encoding="utf-8"))
        for key in ("source_sha256", "start_inclusive", "end_exclusive", "id_ons"):
            if old[key] != selection[key]:
                raise ValueError("O recorte já fixado é diferente; não o substitua silenciosamente.")
        selection = old
    else:
        write_json(protocol_path, selection)
    # A seleção concreta foi gravada ANTES do filtro e da exportação.
    filtered_at = datetime.now(timezone.utc).isoformat()
    assert datetime.fromisoformat(selection["registered_at_utc"]) <= datetime.fromisoformat(filtered_at)
    selected = frame.loc[dates.ge(start) & dates.lt(end)].copy()
    selected["din_instante"] = pd.to_datetime(selected.din_instante).map(pd.Timestamp.isoformat)
    selected.insert(0, "id_ons", manifest["conjunto"])
    selected = selected.sort_values("din_instante", kind="stable").reset_index(drop=True)
    calendar = pd.DataFrame({"din_instante": [t.isoformat() for t in pd.date_range(start, end, freq="h", inclusive="left")]})
    calendar.insert(0, "id_ons", manifest["conjunto"])
    selected.to_csv(folder / "recorte_real.csv", index=False, encoding="utf-8-sig")
    calendar.to_csv(folder / "calendario_exercicio.csv", index=False, encoding="utf-8-sig")
    assert sha(path) == source_hash
    return {**selection, "filter_started_at_utc": filtered_at, "protocol_written_before_filter": True,
            "exported_rows": len(selected), "calendar_positions": len(calendar),
            "source_preserved": True, "no_imputation": True, "no_injected_failures": True,
            "export_files": {p.name: sha(p) for p in (folder / "recorte_real.csv", folder / "calendario_exercicio.csv")}}


def preparar_documentos_e_recibos(demo, daily, real):
    demonstration = daily.copy()
    demonstration.insert(0, "natureza", "referencia_assistida_demo_sintetica_resolvida")
    demonstration.to_csv(REPORTS / "M01-02/diagnostico.csv", index=False, encoding="utf-8-sig")
    card = f"""# Data card — recorte de transferência SQL M01-02

Preparação assistida em 25/11/2026. Diagnóstico independente: **pendente**.

Fonte: `dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet`, pacote M07.3,
série `{real['id_ons']}`. São {real['source_rows']} registros na fonte preservada,
de `{real['source_min']}` a `{real['source_max']}`. O SHA-256 é
`{real['source_sha256']}`; o manifesto identifica sua linhagem.
É um recorte já preparado do projeto, não uma nova aquisição dos brutos ONS.

O exercício usa `[{real['start_inclusive']}, {real['end_exclusive']})`,
o terceiro mês civil completo conforme a regra fixada antes do filtro.
Foram exportadas {real['exported_rows']} linhas e {real['calendar_positions']}
posições esperadas de calendário. Esses são metadados da preparação, não uma
consulta ou resposta atribuída ao aluno.

| Campo | Contrato |
|---|---|
| id_ons | Identidade da série, adicionada a partir do manifesto |
| din_instante | Rótulo temporal original, sem atribuição silenciosa de fuso |
| val_geracao | Geração média em MWmed, valores preservados |
| Chave pretendida | (id_ons, din_instante), uma posição por hora |
| Ausências e zero | Não imputados; zero observado continua zero |
| Duplicidade | Deve ser diagnosticada antes de JOIN/janela; nenhuma cópia é eliminada na exportação |

Arquivos: [fonte do exercício](../reports/fechamento_m00_m09/M01-02/recorte_real.csv),
[calendário](../reports/fechamento_m00_m09/M01-02/calendario_exercicio.csv) e
[protocolo concreto](../reports/fechamento_m00_m09/M01-02/protocolo_recorte.json).
A fonte original e o calendário permanecem separados. Não foram injetadas falhas.
O laboratório não executa a SQL independente nem classifica a qualidade do mês.

Fuso físico, início/fim do intervalo, versão histórica publicada e disponibilidade
real continuam não verificados. O pacote M07.3 usa atraso de geração assumido e
snapshot fixado; isso não demonstra disponibilidade point-in-time da fonte.
Não é teste preditivo novo nem autorização operacional.

`diagnostico.csv` é a referência assistida **sintética A/B**; não é a análise do
recorte real. A resposta e a consulta próprias continuam nos templates pendentes.
"""
    (ROOT / "docs/data_card.md").write_text(card, encoding="utf-8")
    topics = {
        "M00-01": "Mapa do percurso CLI/features preparado; caso novo e adaptação humana ainda sem resposta.",
        "M01-01": "Demonstração JOIN/nulos/LAG/quarentena conferida; novo caso C e sua defesa continuam pendentes.",
        "M01-02": "Mês real exportado sob regra fixada antes do filtro; consulta e reconciliação independentes não executadas.",
        "M07-04": "Parecer corrigido preservado; perguntas novas de janela/plano/medição preparadas, sem Spark ou Databricks.",
    }
    for item in ITEMS:
        folder = REPORTS / item
        text = f"""# {item} — parecer de preparação, não de autonomia

25/11/2026 · preparação e revisão técnica assistidas por Codex.

{topics[item]}

O comando local de preparação usou SQLite em memória e pandas. As nove verificações
da demonstração passaram, incluindo comparação com conta manual e entre motores,
preservação da fonte, quarentena e calendário. A exportação real é preparação
de insumo, sem diagnóstico resolvido ou novo benchmark preditivo.

**Estado: await_human.** Resposta independente, avaliação de transferência e
revisão humana atribuída ainda estão pendentes. Os templates permanecem sem
respostas; os resultados da demonstração são identificados como assistidos.
Não há novo aceite formativo nem operacional, treinamento ou repetição de Spark.
"""
        (folder / "parecer.md").write_text(text, encoding="utf-8")
        common = [Path(__file__), ROOT / "docs/roadmap_m00_m09/Diagnostico_SQL.md",
                  folder / "protocolo.json", folder / "parecer.md", REPORTS / "M01-02/adendo_protocolo.json"]
        own = list(folder.glob("*.md")) + list(folder.glob("*.sql"))
        if item == "M00-01":
            own.append(ROOT / "docs/learning/checkpoint.md")
        if item == "M01-02":
            own += [ROOT / "docs/data_card.md", folder / "protocolo_recorte.json", *folder.glob("*.csv")]
        if item == "M07-04":
            own.append(ROOT / "reports/scale_comparison.md")
        output = {p.relative_to(ROOT).as_posix(): sha(p) for p in dict.fromkeys(common + own)}
        result = {"schema": "renewcast-sql-preparation-result-v1", "item": item, "status": "await_human",
                  "preparation_completed": True, "independent_response_received": False,
                  "human_acceptance_claimed": False, "student_autonomy_claimed": False,
                  "responsibility": "Preparação e revisão técnica assistidas por Codex.",
                  "executed_at_utc": datetime.now(timezone.utc).isoformat(),
                  "command": [sys.executable, *sys.argv], "exit_code": 0,
                  "python": sys.version.split()[0], "platform": platform.platform(),
                  "versions": {"pandas": version("pandas"), "pyarrow": version("pyarrow"), "sqlite": sqlite3.sqlite_version},
                  "summary": topics[item], "demo": demo,
                  "real_exercise_preparation": real if item == "M01-02" else {"independent_query_executed": False},
                  "output_sha256": output, "models_trained": False, "pickle_loaded": False,
                  "spark_or_docker_run": False, "network": False, "historical_runs_modified": False,
                  "operational_approval": False}
        write_json(folder / "resultado.json", result)


def executar_consulta(path):
    # Esta rota é opcional e não é usada durante a preparação da prova.
    sql = path.read_text(encoding="utf-8-sig")
    if not any(line.strip() and not line.lstrip().startswith("--") for line in sql.splitlines()):
        raise ValueError("Consulta independente ainda pendente; o arquivo contém somente comentários.")
    folder = REPORTS / "M01-02"
    with sqlite3.connect(":memory:") as con:
        pd.read_csv(folder / "recorte_real.csv").to_sql("recorte", con, index=False)
        pd.read_csv(folder / "calendario_exercicio.csv").to_sql("calendario", con, index=False)
        con.execute("PRAGMA query_only=ON")
        answer = pd.read_sql_query(sql, con)
    output = folder / "resultado_consulta_usuario.csv"
    answer.to_csv(output, index=False, encoding="utf-8-sig")
    write_json(folder / "execucao_consulta_usuario.json", {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(), "query_sha256": sha(path),
        "output_sha256": sha(output), "rows": len(answer), "independence_or_acceptance_inferred": False})
    print(f"Consulta executada em memória; resultado: {output.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preparar", action="store_true")
    group.add_argument("--verificar", action="store_true")
    group.add_argument("--consultas-exercicio", type=Path)
    args = parser.parse_args()
    if args.consultas_exercicio:
        executar_consulta(args.consultas_exercicio)
        return 0
    demo, daily = demonstracao()
    print(daily.to_string(index=False))
    print(f"Demonstração assistida: {len(demo['checks'])} verificações passaram; SQL, pandas e conta manual coincidem.")
    if args.preparar:
        real = preparar_recorte()
        preparar_documentos_e_recibos(demo, daily, real)
        print(f"Recorte fixado: {real['start_inclusive']} até {real['end_exclusive']} (fim exclusivo).")
        print(f"Exportação: {real['exported_rows']} linhas reais; {real['calendar_positions']} posições de calendário.")
        print("M00-01/M01-01/M01-02/M07-04: preparação concluída; respostas/defesa em await_human.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
