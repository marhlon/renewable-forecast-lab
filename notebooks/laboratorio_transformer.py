from __future__ import annotations

import argparse
import hashlib
import html
import json
import platform
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch

import renewable_forecast.transformer_blocks as blocks_module
from renewable_forecast.transformer_blocks import TransformerDidatico, sinusoidal_positions
import m09_transformer_verificacao as verification_module
from m09_transformer_verificacao import conferir

ROOT = Path(__file__).resolve().parents[1]
MODEL_CONFIG = dict(input_size=1, d_model=16, n_heads=4, d_ff=32, n_layers=2, dropout=0.1)
SEED, QUERY_SLOTS = 1092, 6


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gravar(path, data):
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )


def matrix_svg(matrix, title):
    rows, columns = matrix.shape
    left, top, cell = 40, 32, 14
    maximum = float(matrix.max())
    pieces = []
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            opacity = 0.05 + 0.95 * float(value) / maximum
            pieces.append(
                f'<rect x="{left + j * cell}" y="{top + i * cell}" width="13" height="13" '
                f'fill="#166783" opacity="{opacity:.5f}"><title>consulta {i}, chave {j}: {value:.10f}</title></rect>'
            )
    for j in range(columns):
        pieces.append(f'<text x="{left + j * cell + 6}" y="22" text-anchor="middle" font-size="8">{j}</text>')
    for i in range(rows):
        pieces.append(f'<text x="32" y="{top + i * cell + 10}" text-anchor="end" font-size="8">{i}</text>')
    return (
        f'<figure><figcaption>{html.escape(title)}</figcaption>'
        f'<svg viewBox="0 0 {left + columns * cell} {top + rows * cell}" role="img" '
        f'aria-label="{html.escape(title)}">' + "".join(pieces) + "</svg></figure>"
    )


def render_report(output, result, flow, window, weights):
    head_panels = []
    last_layer = MODEL_CONFIG["n_layers"]
    for head in range(MODEL_CONFIG["n_heads"]):
        figures = []
        for kind, title in (
            ("encoder_self", "Encoder: histórico inteiro"),
            ("decoder_self", "Decoder: self-attention causal"),
            ("decoder_cross", "Decoder: consulta à memória"),
        ):
            part = weights[(weights.kind == kind) & (weights.layer == last_layer) & (weights["head"] == head)]
            matrix = part.pivot(index="query", columns="key", values="weight").to_numpy()
            figures.append(matrix_svg(matrix, title))
        hidden = "" if head == 0 else " hidden"
        head_panels.append(f'<div class="maps" data-head="{head}"{hidden}>' + "".join(figures) + "</div>")
    checks = result["checks"]
    diagram = '''<div class="pipeline"><div>24 medições<br><code>[1,24,1]</code></div><span>→</span>
<div>Projeção + posição<br><code>[1,24,16]</code></div><span>→</span>
<div>2 blocos encoder<br><code>memória [1,24,16]</code></div></div>
<div class="pipeline"><div>6 consultas sintéticas<br><code>[1,6,1]</code></div><span>→</span>
<div>Projeção + posição<br><code>[1,6,16]</code></div><span>→</span>
<div>2 blocos decoder<br><code>representação [1,6,16]</code><br>↑ consulta à memória</div></div>'''
    page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Renewcast — bloco Transformer</title>
