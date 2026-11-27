"""M03-04/M09-04: avaliação final segregada, contrato congelado antes da rede."""
from __future__ import annotations
import argparse,hashlib,json,math,os,platform,subprocess,sys,time,traceback,contextlib
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.venvs/bloco3-packages'))
import joblib,numpy as np,pandas as pd,torch
from torch import nn
from threadpoolctl import threadpool_limits
from bloco2_modelagem_core import build_frame,load_series,fit_mask,period_mask,sha256
from bloco2_risco_core import metricas_intervalo,metricas_probabilidade,metricas_alarmes,alarmes_causais,logit_features,confiabilidade
from m08_3_base import MLP
from renewable_forecast.neural_gru import GRU24h
BASE=ROOT/'reports/fechamento_m00_m09/bloco3_engenharia'
B2=ROOT/'reports/fechamento_m00_m09/bloco2_engenharia'
LEGACY=ROOT/'reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f'
ALT=BASE/'M05-04/alternatives.joblib'
SEAL=BASE/'congelamento_final.json';DATA=BASE/'dados_final'
RAW=ROOT/'data/raw/bloco3_locked/geracao_2026_09.parquet'
MODEL=ROOT/'models/pretrained/chronos-bolt-tiny/a0e552de83495b5c28c14c71c374f3e33280b340'
RESOURCE='c6d1f291-c114-4872-b69d-b487f7410e5c'
def now():return datetime.now(timezone.utc).isoformat()
def rel(p):return Path(p).resolve().relative_to(ROOT).as_posix()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n',encoding='utf-8')
def metric(y,p):
    e=np.asarray(y)-np.asarray(p)
    if not np.isfinite(e).all():raise ValueError('Previsão não finita')
    return dict(n=len(e),mae=float(np.abs(e).mean()),rmse=float(np.sqrt(np.mean(e*e))),bias_observed_minus_predicted=float(e.mean()))
def old_context(frame):return frame[[f'lag_{i}h' for i in range(24,0,-1)]].to_numpy()[:,:,None]
def legacy_predictions(frame):
    context=old_context(frame);scalers=json.loads((LEGACY/'preprocessing.json').read_text(encoding='utf-8'));z=(context-np.asarray(scalers['mean_x']))/np.asarray(scalers['scale_x']);result={}
    coef=np.asarray(json.loads((LEGACY/'linear_24h.json').read_text(encoding='utf-8'))['coefficients'])
    result['linear_legacy']=np.column_stack([z[:,:,0],np.ones(len(z))])@coef*scalers['scale_y']+scalers['mean_y']
    result['hgb_legacy']=joblib.load(LEGACY/'hgb_24h.joblib').predict(z[:,:,0])*scalers['scale_y']+scalers['mean_y']
    torch.set_num_threads(2)
    for architecture,factory in [('mlp',MLP),('gru',GRU24h)]:
        for seed in (17,29,41):
            checkpoint=torch.load(LEGACY/f'{architecture}_24h_seed_{seed}.pt',map_location='cpu',weights_only=True)
            estimator=factory();estimator.load_state_dict(checkpoint['state_dict']);estimator.eval()
            normalized=(context-checkpoint['mean_x'].numpy())/checkpoint['scale_x'].numpy();parts=[]
            with torch.inference_mode():
                for i in range(0,len(context),128):parts.append(estimator(torch.tensor(normalized[i:i+128],dtype=torch.float32)).numpy().reshape(-1))
            result[f'{architecture}_{seed}']=np.concatenate(parts)*checkpoint['scale_y']+checkpoint['mean_y']
    return result
