"""Duas rodadas Actions em branch isolada; nao faz merge ou deploy.

Publicacao deve ser aprovada: no maximo15min por rodada e pode consumir quota.
Usa autenticacao Git existente, nunca imprime ou grava credenciais.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,time
from urllib.request import Request,urlopen,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError
import publicar_ci_bloco3 as publisher
ROOT=Path(__file__).resolve().parents[1];OUT=publisher.OUT
def now():return datetime.now(timezone.utc).isoformat()
def save(name,d):publisher.dump(name,d)
def main():
    if (OUT/'execucao_ci_remoto.json').exists():
        previous=json.loads((OUT/'execucao_ci_remoto.json').read_text(encoding='utf-8'))
        if previous.get('exit_code')!=1 or previous.get('events_completed')!=[] or previous.get('error')!='HTTP Error 404: Not Found' or (OUT/'publicacao_falha.json').exists() or (OUT/'execucao_ci_remoto_tentativa1.json').exists():
            raise FileExistsError('Ciclo remoto ja registrado; nao repetir automaticamente.')
        source=(OUT/'execucao_ci_remoto.json').resolve();archive=(OUT/'execucao_ci_remoto_tentativa1.json').resolve()
        if not source.is_relative_to(ROOT) or not archive.is_relative_to(ROOT):raise ValueError('Arquivo fora do workspace')
        source.rename(archive)
        save('adendo_endpoint_github.json',{'registered_at_utc':now(),'reason':'First root repository URL ended with a slash, which GitHub REST returns404 even for public repos. Canonical URL removes slash; no branch or POST occurred in the first attempt.','previous_receipt_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'public_check':'actions/checkout/ returned404; actions/checkout returned200 via GitHub connector','code_change':'canonical root URL only; credential and branch/package remain unchanged','retuning_or_model_changes':False})
    token=publisher.credential();started=now();events=[]
    def request(path):
        req=Request('https://api.github.com/repos/'+publisher.REPO+('/'+path if path else ''),headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'renewcast-ci'})
        with urlopen(req,timeout=40) as r:return json.loads(r.read())
    def child(action):
        env=os.environ.copy();env['PYTHONUTF8']='1';env['PYTHONIOENCODING']='utf-8'
        r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/publicar_ci_bloco3.py'),action],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        if r.returncode:raise RuntimeError(r.stderr.strip() or 'Publicador falhou')
        print(r.stdout.strip(),flush=True)
    def wait_for(commit):
        deadline=time.monotonic()+15*60
        while time.monotonic()<deadline:
            runs=request('actions/runs?branch='+publisher.BRANCH+'&per_page=20')['workflow_runs'];matches=[r for r in runs if r['head_sha']==commit]
            if matches:
                run=matches[0];print(f'Actions {run["id"]}: {run["status"]} {run.get("conclusion")}',flush=True)
                if run['status']=='completed':return run
            else:print('Aguardando inicio do workflow para o commit isolado.',flush=True)
            time.sleep(20)
        raise TimeoutError('Limite de15min de observacao atingido; consultar execucao sem republicar.')
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):return None
    def evidence(run,label):
        jobs=request(f'actions/runs/{run["id"]}/jobs?per_page=100');save(label+'_jobs.json',jobs)
        logs=[]
        for job in jobs['jobs']:
            req=Request(f'https://api.github.com/repos/{publisher.REPO}/actions/jobs/{job["id"]}/logs',headers={'Authorization':'Bearer '+token,'User-Agent':'renewcast-ci'})
            try:
                response=build_opener(NoRedirect).open(req,timeout=40);content=response.read(8*1024**2+1)
            except HTTPError as exc:
                if exc.code!=302:raise
                # Never forward Authorization or persist a temporary signed URL.
                location=exc.headers['Location']
                with urlopen(Request(location,headers={'User-Agent':'renewcast-ci'}),timeout=40) as r:content=r.read(8*1024**2+1)
            if len(content)>8*1024**2:raise ValueError('Log excede limite de8MiB')
            path=OUT/f'{label}_job_{job["id"]}.log';path.write_bytes(content);logs.append({'file':path.name,'sha256':hashlib.sha256(content).hexdigest(),'job_id':job['id']})
        return {'run_id':run['id'],'commit':run['head_sha'],'conclusion':run['conclusion'],'html_url':run['html_url'],'logs':logs,'jobs_file':label+'_jobs.json'},jobs
    try:
        repo=request('');save('acesso_git_fora_restricao.json',{'checked_at_utc':now(),'repository':repo['full_name'],'private':repo['private'],'authenticated_git_credential_usable':True,'credential_values_persisted':False})
        child('publicar-falha');first=json.loads((OUT/'publicacao_falha.json').read_text(encoding='utf-8'));negative=wait_for(first['commit']);nr,jobs=evidence(negative,'actions_falha');events.append(nr)
        steps=[s for j in jobs['jobs'] for s in j.get('steps',[])]
        if negative['conclusion']!='failure' or not any(s['name']=='Verificar contrato temporal' and s['conclusion']=='failure' for s in steps):raise ValueError('Falha remota nao foi a contraprova temporal esperada; nao classificar como sucesso.')
        child('corrigir');second=json.loads((OUT/'publicacao_correcao.json').read_text(encoding='utf-8'));positive=wait_for(second['commit']);pr,jobs=evidence(positive,'actions_sucesso');events.append(pr)
        if positive['conclusion']!='success':raise ValueError('Rodada corrigida nao terminou com sucesso.')
        save('execucao_ci_remoto.json',{'started_at_utc':started,'completed_at_utc':now(),'exit_code':0,'branch':publisher.BRANCH,'runs':events,'negative_temporal_contract_confirmed':True,'positive_run_confirmed':True,'merged':False,'deployed':False,'credentials_printed_or_persisted':False,'operational_approval':False})
        print('CI remoto: falha esperada e sucesso confirmados, logs gravados; sem merge/deploy.',flush=True)
    except Exception as exc:
        save('execucao_ci_remoto.json',{'started_at_utc':started,'completed_at_utc':now(),'exit_code':1,'events_completed':events,'error':str(exc),'merged':False,'deployed':False,'operational_approval':False});raise
if __name__=='__main__':
    try:main()
    except Exception as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
