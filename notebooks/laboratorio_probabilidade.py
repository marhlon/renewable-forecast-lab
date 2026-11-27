"""M02-01–03: probabilidade, estimação e hipóteses em dados sintéticos.

Use --preparar para registrar somente os protocolos. A execução normal também
os registra, antes das simulações. Um resultado anterior nunca é sobrescrito.
"""
from __future__ import annotations

import argparse
from math import comb
from pathlib import Path

import numpy as np
from scipy.stats import norm, t

from _fundamentos_evidencias import DEFAULT_OUTPUT, Execution, prepare_protocol, write_csv


def probabilidade_positiva(prevalencia, sensibilidade, falso_positivo):
    """P(evento | sinal positivo), sem supor que sensibilidade seja esse valor."""
    values = np.asarray([prevalencia, sensibilidade, falso_positivo], dtype=float)
    if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
        raise ValueError("As três probabilidades devem estar entre zero e um.")
    numerator = prevalencia * sensibilidade
    denominator = numerator + (1 - prevalencia) * falso_positivo
    if denominator == 0:
        raise ValueError("Evento condicionante com probabilidade zero.")
    return float(numerator / denominator)


def momentos_discretos(valores, probabilidades):
    x, p = np.asarray(valores, dtype=float), np.asarray(probabilidades, dtype=float)
    if x.ndim != 1 or p.ndim != 1 or x.shape != p.shape or x.size == 0:
        raise ValueError("Valores e probabilidades precisam ser vetores do mesmo tamanho.")
    if not np.isfinite(x).all() or not np.isfinite(p).all() or np.any(p < 0):
        raise ValueError("Valores finitos e probabilidades não negativas são obrigatórios.")
    if not np.isclose(p.sum(), 1, rtol=0, atol=1e-12):
        raise ValueError("As probabilidades devem somar um.")
    mean = float(x @ p)
    variance = float(((x - mean) ** 2) @ p)
    return mean, variance


def intervalos_normais(amostra, confianca=0.95):
    """IC da média e PI para UMA observação futura, sob normalidade e IID."""
    x = np.asarray(amostra, dtype=float)
    if x.ndim != 1 or x.size < 2 or not np.isfinite(x).all():
        raise ValueError("Use um vetor finito com pelo menos duas observações.")
    if not 0 < confianca < 1:
        raise ValueError("Confiança deve estar entre zero e um.")
    n = x.size
    mean, variance = float(x.mean()), float(x.var(ddof=1))
    q = float(t.ppf((1 + confianca) / 2, n - 1))
    se = float(np.sqrt(variance / n))
    mean_half = q * se
    prediction_half = q * float(np.sqrt(variance * (1 + 1 / n)))
    return {
        "n": int(n), "media": mean, "variancia_n_menos_1": variance,
        "erro_padrao": se, "t_critico": q,
        "ic_media_inferior": mean - mean_half, "ic_media_superior": mean + mean_half,
        "pi_observacao_inferior": mean - prediction_half, "pi_observacao_superior": mean + prediction_half,
    }


def tamanho_efetivo_ar1(n, rho):
    """n_eff exato para a variância da média de AR(1) estacionário conhecido."""
    if type(n) is not int or n < 1 or not np.isfinite(rho) or not -1 < rho < 1:
        raise ValueError("Exige n inteiro positivo e -1 < rho < 1.")
    lags = np.arange(1, n)
    covariance_sum = n + 2 * float(np.sum((n - lags) * rho ** lags))
    return float(n * n / covariance_sum)


