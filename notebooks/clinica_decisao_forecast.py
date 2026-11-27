"""M02/M03/M05: perdas de decisão sobre resultados M09.3 existentes; sem treino."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,uuid
from datetime import datetime,timezone
from pathlib import Path
import numpy as np

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_json(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def perda_assimetrica(y,acao,c_sub=4.,c_super=1.):
    """Custos relativos por MWmed: subestimação e superestimação, respectivamente."""
    y,acao=np.asarray(y,dtype=float),np.asarray(acao,dtype=float)
    if y.ndim!=1 or not len(y) or acao.shape!=y.shape:
        raise ValueError('Esperados dois vetores não vazios, com o mesmo tamanho.')
    if not np.isfinite(y).all() or not np.isfinite(acao).all():
        raise ValueError('Valores reais e ações devem ser finitos.')
    costs=np.asarray([c_sub,c_super],dtype=float)
    if not np.isfinite(costs).all() or (costs<=0).any():
        raise ValueError('Os dois custos devem ser finitos e positivos.')
    residual=y-acao
    return c_sub*np.maximum(residual,0)+c_super*np.maximum(-residual,0)

def verificar_contas():
    # Distribuição manual: P(Y=0)=0,7; P(Y=100)=0,3.
    y=np.array([0.]*7+[100.]*3)
    for action,symmetric,asymmetric in ((0.,30.,120.),(100.,70.,70.)):
        a=np.full(10,action)
        np.testing.assert_allclose(perda_assimetrica(y,a,1,1).mean(),symmetric)
        np.testing.assert_allclose(perda_assimetrica(y,a,4,1).mean(),asymmetric)
    r=np.array([-5.,0.,2.,10.]);tau=.8
    pinball=np.maximum(tau*r,(tau-1)*r)
    np.testing.assert_allclose(perda_assimetrica(r,np.zeros(4),4,1),5*pinball)
    for bad in ([np.nan]*4,[np.inf]*4):
        try:perda_assimetrica(bad,np.zeros(4))
        except ValueError:pass
        else:raise AssertionError('Entrada não finita foi aceita.')
    return {'manual_expected_losses_verified':True,'asymmetric_loss_equals_scaled_pinball':True,
            'nonfinite_inputs_rejected':True}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',required=True,type=Path,help='Uma execução M09.3 completa, explicitamente escolhida.')
    p.add_argument('--output-dir',type=Path,default=Path('reports/consolidacao/m02_m03_m05'))
    args=p.parse_args(argv);source=args.run_dir.resolve()
    r=json.loads((source/'resultado.json').read_text(encoding='utf-8-sig'))
    if r.get('schema')!='renewcast-pretrained-result-v1' or r.get('completed') is not True:
        raise ValueError('A entrada deve ser uma execução M09.3 completa.')
    for name,expected in r['output_sha256'].items():
        path=(source/name).resolve()
        if not path.is_relative_to(source) or sha(path)!=expected:raise ValueError(f'Saída ausente ou alterada: {name}')
    authored_checks=verificar_contas()
    aligned=read_csv(source/'alinhamento_alvos.csv');predictions=read_csv(source/'predictions.csv')
    origins=[row['forecast_origin'] for row in aligned];targets=[row['target_time'] for row in aligned]
    if len(set(origins))!=len(origins):raise ValueError('Origens repetidas.')
    y=np.asarray([float(row['target_generation']) for row in aligned])
    leads=np.asarray([(datetime.fromisoformat(row['target_time'])-datetime.fromisoformat(row['history_end'])).total_seconds()/3600 for row in aligned])
    if not np.all(leads==26):raise ValueError('Esta clínica mantém o contrato h24/d2 do experimento existente.')
    with np.load(source/'quantis_26_passos.npz',allow_pickle=False) as z:
        forecast,levels=z['forecast'],z['quantile_levels']
    if forecast.shape!=(len(y),len(levels),26):raise ValueError('Shape de trajetória incompatível.')
    policies={}
    keys=sorted({(row['method'],row['seed']) for row in predictions})
    for method,seed in keys:
        group=[row for row in predictions if row['method']==method and row['seed']==seed]
        group=sorted(group,key=lambda row:row['forecast_origin'])
        if [row['forecast_origin'] for row in group]!=origins or [row['target_time'] for row in group]!=targets:
            raise ValueError('Variantes sem as mesmas origens e alvos.')
        np.testing.assert_allclose([float(row['target_generation']) for row in group],y,rtol=0,atol=1e-12)
        label=method+(f'/seed={seed}' if seed else '')
        policies[label]=np.asarray([float(row['prediction']) for row in group])
    for q in (.2,.5,.8):
        indices=np.flatnonzero(np.isclose(levels,q,atol=1e-12,rtol=0))
        if len(indices)!=1:raise ValueError(f'Quantil {q} ausente ou duplicado.')
        value=np.asarray(forecast[:,indices[0],25],dtype=float)
        if q==.5:np.testing.assert_allclose(value,policies['chronos_bolt_tiny_zero_shot'],rtol=0,atol=1e-10)
        else:policies[f'chronos_decisao_p{round(100*q):02}']=value
    # Cenários declarados de finalidade didática; nenhum custo econômico foi estimado.
    scenarios=[('simetrico',1.,1.),('subestimar_custa_4',4.,1.),('superestimar_custa_4',1.,4.)]
    rows=[];blocks=[]
    for scenario,cu,co in scenarios:
        for policy,action in policies.items():
            error=y-action;loss=perda_assimetrica(y,action,cu,co)
            rows.append({'scenario':scenario,'policy':policy,'rows':len(y),'cost_under':cu,'cost_over':co,
                'theoretical_optimal_quantile':cu/(cu+co),'mean_relative_loss':float(loss.mean()),
                'mae_mwmed':float(np.abs(error).mean()),'rmse_mwmed':float(np.sqrt((error**2).mean())),
                'bias_observed_minus_action':float(error.mean()),'under_rate':float((error>0).mean())})
            for start in range(0,len(y),24):
                part=loss[start:start+24]
                blocks.append({'scenario':scenario,'policy':policy,'block':start//24+1,
                   'origin_start':origins[start],'rows':len(part),'mean_relative_loss':float(part.mean())})
    checks_before={name:sha(source/name) for name in r['output_sha256']}
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    out=args.output_dir.resolve()/run_id;out.mkdir(parents=True,exist_ok=False)
    for name,table in (('perdas_cenarios.csv',rows),('perdas_blocos_24h.csv',blocks)):
        with (out/name).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    assert checks_before=={name:sha(source/name) for name in r['output_sha256']}
    receipt={'schema':'renewcast-decision-clinic-v1','completed':True,'source_run_id':r['run_id'],
       'source_result_sha256':sha(source/'resultado.json'),'source_outputs_preserved':True,
       'policies':len(policies),'scenarios':scenarios,'rows_per_policy':len(y),
       'scope':'Post-hoc didactic analysis of an already explored development week; no new validation or policy selection.',
       'cost_unit':'Hypothetical relative loss per emission, weighted MWmed; not currency.',
       'optimal_quantile_statement':'Conditional optimum under the stated linear costs; model quantiles may be inaccurate.',
       'model_retrained':False,'new_inference':False,'operational_policy_approved':False,
       'checks':authored_checks,'code_sha256':sha(Path(__file__)),'numpy_version':np.__version__,
       'output_sha256':{n:sha(out/n) for n in ('perdas_cenarios.csv','perdas_blocos_24h.csv')}}
    write_json(out/'resultado.json',receipt)
    print('M02/M03/M05: mesmos alvos; custos hipotéticos; análise posterior, sem nova validação.')
    for row in rows:
        if row['scenario']=='subestimar_custa_4' and (row['policy'].startswith('hgb_24h') or row['policy'] in ('chronos_bolt_tiny_zero_shot','chronos_decisao_p80')):
            print(f"{row['policy']}: MAE={row['mae_mwmed']:.6f}; perda 4:1={row['mean_relative_loss']:.6f}")
    print(out)
    return 0
if __name__=='__main__':raise SystemExit(main())
