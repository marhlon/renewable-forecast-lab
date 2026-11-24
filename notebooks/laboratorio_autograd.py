"""M08.1: tensores, gradiente e otimizacao sobre o treino real aceito em M07.

Executar: python notebooks/laboratorio_autograd.py
Opcional: --autoria notebooks/m08_gradiente_autoral.py
O modo normal esta completo. Nenhum Docker, Spark, Databricks ou GPU e usado.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ['geracao_em_history_end', 'media_historico_mwmed']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mse(pred, target):
    """A dimensao explicita evita broadcasting silencioso [n,1] - [n]."""
    if pred.ndim != 2 or pred.shape[1] != 1 or pred.shape != target.shape:
        raise ValueError(f'MSE exige duas matrizes [n,1]; recebeu {pred.shape} e {target.shape}.')
    return ((pred - target) ** 2).mean()


def gradiente_referencia(X, y, w, b):
    """Derivada analitica do MSE: NumPy, sem autograd."""
    erro = X @ w + b - y
    return (2.0 / len(X)) * X.T @ erro, float(2.0 * erro.mean())


def gradiente_autograd(X, y, w, b):
    x_t = torch.tensor(X, dtype=torch.float64)
    y_t = torch.tensor(y, dtype=torch.float64)
    w_t = torch.tensor(w, dtype=torch.float64, requires_grad=True)
    b_t = torch.tensor(float(b), dtype=torch.float64, requires_grad=True)
    loss = mse(x_t @ w_t + b_t, y_t)
    loss.backward()
    return w_t.grad.detach().numpy().copy(), b_t.grad.item(), loss.item()


def diferencas_finitas(X, y, w, b, epsilon=1e-6):
    """Perturba cada parametro; confere a derivada sem reutilizar sua formula."""
    def objective(weights, bias):
        return float(np.mean((X @ weights + bias - y) ** 2))
    dw = np.empty_like(w)
    for j in range(len(w)):
        plus, minus = w.copy(), w.copy()
        plus[j, 0] += epsilon
        minus[j, 0] -= epsilon
        dw[j, 0] = (objective(plus, b) - objective(minus, b)) / (2 * epsilon)
    db = (objective(w, b + epsilon) - objective(w, b - epsilon)) / (2 * epsilon)
    return dw, db


def conferir_gradientes(X, y, function):
    cases = [
        ('manual', np.eye(2), np.array([[1.0], [2.0]]), np.zeros((2, 1)), 0.0),
        ('oito_linhas_reais', X[:8], y[:8], np.array([[.15], [-.10]]), .05),
    ]
    results = []
    for name, x, target, w, b in cases:
        expected_w, expected_b, loss = gradiente_autograd(x, target, w, b)
        # Copias: uma funcao autoral nao pode mudar os dados usados pela conferencia.
        got_w, got_b = function(x.copy(), target.copy(), w.copy(), float(b))
        got_w = np.asarray(got_w, dtype=float)
        got_b = np.asarray(got_b, dtype=float)
        if got_w.shape != w.shape or got_b.shape != ():
            raise ValueError('A autoria deve devolver dw com shape [2,1] e db escalar.')
        finite_w, finite_b = diferencas_finitas(x, target, w, b)
        np.testing.assert_allclose(got_w, expected_w, rtol=1e-7, atol=1e-8)
        np.testing.assert_allclose(got_b, expected_b, rtol=1e-7, atol=1e-8)
        np.testing.assert_allclose(finite_w, expected_w, rtol=1e-6, atol=1e-8)
        np.testing.assert_allclose(finite_b, expected_b, rtol=1e-6, atol=1e-8)
        results.append({'case': name, 'loss': loss, 'dw': expected_w.tolist(),
                        'db': expected_b, 'analytic_max_difference': float(max(
                            np.max(np.abs(got_w - expected_w)), abs(float(got_b) - expected_b))),
                        'finite_difference_max_error': float(max(
                            np.max(np.abs(finite_w - expected_w)), abs(finite_b - expected_b)))})
    np.testing.assert_allclose(results[0]['dw'], [[-1.0], [-2.0]])
    assert results[0]['loss'] == 2.5 and results[0]['db'] == -3.0
    return results


def demonstrar_armadilhas():
    x = torch.eye(2, dtype=torch.float64)
    target = torch.tensor([[1.0], [2.0]], dtype=torch.float64)
    w = torch.zeros((2, 1), dtype=torch.float64, requires_grad=True)
    b = torch.zeros((), dtype=torch.float64, requires_grad=True)
    mse(x @ w + b, target).backward()
    first = w.grad.clone()
    # Nova passagem forward, mesmos parametros; .grad ainda contem a primeira soma.
    mse(x @ w + b, target).backward()
    torch.testing.assert_close(w.grad, 2 * first)
    accumulated = w.grad.tolist()
    w.grad = b.grad = None
    mse(x @ w + b, target).backward()
    torch.testing.assert_close(w.grad, first)
    with torch.no_grad():
        w -= .1 * w.grad
        b -= .1 * b.grad
        after = mse(x @ w + b, target).item()
        wrong_shape = list(((x @ w + b) - target[:, 0]).shape)
    try:
        mse(x @ w + b, target[:, 0])
    except ValueError:
        rejected = True
    else:
        raise AssertionError('Broadcasting indevido nao foi rejeitado.')
    assert math.isclose(after, 1.305, rel_tol=1e-12)
    return {'first_dw': first.tolist(), 'accumulated_dw': accumulated,
            'mse_before_step': 2.5, 'mse_after_step_lr_0p1': after,
            'incorrect_broadcast_shape': wrong_shape, 'incorrect_shape_rejected': rejected}


def carregar(input_dir):
    manifest_path = input_dir / 'manifesto_entrada.json'
    path = input_dir / 'treino_referencia.parquet'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('schema') != 'renewcast-databricks-input-v1':
        raise ValueError('Use o pacote de entrada M07.3, ja preparado no projeto.')
    expected = manifest['files']['treino_referencia.parquet']
    if sha(path) != expected['sha256'] or path.stat().st_size != expected['bytes']:
        raise ValueError('Treino diferente do manifesto M07.3.')
    params = manifest['parameters']
    if params != {'horizon_hours': 24, 'availability_delay_hours_assumed': 2,
                  'window_hours': 6, 'cutoff': '2026-07-11T06:00:00'}:
        raise ValueError('Esta aula utiliza o recorte h24/d2/w6 aceito.')
    frame = pd.read_parquet(path)
    required = ['serie', 'forecast_origin', 'history_end', 'target_time',
                'target_available_at', 'features_validas', *FEATURES, 'target_generation']
    if not set(required).issubset(frame.columns) or len(frame) != 7485:
        raise ValueError('Esperado treino M07.3 com 7.485 linhas e contrato temporal.')
    if frame[required].isna().any().any() or not frame['serie'].eq('CJU_BA5EIGT').all():
        raise ValueError('Ausentes ou conjunto diferente na entrada.')
    for col in ['forecast_origin', 'history_end', 'target_time', 'target_available_at']:
        frame[col] = pd.to_datetime(frame[col], errors='raise')
        if frame[col].dt.tz is not None:
            raise ValueError('M07 preservou timestamps sem fuso; nao converter implicitamente.')
    frame = frame.sort_values('forecast_origin').reset_index(drop=True)
    origin = frame['forecast_origin']
    if origin.duplicated().any() or not origin.diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError('Origens devem ser unicas e horarias neste recorte.')
    if (not frame['features_validas'].eq(True).all()
        or not (frame['history_end'] == origin - pd.Timedelta(hours=2)).all()
        or not (frame['target_time'] == origin + pd.Timedelta(hours=24)).all()
        or not (frame['target_available_at'] == origin + pd.Timedelta(hours=26)).all()
        or not (frame['target_available_at'] < pd.Timestamp(params['cutoff'])).all()):
        raise ValueError('Contrato temporal de M07.3 violado.')
    if not np.isfinite(frame[[*FEATURES, 'target_generation']].to_numpy(dtype=float)).all():
        raise ValueError('Features e alvos devem ser finitos.')
    # As ultimas 168 emissoes sao validacao de desenvolvimento, ja examinada no projeto.
    valid = frame.tail(168).copy()
    cutoff = valid['forecast_origin'].min()
    fit = frame.loc[frame['target_available_at'] < cutoff].copy()
    excluded = frame.loc[(frame['forecast_origin'] < cutoff)
                         & (frame['target_available_at'] >= cutoff)].copy()
    if (len(fit), len(excluded), len(valid)) != (7291, 26, 168):
        raise ValueError('Divisao inesperada: esperadas 7291/26/168 linhas.')
    return fit, valid, excluded, manifest, {'manifesto_entrada.json': sha(manifest_path),
                                          'treino_referencia.parquet': sha(path)}


def metricas(y, prediction):
    residual = y - prediction
    return {'mae_mwmed': float(np.mean(np.abs(residual))),
            'rmse_mwmed': float(np.sqrt(np.mean(residual**2))),
            'signed_bias_observed_minus_predicted': float(np.mean(residual))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=ROOT/'dist/databricks/CJU_BA5EIGT/m07_3')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'reports/neural/CJU_BA5EIGT/m08_1_autograd')
    parser.add_argument('--learning-rate', type=float, default=.05)
    parser.add_argument('--steps', type=int, default=400)
    parser.add_argument('--autoria', type=Path, help='Arquivo com gradiente_mse(X,y,w,b); retorna dw,db sem torch/autograd.')
    args = parser.parse_args(argv)
    if not math.isfinite(args.learning_rate) or args.learning_rate <= 0 or not 1 <= args.steps <= 2000:
        parser.error('learning-rate deve ser finito e positivo; steps entre 1 e 2000.')
    torch.set_num_threads(2)
    torch.manual_seed(73)
    fit, valid, excluded, manifest, hashes = carregar(args.input_dir)
    x_raw = fit[FEATURES].to_numpy(dtype=float)
    y_raw = fit[['target_generation']].to_numpy(dtype=float)
    mean_x, scale_x = x_raw.mean(axis=0), x_raw.std(axis=0, ddof=0)
    mean_y, scale_y = float(y_raw.mean()), float(y_raw.std(ddof=0))
    if (scale_x <= 0).any() or scale_y <= 0:
        raise ValueError('Escala nula: reveja o recorte de ajuste.')
    X, y = (x_raw - mean_x) / scale_x, (y_raw - mean_y) / scale_y
    author_function, author_sha = gradiente_referencia, None
    if args.autoria:
        author_path = args.autoria.resolve(strict=True)
        spec = importlib.util.spec_from_file_location('m08_autoria', author_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        author_function, author_sha = module.gradiente_mse, sha(author_path)
    gradients = conferir_gradientes(X, y, author_function)
    pitfalls = demonstrar_armadilhas()
    x_t, y_t = torch.tensor(X, dtype=torch.float64), torch.tensor(y, dtype=torch.float64)
    w = torch.zeros((2, 1), dtype=torch.float64, requires_grad=True)
    b = torch.zeros((), dtype=torch.float64, requires_grad=True)
    optimizer = torch.optim.SGD([w, b], lr=args.learning_rate)
    # L(theta) = ||A theta-y||^2/n; Hessiana H = 2 A.T A / n.
    A = np.column_stack([X, np.ones(len(X))])
    hessian = 2 * A.T @ A / len(A)
    stability_limit = float(2 / np.linalg.eigvalsh(hessian).max())
    curve = []
    started = time.perf_counter()
    training_state = 'completed'
    for step in range(args.steps + 1):
        prediction = x_t @ w + b
        loss = mse(prediction, y_t)
        if not torch.isfinite(loss):
            training_state = 'nonfinite_loss'
            break
        curve.append({'step': step, 'fit_mse_standardized': loss.item()})
        if step == args.steps:
            break
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    elapsed = time.perf_counter() - started
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    output = args.output_dir / run_id
    output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(curve).to_csv(output/'curva_treino.csv', index=False)
    results = {'schema': 'renewcast-autograd-m08-1-v1', 'run_id': run_id,
        'training_state': training_state, 'code_sha256': sha(Path(__file__)), 'input_sha256': hashes,
        'source_package_id': manifest['package_id'], 'torch_version': str(torch.__version__),
        'python_version': platform.python_version(), 'device': 'cpu', 'dtype': 'float64',
        'threads': 2, 'feature_columns': FEATURES, 'shapes': {'X': list(x_t.shape), 'y': list(y_t.shape), 'w': list(w.shape), 'b': list(b.shape)},
        'split': {'fit_rows': len(fit), 'excluded_rows': len(excluded), 'validation_rows': len(valid),
                  'validation_origin_start': str(valid['forecast_origin'].min()),
                  'fit_last_target_available_at': str(fit['target_available_at'].max()),
                  'validation_origin_end': str(valid['forecast_origin'].max())},
        'normalization_fit_only': True, 'learning_rate': args.learning_rate,
        'quadratic_stability_upper_bound': stability_limit, 'requested_steps': args.steps,
        'completed_steps': curve[-1]['step'], 'optimization_seconds': elapsed,
        'gradient_checks': gradients, 'pitfalls': pitfalls, 'authorship_file_sha256': author_sha,
        'authorship_checked': author_sha is not None,
        'validation_used_for_early_stopping': False,
        'evaluation_scope': 'single previously explored development week; not a new untouched holdout',
        'availability_is_assumed': True, 'operational_model_approved': False}
    if training_state == 'completed':
        valid_x = (valid[FEATURES].to_numpy(dtype=float) - mean_x) / scale_x
        with torch.no_grad():
            predicted = ((torch.tensor(valid_x, dtype=torch.float64) @ w + b) * scale_y + mean_y).numpy().reshape(-1)
        actual = valid['target_generation'].to_numpy(dtype=float)
        baseline = valid[FEATURES[0]].to_numpy(dtype=float)
        # Minimos quadrados no mesmo ajuste: verifica otimizacao, nao escolhe modelo no futuro.
        least_squares = np.linalg.lstsq(A, y, rcond=None)[0]
        optimum_loss = float(np.mean((A @ least_squares - y)**2))
        results['fit_mse_standardized_final'] = curve[-1]['fit_mse_standardized']
        results['least_squares_fit_mse'] = optimum_loss
        results['optimization_gap'] = curve[-1]['fit_mse_standardized'] - optimum_loss
        results['validation_metrics'] = {'linear_autograd': metricas(actual, predicted),
                                          'persistence_d2': metricas(actual, baseline)}
        state = {'weight': w.detach().clone(), 'bias': b.detach().clone(),
                 'mean_x': mean_x.tolist(), 'scale_x': scale_x.tolist(),
                 'mean_y': mean_y, 'scale_y': scale_y, 'feature_columns': FEATURES}
        torch.save(state, output/'linear_state.pt')
        recovered = torch.load(output/'linear_state.pt', map_location='cpu', weights_only=True)
        with torch.no_grad():
            reloaded_x = (valid[FEATURES].to_numpy(dtype=float) - np.array(recovered['mean_x'])) / np.array(recovered['scale_x'])
            reloaded = ((torch.tensor(reloaded_x, dtype=torch.float64) @ recovered['weight'] + recovered['bias']) * recovered['scale_y'] + recovered['mean_y']).numpy().reshape(-1)
        np.testing.assert_allclose(reloaded, predicted, rtol=0, atol=1e-12)
        results['reload_max_absolute_difference'] = float(np.max(np.abs(reloaded - predicted)))
        predictions = valid[['forecast_origin', 'target_time', 'target_available_at', 'target_generation']].copy()
        predictions['prediction_linear'] = predicted
        predictions['prediction_persistence_d2'] = baseline
        predictions.to_csv(output/'predictions.csv', index=False)
    results['output_sha256'] = {p.name: sha(p) for p in output.iterdir() if p.is_file()}
    (output/'resultado.json').write_text(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(f'Ajuste={len(fit)}; excluidas por disponibilidade={len(excluded)}; validacao={len(valid)}')
    print(f'Tensores X={tuple(x_t.shape)}, y={tuple(y_t.shape)}, w={tuple(w.shape)}, b=escalar')
    print('Gradiente analitico, autograd e diferencas finitas: conferidos.')
    print(f'Caso manual: MSE 2.5 -> {pitfalls["mse_after_step_lr_0p1"]:.3f}; broadcasting e acumulacao demonstrados.')
    print(f'Taxa={args.learning_rate}; limite teorico estrito da quadratica={stability_limit:.6f}; estado={training_state}')
    if training_state == 'completed':
        print(json.dumps(results['validation_metrics'], indent=2))
        print(f'Distancia ao minimo quadratico no ajuste: {results["optimization_gap"]:.8g}')
    print('Validacao de desenvolvimento ja explorada; nao e novo teste final.')
    print(f'Arquivos: {output.resolve()}')
    return 0 if training_state == 'completed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
