"""Seleção temporal nova M03, com preparação, ajuste e avaliação separados.

Executar --preparar ANTES de --ajustar. --avaliar apenas aplica o artefato
congelado ao parquet novo indicado; não escolhe modelos nem refaz ajuste.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
import time

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from bloco2_modelagem_core import FEATURES, GROUPS, RECENT, OLDER, STATS, CALENDAR
from bloco2_modelagem_core import build_frame, load_series, fit_mask, period_mask, sha256
from bloco2_modelagem_core import PersistenceRegressor

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet"
BASE = ROOT / "reports/fechamento_m00_m09/bloco2_engenharia"
OUT = BASE / "M03-03"
FINAL_CUT = "2026-07-01 00:00"
FOLDS = [("2026-06-01", "2026-06-08"), ("2026-06-08", "2026-06-15"),
         ("2026-06-15", "2026-06-22")]
CANDIDATES = [
    ("persistence", ["lag_1h"]), ("Ridge24", RECENT + OLDER),
    ("HGB_recent6", RECENT), ("HGB_lags24", RECENT + OLDER),
    ("HGB_stats", STATS), ("HGB_lags24_stats", RECENT + OLDER + STATS),
    ("HGB_lags24_calendar", RECENT + OLDER + CALENDAR), ("HGB_all", FEATURES),
]
HGB_PARAMS = dict(max_iter=60, max_leaf_nodes=15, min_samples_leaf=20,
                  learning_rate=0.05, l2_regularization=0.1,
                  early_stopping=False, random_state=17)


def now():
    return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT)).replace("\\", "/")


def metrics(y, pred):
    error = np.asarray(pred) - np.asarray(y)
    return dict(n=len(error), mae=float(np.abs(error).mean()),
                rmse=float(np.sqrt(np.square(error).mean())), bias=float(error.mean()))


def make_model(name):
    if name == "persistence":
        return PersistenceRegressor()
    if name == "Ridge24":
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    return HistGradientBoostingRegressor(**HGB_PARAMS)


def predict(model, frame, features):
    return frame["last_observed"].to_numpy() if model is None else model.predict(frame[features])


def code_manifest():
    paths = [Path(__file__), ROOT / "notebooks/bloco2_modelagem_core.py", ROOT / "notebooks/explicacao_local.py"]
    return {relative(p): sha256(p) for p in paths}


def prepare(source):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "protocolo.json"
    if path.exists():
        raise FileExistsError(f"Protocolo já existe; preservar histórico: {path}")
    protocol = {
        "created_at": now(), "scope": ["M03-01", "M03-02", "M03-03"],
        "authorship": "Implementação e análise fornecidas por Codex; sem certificação de autonomia do usuário.",
        "execution_kind": "Novo ajuste local sob contrato temporal novo; não é replay nem repetição de treino aceito.",
        "source": {"path": relative(source), "sha256": sha256(source)}, "code": code_manifest(),
        "dataset": "CJU_BA5EIGT", "clock": "UTC assumido para relógios ingênuos; fuso físico e latência ONS não certificados",
        "availability": {"last_observation": "origin-2h", "target": "y(origin+24h)",
                         "target_available": "origin+26h", "training_filter": "label_available_at < cutoff (strict)"},
        "feature_groups": GROUPS, "missing": "Grade horária, sem imputar zero; coorte comum de features e alvo finitos",
        "folds": FOLDS, "validation_origins_per_fold": 168,
        "training": "Expansivo; labels disponíveis estritamente antes do início da validação; scaler ajustado apenas no treino",
        "candidates": [{"name": name, "features": cols} for name, cols in CANDIDATES],
        "hgb": HGB_PARAMS, "ridge": {"alpha": 1.0, "preprocessing": "StandardScaler fit apenas treino"},
        "threads": 2, "selection": "Menor MAE agregado ponderado pelo número de origens; desempate n_features, ordem prévia",
        "baseline": "Persistência do último valor observado, origin-2h, alinhado à disponibilidade e às mesmas origens",
        "study_model": "Melhor aprendido, mesmo se persistência vencer; estudos não implicam promoção",
        "explanation": {"method": "Exact grouped interventional Shapley; enumeration of every coalition",
                        "origins": [f"2026-07-{d:02d} 12:00" for d in (1, 3, 5, 7, 10, 13)],
                        "background": "16 eligible training observations, uniform positions including endpoints",
                        "sensitivity": "8 eligible training observations, uniform positions including endpoints",
                        "maximum_groups": 4, "test": "Analytical linear model and sum(phi)+base=prediction",
                        "limits": "Correlated groups; hybrid out-of-distribution rows; background-sensitive; no physical causality"},
        "final_training_cut": FINAL_CUT,
        "calibration_scores": ["2026-07-01", "2026-07-14"],
        "policy_calibration": ["2026-07-16", "2026-07-31"],
        "evaluation": {"source": "Outubro 2026, obter e abrir apenas após seleção e calibradores congelados",
                       "origins_start_inclusive": "2026-10-02 01:00", "origins_end_exclusive": "2026-10-31 00:00",
                       "latest_target": "2026-10-31 23:00", "no_retuning": True},
        "prior_exposure": "Agosto 2026 já examinado em estudos h6/h1; setembro 2025–agosto 2026 é desenvolvimento, não holdout novo",
        "hypothesis": "Grupos adicionais podem melhorar a persistência na MAE; ganho não é condição de aceite de engenharia",
        "acceptance": ["Sem vazamento conforme testes de causalidade e purga", "Mesmas origens e oito candidatos executados",
                       "Seleção e artefato congelados antes de abrir outubro", "Explicações verificadas sem interpretação causal",
                       "Resultados negativos registrados; nenhuma aprovação operacional inferida"],
    }
    dump(path, protocol)
    for item in ["M03-01", "M03-02"]:
        dump(BASE / item / "protocolo.json", dict(protocol, scope=[item], selection_protocol=relative(path)))
    print(json.dumps({"prepared": relative(path), "sha256": sha256(path)}, ensure_ascii=False))


def fit(source):
    protocol_path = OUT / "protocolo.json"
    if not protocol_path.exists():
        raise RuntimeError("Executar --preparar antes do ajuste.")
    if (OUT / "point_bundle.joblib").exists():
        raise FileExistsError("Artefato já congelado; não sobrescrever uma seleção.")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if sha256(source) != protocol["source"]["sha256"] or code_manifest() != protocol["code"]:
        raise RuntimeError("Fonte ou código mudou após protocolo; registrar revisão antes do ajuste.")
    started = now()
    t0 = time.perf_counter()
    frame = build_frame(load_series(source))
    rows, preds, fold_audit = [], [], []
    with threadpool_limits(limits=2):
        for fold, (start, end) in enumerate(FOLDS, 1):
            train = frame.loc[fit_mask(frame, start)]
            val = frame.loc[period_mask(frame, start, end)]
            if len(val) != 168 or not train["label_available_at"].lt(pd.Timestamp(start)).all():
                raise AssertionError("Coorte ou purga diverge do protocolo.")
            fold_audit.append(dict(fold=fold, train_n=len(train), validation_n=len(val),
                                   train_origin_max=str(train.forecast_origin.max()),
                                   train_label_available_max=str(train.label_available_at.max()),
                                   validation_start=start, validation_end_exclusive=end))
            for order, (name, features) in enumerate(CANDIDATES):
                model = make_model(name)
                begin = time.perf_counter()
                if model is not None:
                    model.fit(train[features], train.y24)
                prediction = predict(model, val, features)
                rows.append(dict(candidate=name, order=order, fold=fold, n_features=len(features),
                                 fit_predict_seconds=time.perf_counter()-begin, **metrics(val.y24, prediction)))
                prediction_frame = val[["forecast_origin", "history_end", "target_time", "label_available_at", "y24", "last_observed"]].copy()
                prediction_frame["candidate"], prediction_frame["fold"] = name, fold
                prediction_frame["prediction"] = prediction
                preds.append(prediction_frame)
    fold_results = pd.DataFrame(rows)
    ranking = []
    for order, (name, features) in enumerate(CANDIDATES):
        data = fold_results.loc[fold_results.candidate.eq(name)]
        ranking.append(dict(candidate=name, order=order, n_features=len(features), n=int(data.n.sum()),
                            weighted_mae=float(np.average(data.mae, weights=data.n)),
                            weighted_rmse=float(np.sqrt(np.average(data.rmse**2, weights=data.n))),
                            weighted_bias=float(np.average(data.bias, weights=data.n)),
                            fit_predict_seconds=float(data.fit_predict_seconds.sum())))
    candidates = pd.DataFrame(ranking).sort_values(["weighted_mae", "n_features", "order"], kind="stable").reset_index(drop=True)
    selected = str(candidates.iloc[0].candidate)
    study = str(candidates.loc[candidates.candidate.ne("persistence")].iloc[0].candidate)
    training = frame.loc[fit_mask(frame, FINAL_CUT)]
    fitted = {}
    with threadpool_limits(limits=2):
        for name in dict.fromkeys([selected, study]):
            features = list(dict(CANDIDATES)[name])
            model = make_model(name)
            if model is not None:
                model.fit(training[features], training.y24)
            fitted[name] = (model, features)
    bundle = dict(model=fitted[selected][0], features=fitted[selected][1], selected_name=selected,
                  selected_candidate=selected, train_cutoff=FINAL_CUT,
                  study_model=fitted[study][0], study_features=fitted[study][1], study_name=study,
                  trained_cutoff=FINAL_CUT, training_n=len(training), protocol_sha256=sha256(protocol_path),
                  source_sha256=sha256(source), groups=GROUPS, frozen_at=now(), code=code_manifest())
    joblib.dump(bundle, OUT / "point_bundle.joblib")
    candidates.to_csv(OUT / "candidatos.csv", index=False)
    fold_results.to_csv(OUT / "folds.csv", index=False)
    pd.concat(preds, ignore_index=True).to_csv(OUT / "predicoes_folds.csv", index=False)
    cal = frame.loc[period_mask(frame, "2026-07-01", "2026-07-14")].copy()
    cal["prediction"] = predict(bundle["model"], cal, bundle["features"])
    cal["study_prediction"] = predict(bundle["study_model"], cal, bundle["study_features"])
    cal[["forecast_origin", "history_end", "target_time", "label_available_at", "y24", "last_observed", "prediction", "study_prediction"]].to_csv(OUT / "predicoes_cal.csv", index=False)
    manifest = dict(selected=selected, study_model=study, selected_features=bundle["features"], study_features=bundle["study_features"],
                    frozen_at=bundle["frozen_at"], final_training_cut=FINAL_CUT, training_n=len(training),
                    train_origin_max=str(training.forecast_origin.max()),
                    train_label_available_max=str(training.label_available_at.max()), folds=fold_audit,
                    calibration_n=len(cal), calibration_metrics=metrics(cal.y24, cal.prediction),
                    baseline_won=selected == "persistence", evaluation_opened=False,
                    bundle_sha256=sha256(OUT / "point_bundle.joblib"), protocol_sha256=sha256(protocol_path),
                    code=code_manifest(), source=protocol["source"],
                    versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, sklearn=sklearn.__version__))
    dump(OUT / "selection_manifest.json", manifest)
    outputs = {relative(p): sha256(p) for p in OUT.glob("*") if p.is_file() and p.name not in ["resultado.json", "ajuste_receipt.json"]}
    receipt = dict(started_at=started, completed_at=now(), elapsed_seconds=time.perf_counter()-t0,
                   command=sys.argv, execution="new_fit", manifest=manifest, outputs=outputs,
                   attribution="Codex implementou, executou e analisou; sem resposta independente do usuário")
    dump(OUT / "ajuste_receipt.json", receipt)
    dump(OUT / "resultado.json", receipt)
    write_defense(manifest, candidates)
    print(json.dumps(manifest, ensure_ascii=False, default=str))


def write_defense(manifest, candidates):
    winner = candidates.iloc[0]
    text = f"""# Defesa técnica M03-01 — seleção temporal

