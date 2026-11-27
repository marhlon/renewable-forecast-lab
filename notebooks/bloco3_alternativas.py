"""M05-04: quatro candidatos fixos; seleção em junho e outubro exploratório."""
from __future__ import annotations
import argparse,json,sys,time,platform
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.venvs/bloco3-packages'))
import joblib,numpy as np,pandas as pd,sklearn
import lightgbm,catboost
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from threadpoolctl import threadpool_limits
from bloco2_modelagem_core import build_frame,load_series,fit_mask,period_mask,sha256
BASE=ROOT/'reports/fechamento_m00_m09/bloco3_engenharia'
OUT=BASE/'M05-04'
SOURCE=ROOT/'dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet'
POINT=ROOT/'reports/fechamento_m00_m09/bloco2_engenharia/M03-03/point_bundle.joblib'
FOLDS=[('2026-06-01','2026-06-08'),('2026-06-08','2026-06-15'),('2026-06-15','2026-06-22')]
CONFIGS=[('lightgbm',60),('lightgbm',120),('catboost',60),('catboost',120)]
def now():return datetime.now(timezone.utc).isoformat()
def rel(p):return Path(p).resolve().relative_to(ROOT).as_posix()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n',encoding='utf-8')
def metrics(y,p):
    e=np.asarray(y)-np.asarray(p)
    return dict(n=len(e),mae=float(np.abs(e).mean()),rmse=float(np.sqrt(np.mean(e*e))),bias_observed_minus_predicted=float(e.mean()))
def model(family,trees):
    if family=='lightgbm':
        return LGBMRegressor(n_estimators=trees,num_leaves=15,min_child_samples=20,learning_rate=.05,reg_lambda=.1,n_jobs=2,random_state=17,verbosity=-1,deterministic=True,force_col_wise=True)
    return CatBoostRegressor(iterations=trees,depth=4,learning_rate=.05,l2_leaf_reg=.1,loss_function='RMSE',random_seed=17,thread_count=2,allow_writing_files=False,verbose=False,bootstrap_type='No',random_strength=0)
def prepare():
    if (OUT/'protocolo.json').exists():raise FileExistsError('Protocolo já existe; preservar a rodada.')
    features=joblib.load(POINT)['features']
    dump(OUT/'protocolo.json',dict(created_at_utc=now(),id='M05-04',source=rel(SOURCE),source_sha256=sha256(SOURCE),point_bundle_sha256=sha256(POINT),code_sha256={rel(Path(__file__)):sha256(Path(__file__)),rel(ROOT/'notebooks/bloco2_modelagem_core.py'):sha256(ROOT/'notebooks/bloco2_modelagem_core.py')},features=features,folds=FOLDS,configs=[dict(family=f,trees=t,params=model(f,t).get_params()) for f,t in CONFIGS],selection='minimum pooled validation MAE per family; first configuration wins ties; no October tuning',cutoff='2026-07-01',strict_purge='label_available_at < validation/final cutoff',common_origins='504 development; training feature eligibility same as B2 33-feature common cohort',versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,lightgbm=lightgbm.__version__,catboost=catboost.__version__),installation='only two wheels in .venvs/bloco3-packages, no dependency upgrades in Conda; optional plotting dependencies not used',budget='4 configurations x 3 folds + 2 final fits, 60/120 trees, CPU two threads, no other tuning',october='already examined B2; exploratory comparison only after fit',reserved_final='September2026 acquired only after all integrated artifacts/code are frozen; no selection on this period',operational_approval=False,assistance='Codex engineering solution, not independent student authorship'))
    print('Protocolo M05-04 registrado antes dos ajustes.',flush=True)
