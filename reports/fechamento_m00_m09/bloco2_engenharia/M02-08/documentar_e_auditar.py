"""Audita recibos existentes e documenta os resultados; nao sorteia bootstrap."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent.parent
ITEMS = {24: "M02-08", 6: "M02-07"}
DATA = {24: "july_development_h24", 6: "july_development"}
SHARED = [ROOT / "docs/roadmap_m00_m09/Bloco_2_Bootstrap.md",
          ROOT / "reports/statistical_audit.md"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, text):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text.rstrip() + "\n")


def fmt(value):
    return f"{value:.4f}"


def table(frame, fold=False):
    header = ("| Fold | Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |\n"
              "| --- | ---: | ---: | --- | ---: |\n") if fold else (
              "| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |\n"
              "| ---: | ---: | --- | ---: |\n")
    rows = []
    for row in frame.itertuples():
        prefix = f"{int(row.fold)} | " if fold else ""
        rows.append(f"| {prefix}{row.block_hours} | {fmt(row.mean_gain_mwmed)} | "
                    f"[{fmt(row.ci95_low_mwmed)}; {fmt(row.ci95_high_mwmed)}] | "
                    f"{fmt(row.bootstrap_fraction_nonpositive)} |")
    return header + "\n".join(rows)


def verify(horizon, item):
    folder = BASE / item
    protocol = read(folder / "protocolo.json")
    result = read(folder / "resultado.json")
    assert protocol["primary_horizon_hours"] == horizon
    assert result["completed"] and result["exit_code"] == 0
    assert result["protocol_sha256"] == sha(folder / "protocolo.json")
    assert result["runner_sha256"] == sha(BASE / "M02-08/executar.py")
    assert result["primary_horizon"] == horizon
    for group in ["input_sha256", "frozen_method_sha256", "prior_construction_evidence_sha256"]:
        for path, value in protocol[group].items():
            assert sha(ROOT / path) == value, path
    for path, value in result["output_sha256"].items():
        assert sha(folder / path) == value, path
    prior_path = ROOT / "reports/fechamento_m00_m09/M02-05/resultado.json"
    prior = read(prior_path)
    assert prior["completed"] and prior["exit_code"] == 0
    assert prior["test_counts"] == {"passed": 59, "failed": 0, "skipped": 0}
    for path, value in prior["code_sha256"].items():
        assert sha(ROOT / path) == value
    for path, value in prior["output_sha256"].items():
        assert sha(prior_path.parent / path) == value
    source_dir = ROOT / "reports/weather_ablation/CJU_BA5EIGT" / DATA[horizon]
    frame = pd.read_csv(source_dir / "predictions.csv", float_precision="round_trip")
    metadata = read(source_dir / "metadata.json")
    assert sha(source_dir / "predictions.csv") == metadata["output_sha256"]["predictions.csv"]
    assert sha(source_dir / "protocol.json") == metadata["protocol_sha256"]
    assert len(frame) == 504 and frame.groupby("fold").size().to_dict() == {1:168, 2:168, 3:168}
    origin = pd.to_datetime(frame.forecast_origin, utc=True)
    target = pd.to_datetime(frame.target_time, utc=True)
    available = pd.to_datetime(frame.target_available_at, utc=True)
    assert origin.is_monotonic_increasing and origin.is_unique
    assert (target - origin).eq(pd.Timedelta(hours=horizon)).all()
    assert (available - target).eq(pd.Timedelta(hours=2)).all()
    assert origin.diff().iloc[1:].eq(pd.Timedelta(hours=1)).all()
    maes = {}
    for model in ["persistence", "hgb_history", "hgb_history_weather"]:
        error = (frame.target_generation - frame[model]).abs()
        np.testing.assert_allclose(error, frame["absolute_error_" + model], rtol=1e-12, atol=1e-10)
        maes[model] = float(error.mean())
    np.testing.assert_allclose(frame.delta_absolute_error,
        (frame.target_generation-frame.hgb_history).abs()-(frame.target_generation-frame.hgb_history_weather).abs(),
        rtol=1e-12, atol=1e-10)
    derived = pd.read_csv(folder / "pareado_persistencia.csv", float_precision="round_trip")
    lineage = read(folder / "linhagem_persistencia.json")
    assert lineage["source_sha256"] == sha(source_dir / "predictions.csv")
    assert lineage["derived_sha256"] == sha(folder / "pareado_persistencia.csv")
    for name in lineage["preserved_exactly"]:
        pd.testing.assert_series_equal(frame[name], derived[name], check_exact=True)
    pd.testing.assert_series_equal(frame.persistence, derived.hgb_history, check_names=False, check_exact=True)
    pd.testing.assert_series_equal(frame.hgb_history, derived.original_hgb_history, check_names=False, check_exact=True)
    assert derived.reference_model.eq("persistence").all()
    np.testing.assert_allclose(derived.delta_absolute_error,
        (frame.target_generation-frame.persistence).abs()-(frame.target_generation-frame.hgb_history_weather).abs(),
        rtol=1e-12, atol=1e-10)
    tables = {}
    maximum = 0.
    for comparison, filename, reference in [
        ("historia", "bootstrap.csv", "hgb_history"),
        ("persistencia", "bootstrap_vs_persistencia.csv", "persistence")]:
        receipt_path = folder / ("cli_"+comparison) / "receipt.json"
        receipt = read(receipt_path)
        source = source_dir / "predictions.csv" if comparison == "historia" else folder / "pareado_persistencia.csv"
        csv_path = folder / ("cli_"+comparison) / "summary.csv"
        assert receipt["completed"] and receipt["exit_code"] == 0
        assert receipt["input"]["sha256"] == sha(source)
        assert receipt["code"]["sha256"] == result["method_sha256"]
        assert receipt["output_sha256"]["summary.csv"] == sha(csv_path) == sha(folder / filename)
        assert receipt["parameters"] == {"block_hours":[6,24,48], "repetitions":5000, "seed":42, "confidence_level":.95}
        assert receipt["rows_input"] == 504 and receipt["rows_summary"] == 12
        assert pd.Timestamp(protocol["registered_at_utc"]) < pd.Timestamp(receipt["started_at_utc"])
        execution = result["analysis"]["history_reference" if comparison == "historia" else "persistence_reference"]["execution"]
        assert execution["exit_code"] == 0 and execution["command"] == receipt["command"]
        assert pd.Timestamp(execution["started_at_utc"]) <= pd.Timestamp(receipt["started_at_utc"])
        assert pd.Timestamp(receipt["completed_at_utc"]) <= pd.Timestamp(execution["finished_at_utc"])
        summary = pd.read_csv(csv_path, float_precision="round_trip")
        assert len(summary) == 12
        assert sorted(summary.block_hours.unique()) == [6,24,48]
        assert summary.repetitions.eq(5000).all() and summary.seed.eq(42).all()
        assert summary.confidence_level.eq(.95).all()
        assert summary.bootstrap_fraction_nonpositive.between(0,1).all()
        assert summary.ci95_low_mwmed.le(summary.ci95_high_mwmed).all()
        assert np.isfinite(summary.select_dtypes(include="number").drop(columns="fold")).all().all()
        for block in [6,24,48]:
            rows = summary.loc[summary.block_hours.eq(block)]
            assert len(rows) == 4 and rows.scope.eq("aggregate").sum() == 1
            assert sorted(rows.loc[rows.scope.eq("fold"),"fold"].tolist()) == [1.,2.,3.]
            for row in rows.itertuples():
                part = frame if row.scope == "aggregate" else frame.loc[frame.fold.eq(row.fold)]
                assert len(part) == row.n
                ref = float((part.target_generation-part[reference]).abs().mean())
                candidate = float((part.target_generation-part.hgb_history_weather).abs().mean())
                delta = float(((part.target_generation-part[reference]).abs()-(part.target_generation-part.hgb_history_weather).abs()).mean())
                for observed, expected in [(row.mae_history_mwmed,ref), (row.mae_history_weather_mwmed,candidate), (row.mean_gain_mwmed,delta)]:
                    np.testing.assert_allclose(observed,expected,rtol=1e-12,atol=1e-10)
                    maximum = max(maximum, abs(observed-expected))
            folds = rows.loc[rows.scope.eq("fold")]
            aggregate = rows.loc[rows.scope.eq("aggregate")].iloc[0]
            np.testing.assert_allclose(np.average(folds.mean_gain_mwmed,weights=folds.n), aggregate.mean_gain_mwmed,rtol=1e-12,atol=1e-10)
        tables[comparison] = summary
    return {"horizon":horizon, "item":item, "folder":folder, "source_dir":source_dir,
            "protocol":protocol, "result":result, "maes":maes, "tables":tables,
            "maximum_point_estimate_difference":maximum}


METHOD = """O estimando principal é a média dos deltas pareados
`|alvo − HGB história| − |alvo − HGB história+meteorologia|`, em MWmed.
O suplemento troca apenas a referência por persistência. Ganho positivo favorece
o candidato história+meteorologia; ganho contra um HGB fraco não implica ganho
contra a persistência.

