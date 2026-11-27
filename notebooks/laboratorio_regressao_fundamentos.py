"""M02-04: OLS, Ridge, shapes, posto, gradiente e resíduos sintéticos."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from _fundamentos_evidencias import DEFAULT_OUTPUT, Execution, prepare_protocol, write_csv


def matriz_design(features):
    x = np.asarray(features, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or x.shape[0] < 2 or x.shape[1] < 1 or not np.isfinite(x).all():
        raise ValueError("Features precisam ser uma matriz finita (n,p), com n>=2 e p>=1.")
    return np.column_stack((np.ones(x.shape[0]), x))


def validar_design(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if (x.ndim != 2 or y.ndim != 1 or x.shape[0] != y.size
            or x.shape[0] < 2 or x.shape[1] < 1):
        raise ValueError("Exige X:(n,p) e y:(n,); y:(n,1) não é aceito.")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("X e y devem ser finitos.")
    if not np.allclose(x[:, 0], 1, rtol=0, atol=1e-14):
        raise ValueError("A primeira coluna do design deve conter o intercepto unitário.")
    return x, y


def objetivo_gradiente(x, y, beta, *, regularizacao=0.0):
    """J = ||y-Xb||²/n + lambda*sum(b[1:]²); intercepto não penalizado."""
    x, y = validar_design(x, y)
    beta = np.asarray(beta, dtype=float)
    if beta.shape != (x.shape[1],) or not np.isfinite(beta).all():
        raise ValueError("beta deve ter shape (p,) e valores finitos.")
    if not np.isfinite(regularizacao) or regularizacao < 0:
        raise ValueError("Regularização deve ser finita e não negativa.")
    error = x @ beta - y
    penalty_beta = beta.copy()
    penalty_beta[0] = 0
    objective = float(error @ error / y.size + regularizacao * (penalty_beta @ penalty_beta))
    gradient = 2 * (x.T @ error) / y.size + 2 * regularizacao * penalty_beta
    return objective, gradient


def ajustar_linear(x, y, *, regularizacao=0.0):
    """Use mínimos quadrados por SVD; evite inverter X.T@X explicitamente."""
    x, y = validar_design(x, y)
    if not np.isfinite(regularizacao) or regularizacao < 0:
        raise ValueError("Regularização deve ser finita e não negativa.")
    penalty = np.eye(x.shape[1])
    penalty[0, 0] = 0
    if regularizacao:
        augmented_x = np.vstack((x, np.sqrt(y.size * regularizacao) * penalty))
        augmented_y = np.concatenate((y, np.zeros(x.shape[1])))
    else:
        augmented_x, augmented_y = x, y
    beta, _, _, _ = np.linalg.lstsq(augmented_x, augmented_y, rcond=None)
    return beta


def diagnosticar_residuos(y, prediction):
    y, prediction = np.asarray(y, dtype=float), np.asarray(prediction, dtype=float)
    if y.ndim != 1 or prediction.shape != y.shape or y.size < 3:
        raise ValueError("Observação e previsão precisam ser vetores iguais, com ao menos três valores.")
    if not np.isfinite(y).all() or not np.isfinite(prediction).all():
        raise ValueError("Observação e previsão devem ser finitas.")
    residual = y - prediction
    denominator = float(residual @ residual)
    lag1 = None
    if residual[:-1].std() > 0 and residual[1:].std() > 0:
        lag1 = float(np.corrcoef(residual[:-1], residual[1:])[0, 1])
    return {"media_residuo": float(residual.mean()), "rmse": float(np.sqrt(np.mean(residual ** 2))),
            "autocorrelacao_lag1": lag1,
            "durbin_watson_descritivo": float(np.sum(np.diff(residual) ** 2) / denominator) if denominator else None}


def plano():
    return {
        "source": "Somente matriz manual e regressão sintética; sem dados dos benchmarks Renewcast.",
        "manual": {"x": [-1, 0, 1], "y": [1, 2, 4], "ridge_lambda": 1 / 3},
        "objective": "mean((y-X@beta)**2) + lambda*sum(beta[1:]**2)",
        "intercept_penalized": False,
        "seed": 2026112504, "bit_generator": "PCG64", "n": 240, "training_rows": 160,
        "generating_beta": [2.0, 3.0], "feature_distribution": "independent Normal(0,1)",
        "errors": {"type": "stationary_AR1", "rho": 0.8, "marginal_sigma": 1.0},
        "ridge_lambda": 0.1,
        "split": "First 160 rows fit; following 80 rows descriptive evaluation. Lambda is fixed, no search or model selection.",
        "assumptions": ["x independent of the error process by construction", "errors correlated in time, violating IID", "no causal identification or production claim"],
        "checks": ["manual OLS beta=(7/3,3/2)", "manual Ridge beta=(7/3,1)", "gradient matches central finite differences", "collinear design has rank 2 for 3 columns", "rank-deficient coefficients can differ without changing predictions", "inputs preserved"],
    }


def executar(protocol):
    execution = Execution(protocol)
    design = execution.plan["design"]
    x = matriz_design(design["manual"]["x"])
    y = np.array(design["manual"]["y"], dtype=float)
    originals = (x.copy(), y.copy())
    ols = ajustar_linear(x, y)
    ridge = ajustar_linear(x, y, regularizacao=design["manual"]["ridge_lambda"])
    point = np.array([0.3, -0.4])
    _, analytic = objetivo_gradiente(x, y, point, regularizacao=.3)
    h = 1e-6
    finite = np.empty_like(point)
    for j in range(point.size):
        increment = np.zeros_like(point)
        increment[j] = h
        plus, _ = objetivo_gradiente(x, y, point + increment, regularizacao=.3)
        minus, _ = objetivo_gradiente(x, y, point - increment, regularizacao=.3)
        finite[j] = (plus - minus) / (2 * h)
    deficient = matriz_design(np.column_stack((x[:, 1], 2 * x[:, 1])))
    beta_deficient = ajustar_linear(deficient, y)
    null_direction = np.array([0, 2, -1])
    max_prediction_difference = float(np.max(np.abs(deficient @ beta_deficient - deficient @ (beta_deficient + null_direction))))
    rng = np.random.Generator(np.random.PCG64(design["seed"]))
    feature = rng.normal(0, 1, design["n"])
    errors = np.empty(design["n"])
    error_design = design["errors"]
    errors[0] = rng.normal(0, error_design["marginal_sigma"])
    innovation_sigma = error_design["marginal_sigma"] * np.sqrt(1 - error_design["rho"] ** 2)
    for j in range(1, errors.size):
        errors[j] = error_design["rho"] * errors[j - 1] + rng.normal(0, innovation_sigma)
    full_x = matriz_design(feature)
    full_y = design["generating_beta"][0] + design["generating_beta"][1] * feature + errors
    cut = design["training_rows"]
    rows = []
    coefficients = {}
    for model, regularization in (("OLS", 0.0), ("Ridge", design["ridge_lambda"])):
        beta = ajustar_linear(full_x[:cut], full_y[:cut], regularizacao=regularization)
        coefficients[model] = beta.tolist()
        for partition, chosen in (("ajuste", slice(None, cut)), ("posterior_sintetico", slice(cut, None))):
            current_x, current_y = full_x[chosen], full_y[chosen]
            diagnostic = diagnosticar_residuos(current_y, current_x @ beta)
            rows.append({"modelo": model, "particao": partition, "n": int(current_y.size),
                         "p_com_intercepto": int(current_x.shape[1]), "posto_design": int(np.linalg.matrix_rank(current_x)),
                         "lambda": regularization, "intercepto": float(beta[0]), "coeficiente_x": float(beta[1]), **diagnostic})
    write_csv(execution.directory / "diagnosticos.csv", rows)
    statements = "\n".join(f"- {r['modelo']}/{r['particao']}: RMSE={r['rmse']:.6f}; média residual={r['media_residuo']:.6f}; correlação lag1={r['autocorrelacao_lag1']:.6f}." for r in rows)
    ols_objective, ols_gradient = objetivo_gradiente(x, y, ols)
    (execution.directory / "parecer.md").write_text(f"""# Parecer da demonstração M02-04