def teste_melhoria_blocos(diferencas, *, tamanho_bloco, efeito_minimo, alpha):
    """Teste t unilateral em médias de blocos independentes de tamanho fixo.

    H0: média da diferença <= efeito_minimo. Diferença positiva favorece B.
    A validade requer normalidade/independência das médias de blocos; o nome
    'bloco' por si só não garante essas condições em dados reais.
    """
    d = np.asarray(diferencas, dtype=float)
    if d.ndim != 1 or not np.isfinite(d).all():
        raise ValueError("Diferenças precisam ser um vetor finito.")
    if type(tamanho_bloco) is not int or tamanho_bloco < 1 or d.size % tamanho_bloco:
        raise ValueError("Tamanho de bloco positivo deve dividir exatamente a amostra.")
    if d.size // tamanho_bloco < 2 or not 0 < alpha < 1 or not np.isfinite(efeito_minimo):
        raise ValueError("São necessários dois blocos, alpha válido e efeito mínimo finito.")
    blocks = d.reshape(-1, tamanho_bloco).mean(axis=1)
    se = float(blocks.std(ddof=1) / np.sqrt(blocks.size))
    if se == 0:
        raise ValueError("Variabilidade entre blocos nula; teste t não definido.")
    mean = float(blocks.mean())
    statistic = (mean - efeito_minimo) / se
    p_value = float(t.sf(statistic, blocks.size - 1))
    lower = mean - float(t.ppf(1 - alpha, blocks.size - 1)) * se
    return {"media_diferenca": mean, "n_blocos": int(blocks.size), "erro_padrao_blocos": se,
            "t": statistic, "p_unilateral": p_value, "limite_inferior_unilateral": lower,
            "rejeita_h0": bool(p_value < alpha)}


def planos():
    return {
        "M02-01": {
            "source": "Somente tabelas e variáveis sintéticas; nenhum dado ONS/ESA.",
            "population": {"n": 10000, "event_prevalence": 0.01, "sensitivity": 0.90, "false_positive_rate": 0.05},
            "discrete": {"values": [0, 1, 2], "probabilities": [0.5, 0.3, 0.2]},
            "binomial": {"n": 24, "p": 0.01, "independent_trials_assumed": True},
            "checks": ["PPV = 90/585", "E[X] = 0.7", "Var[X] = 0.61", "binomial probabilities sum to one"],
        },
        "M02-02": {
            "source": "Amostra didática fixa e simulações normais sintéticas.",
            "seed": 2026112502, "bit_generator": "PCG64", "manual_sample": [8, 10, 12],
            "normal_simulation": {"repetitions": 2000, "n": 16, "mu": 10.0, "sigma": 2.0},
            "ar1_simulation": {"repetitions": 2000, "n": 48, "mu": 10.0, "marginal_sigma": 1.0, "rho": 0.8, "stationary_start": True},
            "confidence": 0.95,
            "assumptions": ["t intervals: normal IID observations", "AR1 coverage: covariance known from synthetic generator; not estimated from real data"],
            "checks": ["manual mean = 10 and sample variance = 4", "PI wider than mean CI", "n_eff(rho=0)=n", "AR1 known covariance positive"],
        },
        "M02-03": {
            "source": "Diferenças de perda geradas diretamente; nenhum modelo ou benchmark treinado.",
            "seed": 2026112503, "bit_generator": "PCG64", "n_blocks": 10, "observations_per_block": 24,
            "family_size": 4, "true_mean_differences": [1.2, 0.0, 0.0, 0.0],
            "block_shift_sigma": 1.8, "within_block_sigma": 0.5,
            "estimand": "Média populacional de perda_A - perda_B por unidade sintética.",
            "h0": "mu_d <= 1.0", "h1": "mu_d > 1.0", "minimum_relevant_effect": 1.0,
            "alpha_family": 0.05, "multiplicity": "Bonferroni: alpha = 0.05 / 4, before generating any data",
            "decision": "Reject H0 only if block-based one-sided p < 0.0125. Never select the smallest unadjusted p as confirmatory evidence.",
            "assumptions": ["independent normal block shifts", "independent normal within-block noise", "adjacent observations share a block effect", "same fixed family of four hypotheses"],
            "checks": ["all four prespecified hypotheses reported", "block mean equals full mean", "p-values between zero and one", "lower-bound and p-value decisions agree"],
        },
    }


