"""Escolha top-k com pesos estáveis e um sorteio uniforme fornecido pelo chamador."""

from math import exp, fsum, isfinite, nextafter


def selecionar_token_top_k(logits, *, temperatura, k, u):
    """Devolve um ID int; preserva logits e usa somente a uniforme u recebida."""
    valores = tuple(float(valor) for valor in logits)
    if not valores or not all(isfinite(valor) for valor in valores):
        raise ValueError("Informe uma sequência não vazia de logits finitos.")
    if type(k) is not int or not 1 <= k <= len(valores):
        raise ValueError("k deve ser um inteiro entre 1 e o tamanho do vocabulário.")
    if not isfinite(temperatura) or temperatura <= 0:
        raise ValueError("A temperatura deve ser finita e positiva.")
    if not 0 <= u < 1:
        raise ValueError("u deve estar no intervalo [0,1).")

    candidatos = sorted(range(len(valores)), key=lambda i: (-valores[i], i))[:k]
    maior = valores[candidatos[0]]
    pesos = [exp((valores[i] - maior) / temperatura) for i in candidatos]
    total = fsum(pesos)
    # Evita que o produto arredondado coloque u exatamente fora da massa final.
    alvo = min(u * total, nextafter(total, 0.0))
    acumulado = 0.0
    ultimo_positivo = candidatos[0]
    for i, peso in zip(candidatos, pesos):
        if peso > 0:
            ultimo_positivo = i
            acumulado += peso
            if acumulado > alvo:
                return int(i)
    return int(ultimo_positivo)
