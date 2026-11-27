"""Shapley exato de grupos para o melhor modelo aprendido do bloco 2.

v(S) é a média de previsões em um fundo de treino com os grupos de S
substituídos pelos do exemplo. Não é explicação condicional nem causal.
"""
from __future__ import annotations

from datetime import datetime, timezone
import itertools
import json
import math
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from bloco2_modelagem_core import GROUPS, build_frame, load_series, fit_mask, sha256

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/fechamento_m00_m09/bloco2_engenharia"
SOURCE = ROOT / "dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet"
ORIGINS = [f"2026-07-{day:02d} 12:00" for day in (1, 3, 5, 7, 10, 13)]


def exact_group_shapley(predict, example: pd.Series, background: pd.DataFrame, groups):
    """Enumerate <=16 coalitions and return phi, base, prediction, all v(S).

    Group columns must partition the model input; all rows receive equal weight.
    Model calls are batched, so this also works for nonlinear regressors.
    """
    names = list(groups)
    if not 1 <= len(names) <= 4:
        raise ValueError("Este protocolo permite de um a quatro grupos.")
    columns = list(background.columns)
    flat = list(itertools.chain.from_iterable(groups.values()))
    if len(flat) != len(set(flat)) or set(flat) != set(columns):
        raise ValueError("Grupos devem particionar exatamente as features do modelo.")
    hybrids = []
    for mask in range(2 ** len(names)):
        hybrid = background.copy(deep=True)
        for j, name in enumerate(names):
            if mask & (1 << j):
                hybrid.loc[:, groups[name]] = example[groups[name]].to_numpy()
        hybrids.append(hybrid)
    values = np.asarray(predict(pd.concat(hybrids, ignore_index=True)), dtype=float).reshape(len(hybrids), len(background)).mean(axis=1)
    phi = {}
    m = len(names)
    for j, name in enumerate(names):
        contribution = 0.0
        for mask in range(2 ** m):
            if not mask & (1 << j):
                size = mask.bit_count()
                weight = math.factorial(size) * math.factorial(m-size-1) / math.factorial(m)
                contribution += weight * (values[mask | (1 << j)] - values[mask])
        phi[name] = float(contribution)
    prediction = float(np.asarray(predict(pd.DataFrame([example], columns=columns)))[0])
    if not np.isclose(values[0] + sum(phi.values()), prediction, atol=1e-8, rtol=1e-10):
        raise AssertionError("Aditividade exata do jogo de coalizões falhou.")
    return phi, float(values[0]), prediction, values


