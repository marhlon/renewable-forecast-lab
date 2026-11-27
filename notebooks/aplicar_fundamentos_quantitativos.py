"""Resolva os casos M02-01–04 como aplicação técnica assistida.

Preserva as demonstrações anteriores. --preparar grava os protocolos antes de
calcular; a execução normal também os grava antes de chamar os calculadores.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys

import numpy as np
from scipy.stats import t

from laboratorio_probabilidade import (
    intervalos_normais, probabilidade_positiva, tamanho_efetivo_ar1,
    teste_melhoria_blocos,
)
from laboratorio_regressao_fundamentos import (
    ajustar_linear, matriz_design, objetivo_gradiente,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports/fechamento_m00_m09/bloco1_engenharia"
DOCUMENT = ROOT / "docs/roadmap_m00_m09/Fundamentos_Aplicados_Resultados.md"
SOURCES = (
    "notebooks/aplicar_fundamentos_quantitativos.py",
    "notebooks/laboratorio_probabilidade.py",
    "notebooks/laboratorio_regressao_fundamentos.py",
    "notebooks/_fundamentos_evidencias.py",
    "docs/roadmap_m00_m09/Avaliacao_Fundamentos.md",
    "tests/test_fundamentos_aplicados.py",
)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def dump(path, content):
    Path(path).write_text(json.dumps(content, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def path_label(path):
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(Path(path).resolve())


def plans():
    common = {
        "synthetic_or_didactic_inputs_only": True,
        "randomness": "Nenhuma; casos fixos fornecidos na atividade, sem simulação ou seleção de semente.",
        "purpose": "Aplicação técnica assistida solicitada pelo usuário; não é prova de autoria independente.",
        "human_response_required": False,
        "learning_evaluation": "não avaliada",
        "benchmarks_retrained": False,
        "tolerances": {"analytic_numeric": 1e-12, "rounded_t_interval": 1e-6},
    }
    return {
        "M02-01": {**common, "inputs": {"n": 20000, "prevalence": 0.02, "sensitivity": 0.85, "false_positive_rate": 0.03},
                   "method": "Tabela de contingência construída e Bayes; comparação com frações exatas.",
                   "checks": ["totais de linhas e colunas", "posterior igual ao cálculo racional", "condição de sensibilidade distinta da condição do posterior"]},
        "M02-02": {**common, "inputs": {"sample": [18, 20, 22, 24], "confidence": 0.95, "t_given": 3.182446, "ar1_n": 72, "ar1_rho": 0.6},
                   "method": "Média, s², IC da média e PI de uma observação sob Normal IID; n_eff AR1 como cenário separado de covariância conhecida.",
                   "checks": ["média e variância por fração exata", "IC e PI com t arredondado versus SciPy", "PI/IC = sqrt(n+1)", "n_eff AR1 contra soma racional finita"]},
        "M02-03": {**common, "inputs": {"block_means": [0.2, 1.4, 0.9, 1.8, 1.2, 1.0], "minimum_effect": 0.5, "alpha": 0.05, "t_given": 2.015048,
                                        "separate_family_p_values": [0.009, 0.03, 0.4], "separate_family_alpha": 0.05},
                   "method": "Teste t unilateral sobre as seis médias de blocos já fornecidas; Bonferroni em outra família de três p-valores fornecidos, sem confundir as duas perguntas.",
                   "assumptions": ["As seis médias de blocos são independentes e normais, conforme a hipótese da questão.", "As 144 horas originais não foram fornecidas e não serão fabricadas.", "Os três p-valores da família separada são assumidos individualmente válidos."],
                   "checks": ["média e s² por soma racional", "limite inferior com t dado versus SciPy", "decisão p e intervalo coerentes", "Bonferroni divide alpha por três"]},
        "M02-04": {**common, "inputs": {"x": [-2, 0, 2], "y": [0, 1, 5], "ridge_lambda_fraction": "1/3", "initial_beta": [0, 0], "demonstration_step_rates": [0.1, 1.0]},
                   "method": "OLS/Ridge por SVD e conferência por equações normais/frações; um passo de gradiente e limite teórico de estabilidade, sem treino iterativo de benchmark.",
                   "checks": ["XTX e XTy manuais", "OLS e Ridge contra frações exatas", "gradiente inicial e seu sinal", "n_lambda na equação normal", "posto e direção nula", "taxa pequena reduz perda e taxa grande pode aumentá-la", "entradas preservadas"]},
    }


def prepare(output_root):
    protocols = {}
    source_hashes = {name: sha(ROOT / name) for name in SOURCES}
    prior_paths = set()
    for item in SOLVERS:
        old_directory = ROOT / "reports/fechamento_m00_m09" / item
        if old_directory.is_dir():
            prior_paths.update(path for path in old_directory.iterdir() if path.is_file())
    prior_paths.update(ROOT / name for name in (
        "docs/roadmap_m00_m09/Fundamentos_Quantitativos.md",
        "tests/test_fundamentos_quantitativos.py",
    ) if (ROOT / name).is_file())
    prior_hashes = {path_label(path): sha(path) for path in sorted(prior_paths)}
    for item, design in plans().items():
        directory = Path(output_root).resolve() / item
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "protocolo.json"
        content = {"schema": "m02-aplicacao-tecnica-protocol-v1", "item": item, "design": design, "source_sha256": source_hashes,
                   "preserved_prior_artifacts_sha256": prior_hashes}
        if path.exists():
            previous = json.loads(path.read_text(encoding="utf-8"))
            if {key: value for key, value in previous.items() if key != "frozen_at_utc"} != content:
                raise ValueError(f"O protocolo existente difere do desenho/código: {path}. Use outro --output-root.")
        else:
            if any(directory.iterdir()):
                raise ValueError(f"Pasta não vazia sem protocolo: {directory}.")
            content["frozen_at_utc"] = now()
            with path.open("x", encoding="utf-8") as handle:
                json.dump(content, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.write("\n")
        protocols[item] = path
    return protocols


def solve_probability(inputs):
    n = inputs["n"]
    event = n * inputs["prevalence"]
    tp = event * inputs["sensitivity"]
    fn = event - tp
    fp = (n - event) * inputs["false_positive_rate"]
    tn = n - event - fp
    ppv = probabilidade_positiva(inputs["prevalence"], inputs["sensitivity"], inputs["false_positive_rate"])
    rows = [
        {"sinal": "positivo", "evento": tp, "sem_evento": fp, "total": tp + fp},
        {"sinal": "negativo", "evento": fn, "sem_evento": tn, "total": fn + tn},
        {"sinal": "total", "evento": event, "sem_evento": n - event, "total": n},
    ]
    checks = {
        "counts_manual": bool(np.allclose([tp, fn, fp, tn], [340, 60, 588, 19012], rtol=0, atol=1e-12)),
        "total_preserved": bool(tp + fn + fp + tn == n),
        "posterior_rational": bool(np.isclose(ppv, float(Fraction(85, 232)), rtol=0, atol=1e-12)),
        "conditional_probabilities_distinguished": bool(np.isclose(tp / (tp + fn), inputs["sensitivity"]) and not np.isclose(ppv, inputs["sensitivity"])),
    }
    result = {"n": n, "event_count": event, "non_event_count": n - event, "true_positive": tp, "false_negative": fn,
              "false_positive": fp, "true_negative": tn, "positive_total": tp + fp, "negative_total": fn + tn,
              "event_given_positive": ppv, "positive_given_event": inputs["sensitivity"]}
    solution = f"""## M02-01 — taxa-base, unidade e distribuição

