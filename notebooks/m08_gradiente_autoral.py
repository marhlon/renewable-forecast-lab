"""Gradiente analitico do MSE para o modelo afim da unidade M08.1.

Transcrita do codigo enviado em 04/11/2026; somente formatacao normalizada.
Usa apenas NumPy e nao modifica os dados nem os parametros recebidos.
"""
import numpy as np

def gradiente_mse(X, y, w, b):
    """Devolve (dw, db) para X [n,2], y [n,1], w [2,1] e b escalar."""
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    w = np.asarray(w, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if X.ndim != 2 or X.shape[1] != 2 or X.shape[0] == 0:
        raise ValueError('X deve ter shape [n,2], com n maior que zero.')
    n = X.shape[0]
    if y.shape != (n, 1) or w.shape != (2, 1) or b.shape != ():
        raise ValueError('Esperados y [n,1], w [2,1] e b escalar.')
    # Residuo = previsto - observado; trocar esse sinal inverte o gradiente.
    residuo = X @ w + b - y
    fator = 2.0 / n
    dw = fator * (X.T @ residuo)
    db = float(fator * np.sum(residuo))
    return dw, db