def main():
    out = BASE / "M03-02"
    protocol_path = out / "protocolo.json"
    if not protocol_path.exists():
        raise RuntimeError("Protocolo deve ser registrado antes do ajuste/explicação.")
    if (out / "resultado.json").exists():
        raise FileExistsError("Preservar explicação anterior; não sobrescrever.")
    started = datetime.now(timezone.utc).isoformat()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["source"]["sha256"] != sha256(SOURCE):
        raise RuntimeError("Fonte mudou após protocolo.")
    bundle_path = BASE / "M03-03/point_bundle.joblib"
    manifest = json.loads((BASE / "M03-03/selection_manifest.json").read_text(encoding="utf-8"))
    if manifest["bundle_sha256"] != sha256(bundle_path):
        raise RuntimeError("Artefato diverge do congelamento.")
    bundle = joblib.load(bundle_path)
    model, features = bundle["study_model"], bundle["study_features"]
    groups = {name: [column for column in cols if column in features] for name, cols in GROUPS.items()}
    groups = {name: cols for name, cols in groups.items() if cols}
    frame = build_frame(load_series(SOURCE))
    training = frame.loc[fit_mask(frame, "2026-07-01")]
    results, coalition_rows, background_hashes = [], [], {}
    with threadpool_limits(limits=2):
        for size in (16, 8):
            positions = np.linspace(0, len(training)-1, num=size, dtype=int)
            selected = training.iloc[positions]
            background = selected[features]
            path = out / ("fundo.csv" if size == 16 else "fundo_sensibilidade.csv")
            selected[["forecast_origin", "label_available_at"] + features].to_csv(path, index=False)
            background_hashes[path.name] = sha256(path)
            for origin in ORIGINS:
                example_frame = frame.loc[frame.forecast_origin.eq(pd.Timestamp(origin)), features]
                if len(example_frame) != 1 or not np.isfinite(example_frame).all().all():
                    raise AssertionError(f"Exemplo indisponível: {origin}")
                phi, base, prediction, values = exact_group_shapley(model.predict, example_frame.iloc[0], background, groups)
                residual = base + sum(phi.values()) - prediction
                for name, contribution in phi.items():
                    results.append(dict(forecast_origin=origin, background_n=size, model=bundle["study_name"],
                                        group=name, contribution_mw=contribution, base_mw=base, prediction_mw=prediction,
                                        additive_residual_mw=residual))
                for mask, value in enumerate(values):
                    coalition_rows.append(dict(forecast_origin=origin, background_n=size, mask=mask,
                                               groups="|".join(name for j, name in enumerate(groups) if mask & (1 << j)), value_mw=float(value)))
    data = pd.DataFrame(results)
    primary = data.loc[data.background_n.eq(16)]
    primary.to_csv(out / "explicacoes.csv", index=False)
    data.to_csv(out / "explicacoes_fundos.csv", index=False)
    pd.DataFrame(coalition_rows).to_csv(out / "coalizoes.csv", index=False)
    sensitivity = primary.merge(data.loc[data.background_n.eq(8)], on=["forecast_origin", "group", "model"], suffixes=("_16", "_8"))
    sensitivity["delta_contribution_mw"] = sensitivity.contribution_mw_8 - sensitivity.contribution_mw_16
    sensitivity["sign_changed"] = np.sign(sensitivity.contribution_mw_8).ne(np.sign(sensitivity.contribution_mw_16))
    sensitivity.to_csv(out / "sensibilidade.csv", index=False)
    max_residual = float(data.additive_residual_mw.abs().max())
    max_change = float(sensitivity.delta_contribution_mw.abs().max())
    signs = int(sensitivity.sign_changed.sum())
    summary = primary.loc[primary.groupby("forecast_origin").contribution_mw.apply(lambda x: x.abs().idxmax()).to_numpy(), ["forecast_origin", "group", "contribution_mw"]]
    lines = "\n".join(f"- {row.forecast_origin}: grupo {row.group}, contribuição {row.contribution_mw:.6f} MW." for row in summary.itertuples())
    review = f"""# Parecer M03-02 — explicação local por Shapley de grupos

Codex, 25/11/2026. Aprovada a entrega de engenharia: método compatível com `{bundle['study_name']}`, seis origens de julho e fundos de treino predefinidos, enumeração exata de {2**len(groups)} coalizões por exemplo/fundo e teste analítico linear. O modelo explicado é o melhor aprendido; isto não o promove sobre a persistência.

O jogo usa v(S)=média das previsões em linhas do fundo de treino nas quais os grupos presentes são substituídos pelos do exemplo. O fundo principal tem 16 linhas uniformemente espaçadas no treino elegível, com rótulos disponíveis antes de 01/07; a sensibilidade repete com oito linhas. Não houve amostragem de coalizões nem dependência de instalação SHAP. Os grupos particionam somente as features efetivamente usadas. Assim, a exatidão refere-se a esse jogo interventional finito, sem alegar os valores de outra definição SHAP.

O maior resíduo de aditividade |base+Σphi−previsão| foi {max_residual:.3g} MW. Os grupos de maior contribuição absoluta foram:

{lines}

A troca de fundo alterou a contribuição em até {max_change:.6f} MW e mudou {signs} sinais entre {len(sensitivity)} atribuições. Essa sensibilidade é registrada, sem escolher apenas exemplos estáveis. A diferença entre exemplos descreve a resposta do estimador às histórias disponíveis; não mede um efeito físico do grupo. Grupos ausentes do modelo não recebem importância zero como conclusão científica: simplesmente não fazem parte do jogo.

Lags e estatísticas são fortemente dependentes. Substituir grupos independentemente produz combinações híbridas que podem sair da distribuição real; médias e desvios podem ficar incoerentes com lags. O fundo influencia base e contribuições, e um grupo correlacionado pode dividir/absorver informação de outro. A soma exata não elimina esses limites. Não há intervenção na geração, meteorologia ou causalidade física; as atribuições são do modelo e do jogo escolhido. Sem autorização de produção e sem certificação de autonomia pessoal; revisão integradora do agente principal separada.
"""
    (out / "parecer.md").write_text(review, encoding="utf-8")
    outputs = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in out.glob("*") if p.is_file() and p.name != "resultado.json"}
    receipt = dict(started_at=started, completed_at=datetime.now(timezone.utc).isoformat(), execution="new_exact_group_shapley",
                   model=bundle["study_name"], selected_candidate=bundle["selected_name"], bundle_sha256=sha256(bundle_path),
                   source_sha256=sha256(SOURCE), code_sha256=sha256(__file__), protocol_sha256=sha256(protocol_path),
                   origins=ORIGINS, backgrounds=background_hashes, groups=groups, coalitions_per_example=2**len(groups),
                   max_additivity_error_mw=max_residual, max_background_change_mw=max_change, sign_changes=signs,
                   command=sys.argv, outputs=outputs, attribution="Codex implementou, executou e analisou; sem resposta independente do usuário")
    (out / "resultado.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ["model", "max_additivity_error_mw", "max_background_change_mw", "sign_changes"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