### Conta executada

Das {n:,} oportunidades didáticas, 2% correspondem a 400 eventos e 19.600 a situações sem evento. A sensibilidade de 85% produz 340 positivos entre os eventos e 60 negativos. A taxa de falso positivo de 3% produz 588 positivos entre os 19.600 sem evento; restam 19.012 negativos.

| Sinal | Evento | Sem evento | Total |
| --- | ---: | ---: | ---: |
| Positivo | 340 | 588 | 928 |
| Negativo | 60 | 19.012 | 19.072 |
| Total | 400 | 19.600 | 20.000 |

```text
P(evento | positivo) = 340 / 928 = 85 / 232
                    = {ppv:.12f} = {100*ppv:.6f}%
P(positivo | evento) = 340 / 400 = 85%
```

A primeira condição pergunta quantos positivos são eventos; a segunda pergunta quantos eventos geram um positivo. A taxa-base de 2% afeta a primeira. Sensibilidade alta não impede que a maioria dos positivos seja falsa quando o evento é raro e o falso positivo incide sobre uma população maior.

### As oito horas não são oito eventos independentes

Se uma mesma ocorrência dura oito horas, seus indicadores horários compartilham informação e duração. Não se justifica uma Binomial(24,p) apenas porque há 24 linhas: seriam necessários ensaios independentes e p constante. A unidade pode ser uma hora positiva ou o início de um episódio; são alvos diferentes. Para avaliar episódios, é preciso identificar início, fim, exposição observável e regra de agrupamento, preservando a informação temporal. Não foi estimada aqui uma probabilidade operacional de um detector real.

### Distribuições e condições de rejeição

Um indicador isolado 0/1 pode ser descrito marginalmente por Bernoulli(p); isso não torna a sequência IID nem mantém p estável entre regimes. Uma contagem por exposição fixa pode motivar Poisson(λ), se a taxa e os incrementos independentes forem defensáveis; agrupamento de episódios ou sobredispersão pode invalidar essa forma simples. Um erro contínuo pode motivar Normal(μ,σ²), mas assimetria forte, caudas pesadas ou variância que muda com o estado exigiriam outra avaliação. Se o objeto for geração não negativa, o suporte negativo da normal é outro ponto a examinar.