Responsável: Codex, implementação e análise assistidas em 25/11/2026. Esta solução é fornecida integralmente e não certifica autonomia pessoal.

O problema novo é prever geração MW em t+24h usando apenas história até t−2h. O alvo só está disponível em t+26h. Não basta dividir por origem: em cada fold removemos todos os rótulos com disponibilidade maior ou igual ao início da validação. O último rótulo de treino precede estritamente o corte; o ajuste final usa disponibilidade anterior a 01/07/2026. O scaler da Ridge é ajustado de novo exclusivamente no treino de cada fold. As três validações semanais de junho têm 168 origens cada, com treino expansivo e a mesma coorte para os oito candidatos.

A persistência é y(t−2h), último valor disponível no contrato. É um comparador simples, sem treino e sem custo de inferência significativo, mas não sabe antecipar mudanças. A MAE mede desvio absoluto em MW, alinhado ao custo simétrico linear desta seleção. RMSE e viés são diagnósticos adicionais; eventos com custos assimétricos são avaliados separadamente. Selecionar o melhor fold premiaria uma semana favorável: agregamos as 504 origens, ponderando cada fold por seu tamanho. Quantidade de features e ordem prévia resolvem empates.

O vencedor foi **{manifest['selected']}**, MAE de desenvolvimento **{winner.weighted_mae:.6f} MW**. O melhor aprendido foi **{manifest['study_model']}**. Se a persistência vencer, mantê-la como vencedora evita transformar o estudo explicativo do melhor aprendido em recomendação de promoção. Os grupos, hiperparâmetros, cortes e regra de seleção foram escritos antes do ajuste em `M03-03/protocolo.json`. Não houve busca no teste. O artefato e o ranking estão congelados; outubro continua fechado nesta fase.