def run_probabilidade(protocol):
    execution = Execution(protocol)
    design = execution.plan["design"]
    pop = design["population"]
    total_events = pop["n"] * pop["event_prevalence"]
    tp = total_events * pop["sensitivity"]
    fn = total_events - tp
    fp = (pop["n"] - total_events) * pop["false_positive_rate"]
    tn = pop["n"] - total_events - fp
    ppv = probabilidade_positiva(pop["event_prevalence"], pop["sensitivity"], pop["false_positive_rate"])
    mean, variance = momentos_discretos(design["discrete"]["values"], design["discrete"]["probabilities"])
    n, p = design["binomial"]["n"], design["binomial"]["p"]
    pmf = [comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(n + 1)]
    content = f"""# M02-01 — contas resolvidas e aplicação

Demonstração assistida; avaliação independente pendente em `docs/roadmap_m00_m09/Avaliacao_Fundamentos.md`.

Em 10.000 oportunidades sintéticas: {tp:.0f} verdadeiros positivos, {fn:.0f} falsos negativos, {fp:.0f} falsos positivos e {tn:.0f} verdadeiros negativos. Assim, P(evento|positivo) = 90/(90+495) = {ppv:.12f}. A sensibilidade de 90% é P(positivo|evento), outra condição.

Para X em {{0,1,2}} com probabilidades {{0,5;0,3;0,2}}: E[X] = 0×0,5+1×0,3+2×0,2 = {mean:.6f}; E[X²] = 1,1; Var[X] = 1,1−0,7² = {variance:.6f}.

Bernoulli descreve um indicador; Binomial(24,0,01) conta sucessos em 24 tentativas independentes com p constante (média 0,24; variância 0,2376); Poisson(0,24) seria outra hipótese para contagens raras sob taxa constante e incrementos independentes. Normal é uma hipótese possível para erro contínuo, sem garantir suporte não negativo para geração. Nenhuma distribuição é validada em dados ONS por esta conta. Sensores e horas correlacionadas não viram tentativas independentes por conveniência.

A população de 10.000 é uma tabela didática construída; uma amostra observada terá flutuação. A taxa-base usada aqui é conhecida por desenho. No uso real, é preciso estimá-la na população e no período pertinentes.
"""
    (execution.directory / "exercicios.md").write_text(content, encoding="utf-8")
    (execution.directory / "parecer.md").write_text(
        "# Parecer da demonstração M02-01\n\nResponsável: Codex, construção e execução assistidas.\n\n"
        f"As contas manuais coincidiram com a implementação: PPV={ppv:.12f}, esperança={mean:.6f}, variância={variance:.6f}. "
        "A taxa-base baixa explica a maioria de falsos positivos entre os sinais positivos mesmo com sensibilidade alta. "
        "A conta não transforma um percentil de escore em probabilidade de evento.\n\n"
        "Decisão: demonstração técnica executada; aprendizagem não validada. Aguardam-se respostas do aluno aos casos novos e revisão humana.\n", encoding="utf-8")
    return execution.finish(
        {"true_positives": tp, "false_negatives": fn, "false_positives": fp, "true_negatives": tn,
         "posterior_positive": ppv, "discrete_mean": mean, "discrete_variance": variance,
         "binomial_mean": n * p, "binomial_variance": n * p * (1 - p), "binomial_pmf_sum": float(sum(pmf))},
        {"bayes_manual": bool(np.isclose(ppv, 90 / 585, rtol=0, atol=1e-14)),
         "manual_moments": bool(np.allclose([mean, variance], [.7, .61], rtol=0, atol=1e-14)),
         "confusion_total": bool(np.isclose(tp + fn + fp + tn, pop["n"])),
         "binomial_sum": bool(np.isclose(sum(pmf), 1, rtol=0, atol=1e-12))})