def prepare():
    p=BASE/'M03-04/protocolo.json'
    if p.exists() or RAW.exists() or DATA.exists():raise FileExistsError('Não sobrescrever protocolo ou abrir período já obtido.')
    plan=dict(created_at_utc=now(),scope=['M03-04','M09-04'],source_month='2026-09',resource_id=RESOURCE,resource_page=f'https://dados.ons.org.br/dataset/geracao-usina-2/resource/{RESOURCE}',metadata_only_viewed=True,new_raw_not_present=True,source='ONS usina CJU_BA5EIGT, snapshot newly acquired; no historical published vintage proof',origins_start='2026-09-02 01:00',origins_end_exclusive='2026-09-30 00:00',source_hours=720,origins=671,availability={'history_end':'origin-2h','context':'24 real chronological values origin-25h..origin-2h','target':'origin+24h','label_available':'origin+26h','chronos_forecast_index':25,'timezone':'UTC interpreted under hypothesis'},no_training_on_final=True,no_tuning_on_final=True,no_seed_selection=True,model_families=['persistence','legacy linear','legacy HGB','MLP all3seeds','GRU all3seeds','B2 selected HGB28','LightGBM dev-selected','CatBoost dev-selected','HGB quantile median','Chronos P50'],champion_fixed='hgb_bloco2',baseline='persistence',primary_metric='MAE',paired_gain='absolute_error_persistence - absolute_error_candidate',bootstrap={'method':'circular paired blocks','block_hours':24,'repetitions':2000,'seed':31,'confidence':.95,'scope':'conditional on frozen models/snapshot; no refitting, no p-value'},consideration_rule={'minimum_mean_mae_gain_mwmed':2,'gain_ci_lower_above_zero':True,'cqr_coverage_nominal':.8,'coverage_tolerance':.1,'interval_mean_width_limit_mwmed':100,'frozen_policy_cost_less_than_never_alarm':True,'all_runtime_day_alarm_limits_at_most':6,'operational_data_contract_required':True},decision='Engineering may close even with negative results. No automatic promotion; M04 PIT and live evidence remain prerequisites.',point_cost_scenarios=[{'name':'symmetric','under':1,'over':1},{'name':'under_cost4','under':4,'over':1},{'name':'over_cost4','under':1,'over':4}],intervals=['B2 raw_sorted','B2 CQR frozen July','Chronos raw P10-P90'],probabilities='B2 raw / Platt / historical frequency only; do not invent class probabilities from three quantiles or point forecasts',latency='record observed scopes and library environments; Chronos separate private process, no claim of isolated model RAM or strict apples-to-apples latency ranking',legacy_fits='reused without any retraining; original M08 training vs B2 training differ and must be disclosed',pretraining_overlap_verified=False,operational_approval=False,attribution='Codex supplied engineering analysis; no independent learning or human approval asserted')
    dump(p,plan);dump(BASE/'M09-04/protocolo.json',plan)
    print('Protocolo final gravado antes do congelamento/download de setembro.')
def check_adapter():
    plan=json.loads((BASE/'M03-04/protocolo.json').read_text(encoding='utf-8'))
    frame=build_frame(load_series(ROOT/'dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet'))
    data=frame.loc[period_mask(frame,'2026-07-03 04:00','2026-07-10 04:00')].iloc[[0,1,2,83,166,167]].copy();assert len(data)==6
    saved=pd.read_csv(LEGACY/'predictions.csv',parse_dates=['forecast_origin']);pred=legacy_predictions(data);diffs={}
    for name,values in pred.items():
        if name=='linear_legacy':method='linear_24h';seed=None
        elif name=='hgb_legacy':method='hgb_24h';seed=17
        else:architecture,number=name.split('_');method=architecture+'_24h';seed=int(number)
        group=saved.loc[saved.method.eq(method)&(saved.seed.isna() if seed is None else saved.seed.eq(seed))].set_index('forecast_origin').loc[data.forecast_origin]
        difference=float(np.max(np.abs(values-group.prediction.to_numpy())));diffs[name]=difference
        np.testing.assert_allclose(values,group.prediction.to_numpy(),rtol=0,atol=1e-4)
    dump(BASE/'M03-04/compatibilidade_adaptador.json',dict(checked_at_utc=now(),origins=6,maximum_difference_by_method=diffs,atol=1e-4,trained=False,scope='new adapter checked on six old origins, not rerunning training or final dataset'))
    print(json.dumps(diffs))