Há dependência temporal, uma única série e sazonalidade. As semanas de junho não representam toda a variabilidade anual. Setembro/2025 a agosto/2026 é desenvolvimento já acessível; agosto já apareceu em estudos h6/h1 e não é holdout intocado. Fuso físico, latência efetiva e cadastro operacional permanecem hipóteses/limites; preencher uma grade horária com NaN e usar apenas coortes completas evita tratar falta como geração zero. Nenhum resultado desta análise autoriza produção.

Evidências: `M03-03/candidatos.csv`, `folds.csv`, `predicoes_folds.csv`, `selection_manifest.json` e `ajuste_receipt.json`. As novas execuções não substituem os runs históricos aceitos.
"""
    item = BASE / "M03-01"
    (item / "defesa_tecnica.md").write_text(text, encoding="utf-8")
    (item / "defesa.md").write_text(text, encoding="utf-8")
    (item / "parecer.md").write_text("# Parecer técnico M03-01\n\nCodex — 25/11/2026. Aprovada a construção e execução de engenharia da defesa: disponibilidade, purga estrita, treino/preprocessamento, seleção agregada, baseline e custo foram explicitados e sustentados pelas saídas. Autonomia pessoal e autorização operacional não foram avaliadas. Revisão integradora do agente principal é registrada separadamente.\n", encoding="utf-8")
    dump(item / "resultado.json", dict(completed_at=now(), execution="technical_analysis_of_new_fit", selection_manifest=manifest,
                                       outputs={relative(p): sha256(p) for p in item.glob("*.md")}))
    card = f"""# Model card — bloco 2, contrato de geração h24