Os protocolos foram registrados em 25/11/2026, às 16:20:13 UTC, antes das quatro
execuções, concluídas entre 16:22:39 e 16:24:38 UTC. Fixaram 5.000 réplicas,
semente 42, blocos 6/24/48 horas e quantis lineares 2,5%/97,5%. Cada réplica
reamostra blocos consecutivos **dos deltas pareados**, com retorno circular
restrito ao mesmo fold, até obter 168 horas; o último bloco é truncado.
Nenhum bloco atravessa a fronteira de um fold. Os três folds observados ficam
fixos, com 168 horas cada; não se sorteiam folds como unidades independentes.
O agregado usa a média ponderada por n das três médias de cada réplica, e
calcula seus quantis a partir dessas 5.000 médias agregadas. Não se faz média
das pontas dos intervalos. Como os folds têm o mesmo n, os pesos são 1/3.

Os fluxos locais usam `SeedSequence([42, comprimento_do_bloco, fold])`.
Os três comprimentos foram fixados antes do cálculo e todos são publicados,
independentemente do sinal. Um bloco de 6 horas não é o horizonte h+6:
o primeiro é uma escolha de dependência na reamostragem; o segundo identifica
o alvo da previsão.

O intervalo é percentil, nominalmente de 95%, **condicional às previsões
salvas, aos folds e à família de blocos escolhida**. Não é intervalo de
predição de uma observação futura, garantia de cobertura futura ou correção
da seleção histórica de modelos. A fração de réplicas com ganho ≤ 0 é um
resumo descritivo da distribuição bootstrap, sem centralização sob uma
hipótese nula; **não é p-valor**, probabilidade de a hipótese nula ser verdadeira
ou probabilidade de o modelo perder no futuro. Fração zero significa zero
ocorrências nas 5.000 réplicas, sem provar impossibilidade de perda.

