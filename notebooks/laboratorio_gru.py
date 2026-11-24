"""M08.3: GRU versus MLP, linear, HGB e persistencia nas mesmas origens.

Executar na raiz: python notebooks/laboratorio_gru.py
Somente conferencias sem treino: --verificar
Passo NumPy do aluno, sem repetir treino: --autoria notebooks/m08_gru_autoral.py --verificar
"""
from __future__ import annotations

import argparse
import copy
import html
import json
import platform
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import torch
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from renewable_forecast.neural_gru import GRU24h, avaliar_lotes
import renewable_forecast.neural_gru as neural_module
from m08_3_base import (MLP, JanelasDataset, TIME_COLUMNS, carregar, dividir,
                       loader, metricas, sha, gravar_json)
from m08_3_verificacao import carregar_passo, conferir

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (17, 29, 41)
MAX_EPOCHS, PATIENCE, LR, WEIGHT_DECAY = 60, 8, .001, .0001
HGB_PARAMS = dict(max_iter=200, max_leaf_nodes=15, learning_rate=.05,
                  min_samples_leaf=20, l2_regularization=1.,
                  early_stopping=False, random_state=17)


def treinar(factory, architecture, fit_ds, selection_ds, seed):
    """Recebe somente ajuste/selecao. Nunca recebe a semana de avaliacao."""
    torch.manual_seed(seed)
    model = factory()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    train_loader = loader(fit_ds, shuffle=True, seed=seed)
    fit_loader, select_loader = loader(fit_ds), loader(selection_ds)
    best_loss, best_epoch, stale, best_state = float('inf'), 0, 0, None
    curves = []
    start = time.perf_counter()
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        online_sse, seen = 0., 0
        for x, y in train_loader:
            optimizer.zero_grad(set_to_none=True)
            prediction = model(x)
            if prediction.shape != y.shape:
                raise ValueError('Broadcasting indevido no treino.')
            loss = (prediction - y).square().mean()
            if not torch.isfinite(loss):
                raise ValueError('Perda nao finita; treino interrompido.')
            loss.backward()
            optimizer.step()
            online_sse += loss.item() * len(y)
            seen += len(y)
        fit_mse = avaliar_lotes(model, fit_loader)['mse']
        selection_mse = avaliar_lotes(model, select_loader)['mse']
        improved = selection_mse < best_loss
        if improved:
            best_loss, best_epoch, stale = selection_mse, epoch, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            stale += 1
        curves.append(dict(architecture=architecture, seed=seed, epoch=epoch,
                           online_train_mse=online_sse / seen, fit_eval_mse=fit_mse,
                           selection_mse=selection_mse, checkpoint_updated=improved))
        if epoch == 1 or epoch % 10 == 0 or stale >= PATIENCE:
            print(f'{architecture} seed={seed}; epoca={epoch}; ajuste={fit_mse:.5f}; '
                  f'selecao={selection_mse:.5f}; melhor={best_epoch}', flush=True)
        if stale >= PATIENCE:
            break
    model.load_state_dict(best_state)
    model.eval()
    return model, curves, dict(architecture=architecture, seed=seed, best_epoch=best_epoch,
                              epochs_executed=epoch, best_selection_mse=best_loss,
                              training_seconds=time.perf_counter() - start,
                              parameter_count=sum(p.numel() for p in model.parameters()),
                              stop_reason='patience' if stale >= PATIENCE else 'max_epochs')


def prever(model, dataset):
    model.eval()
    with torch.no_grad():
        return torch.cat([model(x) for x, _ in loader(dataset)]).numpy().astype(float)


