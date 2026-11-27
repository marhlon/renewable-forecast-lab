"""Maior limiar sustentado por uma janela consecutiva inteiramente utilizável."""

import numpy as np


def limite_confirmacao(escores, utilizavel, *, consecutivos):
    """Retorna o maior mínimo e o fim da primeira janela que o alcança."""
    escores = np.asarray(escores, dtype=float)
    utilizavel = np.asarray(utilizavel)
    if escores.ndim != 1 or utilizavel.shape != escores.shape or utilizavel.dtype != bool:
        raise ValueError("Informe vetores 1D do mesmo tamanho e uma máscara booleana.")
    if (isinstance(consecutivos, (bool, np.bool_))
            or not isinstance(consecutivos, (int, np.integer)) or consecutivos < 1):
        raise ValueError("consecutivos deve ser um inteiro positivo.")
    if not np.isfinite(escores[utilizavel]).all():
        raise ValueError("Os escores utilizáveis devem ser finitos.")

    melhor = None
    indice = None
    sequencia = 0
    k = int(consecutivos)
    for fim, valido in enumerate(utilizavel):
        sequencia = sequencia + 1 if valido else 0
        if sequencia < k:
            continue
        minimo = float(min(escores[fim - k + 1:fim + 1]))
        # Não substituir em empate preserva a primeira janela vencedora.
        if melhor is None or minimo > melhor:
            melhor = minimo
            indice = fim

    return {"limiar_maximo": melhor, "indice_confirmacao": indice}