Responsável: Codex, construção e execução assistidas. Dados sintéticos e parâmetros fixados antes da execução.

Na conta manual, X tem shape (3,2), y (3,) e beta (2,). OLS devolveu [{ols[0]:.12f}, {ols[1]:.12f}], MSE={ols_objective:.12f}; o gradiente no mínimo tem norma {np.linalg.norm(ols_gradient):.3g}. Ridge com lambda=1/3 devolveu [{ridge[0]:.12f}, {ridge[1]:.12f}]. O intercepto não é penalizado. Para esta definição de perda, a equação normal contém n×lambda; omitir n muda o problema. O gradiente em um ponto fora do mínimo diferiu das diferenças finitas em no máximo {np.max(np.abs(analytic-finite)):.3g}.

Com colunas x e 2x, o design tem posto {np.linalg.matrix_rank(deficient)} para três parâmetros. Somar [0,2,−1] aos coeficientes não muda a previsão, com diferença máxima observada de {max_prediction_difference:.3g}. A solução de norma mínima retornada pela SVD é uma convenção, não identificação de efeitos separados. Ridge regulariza essa ambiguidade; não cria identificação causal.

Resultados do desenho temporal sintético, com ajuste nas primeiras 160 linhas e avaliação descritiva nas 80 seguintes:

