"""M08.2: janelas causais, Dataset/DataLoader e MLP pequena em CPU.

Executar na raiz: python notebooks/laboratorio_mlp.py
Autoria opcional: --autoria notebooks/m08_avaliacao_autoral.py
O modo normal esta completo; leia docs/Aula_M08_2_Dataset_MLP.md.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import platform
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
CONTEXT, HORIZON, DELAY = 24, 24, 2
SEEDS = (17, 29, 41)
HIDDEN, DROPOUT = 32, 0.1
BATCH, MAX_EPOCHS, PATIENCE = 128, 60, 8
LR, WEIGHT_DECAY = 0.001, 0.0001
TIME_COLUMNS = ['forecast_origin', 'history_end', 'target_time', 'target_available_at']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gravar_json(path, content):
    Path(path).write_text(json.dumps(content, indent=2, ensure_ascii=False,
                                    allow_nan=False) + '\n', encoding='utf-8')


def montar_janelas(generation, origins):
    """X[i]: 24 horas exatas, da mais antiga a o-2; nenhuma imputacao."""
    lags = np.arange(DELAY + CONTEXT - 1, DELAY - 1, -1)
    # reindex por horario, nao por posicao: uma hora ausente permanece NaN.
    columns = [generation.reindex(origins - pd.Timedelta(hours=int(lag))).to_numpy()
               for lag in lags]
    return np.column_stack(columns).astype(np.float64)[:, :, None]


def carregar(input_dir):
    manifest_path = input_dir / 'manifesto_entrada.json'
    if not manifest_path.is_file():
        raise FileNotFoundError(f'Entrada M07.3 ausente: {manifest_path}. '
                                'Use a mesma pasta dist/databricks/CJU_BA5EIGT/m07_3 do M08.1.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    expected_parameters = {'horizon_hours': 24, 'availability_delay_hours_assumed': 2,
                           'window_hours': 6, 'cutoff': '2026-07-11T06:00:00'}
    if (manifest.get('schema') != 'renewcast-databricks-input-v1'
            or manifest.get('parameters') != expected_parameters):
        raise ValueError('Esta unidade utiliza o pacote M07.3 h24/d2/w6 ja preparado.')
    hashes = {'manifesto_entrada.json': sha(manifest_path)}
    for name in ('geracao.parquet', 'treino_referencia.parquet'):
        path = input_dir / name
        if not path.is_file():
            raise FileNotFoundError(f'Arquivo da entrada M07.3 ausente: {path}')
        expected = manifest['files'][name]
        hashes[name] = sha(path)
        if hashes[name] != expected['sha256'] or path.stat().st_size != expected['bytes']:
            raise ValueError(f'Entrada diferente do seu manifesto: {name}')

    raw = pd.read_parquet(input_dir / 'geracao.parquet')
    frame = pd.read_parquet(input_dir / 'treino_referencia.parquet')
    required = {*TIME_COLUMNS, 'serie', 'features_validas', 'target_generation',
                'geracao_em_history_end'}
    if not {'din_instante', 'val_geracao'}.issubset(raw) or not required.issubset(frame):
        raise ValueError('Colunas da entrada M07.3 incompativeis.')
    if len(raw) != 8760 or len(frame) != 7485 or frame[list(required)].isna().any().any():
        raise ValueError('Esperadas 8760 horas e 7485 origens elegiveis, sem campos obrigatorios ausentes.')
    for data, column in [(raw, 'din_instante'), *[(frame, c) for c in TIME_COLUMNS]]:
        data[column] = pd.to_datetime(data[column], errors='raise')
        if data[column].isna().any() or data[column].dt.tz is not None:
            raise ValueError('Use o eixo sem fuso preservado pelo M07; sem conversao implicita.')
        if not data[column].eq(data[column].dt.floor('h')).all():
            raise ValueError('Timestamps devem estar alinhados a horas inteiras.')
    raw = raw.sort_values('din_instante')
    frame = frame.sort_values('forecast_origin').reset_index(drop=True)
    if raw['din_instante'].duplicated().any() or frame['forecast_origin'].duplicated().any():
        raise ValueError('Instantes duplicados na entrada.')
    for times in (raw['din_instante'], frame['forecast_origin']):
        if not times.diff().dropna().eq(pd.Timedelta(hours=1)).all():
            raise ValueError('O recorte M07.3 deste protocolo deve ter grade horaria completa.')
    origin = frame['forecast_origin']
    if (not frame['serie'].eq('CJU_BA5EIGT').all()
            or not frame['features_validas'].eq(True).all()
            or not frame['history_end'].eq(origin - pd.Timedelta(hours=DELAY)).all()
            or not frame['target_time'].eq(origin + pd.Timedelta(hours=HORIZON)).all()
            or not frame['target_available_at'].eq(origin + pd.Timedelta(hours=HORIZON + DELAY)).all()
            or not (frame['target_available_at'] < pd.Timestamp(expected_parameters['cutoff'])).all()):
        raise ValueError('Fronteiras temporais M07.3 violadas.')
    generation = raw.set_index('din_instante')['val_geracao'].astype(float)
    if np.isinf(generation.to_numpy()).any():
        raise ValueError('Geracao infinita nao e uma medicao valida.')
    x_all = montar_janelas(generation, pd.DatetimeIndex(origin))
    targets = generation.reindex(pd.DatetimeIndex(frame['target_time'])).to_numpy()
    np.testing.assert_allclose(targets, frame['target_generation'].to_numpy(), rtol=0, atol=1e-9)
    np.testing.assert_allclose(x_all[:, -1, 0], frame['geracao_em_history_end'], rtol=0, atol=1e-9)
    mask = np.isfinite(x_all).all(axis=(1, 2)) & np.isfinite(targets)
    excluded = frame.loc[~mask, TIME_COLUMNS].copy().assign(reason='historico_24h_incompleto')
    frame = frame.loc[mask].copy().reset_index(drop=True)
    x, y = x_all[mask], targets[mask, None]
    return frame, x, y, excluded, hashes, manifest


def dividir(frame):
    """Ajuste, selecao de epoca e avaliacao; purga por disponibilidade do rotulo."""
    report_idx = np.arange(len(frame) - 168, len(frame))
    report_start = frame.iloc[report_idx[0]]['forecast_origin']
    before_report = np.flatnonzero((frame['target_available_at'] < report_start).to_numpy())
    select_idx = before_report[-168:]
    select_start = frame.iloc[select_idx[0]]['forecast_origin']
    fit_idx = np.flatnonzero((frame['target_available_at'] < select_start).to_numpy())
    if len(fit_idx) < 1000 or len(select_idx) != 168:
        raise ValueError('Historico insuficiente para a divisao prescrita.')
    assigned = set(fit_idx) | set(select_idx) | set(report_idx)
    excluded_idx = np.array([i for i in range(len(frame)) if i not in assigned], dtype=int)
    parts = {'ajuste': fit_idx, 'selecao': select_idx, 'avaliacao': report_idx,
             'excluidas_disponibilidade': excluded_idx}
    if len(assigned) != len(fit_idx) + len(select_idx) + len(report_idx):
        raise ValueError('Divisoes sobrepostas.')
    assert frame.iloc[fit_idx]['target_available_at'].max() < select_start
    assert frame.iloc[select_idx]['target_available_at'].max() < report_start
    return parts


class JanelasDataset(Dataset):
    """Uma origem e um exemplo; o tempo interno da janela nunca e embaralhado."""
    def __init__(self, x, y):
        if x.ndim != 3 or x.shape[1:] != (CONTEXT, 1) or y.shape != (len(x), 1):
            raise ValueError('Esperados X [n,24,1] e y [n,1].')
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, index):
        return self.x[index], self.y[index]


class MLP(nn.Module):
    """24 entradas -> 32 unidades ReLU -> 1 saida; 833 parametros."""
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(nn.Flatten(start_dim=1), nn.Linear(CONTEXT, HIDDEN),
                                     nn.ReLU(), nn.Dropout(DROPOUT), nn.Linear(HIDDEN, 1))

    def forward(self, x):
        return self.network(x)


def avaliar_lotes_referencia(modelo, loader):
    """MSE por exemplo, inclusive o ultimo lote menor. Preserva o modo de entrada."""
    old_mode = modelo.training
    n, sse = 0, 0.0
    modelo.eval()
    try:
        with torch.no_grad():
            for x, y in loader:
                prediction = modelo(x)
                if prediction.shape != y.shape or y.ndim != 2 or y.shape[1] != 1:
                    raise ValueError('Previsao e alvo devem ter shape [batch,1].')
                error = (prediction - y).double()
                if not torch.isfinite(error).all():
                    raise ValueError('Erro de avaliacao nao finito.')
                sse += error.square().sum().item()
                n += len(y)
    finally:
        modelo.train(old_mode)
    if n == 0:
        raise ValueError('Nao e possivel avaliar um loader vazio.')
    return {'rows': n, 'mse': sse / n}


def loader(dataset, shuffle=False, seed=0):
    return DataLoader(dataset, batch_size=BATCH, shuffle=shuffle, drop_last=False,
                      num_workers=0, generator=torch.Generator().manual_seed(seed))


def treinar(fit_ds, selection_ds, seed, evaluate):
    """Avaliacao final nao entra aqui. Cada seed mantem seu proprio checkpoint."""
    torch.manual_seed(seed)
    model = MLP()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    train_loader = loader(fit_ds, shuffle=True, seed=seed)
    fit_loader, selection_loader = loader(fit_ds), loader(selection_ds)
    best_loss, best_epoch, stale, best_state = float('inf'), 0, 0, None
    curve = []
    start = time.perf_counter()
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        online_sse, seen = 0.0, 0
        for x, y in train_loader:
            optimizer.zero_grad(set_to_none=True)
            prediction = model(x)
            if prediction.shape != y.shape:
                raise ValueError('Broadcasting indevido no treino.')
            loss = (prediction - y).square().mean()
            if not torch.isfinite(loss):
                raise ValueError('Perda nao finita; execucao reprovada.')
            loss.backward()
            optimizer.step()
            online_sse += loss.item() * len(y)
            seen += len(y)
        fit_mse = float(evaluate(model, fit_loader)['mse'])
        select_mse = float(evaluate(model, selection_loader)['mse'])
        if not np.isfinite([fit_mse, select_mse]).all():
            raise ValueError('Avaliador devolveu perda nao finita.')
        improved = select_mse < best_loss
        if improved:
            best_loss, best_epoch, stale = select_mse, epoch, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            stale += 1
        curve.append({'seed': seed, 'epoch': epoch, 'online_train_mse': online_sse / seen,
                      'fit_eval_mse': fit_mse, 'selection_mse': select_mse,
                      'checkpoint_updated': improved, 'examples_seen': seen})
        if epoch == 1 or epoch % 10 == 0 or stale >= PATIENCE:
            print(f'Seed {seed}; epoca {epoch}; ajuste={fit_mse:.5f}; '
                  f'selecao={select_mse:.5f}; melhor={best_epoch}', flush=True)
        if stale >= PATIENCE:
            break
    model.load_state_dict(best_state)
    model.eval()
    metadata = {'seed': seed, 'best_epoch': best_epoch, 'epochs_executed': epoch,
                'best_selection_mse': best_loss, 'training_seconds': time.perf_counter() - start,
                'stop_reason': 'patience' if stale >= PATIENCE else 'max_epochs'}
    return model, curve, metadata


def prever(model, dataset):
    model.eval()
    with torch.no_grad():
        return torch.cat([model(x) for x, _ in loader(dataset)]).numpy().astype(float)


def metricas(y, prediction):
    error = y - prediction
    return {'mae_mwmed': float(np.abs(error).mean()),
            'rmse_mwmed': float(np.sqrt(np.square(error).mean())),
            'bias_observed_minus_predicted_mwmed': float(error.mean())}


def carregar_autoria(path):
    spec = importlib.util.spec_from_file_location('m08_avaliacao_autoral', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.avaliar_lotes


def conferir_avaliador(evaluate):
    """Cinco exemplos em lotes 4+1: MSE correto 20, media de medias errada 50."""
    x = torch.ones(5, 24, 1)
    y = torch.tensor([[1.], [1.], [1.], [1.], [11.]])
    class Toy(nn.Module):
        def __init__(self):
            super().__init__()
            self.scale = nn.Parameter(torch.ones(()))
            self.drop = nn.Dropout(0.5)
        def forward(self, batch):
            if self.training or torch.is_grad_enabled():
                raise ValueError('A avaliacao deve usar eval() e desativar gradientes.')
            return self.drop(batch[:, 0, :]) * self.scale
    toy = Toy()
    toy.scale.grad = torch.tensor(7.0)
    before = {k: v.clone() for k, v in toy.state_dict().items()}
    data = DataLoader(torch.utils.data.TensorDataset(x, y), batch_size=4)
    for mode in (True, False):
        toy.train(mode)
        result = evaluate(toy, data)
        if set(result) != {'rows', 'mse'} or result['rows'] != 5:
            raise ValueError('Devolva exatamente rows e mse com todos os exemplos.')
        np.testing.assert_allclose(result['mse'], 20.0, rtol=0, atol=1e-9)
        if toy.training != mode or toy.scale.grad.item() != 7.0:
            raise ValueError('A avaliacao alterou modo inicial ou gradiente existente.')
        for k, v in toy.state_dict().items():
            torch.testing.assert_close(v, before[k], rtol=0, atol=0)
    empty = DataLoader(torch.utils.data.TensorDataset(x[:0], y[:0]), batch_size=4)
    try:
        evaluate(toy, empty)
    except ValueError:
        pass
    else:
        raise ValueError('Loader vazio deve provocar ValueError.')
    return {'batch_sizes': [4, 1], 'correct_mse': 20.0, 'incorrect_unweighted_mse': 50.0,
            'eval_no_grad_mode_restore_checked': True, 'empty_loader_rejected': True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=ROOT/'dist/databricks/CJU_BA5EIGT/m07_3')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'reports/neural/CJU_BA5EIGT/m08_2_mlp')
    parser.add_argument('--autoria', type=Path)
    args = parser.parse_args(argv)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    evaluate = carregar_autoria(args.autoria) if args.autoria else avaliar_lotes_referencia
    checks = conferir_avaliador(evaluate)
    frame, x, y, incomplete, input_hashes, source = carregar(args.input_dir)
    parts = dividir(frame)
    fit, selection, report = (parts[k] for k in ('ajuste', 'selecao', 'avaliacao'))
    mean_x, scale_x = x[fit].mean(axis=0), x[fit].std(axis=0)
    mean_y, scale_y = float(y[fit].mean()), float(y[fit].std())
    if (scale_x <= 0).any() or scale_y <= 0:
        raise ValueError('Desvio nulo no ajuste.')
    z, target = (x - mean_x) / scale_x, (y - mean_y) / scale_y
    datasets = {k: JanelasDataset(z[idx], target[idx])
                for k, idx in parts.items() if k != 'excluidas_disponibilidade'}
    print('MLP h24/d2: janela 24h; CPU/float32; 3 seeds fixas; ate 60 epocas por seed.', flush=True)
    print('Linhas: ' + ', '.join(f'{k}={len(idx)}' for k, idx in parts.items())
          + f', historico_incompleto={len(incomplete)}', flush=True)
    print('Selecao escolhe a epoca; a ultima semana sera avaliada depois dos checkpoints.', flush=True)
    output = args.output_dir / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False)
    protocol = {'schema': 'renewcast-mlp-protocol-v1', 'horizon_hours': HORIZON,
                'availability_delay_hours_assumed': DELAY, 'context_hours': CONTEXT,
                'seeds': list(SEEDS), 'hidden': HIDDEN, 'dropout': DROPOUT,
                'batch_size': BATCH, 'max_epochs': MAX_EPOCHS, 'patience': PATIENCE,
                'learning_rate': LR, 'weight_decay': WEIGHT_DECAY, 'optimizer': 'AdamW',
                'selection_rule': 'lowest selection MSE; first epoch wins ties; no refit',
                'seed_selection': 'none; report every seed', 'cpu_threads': 2,
                'dtype_mlp': 'float32', 'num_workers': 0, 'drop_last': False,
                'input_sha256': input_hashes, 'code_sha256': sha(__file__),
                'authorship_sha256': sha(args.autoria) if args.autoria else None,
                'report_scope': 'previously explored development week; not untouched holdout'}
    gravar_json(output/'protocol.json', protocol)
    partition = frame[TIME_COLUMNS].copy()
    partition['role'] = ''
    for name, idx in parts.items():
        partition.loc[idx, 'role'] = name
    partition.to_csv(output/'particoes.csv', index=False)
    incomplete.to_csv(output/'origens_sem_janela.csv', index=False)
    windows = frame.iloc[report][TIME_COLUMNS].copy()
    windows['history_start'] = windows['forecast_origin'] - pd.Timedelta(hours=DELAY + CONTEXT - 1)
    windows['history_start_generation'] = x[report, 0, 0]
    windows['history_end_generation'] = x[report, -1, 0]
    windows['target_generation'] = y[report, 0]
    windows.to_csv(output/'janelas_avaliacao.csv', index=False)
    # Baseline linear nos MESMOS 24 lags; solucao de minimos quadrados, sem escolher epoca.
    a_fit = np.column_stack([z[fit, :, 0], np.ones(len(fit))])
    coefficients, _, rank, singular = np.linalg.lstsq(a_fit, target[fit], rcond=None)
    baseline = {'coefficients_standardized': coefficients[:, 0].tolist(), 'rank': int(rank),
                'smallest_singular_value': float(singular[-1]), 'fit_rows': len(fit)}
    gravar_json(output/'linear_24h.json', baseline)
    trained, curves, trained_meta = [], [], []
    for seed in SEEDS:
        model, curve, metadata = treinar(datasets['ajuste'], datasets['selecao'], seed, evaluate)
        checkpoint = {'state_dict': model.state_dict(), 'mean_x': torch.tensor(mean_x),
                      'scale_x': torch.tensor(scale_x), 'mean_y': mean_y, 'scale_y': scale_y,
                      'seed': seed, 'best_epoch': metadata['best_epoch'], 'context': CONTEXT,
                      'hidden': HIDDEN, 'dropout': DROPOUT}
        checkpoint_path = output/f'mlp_seed_{seed}.pt'
        torch.save(checkpoint, checkpoint_path)
        trained.append((seed, model, checkpoint_path))
        curves.extend(curve)
        trained_meta.append(metadata)
    # Somente aqui se calcula desempenho na semana de avaliacao.
    predictions, metrics, reload_differences = [], [], []
    baseline_z = np.column_stack([z[report, :, 0], np.ones(len(report))]) @ coefficients
    methods = [('persistence_d2', None, x[report, -1, :]),
               ('linear_24h', None, baseline_z * scale_y + mean_y)]
    for seed, model, checkpoint_path in trained:
        predicted = prever(model, datasets['avaliacao']) * scale_y + mean_y
        checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=True)
        restored = MLP()
        restored.load_state_dict(checkpoint['state_dict'])
        restored_x = (x[report] - checkpoint['mean_x'].numpy()) / checkpoint['scale_x'].numpy()
        restored_ds = JanelasDataset(restored_x, target[report])
        reloaded = prever(restored, restored_ds) * checkpoint['scale_y'] + checkpoint['mean_y']
        delta = float(np.max(np.abs(predicted - reloaded)))
        np.testing.assert_allclose(predicted, reloaded, rtol=0, atol=1e-5)
        reload_differences.append({'seed': seed, 'max_difference_mwmed': delta})
        methods.append(('mlp_24h', seed, predicted))
    for method, seed, pred in methods:
        metrics.append({'method': method, 'seed': seed, 'rows': len(report), **metricas(y[report], pred)})
        table = frame.iloc[report][TIME_COLUMNS].copy()
        table['method'], table['seed'] = method, seed
        table['target_generation'], table['prediction'] = y[report, 0], pred[:, 0]
        table['absolute_error'] = np.abs(y[report, 0] - pred[:, 0])
        predictions.append(table)
    pd.DataFrame(curves).to_csv(output/'curvas.csv', index=False)
    pd.concat(predictions).to_csv(output/'predictions.csv', index=False)
    summary = pd.DataFrame(metrics)
    summary.to_csv(output/'summary.csv', index=False)
    boundaries = {name: {'rows': len(idx),
                        'origin_start': frame.iloc[idx]['forecast_origin'].min().isoformat(),
                        'origin_end': frame.iloc[idx]['forecast_origin'].max().isoformat(),
                        'latest_target_available_at': frame.iloc[idx]['target_available_at'].max().isoformat()}
                  for name, idx in parts.items() if len(idx)}
    mlp_mae = summary.loc[summary.method.eq('mlp_24h'), 'mae_mwmed']
    result = {'schema': 'renewcast-mlp-result-v1', 'completed': True,
              'python': platform.python_version(), 'torch': str(torch.__version__),
              'platform': platform.platform(), 'numpy': np.__version__, 'pandas': pd.__version__,
              'rows_source_training': len(frame) + len(incomplete), 'excluded_incomplete': len(incomplete),
              'partitions': boundaries, 'parameter_count_mlp': sum(p.numel() for p in trained[0][1].parameters()),
              'fit_input_tensor_bytes_float32': datasets['ajuste'].x.nelement() * 4,
              'memory_scope': 'input tensor only; not peak process memory',
              'training': trained_meta, 'reload': reload_differences, 'evaluator_check': checks,
              'mlp_seed_mae': {'median': float(mlp_mae.median()), 'min': float(mlp_mae.min()),
                               'max': float(mlp_mae.max()), 'not_confidence_interval': True},
              'source_package_id': source['package_id'], 'availability_is_assumed': True,
              'timezone_verified': False, 'operational_approval': False,
              'output_sha256': {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    gravar_json(output/'resultado.json', result)
    print('\nMesmas 168 origens; vies = observado - previsto:')
    print(summary.round(6).to_string(index=False))
    print(f'MLP: mediana MAE entre seeds={mlp_mae.median():.6f}; '
          f'faixa=[{mlp_mae.min():.6f}, {mlp_mae.max():.6f}] MWmed.')
    print('Faixa entre seeds nao e intervalo de confianca. Nenhuma seed escolhida pela avaliacao.')
    print(f'Arquivos: {output.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