Criado por Codex em 25/11/2026; estudo local de engenharia, sem homologação operacional.

**Uso e alvo.** CJU_BA5EIGT, geração em MW em origin+24h; dados disponíveis assumidos até origin−2h. Relógios interpretados como UTC por hipótese, sem prova do fuso físico/latência ONS. Somente uma série; não extrapolar a outras usinas.

**Modelo congelado.** {manifest['selected']}; melhor aprendido para estudos: {manifest['study_model']}. Artefato `reports/fechamento_m00_m09/bloco2_engenharia/M03-03/point_bundle.joblib`, SHA-256 `{manifest['bundle_sha256']}`. Ajuste com {manifest['training_n']} linhas, rótulos disponíveis estritamente antes de {FINAL_CUT}. Última disponibilidade no treino: {manifest['train_label_available_max']}.

**Features.** Lags 1–24 correspondem a origin−2h até origin−25h, médias/desvios populacionais de 6/24 horas, delta entre duas últimas observações, senos/cossenos da hora e dia da semana da origem. Grupos selecionados estão no manifesto. Grade horária mantém faltas como NaN; a coorte comum exclui linhas com qualquer feature/label indisponível. Ridge usa StandardScaler treinado apenas no treino. HGB tem 60 iterações, 15 folhas, folha mínima 20, taxa .05, L2 .1, sem early stopping, semente 17 e duas threads.

**Seleção e métricas.** Oito candidatos, três folds semanais expansivos em junho/2026, 504 previsões por candidato. Menor MAE ponderada, desempate por features/ordem; RMSE e viés adicionais em `candidatos.csv`. MAE vencedora: {winner.weighted_mae:.6f} MW. A calibração de intervalos/probabilidades e a política são etapas separadas; não se calibra no teste. Outubro/2026 é a avaliação reservada, a abrir após todos os congelamentos.

**Limites e decisão.** Junho orienta seleção, julho calibração. Agosto já foi visto historicamente; não é teste novo. A seleção pode perder da persistência e a comparação futura pode ser negativa. Explicações de Shapley descrevem o modelo sob um fundo escolhido, sem provar causalidade física. Sem meteorologia, contrafactuais físicos ou garantia sob mudança de regime. Não há evidência aqui de CI remoto, shadow contínuo, capacidade/custos operacionais ou disponibilidade real point-in-time. Aceite de engenharia não autoriza implantação.

