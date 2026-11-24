"""Gera figuras dos arquivos da execução, sem carregar ou executar o modelo."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "20261117T213329Z_3b201a01"
RUN = ROOT / "reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado" / RUN_ID
OUT = Path(__file__).resolve().parent


def main():
    summary = pd.read_csv(RUN / "summary.csv")
    aligned = pd.read_csv(RUN / "alinhamento_alvos.csv", parse_dates=["target_time"])
    paired = pd.read_csv(RUN / "comparacao_pareada.csv", parse_dates=["target_time"])
    paired = paired.sort_values("target_time")
    aligned = aligned.sort_values("target_time")
    assert len(aligned) == len(paired) == 168
    pd.testing.assert_series_equal(aligned.target_time, paired.target_time)
    np.testing.assert_allclose(aligned.target_generation, paired.target_generation)

    labels = []
    colors = []
    for row in summary.itertuples():
        if row.method == "chronos_bolt_tiny_zero_shot":
            label, color = "Chronos-Bolt Tiny · P50", "#087f5b"
        elif row.method == "hgb_24h":
            label, color = "HGB · semente 17", "#1971c2"
        elif row.method == "persistence_d2":
            label, color = "Persistência d2", "#a3adb8"
        elif row.method == "linear_24h":
            label, color = "Linear · 24 horas", "#a3adb8"
        else:
            label = f"{row.method.split('_')[0].upper()} · semente {int(row.seed)}"
            color = "#a3adb8"
        labels.append(label)
        colors.append(color)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axes = plt.subplots(1, 3, figsize=(15, 6.2), sharey=True)
    measures = [
        ("mae_mwmed", "Erro absoluto médio (MAE)"),
        ("rmse_mwmed", "Raiz do erro quadrático (RMSE)"),
        ("bias_observed_minus_predicted_mwmed", "Viés: observado − previsto"),
    ]
    y = np.arange(len(summary))
    for ax, (column, title) in zip(axes, measures):
        values = summary[column].to_numpy()
        bars = ax.barh(y, values, color=colors, height=0.66)
        ax.bar_label(bars, labels=[f"{value:.2f}".replace(".", ",") for value in values],
                     padding=4, fontsize=9)
        ax.axvline(0, color="#5c6670", linewidth=0.8)
        ax.set_title(title, fontsize=11, pad=12)
        ax.set_xlabel("MWmed")
        ax.grid(axis="x", alpha=0.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.set_xlim(min(0, values.min() * 1.4), values.max() * 1.18)
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    fig.suptitle("Mesmos 168 alvos · comparação Windows", fontsize=16, x=0.03, ha="left")
    fig.text(0.03, 0.925, "Azul: HGB de referência   |   Verde: Chronos com pesos congelados   |   Todas as sementes preservadas",
             color="#4e5964", fontsize=10)
    fig.text(0.03, 0.025, "Viés positivo indica subestimação média. Semana de desenvolvimento; sem aprovação operacional.",
             color="#4e5964", fontsize=10)
    fig.subplots_adjust(left=0.19, right=0.98, top=0.84, bottom=0.15, wspace=0.17)
    fig.savefig(OUT / "comparacao_modelos.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(13.5, 5.7))
    times = aligned.target_time
    ax.fill_between(times, aligned.p10, aligned.p90, color="#b2dfd0", alpha=0.8,
                    label="P10–P90 · cobertura nominal de 80%")
    ax.plot(times, aligned.target_generation, color="#252a30", linewidth=1.5, label="Observado")
    ax.plot(times, aligned.p50, color="#087f5b", linewidth=1.3, label="Chronos · P50")
    ax.plot(times, paired.hgb_prediction, color="#1971c2", linewidth=1.1, alpha=0.85, label="HGB")
    ax.set_title("Intervalos brutos e previsões pontuais nos 168 alvos", loc="left", fontsize=15, pad=38)
    ax.text(0, 1.055, "135 alvos cobertos (80,36%) · largura média: 83,60 MWmed · sem clipping ou recalibração",
            transform=ax.transAxes, fontsize=10, color="#4e5964")
    ax.set_ylabel("Geração (MWmed)")
    ax.set_xlabel("Timestamp do alvo · julho de 2026 · eixo sem fuso da entrada")
    locator = mdates.AutoDateLocator(minticks=6, maxticks=9)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.grid(alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", ncols=2, fontsize=9)
    ax.margins(x=0.005)
    fig.text(0.07, 0.02, "Intervalo preditivo, não intervalo de confiança da média. Cobertura nesta semana não prova calibração futura.",
             fontsize=9, color="#4e5964")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.16)
    fig.savefig(OUT / "intervalos_previsoes.png", dpi=170)
    plt.close(fig)
    print("Figuras geradas a partir dos CSVs; nenhuma inferência foi executada.")


if __name__ == "__main__":
    main()
