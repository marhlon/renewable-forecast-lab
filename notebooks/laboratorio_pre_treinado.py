"""M09.3: Chronos-Bolt Tiny congelado versus previsoes ja produzidas em M08.3.

Comando recomendado: python scripts/executar_m09_3.py
Nao treina baselines, nao seleciona contexto/epoca/semente na avaliacao.
"""
from __future__ import annotations
import argparse
import importlib.util
import importlib.metadata as metadata
import json
import platform
import time
import uuid
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from m09_pre_treinado_core import sha,preparar_snapshot,alinhar_quantis,conferir_alinhamento

ROOT=Path(__file__).resolve().parents[1]

def gravar(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def carregar_baseline(directory,input_hashes,origins,targets):
    result=json.loads((directory/'resultado.json').read_text(encoding='utf-8'))
    if result.get('schema')!='renewcast-gru-result-v1' or result.get('completed') is not True:
        raise ValueError('A referencia deve ser uma execucao completa M08.3.')
    if result['input_sha256']!=input_hashes:raise ValueError('M08.3 e M09.3 devem usar o mesmo pacote de entrada.')
    hashes={}
    for name in ('predictions.csv','summary.csv','particoes.csv','preprocessing.json','protocol.json'):
        p=directory/name;hashes[name]=sha(p)
        if hashes[name]!=result['output_sha256'][name]:raise ValueError(f'Referencia alterada: {p}')
    hashes['resultado.json']=sha(directory/'resultado.json')
    pred=pd.read_csv(directory/'predictions.csv',parse_dates=['forecast_origin'])
    required={'method','seed','forecast_origin','target_generation','prediction'}
    if not required.issubset(pred) or len(pred)!=1512:raise ValueError('Previsoes M08.3 incompatíveis.')
    allowed={('persistence_d2',None),('linear_24h',None),('hgb_24h',17),
             ('mlp_24h',17),('mlp_24h',29),('mlp_24h',41),('gru_24h',17),('gru_24h',29),('gru_24h',41)}
    keys={(r.method,None if pd.isna(r.seed) else int(r.seed)) for r in pred[['method','seed']].drop_duplicates().itertuples()}
    if keys!=allowed:raise ValueError('Referencia deve conter exatamente as nove variantes M08.3.')
    for _,g in pred.groupby(['method','seed'],dropna=False):
        g=g.sort_values('forecast_origin')
        if g.forecast_origin.duplicated().any():raise ValueError('Origem duplicada no baseline.')
        np.testing.assert_array_equal(g.forecast_origin.to_numpy(),origins.to_numpy())
        np.testing.assert_allclose(g.target_generation,targets,atol=1e-9,rtol=0)
        if not np.isfinite(g.prediction).all():raise ValueError('Baseline nao finito.')
    return pred,result,hashes

def metricas(y,p):
    e=np.asarray(y)-np.asarray(p)
    return dict(mae_mwmed=float(np.abs(e).mean()),rmse_mwmed=float(np.sqrt(np.square(e).mean())),
                bias_observed_minus_predicted_mwmed=float(e.mean()))

def quantile_metrics(y,a):
    p10,p50,p90=(a[k] for k in ('p10','p50','p90'))
    result={}
    for tau,pred in ((.1,p10),(.5,p50),(.9,p90)):
        e=y-pred;result[f'pinball_p{int(tau*100)}']=float(np.maximum(tau*e,(tau-1)*e).mean())
    width=p90-p10
    result.update(coverage_80=float(((y>=p10)&(y<=p90)).mean()),below_p10=float((y<p10).mean()),
                  above_p90=float((y>p90).mean()),mean_width_mwmed=float(width.mean()),
                  interval_score_80=float((width+10*np.maximum(p10-y,0)+10*np.maximum(y-p90,0)).mean()),
                  crossing_rows=int(((p10>p50)|(p50>p90)).sum()),negative_p50_rows=int((p50<0).sum()),
                  clipped=False,recalibrated=False)
    return result

def executar(args,out,align,checks):
    import torch
    from chronos import ChronosBoltPipeline
    from m08_3_base import carregar,dividir,montar_janelas
    from m09_pre_treinado_core import preparar_snapshot
    started=time.perf_counter();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);torch.manual_seed(1093)
    spec=json.loads((ROOT/'docs/model_source_m09_3.json').read_text())
    frame,x,y,incomplete,input_hashes,source=carregar(args.input_dir);parts=dividir(frame);report=parts['avaliacao']
    windows=frame.iloc[report].copy().reset_index(drop=True)
    origins=pd.DatetimeIndex(windows.forecast_origin);actual=y[report,0];context=x[report,:,0]
    if context.shape!=(168,24):raise ValueError('O protocolo exige 168 origens com 24 observacoes cada.')
    baseline,baseline_result,baseline_hashes=carregar_baseline(args.baseline_run_dir,input_hashes,origins,actual)
    # Dados futuros podem constar do arquivo de avaliacao; nao entram no contexto.
    raw=pd.read_parquet(args.input_dir/'geracao.parquet');raw['din_instante']=pd.to_datetime(raw.din_instante)
    generation=raw.set_index('din_instante').val_geracao
    o=origins[0];changed=generation.copy();changed.loc[changed.index>o-pd.Timedelta(hours=2)]+=500
    np.testing.assert_array_equal(montar_janelas(generation,pd.DatetimeIndex([o])),montar_janelas(changed,pd.DatetimeIndex([o])))
    model_hashes=preparar_snapshot(spec,args.model_dir,args.offline)
    versions={n:metadata.version(n) for n in ('torch','chronos-forecasting','transformers','accelerate','numpy','pandas','pyarrow')}
    protocol=dict(schema='renewcast-pretrained-protocol-v1',model=spec,versions=versions,
                  baseline_run_id=baseline_result['run_id'],baseline_source=str(args.baseline_run_dir),baseline_hashes=baseline_hashes,
                  input_sha256=input_hashes,source_package_id=source['package_id'],context_hours=24,
                  horizon_hours=24,availability_delay_hours_assumed=2,steps_after_history_end=26,
                  selected_quantile=.5,selection_rule='prescribed model/context/quantile; no tuning on evaluation',
                  models_trained=False,baseline_retrained=False,weights_finetuned=False,
                  scope='same previously explored development week; not untouched holdout',
                  code_sha256={Path(__file__).name:sha(__file__),
                      'm09_pre_treinado_core.py':sha(Path(__file__).with_name('m09_pre_treinado_core.py')),
                      'executar_m09_3.py':sha(ROOT/'scripts/executar_m09_3.py'),
                      'm08_3_base.py':sha(Path(__file__).with_name('m08_3_base.py'))},
                  model_spec_sha256=sha(ROOT/'docs/model_source_m09_3.json'),
                  requirements_sha256=sha(ROOT/'docs/requirements_m09_3.lock.txt'),
                  authorship_sha256=sha(args.autoria) if args.autoria else None)
    gravar(out/'protocol.json',protocol)
    t=time.perf_counter()
    pipeline=ChronosBoltPipeline.from_pretrained(args.model_dir,device_map='cpu',torch_dtype=torch.float32,
                       local_files_only=True,use_safetensors=True,trust_remote_code=False)
    pipeline.model.eval();pipeline.model.requires_grad_(False)
    load_seconds=time.perf_counter()-t
    levels=np.array(pipeline.quantiles)
    if list(levels)!=[.1,.2,.3,.4,.5,.6,.7,.8,.9]:raise ValueError('Niveis do modelo diferentes do protocolo.')
    tensor=torch.tensor(context,dtype=torch.float32)
    print('Modelo pre-treinado carregado em CPU; 24 horas por origem; 26 passos; sem fit.',flush=True)
    t=time.perf_counter()
    with torch.inference_mode():warm=pipeline.predict(tensor[:1],prediction_length=26,limit_prediction_length=True)
    warm_seconds=time.perf_counter()-t
    forecast=[];latencies=[]
    for start in range(0,len(tensor),spec['batch_size']):
        batch=tensor[start:start+spec['batch_size']];t=time.perf_counter()
        with torch.inference_mode():pred=pipeline.predict(batch,prediction_length=26,limit_prediction_length=True)
        seconds=time.perf_counter()-t
        forecast.append(pred.numpy());latencies.append(dict(start=start,rows=len(batch),seconds=seconds))
        print(f'Inferencia: {min(start+len(batch),len(tensor))}/{len(tensor)} origens; lote={seconds:.3f}s',flush=True)
    forecast=np.concatenate(forecast)
    if forecast.shape!=(168,9,26) or not np.isfinite(forecast).all():raise ValueError('Saida do modelo fora do contrato.')
    with torch.inference_mode():repeat=pipeline.predict(tensor[:1],prediction_length=26,limit_prediction_length=True)
    np.testing.assert_allclose(repeat.numpy(),warm.numpy(),atol=1e-6,rtol=0)
    alignment=align(forecast,levels,windows.history_end.to_numpy(),windows.target_time.to_numpy())
    np.testing.assert_array_equal(alignment['lead_hours'],np.full(168,26))
    np.testing.assert_array_equal(alignment['index_zero_based'],np.full(168,25))
    method='chronos_bolt_tiny_zero_shot'
    own=windows[['forecast_origin','history_end','target_time','target_available_at']].copy()
    own['method']=method;own['seed']=np.nan;own['target_generation']=actual;own['prediction']=alignment['p50']
    for key in ('p10','p50','p90','lead_hours','index_zero_based'):own[key]=alignment[key]
    own['absolute_error']=np.abs(actual-own.prediction);own['squared_error']=(actual-own.prediction)**2
    combined=pd.concat([baseline,own],ignore_index=True)
    rows=[]
    for (name,seed),g in combined.groupby(['method','seed'],dropna=False,sort=False):
        rows.append(dict(method=name,seed=None if pd.isna(seed) else int(seed),rows=len(g),
                         **metricas(g.target_generation,g.prediction)))
    summary=pd.DataFrame(rows)
    hgb=summary.loc[summary.method.eq('hgb_24h'),'mae_mwmed'].iloc[0]
    persistence=summary.loc[summary.method.eq('persistence_d2'),'mae_mwmed'].iloc[0]
    summary['mae_gain_vs_hgb_pct']=100*(hgb-summary.mae_mwmed)/hgb
    summary['mae_gain_vs_persistence_pct']=100*(persistence-summary.mae_mwmed)/persistence
    combined.to_csv(out/'predictions.csv',index=False);summary.to_csv(out/'summary.csv',index=False)
    own.to_csv(out/'alinhamento_alvos.csv',index=False);pd.DataFrame(latencies).to_csv(out/'latencias_lotes.csv',index=False)
    np.savez_compressed(out/'quantis_26_passos.npz',forecast=forecast,quantile_levels=levels)
    paths=[]
    for b in range(len(tensor)):
        for step in range(26):
            row=dict(forecast_origin=origins[b],history_end=windows.history_end.iloc[b],lead_hours=step+1,
                     forecast_time=windows.history_end.iloc[b]+pd.Timedelta(hours=step+1),selected_target=step==25)
            row.update({f'p{int(tau*100):02}':float(forecast[b,q,step]) for q,tau in enumerate(levels)});paths.append(row)
    pd.DataFrame(paths).to_csv(out/'trajetorias_26_passos.csv',index=False)
    interval=quantile_metrics(actual,alignment);gravar(out/'quantile_metrics.json',interval)
    hgb_predictions=baseline.loc[baseline.method.eq('hgb_24h')].sort_values('forecast_origin').prediction.to_numpy()
    gains=np.abs(actual-hgb_predictions)-np.abs(actual-alignment['p50'])
    paired=own[['forecast_origin','target_time','target_generation','prediction']].copy()
    paired['hgb_prediction']=hgb_predictions;paired['mae_gain_hgb_minus_chronos']=gains;paired.to_csv(out/'comparacao_pareada.csv',index=False)
    process_peak=None
    try:
        import resource
        process_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024 if platform.system()!='Darwin' else 1024**2)
    except ImportError:
        try:
            import psutil
            mem=psutil.Process().memory_info();process_peak=getattr(mem,'peak_wset',mem.rss)/1024**2
        except ImportError:pass
    result=dict(schema='renewcast-pretrained-result-v1',completed=True,run_id=out.name,model_repo=spec['repo_id'],model_revision=spec['revision'],
                model_file_sha256=model_hashes,parameter_count=sum(p.numel() for p in pipeline.model.parameters()),
                baseline_run_id=baseline_result['run_id'],input_sha256=input_hashes,checks=checks,
                temporal_invariance_checked=True,repeated_inference_max_difference=float(np.abs(repeat.numpy()-warm.numpy()).max()),
                model_load_seconds=load_seconds,warmup_seconds=warm_seconds,inference_seconds=sum(r['seconds'] for r in latencies),
                batch_size=spec['batch_size'],cpu_threads=2,process_peak_mib=process_peak,process_peak_scope='whole process; not isolated model memory',
                versions=versions,python=platform.python_version(),platform=platform.platform(),
                chronological_rows=168,quantile_rows=forecast.shape[0],selected_forecast_index=25,
                forecast_metric=metricas(actual,alignment['p50']),interval_metrics=interval,
                paired_mae_gain_vs_hgb=float(gains.mean()),origins_abs_error_better_than_hgb=int((gains>0).sum()),
                frozen_parameters=True,models_trained=False,weights_finetuned=False,optimizer_steps=0,
                future_targets_used_as_inputs=False,pretraining_overlap_verified=False,
                availability_is_assumed=True,physical_timezone_verified=False,untouched_holdout=False,operational_approval=False,
                elapsed_seconds_before_report=time.perf_counter()-started)
    html='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>M09.3 previsao pre-treinada</title>
