from __future__ import annotations
import argparse,hashlib,html,importlib.util,json,sys,time,uuid
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'))
from satmon.temporal import sincronizar_causal,verificar_contrato
DATA=PROJECT/'data/reference/esa_mission1_2007'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def json_write(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def csv_write(df,p):df.to_csv(p,index=False,compression={'method':'gzip','mtime':0} if p.suffix=='.gz' else None)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=PROJECT/'reports/m10_1')
    parser.add_argument('--autoria',type=Path,help='Arquivo com sincronizar_causal(tabelas,grade,tolerancia).')
    parser.add_argument('--verificar',action='store_true')
    args=parser.parse_args(argv)
    started=time.perf_counter();fn=sincronizar_causal
    if args.autoria:
        if not args.autoria.is_file():parser.error(f'Arquivo não encontrado: {args.autoria}')
        spec=importlib.util.spec_from_file_location('sincronizacao_aluno',args.autoria.resolve())
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        fn=module.sincronizar_causal
    checks=verificar_contrato(fn)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    out=args.output_dir.resolve()/run_id;out.mkdir(parents=True,exist_ok=False)
    json_write(out/'conferencia.json',checks)
    if args.verificar:
        print('Conferência aprovada: cinco grupos; nearest usaria amostra futura.');print(out);return 0
    source=json.loads((DATA/'source.json').read_text(encoding='utf-8'))
    for name,entry in source['files'].items():
        p=DATA/name
        if p.stat().st_size!=entry['bytes'] or sha(p)!=entry['sha256']:raise ValueError(f'Entrada alterada: {name}')
    tables={};profiles=[]
    for c in source['channels']:
        df=pd.read_csv(DATA/f'{c}.csv.gz')
        df.timestamp=pd.to_datetime(df.timestamp,utc=True).astype('datetime64[ns, UTC]')
        if df.timestamp.duplicated().any():raise ValueError(f'Instantes duplicados: {c}')
        delta=df.timestamp.sort_values().diff().dt.total_seconds().dropna()
        profiles.append({'channel':c,'raw_rows':len(df),'null_values':int(df.value.isna().sum()),
           'median_spacing_seconds':float(delta.median()),'p99_spacing_seconds':float(delta.quantile(.99)),
           'largest_spacing_seconds':float(delta.max()),'spacing_over_180s':int(delta.gt(180).sum())})
        tables[c]=df
    # pandas 3 pode criar a grade em us; a sincronização padroniza em ns.
    grid=pd.date_range('2007-01-01T00:00:00Z','2008-01-01T00:00:00Z',freq='90s',inclusive='left').astype('datetime64[ns, UTC]')
    aligned=fn(tables,grid,pd.Timedelta(seconds=180))
    # O exercício é confrontado com o resultado real, além das contas pequenas.
    if args.autoria:
        pd.testing.assert_frame_equal(aligned,sincronizar_causal(tables,grid,pd.Timedelta(seconds=180)),
                                      check_dtype=False,rtol=1e-12,atol=1e-10)
    if len(aligned)!=len(grid) or not pd.to_datetime(aligned.timestamp,utc=True).reset_index(drop=True).equals(pd.Series(grid)):
        raise ValueError('A sincronização perdeu ou alterou instantes da grade.')
    for row in profiles:
        c=row['channel'];usable=aligned[f'{c}_usable'];age=aligned[f'{c}_age_seconds']
        assert aligned.loc[usable,f'{c}_sample_time'].le(aligned.loc[usable,'timestamp']).all()
        assert age[usable].between(0,180).all()
        row.update(usable_grid_rows=int(usable.sum()),unusable_grid_rows=int((~usable).sum()),
                   usable_fraction=float(usable.mean()))
    aligned['all_channels_usable']=aligned[[f'{c}_usable' for c in tables]].all(axis=1)
    labels=pd.read_csv(DATA/'labels.csv');types=pd.read_csv(DATA/'anomaly_types.csv')
    events=labels.loc[labels.Channel.isin(tables)].merge(types,on='ID',how='left',validate='many_to_one')
    events.StartTime=pd.to_datetime(events.StartTime,utc=True);events.EndTime=pd.to_datetime(events.EndTime,utc=True)
    if events.Category.isna().any() or events.StartTime.gt(events.EndTime).any():raise ValueError('Metadados de eventos incompatíveis.')
    events=events.loc[events.StartTime.lt(grid[-1]+pd.Timedelta(seconds=90)) & events.EndTime.ge(grid[0])].copy()
    category_columns={'Anomaly':'anomaly_annotation','Rare Event':'rare_event_annotation','Communication Gap':'communication_gap_annotation'}
    annotations=pd.DataFrame({'timestamp':grid,**{v:False for v in category_columns.values()}})
    coverage=[]
    for event in events.itertuples(index=False):
        mask=(grid>=event.StartTime)&(grid<=event.EndTime)
        annotations.loc[mask,category_columns[event.Category]]=True
        usable=aligned[f'{event.Channel}_usable'].to_numpy()
        coverage.append({'ID':event.ID,'Channel':event.Channel,'StartTime':event.StartTime,'EndTime':event.EndTime,
           'Category':event.Category,'grid_rows_in_interval':int(mask.sum()),'usable_grid_rows_in_interval':int((mask&usable).sum())})
    annotations['unannotated']=~annotations[list(category_columns.values())].any(axis=1)
    event_coverage=pd.DataFrame(coverage)
    category_summary=[]
    for category,column in category_columns.items():
        group=events.loc[events.Category.eq(category)]
        category_summary.append({'category':category,'source_annotation_rows':len(group),
           'distinct_annotation_ids':group.ID.nunique(),'grid_rows_with_annotation':int(annotations[column].sum())})
    profile=pd.DataFrame(profiles);cat=pd.DataFrame(category_summary)
    csv_write(aligned,out/'grade_features.csv.gz');csv_write(annotations,out/'rotulos_grade.csv.gz')
    csv_write(profile,out/'perfil_canais.csv');csv_write(events,out/'eventos_fonte.csv');csv_write(event_coverage,out/'cobertura_eventos.csv')
    csv_write(cat,out/'categorias.csv')
    # Contraprova concreta é separada do recorte ESA real.
    t=pd.Timestamp('2007-01-01T00:00:00Z');small=pd.DataFrame({'timestamp':[t,t+pd.Timedelta(seconds=10)],'value':[0.,10.]})
    mini=sincronizar_causal({'c':small},pd.DatetimeIndex([t+pd.Timedelta(seconds=s) for s in (2,7,12)]),pd.Timedelta(seconds=5))
    csv_write(mini,out/'contraprova_sintetica.csv')
    summary={'schema':'satmon-m10-1-contract-v1','completed':True,'run_id':run_id,'source_doi':source['doi'],
      'source_spec_sha256':sha(DATA/'source.json'),'grid_rows':len(grid),'grid_step_seconds':90,'max_age_seconds':180,
      'all_channels_usable':int(aligned.all_channels_usable.sum()),'raw_rows_total':sum(p['raw_rows'] for p in profiles),
      'event_annotation_rows':len(events),'event_ids':events.ID.nunique(),'category_summary':category_summary,
      'physical_units_known':False,'availability_is_assumed':True,'measurement_axis_utc_interpretation_assumed':True,
      'grid_protocol_is_exploratory':True,'unannotated_is_not_proven_normal':True,
      'future_sample_used':False,'labels_used_as_features':False,'models_trained':False,'operational_approval':False,
      'checks':checks,'authorship_sha256':sha(args.autoria) if args.autoria else None,
      'code_sha256':{'runner':sha(Path(__file__)),'temporal.py':sha(PROJECT/'src/satmon/temporal.py')},
      'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__},
      'elapsed_seconds':time.perf_counter()-started}
    page='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>M10.1 — contrato ESA</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;line-height:1.5}table{border-collapse:collapse}th,td{padding:8px;border:1px solid #ddd}code{background:#eee}</style>'
    page+='<h1>ESA Mission1 — contrato temporal do P2</h1><p>Recorte real de 2007. Três canais do grupo 10; nomes/unidades anonimizados. Rótulos retrospectivos separados das features. Nenhum detector foi treinado.</p>'
    page+='<h2>Amostragem e frescor</h2>'+profile.round(6).to_html(index=False)
    page+='<h2>Anotações: ID, canal e intervalo</h2>'+cat.to_html(index=False)
    page+='<p>IDs não são contagens de amostras nem garantia de episódios independentes. Rare Event permanece distinto de Anomaly. Sem anotação não significa normalidade comprovada.</p>'
    page+='<h2>Eventos preservados</h2>'+event_coverage.to_html(index=False)
    page+='<h2>Contrato executado</h2><pre>'+html.escape(json.dumps(summary,ensure_ascii=False,indent=2))+'</pre>'
    (out/'relatorio.html').write_text(page,encoding='utf-8')
    summary['output_sha256']={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    json_write(out/'resultado.json',summary)
    json_write(args.output_dir.resolve()/'latest_run.json',{'run_id':run_id,'directory':str(out),'resultado_sha256':sha(out/'resultado.json')})
    print(f"ESA Mission1/2007: {summary['raw_rows_total']:,} medições; {len(grid):,} instantes da grade.")
    print(profile.to_string(index=False));print(cat.to_string(index=False))
    print('Cinco conferências aprovadas; rótulos e features separados; nenhum treino.')
    print(f'Relatório: {out / "relatorio.html"}')
    return 0
if __name__=='__main__':raise SystemExit(main())