def freeze():
    if SEAL.exists() or RAW.exists() or DATA.exists():raise FileExistsError('Congelamento/dados já existem.')
    files=[Path(__file__),ROOT/'notebooks/bloco3_chronos_inferencia.py',ROOT/'notebooks/bloco3_alternativas.py',ROOT/'notebooks/bloco2_modelagem_core.py',ROOT/'notebooks/bloco2_risco_core.py',ROOT/'notebooks/m08_3_base.py',ROOT/'src/renewable_forecast/neural_gru.py',BASE/'M03-04/protocolo.json',BASE/'M09-04/protocolo.json',BASE/'M03-04/compatibilidade_adaptador.json',ALT,BASE/'M05-04/protocolo.json',BASE/'M05-04/freeze.json',B2/'M03-03/point_bundle.joblib',B2/'M05-01/interval_bundle.joblib',B2/'M05-02/probability_bundle.joblib',B2/'M05-02/politica_congelada.json',LEGACY/'hgb_24h.joblib',LEGACY/'linear_24h.json',LEGACY/'preprocessing.json']+[LEGACY/f'{a}_24h_seed_{s}.pt' for a in ['mlp','gru'] for s in [17,29,41]]+[MODEL/n for n in ['config.json','model.safetensors','README.md']]
    old=json.loads((LEGACY/'resultado.json').read_text(encoding='utf-8'))
    for path in files:
        if not path.is_file():raise FileNotFoundError(path)
        if path.parent==LEGACY and path.name in old['output_sha256'] and sha256(path)!=old['output_sha256'][path.name]:raise ValueError(f'Artefato histórico divergente: {path}')
    spec=json.loads((ROOT/'docs/model_source_m09_3.json').read_text(encoding='utf-8'))
    for n,entry in spec['files'].items():
        if sha256(MODEL/n)!=entry['sha256']:raise ValueError('Snapshot Chronos divergente')
    dump(SEAL,dict(schema='renewcast-bloco3-final-freeze-v1',created_at_utc=now(),raw_evaluation_present=False,files={rel(p):sha256(p) for p in files},source_month='2026-09',operational_approval=False))
    print(f'Congelados {len(files)} arquivos antes de obter setembro.')
def verify():
    seal=json.loads(SEAL.read_text(encoding='utf-8'))
    for p,h in seal['files'].items():
        if sha256(ROOT/p)!=h:raise ValueError(f'Arquivo congelado alterado: {p}')
    return seal
def fetch_bytes(url,limit):
    with urlopen(Request(url,headers={'User-Agent':'Renewcast-research/1.0'}),timeout=90) as r:
        b=r.read(limit+1)
        if len(b)>limit:raise ValueError('Resposta excede limite predefinido')
        return b,dict(url=r.url,headers=dict(r.headers.items()))
def download():
    seal=verify()
    if RAW.exists() or DATA.exists():raise FileExistsError('Não substituir snapshot final.')
    meta,httpmeta=fetch_bytes(f'https://dados.ons.org.br/api/3/action/resource_show?id={RESOURCE}',2*1024**2);resource=json.loads(meta)
    assert resource.get('success') and resource['result']['id']==RESOURCE and resource['result']['format'].lower()=='parquet'
    content,http=fetch_bytes(resource['result']['url'],32*1024**2);assert content[:4]==b'PAR1' and content[-4:]==b'PAR1'
    RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_bytes(content);DATA.mkdir(parents=True,exist_ok=False)
    dump(DATA/'fonte_ckan.json',resource)
    receipt=dict(downloaded_at_utc=now(),freeze_sha256=sha256(SEAL),freeze_created_at_utc=seal['created_at_utc'],raw_path=rel(RAW),raw_sha256=sha256(RAW),raw_bytes=len(content),http=http,metadata_http=httpmeta,retrospective_snapshot=True,historically_point_in_time_proven=False,operational_approval=False)
    dump(DATA/'fonte.json',receipt)
    raw=pd.read_parquet(RAW);data=raw.loc[raw.id_ons.eq('CJU_BA5EIGT'),['din_instante','val_geracao']].copy();data['din_instante']=pd.to_datetime(data.din_instante,utc=True).dt.tz_localize(None);data=data.sort_values('din_instante').reset_index(drop=True)
    assert pd.DatetimeIndex(data.din_instante).equals(pd.date_range('2026-09-01','2026-09-30 23:00',freq='h')) and np.isfinite(data.val_geracao).all()
    output=DATA/'geracao_CJU_BA5EIGT_2026_09.parquet';data.to_parquet(output,index=False)
    receipt.update(filtered_path=rel(output),filtered_sha256=sha256(output),filtered_rows=len(data),extracted_at_utc=now(),extraction_status='validated');dump(DATA/'fonte.json',receipt);print('Fonte final:720 horas únicas e finitas, obtidas após congelamento.')
def get_final():
    verify();receipt=json.loads((DATA/'fonte.json').read_text(encoding='utf-8'));path=ROOT/receipt['filtered_path'];assert sha256(path)==receipt['filtered_sha256']
    frame=build_frame(load_series(path));data=frame.loc[period_mask(frame,'2026-09-02 01:00','2026-09-30')].reset_index(drop=True)
    assert len(data)==671 and pd.DatetimeIndex(data.forecast_origin).equals(pd.date_range('2026-09-02 01:00','2026-09-30',freq='h',inclusive='left'))
    return data
