"""Auditoria desta sessão: lê os anexos efetivamente recebidos e não faz inferência."""
from pathlib import Path
import sys, json, hashlib, math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
U = ROOT / 'upload'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'm093_entrega/notebooks'))
sys.path.insert(0, str(OUT))
from m09_pre_treinado_core import conferir_alinhamento
from m09_alinhamento_recebido import alinhar_quantis

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def same(a, b): np.testing.assert_allclose(a, b, rtol=1e-12, atol=1e-10, equal_nan=True)
def main():
    r = json.loads((U / 'resultado(1).json').read_text())
    mapping = {'summary.csv':'summary(9).csv','predictions.csv':'predictions(7).csv',
               'protocol.json':'protocol(7).json','conferencia.json':'conferencia(2).json',
               'relatorio.html':'relatorio(1).html'}
    hashes = {}
    for name, expected in r['output_sha256'].items():
        p = U / mapping.get(name, name)
        hashes[name] = {'uploaded_name':p.name,'actual':sha(p),'expected':expected}
        assert hashes[name]['actual'] == expected, name
    a = pd.read_csv(U / 'alinhamento_alvos.csv')
    pred = pd.read_csv(U / 'predictions(7).csv')
    summary = pd.read_csv(U / 'summary(9).csv')
    path = pd.read_csv(U / 'trajetorias_26_passos.csv')
    paired = pd.read_csv(U / 'comparacao_pareada.csv')
    batches = pd.read_csv(U / 'latencias_lotes.csv')
    arrays = np.load(U / 'quantis_26_passos.npz', allow_pickle=False)
    forecast, levels = arrays['forecast'], arrays['quantile_levels']
    assert forecast.shape == (168,9,26)
    origin = pd.to_datetime(a.forecast_origin)
    end, target = pd.to_datetime(a.history_end), pd.to_datetime(a.target_time)
    assert origin.is_unique and origin.diff().dropna().eq(pd.Timedelta(hours=1)).all()
    assert end.eq(origin-pd.Timedelta(hours=2)).all()
    assert target.eq(origin+pd.Timedelta(hours=24)).all()
    assert pd.to_datetime(a.target_available_at).eq(target+pd.Timedelta(hours=2)).all()
    check_author = conferir_alinhamento(alinhar_quantis)
    aligned = alinhar_quantis(forecast, levels, end.to_numpy(), target.to_numpy())
    for name, values in aligned.items(): same(values, a[name])
    assert np.all(aligned['lead_hours']==26) and np.all(aligned['index_zero_based']==25)
    for array in (forecast,levels): array.setflags(write=False)
    readonly = alinhar_quantis(forecast, levels, end.to_numpy(), target.to_numpy())
    for key in aligned: same(readonly[key], aligned[key])
    assert len(path)==168*26
    for i in range(168):
        p = path.iloc[26*i:26*(i+1)]
        same(p.lead_hours,np.arange(1,27))
        assert pd.to_datetime(p.forecast_origin).eq(origin.iloc[i]).all()
        assert pd.to_datetime(p.forecast_time).eq(end.iloc[i]+pd.to_timedelta(p.lead_hours,unit='h')).all()
        assert np.array_equal(p.selected_target.to_numpy(),np.arange(26)==25)
        for j,q in enumerate(levels): same(p[f'p{round(q*100):02}'],forecast[i,j])
    metrics=[];maxdiff=0
    assert len(summary)==10 and len(pred)==1680
    for row in summary.to_dict('records'):
        m = pred.method.eq(row['method']) & (pred.seed.isna() if pd.isna(row['seed']) else pred.seed.eq(row['seed']))
        g=pred.loc[m].sort_values('forecast_origin')
        assert len(g)==168 and pd.to_datetime(g.forecast_origin).reset_index(drop=True).equals(origin)
        same(g.target_generation,a.target_generation)
        e=g.target_generation.to_numpy()-g.prediction.to_numpy()
        values={'mae_mwmed':np.mean(abs(e)),'rmse_mwmed':np.sqrt(np.mean(e**2)),
                'bias_observed_minus_predicted_mwmed':np.mean(e)}
        for name,value in values.items():
            same(value,row[name]);maxdiff=max(maxdiff,abs(value-row[name]))
        metrics.append({'method':row['method'],'seed':None if pd.isna(row['seed']) else int(row['seed']),**values})
    chronos=pred.loc[pred.method.eq('chronos_bolt_tiny_zero_shot')].sort_values('forecast_origin')
    hgb=pred.loc[pred.method.eq('hgb_24h')].sort_values('forecast_origin')
    for key in ('p10','p50','p90'): same(chronos[key],aligned[key])
    y=a.target_generation.to_numpy(); lo,med,hi=(aligned[k] for k in ('p10','p50','p90'))
    reported=json.loads((U/'quantile_metrics.json').read_text());qmetrics={}
    for tau,qs in ((.1,lo),(.5,med),(.9,hi)):
        residual=y-qs;qmetrics[f'pinball_p{round(tau*100):02}']=float(np.maximum(tau*residual,(tau-1)*residual).mean())
    below,above=y<lo,y>hi
    qmetrics.update(coverage_80=float(np.mean(~below&~above)),below_p10=float(below.mean()),above_p90=float(above.mean()),
       mean_width_mwmed=float(np.mean(hi-lo)),interval_score_80=float(np.mean(hi-lo+10*np.maximum(lo-y,0)+10*np.maximum(y-hi,0))),
       crossing_rows=int(np.sum((lo>med)|(med>hi))),negative_p50_rows=int(np.sum(med<0)))
    for key,value in qmetrics.items(): same(value,reported[key]);same(value,r['interval_metrics'][key])
    eg=y-hgb.prediction.to_numpy();ec=y-med;gain=np.abs(eg)-np.abs(ec)
    same(paired.hgb_prediction,hgb.prediction);same(paired.mae_gain_hgb_minus_chronos,gain)
    same(gain.mean(),r['paired_mae_gain_vs_hgb']);same(math.fsum(batches.seconds),r['inference_seconds'])
    assert batches.rows.tolist()==[16]*10+[8]
    base_path=U/'predictions(6).csv'
    base_status='not available with required hash'
    proto=json.loads((U/'protocol(7).json').read_text())
    if base_path.is_file() and sha(base_path)==proto['baseline_hashes']['predictions.csv']:
        base=pd.read_csv(base_path);old=pred.loc[~pred.method.eq('chronos_bolt_tiny_zero_shot'),base.columns].reset_index(drop=True)
        pd.testing.assert_frame_equal(old,base,check_dtype=False,atol=1e-10,rtol=1e-12);base_status='1512 original baseline rows independently matched'
    raw_status='source parquet not attached with required hash'
    for f in U.glob('part-*.parquet'):
        if sha(f)==r['input_sha256']['geracao.parquet']:
            raw=pd.read_parquet(f); actual=raw.set_index('din_instante').val_geracao.reindex(pd.DatetimeIndex(target)).to_numpy();same(actual,y);raw_status='all targets independently matched to received source parquet'
    local_audit=json.loads((U/'auditoria_resultados.json').read_text()); diffs=[]
    for n,entry in hashes.items():
        claimed=local_audit['checked_hashes'].get('run/'+n)
        if claimed!=entry['actual']: diffs.append(n)
    byblock=[]
    for i in range(7):
        sl=slice(i*24,(i+1)*24);byblock.append({'block':i+1,'first_origin':str(origin.iloc[i*24]),'mae_hgb':float(abs(eg[sl]).mean()),'mae_chronos':float(abs(ec[sl]).mean()),'mean_gain':float(gain[sl].mean())})
    idx=np.argsort(gain);extremes=[]
    for tag,i in [('largest_loss',idx[0]),('largest_gain',idx[-1])]:
        extremes.append({'case':tag,'forecast_origin':str(origin.iloc[i]),'target_time':str(target.iloc[i]),'observed':float(y[i]),'hgb':float(hgb.prediction.iloc[i]),'chronos':float(med[i]),'absolute_error_gain':float(gain[i])})
    receipt={'schema':'renewcast-received-m093-review-v1','run_id_verified':r['run_id'],'all_received_output_hashes_match':True,'output_hashes':hashes,
      'authored_function_transcribed_from_message':True,'author_conformance_executed_here':check_author,'author_binary_file_not_received':True,
      'all_30_metrics_recalculated':True,'max_metric_abs_difference':maxdiff,'baseline_check':base_status,'source_check':raw_status,
      'point_metrics':metrics,'quantile_metrics':qmetrics,'inside':int((~below&~above).sum()),'below':int(below.sum()),'above':int(above.sum()),
      'wins':int((gain>0).sum()),'losses':int((gain<0).sum()),'mae_gain':float(gain.mean()),'mae_gain_pct':float(100*gain.mean()/abs(eg).mean()),
      'rmse_change_pct':float(100*(np.sqrt(np.mean(ec**2))/np.sqrt(np.mean(eg**2))-1)),
      'blocks_24_origins':byblock,'extremes':extremes,'recorded_inference_seconds':math.fsum(batches.seconds),
      'second_run_reported_by_uploaded_audit':local_audit['run_directory'],'second_run_different_artifacts':diffs,
      'second_run_result_not_attached':True,'second_run_not_independently_reconstructed':True,
      'no_inference_or_training_performed_by_this_review':True,'operational_approval':False}
    (OUT/'revisao_anexos.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    pd.DataFrame(byblock).to_csv(OUT/'ganhos_blocos_24h.csv',index=False)
    print(json.dumps({k:receipt[k] for k in ('run_id_verified','all_received_output_hashes_match','max_metric_abs_difference','baseline_check','source_check','wins','mae_gain','mae_gain_pct','rmse_change_pct','inside','second_run_different_artifacts','blocks_24_origins','extremes')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