O método preserva dependência local dentro do tamanho do bloco, sob uma
aproximação de repetição temporal dentro de cada fold. O retorno do final
para o início de uma semana é uma aproximação; a distribuição real pode
conter mudanças de regime e dependência além de 48 horas. A escolha de blocos
não elimina isso. Não foi usado bootstrap IID como evidência temporal, nem
inferida independência dos folds ou dos três comprimentos. Os intervalos
publicados são pontuais; não há ajuste de comparações múltiplas nem alegação
de cobertura simultânea de todas as linhas.
"""

SCOPE = """São 504 previsões salvas por horizonte para CJU_BA5EIGT, com origens
horárias de 11/07/2026 06:00 a 01/08/2026 05:00, conforme timestamps do CSV
interpretados como UTC. Fold 1 vai até 18/07 05:00; fold 2, de 18/07 06:00
a 25/07 05:00; fold 3, de 25/07 06:00 a 01/08 05:00. O rótulo
`july_development` não implica que todos os alvos estejam em julho.
Foi conferido `target_time − forecast_origin = horizonte` em todas as linhas,
e `target_available_at − target_time = 2h`. Isso verifica a coerência interna
dos relógios gravados; o significado físico do fuso e a disponibilidade
histórica operacional continuam sujeitos aos limites M04.