<style>body{font:16px system-ui;max-width:1200px;margin:32px auto;padding:18px;color:#172d39}table{border-collapse:collapse;font-size:13px}td,th{padding:7px;border:1px solid #ccd6dd}.scroll{overflow:auto}.note{padding:14px;background:#fff5df;border-left:4px solid #bd8030}</style>
<h1>M09.3 — previsao com Chronos-Bolt Tiny</h1><p class="note">Pesos pre-treinados congelados; contexto 24h igual aos baselines. Semana de desenvolvimento ja examinada. Nao e promocao operacional nem prova de ausencia de sobreposicao no pre-treino.</p>'''
    html+=f'<p>Revisao {spec["revision"]}; {result["parameter_count"]:,} parametros; CPU/float32. H24 desde a origem exige 26 passos desde history_end: selecionado indice25.</p>'
    html+='<h2>Mesmas 168 origens</h2><div class="scroll">'+summary.to_html(index=False,float_format=lambda v:f'{v:.6f}')+'</div>'
    html+='<h2>Primeiros alvos alinhados</h2><div class="scroll">'+own.head(8).to_html(index=False,float_format=lambda v:f'{v:.6f}')+'</div>'
    html+='<h2>Intervalo preditivo bruto</h2><pre>'+json.dumps(interval,indent=2)+'</pre>'
    html+=f'<p>Inferencia dos lotes: {result["inference_seconds"]:.3f}s; carga: {load_seconds:.3f}s; aquecimento: {warm_seconds:.3f}s. Pico do processo: {process_peak} MiB. Os tempos nao incluem instalacao/download.</p>'
    html+='<p>Fontes completas: protocol.json, resultado.json, alinhamento_alvos.csv, trajetorias_26_passos.csv e comparacao_pareada.csv.</p></html>'
    (out/'relatorio.html').write_text(html,encoding='utf-8')
    for name,expected in input_hashes.items():
        if sha(args.input_dir/name)!=expected:raise ValueError('Entrada alterada durante a execucao.')
    for name,expected in model_hashes.items():
        if sha(args.model_dir/name)!=expected:raise ValueError('Snapshot mudou durante a inferencia.')
    result['output_sha256']={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    gravar(out/'resultado.json',result);gravar(args.output_dir/'latest_run.json',dict(run_id=out.name,directory=str(out.resolve()),resultado_sha256=sha(out/'resultado.json')))
    print('\nMESMAS 168 ORIGENS, MWmed; vies = observado - previsto')
    print(summary.round(6).to_string(index=False));print('Quantis brutos:',interval)
    print(f'Resultados: {out.resolve()}')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',type=Path,default=ROOT/'dist/databricks/CJU_BA5EIGT/m07_3')
    p.add_argument('--baseline-run-dir',type=Path)
    p.add_argument('--model-dir',type=Path,default=ROOT/'models/pretrained/chronos-bolt-tiny/a0e552de83495b5c28c14c71c374f3e33280b340')
    p.add_argument('--output-dir',type=Path,default=ROOT/'reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado')
    p.add_argument('--autoria',nargs='?',type=Path,const=ROOT/'notebooks/m09_alinhamento_autoral.py')
    p.add_argument('--verificar',action='store_true');p.add_argument('--offline',action='store_true')
    args=p.parse_args(argv)
    for field in ('input_dir','model_dir','output_dir'):setattr(args,field,getattr(args,field).resolve())
    if args.baseline_run_dir is None and not args.verificar:
        pointer=ROOT/'reports/neural/CJU_BA5EIGT/m08_3_gru/latest_run.json'
        if not pointer.is_file():raise FileNotFoundError('Ponteiro M08.3 ausente. Informe --baseline-run-dir com a execucao ja realizada.')
        args.baseline_run_dir=Path(json.loads(pointer.read_text())['directory'])
    if args.baseline_run_dir is not None:args.baseline_run_dir=args.baseline_run_dir.resolve()
    align=alinhar_quantis
    if args.autoria is not None:
        spec=importlib.util.spec_from_file_location('m09_alinhamento_autoral',args.autoria)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);align=module.alinhar_quantis
    out=args.output_dir/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True,exist_ok=False)
    try:
        checks=conferir_alinhamento(align);gravar(out/'conferencia.json',checks)
        if args.verificar:print(f'Alinhamento aprovado; sem treino/dados/modelo. Recibo: {out}')
        else:executar(args,out,align,checks)
    except Exception as e:
        gravar(out/'failure.json',dict(completed=False,error_type=type(e).__name__,error=str(e)));raise

if __name__=='__main__':main()
