"""Conferencias pequenas de semantica; nao treinam modelos nem leem a serie."""
from __future__ import annotations

import importlib.util
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from renewable_forecast.neural_gru import GRU24h, avaliar_lotes


def passo_gru_referencia(x, h, weight_ih, weight_hh, bias_ih, bias_hh):
    """Referencia NumPy: exemplos em linhas; blocos das matrizes na ordem r,z,n."""
    a = x @ weight_ih.T + bias_ih
    c = h @ weight_hh.T + bias_hh
    ar, az, an = np.split(a, 3, axis=1)
    cr, cz, cn = np.split(c, 3, axis=1)
    # tanh evita overflow numerico de exp para a sigmoide desta referencia.
    sigmoid = lambda v: 0.5 * (1.0 + np.tanh(0.5 * v))
    r, z = sigmoid(ar + cr), sigmoid(az + cz)
    n = np.tanh(an + r * cn)
    return {'r': r, 'z': z, 'n': n, 'h': (1.0 - z) * n + z * h}


def carregar_passo(path):
    if path is None:
        return passo_gru_referencia
    if not path.is_file():
        raise FileNotFoundError(f'Funcao autoral nao encontrada: {path}')
    spec = importlib.util.spec_from_file_location('m08_gru_autoral', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, 'passo_gru', None)):
        raise ValueError('O arquivo deve definir passo_gru(x,h,weight_ih,weight_hh,bias_ih,bias_hh).')
    return module.passo_gru


def conferir(passo=None):
    """Falha antes do treino se estado, broadcasting, avaliacao ou portas divergirem."""
    passo = passo or passo_gru_referencia
    torch.manual_seed(501)
    rng = np.random.default_rng(501)
    checks = []
    differences = []
    for batch, inputs, hidden in ((1, 1, 1), (4, 1, 3), (3, 2, 5)):
        cell = nn.GRUCell(inputs, hidden).double()
        arrays = [rng.normal(size=(batch, inputs)), rng.normal(size=(batch, hidden))]
        arrays += [p.detach().numpy().copy() for p in cell.parameters()]
        saved = [a.copy() for a in arrays]
        for array in arrays:
            array.setflags(write=False)
        actual = passo(*arrays)
        expected = passo_gru_referencia(*arrays)
        if not isinstance(actual, dict) or set(actual) != {'r', 'z', 'n', 'h'}:
            raise ValueError('passo_gru deve devolver exatamente r, z, n, h.')
        for key in expected:
            value = np.asarray(actual[key])
            if value.shape != (batch, hidden) or not np.isfinite(value).all():
                raise ValueError(f'Shape ou finitude incorretos em {key}.')
            np.testing.assert_allclose(value, expected[key], rtol=0, atol=1e-12)
        with torch.no_grad():
            reference = cell(torch.tensor(arrays[0]), torch.tensor(arrays[1])).numpy()
        differences.append(float(np.max(np.abs(actual['h'] - reference))))
        np.testing.assert_allclose(actual['h'], reference, rtol=0, atol=1e-12)
        for a, b in zip(arrays, saved):
            np.testing.assert_array_equal(a, b)
    checks.append('portas_numpy_vs_grucell_e_entradas_preservadas')

    gru = nn.GRU(1, 3, batch_first=True).double()
    sequence = rng.normal(size=(2, 24, 1))
    params = [p.detach().numpy().copy() for p in gru.parameters()]
    state = np.zeros((2, 3))
    trace = []
    for t in range(24):
        state = passo(sequence[:, t, :], state, *params)['h']
        trace.append(state)
    with torch.no_grad():
        output, last = gru(torch.tensor(sequence))
    np.testing.assert_allclose(np.stack(trace, axis=1), output.numpy(), rtol=0, atol=1e-12)
    np.testing.assert_allclose(state, last[-1].numpy(), rtol=0, atol=1e-12)
    checks.append('vinte_quatro_passos_numpy_vs_gru')

    model = GRU24h().eval()
    x = torch.randn(5, 24, 1)
    with torch.no_grad():
        before = model(x)
        model(torch.randn_like(x) * 10)
        after = model(x)
        split = torch.cat([model(x[:4]), model(x[4:])])
        permutation = torch.tensor([4, 1, 3, 0, 2])
        permuted = model(x[permutation])
        outputs, hidden = model.gru(x)
    assert before.shape == (5, 1) and sum(p.numel() for p in model.parameters()) == 929
    torch.testing.assert_close(before, after, rtol=0, atol=0)
    torch.testing.assert_close(before, split, rtol=0, atol=1e-6)
    torch.testing.assert_close(before[permutation], permuted, rtol=0, atol=1e-6)
    torch.testing.assert_close(outputs[:, -1], hidden[-1], rtol=0, atol=0)
    checks += ['estado_reiniciado_entre_chamadas', 'ordem_do_lote_nao_muda_previsao',
               'ultimo_lote_e_ultimo_estado', 'gru_929_parametros']
    for bad in (torch.ones(2, 24), torch.ones(2, 23, 1), torch.ones(0, 24, 1)):
        try:
            model(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Shape invalido foi aceito pela GRU.')
    checks.append('shapes_invalidos_rejeitados')

    class Toy(nn.Module):
        def __init__(self):
            super().__init__()
            self.scale = nn.Parameter(torch.ones(()))
            self.drop = nn.Dropout(.5)
        def forward(self, batch):
            if self.training or self.drop.training or torch.is_grad_enabled():
                raise AssertionError('Avaliacao nao desativou treino ou gradientes.')
            return self.drop(batch) * self.scale
    toy = Toy().train()
    toy.drop.eval()  # Configuracao mista que deve ser restaurada.
    toy.scale.grad = torch.tensor(7.)
    modes = [m.training for m in toy.modules()]
    parameters = {k: v.clone() for k, v in toy.state_dict().items()}
    good = DataLoader(TensorDataset(torch.ones(5, 1), torch.tensor([[1.]] * 4 + [[11.]])), batch_size=4)
    assert avaliar_lotes(toy, good) == {'rows': 5, 'mse': 20.0}
    assert modes == [m.training for m in toy.modules()]
    for invalid in ([], [(torch.ones(2, 1), torch.ones(2))],
                    [(torch.ones(1, 1), torch.tensor([[float('nan')]]))],
                    [(torch.ones(1, 1, dtype=torch.float64), torch.tensor([[1e308]], dtype=torch.float64))]):
        try:
            avaliar_lotes(toy, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Avaliador aceitou vazio, shape errado ou erro nao finito.')
        assert modes == [m.training for m in toy.modules()]
    assert toy.scale.grad.item() == 7.
    for key, value in toy.state_dict().items():
        torch.testing.assert_close(value, parameters[key], rtol=0, atol=0)
    checks += ['avaliador_4_mais_1_mse20', 'avaliador_modos_mistos_e_excecoes',
               'avaliador_preserva_pesos_e_gradientes', 'avaliador_rejeita_vazio_shape_nan_overflow']
    return {'passed': True, 'checks': checks, 'checks_count': len(checks),
            'max_grucell_difference': max(differences), 'tolerance_grucell': 1e-12,
            'training_uses': 'torch.nn.GRU and autograd; numpy step is a separate semantic check'}
