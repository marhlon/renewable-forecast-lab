"""Amostragem auditável: separar distribuição do sorteio."""
from __future__ import annotations

from heapq import nsmallest
from math import exp, fsum, isfinite, nextafter


def candidatos_top_k(logits, k):
    """IDs em ordem decrescente de logit, desempate pelo menor ID."""
    return nsmallest(k, range(len(logits)), key=lambda i: (-logits[i], i))


def peso_top_k(logits, ids, temperatura):
    maior = logits[ids[0]]
    return [exp((logits[i] - maior) / temperatura) for i in ids]


def selecionar_token_top_k(logits, *, temperatura, k, u):
    """Amostra com uma uniforme externa; não depende da máquina gerar o mesmo RNG."""
    if not len(logits) or not all(isfinite(v) for v in logits):
        raise ValueError("Esperado um vetor não vazio de logits finitos.")
    if type(k) is not int or not 1 <= k <= len(logits):
        raise ValueError("k deve ser um inteiro entre 1 e o tamanho do vocabulário.")
    if not isfinite(temperatura) or temperatura <= 0:
        raise ValueError("A temperatura de sampling precisa ser positiva e finita.")
    if not 0 <= u < 1:
        raise ValueError("O sorteio u deve estar em [0,1).")
    ids = candidatos_top_k(logits, k)
    pesos = peso_top_k(logits, ids, temperatura)
    total = fsum(pesos)
    alvo = min(u * total, nextafter(total, 0))
    soma = 0.0
    ultimo_positivo = ids[0]
    for i, w in zip(ids, pesos, strict=True):
        if w:
            ultimo_positivo = i
            soma += w
            if alvo < soma:
                return i
    return ultimo_positivo


def conferir_picker(func):
    """Casos de empate, CDF, estabilidade e mudança real com temperatura."""
    cases = [
        ((0., 0., 0.), 1., 2, .0, 0, "empate no corte top-k"),
        ((0., 0., 0.), 1., 2, .5, 1, "fronteira da CDF"),
        ((-100., 1000., 999.), 1., 2, .8, 2, "softmax estável"),
        ((-100., 1000., 999.), .5, 2, .8, 1, "temperatura altera a escolha"),
        ((-100., 1000., 999.), 9., 1, .999, 1, "top-1"),
        ((1000., -2000., -4000.), 1., 3, .999999, 0, "underflow de alternativas"),
    ]
    for s, temp, k, u, target, name in cases:
        got = func(s, temperatura=temp, k=k, u=u)
        if type(got) is not int or got != target:
            raise ValueError(f"{name}: esperado ID {target}; recebido {got!r}.")
    return len(cases)


def cabe_no_contexto(n_entrada, n_novos, n_limite):
    if not all(type(x) is int for x in (n_entrada, n_novos, n_limite)) or min(n_entrada,n_novos,n_limite) < 1:
        raise ValueError("Comprimentos e limite devem ser inteiros positivos.")
    return n_entrada + n_novos <= n_limite
