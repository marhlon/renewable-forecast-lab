"""Guard temporal executavel sem bruto/modelos; inclui contraprova negativa."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
from renewable_forecast.bloco3_data import causal_gold,make_silver
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contraprova',action='store_true');a=p.parse_args()
    cfg=json.loads((ROOT/'config/ci_bloco3.json').read_text(encoding='utf-8'))
    timestamps=pd.date_range('2026-10-01',periods=40,freq='h')
    raw=pd.DataFrame(dict(id_ons='a',din_instante=timestamps,val_geracao=np.arange(40,dtype=float),nom_usina='fixture',nom_tipousina='EOL'))
    silver,quarantine=make_silver(raw);gold=causal_gold(silver,['a']);row=gold.iloc[30].copy()
    if a.contraprova or cfg['inject_lag_failure']:row['lag2']=29.0
    correct=bool(row['lag2']==28.0 and row['target']==31.0 and len(quarantine)==0)
    print(json.dumps(dict(passed=correct,invariant='lag2_exact_timestamp',expected_lag2=28,observed_lag2=float(row['lag2']),external_files_or_models_used=False,operational_approval=False)))
    return 0 if correct else 1
if __name__=='__main__':raise SystemExit(main())