### População, amostra e outro ano

Os 20.000 casos e seus totais são uma tabela construída a partir das porcentagens fornecidas, não 20.000 medições coletadas pelo programa. Numa amostra real, as contagens flutuariam e a inclusão/ausência de dados precisaria ser descrita. A população-alvo deve definir período, equipamentos e unidade. Uma prevalência de outro ano pode não se transferir; sensibilidade e taxa de falso positivo também podem mudar. Inserir uma taxa-base antiga na fórmula não comprova disponibilidade, calibração ou validade operacional atuais.
"""
    return result, checks, {"contingencia.csv": rows}, solution


def solve_estimation(inputs):
    sample = np.array(inputs["sample"], dtype=float)
    stats = intervalos_normais(sample, inputs["confidence"])
    mean = float(sample.mean())
    variance = float(sample.var(ddof=1))
    se = float(np.sqrt(variance / sample.size))
    given = inputs["t_given"]
    ci = [mean - given * se, mean + given * se]
    pi_half = given * float(np.sqrt(variance * (1 + 1 / sample.size)))
    pi = [mean - pi_half, mean + pi_half]
    n, rho = inputs["ar1_n"], inputs["ar1_rho"]
    approximate = n * (1 - rho) / (1 + rho)
    exact = tamanho_efetivo_ar1(n, rho)
    rational_covariance_sum = Fraction(n) + 2 * sum(Fraction(n-lag) * Fraction(3, 5)**lag for lag in range(1, n))
    exact_rational = float(Fraction(n*n) / rational_covariance_sum)
    result = {"n": int(sample.size), "mean": mean, "sample_variance": variance, "standard_error": se,
              "t_given": given, "t_scipy": stats["t_critico"], "mean_ci_using_given_t": ci,
              "prediction_interval_using_given_t": pi, "mean_ci_using_scipy_t": [stats["ic_media_inferior"], stats["ic_media_superior"]],
              "prediction_interval_using_scipy_t": [stats["pi_observacao_inferior"], stats["pi_observacao_superior"]],
              "separate_ar1_scenario": {"n": n, "rho": rho, "n_eff_approximate": approximate, "n_eff_finite_exact": exact}}
    rows = [{"medida": key, "valor": value} for key, value in (
        ("media", mean), ("variancia_amostral", variance), ("erro_padrao", se), ("t_dado", given), ("t_scipy", stats["t_critico"]),
        ("ic_media_inferior_t_dado", ci[0]), ("ic_media_superior_t_dado", ci[1]),
        ("pi_observacao_inferior_t_dado", pi[0]), ("pi_observacao_superior_t_dado", pi[1]),
        ("n_eff_ar1_aproximado", approximate), ("n_eff_ar1_finito_exato", exact))]
    checks = {
        "mean_variance_rational": bool(np.allclose([mean, variance], [21, float(Fraction(20, 3))], rtol=0, atol=1e-12)),
        "given_t_and_scipy_intervals_agree_to_rounding": bool(np.allclose(ci + pi, result["mean_ci_using_scipy_t"] + result["prediction_interval_using_scipy_t"], rtol=0, atol=1e-6)),
        "prediction_interval_width": bool(np.isclose((pi[1] - pi[0]) / (ci[1] - ci[0]), np.sqrt(5), rtol=0, atol=1e-12)),
        "effective_sample_size_rational": bool(np.isclose(exact, exact_rational, rtol=0, atol=1e-12)),
        "effective_sample_size_approximate": bool(np.isclose(approximate, 18, rtol=0, atol=1e-12)),
    }
    solution = f"""## M02-02 — média, variância, IC e previsão

### Derivação com os quatro valores

O estimando é a média populacional μ da variável e população definidas. O estimador é a média amostral; sua realização é 21. Para `[18,20,22,24]`, os desvios são `[−3,−1,1,3]`, cuja soma dos quadrados é 20.

```text
n = 4; soma(x) = 84; média = 84/4 = 21
s² = 20/(4−1) = 20/3 = {variance:.12f}
SE(média) = sqrt(s²/n) = sqrt(5/3) = {se:.12f}
```

Sob Normal IID com variância desconhecida, há três graus de liberdade. Usando o t arredondado fornecido, {given:.6f}:

```text
IC95% da média = 21 ± t × sqrt(5/3)
               = [{ci[0]:.12f}, {ci[1]:.12f}]
PI95% de UMA nova observação independente da mesma população
               = 21 ± t × sqrt((20/3) × (1+1/4))
               = [{pi[0]:.12f}, {pi[1]:.12f}]
```

