"""Suporte M08.3: contrato de dados e baselines preservados do M08.2.
Nao executa treinamento ao importar. Fonte registrada no protocolo M08.3.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
CONTEXT, HORIZON, DELAY = 24, 24, 2
HIDDEN, DROPOUT, BATCH = 32, 0.1, 128
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

def loader(dataset, shuffle=False, seed=0):
    return DataLoader(dataset, batch_size=BATCH, shuffle=shuffle, drop_last=False,
                      num_workers=0, generator=torch.Generator().manual_seed(seed))

def metricas(y, prediction):
    error = y - prediction
    return {'mae_mwmed': float(np.abs(error).mean()),
            'rmse_mwmed': float(np.sqrt(np.square(error).mean())),
            'bias_observed_minus_predicted_mwmed': float(error.mean())}