def evaluate_local():
    data=get_final();out=BASE/'M03-04'
    if (out/'predicoes_locais.csv').exists():raise FileExistsError('Aplicação local já realizada.')
    started=now();torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        t=time.perf_counter();preds=legacy_predictions(data);legacy_seconds=time.perf_counter()-t
        preds['persistence']=data.last_observed.to_numpy();bundle=joblib.load(B2/'M03-03/point_bundle.joblib');preds['hgb_bloco2']=bundle['model'].predict(data[bundle['features']]);alternatives=joblib.load(ALT)
        for name,estimator in alternatives['models'].items():preds[name]=estimator.predict(data[alternatives['features']])
        interval=joblib.load(B2/'M05-01/interval_bundle.joblib');q=np.sort(np.column_stack([m.predict(data[interval['features']]) for m in interval['models']]),axis=1);preds['hgb_quantile_p50']=q[:,1];delta=interval['correction']
        cqr=np.column_stack([q[:,0]-delta,q[:,1],q[:,2]+delta])
        ibase=data[['forecast_origin','target_time','y24']].copy();ibase[['p10','p50','p90']]=q;ibase[['cqr_p10','cqr_p50','cqr_p90']]=cqr;ibase.to_csv(out/'intervalos_locais.csv',index=False)
        probs=joblib.load(B2/'M05-02/probability_bundle.joblib');raw=probs['model'].predict_proba(data[probs['features']])[:,1];cal=probs['calibrator'].predict_proba(logit_features(raw))[:,1];y=(data.last_observed-data.y24>=22.77).astype(int).to_numpy();policy=json.loads((B2/'M05-02/politica_congelada.json').read_text(encoding='utf-8'))
        if (policy['daily_budget'],policy['cost_fp'],policy['cost_fn'])!=(6,1,4):raise ValueError('Política não coincide com custos/capacidade protocolados')
        prows=[];conf=[];arows=[];daily=[];probdata=data[['forecast_origin','y24','last_observed']].copy();probdata['event']=y
        for name,p in [('raw',raw),('calibrated',cal),('frequency',np.full(len(y),probs['frequency']))]:
            prows.append(dict(method=name,**metricas_probabilidade(y,p)));conf.extend(confiabilidade(y,p,name));probdata['p_'+name]=p
            cut=policy['threshold'] if name=='calibrated' else .5;a=alarmes_causais(data.forecast_origin,p,cut,policy['daily_budget']);arows.append(dict(method=name,threshold=cut,**metricas_alarmes(y,a,policy['cost_fp'],policy['cost_fn'])));probdata['alarm_'+name]=a
            for day,group in pd.DataFrame({'day':data.forecast_origin.dt.date,'alarm':a}).groupby('day'):
                count=int(group.alarm.sum())
                if count>policy['daily_budget']:raise AssertionError('Orçamento diário violado')
                daily.append(dict(method=name,day=str(day),alarms=count,budget=policy['daily_budget']))
        arows.append(dict(method='never_alarm',threshold=None,**metricas_alarmes(y,np.zeros(len(y),dtype=bool))))
        pd.DataFrame(prows).to_csv(out/'metricas_probabilidades.csv',index=False);pd.DataFrame(arows).to_csv(out/'metricas_alarmes.csv',index=False);pd.DataFrame(conf).to_csv(out/'confiabilidade.csv',index=False);probdata.to_csv(out/'probabilidades.csv',index=False);pd.DataFrame(daily).to_csv(out/'orcamento_diario.csv',index=False)
    records=[]
    for name,p in preds.items():
        part=data[['forecast_origin','history_end','target_time','label_available_at','y24']].copy();part['method']=name;part['prediction']=p;records.append(part)
    pd.concat(records).to_csv(out/'predicoes_locais.csv',index=False);np.save(out/'contexto_final.npy',old_context(data)[:,:,0])
    dump(out/'infer_local.json',dict(started_at_utc=started,completed_at_utc=now(),command=sys.argv,exit_code=0,rows=671,legacy_all8_load_and_predict_seconds=legacy_seconds,models_refitted=False,versions=dict(python=platform.python_version(),torch=torch.__version__,numpy=np.__version__,pandas=pd.__version__),scope='Local models, original scalers/weights; legacy group timing includes loading all8; no isolated latency ranking'))
    print('Inferência local concluída671: nenhum ajuste ou seleção nova.')