SciPy retornou t={stats['t_critico']:.12f}. O resultado preserva os dois cálculos: a diferença dos limites fica abaixo de 10⁻⁶ e decorre apenas do arredondamento fornecido. O PI é √5 vezes mais largo: ele inclui tanto a incerteza da média quanto a dispersão da observação futura. O IC não é um intervalo que deva conter 95% dos valores individuais.

### Dependência e tamanho efetivo

Se as leituras forem AR(1), deixa de valer a hipótese de independência usada pelo IC t simples. Para o cenário separado n=72 e ρ=0,6, a aproximação de série longa dá:

```text
n_eff aproximado = 72 × (1−0,6)/(1+0,6) = {approximate:.12f}
n_eff finito exato para a variância da média de AR(1) estacionário
                = n² / [n + 2 soma((n−h)ρ^h)]
                = {exact:.12f}
```

A soma finita foi conferida também com aritmética racional. Os dois números diferem porque a aproximação ignora o efeito de borda. São específicos da média e de uma covariância AR(1) conhecida: não são n_eff universais nem licença para trocar n por 18 e inventar automaticamente novos graus de liberdade t. Não há 72 observações novas fornecidas neste exercício; o programa calculou a expressão da covariância, sem fabricar uma série ou afirmar cobertura empírica.

### Interpretação frequentista

μ é fixo nesse enquadramento, e o intervalo varia entre amostras. A afirmação correta é que o procedimento cobre μ em 95% das repetições sob o desenho e os pressupostos declarados. A frase “há 95% de probabilidade de o parâmetro estar neste intervalo observado” exigiria outro enquadramento probabilístico, como uma análise bayesiana com seus próprios pressupostos. A precisão aritmética desta conta não valida normalidade, independência ou representatividade em dados reais.
"""
    return result, checks, {"estimativas.csv": rows}, solution


def solve_hypotheses(inputs):
    blocks = np.array(inputs["block_means"], dtype=float)
    test = teste_melhoria_blocos(blocks, tamanho_bloco=1, efeito_minimo=inputs["minimum_effect"], alpha=inputs["alpha"])
    sample_variance = float(blocks.var(ddof=1))
    se = test["erro_padrao_blocos"]
    lower_given = test["media_diferenca"] - inputs["t_given"] * se
    q_scipy = float(t.ppf(1 - inputs["alpha"], blocks.size - 1))
    p_values = inputs["separate_family_p_values"]
    adjusted_alpha = inputs["separate_family_alpha"] / len(p_values)
    rejected = [bool(p < adjusted_alpha) for p in p_values]
    result = {"block_count": int(blocks.size), "mean_difference": test["media_diferenca"], "sample_variance_between_blocks": sample_variance,
              "standard_error_between_blocks": se, "minimum_effect": inputs["minimum_effect"], "t_statistic": test["t"],
              "degrees_freedom": int(blocks.size - 1), "p_one_sided": test["p_unilateral"], "alpha_nominal": inputs["alpha"],
              "lower_bound_given_t": lower_given, "lower_bound_scipy_t": test["limite_inferior_unilateral"],
              "t_given": inputs["t_given"], "t_scipy": q_scipy, "reject_h0_nominal": test["rejeita_h0"],
              "separate_family": {"p_values": p_values, "alpha_family": inputs["separate_family_alpha"], "alpha_per_test": adjusted_alpha, "rejected": rejected},
              "original_hourly_series_supplied": False, "hourly_series_fabricated": False}
    rows = [{"pergunta": "seis_medias_de_blocos", "teste": "H0_mu_menor_igual_0_5", "p": test["p_unilateral"], "alpha": inputs["alpha"], "rejeita": test["rejeita_h0"]}]
    rows += [{"pergunta": "outra_familia_bonferroni", "teste": f"H{i+1}", "p": p, "alpha": adjusted_alpha, "rejeita": rejected[i]} for i, p in enumerate(p_values)]
    checks = {
        "block_mean_variance_rational": bool(np.allclose([test["media_diferenca"], sample_variance], [float(Fraction(13, 12)), float(Fraction(869, 3000))], rtol=0, atol=1e-12)),
        "given_t_and_scipy_bound_agree": bool(np.isclose(lower_given, test["limite_inferior_unilateral"], rtol=0, atol=1e-6)),
        "p_and_bound_decision_agree": test["rejeita_h0"] == (lower_given > inputs["minimum_effect"]),
        "bonferroni_alpha_rational": bool(np.isclose(adjusted_alpha, float(Fraction(1, 60)), rtol=0, atol=1e-12)),
        "separate_family_decisions": rejected == [True, False, False],
    }
    solution = f"""## M02-03 — efeito relevante, blocos e multiplicidade

### Teste sobre as seis médias fornecidas