Os dois conjuntos já haviam sido examinados e usados no desenvolvimento.
O protocolo novo fixa a análise da incerteza; não transforma esses dados em
holdout novo. As origens/folds coincidem, mas os alvos h+6 e h+24 ocorrem em
instantes diferentes e os cortes de treino históricos também diferem.
Portanto, a comparação entre horizontes é descritiva. Não foi calculado
intervalo da diferença entre horizontes, teste de superioridade de horizonte
ou efeito causal da meteorologia.
"""

TECHNICAL = """Foram preservados a fonte congelada do bootstrap, os CSVs de origem,
os protocolos, metadados e métricas históricos, os quatro recibos CLI e os
dois resultados já concluídos. Esta retomada auditou os arquivos existentes;
não repetiu os sorteios, o treino, a inferência nem os 59 testes M02-05.
Os hashes da fonte e dos testes coincidem com o recibo de 59 casos aprovados,
cujo alcance continua sendo construção/verificação do método em casos
controlados. A execução nos dados reais salvos é evidência distinta, aqui
registrada nos recibos M02-08/M02-07.

A auditoria final reconcilia SHA-256 das entradas, protocolos, fonte,
recibos e saídas; verifica precedência temporal do protocolo, comandos e
exit codes 0, 504 linhas, grades horárias, folds, erros absolutos e deltas,
parâmetros, 12 linhas de resumo por comparação, estimativas pontuais e
ponderação por n, finitude e ordenação dos intervalos. As réplicas individuais
não foram persistidas pela CLI congelada: os quantis são os produzidos por
essa fonte, coberta pelos testes prévios. A revisão dos resumos não se
apresenta como recomputação independente de cada sorteio ou de seus quantis.

No suplemento, `pareado_persistencia.csv` é uma derivação declarada:
`hgb_history` recebe a coluna original `persistence` somente para reutilizar
o campo de referência exigido pela CLI; `original_hgb_history` preserva o
HGB original, e `reference_model=persistence` identifica a troca.
Origens, alvos, disponibilidade, folds e candidato foram preservados exatamente;
o delta foi recalculado para a nova referência. A coluna do resumo CLI chamada
`mae_history_mwmed` representa **MAE da persistência** nesse suplemento.
`linhagem_persistencia.json` registra fonte, derivação e hashes. Os recibos
brutos mantêm os nomes genéricos da CLI; a interpretação correta está nesta
linhagem e nos títulos das tabelas.

Toda solução, execução e interpretação são atribuídas ao Codex, com assistência
integral declarada. A revisão técnica assistida não certifica autonomia pessoal,
autoria independente, aprovação humana ou autorização de operação.
"""


def comparison_section(record):
    h = record["horizon"]
    mae = record["maes"]
    text = (f"### h+{h}: métricas e efeito\n\n"
            f"MAE de persistência: **{fmt(mae['persistence'])} MWmed**; HGB história: "
            f"**{fmt(mae['hgb_history'])} MWmed**; HGB história+meteorologia: "
            f"**{fmt(mae['hgb_history_weather'])} MWmed**.\n\n")
    for comparison, label in [("historia", "Ganho contra HGB história"), ("persistencia", "Ganho contra persistência — suplemento")]:
        frame = record["tables"][comparison]
        text += f"#### {label}\n\n" + table(frame.loc[frame.scope.eq("aggregate")])
        text += "\n\nTodos os folds, sem escolher o bloco pelo sinal:\n\n"
        text += table(frame.loc[frame.scope.eq("fold")], fold=True) + "\n\n"
    return text


INTERPRETATIONS = {
24: """O ganho principal é 9,3841 MWmed (24,5773% do MAE do HGB história).
Os três intervalos agregados ficam acima de zero. Isso sustenta uma redução
condicional do erro nesse desenvolvimento em relação ao HGB de história
congelado. No fold 1, porém, os intervalos de blocos 24h e 48h incluem zero,
enquanto o de 6h fica pouco acima de zero. Os folds 2 e 3 têm intervalos
positivos nas três escolhas. A média agregada não torna uniforme a evidência
de cada semana.