**Linhas e reprodução.** Fonte preservada `dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet`; protocolo e receipts registram hashes/versões, origem dos dados e atribuição. `notebooks/selecao_atributos_temporal.py --preparar`, depois `--ajustar`; `--avaliar --evaluation-parquet CAMINHO` aplica somente o artefato congelado. Para nova rodada, preservar os arquivos anteriores em diretório próprio antes de preparar outro protocolo.
"""
    (ROOT / "docs/model_card.md").write_text(card, encoding="utf-8")


def evaluate(evaluation_source):
    if evaluation_source is None:
        raise ValueError("--evaluation-parquet é obrigatório ao avaliar.")
    manifest = json.loads((OUT / "selection_manifest.json").read_text(encoding="utf-8"))
    bundle_path = OUT / "point_bundle.joblib"
    if sha256(bundle_path) != manifest["bundle_sha256"]:
        raise RuntimeError("Artefato congelado diverge do manifesto.")
    if (OUT / "evaluation_receipt.json").exists():
        raise FileExistsError("Avaliação já registrada; preservar a primeira execução.")
    started = now()
    bundle = joblib.load(bundle_path)
    frame = build_frame(load_series(evaluation_source))
    data = frame.loc[period_mask(frame, "2026-10-02 01:00", "2026-10-31 00:00")].copy()
    if len(data) != 695:
        raise AssertionError(f"Avaliação precisa de 695 origens comuns completas, recebeu {len(data)}.")
    with threadpool_limits(limits=2):
        data["prediction"] = predict(bundle["model"], data, bundle["features"])
        data["study_prediction"] = predict(bundle["study_model"], data, bundle["study_features"])
    data[["forecast_origin", "history_end", "target_time", "label_available_at", "y24", "last_observed", "prediction", "study_prediction"]].to_csv(OUT / "predicoes_evaluation.csv", index=False)
    report = dict(started_at=started, completed_at=now(), execution="first_frozen_october_evaluation_no_refit",
                  source_path=str(evaluation_source), source_sha256=sha256(evaluation_source),
                  bundle_sha256=sha256(bundle_path), selected=manifest["selected"], study_model=manifest["study_model"],
                  selected_metrics=metrics(data.y24, data.prediction), study_metrics=metrics(data.y24, data.study_prediction),
                  persistence_metrics=metrics(data.y24, data.last_observed),
                  origin_min=str(data.forecast_origin.min()), origin_max=str(data.forecast_origin.max()),
                  target_max=str(data.target_time.max()), outputs={relative(OUT / "predicoes_evaluation.csv"): sha256(OUT / "predicoes_evaluation.csv")})
    dump(OUT / "evaluation_receipt.json", report)
    (OUT / "parecer.md").write_text(f"# Parecer M03-03 — seleção e avaliação congeladas\n\nCodex, 25/11/2026. Aprovada a entrega de engenharia: oito candidatos e grupos fixados antes do ajuste, coorte comum, três folds temporais com purga, baseline e custos computacionais registrados. Vencedor: {manifest['selected']}; estudo aprendido: {manifest['study_model']}.\n\nA avaliação nova de outubro aplicou o artefato congelado sem ajuste: MAE selecionado {report['selected_metrics']['mae']:.6f} MW, persistência {report['persistence_metrics']['mae']:.6f} MW e aprendido {report['study_metrics']['mae']:.6f} MW, {len(data)} origens. O ganho não era condição de aceite; qualquer piora é conservada. Acesso ao teste ocorreu depois dos congelamentos segundo o protocolo geral. Sem certificação de autonomia pessoal ou aprovação operacional; revisão integradora do agente principal separada.\n", encoding="utf-8")
    dump(OUT / "resultado.json", dict(adjustment_receipt=relative(OUT / "ajuste_receipt.json"),
                                      adjustment_sha256=sha256(OUT / "ajuste_receipt.json"), evaluation=report,
                                      review_sha256=sha256(OUT / "parecer.md")))
    with (ROOT / "docs/model_card.md").open("a", encoding="utf-8") as handle:
        handle.write(f"\n**Avaliação futura executada.** Outubro/2026, 695 origens: MAE selecionado {report['selected_metrics']['mae']:.6f} MW; aprendido {report['study_metrics']['mae']:.6f} MW; persistência {report['persistence_metrics']['mae']:.6f} MW. Artefato aplicado sem retreino/reseleção; detalhes e hashes em `M03-03/evaluation_receipt.json`.\n")
    print(json.dumps(report, ensure_ascii=False, default=str))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preparar", action="store_true")
    action.add_argument("--ajustar", action="store_true")
    action.add_argument("--avaliar", action="store_true")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--evaluation-parquet", type=Path)
    args = parser.parse_args()
    if args.preparar:
        prepare(args.source)
    elif args.ajustar:
        fit(args.source)
    else:
        evaluate(args.evaluation_parquet)


if __name__ == "__main__":
    main()