O ganho é `perda_A−perda_B`: positivo favorece B. O alvo é μ_d, sua média populacional. O efeito mínimo relevante foi fixado em 0,5; portanto H0: μ_d≤0,5 e H1: μ_d>0,5. Os números `[0.2,1.4,0.9,1.8,1.2,1.0]` já são **médias de seis blocos independentes**, não seis horas selecionadas de uma série.

```text
soma(d) = 6,5
média = 13/12 = {test['media_diferenca']:.12f}
s² entre blocos = 869/3000 = {sample_variance:.12f}
SE = sqrt(s²/6) = {se:.12f}
t = (média−0,5)/SE = {test['t']:.12f}; graus de liberdade = 5
p unilateral = {test['p_unilateral']:.12f}
limite inferior95%, usando t dado=2,015048
             = {lower_given:.12f}
```

O t exato da biblioteca foi {q_scipy:.12f}; o limite correspondente é {test['limite_inferior_unilateral']:.12f}. A diferença está dentro do arredondamento previsto. O limite inferior é maior que 0,5 e o p é menor que 0,05; **rejeitamos H0 no teste nominal especificado**, sob normalidade e independência dessas médias. Há evidência, nesse desenho, de ganho médio superior ao mínimo relevante. Não se demonstrou superioridade de um modelo Renewcast real, causalidade ou transferência para outro período.

### Por que não usar automaticamente as 144 horas

Para o teste t IID aplicado a 144 valores, seria necessário justificar independência e a distribuição/condições apropriadas desses valores. Horas do mesmo bloco podem compartilhar estado, regime ou erro; a contagem de linhas não é uma justificativa. A alternativa é tratar a estrutura de covariância ou manter uma unidade de inferência adequada, como as médias de blocos independentes assumidas na questão. Como as 144 observações originais não foram fornecidas, não foram replicadas artificialmente as médias para produzir uma falsa série horária nem calculado um teste “horário” sem dados.

### Outra família de três hipóteses

Esta é uma pergunta separada: os p-valores fornecidos são 0,009; 0,03; 0,4. Com alpha familiar de 5% e três testes, Bonferroni fixa `0,05/3 = {adjusted_alpha:.12f}` por teste. **Somente H1, com p=0,009, passa**. H2 e H3 não passam. A família e o denominador são três; não se escolhe apenas o menor p e depois se declara que só houve um teste. Não é necessário assumir independência entre os três para o limite Bonferroni, mas os p-valores individuais precisam ser válidos.

O teste das seis médias e essa família de p-valores foram mantidos distintos porque o enunciado diz “em outra família”. Nenhum p-valor adicional foi inventado para completar uma comparação.

### Não rejeição e equivalência

