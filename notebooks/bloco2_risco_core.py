"""Cálculos de intervalos, probabilidades e orçamento causal do bloco 2."""
from __future__ import annotations
from math import ceil
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, log_loss


def ordenar_quantis(q):
    q=np.asarray(q,dtype=float)
    if q.ndim!=2 or q.shape[1]!=3 or not np.isfinite(q).all():
        raise ValueError("Esperado [n,3] finito para P10/P50/P90.")
    return np.sort(q,axis=1)


def correcao_cqr(y,q,alpha=0.2):
    y=np.asarray(y,dtype=float); q=ordenar_quantis(q)
    if y.ndim!=1 or len(y)!=len(q) or not len(y) or not np.isfinite(y).all() or not 0<alpha<1:
        raise ValueError("Calibração inválida.")
    scores=np.maximum.reduce([q[:,0]-y,y-q[:,2],np.zeros(len(y))])
    rank=ceil((len(y)+1)*(1-alpha))
    if rank>len(y): raise ValueError("Calibração insuficiente para o rank solicitado.")
    return float(np.sort(scores)[rank-1]),rank


def metricas_intervalo(y,q,correcao=0.0,alpha=0.2):
    y=np.asarray(y,dtype=float); q=ordenar_quantis(q)
    if y.ndim!=1 or len(y)!=len(q) or not len(y) or not np.isfinite(y).all() or not np.isfinite(correcao) or correcao<0 or not 0<alpha<1:
        raise ValueError("Avaliação de intervalo inválida.")
    lo=q[:,0]-correcao; hi=q[:,2]+correcao
    evaluated=np.column_stack([lo,q[:,1],hi])
    loss=[float(np.maximum(tau*(y-evaluated[:,j]),(tau-1)*(y-evaluated[:,j])).mean())
          for j,tau in enumerate((0.1,0.5,0.9))]
    score=(hi-lo)+2/alpha*np.maximum(lo-y,0)+2/alpha*np.maximum(y-hi,0)
    return {"n":len(y),"coverage":float(np.mean((y>=lo)&(y<=hi))),
        "width":float(np.mean(hi-lo)),"interval_score":float(np.mean(score)),
        "pinball_p10":loss[0],"pinball_p50":loss[1],"pinball_p90":loss[2],
        "pinball_mean":float(np.mean(loss)),"correction":float(correcao)}


def metricas_probabilidade(y,p):
    y=np.asarray(y); p=np.asarray(p,dtype=float)
    if y.ndim!=1 or p.shape!=y.shape or not len(y) or not np.isin(y,[0,1]).all() or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError("Classes/probabilidades inválidas.")
    return {"n":len(y),"positives":int(y.sum()),"prevalence":float(y.mean()),
        "brier":float(np.mean((p-y)**2)),
        "log_loss":float(log_loss(y,np.clip(p,1e-12,1-1e-12),labels=[0,1])),
        "average_precision":float(average_precision_score(y,p)) if y.sum()>0 else None}


def confiabilidade(y,p,method):
    y=np.asarray(y); p=np.asarray(p); bins=np.minimum((p*10).astype(int),9)
    rows=[]
    for k in range(10):
        mask=bins==k; n=int(mask.sum())
        rows.append({"method":method,"bin":k,"lower":k/10,"upper":(k+1)/10,"n":n,
            "mean_probability":float(p[mask].mean()) if n else None,
            "event_rate":float(y[mask].mean()) if n else None})
    return rows


def logit_features(p):
    p=np.asarray(p,dtype=float)
    if p.ndim!=1 or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError("p inválida.")
    p=np.clip(p,1e-6,1-1e-6)
    return np.log(p/(1-p)).reshape(-1,1)


def alarmes_causais(origins,p,limiar,budget=6):
    stamps=pd.DatetimeIndex(pd.to_datetime(origins))
    p=np.asarray(p,dtype=float)
    if len(stamps)!=len(p) or stamps.hasnans or not stamps.is_monotonic_increasing or not stamps.is_unique:
        raise ValueError("Origens devem ser únicas e crescentes.")
    if not np.isfinite(p).all() or ((p<0)|(p>1)).any() or type(budget) is not int or budget<0:
        raise ValueError("Probabilidades/orçamento inválidos.")
    if limiar is not None and not 0<=limiar<=1: raise ValueError("Limiar inválido.")
    result=np.zeros(len(p),dtype=bool); count={}
    for i,(stamp,score) in enumerate(zip(stamps,p)):
        day=stamp.date().isoformat()
        if limiar is not None and score>=limiar and count.get(day,0)<budget:
            result[i]=True; count[day]=count.get(day,0)+1
    return result


def metricas_alarmes(y,a,fp_cost=1,fn_cost=4):
    y=np.asarray(y).astype(bool); a=np.asarray(a).astype(bool)
    if y.shape!=a.shape or y.ndim!=1 or not len(y): raise ValueError("Alarmes inválidos.")
    tp=int(np.sum(y&a)); fp=int(np.sum(~y&a)); fn=int(np.sum(y&~a)); tn=int(np.sum(~y&~a))
    return {"n":len(y),"tp":tp,"fp":fp,"fn":fn,"tn":tn,"alarms":tp+fp,
        "cost":int(fp*fp_cost+fn*fn_cost),"cost_per_origin":float((fp*fp_cost+fn*fn_cost)/len(y)),
        "precision":tp/(tp+fp) if tp+fp else None,"recall":tp/(tp+fn) if tp+fn else None}


def selecionar_politica(origins,y,p,thresholds,budget=6):
    rows=[]
    for threshold in [*thresholds,None]:
        alarm=alarmes_causais(origins,p,threshold,budget)
        rows.append({"threshold":threshold,**metricas_alarmes(y,alarm)})
    chosen=min(rows,key=lambda r:(r["cost"],r["alarms"],-r["threshold"] if r["threshold"] is not None else -float("inf")))
    return chosen,rows


def metricas_regressao(y,p):
    error=np.asarray(y,dtype=float)-np.asarray(p,dtype=float)
    if error.ndim!=1 or not len(error) or not np.isfinite(error).all(): raise ValueError("Resíduos inválidos.")
    return {"n":len(error),"mae":float(np.abs(error).mean()),
        "rmse":float(np.sqrt(np.mean(error**2))),"bias_observed_minus_predicted":float(error.mean())}
