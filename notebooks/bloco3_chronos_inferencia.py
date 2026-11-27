"""Inferência offline única no runtime M09.3 preservado; nenhuma instalação/fit."""
from pathlib import Path
import argparse,json,time,os,hashlib,importlib.metadata
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import numpy as np,pandas as pd,torch
from chronos import ChronosBoltPipeline
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--context',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Previsões Chronos já existem; preservar primeira inferência.')
    context=np.load(a.context);assert context.shape==(671,24) and np.isfinite(context).all()
    torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    path=ROOT/'models/pretrained/chronos-bolt-tiny/a0e552de83495b5c28c14c71c374f3e33280b340'
    start=time.perf_counter();pipeline=ChronosBoltPipeline.from_pretrained(str(path),device_map='cpu',torch_dtype=torch.float32,local_files_only=True,use_safetensors=True,trust_remote_code=False);pipeline.model.eval();pipeline.model.requires_grad_(False)
    load=time.perf_counter()-start;values=torch.tensor(context,dtype=torch.float32)
    start=time.perf_counter()
    with torch.inference_mode():pipeline.predict(values[:1],prediction_length=26,limit_prediction_length=True)
    warmup=time.perf_counter()-start;forecasts=[];times=[]
    for i in range(0,len(values),16):
        start=time.perf_counter()
        with torch.inference_mode():out=pipeline.predict(values[i:i+16],prediction_length=26,limit_prediction_length=True)
        times.append({'start':i,'n':len(out),'seconds':time.perf_counter()-start});forecasts.append(out.numpy())
    forecasts=np.concatenate(forecasts)
    assert forecasts.shape==(671,9,26) and np.isfinite(forecasts).all()
    np.savez_compressed(a.output,forecast=forecasts,levels=np.asarray(pipeline.quantiles))
    a.output.with_suffix('.json').write_text(json.dumps({'model':'amazon/chronos-bolt-tiny','revision':path.name,'rows':671,'context':24,'steps_after_history_end':26,'target_index_zero_based':25,'context_sha256':hashlib.sha256(a.context.read_bytes()).hexdigest(),'forecast_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'load_seconds':load,'warmup_seconds':warmup,'prediction_seconds':sum(r['seconds'] for r in times),'batches':times,'torch':torch.__version__,'numpy':np.__version__,'pandas':pd.__version__,'versions':{n:importlib.metadata.version(n) for n in ['chronos-forecasting','transformers','safetensors']},'optimizer_steps':0,'weights_finetuned':False,'offline':True,'device':'cpu','threads':2},indent=2)+'\n',encoding='utf-8')
    print('Chronos offline: 671 origens, nenhum ajuste; saída preservada.')
if __name__=='__main__':main()