Não rejeitar H0 não demonstra equivalência: pode refletir pouca precisão ou baixa potência. Uma pergunta de equivalência exige margem inferior/superior relevante, hipóteses próprias e um procedimento como dois testes unilaterais ou intervalo compatível, escolhidos antes do resultado. Também exige unidade, exposição e dependência apropriadas. O p-valor não é P(H0|dados), e significância não corrige um desenho inválido.
"""
    return result, checks, {"comparacao.csv": rows}, solution


def solve_regression(inputs):
    x = matriz_design(inputs["x"])
    y = np.array(inputs["y"], dtype=float)
    originals = (x.copy(), y.copy())
    regularization = float(Fraction(inputs["ridge_lambda_fraction"]))
    ols = ajustar_linear(x, y)
    ridge = ajustar_linear(x, y, regularizacao=regularization)
    beta0 = np.array(inputs["initial_beta"], dtype=float)
    initial_loss, gradient = objetivo_gradiente(x, y, beta0)
    penalty_matrix = np.diag([0., 1.])
    xtx, xty = x.T @ x, x.T @ y
    ridge_normal = xtx + y.size * regularization * penalty_matrix
    hessian_ols = 2 * xtx / y.size
    hessian_ridge = hessian_ols + 2 * regularization * penalty_matrix
    maximum_rate_ols = float(2 / np.linalg.eigvalsh(hessian_ols).max())
    maximum_rate_ridge = float(2 / np.linalg.eigvalsh(hessian_ridge).max())
    steps = []
    for rate in inputs["demonstration_step_rates"]:
        beta_after = beta0 - rate * gradient
        loss_after, _ = objetivo_gradiente(x, y, beta_after)
        steps.append({"rate": rate, "beta_after_one_step": beta_after.tolist(), "mse_after_one_step": loss_after})
    deficient = matriz_design(np.column_stack((x[:, 1], 2 * x[:, 1])))
    beta_deficient = ajustar_linear(deficient, y)
    null = np.array([0., 2., -1.])
    prediction_difference = float(np.max(np.abs(deficient @ beta_deficient - deficient @ (beta_deficient + null))))
    ols_mse, _ = objetivo_gradiente(x, y, ols)
    ridge_mse, _ = objetivo_gradiente(x, y, ridge)
    ridge_j, _ = objetivo_gradiente(x, y, ridge, regularizacao=regularization)
    ols_j, _ = objetivo_gradiente(x, y, ols, regularizacao=regularization)
    rows = [{"x": float(row[1]), "observado": float(observed), "previsao_ols": float(p0), "residuo_ols": float(observed-p0), "previsao_ridge": float(p1), "residuo_ridge": float(observed-p1)}
            for row, observed, p0, p1 in zip(x, y, x @ ols, x @ ridge)]
    result = {"shapes": {"X": list(x.shape), "y": list(y.shape), "beta": list(ols.shape), "prediction": list((x @ ols).shape)},
              "xtx": xtx.tolist(), "xty": xty.tolist(), "ols_beta": ols.tolist(), "ridge_beta": ridge.tolist(),
              "lambda": regularization, "n_lambda": float(y.size * regularization), "ridge_normal_matrix": ridge_normal.tolist(),
              "initial_gradient": gradient.tolist(), "initial_mse": initial_loss, "one_step_demonstrations": steps,
              "stable_rate_upper_bound_ols": maximum_rate_ols, "stable_rate_upper_bound_ridge": maximum_rate_ridge,
              "ols_mse": ols_mse, "ridge_mse": ridge_mse, "ols_objective_at_common_ridge_lambda": ols_j,
              "ridge_objective_at_common_ridge_lambda": ridge_j, "deficient_rank": int(np.linalg.matrix_rank(deficient)),
              "deficient_columns": int(deficient.shape[1]), "minimum_norm_beta_deficient": beta_deficient.tolist(),
              "null_direction": null.tolist(), "null_direction_prediction_max_difference": prediction_difference,
              "future_observations_supplied": False, "future_autocorrelation_measured": False}
    checks = {
        "manual_normal_equations": bool(np.allclose(xtx, [[3, 0], [0, 8]], rtol=0, atol=1e-12) and np.allclose(xty, [6, 10], rtol=0, atol=1e-12)),
        "ols_rational": bool(np.allclose(ols, [2, float(Fraction(5, 4))], rtol=0, atol=1e-12)),
        "ridge_rational": bool(np.allclose(ridge, [2, float(Fraction(10, 9))], rtol=0, atol=1e-12)),
        "initial_gradient_rational": bool(np.allclose(gradient, [-4, float(Fraction(-20, 3))], rtol=0, atol=1e-12)),
        "n_lambda_and_intercept_not_penalized": bool(np.allclose(ridge_normal, [[3, 0], [0, 9]], rtol=0, atol=1e-12)),
        "manual_losses": bool(np.allclose([ols_mse, ridge_mse, ridge_j], [.5, float(Fraction(134, 243)), float(Fraction(26, 27))], rtol=0, atol=1e-12)),
        "rank_and_null_direction": int(np.linalg.matrix_rank(deficient)) == 2 and prediction_difference < 1e-12,
        "gradient_step_stability_demonstration": bool(steps[0]["mse_after_one_step"] < initial_loss < steps[1]["mse_after_one_step"]),
        "hessian_stability_bounds": bool(np.allclose([maximum_rate_ols, maximum_rate_ridge], [float(Fraction(3, 8)), float(Fraction(1, 3))], rtol=0, atol=1e-12)),
        "inputs_preserved": bool(np.array_equal(x, originals[0]) and np.array_equal(y, originals[1])),
    }
    solution = f"""## M02-04 — OLS, Ridge, gradiente e posto

### Matriz e solução OLS

```text
X = [[1,−2], [1,0], [1,2]]    shape (3,2)
y = [0,1,5]                    shape (3,)
beta                            shape (2,)
X@beta                          shape (3,)
XᵀX = [[3,0], [0,8]]
Xᵀy = [6,10]
beta_OLS = [6/3,10/8] = [2,5/4]
```

A implementação por SVD retornou `[{ols[0]:.12f}, {ols[1]:.12f}]`. As previsões são `[−0,5;2;4,5]`; os resíduos `y−previsão` são `[0,5;−1;0,5]`. RSS=1,5 e MSE={ols_mse:.12f}. O vetor y precisa ser `(3,)`: `(3,1)` pode induzir broadcasting e uma matriz errada de resíduos `(3,3)`; o validador rejeita esse shape.

### Sinal do gradiente e taxa

```text
J_OLS = ||y−X beta||²/n
gradiente = 2Xᵀ(X beta−y)/n
em beta=[0,0]: gradiente = −2[6,10]/3 = [−4,−20/3]
beta_novo = beta−eta*gradiente = [4 eta,(20/3) eta]
```