def fit():
    protocol=json.loads((OUT/'protocolo.json').read_text(encoding='utf-8'))
    if (OUT/'alternatives.joblib').exists():raise FileExistsError('Ajuste já congelado.')
    if sha256(SOURCE)!=protocol['source_sha256']:raise ValueError('Fonte alterada')
    for p,h in protocol['code_sha256'].items():
        if sha256(ROOT/p)!=h:raise ValueError('Código mudou após protocolo')
    started=now();begin=time.perf_counter();frame=build_frame(load_series(SOURCE));features=protocol['features'];rows=[];all_predictions=[]
    with threadpool_limits(limits=2):
        for fold,(start,end) in enumerate(FOLDS,1):
            train=frame.loc[fit_mask(frame,start)];val=frame.loc[period_mask(frame,start,end)]
            assert len(val)==168 and train.label_available_at.lt(pd.Timestamp(start)).all()
            for family,trees in CONFIGS:
                estimator=model(family,trees);t=time.perf_counter();estimator.fit(train[features],train.y24);p=estimator.predict(val[features])
                rows.append(dict(fold=fold,family=family,trees=trees,train_n=len(train),seconds_fit_predict=time.perf_counter()-t,**metrics(val.y24,p)))
                pred=val[['forecast_origin','target_time','y24']].copy();pred['family']=family;pred['trees']=trees;pred['fold']=fold;pred['prediction']=p;all_predictions.append(pred)
                print(f'{family} trees={trees} fold={fold} MAE={rows[-1]["mae"]:.6f}',flush=True)
        ranking=[]
        for family,trees in CONFIGS:
            group=[r for r in rows if r['family']==family and r['trees']==trees]
            ranking.append(dict(family=family,trees=trees,n=sum(r['n'] for r in group),mae=float(np.mean([r['mae'] for r in group])),rmse=float(np.sqrt(np.mean([r['rmse']**2 for r in group]))),seconds_fit_predict=sum(r['seconds_fit_predict'] for r in group)))
        selected={f:min([r for r in ranking if r['family']==f],key=lambda r:(r['mae'],r['trees'])) for f in ['lightgbm','catboost']}
        train=frame.loc[fit_mask(frame,'2026-07-01')];models={}
        for f,r in selected.items():models[f]=model(f,r['trees']).fit(train[features],train.y24)
    joblib.dump(dict(models=models,features=features,selected=selected,train_cutoff='2026-07-01',source_sha256=sha256(SOURCE),frozen_at_utc=now()),OUT/'alternatives.joblib')
    pd.DataFrame(rows).to_csv(OUT/'folds.csv',index=False);pd.DataFrame(ranking).to_csv(OUT/'candidatos.csv',index=False);pd.concat(all_predictions).to_csv(OUT/'predicoes_dev.csv',index=False)
    dump(OUT/'freeze.json',dict(created_at_utc=now(),files={rel(p):sha256(p) for p in [Path(__file__),OUT/'protocolo.json',OUT/'alternatives.joblib',ROOT/'notebooks/bloco2_modelagem_core.py']},selected=selected,training_rows=len(train),maximum_label_available=str(train.label_available_at.max()),evaluation_source_opened=False))
    dump(OUT/'resultado.json',dict(completed=False,phase='fit_frozen',started_at_utc=started,completed_at_utc=now(),fit_seconds=time.perf_counter()-begin,command=sys.argv,exit_code=0,selected=selected,operational_approval=False))
    print('Duas famílias ajustadas e congeladas. Setembro continua fechado.',flush=True)
def october():
    freeze=json.loads((OUT/'freeze.json').read_text(encoding='utf-8'))
    for p,h in freeze['files'].items():
        if sha256(ROOT/p)!=h:raise ValueError('Congelamento divergente')
    if (OUT/'metricas_outubro.csv').exists():raise FileExistsError('Comparação já executada.')
    path=ROOT/'reports/fechamento_m00_m09/bloco2_engenharia/dados_avaliacao/geracao_CJU_BA5EIGT_2026_10.parquet'
    frame=build_frame(load_series(path));data=frame.loc[period_mask(frame,'2026-10-02 01:00','2026-10-31')].copy();assert len(data)==695
    bundle=joblib.load(OUT/'alternatives.joblib');rows=[];preds=[]
    with threadpool_limits(limits=2):
        for f,m in bundle['models'].items():
            t=time.perf_counter();p=m.predict(data[bundle['features']]);rows.append(dict(method=f,**metrics(data.y24,p),predict_seconds=time.perf_counter()-t))
            part=data[['forecast_origin','history_end','target_time','y24']].copy();part['method']=f;part['prediction']=p;preds.append(part)
    pd.DataFrame(rows).to_csv(OUT/'metricas_outubro.csv',index=False);pd.concat(preds).to_csv(OUT/'predicoes_outubro.csv',index=False)
    result=json.loads((OUT/'resultado.json').read_text(encoding='utf-8'));result.update(completed=True,phase='exploratory_october_complete',october_evaluated_at_utc=now(),october_metrics=rows,october_used_for_selection=False,output_sha256={p.name:sha256(p) for p in OUT.iterdir() if p.is_file() and p.name!='resultado.json'});dump(OUT/'resultado.json',result)
    text='# M05-04 — alternativas de boosting\n\nAjuste e seleção executados somente nas três semanas de junho; dois candidatos por família, orçamento fixado antes dos cálculos. Features/cortes/coortes iguais aos do bloco2. O ajuste final tem rótulos disponíveis antes de 01/07. Outubro já fora examinado: esta comparação é exploratória e não determina a seleção. Os números completos estão em candidatos.csv, folds.csv e metricas_outubro.csv.\n\n'+pd.DataFrame(rows).to_string(index=False)+'\n\nInstalação privada de LightGBM4.6.0 e CatBoost1.2.8; Conda preservado. Somente previsão pontual, sem alegar quantis ou probabilidades desses dois ajustes. Sem promoção operacional ou certificação de autoria independente. A avaliação final de setembro pertence ao protocolo integrado e não altera estes ajustes.\n'
    (OUT/'parecer.md').write_text(text,encoding='utf-8');print(pd.DataFrame(rows).to_string(index=False),flush=True)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['preparar','ajustar','outubro','completo']);a=p.parse_args()
    if a.action=='completo':
        prepare();fit();october();return
    {'preparar':prepare,'ajustar':fit,'outubro':october}[a.action]()
if __name__=='__main__':main()
