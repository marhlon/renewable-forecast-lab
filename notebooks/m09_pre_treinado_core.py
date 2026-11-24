"""M09.3: download verificado e alinhamento temporal, sem treino."""
from __future__ import annotations
import hashlib
from pathlib import Path
import urllib.request
import numpy as np


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def preparar_snapshot(spec,directory,offline=False):
    """Reutiliza somente arquivos com tamanho/hash corretos. Nao envia dados."""
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    if spec['repo_id']!='amazon/chronos-bolt-tiny' or len(spec['revision'])!=40:
        raise ValueError('Identidade de modelo fora do protocolo.')
    if set(spec['files'])!={'config.json','README.md','model.safetensors'}:
        raise ValueError('Lista de arquivos do snapshot inesperada.')
    for name,expected in spec['files'].items():
        path=directory/name
        if path.is_file() and path.stat().st_size==expected['bytes'] and sha(path)==expected['sha256']:
            print(f'Reutilizando snapshot verificado: {name}',flush=True)
            continue
        if offline:raise FileNotFoundError(f'Snapshot ausente ou divergente em modo offline: {path}')
        url=f"https://huggingface.co/{spec['repo_id']}/resolve/{spec['revision']}/{name}"
        print(f'Obtendo arquivo publico do modelo: {name} ({expected["bytes"]/1024**2:.2f} MiB)',flush=True)
        temporary=path.with_suffix(path.suffix+'.part')
        try:
            with urllib.request.urlopen(url,timeout=60) as response,temporary.open('wb') as output:
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    output.write(chunk)
            if temporary.stat().st_size!=expected['bytes'] or sha(temporary)!=expected['sha256']:
                raise ValueError(f'Tamanho ou SHA256 do modelo divergente: {name}')
            temporary.replace(path)
        finally:
            if temporary.exists():temporary.unlink()
    return {name:sha(directory/name) for name in spec['files']}


def alinhar_quantis(forecast,quantile_levels,history_end,target_times):
    """Forecast[B,Q,P] -> P10/P50/P90[B], calculando o passo por timestamp.

    O primeiro passo ocorre uma hora depois de history_end. Nao confundir h24
    desde a origem com 24 passos desde a ultima medicao disponivel.
    """
    a=np.asarray(forecast,dtype=np.float64);levels=np.asarray(quantile_levels,dtype=float)
    end=np.asarray(history_end,dtype='datetime64[ns]');target=np.asarray(target_times,dtype='datetime64[ns]')
    if a.ndim!=3 or min(a.shape)<=0 or levels.shape!=(a.shape[1],):
        raise ValueError('Esperados forecast[B,Q,P] e niveis[Q].')
    if end.shape!=(a.shape[0],) or target.shape!=end.shape or np.isnat(end).any() or np.isnat(target).any():
        raise ValueError('Timestamps devem identificar cada exemplo, sem NaT.')
    if not np.isfinite(a).all() or not np.isfinite(levels).all() or ((levels<=0)|(levels>=1)).any():
        raise ValueError('Previsoes finitas e niveis em (0,1) sao obrigatorios.')
    if (np.diff(levels)<=0).any():raise ValueError('Niveis devem ser distintos e crescentes.')
    ns_hour=3_600_000_000_000
    difference=(target-end).astype('timedelta64[ns]').astype(np.int64)
    if (difference<=0).any() or (difference%ns_hour!=0).any():
        raise ValueError('Alvos devem estar horas inteiras depois do fim do historico.')
    lead=difference//ns_hour;index=lead-1
    if (index>=a.shape[2]).any():raise ValueError('A trajetoria prevista nao alcanca o alvo.')
    out={'lead_hours':lead,'index_zero_based':index}
    for name,tau in (('p10',.1),('p50',.5),('p90',.9)):
        matches=np.flatnonzero(np.isclose(levels,tau,rtol=0,atol=1e-12))
        if len(matches)!=1:raise ValueError(f'Quantil {tau} nao encontrado uma unica vez.')
        out[name]=a[np.arange(len(a)),matches[0],index]
    return out


def conferir_alinhamento(fn=alinhar_quantis):
    """Casos independentes com rotulos que revelam troca de eixo/passo."""
    levels=np.array([.1,.5,.9]);a=np.empty((2,3,26))
    for b in range(2):
        for q in range(3):a[b,q]=10000*b+100*q+np.arange(1,27)
    end=np.array(['2026-07-03T02','2026-07-04T02'],dtype='datetime64[ns]')
    targets=end+np.array([26,5],dtype='timedelta64[h]')
    saved=a.copy();a.setflags(write=False)
    result=fn(a,levels,end,targets)
    if set(result)!={'lead_hours','index_zero_based','p10','p50','p90'}:raise ValueError('Devolva as cinco chaves do contrato.')
    for k,expected in {'lead_hours':[26,5],'index_zero_based':[25,4],
                      'p10':[26,10005],'p50':[126,10105],'p90':[226,10205]}.items():
        np.testing.assert_array_equal(result[k],expected)
    np.testing.assert_array_equal(a,saved)
    cases=[(a[:,:,:24],levels,end,targets),(a,levels,end,end),
           (a,levels,end,end+np.timedelta64(30,'m')),(a,np.array([.1,.1,.9]),end,targets)]
    for args in cases:
        try:fn(*args)
        except ValueError:pass
        else:raise ValueError('Alinhamento invalido foi aceito.')
    return {'passed':True,'checks':['passo26_h24_d2','comprimentos_distintos_por_exemplo',
           'eixos_quantile_batch_time','entradas_preservadas',
           'trajetoria_curta_tempo_nao_horario_e_quantile_duplicado_rejeitados'],
           'example_correct_step':26,'example_wrong_step24_target':'2026-07-04T02:00:00',
           'example_required_target':'2026-07-04T04:00:00'}