def run_estimacao(protocol):
    execution = Execution(protocol)
    design = execution.plan["design"]
    rng = np.random.Generator(np.random.PCG64(design["seed"]))
    manual = intervalos_normais(design["manual_sample"], design["confidence"])
    sim = design["normal_simulation"]
    samples = rng.normal(sim["mu"], sim["sigma"], size=(sim["repetitions"], sim["n"]))
    mle_variance = float(samples.var(axis=1, ddof=0).mean())
    unbiased_variance = float(samples.var(axis=1, ddof=1).mean())
    mean_bias = float(samples.mean(axis=1).mean() - sim["mu"])
    ar = design["ar1_simulation"]
    centered = np.empty((ar["repetitions"], ar["n"]))
    centered[:, 0] = rng.normal(0, ar["marginal_sigma"], ar["repetitions"])
    innovation_sigma = ar["marginal_sigma"] * np.sqrt(1 - ar["rho"] ** 2)
    for j in range(1, ar["n"]):
        centered[:, j] = ar["rho"] * centered[:, j - 1] + rng.normal(0, innovation_sigma, ar["repetitions"])
    neff = tamanho_efetivo_ar1(ar["n"], ar["rho"])
    z = float(norm.ppf((1 + design["confidence"]) / 2))
    ar_samples = ar["mu"] + centered
    errors = ar_samples.mean(axis=1) - ar["mu"]
    half_iid = z * ar["marginal_sigma"] / np.sqrt(ar["n"])
    half_ar1 = z * ar["marginal_sigma"] / np.sqrt(neff)
    iid_coverage = float(np.mean(np.abs(errors) <= half_iid))
    correct_coverage = float(np.mean(np.abs(errors) <= half_ar1))
    rows = [{"grupo": "amostra_manual", "medida": key, "valor": value, "hipotese": "Normal IID; variância desconhecida"} for key, value in manual.items()]
    rows += [
        {"grupo": "simulacao_iid", "medida": "vies_media_monte_carlo", "valor": mean_bias, "hipotese": "2000 amostras de Normal(10,2²), n=16"},
        {"grupo": "simulacao_iid", "medida": "variancia_mle_media", "valor": mle_variance, "hipotese": "Expectativa teórica = 3,75"},
        {"grupo": "simulacao_iid", "medida": "variancia_n_menos_1_media", "valor": unbiased_variance, "hipotese": "Expectativa teórica = 4"},
        {"grupo": "simulacao_ar1", "medida": "n_efetivo_exato", "valor": neff, "hipotese": "Covariância AR1 conhecida; rho=0,8, n=48"},
        {"grupo": "simulacao_ar1", "medida": "cobertura_ic_iid_inadequado", "valor": iid_coverage, "hipotese": "Sigma marginal conhecido; dependência ignorada"},
        {"grupo": "simulacao_ar1", "medida": "cobertura_ic_ar1_conhecido", "valor": correct_coverage, "hipotese": "Sigma e rho conhecidos do gerador"},
    ]
    write_csv(execution.directory / "estimativas.csv", rows)
    (execution.directory / "parecer.md").write_text(f"""# Parecer da demonstração M02-02

Responsável: Codex, construção e execução assistidas. Dados exclusivamente sintéticos; protocolo anterior à geração.

O estimando é a média populacional μ; o estimador é a média amostral. Na amostra [8,10,12], média = {manual['media']:.6f}, s² = {manual['variancia_n_menos_1']:.6f}, erro-padrão = {manual['erro_padrao']:.6f}. Sob Normal IID, o IC de 95% da média é [{manual['ic_media_inferior']:.6f}, {manual['ic_media_superior']:.6f}]; o PI para uma nova observação é [{manual['pi_observacao_inferior']:.6f}, {manual['pi_observacao_superior']:.6f}]. A observação futura contém dispersão própria, por isso seu intervalo é maior. Confiança é uma propriedade de cobertura do procedimento, não probabilidade frequentista posterior do parâmetro fixo.

Em 2.000 amostras IID de tamanho 16, o viés Monte Carlo da média foi {mean_bias:.6f}; as médias dos estimadores de variância foram {mle_variance:.6f} com divisor n e {unbiased_variance:.6f} com divisor n−1. Os alvos teóricos são 3,75 e 4. O pequeno desvio de Monte Carlo não altera a identidade teórica; não se escolheu outra semente para melhorar a aparência.

Na simulação AR(1) estacionária com 48 observações e rho conhecido de 0,8, n_eff exato para a variância da média = {neff:.6f}. A cobertura simulada do IC que ignora dependência foi {iid_coverage:.4%}; usando a covariância conhecida do gerador, {correct_coverage:.4%}. São 2.000 repetições; cobertura observada também tem erro Monte Carlo. Essa correção não foi estimada em dados reais e não substitui um bootstrap em blocos. O n_eff é específico desse estimando e desse modelo de covariância, não uma contagem universal de observações independentes.

Decisão: demonstração técnica executada; aguarda resposta e revisão humanas para fechamento formativo.
""", encoding="utf-8")
    return execution.finish(
        {"manual": manual, "monte_carlo_mean_bias": mean_bias, "mean_variance_mle": mle_variance,
         "mean_variance_unbiased": unbiased_variance, "ar1_n_eff_exact": neff,
         "ar1_iid_interval_coverage": iid_coverage, "ar1_known_covariance_interval_coverage": correct_coverage,
         "monte_carlo_repetitions": sim["repetitions"]},
        {"manual_mean_variance": bool(np.allclose([manual["media"], manual["variancia_n_menos_1"]], [10, 4])),
         "prediction_interval_wider": bool(manual["pi_observacao_superior"] > manual["ic_media_superior"]),
         "independent_n_eff": bool(np.isclose(tamanho_efetivo_ar1(48, 0.0), 48)),
         "ar1_covariance_positive": bool(0 < neff < ar["n"]),
         "same_samples_variance_identity": bool(np.isclose(unbiased_variance, mle_variance * sim["n"] / (sim["n"] - 1)))})