{statements}

O gerador impõe erros AR(1) com rho=0,8 e x independente dos erros. A dependência aparece nos resíduos e invalida inferência que trate as 240 horas como observações IID. OLS pode manter ausência de viés dos coeficientes sob exogeneidade, mas a fórmula usual de erro-padrão IID não fica justificada. Não foram publicados p-valores ou intervalos ingênuos dos coeficientes. Média residual próxima de zero no ajuste com intercepto é uma propriedade algébrica; não comprova ausência de viés futuro. A coluna Durbin–Watson é descritiva, sem p-valor ou teste formal neste laboratório.

Nenhuma garantia de normalidade, homocedasticidade, exogeneidade ou causalidade é estabelecida apenas por um gráfico ou por RMSE. No caso real, investigar fonte, omissão de variáveis, dependência e mudança de regime é parte do contrato. Aqui não houve busca de lambda, treino de benchmark histórico nem decisão operacional.

Decisão: demonstração técnica executada. A prova nova e a revisão humana continuam pendentes; esta execução não valida autonomia.
""", encoding="utf-8")
    return execution.finish(
        {"manual_ols_beta": ols.tolist(), "manual_ridge_beta": ridge.tolist(),
         "manual_ols_mse": ols_objective, "finite_difference_max_error": float(np.max(np.abs(analytic-finite))),
         "rank_deficient_design_rank": int(np.linalg.matrix_rank(deficient)),
         "rank_deficient_design_columns": int(deficient.shape[1]), "null_direction_prediction_max_difference": max_prediction_difference,
         "synthetic_coefficients": coefficients, "diagnostics": rows},
        {"manual_ols": bool(np.allclose(ols, [7 / 3, 3 / 2], rtol=0, atol=1e-12)),
         "manual_ridge": bool(np.allclose(ridge, [7 / 3, 1], rtol=0, atol=1e-12)),
         "gradient_finite_difference": bool(np.allclose(analytic, finite, rtol=0, atol=1e-8)),
         "rank_deficiency_identified": int(np.linalg.matrix_rank(deficient)) == 2,
         "same_predictions_nonunique_coefficients": max_prediction_difference < 1e-12,
         "inputs_preserved": bool(np.array_equal(x, originals[0]) and np.array_equal(y, originals[1]))})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preparar", action="store_true", help="Grava somente o protocolo; não gera dados.")
    args = parser.parse_args(argv)
    protocol = prepare_protocol(args.output_root, "M02-04", plano())
    if args.preparar:
        print(f"M02-04: protocolo congelado em {protocol}")
        return 0
    executar(protocol)
    print("Demonstração concluída. Avaliação independente: aguarda resposta humana.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Fundamentos M02-04: {exc}") from None
