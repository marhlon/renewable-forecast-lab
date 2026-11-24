"""Executa M09.3 com ambiente privado e dependencias fixadas.

Uso: python scripts/executar_m09_3.py
Na primeira vez baixa dependencias CPU e 33 MiB de pesos publicos.
Nao instala nada no ambiente Conda chamador.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',type=Path)
    p.add_argument('--baseline-run-dir',type=Path)
    p.add_argument('--model-dir',type=Path)
    p.add_argument('--output-dir',type=Path)
    p.add_argument('--verificar',action='store_true')
    p.add_argument('--offline',action='store_true')
    p.add_argument('--autoria',nargs='?',type=Path,const=ROOT/'notebooks/m09_alinhamento_autoral.py')
    args=p.parse_args()
    if sys.version_info[:2]!=(3,12):
        raise RuntimeError('Use o Python3.12 do ambiente renewable-forecast: conda activate renewable-forecast.')
    if args.autoria is not None and not args.autoria.is_file():
        raise FileNotFoundError(f'Arquivo autoral nao encontrado: {args.autoria}')
    # Nao criar/instalar ambiente se as entradas essenciais estiverem ausentes.
    input_dir=(args.input_dir or ROOT/'dist/databricks/CJU_BA5EIGT/m07_3').resolve()
    if not args.verificar:
        if not (ROOT/'notebooks/m08_3_base.py').is_file():
            raise FileNotFoundError('Suporte notebooks/m08_3_base.py ausente. Use o arquivo ja entregue no pacote M08.3.')
        for name in ('manifesto_entrada.json','geracao.parquet','treino_referencia.parquet'):
            if not (input_dir/name).is_file():raise FileNotFoundError(f'Entrada ja usada no M08 ausente: {input_dir/name}')
        baseline=args.baseline_run_dir
        if baseline is None:
            pointer=ROOT/'reports/neural/CJU_BA5EIGT/m08_3_gru/latest_run.json'
            if not pointer.is_file():raise FileNotFoundError('Informe --baseline-run-dir com a pasta da execucao M08.3.')
            baseline=Path(json.loads(pointer.read_text())['directory'])
        if not (baseline/'resultado.json').is_file():raise FileNotFoundError(f'Baseline M08.3 ausente: {baseline}')
    lock=ROOT/'docs/requirements_m09_3.lock.txt'
    fingerprint=hashlib.sha256(lock.read_bytes()+b'torch==2.7.1+cpu').hexdigest()
    runtime=ROOT/'.venvs/m09_3_chronos'
    executable=runtime/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    marker=runtime/'renewcast_environment.json'
    environment=os.environ.copy()
    environment.pop('PYTHONPATH',None);environment.pop('PYTHONHOME',None)
    environment['PYTHONNOUSERSITE']='1';environment['HF_HUB_DISABLE_TELEMETRY']='1';environment['TOKENIZERS_PARALLELISM']='false'
    log_dir=ROOT/'reports/setup/m09_3';log_dir.mkdir(parents=True,exist_ok=True)
    def run(command,label):
        print(label,flush=True)
        with (log_dir/'instalacao.log').open('a',encoding='utf-8') as handle:
            process=subprocess.run(command,cwd=ROOT,env=environment,stdout=handle,stderr=subprocess.STDOUT,check=False)
        if process.returncode:
            raise RuntimeError(f'{label} falhou. Leia {log_dir/"instalacao.log"}. O Conda original foi preservado.')
    reuse=False
    if marker.is_file() and executable.is_file():
        old=json.loads(marker.read_text());reuse=old.get('requirements_sha256')==fingerprint
    if not reuse:
        if args.offline:raise RuntimeError('Ambiente privado ainda nao preparado. Execute uma vez com internet, sem --offline.')
        if not executable.is_file():
            print('Criando ambiente privado em .venvs/m09_3_chronos; Conda atual preservado.',flush=True)
            venv.EnvBuilder(with_pip=True,system_site_packages=False).create(runtime)
        run([str(executable),'-m','pip','install','--only-binary=:all:','torch==2.7.1+cpu','--index-url','https://download.pytorch.org/whl/cpu'],
             'Preparando PyTorch CPU fixado; primeiro download pode demorar')
        run([str(executable),'-m','pip','install','--only-binary=:all:','-r',str(lock)],
             'Preparando as demais dependencias fixadas')
        run([str(executable),'-m','pip','check'],'Conferindo compatibilidade das dependencias')
        marker.write_text(json.dumps(dict(requirements_sha256=fingerprint,python=str(executable),torch='2.7.1+cpu'),indent=2)+'\n')
    else:print('Reutilizando ambiente privado M09.3.',flush=True)
    # Detectar alteracoes posteriores no ambiente, sem confiar so no marcador.
    check_code='''import importlib.metadata as m,json,pathlib,torch
lock=pathlib.Path(__import__('sys').argv[1])
for line in lock.read_text().splitlines():
 if line.strip():
  name,version=line.split('==');assert m.version(name)==version,(name,m.version(name),version)
assert torch.__version__=='2.7.1+cpu',torch.__version__
from chronos import ChronosBoltPipeline
print('Ambiente privado conferido; CPU/float32, dois threads.')
'''
    subprocess.run([str(executable),'-c',check_code,str(lock)],cwd=ROOT,env=environment,check=True)
    command=[str(executable),str(ROOT/'notebooks/laboratorio_pre_treinado.py')]
    for name in ('input_dir','baseline_run_dir','model_dir','output_dir','autoria'):
        value=getattr(args,name)
        if value is not None:command.extend(['--'+name.replace('_','-'),str(value.resolve())])
    if args.verificar:command.append('--verificar')
    if args.offline:command.append('--offline')
    raise SystemExit(subprocess.run(command,cwd=ROOT,env=environment,check=False).returncode)


if __name__=='__main__':main()