def memoria_pico_processo():
    """Pico do processo inteiro; nao e memoria isolada de cada arquitetura."""
    try:
        if sys.platform == 'win32':
            import ctypes
            from ctypes import wintypes
            class Counters(ctypes.Structure):
                _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                    (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
                    'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                    'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
            data = Counters()
            data.cb = ctypes.sizeof(data)
            current = ctypes.WinDLL('kernel32', use_last_error=True).GetCurrentProcess
            current.restype = wintypes.HANDLE
            query = ctypes.WinDLL('psapi', use_last_error=True).GetProcessMemoryInfo
            query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
            query.restype = wintypes.BOOL
            if not query(current(), ctypes.byref(data), data.cb):
                raise OSError(ctypes.get_last_error())
            count = data.PeakWorkingSetSize
            source = 'Windows GetProcessMemoryInfo PeakWorkingSetSize'
        else:
            import resource
            count = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            count *= 1 if sys.platform == 'darwin' else 1024
            source = 'getrusage ru_maxrss'
        return dict(peak_mib=count / 1024**2, source=source,
                    scope='whole process lifetime; not per-model memory', error=None)
    except (ImportError, AttributeError, OSError) as exc:
        return dict(peak_mib=None, source=None, scope='unavailable', error=str(exc))


def relatorio_html(output, summary, curves, result):
    """Relatorio local sem servidor; graficos sao opcionais se matplotlib faltar."""
    plot = ''
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 3, figsize=(13, 6.6), sharex=True, sharey=True)
        for i, architecture in enumerate(('mlp_24h', 'gru_24h')):
            for j, seed in enumerate(SEEDS):
                part = curves[(curves.architecture == architecture) & (curves.seed == seed)]
                ax = axes[i, j]
                ax.plot(part.epoch, part.fit_eval_mse, label='Ajuste em eval()', color='#1d4ed8')
                ax.plot(part.epoch, part.selection_mse, label='Selecao', color='#b45309')
                best = part.loc[part.selection_mse.idxmin()]
                ax.axvline(best.epoch, color='#475569', linestyle=':', linewidth=1)
                ax.set_title(f'{architecture} · semente {seed}')
                ax.grid(alpha=.2)
                if i == 1:
                    ax.set_xlabel('Epoca')
                if j == 0:
                    ax.set_ylabel('MSE padronizado')
        axes[0, 0].legend(fontsize=8)
        fig.suptitle('Pesos fixos por epoca; linha vertical = checkpoint selecionado')
        fig.tight_layout()
        fig.savefig(output / 'curvas.png', dpi=150)
        plt.close(fig)
        plot = '<img src="curvas.png" alt="Curvas de ajuste e selecao das seis redes">'
    except ImportError:
        plot = '<p>matplotlib ausente: use curvas.csv; treino e conferencia preservados.</p>'
    body = f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Renewcast M08.3</title><style>body{{font:16px system-ui;max-width:1200px;margin:32px auto;padding:16px;color:#17223b}}
table{{border-collapse:collapse;font-size:14px}}td,th{{padding:8px;border:1px solid #ccd5e3}}img{{max-width:100%}}
code{{background:#eef2f8;padding:3px}}.note{{border-left:4px solid #b45309;padding:12px;background:#fff7ed}}</style>
<h1>M08.3 — memoria recorrente e comparacao pareada</h1>
<p>Execucao <code>{html.escape(result['run_id'])}</code>. CPU, 2 threads; janela 24h, horizonte 24h, atraso assumido 2h.</p>
<p class="note">Semana de desenvolvimento ja examinada. Nenhuma semente foi escolhida pelo desempenho abaixo.
Esta tabela nao certifica generalizacao, causalidade ou superioridade em outros periodos.</p>
<h2>Mesmas 168 origens de avaliacao</h2>{summary.round(6).to_html(index=False, na_rep='—')}
<h2>Treinamento e selecao</h2>{plot}
<p>O tempo inclui treino e avaliacoes de ajuste/selecao em cada epoca; nao e benchmark controlado entre plataformas.</p>
<p>Memoria: {html.escape(str(result['process_memory']))}</p>
<p>Consulte particoes.csv, janelas_avaliacao.csv, curvas.csv, predictions.csv, protocol.json e resultado.json.</p>
</html>'''
    (output / 'relatorio.html').write_text(body, encoding='utf-8')


def executar(args, output, checks):
    started = time.perf_counter()
    frame, x, y, incomplete, input_hashes, source = carregar(args.input_dir)
    parts = dividir(frame)
    counts = {k: len(idx) for k, idx in parts.items()}
    if counts != dict(ajuste=7079, selecao=168, avaliacao=168, excluidas_disponibilidade=52) or len(incomplete) != 18:
        raise ValueError('A divisao mudou em relacao ao protocolo M08.2.')
    fit, selection, report = (parts[k] for k in ('ajuste', 'selecao', 'avaliacao'))
    mean_x, scale_x = x[fit].mean(axis=0), x[fit].std(axis=0)
    mean_y, scale_y = float(y[fit].mean()), float(y[fit].std())
    if (scale_x <= 0).any() or scale_y <= 0:
        raise ValueError('Desvio nulo no ajuste.')
    z, target = (x - mean_x) / scale_x, (y - mean_y) / scale_y
    datasets = {k: JanelasDataset(z[idx], target[idx]) for k, idx in parts.items()
                if k != 'excluidas_disponibilidade'}
    scalers = dict(mean_x=mean_x.tolist(), scale_x=scale_x.tolist(), mean_y=mean_y,
                   scale_y=scale_y, fitted_on='ajuste only', ddof=0,
                   order='oldest o-25 through newest o-2; one scale per lag, preserved from M08.2')
    versions = dict(python=platform.python_version(), platform=platform.platform(),
                    torch=torch.__version__, numpy=np.__version__, pandas=pd.__version__,
                    sklearn=sklearn.__version__)
    code_paths = [Path(__file__), Path(__file__).with_name('m08_3_base.py'),
                  Path(__file__).with_name('m08_3_verificacao.py'), Path(neural_module.__file__)]
    code_hashes = {p.name: sha(p) for p in code_paths}
    protocol = dict(schema='renewcast-gru-protocol-v1', seeds=list(SEEDS), horizon_hours=24,
                    context_hours=24, availability_delay_hours_assumed=2,
                    fit_rows=7079, selection_rows=168, evaluation_rows=168,
                    excluded_unavailable_rows=52, excluded_incomplete_rows=18,
                    architectures={'mlp': '24->32 ReLU->dropout .1->1; 833 parameters',
                                   'gru': '1 layer, 16 hidden, reset per window, head dropout .1; 929 parameters'},
                    optimizer='AdamW', learning_rate=LR, weight_decay=WEIGHT_DECAY,
                    max_epochs=MAX_EPOCHS, patience=PATIENCE, batch_size=128,
                    cpu_threads=2, dtype_neural='float32', gradient_clipping=False,
                    selection_rule='lowest selection MSE; first epoch wins ties; no refit',
                    seed_selection='none; every prescribed seed is reported',
                    hgb_parameters=HGB_PARAMS, hgb_early_stopping=False,
                    input_sha256=input_hashes, source_package_id=source.get('package_id'),
                    code_sha256=code_hashes, versions=versions,
                    authorship_sha256=sha(args.autoria) if args.autoria else None,
                    scope='previously explored development week; no new untouched holdout',
                    weather_inputs_used=False, physical_timezone_verified=False)
    # Protocolo e fronteiras gravados ANTES do treinamento e das metricas finais.
    gravar_json(output / 'protocol.json', protocol)
    gravar_json(output / 'preprocessing.json', scalers)
    partition = frame[TIME_COLUMNS].copy().assign(role='')
    for role, idx in parts.items():
        partition.loc[idx, 'role'] = role
    partition.to_csv(output / 'particoes.csv', index=False)
    incomplete.to_csv(output / 'origens_sem_janela.csv', index=False)
    windows = frame.iloc[report][TIME_COLUMNS].copy()
    windows['history_start'] = windows.forecast_origin - pd.Timedelta(hours=25)
    windows['history_start_generation'] = x[report, 0, 0]
    windows['history_end_generation'] = x[report, -1, 0]
    windows['target_generation'] = y[report, 0]
    windows.to_csv(output / 'janelas_avaliacao.csv', index=False)
    print('Mesmas origens do M08.2: ajuste=7079, selecao=168, avaliacao=168; exclusoes=52+18.', flush=True)
    print('Treinando MLP e GRU, 3 sementes cada; HGB fixo e linear. Sem novas buscas.', flush=True)
    start = time.perf_counter()
    a = np.column_stack([z[fit, :, 0], np.ones(len(fit))])
    coefficients, _, rank, _ = np.linalg.lstsq(a, target[fit], rcond=None)
    linear_seconds = time.perf_counter() - start
    gravar_json(output / 'linear_24h.json', dict(coefficients=coefficients[:, 0].tolist(), rank=int(rank)))
    hgb = HistGradientBoostingRegressor(**HGB_PARAMS)
    start = time.perf_counter()
    hgb.fit(z[fit, :, 0], target[fit, 0])
    hgb_seconds = time.perf_counter() - start
    joblib.dump(hgb, output / 'hgb_24h.joblib')
    trained, curves, training = [], [], []
    factories = {'mlp_24h': MLP, 'gru_24h': GRU24h}
    for architecture, factory in factories.items():
        for seed in SEEDS:
            model, curve, metadata = treinar(factory, architecture, datasets['ajuste'], datasets['selecao'], seed)
            checkpoint_path = output / f'{architecture}_seed_{seed}.pt'
            checkpoint = dict(schema='renewcast-neural-checkpoint-v1', architecture=architecture,
                              state_dict=model.state_dict(), mean_x=torch.tensor(mean_x),
                              scale_x=torch.tensor(scale_x), mean_y=mean_y, scale_y=scale_y,
                              context=24, horizon=24, delay_assumed=2, hidden_size=16 if architecture=='gru_24h' else 32,
                              dropout=.1, seed=seed, best_epoch=metadata['best_epoch'])
            torch.save(checkpoint, checkpoint_path)
            trained.append((architecture, seed, model, checkpoint_path, metadata))
            training.append(metadata)
            curves.extend(curve)
    # Avaliacao final somente depois de fixar todos os checkpoints.
    baseline_z = np.column_stack([z[report, :, 0], np.ones(len(report))]) @ coefficients
    hgb_z = hgb.predict(z[report, :, 0])[:, None]
    loaded_hgb = joblib.load(output / 'hgb_24h.joblib')
    np.testing.assert_array_equal(loaded_hgb.predict(z[report, :, 0])[:, None], hgb_z)
    loaded_coefficients = np.array(json.loads((output / 'linear_24h.json').read_text())['coefficients'])[:, None]
    np.testing.assert_array_equal(loaded_coefficients, coefficients)
    methods = [('persistence_d2', None, x[report, -1, :], None, 0.),
               ('linear_24h', None, baseline_z * scale_y + mean_y, 25, linear_seconds),
               ('hgb_24h', 17, hgb_z * scale_y + mean_y, None, hgb_seconds)]
    reload_checks = []
    for architecture, seed, model, path, metadata in trained:
        predicted = prever(model, datasets['avaliacao']) * scale_y + mean_y
        checkpoint = torch.load(path, map_location='cpu', weights_only=True)
        restored = factories[architecture]()
        restored.load_state_dict(checkpoint['state_dict'])
        restored_x = (x[report] - checkpoint['mean_x'].numpy()) / checkpoint['scale_x'].numpy()
        restored_ds = JanelasDataset(restored_x, np.zeros((len(report), 1)))
        again = prever(restored, restored_ds) * checkpoint['scale_y'] + checkpoint['mean_y']
        difference = float(np.max(np.abs(predicted - again)))
        np.testing.assert_allclose(predicted, again, rtol=0, atol=1e-6)
        reload_checks.append(dict(architecture=architecture, seed=seed, max_difference_mwmed=difference))
        metadata['checkpoint_bytes'] = path.stat().st_size
        metadata['parameter_bytes_float32'] = metadata['parameter_count'] * 4
        methods.append((architecture, seed, predicted, metadata['parameter_count'], metadata['training_seconds']))
    predictions, summaries = [], []
    for method, seed, predicted, parameters, seconds in methods:
        if predicted.shape != (168, 1) or not np.isfinite(predicted).all():
            raise ValueError('Previsao com dimensao ou valores invalidos.')
        metrics = metricas(y[report], predicted)
        summaries.append(dict(method=method, seed=seed, rows=168, **metrics,
                              parameters=parameters, training_seconds=seconds))
        rows = windows.copy().assign(method=method, seed=seed, prediction=predicted[:, 0])
        rows['absolute_error'] = np.abs(rows.target_generation - rows.prediction)
        rows['squared_error'] = (rows.target_generation - rows.prediction)**2
        predictions.append(rows)
    summary, curves = pd.DataFrame(summaries), pd.DataFrame(curves)
    prediction_frame = pd.concat(predictions, ignore_index=True)
    summary.to_csv(output / 'summary.csv', index=False)
    prediction_frame.to_csv(output / 'predictions.csv', index=False)
    curves.to_csv(output / 'curvas.csv', index=False)
    medians = []
    for architecture in factories:
        values = summary.loc[summary.method.eq(architecture), 'mae_mwmed']
        medians.append(dict(architecture=architecture, median_mae=float(values.median()),
                            min_mae=float(values.min()), max_mae=float(values.max()),
                            interpretation='seed range, not confidence interval or ensemble'))
    for name, expected in input_hashes.items():
        if sha(args.input_dir / name) != expected:
            raise ValueError(f'Entrada mudou durante a execucao: {name}')
    result = dict(schema='renewcast-gru-result-v1', completed=True, run_id=output.name,
                  checks=checks, partition_counts=counts, excluded_incomplete=len(incomplete),
                  input_sha256=input_hashes, source_package_id=source.get('package_id'),
                  code_sha256=code_hashes, environment=versions, training=training,
                  reload_checks=reload_checks, reload_tolerance_mwmed=1e-6,
                  neural_seed_summary=medians, process_memory=memoria_pico_processo(),
                  elapsed_seconds=time.perf_counter() - started,
                  availability_is_assumed=True, physical_timezone_verified=False,
                  operational_policy_approved=False, heldout_test_used=False,
                  scope=protocol['scope'])
    relatorio_html(output, summary, curves, result)
    result['output_sha256'] = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    gravar_json(output / 'resultado.json', result)
    gravar_json(args.output_dir / 'latest_run.json', dict(run_id=output.name, directory=str(output.resolve()),
                                                       resultado_sha256=sha(output / 'resultado.json')))
    print('\nMESMAS 168 ORIGENS; MWmed; vies = observado - previsto', flush=True)
    print(summary.round(6).to_string(index=False), flush=True)
    for row in medians:
        print(f"{row['architecture']}: MAE mediano={row['median_mae']:.6f}; "
              f"faixa de sementes={row['min_mae']:.6f}--{row['max_mae']:.6f}.")
    print('Conferencias e recarregamentos aprovados. Isso nao aprova o desempenho preditivo.')
    print(f'Resultados: {output.resolve()}')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=ROOT / 'dist/databricks/CJU_BA5EIGT/m07_3')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'reports/neural/CJU_BA5EIGT/m08_3_gru')
    parser.add_argument('--autoria', type=Path)
    parser.add_argument('--verificar', action='store_true', help='Confere portas/estado/avaliador sem dados nem treino.')
    args = parser.parse_args(argv)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    args.input_dir, args.output_dir = args.input_dir.resolve(), args.output_dir.resolve()
    output = args.output_dir / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False)
    try:
        checks = conferir(carregar_passo(args.autoria))
        if args.verificar:
            checks['authorship_sha256'] = sha(args.autoria) if args.autoria else None
            gravar_json(output / 'conferencia_sem_treino.json', checks)
            print(f"Conferencia aprovada: {checks['checks_count']} grupos; portas, estado e avaliador.")
            print(f'Sem treino. Recibo: {output / "conferencia_sem_treino.json"}')
        else:
            with threadpool_limits(limits=2):
                executar(args, output, checks)
    except Exception as exc:
        gravar_json(output / 'failure.json', dict(completed=False, error_type=type(exc).__name__, error=str(exc)))
        raise


if __name__ == '__main__':
    main()