def bootstrap_gains(actual,predictions):
    rng=np.random.default_rng(31);n=len(actual);starts=rng.integers(0,n,size=(2000,math.ceil(n/24)));idx=((starts[:,:,None]+np.arange(24))%n).reshape(2000,-1)[:,:n];ref=np.abs(actual-predictions['persistence']);rows=[]
    for name,p in predictions.items():
        delta=ref-np.abs(actual-p);samples=delta[idx].mean(axis=1);lo,hi=np.quantile(samples,[.025,.975]);rows.append(dict(method=name,mean_gain=float(delta.mean()),ci95_low=float(lo),ci95_high=float(hi),block_hours=24,repetitions=2000,seed=31))
    return rows
def summarize():
    verify();out=BASE/'M03-04';end=BASE/'M09-04'
    if (end/'resultado.json').exists():raise FileExistsError('Síntese final já existe.')
    data=get_final();saved=pd.read_csv(out/'predicoes_locais.csv',parse_dates=['forecast_origin']);preds={name:part.sort_values('forecast_origin').prediction.to_numpy() for name,part in saved.groupby('method')};assert all(len(p)==671 for p in preds.values())
    chrono=np.load(out/'chronos.npz');a=chrono['forecast'];levels=chrono['levels'];assert a.shape==(671,9,26) and list(levels)==[.1,.2,.3,.4,.5,.6,.7,.8,.9]
    preds['chronos_p50']=a[:,4,25];actual=data.y24.to_numpy();rows=[dict(method=name,**metric(actual,p)) for name,p in preds.items()];summary=pd.DataFrame(rows).sort_values('mae');summary.to_csv(out/'summary.csv',index=False)
    old=pd.read_csv(out/'intervalos_locais.csv');intervalrows=[]
    for name,q in [('hgb_raw',old[['p10','p50','p90']].to_numpy()),('hgb_cqr',old[['cqr_p10','cqr_p50','cqr_p90']].to_numpy()),('chronos_raw',a[:,[0,4,8],25])]:intervalrows.append(dict(method=name,**metricas_intervalo(actual,q)))
    pd.DataFrame(intervalrows).to_csv(out/'metricas_intervalos.csv',index=False)
    gains=bootstrap_gains(actual,preds);pd.DataFrame(gains).to_csv(out/'bootstrap_pareado.csv',index=False)
    costs=[];actions={**preds,'chronos_p20':a[:,1,25],'chronos_p80':a[:,7,25]}
    for name,p in actions.items():
        residual=actual-p
        for scenario,under,over in [('symmetric',1,1),('under_cost4',4,1),('over_cost4',1,4)]:costs.append(dict(method=name,scenario=scenario,cost_under=under,cost_over=over,relative_loss_mean=float((under*np.maximum(residual,0)+over*np.maximum(-residual,0)).mean())))
    pd.DataFrame(costs).to_csv(out/'custos.csv',index=False)
    part=data[['forecast_origin','history_end','target_time','label_available_at','y24']].copy();part['method']='chronos_p50';part['prediction']=preds['chronos_p50'];pd.concat([saved,part]).to_csv(out/'predictions.csv',index=False)
    family=[]
    for name in ['mlp','gru']:
        values=[r for r in rows if r['method'].startswith(name+'_')];family.append(dict(family=name,all_seeds=[17,29,41],median_mae=float(np.median([r['mae'] for r in values])),min_mae=min(r['mae'] for r in values),max_mae=max(r['mae'] for r in values),median_rmse=float(np.median([r['rmse'] for r in values]))))
    alarms=pd.read_csv(out/'metricas_alarmes.csv');policycost=float(alarms.loc[alarms.method.eq('calibrated'),'cost'].iloc[0]);never=float(alarms.loc[alarms.method.eq('never_alarm'),'cost'].iloc[0]);gain=next(r for r in gains if r['method']=='hgb_bloco2');coverage=next(r for r in intervalrows if r['method']=='hgb_cqr')
    daily=pd.read_csv(out/'orcamento_diario.csv')
    decision=dict(fixed_champion='hgb_bloco2',mean_gain_at_least2=gain['mean_gain']>=2,gain_ci_above_zero=gain['ci95_low']>0,cqr_coverage_within70_90=.7<=coverage['coverage']<=.9,cqr_width_at_most100=coverage['width']<=100,policy_cost_better_than_never=policycost<never,daily_alarm_limits_respected=bool((daily.alarms<=daily.budget).all()),maximum_daily_alarms=int(daily.alarms.max()),operational_data_contract_proven=False,promotion_authorized=False,no_reselection_on_final=True)
    result=dict(schema='renewcast-bloco3-final-result-v1',completed=True,completed_at_utc=now(),rows=671,source_receipt_sha256=sha256(DATA/'fonte.json'),freeze_sha256=sha256(SEAL),models_refitted=False,policy_changed=False,calibrators_changed=False,retrospective=True,new_snapshot_after_freeze=True,pretraining_overlap_verified=False,operational_approval=False,metrics=rows,intervals=intervalrows,neural_family_seed_summary=family,decision=decision,outputs={p.name:sha256(p) for p in out.iterdir() if p.is_file() and p.name!='resultado.json'})
    dump(out/'resultado.json',result);dump(end/'resultado.json',result);dump(end/'decisao_congelada_avaliada.json',decision);pd.DataFrame(rows).to_csv(end/'matriz_decisao.csv',index=False)
    text='# Avaliação final segregada — setembro2026\n\n671 origens comuns; contexto24, histórico até origem−2h, alvo+24h, índiceChronos25. Snapshot obtido somente após congelar código, modelos, escaladores, calibradores e política. Estudo retrospectivo, sem comprovação da versão publicada na origem.\n\n'+summary.to_string(index=False)+'\n\nCritérios predefinidos do candidato HGBbloco2:\n'+json.dumps(decision,ensure_ascii=False,indent=2)+'\n\nTodas as sementes neurais foram mantidas; os ajustes antigos não foram repetidos. O treino neural original e o ajuste B2 usam cortes diferentes, declarados nos protocolos. As probabilidades de classe são somente do classificador B2, não inferidas de quantis/points. Métricas/custos são pareados, sob as mesmas origens; custos são relativos hipotéticos. A seleção não foi refeita com setembro. Índices de latência e memória de processos distintos não representam benchmark estritamente equivalente. Sem CI/shadow/produção aprovados nem certificação de autonomia pessoal.\n'
    (out/'parecer.md').write_text(text,encoding='utf-8');(end/'parecer.md').write_text(text,encoding='utf-8');(end/'defesa_final.md').write_text(text,encoding='utf-8');print(summary.to_string(index=False));print(json.dumps(decision))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['preparar','verificar-adaptador','congelar','verificar','baixar','avaliar-local','sintetizar','executar-final']);a=p.parse_args()
    if a.action=='executar-final':
        receipt=BASE/'execucao_avaliacao_final.json'
        if receipt.exists():raise FileExistsError('Execução final já registrada; não repetir automaticamente.')
        phases=[];start=now();messages=[]
        class Tee:
            def write(self,s):messages.append(s);return sys.__stdout__.write(s)
            def flush(self):return sys.__stdout__.flush()
        def chronos():
            environment=os.environ.copy();environment.pop('PYTHONPATH',None);environment['PYTHONNOUSERSITE']='1'
            command=[str(ROOT/'.venvs/m09_3_chronos/Scripts/python.exe'),str(ROOT/'notebooks/bloco3_chronos_inferencia.py'),'--context',str(BASE/'M03-04/contexto_final.npy'),'--output',str(BASE/'M03-04/chronos.npz')]
            completed=subprocess.run(command,cwd=ROOT,env=environment,capture_output=True,text=True,encoding='utf-8',errors='replace')
            print(completed.stdout);print(completed.stderr)
            if completed.returncode:raise RuntimeError(f'Inferência offline Chronos retornou {completed.returncode}')
        success=False
        with contextlib.redirect_stdout(Tee()),contextlib.redirect_stderr(Tee()):
            try:
                for name,action in [('freeze',freeze),('source_download',download),('local_inference',evaluate_local),('chronos_offline_inference',chronos),('summary_without_reselection',summarize)]:
                    began=now();action();phases.append(dict(phase=name,started_at_utc=began,completed_at_utc=now(),exit_code=0))
                success=True
            except Exception:traceback.print_exc()
        log=BASE/'execucao_avaliacao_final.log';log.write_text(''.join(messages),encoding='utf-8')
        dump(receipt,dict(started_at_utc=start,completed_at_utc=now(),command=[sys.executable,*sys.argv],exit_code=0 if success else 1,completed_phases=phases,log_path=rel(log),log_sha256=sha256(log)))
        raise SystemExit(0 if success else 1)
    {'preparar':prepare,'verificar-adaptador':check_adapter,'congelar':freeze,'verificar':lambda:print(f'Selo conferido: {len(verify()["files"])} arquivos.'),'baixar':download,'avaliar-local':evaluate_local,'sintetizar':summarize}[a.action]()
if __name__=='__main__':main()