A persistência já tem MAE 29,3943 MWmed, menor que os 38,1821 do HGB história.
Contra ela, o ganho do candidato é apenas 0,5963 MWmed (2,0285%); os três
intervalos agregados incluem zero. O fold 1 apresenta ganho pontual
**negativo de −7,7185**, contraposto a +4,2482 e +5,2591 nos outros folds.
Logo, esta análise não estabelece melhoria estável sobre a persistência.
Escolher apenas o contraste contra história ou apenas o bloco de 6h ocultaria
essa conclusão prática. Não há limiar econômico de benefício registrado
neste protocolo; MAE e IC por si só não encerram uma decisão de operação.
""",
6: """O ganho principal é 6,2904 MWmed (19,2106% do MAE do HGB história).
Os três intervalos agregados ficam acima de zero; as frações ≤ 0 são 0,
0 e 0,0004. A última corresponde a 2 de 5.000 réplicas, sem interpretação
de p-valor. A heterogeneidade semanal permanece: o fold 2 inclui zero
com bloco de 6h, mas tem intervalos positivos com 24h/48h; no fold 3
acontece a inversão. O fold 1 tem ganho maior, 11,8074 MWmed, com os três
intervalos positivos. Dependência serial e truncamento do último bloco
podem tornar a largura não monotônica; não se exige que todo bloco maior
gere todo intervalo maior, nem se escolhe a conclusão mais conveniente.

