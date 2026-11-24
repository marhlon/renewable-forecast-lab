"""Confirma sequências na grade e marca somente o início disponível do alarme."""

import numpy as np


def iniciar_alarmes(escores, utilizavel, *, limiar, consecutivos):
    """Devolve um booleano por instante, preservando a grade e as entradas."""
    escores = np.asarray(escores, dtype=float)
    utilizavel = np.asarray(utilizavel, dtype=bool)
    inicios = np.zeros(escores.shape, dtype=bool)
    contagem = 0

    for i in range(len(escores)):
        if utilizavel[i] and escores[i] >= limiar:
            contagem += 1
            if contagem == consecutivos:
                inicios[i] = True
        else:
            contagem = 0

    return inicios