Portanto, uma taxa positiva pequena inicialmente aumenta intercepto e inclinação. Isso segue do sinal negativo das derivadas; não significa que uma taxa arbitrária seja estável. A Hessiana OLS é `diag(2,16/3)`. Para descida de gradiente nessa quadrática com taxa constante, a faixa estrita de convergência é `0<eta<2/L = {maximum_rate_ols:.12f}`, onde L é o maior autovalor. O passo demonstrativo eta=0,1 reduziu a MSE de {initial_loss:.12f} para {steps[0]['mse_after_one_step']:.12f}; eta=1 aumentou-a para {steps[1]['mse_after_one_step']:.12f}. Foram dois passos isolados predefinidos, não um treino ou busca de taxa.

### Ridge com a normalização correta

```text
J_Ridge = ||y−X beta||²/n + lambda*beta_1²
P = diag(0,1); lambda=1/3; n lambda=1
(XᵀX+n lambda P) beta = Xᵀy
[[3,0],[0,9]] beta = [6,10]
beta_Ridge = [2,10/9] = [{ridge[0]:.12f}, {ridge[1]:.12f}]
```

O intercepto não é penalizado. A inclinação encolhe de 1,25 para 10/9; omitir n mudaria a solução. A MSE de ajuste Ridge foi {ridge_mse:.12f}, maior que a OLS, mas seu objetivo **com a penalização comum lambda=1/3** foi {ridge_j:.12f}, menor que {ols_j:.12f} ao avaliar OLS com a mesma penalização. Isso confere que os dois algoritmos resolvem objetivos distintos. Na quadrática Ridge, a Hessiana é `diag(2,6)` e a faixa correspondente é `0<eta<1/3`. Nenhuma dessas contas garante menor erro futuro ou identificação causal.

### Colinearidade e direção nula

Ao acrescentar a coluna 2x, X tem três colunas e posto {int(np.linalg.matrix_rank(deficient))}. A direção `[0,2,−1]` é nula: `2x−(2x)=0`. Somá-la a qualquer solução deixa as previsões iguais; a maior diferença numérica observada foi {prediction_difference:.3g}. A SVD devolveu uma solução de norma mínima `[{beta_deficient[0]:.12f}, {beta_deficient[1]:.12f}, {beta_deficient[2]:.12f}]`, que é uma convenção entre várias decomposições equivalentes. Regularização pode tornar a solução numérica única, mas não cria efeitos físicos separados.

### Resíduos de ajuste e futuro

Com intercepto em OLS, `Xᵀr=0` implica soma residual de ajuste aproximadamente zero. Essa propriedade algébrica não valida previsões futuras nem seus intervalos. Se resíduos futuros exibirem autocorrelação, a fórmula IID usual de erro-padrão dos coeficientes não fica justificada. Sob exogeneidade, OLS pode continuar sem viés, mas a inferência precisa da estrutura de covariância; dependência e mudança de regime também importam para previsão. O exercício não fornece uma série futura, então não foi fabricada nem medida autocorrelação futura. A conta resolve a interpretação da hipótese apresentada, sem alegar um experimento que não ocorreu.
"""
    return result, checks, {"contas_regressao.csv": rows}, solution


SOLVERS = {"M02-01": solve_probability, "M02-02": solve_estimation, "M02-03": solve_hypotheses, "M02-04": solve_regression}


def execute(protocols, document):
    if document.exists():
        raise ValueError(f"O documento de saída já existe e será preservado: {document}")
    sessions = {}
    for item, path in protocols.items():
        others = [p.name for p in path.parent.iterdir() if p.name != "protocolo.json"]
        if others:
            raise ValueError(f"Há saídas preservadas em {path.parent}: {others}. Use outro --output-root.")
        plan = json.loads(path.read_text(encoding="utf-8"))
        started = now()
        if datetime.fromisoformat(plan["frozen_at_utc"]) > datetime.fromisoformat(started):
            raise ValueError("O protocolo deve anteceder os cálculos.")
        sessions[item] = {"path": path, "plan": plan, "started": started, "protocol_sha": sha(path)}
    # Os quatro protocolos estão fechados antes da primeira chamada numérica.
    solutions = {}
    for item, session in sessions.items():
        result, checks, tables, solution = SOLVERS[item](session["plan"]["design"]["inputs"])
        if not checks or any(value is not True for value in checks.values()):
            raise ValueError(f"Conferência analítica falhou em {item}: {checks}")
        solutions[item] = (result, checks, tables, solution)
    intro = """# Fundamentos aplicados — soluções e resultados M02-01–04

Aplicação técnica assistida solicitada pelo usuário. Os casos antes apresentados como questões foram agora resolvidos por código e por derivação. **Não se exige uma resposta do usuário para concluir esta aplicação técnica.** Isso não declara autoria independente nem mede aprendizagem; `learning_validated=false` permanece como limite de escopo, sem constituir uma pendência que bloqueie esta entrega de engenharia.

