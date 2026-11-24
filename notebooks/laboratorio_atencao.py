"""M09.1: Q/K/V, mascara e posicao; uma janela real, sem treinamento.

python notebooks/laboratorio_atencao.py
python notebooks/laboratorio_atencao.py --autoria notebooks/m09_atencao_autoral.py --verificar
"""
from __future__ import annotations
import argparse
import hashlib
import html
import importlib.util
import json
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.nn import functional as F

from renewable_forecast.attention_math import atencao_escalada

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def gravar(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def conferir(fn):
    """Contraprovas de semantica, nao uma prova de qualidade de previsao."""
    checks=[];differences=[]
    rng=np.random.default_rng(1091)
    for batch,length,source,dim,values in ((1,2,2,2,1),(2,4,6,3,2),(3,5,5,4,3)):
        q=rng.normal(size=(batch,length,dim));k=rng.normal(size=(batch,source,dim));v=rng.normal(size=(batch,source,values))
        mask=rng.uniform(size=(length,source))>.4;mask[:,0]=True
        saved=[a.copy() for a in (q,k,v,mask)]
        for a in (q,k,v,mask):a.setflags(write=False)
        for allowed in (None,mask):
            actual=fn(q,k,v,allowed)
            if set(actual)!={'pesos','saida'}:raise ValueError('Retorne exatamente pesos e saida.')
            weights,output=np.asarray(actual['pesos']),np.asarray(actual['saida'])
            if weights.shape!=(batch,length,source) or output.shape!=(batch,length,values):raise ValueError('Shape da saida incorreto.')
            np.testing.assert_allclose(weights.sum(axis=-1),1.,atol=1e-12,rtol=0)
            if not np.isfinite(weights).all() or (weights<0).any():raise ValueError('Pesos invalidos.')
            if allowed is not None:
                assert np.all(weights[:,~allowed]==0)
            with torch.no_grad():
                expected=F.scaled_dot_product_attention(torch.tensor(q)[:,None],torch.tensor(k)[:,None],
                   torch.tensor(v)[:,None],attn_mask=None if allowed is None else torch.tensor(allowed),dropout_p=0.)[:,0].numpy()
            differences.append(float(np.max(np.abs(output-expected))))
            np.testing.assert_allclose(output,expected,atol=1e-12,rtol=0)
        for a,b in zip((q,k,v,mask),saved):np.testing.assert_array_equal(a,b)
    checks.append('numpy_vs_pytorch_retangular_batched_com_mascara_e_readonly')
    q=np.array([[[1.,0.]]]);k=np.array([[[np.sqrt(2)*np.log(3),0.],[0.,0.]]]);v=np.array([[[10.],[30.]]])
    manual=fn(q,k,v)
    np.testing.assert_allclose(manual['pesos'],[[[.75,.25]]],atol=1e-12,rtol=0)
    np.testing.assert_allclose(manual['saida'],[[[15.]]],atol=1e-12,rtol=0)
    checks.append('caso_manual_pesos_075_025_saida15')
    q=np.zeros((1,3,2));v=np.array([[[0.],[6.],[12.]]]);mask=np.tri(3,dtype=bool)
    causal=fn(q,q,v,mask);full=fn(q,q,v)
    np.testing.assert_allclose(causal['saida'][0,:,0],[0.,3.,6.],atol=1e-12,rtol=0)
    np.testing.assert_allclose(full['saida'][0,:,0],[6.,6.,6.],atol=1e-12,rtol=0)
    changed=v.copy();changed[:,-1]+=300
    perturbed=fn(q,q,changed,mask)
    np.testing.assert_array_equal(causal['saida'][:,:-1],perturbed['saida'][:,:-1])
    np.testing.assert_allclose(causal['saida'][:,-1],full['saida'][:,-1],atol=1e-12,rtol=0)
    checks += ['mascara_causal_prefixo_e_diagonal','perturbacao_de_posicao_posterior_bloqueada','ultima_consulta_igual_na_atencao_de_uma_camada']
    q=np.full((1,2,1),1000.);k=np.array([[[1000.],[999.]]]);v=np.array([[[1.],[2.]]])
    with np.errstate(over='raise',invalid='raise'):
        actual=fn(q,k,v)
    assert np.isfinite(actual['pesos']).all()
    checks.append('softmax_estavel_scores_grandes')
    for bad in (np.zeros((2,2),dtype=bool),np.ones((2,2),dtype=int),np.ones((1,2),dtype=bool)):
        try:fn(q,k,v,bad)
        except ValueError:pass
        else:raise ValueError('Mascara invalida aceita.')
    checks.append('linha_totalmente_bloqueada_e_mascara_incompativel_rejeitadas')
    q=rng.normal(size=(1,4,3));perm=np.array([2,0,3,1])
    a=fn(q,q,q)['saida'];b=fn(q[:,perm],q[:,perm],q[:,perm])['saida']
    np.testing.assert_allclose(b,a[:,perm],atol=1e-12,rtol=0)
    checks.append('equivariancia_sem_posicao')
    return dict(passed=True,checks=checks,checks_count=len(checks),
                max_difference_pytorch=max(differences),tolerance=1e-12)


def carregar_autoria(path):
    if path is None:return atencao_escalada
    spec=importlib.util.spec_from_file_location('m09_atencao_autoral',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.atencao_escalada


def svg_matrix(weights,title):
    cell=20; left=48;top=40;size=len(weights);parts=[]
    for i,row in enumerate(weights):
        for j,value in enumerate(row):
            opacity=.08+.92*float(value)/float(weights.max())
            parts.append(f'<rect x="{left+j*cell}" y="{top+i*cell}" width="19" height="19" fill="#1d4ed8" opacity="{opacity:.4f}"><title>consulta {i}, chave {j}: {value:.8f}</title></rect>')
    for i in range(size):
        parts.append(f'<text x="{left+i*cell+9}" y="28" text-anchor="middle" font-size="9">{i}</text>')
        parts.append(f'<text x="38" y="{top+i*cell+13}" text-anchor="end" font-size="9">{i}</text>')
    return f'<figure><figcaption>{html.escape(title)}</figcaption><svg viewBox="0 0 {left+size*cell} {top+size*cell}" role="img" aria-label="{html.escape(title)}">'+''.join(parts)+'</svg></figure>'


def executar(args,out,fn,checks):
    # Reutiliza o contrato ja distribuido, sem reabrir treinamento M08.
    from m08_3_base import carregar,dividir
    frame,x,y,incomplete,hashes,source=carregar(args.input_dir)
    parts=dividir(frame);fit=parts['ajuste']
    index=np.flatnonzero(frame.forecast_origin.eq(pd.Timestamp(args.origin)).to_numpy())
    if len(index)!=1:raise ValueError('Origem ausente no recorte elegivel M07.3.')
    i=int(index[0]);history=x[i:i+1]
    mean=x[fit].mean(axis=0);scale=x[fit].std(axis=0)
    z=(history-mean)/scale
    embedding=z*np.array([1.,.5,-.25,.75])[None,None,:]
    pos=np.arange(24,dtype=float)[:,None]
    frequencies=np.exp(-np.log(10000.)*np.arange(0,4,2)/4)
    position=np.zeros((24,4));position[:,0::2]=np.sin(pos*frequencies);position[:,1::2]=np.cos(pos*frequencies)
    rng=np.random.default_rng(1091)
    wq=rng.normal(scale=.5,size=(4,4));wk=rng.normal(scale=.5,size=(4,4))
    def make(values,include_position):
        e=values+(position[None] if include_position else 0)
        return e@wq,e@wk,history.copy()
    q,k,v=make(embedding,True)
    full=fn(q,k,v);mask=np.tri(24,dtype=bool);causal=fn(q,k,v,mask)
    permutation=rng.permutation(24)
    no_q,no_k,no_v=make(embedding,False)
    unpositioned=fn(no_q,no_k,no_v)['saida']
    permuted=fn(no_q[:,permutation],no_k[:,permutation],no_v[:,permutation])['saida']
    without_position_delta=float(np.max(np.abs(permuted-unpositioned[:,permutation])))
    # Reordena conteudos e valores, mantendo os indices de posicao fixos.
    e2=embedding[:,permutation]+position[None]
    with_position=fn(e2@wq,e2@wk,v[:,permutation])['saida']
    with_position_delta=float(np.max(np.abs(with_position-full['saida'][:,permutation])))
    np.testing.assert_allclose(causal['saida'][:,-1],full['saida'][:,-1],atol=1e-12,rtol=0)
    origin=frame.forecast_origin.iloc[i]
    times=pd.date_range(origin-pd.Timedelta(hours=25),origin-pd.Timedelta(hours=2),freq='h')
    pd.DataFrame(full['pesos'][0]).to_csv(out/'pesos_livres.csv',index_label='consulta')
    pd.DataFrame(causal['pesos'][0]).to_csv(out/'pesos_causais.csv',index_label='consulta')
    context=pd.DataFrame(dict(position=np.arange(24),measurement_time=times,generation=history[0,:,0],
                  represented_free=full['saida'][0,:,0],represented_causal=causal['saida'][0,:,0]))
    context.to_csv(out/'janela_e_representacoes.csv',index=False)
    gravar(out/'projecoes.json',dict(Wq=wq.tolist(),Wk=wk.tolist(),position_encoding=position.tolist(),
                                   trained=False,values='raw historical generation; no future target'))
    detail=dict(schema='renewcast-attention-lab-v1',completed=True,run_id=out.name,checks=checks,
                 forecast_origin=origin.isoformat(),history_start=times[0].isoformat(),history_end=times[-1].isoformat(),
                 horizon_hours=24,availability_delay_hours_assumed=2,context_hours=24,
                 q_shape=list(q.shape),k_shape=list(k.shape),v_shape=list(v.shape),weights_shape=list(full['pesos'].shape),
                 output_shape=list(full['saida'].shape),models_trained=False,forecast_metrics_computed=False,
                 random_projections_are_untrained=True,target_not_used_in_attention=True,
                 input_sha256=hashes,source_package_id=source['package_id'],
                 numpy=np.__version__,pytorch=torch.__version__,python=platform.python_version(),
                 permutation_difference_without_position=without_position_delta,
                 permutation_difference_with_fixed_positions=with_position_delta,
                 last_query_full_causal_difference=float(np.max(np.abs(causal['saida'][:,-1]-full['saida'][:,-1]))),
                 authorship_sha256=sha(args.autoria) if args.autoria else None,
                 code_sha256={Path(__file__).name:sha(__file__)},
                 scope='attention arithmetic on historical context; not a trained Transformer or pretrained model')
    gravar(out/'resultado.json',detail)
    page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>M09.1 Atencao</title>
<style>body{font:16px system-ui;max-width:1150px;margin:30px auto;padding:16px;color:#17223b}.matrices{display:flex;gap:25px}figure{margin:0;flex:1}svg{width:100%}td,th{padding:5px;border:1px solid #ddd}table{border-collapse:collapse;font-size:13px}.note{padding:14px;background:#fff7ed;border-left:4px solid #b45309}</style>
<h1>M09.1 — consultar uma janela, com e sem mascara</h1>
<p class="note">Projecoes fixas nao treinadas. As saidas sao representacoes ponderadas do historico; nao sao previsoes h24.</p>'''
    page+=f'<p>Origem: {origin}. Historico: {times[0]} a {times[-1]}. Cada linha e uma consulta; cada coluna e uma hora consultada. Escala visual relativa em cada painel.</p><div class="matrices">'
    page+=svg_matrix(full['pesos'][0],'Atencao livre no contexto conhecido')+svg_matrix(causal['pesos'][0],'Atencao causal por prefixo')+'</div>'
    page+='<h2>Medicoes e representacoes</h2>'+context.to_html(index=False, float_format=lambda valor: f"{valor:.6f}")
    page+=f'<p>Ultima consulta: diferenca livre/causal = {detail["last_query_full_causal_difference"]:.3g}. Permutacao sem posicao: {without_position_delta:.3g}; com posicoes fixas: {with_position_delta:.6f}.</p></html>'
    (out/'relatorio.html').write_text(page,encoding='utf-8')
    for name,expected in hashes.items():
        if sha(args.input_dir/name)!=expected:raise ValueError('Entrada alterada durante a execucao.')
    detail['output_sha256']={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='resultado.json'}
    gravar(out/'resultado.json',detail)
    gravar(args.output_dir/'latest_run.json',dict(directory=str(out.resolve()),run_id=out.name,resultado_sha256=sha(out/'resultado.json')))
    print(f'Janela real: {times[0]} a {times[-1]}; origem {origin}.')
    print(f'Q{q.shape}; K{k.shape}; V{v.shape}; pesos{full["pesos"].shape}; saida{full["saida"].shape}.')
    print(f'Ultima consulta livre/causal: delta={detail["last_query_full_causal_difference"]:.3g}.')
    print(f'Permutar sem posicao: delta={without_position_delta:.3g}; com posicoes fixas: delta={with_position_delta:.6f}.')
    print('Nenhum treino, forecast ou medicao de acuracia. Leia a aula para interpretar as mascaras.')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,default=ROOT/'dist/databricks/CJU_BA5EIGT/m07_3')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'reports/transformer/CJU_BA5EIGT/m09_1_atencao')
    parser.add_argument('--origin',default='2026-07-03 04:00:00')
    parser.add_argument('--autoria',type=Path)
    parser.add_argument('--verificar',action='store_true',help='Conferir matematica sem ler a serie ou treinar.')
    args=parser.parse_args(argv);torch.set_num_threads(2)
    output=args.output_dir/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);output.mkdir(parents=True,exist_ok=False)
    try:
        fn=carregar_autoria(args.autoria);checks=conferir(fn)
        gravar(output/'conferencia.json',dict(**checks,authorship_sha256=sha(args.autoria) if args.autoria else None))
        print(f'Conferencias aprovadas: {checks["checks_count"]} grupos; delta PyTorch={checks["max_difference_pytorch"]:.3g}.')
        if not args.verificar:executar(args,output,fn,checks)
        print(f'Resultados: {output.resolve()}')
    except Exception as exc:
        gravar(output/'failure.json',dict(completed=False,error_type=type(exc).__name__,error=str(exc)));raise


if __name__=='__main__':main()
