"""Passo de uma célula GRU, com os pesos na ordem r, z, n do PyTorch."""

import numpy as np


def _sigmoide(valores):
    """Calcula a sigmoide sem exponenciar números positivos grandes."""
    resultado = np.empty_like(valores)
    positivos = valores >= 0
    resultado[positivos] = 1.0 / (1.0 + np.exp(-valores[positivos]))
    exponenciais = np.exp(valores[~positivos])
    resultado[~positivos] = exponenciais / (1.0 + exponenciais)
    return resultado


def passo_gru(x, h, weight_ih, weight_hh, bias_ih, bias_hh):
    """Recebe um lote [B,I] e um estado [B,H]; devolve r, z, n e h [B,H]."""
    x, h, weight_ih, weight_hh, bias_ih, bias_hh = (
        np.asarray(valor, dtype=np.float64)
        for valor in (x, h, weight_ih, weight_hh, bias_ih, bias_hh)
    )
    if x.ndim != 2 or h.ndim != 2:
        raise ValueError("x e h devem ser matrizes [B,I] e [B,H].")
    batch, entradas = x.shape
    unidades = h.shape[1]
    if batch == 0 or entradas == 0 or unidades == 0 or h.shape[0] != batch:
        raise ValueError("Lote, entradas e estado devem ter dimensões compatíveis e positivas.")
    if (
        weight_ih.shape != (3 * unidades, entradas)
        or weight_hh.shape != (3 * unidades, unidades)
        or bias_ih.shape != (3 * unidades,)
        or bias_hh.shape != (3 * unidades,)
    ):
        raise ValueError("Esperados pesos [3H,I], [3H,H] e vieses [3H].")
    if not all(np.isfinite(valor).all() for valor in (x, h, weight_ih, weight_hh, bias_ih, bias_hh)):
        raise ValueError("As entradas da célula devem ser finitas.")

    # Os exemplos estão nas linhas; por isso os pesos entram transpostos.
    termos_entrada = x @ weight_ih.T + bias_ih
    termos_estado = h @ weight_hh.T + bias_hh
    xr, xz, xn = np.split(termos_entrada, 3, axis=1)
    hr, hz, hn = np.split(termos_estado, 3, axis=1)

    r = _sigmoide(xr + hr)
    z = _sigmoide(xz + hz)
    # No PyTorch, r multiplica o termo recorrente já transformado, com seu viés.
    n = np.tanh(xn + r * hn)
    novo_estado = (1.0 - z) * n + z * h
    return {"r": r, "z": z, "n": n, "h": novo_estado}
