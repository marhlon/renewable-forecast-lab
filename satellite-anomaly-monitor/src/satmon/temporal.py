"""Sincronização causal com idade explícita, independente de rótulos."""
from __future__ import annotations
import numpy as np
import pandas as pd


def instantes_utc(values, name):
    """Exige timestamps com fuso; padroniza resolução para pandas 2 e 3."""
    raw = pd.Series(values, copy=True)
    if raw.empty:
        raise ValueError(f'{name} não pode ser vazio.')
    for value in raw:
        ts = pd.Timestamp(value)
        if pd.isna(ts) or ts.tzinfo is None or ts.utcoffset() is None:
            raise ValueError(f'{name} exige timestamps válidos com fuso.')
    return pd.to_datetime(raw, utc=True).astype('datetime64[ns, UTC]')


def sincronizar_causal(tabelas, grade, tolerancia):
    """Recebe {canal: DataFrame(timestamp,value)}, grade UTC e Timedelta >=0.

    Devolve timestamp e, por canal, value/sample_time/age_seconds/usable.
    Preserva a idade e o timestamp da última amostra até quando ela expira;
    apenas value vira NaN. O instante da medição é a disponibilidade ASSUMIDA.
    Não consulta rótulos e não modifica entradas.
    """
    if not isinstance(tabelas, dict) or not tabelas:
        raise ValueError('Informe um dicionário não vazio de canais.')
    tol = pd.Timedelta(tolerancia)
    if pd.isna(tol) or tol < pd.Timedelta(0):
        raise ValueError('tolerancia deve ser uma duração finita não negativa.')
    times = instantes_utc(grade, 'grade')
    if times.duplicated().any() or not times.is_monotonic_increasing:
        raise ValueError('grade deve ser crescente e sem duplicidades.')
    result = pd.DataFrame({'timestamp': times.to_numpy()})
    for canal, source in tabelas.items():
        if not isinstance(canal, str) or not canal.isidentifier():
            raise ValueError('Cada canal deve ter um nome identificador.')
        if not isinstance(source, pd.DataFrame) or set(source.columns) != {'timestamp','value'}:
            raise ValueError('Cada tabela deve conter exatamente timestamp e value.')
        data = source.copy(deep=True)
        data['timestamp'] = instantes_utc(data.timestamp.to_numpy(), canal).to_numpy()
        data['value'] = pd.to_numeric(data.value, errors='raise')
        if np.isinf(data.value.to_numpy(dtype=float)).any():
            raise ValueError('Infinito não é medição válida; NaN permanece desconhecido.')
        if data.timestamp.duplicated().any():
            raise ValueError(f'Instantes duplicados em {canal}; não escolher silenciosamente.')
        data = data.sort_values('timestamp').reset_index(drop=True)
        sample = f'{canal}_sample_time'
        data = data.rename(columns={'timestamp':sample,'value':f'{canal}_value'})
        result = pd.merge_asof(result, data, left_on='timestamp', right_on=sample,
                               direction='backward', allow_exact_matches=True)
        age = f'{canal}_age_seconds'
        usable = f'{canal}_usable'
        result[age] = (result.timestamp-result[sample]).dt.total_seconds()
        result[usable] = (result[sample].notna() & result[age].ge(0)
                          & result[age].le(tol.total_seconds())
                          & result[f'{canal}_value'].notna())
        result.loc[~result[usable], f'{canal}_value'] = np.nan
    columns = ['timestamp']
    for canal in tabelas:
        columns += [f'{canal}_value', f'{canal}_sample_time',
                    f'{canal}_age_seconds', f'{canal}_usable']
    return result[columns]


def verificar_contrato(fn=sincronizar_causal):
    """Contas com relógios diferentes; falham com nearest, ffill livre ou mutação."""
    t = pd.Timestamp('2007-01-01T00:00:00Z')
    source = pd.DataFrame({'timestamp':[t,t+pd.Timedelta(seconds=10)],'value':[0.,10.]})
    grade = pd.DatetimeIndex([t+pd.Timedelta(seconds=s) for s in (2,7,12)])
    before = source.copy(deep=True)
    got = fn({'c':source},grade,pd.Timedelta(seconds=5))
    expected_cols = ['timestamp','c_value','c_sample_time','c_age_seconds','c_usable']
    if got.columns.tolist()!=expected_cols or len(got)!=3:
        raise AssertionError('Preserve a grade e o contrato de colunas.')
    np.testing.assert_allclose(got.c_value,[0.,np.nan,10.],equal_nan=True)
    np.testing.assert_allclose(got.c_age_seconds,[2.,7.,2.])
    assert got.c_usable.tolist()==[True,False,True]
    pd.testing.assert_frame_equal(source,before)
    changed=source.copy();changed.loc[1,'value']=999.
    after=fn({'c':changed},grade,pd.Timedelta(seconds=5))
    pd.testing.assert_frame_equal(got.iloc[:2],after.iloc[:2])
    other=pd.DataFrame({'timestamp':[t+pd.Timedelta(seconds=1),t+pd.Timedelta(seconds=11)],'value':[100.,200.]})
    both=fn({'c':source,'d':other},grade,pd.Timedelta(seconds=5))
    np.testing.assert_allclose(both.d_value,[100.,np.nan,200.],equal_nan=True)
    exact=fn({'c':source},pd.DatetimeIndex([t,t+pd.Timedelta(seconds=5)]),pd.Timedelta(seconds=5))
    assert exact.c_usable.all() and exact.c_age_seconds.tolist()==[0.,5.]
    for bad,grid,tol in ((pd.concat([source,source.iloc[:1]]),grade,pd.Timedelta(seconds=5)),
                        (source,grade[::-1],pd.Timedelta(seconds=5)),
                        (source,grade,pd.Timedelta(seconds=-1))):
        try:fn({'c':bad},grid,tol)
        except (ValueError,TypeError):pass
        else:raise AssertionError('Duplicidade, grade invertida ou tolerância negativa aceitas.')
    nearest=pd.merge_asof(pd.DataFrame({'timestamp':grade}),source.rename(columns={'timestamp':'sample_time'}),
                         left_on='timestamp',right_on='sample_time',direction='nearest')
    assert nearest.sample_time.iloc[1]>grade[1]
    return {'passed':True,'groups':5,'checks':['valores_idades_e_expiracao','invariancia_ao_futuro',
       'multicanal_assincrono_e_sem_mutacao','fronteiras_exatas','entradas_invalidas'],
       'nearest_counterexample_uses_future_at_second_7':True}