<style>body{{font:16px system-ui;max-width:1220px;margin:28px auto;padding:20px;color:#172d39;line-height:1.5}}
h1,h2{{line-height:1.2}}code{{background:#eef4f6;padding:2px 5px;border-radius:4px}}.note{{padding:15px;background:#fff5df;border-left:4px solid #bd8030}}
.pipeline{{display:flex;align-items:center;gap:12px;margin:18px 0;flex-wrap:wrap}}.pipeline div{{padding:14px;border:1px solid #96b5c3;border-radius:6px}}
.maps{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}}.maps[hidden]{{display:none}}figure{{margin:0}}figcaption{{font-weight:600;margin:10px 0}}svg{{width:100%}}
table{{border-collapse:collapse;font-size:13px;white-space:nowrap}}td,th{{padding:7px;border:1px solid #cbd9df;text-align:left}}.scroll{{overflow:auto}}select{{padding:7px;font:inherit}}
@media(max-width:800px){{.maps{{grid-template-columns:1fr}}}}.metric{{display:inline-block;margin:5px 20px 5px 0}}
</style></head><body><h1>Como o bloco Transformer transforma uma janela</h1>
<p>Execução <code>{html.escape(result['run_id'])}</code> · CPU/float64 · pesos não treinados.</p>
<p class="note">Prática local de composição para revisão. As saídas têm 16 coordenadas e não têm unidade MWmed.
As seis consultas não representam seis horizontes futuros. Nenhum modelo foi treinado ou comparado por acurácia.</p>
<h2>1. O caminho dos dados</h2>{diagram}
<p>Encoder: self-attention → residual + LayerNorm → feed-forward → residual + LayerNorm.
Decoder: self-attention causal → residual + LayerNorm → cross-attention → residual + LayerNorm → feed-forward → residual + LayerNorm.
Cada pilha tem duas camadas post-norm, sem uma norma adicional ao final.</p>
<h2>2. Conferências da composição</h2>
<p><span class="metric"><b>{checks['checks_count']}</b> grupos aprovados</span>
<span class="metric">Maior diferença PyTorch: <b>{checks['max_difference']:.3g}</b></span>
<span class="metric">Parâmetros: <b>{result['parameter_count']:,}</b></span></p>
<p>Prefixos do decoder com memória fixa: diferença <code>{result['real_decoder_prefix_difference']:.3g}</code>.
Recarregamento: diferença <code>{result['reload_difference']:.3g}</code>.
Uma camada, última consulta livre/causal: <code>{checks['differences']['last_query_one_layer']:.3g}</code>;
duas camadas: <code>{checks['last_query_two_layers_delta']:.6f}</code>.</p>
<h2>3. Cabeças da última camada</h2><label>Cabeça <select id="head">{''.join(f'<option>{i}</option>' for i in range(MODEL_CONFIG['n_heads']))}</select></label>
<p>Linhas são consultas; colunas são chaves. A cor é relativa ao máximo de cada painel.
Passe o mouse para ler o peso. Os índices das consultas são slots sintéticos.</p>{''.join(head_panels)}
<h2>4. Dimensões e estatísticas por subcamada</h2><div class="scroll">{flow.to_html(index=False, float_format=lambda value: f'{value:.6f}')}</div>
<h2>5. Histórico usado</h2><p>Origem {html.escape(result['forecast_origin'])}; medições de {html.escape(result['history_start'])}
a {html.escape(result['history_end'])}, sob atraso assumido de duas horas. A normalização usa somente as 7.079 janelas de ajuste.</p>
<div class="scroll">{window.to_html(index=False, float_format=lambda value: f'{value:.6f}')}</div>
<h2>6. Interpretação</h2><p>A atenção cruzada usa Q do decoder e K/V da memória do encoder.
A máscara causal restringe as consultas entre si, enquanto a memória contém somente histórico já disponível na origem.
As projeções, as somas residuais e a feed-forward retiram da saída do bloco a propriedade de média convexa do histórico bruto.</p>
<p>O backward de conferência usa uma sonda fixa para verificar caminhos de gradiente e não executa optimizer.step().
O checkpoint salvo contém a inicialização aleatória, a configuração e as escalas; não são pesos pré-treinados.</p>
<p>Arquivos: <a href="resultado.json">resultado.json</a>, <a href="conferencia.json">conferencia.json</a>,
<a href="fluxo.csv">fluxo.csv</a>, <a href="pesos_atencao.csv">pesos_atencao.csv</a>,
<a href="representacoes_encoder.csv">encoder</a> e <a href="representacoes_decoder.csv">decoder</a>.</p>
<script>document.getElementById('head').addEventListener('change',function(){{document.querySelectorAll('[data-head]').forEach(el=>el.hidden=el.dataset.head!==this.value);}});</script>
</body></html>'''
    (output / "relatorio.html").write_text(page, encoding="utf-8")


def execute(args, output, checks):
    from m08_3_base import carregar, dividir

    started = time.perf_counter()
    frame, x, _, incomplete, hashes, package = carregar(args.input_dir)
    parts = dividir(frame)
    selected = np.flatnonzero(frame.forecast_origin.eq(pd.Timestamp(args.origin)).to_numpy())
    if len(selected) != 1:
        raise ValueError("A origem deve identificar uma janela elegível do pacote M07.3.")
    index = int(selected[0])
    mean = x[parts["ajuste"]].mean(axis=0)
    scale = x[parts["ajuste"]].std(axis=0)
    if not np.isfinite(scale).all() or (scale <= 0).any():
        raise ValueError("As escalas de ajuste devem ser finitas e positivas.")
    raw = x[index:index + 1]
    z = (raw - mean) / scale
    source = torch.tensor(z, dtype=torch.float64)
    queries = torch.zeros(1, QUERY_SLOTS, 1, dtype=torch.float64)
    torch.manual_seed(SEED)
    model = TransformerDidatico(**MODEL_CONFIG).double().eval()
    preprocessing = dict(mean_x=mean.tolist(), scale_x=scale.tolist(), fitted_on="ajuste only", fit_rows=len(parts["ajuste"]), ddof=0)
    config = dict(
        schema="renewcast-transformer-composition-config-v1", model=MODEL_CONFIG,
        seed=SEED, dtype="float64", cpu_threads=2, query_slots=QUERY_SLOTS,
        query_input="zeros in standardized scalar space; not future targets or horizons",
        block_layout="post_norm; no additional norm after stacks", input_sha256=hashes,
        weights_trained=False, pretrained_weights_used=False,
    )
    gravar(output / "config.json", config)
    gravar(output / "preprocessing.json", preprocessing)
    with torch.no_grad():
        result = model(source, queries)
        changed = queries.clone()
        changed[:, -2:] += 3
        before, _ = model.decode(queries, result["memory"])
        after, _ = model.decode(changed, result["memory"])
        prefix_delta = float((before[:, :-2] - after[:, :-2]).abs().max())
        changed_delta = float((before[:, -2:] - after[:, -2:]).abs().max())
    torch.testing.assert_close(before[:, :-2], after[:, :-2], rtol=0, atol=1e-12)
    assert changed_delta > 1e-8

    rows = []

    def stage(path, name, tensor):
        value = tensor.detach()
        rows.append(dict(path=path, stage=name, shape=str(list(value.shape)), mean=float(value.mean()), std=float(value.std(unbiased=False)), max_abs=float(value.abs().max())))

    stage("input", "historico_padronizado", source)
    stage("input", "consultas_sinteticas", queries)
    stage("embedding", "historico_mais_posicao", result["source_embedding"])
    stage("embedding", "consultas_mais_posicao", result["query_embedding"])
    attention_rows = []
    for group, traces in (("encoder", result["encoder_traces"]), ("decoder", result["decoder_traces"])):
        for layer, trace in enumerate(traces, start=1):
            for name, tensor in trace.items():
                if name.endswith("weights"):
                    kind = "encoder_self" if group == "encoder" else ("decoder_self" if name.startswith("self") else "decoder_cross")
                    weights = tensor[0].detach().numpy()
                    for head in range(weights.shape[0]):
                        for query in range(weights.shape[1]):
                            for key in range(weights.shape[2]):
                                attention_rows.append(dict(kind=kind, layer=layer, head=head, query=query, key=key, weight=float(weights[head, query, key])))
                else:
                    stage(f"{group}.{layer}", name, tensor)
    flow, weights_frame = pd.DataFrame(rows), pd.DataFrame(attention_rows)
    flow.to_csv(output / "fluxo.csv", index=False)
    weights_frame.to_csv(output / "pesos_atencao.csv", index=False)
    origin = frame.forecast_origin.iloc[index]
    times = pd.date_range(origin - pd.Timedelta(hours=25), origin - pd.Timedelta(hours=2), freq="h")
    window = pd.DataFrame(dict(position=np.arange(24), measurement_time=times, generation=raw[0, :, 0], standardized=z[0, :, 0]))
    window.to_csv(output / "janela.csv", index=False)
    for name, tensor in (("encoder", result["memory"]), ("decoder", result["decoder"])):
        table = pd.DataFrame(tensor[0].detach().numpy(), columns=[f"coord_{i:02}" for i in range(MODEL_CONFIG["d_model"])])
        table.insert(0, "position" if name == "encoder" else "query_slot", np.arange(len(table)))
        if name == "encoder":
            table.insert(1, "measurement_time", times)
        table.to_csv(output / f"representacoes_{name}.csv", index=False)

    checkpoint = dict(model_config=MODEL_CONFIG, state_dict=model.state_dict(), preprocessing=preprocessing, seed=SEED, dtype="float64", weights_trained=False)
    torch.save(checkpoint, output / "estado_transformer.pt")
    recovered = torch.load(output / "estado_transformer.pt", map_location="cpu", weights_only=True)
    restored = TransformerDidatico(**recovered["model_config"]).double().eval()
    restored.load_state_dict(recovered["state_dict"])
    again_z = (raw - np.array(recovered["preprocessing"]["mean_x"])) / np.array(recovered["preprocessing"]["scale_x"])
    with torch.no_grad():
        again = restored(torch.tensor(again_z, dtype=torch.float64), queries)
    torch.testing.assert_close(again["decoder"], result["decoder"], rtol=0, atol=0)
    torch.testing.assert_close(again["memory"], result["memory"], rtol=0, atol=0)
    for name, digest in hashes.items():
        if sha(args.input_dir / name) != digest:
            raise ValueError("Uma entrada mudou durante a execução.")
    code_paths = [Path(__file__), Path(verification_module.__file__), Path(blocks_module.__file__), Path(__file__).with_name("m08_3_base.py")]
    detail = dict(
        schema="renewcast-transformer-composition-result-v1", completed=True, run_id=output.name,
        status="local didactic composition for review; not a distributed course acceptance",
        forecast_origin=origin.isoformat(), history_start=times[0].isoformat(), history_end=times[-1].isoformat(),
        availability_delay_hours_assumed=2, physical_timezone_verified=False,
        partition_rows={name:len(indices) for name,indices in parts.items()}, excluded_incomplete=len(incomplete),
        shapes=dict(source=list(source.shape), queries=list(queries.shape), source_embedding=list(result["source_embedding"].shape), memory=list(result["memory"].shape), decoder=list(result["decoder"].shape)),
        parameter_count=sum(p.numel() for p in model.parameters()), query_slots=QUERY_SLOTS,
        checks=checks, real_decoder_prefix_difference=prefix_delta, changed_query_slots_difference=changed_delta,
        reload_difference=float((again["decoder"] - result["decoder"]).abs().max()),
        input_sha256=hashes, source_package_id=package["package_id"], code_sha256={p.name:sha(p) for p in code_paths},
        environment=dict(python=platform.python_version(), torch=str(torch.__version__), numpy=np.__version__, pandas=pd.__version__, device="cpu", dtype="float64"),
        models_trained=False, optimizer_steps=0, pretrained_weights_used=False,
        forecast_metrics_computed=False, future_targets_used=False, operational_approval=False,
        elapsed_seconds=time.perf_counter() - started,
    )
    render_report(output, detail, flow, window, weights_frame)
    detail["output_sha256"] = {p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    gravar(output / "resultado.json", detail)
    gravar(args.output_dir / "latest_run.json", dict(run_id=output.name, directory=str(output.resolve()), resultado_sha256=sha(output / "resultado.json")))
    print(f'Janela: {times[0]} a {times[-1]}; origem {origin}.')
    print(f'Encoder {tuple(result["memory"].shape)}; decoder {tuple(result["decoder"].shape)}; parâmetros={detail["parameter_count"]}.')
    print(f'Prefixo causal: delta={prefix_delta:.3g}; recarregamento: delta={detail["reload_difference"]:.3g}.')
    print("Representações não treinadas; nenhuma previsão ou métrica de acurácia.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "dist/databricks/CJU_BA5EIGT/m07_3")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/transformer/CJU_BA5EIGT/m09_2_transformer")
    parser.add_argument("--origin", default="2026-07-03 04:00:00")
    parser.add_argument("--verificar", action="store_true", help="Confere os blocos sem ler os Parquets.")
    args = parser.parse_args(argv)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    args.input_dir, args.output_dir = args.input_dir.resolve(), args.output_dir.resolve()
    output = args.output_dir / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False)
    try:
        checks = conferir()
        gravar(output / "conferencia.json", checks)
        print(f'Conferências aprovadas: {checks["checks_count"]} grupos; maior diferença={checks["max_difference"]:.3g}.', flush=True)
        if not args.verificar:
            execute(args, output, checks)
        print(f"Resultados: {output}")
    except Exception as exc:
        gravar(output / "failure.json", dict(completed=False, error_type=type(exc).__name__, error=str(exc)))
        raise


if __name__ == "__main__":
    main()