Os protocolos foram gravados antes dos cálculos, e as saídas estão separadas em `reports/fechamento_m00_m09/bloco1_engenharia/M02-01` a `M02-04`. As demonstrações e avaliações anteriores foram preservadas. Os dados desta aplicação são os números fixos dos enunciados: não há treino de benchmark, novo holdout, download ou equipamento comandado.

Para conferir a execução em outra pasta, use na raiz:

```powershell
python notebooks/aplicar_fundamentos_quantitativos.py --preparar --output-root reports/reproducao_fundamentos_aplicados_01
python notebooks/aplicar_fundamentos_quantitativos.py --output-root reports/reproducao_fundamentos_aplicados_01
```

No destino alternativo, o documento compartilhado fica na própria pasta de reprodução. Arquivos já existentes não são sobrescritos. Os CSVs mantêm os números usados nas contas; cada recibo guarda versões, fontes, hashes e conferências observadas.

"""
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text(intro + "\n\n".join(value[3] for value in solutions.values()), encoding="utf-8")
    for item, session in sessions.items():
        result, checks, tables, solution = solutions[item]
        directory = session["path"].parent
        for filename, rows in tables.items():
            with (directory / filename).open("x", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        (directory / "solucao_tecnica.md").write_text(
            f"# Solução técnica assistida — {item}\n\nResponsável pela implementação e execução: Codex. Aplicação solicitada pelo usuário; não é resposta independente atribuída ao aluno.\n\n" + solution,
            encoding="utf-8")
        (directory / "parecer.md").write_text(
            f"# Conclusão técnica — {item}\n\nResponsável: Codex, implementação e conferência assistidas.\n\n"
            f"A aplicação numérica foi executada e passou em {len(checks)} conferências analíticas predefinidas. As contas e interpretações estão em `solucao_tecnica.md`, com tabelas CSV nesta pasta. "
            "Os números foram calculados depois do protocolo e não houve treino de benchmark.\n\n"
            "Decisão de engenharia: aplicação técnica concluída no escopo dos casos fornecidos. Não requer resposta adicional do usuário. Aprendizagem e autoria independente não foram avaliadas; isso não é um aceite de professor nem uma aprovação operacional.\n", encoding="utf-8")
        if sha(session["path"]) != session["protocol_sha"]:
            raise ValueError("Protocolo alterado durante a execução.")
        current_sources = {name: sha(ROOT / name) for name in SOURCES}
        if current_sources != session["plan"]["source_sha256"]:
            raise ValueError("Uma fonte mudou após o congelamento.")
        prior_hashes = session["plan"]["preserved_prior_artifacts_sha256"]
        if any(sha(ROOT / name) != digest for name, digest in prior_hashes.items()):
            raise ValueError("Um artefato anterior mudou durante a aplicação.")
        output_hashes = {path_label(path): sha(path) for path in sorted(directory.iterdir()) if path.is_file()}
        output_hashes[path_label(document)] = sha(document)
        receipt = {
            "schema": "m02-aplicacao-tecnica-result-v1", "item": item, "completed": True,
            "status": "concluido_tecnico_assistido", "technical_application_completed": True,
            "execution_started_at_utc": session["started"], "execution_finished_at_utc": now(),
            "protocol_frozen_at_utc": session["plan"]["frozen_at_utc"], "protocol_before_numeric_calculations": True,
            "protocol_unchanged_after_execution": True, "os": platform.system(), "python": sys.version.split()[0],
            "versions": {name: version(name) for name in ("numpy", "scipy")}, "input_sha256": {path_label(session["path"]): session["protocol_sha"]},
            "source_sha256": current_sources, "output_sha256": output_hashes, "checks": checks, "results": result,
            "preserved_prior_artifacts_sha256": prior_hashes,
            "responsibility": "Codex: implementação, execução e solução técnica assistidas, conforme a demanda atual.",
            "human_response_required": False, "learning_validated": False, "learning_evaluation": "não avaliada",
            "independent_student_authorship_claimed": False, "operational_approval": False,
            "benchmark_retrained": False, "original_frozen_deliveries_modified": False,
        }
        dump(directory / "resultado.json", receipt)
        print(f"{item}: aplicação concluída; {len(checks)} conferências analíticas; {directory}")
    print(f"Explicação detalhada: {document}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preparar", action="store_true", help="Registra os quatro protocolos sem calcular as soluções.")
    args = parser.parse_args(argv)
    output_root = args.output_root.resolve()
    protocols = prepare(output_root)
    if args.preparar:
        for item, path in protocols.items():
            print(f"{item}: protocolo congelado em {path}")
        return 0
    document = DOCUMENT if output_root == DEFAULT_OUTPUT.resolve() else output_root / "Fundamentos_Aplicados_Resultados.md"
    return execute(protocols, document)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Aplicação M02: {exc}") from None
