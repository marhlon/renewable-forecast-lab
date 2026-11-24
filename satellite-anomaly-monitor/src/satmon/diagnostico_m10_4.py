"""Limites de confirmação e diagnósticos da série, sem escolher novos alarmes."""
from __future__ import annotations

import numpy as np
import pandas as pd


def limite_confirmacao(escores, utilizavel, *, consecutivos):
    """Maior corte que admite uma janela inteira e o índice em que ela termina."""
    s = np.asarray(escores, dtype=float)
    u = np.asarray(utilizavel)
    if s.ndim != 1 or u.shape != s.shape or u.dtype != bool:
        raise ValueError("Informe vetores 1D do mesmo tamanho, com máscara booleana.")
    if (isinstance(consecutivos, (bool, np.bool_)) or not isinstance(consecutivos, (int, np.integer))
            or consecutivos < 1):
        raise ValueError("consecutivos deve ser um inteiro positivo.")
    if not np.isfinite(s[u]).all():
        raise ValueError("Os escores utilizáveis devem ser finitos.")
    k = int(consecutivos)
    sem_janela = {"limiar_maximo": None, "indice_confirmacao": None}
    if k > s.size:
        return sem_janela
    mascarado = np.where(u, s, -np.inf)
    minimos = np.lib.stride_tricks.sliding_window_view(mascarado, k).min(axis=-1)
    i = int(minimos.argmax())
    if np.isneginf(minimos[i]):
        return sem_janela
    return {"limiar_maximo": float(minimos[i]), "indice_confirmacao": i + k - 1}


def checar_saida(func, escores, utilizavel, k):
    """A autoria recebe a grade completa, sem poder alterar os vetores."""
    s = escores.view()
    u = utilizavel.view()
    s.setflags(write=False)
    u.setflags(write=False)
    got = func(s, u, consecutivos=k)
    error = "Retorne limiar_maximo numérico e indice_confirmacao inteiro, ou ambos None."
    if not isinstance(got, dict) or set(got) != {"limiar_maximo", "indice_confirmacao"}:
        raise ValueError(error)
    value, i = got["limiar_maximo"], got["indice_confirmacao"]
    if value is None and i is None:
        return got
    if (not isinstance(value, (int, float, np.integer, np.floating)) or isinstance(value, (bool, np.bool_))
            or not np.isfinite(value) or not isinstance(i, (int, np.integer))
            or isinstance(i, (bool, np.bool_)) or not k - 1 <= i < len(s)):
        raise ValueError(error)
    return {"limiar_maximo": float(value), "indice_confirmacao": int(i)}


def conferir_autoria(func):
    cases = [
        ([.70, .80, .90, .95, .88, .89, .65, .71, .71], [1, 1, 1, 0, 1, 1, 1, 1, 1], 2, .88, 5),
        ([1., 10., 2.], [1, 0, 1], 2, None, None),
        ([5., 7., 5.], [1, 1, 1], 2, 5., 1),
        ([-8., -2., -3., -1.], [1, 1, 1, 1], 2, -3., 2),
        ([np.nan, 8., 1.], [0, 1, 1], 1, 8., 1),
        ([1.], [1], 3, None, None),
        ([], [], 1, None, None),
    ]
    for no, (x, u, k, val, ind) in enumerate(cases, start=1):
        got = checar_saida(func, np.asarray(x, dtype=float), np.asarray(u, dtype=bool), k)
        want = {"limiar_maximo": val, "indice_confirmacao": ind}
        if got != want:
            raise ValueError(f"Contraprova {no}: recebido {got}; esperado {want}.")
    return len(cases)


def janela_conferida(func, scores, mask, k):
    got = checar_saida(func, scores, mask, k)
    if func is not limite_confirmacao and got != limite_confirmacao(scores, mask, consecutivos=k):
        raise ValueError(f"Autoria não reproduz o limite de confirmação com k={k} na grade real.")
    return got


def perfil_temporal(particao, escala_original, scores, ev, threshold, limite, k):
    """Perfil anual da mesma floresta e medidas marginais na mesma coorte."""
    score_rows, channel_rows, pair_rows = [], [], []
    names = ("channel_50", "channel_51", "channel_52")
    years = ev.t.year.to_numpy()
    # Uma janela anual não pode usar o último slot do ano anterior.
    for year in sorted(set(years)):
        ano = years == year
        for cohort, cohort_mask in (("utilizavel", ev.valid), ("sem_anotacao", ev.nominal)):
            mask = ano & cohort_mask
            a = scores[mask]
            if not a.size:
                continue
            values = np.quantile(a, [.50, .90, .99, .9995])
            m1 = float(a.max())
            janela = janela_conferida(limite, scores, mask, k)
            score_rows.append({
                "particao": particao, "ano": int(year), "coorte": cohort,
                "instantes": len(a), "p50": values[0], "p90": values[1], "p99": values[2],
                "p9995": values[3], "s1": m1, "s2": janela["limiar_maximo"],
                "limiar_congelado": threshold, "pontos_no_corte": int((a >= threshold).sum()),
            })
            # Evita confundir mudança de prevalência anotada com mudança fora das anotações.
            if cohort != "sem_anotacao":
                continue
            z = escala_original[mask]
            for ix, name in enumerate(names):
                p10, med, p90 = np.quantile(z[:, ix], [.1, .5, .9])
                channel_rows.append({"particao": particao, "ano": int(year), "canal": name,
                                     "instantes": len(z), "z_p10": p10, "z_p50": med, "z_p90": p90})
            rank_corr = pd.DataFrame(z, columns=names).rank().corr()
            for i, first in enumerate(names):
                for second in names[i+1:]:
                    pair_rows.append({"particao": particao, "ano": int(year), "par": f"{first}/{second}",
                                      "instantes": len(z), "spearman": rank_corr.loc[first, second]})
    return score_rows, channel_rows, pair_rows


def limites_por_id(scores, ev, event_rows, func, k):
    """Janela contida na união de slots anotados e avaliáveis de cada ID."""
    for data in event_rows:
        eid = data["id"]
        spans = ev.intervals[eid]
        m = np.zeros(len(scores), dtype=bool)
        for span in spans:
            m[span.left:span.right] = True
        mask = m & ev.eligible
        strongest = janela_conferida(func, scores, mask, k)
        i = strongest["indice_confirmacao"]
        yield {
            **data, "canais_anotados": ",".join(sorted({s.channel for s in spans})),
            "slots_anotados_avaliaveis": int(mask.sum()),
            "s1_no_id": float(scores[mask].max()) if mask.any() else None,
            "s2_no_id": strongest["limiar_maximo"],
            "fim_janela_mais_forte_utc": ev.t[i].isoformat() if i is not None else None,
        }