def run_hipoteses(protocol):
    execution = Execution(protocol)
    design = execution.plan["design"]
    (execution.directory / "plano_hipoteses.md").write_text("""# Plano fixado antes de gerar as diferenças

Responsável: Codex. Dados sintéticos, sem treino ou seleção de benchmark. O protocolo JSON é o registro de hipóteses e parâmetros.

Estimando: μ_d = E[perda_A−perda_B], em unidades de perda sintética. Positivo favorece B. Para cada um dos quatro candidatos, H0: μ_d ≤ 1; H1: μ_d > 1. A melhoria mínima relevante é 1. Não testar somente μ_d=0 e depois chamar uma melhoria menor que 1 de suficiente.

Desenho: 10 blocos independentes, com 24 leituras cada. Um deslocamento normal compartilhado gera dependência dentro do bloco; blocos e ruídos são independentes pelo gerador. O teste principal usa as 10 médias de blocos. O teste ingênuo com 240 horas é apenas uma contraprova de pseudorreplicação e não define a decisão.

Família congelada: quatro hipóteses unilaterais; alpha familiar 0,05, Bonferroni 0,0125 por teste. Reportar todos os resultados. Rejeitar H0 apenas se p de blocos < 0,0125. O IC unilateral inferior correspondente usa 98,75% por teste, não 95%. O resultado é exploratório/didático, sem operação.

Um p-valor não é P(H0|dados). Não rejeitar H0 não demonstra equivalência nem ausência de efeito. Significância não corrige um desenho inválido. Em dados reais, a independência dos blocos precisaria de defesa; blocos arbitrários não a garantem. Nenhum ajuste após o resultado desta rodada.
""", encoding="utf-8")
    rng = np.random.Generator(np.random.PCG64(design["seed"]))
    k, width = design["n_blocks"], design["observations_per_block"]
    family = design["family_size"]
    block_shift = rng.normal(0, design["block_shift_sigma"], size=(family, k, 1))
    noise = rng.normal(0, design["within_block_sigma"], size=(family, k, width))
    differences = np.asarray(design["true_mean_differences"])[:, None, None] + block_shift + noise
    alpha = design["alpha_family"] / family
    rows = []
    matching_means, matching_decisions = [], []
    for index, values in enumerate(differences):
        d = values.reshape(-1)
        robust = teste_melhoria_blocos(d, tamanho_bloco=width, efeito_minimo=design["minimum_relevant_effect"], alpha=alpha)
        naive = teste_melhoria_blocos(d, tamanho_bloco=1, efeito_minimo=design["minimum_relevant_effect"], alpha=alpha)
        rows.append({"candidato": f"B{index + 1}", "n_horas": int(d.size), "n_blocos": k,
                     "efeito_minimo": design["minimum_relevant_effect"], "diferenca_media": robust["media_diferenca"],
                     "erro_padrao_ingenuo": naive["erro_padrao_blocos"], "p_ingenuo": naive["p_unilateral"],
                     "erro_padrao_blocos": robust["erro_padrao_blocos"], "p_blocos": robust["p_unilateral"],
                     "alpha_bonferroni": alpha, "limite_inferior_bonferroni": robust["limite_inferior_unilateral"],
                     "rejeita_h0_blocos_bonferroni": robust["rejeita_h0"]})
        matching_means.append(bool(np.isclose(robust["media_diferenca"], d.mean())))
        matching_decisions.append(robust["rejeita_h0"] == (robust["limite_inferior_unilateral"] > design["minimum_relevant_effect"]))
    write_csv(execution.directory / "comparacao.csv", rows)
    statements = "\n".join(f"- {r['candidato']}: média {r['diferenca_media']:.6f}; p ingênuo {r['p_ingenuo']:.6g}; p por blocos {r['p_blocos']:.6g}; limite inferior ajustado {r['limite_inferior_bonferroni']:.6f}; rejeição = {r['rejeita_h0_blocos_bonferroni']}." for r in rows)
    (execution.directory / "parecer.md").write_text(f"""# Parecer da demonstração M02-03

Responsável: Codex, construção e execução assistidas. A família de quatro testes, o efeito mínimo de 1 e alpha Bonferroni de {alpha:.4f} foram fixados antes da geração.

{statements}

O teste principal usa dez médias independentes pelo desenho sintético. Contar 240 horas como independentes encolhe artificialmente o erro-padrão quando as leituras compartilham um deslocamento por bloco. A coluna ingênua é diagnóstico e não decide aceite. A correção de Bonferroni controla a probabilidade de ao menos uma rejeição falsa na família, sob validade dos testes individuais; não repara dependência ignorada dentro de um teste.

As conclusões dizem respeito a diferenças sintéticas de perda. Nenhum resultado aqui sustenta superioridade de HGB, GRU ou Chronos. Não houve treino, consulta ao holdout histórico ou escolha da semente pelo resultado. Uma não rejeição limita a evidência contra H0 e não prova equivalência. A validade em uma população real precisaria de outro desenho e de dados apropriados.

Decisão: demonstração técnica executada; fechamento formativo aguarda interpretação do aluno em caso novo e revisão humana.
""", encoding="utf-8")
    return execution.finish(
        {"family_size": family, "alpha_family": design["alpha_family"], "alpha_per_test": alpha, "comparison": rows},
        {"all_prespecified_hypotheses": len(rows) == family,
         "same_means": all(matching_means), "p_values_valid": all(0 <= r["p_blocos"] <= 1 and 0 <= r["p_ingenuo"] <= 1 for r in rows),
         "p_and_interval_decisions_agree": all(matching_decisions)})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preparar", action="store_true", help="Grava somente os três protocolos, sem simular.")
    args = parser.parse_args(argv)
    protocols = {item: prepare_protocol(args.output_root, item, design) for item, design in planos().items()}
    if args.preparar:
        for item, path in protocols.items():
            print(f"{item}: protocolo congelado em {path}")
        return 0
    run_probabilidade(protocols["M02-01"])
    run_estimacao(protocols["M02-02"])
    run_hipoteses(protocols["M02-03"])
    print("Demonstrações concluídas. Avaliação independente e aprendizagem: aguardam resposta humana.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Fundamentos M02: {exc}") from None