Contra persistência, o ganho é 33,8080 MWmed (56,1017%), com intervalos
agregados positivos em 6/24/48h. Ainda assim, o fold 1 tem ganho apenas
3,6740 e intervalos cruzando zero nas três escolhas, enquanto os folds 2 e 3
mostram ganhos de 51,3050 e 46,4450. O efeito agregado forte está ligado
a essas duas semanas; não é evidência de benefício uniforme em todo regime.
"""}


def main():
    started = datetime.now(timezone.utc).isoformat()
    records = {h: verify(h, item) for h, item in ITEMS.items()}
    main_document = "# Bootstrap horário aplicado — bloco 2\n\n25/11/2026 · M02-08 e M02-07 · portão de engenharia.\n\n"
    main_document += "## Resultado e decisão técnica\n\n"
    main_document += ("A história+meteorologia reduz o MAE agregado contra o HGB história nos dois "
                      "horizontes salvos. A referência muda a decisão: em h+24, a vantagem sobre "
                      "persistência é pequena e incerta; em h+6, o ganho agregado contra "
                      "persistência é maior, com heterogeneidade por semana. O aceite aqui "
                      "é a execução e interpretação corretas, sem exigir ganho positivo "
                      "ou aprovar implantação.\n\n")
    main_document += "## Recorte e relógios\n\n" + SCOPE + "\n## Método e interpretação da incerteza\n\n" + METHOD
    for h in [24,6]:
        main_document += "\n" + comparison_section(records[h]) + INTERPRETATIONS[h]
    main_document += "\n## Transferência aplicada entre os recortes\n\n"
    main_document += ("A adaptação de h+24 (M02-08) para h+6 (M02-07) conserva o estimando, "
                      "a unidade MWmed, o pareamento, a estratificação e todos os parâmetros. "
                      "Muda o CSV, o horizonte e o alvo; o protocolo identifica essa mudança "
                      "antes da análise. A conclusão foi recalculada: o contraste com história "
                      "fica positivo nos dois agregados; o contraste com persistência passa "
                      "de pequeno/incerto em h+24 para grande nos agregados h+6. Essa mudança "
                      "é resultado dos dados, não cópia de uma conclusão histórica. "
                      "Não autoriza chamar h+6 de superior a h+24, pois os alvos diferem.\n\n")
    main_document += "## Proveniência e verificações\n\n" + TECHNICAL
    main_document += "\nAmbiente dos quatro recibos: Python 3.12.13, NumPy 2.5.3, pandas 3.0.5, Windows 11. "
    main_document += "Fonte congelada SHA-256 `f8c1dff888fb5796e5405b87761da038d73af4164435f829abd1f1cca078dc03`.\n\n"
    main_document += "Comando conjunto efetivamente executado, preservado nos resultados:\n\n```powershell\n"
    main_document += "& 'C:\\Users\\marhl\\miniconda3\\envs\\renewable-forecast\\python.exe' reports\\fechamento_m00_m09\\bloco2_engenharia\\M02-08\\executar.py\n```\n\n"
    main_document += ("O runner chamou a CLI quatro vezes com `--block-hours 6 24 48 "
                      "--repetitions 5000 --seed 42`. As listas exatas de argumentos, stdout, "
                      "stderr, horários e exit code 0 estão em `resultado.json`; cada chamada "
                      "tem `cli_historia/receipt.json` ou `cli_persistencia/receipt.json`. "
                      "O tempo externo conjunto foi 118,22 s, incluindo inicialização dos "
                      "subprocessos; os tempos internos menores da CLI não representam todo "
                      "o custo observado pelo runner.\n\n")
    main_document += "| Item | Fonte das previsões | SHA-256 de predictions.csv |\n| --- | --- | --- |\n"
    for h in [24,6]:
        record = records[h]
        main_document += f"| {record['item']} / h+{h} | `reports/weather_ablation/CJU_BA5EIGT/{DATA[h]}` | `{sha(record['source_dir']/'predictions.csv')}` |\n"
    main_document += "\n## Arquivos de saída\n\n"
    main_document += ("Em cada pasta `reports/fechamento_m00_m09/bloco2_engenharia/M02-08` e "
                      "`M02-07`: protocolo e resultado preservados; `bootstrap.csv` principal; "
                      "`bootstrap_vs_persistencia.csv`; CSV derivado e linhagem; dois recibos "
                      "CLI; `analise_tecnica.md`, `parecer.md` e `auditoria_final.json`. "
                      "M02-07 acrescenta `resposta_tecnica.md`, e `reports/statistical_audit.md` "
                      "consolida a interpretação. O script `documentar_e_auditar.py` audita e "
                      "documenta sem sortear novas réplicas. Seus arquivos são exclusivos: "
                      "a repetição exige destinos novos para preservar esta rodada.\n\n"
                      "A decisão de cadastro e a revisão integrada do bloco cabem à consolidação "
                      "do agente principal. Estes artefatos não encerram formação independente "
                      "nem comprovações do portão operacional.\n")
    save(SHARED[0], main_document)
    for h in [24,6]:
        record = records[h]
        folder = record["folder"]
        analysis = f"# {record['item']} — análise técnica do bootstrap h+{h}\n\n"
        analysis += "25/11/2026 · Solução e revisão técnicas fornecidas com assistência Codex.\n\n"
        analysis += INTERPRETATIONS[h] + "\n## Recorte\n\n" + SCOPE
        analysis += "\n## Método\n\n" + METHOD + "\n## Resultados completos\n\n" + comparison_section(record)
        analysis += "\n## Auditoria e atribuição\n\n" + TECHNICAL
        analysis += f"\nDiferença absoluta máxima na recomputação dos MAEs/ganhos dos 24 resumos: {record['maximum_point_estimate_difference']:.17g} MWmed. "
        analysis += "Os hashes e o comando da auditoria posterior ficam em `auditoria_final.json`; "
        analysis += "o resultado original da execução foi mantido. A síntese conjunta está em "
        analysis += "`docs/roadmap_m00_m09/Bloco_2_Bootstrap.md`.\n"
        save(folder / "analise_tecnica.md", analysis)
        parecer = f"# Parecer técnico assistido — {record['item']}\n\n"
        parecer += "25/11/2026 · Responsável: Codex, agente de bootstrap e auditoria do bloco 2.\n\n"
        parecer += ("**Decisão: aprovado no escopo técnico de engenharia atribuído.** Foram "
                    "localizadas execuções completas anteriores à retomada, com quatro "
                    "recibos, comandos reais e exit codes 0. A auditoria posterior preservou "
                    "esses arquivos e conferiu protocolo prévio, hashes, pareamento, "
                    "relógios internos, estimativas e todos os resumos de 6/24/48h. "
                    "Não houve novo treino nem repetição dos 59 testes congelados.\n\n")
        if h == 24:
            parecer += ("C1 atendido: previsões salvas reutilizadas, 5.000 réplicas, semente 42 e "
                        "blocos pré-fixados, sem refazer ajuste. C2 atendido: blocos horários "
                        "circulares dentro de folds fixos, agregação ponderada por n e "
                        "intervalos condicionais explicitados; todos os blocos publicados.\n\n")
        else:
            parecer += ("A transferência aplicada usou h+6 como outro recorte, registrado antes "
                        "da análise, com efeito e incerteza próprios. A resposta técnica explica "
                        "a mudança de conclusão contra persistência e os limites da comparação "
                        "entre horizontes. O critério antigo de resposta independente permanece "
                        "histórico; esta entrega fornece a solução e não certifica autonomia.\n\n")
        parecer += INTERPRETATIONS[h]
        parecer += ("\nA aprovação técnica é da execução/interpretação; não implica adoção do "
                    "modelo. O desenvolvimento já foi examinado, os alvos dos horizontes "
                    "diferem e o fuso físico não foi homologado por esta análise. Não há "
                    "validação prospectiva, autorização de produção ou revisão humana "
                    "independente atribuída. A revisão integrada e a atualização do cadastro "
                    "serão realizadas pelo agente principal.\n\n"
                    "Evidências: `protocolo.json`, `resultado.json`, `bootstrap.csv`, "
                    "`bootstrap_vs_persistencia.csv`, `linhagem_persistencia.json`, "
                    "`analise_tecnica.md` e `auditoria_final.json`.\n")
        save(folder / "parecer.md", parecer)
    response = "# M02-07 — resposta técnica fornecida: transferência para h+6\n\n"
    response += ("Autoria: Codex, 25/11/2026. Solução integral de engenharia com assistência "
                 "declarada; não é resposta independente do usuário.\n\n"
                 "O recorte principal M02-08 é h+24; a transferência M02-07 aplica o mesmo "
                 "estimando a h+6 usando outro CSV de previsões históricas salvas. O "
                 "protocolo h+6 foi gravado às 16:20:13.842474 UTC, antes dos cálculos. "
                 "A semente, réplicas, blocos, estratificação e regra de sinal são idênticos. "
                 "Mudam o alvo temporal e os ajustes históricos já salvos; não houve novo ajuste.\n\n")
    response += INTERPRETATIONS[6]
    response += ("\nEm h+24, o ganho contra história é 9,3841 MWmed e o ganho contra "
                 "persistência é 0,5963 MWmed, com ICs deste último incluindo zero. Em "
                 "h+6, a comparação contra história é menor, 6,2904, mas contra "
                 "persistência é muito maior, 33,8080. Isso mostra por que a referência "
                 "faz parte da pergunta: o HGB história tem MAE 38,1821 contra persistência "
                 "29,3943 em h+24; em h+6, os respectivos MAEs são 32,7444 e 60,2620.\n\n"
                 "A decisão fornecida é manter a evidência h+6 como melhoria condicional "
                 "do erro agregado contra as duas referências, com ressalva de "
                 "heterogeneidade. Para h+24, a evidência de melhoria frente ao HGB "
                 "história é positiva, mas a vantagem frente à persistência não está "
                 "estabelecida de modo estável. Nenhuma dessas frases se estende a dados "
                 "futuros ou sustenta uma aprovação operacional. Não se subtraiu IC de "
                 "h+6 do de h+24, nem se testou superioridade entre alvos distintos.\n\n")
    response += METHOD
    response += "\nAs tabelas completas estão em `analise_tecnica.md` e a conferência dos artefatos em `auditoria_final.json`.\n"
    save(BASE / "M02-07/resposta_tecnica.md", response)
    audit_text = "# Auditoria estatística aplicada — M02-07 e M02-08\n\n25/11/2026 · Codex · assistência integral declarada.\n\n"
    audit_text += ("Este relatório é a síntese da análise de bootstrap em previsões de "
                   "desenvolvimento já examinadas. Não registra novo benchmark nem uma "
                   "resposta independente do usuário.\n\n")
    audit_text += SCOPE + "\n" + METHOD
    for h in [24,6]:
        audit_text += f"\n## h+{h}\n\n" + INTERPRETATIONS[h]
        for comparison,label in [("historia","Referência HGB história"),("persistencia","Referência persistência")]:
            audit_text += "\n### " + label + "\n\n" + table(records[h]["tables"][comparison].query("scope == 'aggregate'")) + "\n"
    audit_text += "\n## Conferência e decisão\n\n" + TECHNICAL
    audit_text += ("\nO efeito foi calculado por par de previsões, e a dependência recebeu a "
                   "sensibilidade de três blocos previamente fixados. A decisão é técnica "
                   "e condicional ao desenvolvimento: concluir a entrega de engenharia e "
                   "preservar os limites de generalização e operação. Os detalhes por fold, "
                   "comandos e hashes constam nas pastas M02-07/M02-08 do bloco 2 e em "
                   "`docs/roadmap_m00_m09/Bloco_2_Bootstrap.md`.\n")
    save(SHARED[1], audit_text)
    completed = datetime.now(timezone.utc).isoformat()
    for h in [24,6]:
        record = records[h]
        folder = record["folder"]
        paths = [p for p in folder.rglob("*") if p.is_file() and p.name != "auditoria_final.json"]
        paths += SHARED
        audit = {"schema":"renewcast-bloco2-existing-bootstrap-audit-v1", "item_id":record["item"],
            "completed":True, "exit_code":0, "started_at_utc":started, "completed_at_utc":completed,
            "command":[sys.executable,str(Path(__file__).resolve())],
            "versions":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__},
            "auditor_sha256":sha(__file__), "original_result_preserved_sha256":sha(folder/"resultado.json"),
            "prior_construction_tests_verified":59,"prior_tests_rerun":False,
            "existing_bootstrap_cli_runs_verified_total":4,"new_bootstrap_runs":0,
            "horizon_hours":h,"comparisons_verified":2,"summary_rows_verified":24,"prediction_rows":504,
            "checks":{"protocol_precedes_all_calls":True,"commands_and_zero_exits_match":True,
                "input_code_receipt_output_hashes_match":True,"source_absolute_errors_and_delta_match":True,
                "derived_persistence_alias_and_preserved_columns_match":True,"internal_clocks_and_hourly_grid_match":True,
                "all_summary_point_estimates_match":True,"n_weighted_fold_estimates_match":True,
                "all_three_prefixed_block_lengths_reported":True,"intervals_and_fractions_finite_and_ordered":True},
            "maximum_point_estimate_absolute_difference":record["maximum_point_estimate_difference"],
            "quantiles_independently_recomputed":False,"replicas_persisted_by_original_cli":False,
            "physical_timezone_verified":False,"new_holdout":False,"operational_approval":False,
            "independent_user_authorship_certified":False,"independent_human_review_claimed":False,
            "assistance":"Codex technical audit and interpretation; root integrates final engineering review.",
            "output_sha256":{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}}
        save(folder / "auditoria_final.json", json.dumps(audit,ensure_ascii=False,indent=2,allow_nan=False))
    print(json.dumps({"completed":True,"exit_code":0,"new_bootstrap_runs":0,
        "existing_cli_runs_verified":4,"generated_shared":[str(p.relative_to(ROOT)) for p in SHARED],
        "items":[{"id":r["item"],"summary_rows_verified":24,"maximum_difference":r["maximum_point_estimate_difference"]} for r in records.values()]},ensure_ascii=True))


if __name__ == "__main__":
    main()
