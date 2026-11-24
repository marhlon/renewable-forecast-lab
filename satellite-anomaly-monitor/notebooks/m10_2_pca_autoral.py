"""Erro de reconstrução por instante, usando o PCA já ajustado."""

import numpy as np


def erro_pca_por_amostra(x, centro, componentes):
    """Recebe x [n,p], centro [p], componentes [k,p] e devolve escores [n]."""
    x = np.asarray(x, dtype=float)
    centro = np.asarray(centro, dtype=float)
    componentes = np.asarray(componentes, dtype=float)

    centrado = x - centro
    coordenadas = centrado @ componentes.T  # [n,k]
    reconstruido = coordenadas @ componentes + centro  # [n,p]
    residuo = x - reconstruido
    return np.square(residuo).sum(axis=1)
