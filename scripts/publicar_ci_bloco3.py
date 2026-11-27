"""Publica APENAS o pacote CI revisado em branch separada; nunca faz merge.

Credencial existente vem do Git Credential Manager em memoria e nunca e impressa.
Acao requires approval: cria branch/commit e pode consumir minutos do Actions.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,base64,json,os,subprocess,sys
from urllib.request import Request,urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/fechamento_m00_m09/bloco3_engenharia/M06-02'
REPO='marhlon/renewable-forecast-lab';BRANCH='codex/bloco3-ci-20261126'
def now():return datetime.now(timezone.utc).isoformat()
def dump(name,d):(OUT/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def credential():
    environment=os.environ.copy();environment['GCM_INTERACTIVE']='Never';environment['GIT_TERMINAL_PROMPT']='0'
    r=subprocess.run(['git','-c','credential.interactive=never','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,env=environment,timeout=40)
    fields=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
    if r.returncode or not fields.get('password'):raise RuntimeError('Git Credential Manager nao forneceu credencial em cache; autorize acesso ao repositorio, sem enviar tokens no chat.')
    return fields['password']
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['publicar-falha','corrigir','status','verificar-credencial']);a=p.parse_args()
    token=credential()
    if a.action=='verificar-credencial':
        print('Credencial Git em cache disponivel; nenhum valor exposto nem requisicao remota realizada.');return
    def api(path,method='GET',data=None):
        body=json.dumps(data).encode() if data is not None else None
        request=Request('https://api.github.com/repos/'+REPO+('/'+path if path else ''),data=body,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json','User-Agent':'renewcast-ci'} )
        try:
            with urlopen(request,timeout=40) as response:return json.loads(response.read() or b'{}')
        except HTTPError as exc:
            payload=json.loads(exc.read() or b'{}');raise RuntimeError(f'GitHub HTTP{exc.code}: {payload.get("message","request failed")}') from None
    repo=api('')
    if a.action=='status':
        runs=api('actions/runs?branch='+BRANCH+'&per_page=10')
        result={'checked_at_utc':now(),'runs':[{k:r.get(k) for k in ['id','head_sha','status','conclusion','html_url','created_at','updated_at']} for r in runs.get('workflow_runs',[])]};dump('actions_status.json',result);print(json.dumps(result));return
    manifest=json.loads((OUT/'manifesto_pacote_ci.json').read_text(encoding='utf-8'))
    import hashlib
    for name,digest in manifest['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('Pacote local mudou apos verificacao: '+name)
    if a.action=='publicar-falha':
        if (OUT/'publicacao_falha.json').exists():raise FileExistsError('Publicacao ja registrada; consultar status.')
        base=api('git/ref/heads/'+repo['default_branch'])['object']['sha'];parent=api('git/commits/'+base);entries=[]
        for name in manifest['files']:
            content=(ROOT/name).read_bytes()
            if name=='config/ci_bloco3.json':content=json.dumps({'inject_lag_failure':True,'purpose':'intentional negative CI run, never merge this state'}).encode()
            blob=api('git/blobs','POST',{'content':base64.b64encode(content).decode(),'encoding':'base64'})
            entries.append({'path':name,'mode':'100644','type':'blob','sha':blob['sha']})
        tree=api('git/trees','POST',{'base_tree':parent['tree']['sha'],'tree':entries})
        commit=api('git/commits','POST',{'message':'ci: exercise temporal contract failure on isolated branch','tree':tree['sha'],'parents':[base]})
        api('git/refs','POST',{'ref':'refs/heads/'+BRANCH,'sha':commit['sha']})
        result=dict(published_at_utc=now(),repository=REPO,branch=BRANCH,commit=commit['sha'],html_url='https://github.com/'+REPO+'/commit/'+commit['sha'],deliberate_failure=True,merged=False,deployed=False)
        dump('publicacao_falha.json',result);print(json.dumps(result))
    else:
        prior=json.loads((OUT/'publicacao_falha.json').read_text(encoding='utf-8'));runs=api('actions/runs?branch='+BRANCH+'&per_page=10')['workflow_runs'];negative=[r for r in runs if r['head_sha']==prior['commit'] and r['status']=='completed' and r['conclusion']=='failure']
        if not negative:raise RuntimeError('Aguardar falha remota concluida antes do segundo commit.')
        ref=api('git/ref/heads/'+BRANCH)['object']['sha']
        if ref!=prior['commit']:raise ValueError('Branch mudou externamente; nao atualizar.')
        parent=api('git/commits/'+ref);blob=api('git/blobs','POST',{'content':base64.b64encode((ROOT/'config/ci_bloco3.json').read_bytes()).decode(),'encoding':'base64'});tree=api('git/trees','POST',{'base_tree':parent['tree']['sha'],'tree':[{'path':'config/ci_bloco3.json','mode':'100644','type':'blob','sha':blob['sha']}]});commit=api('git/commits','POST',{'message':'ci: restore valid temporal contract after negative control','tree':tree['sha'],'parents':[ref]});api('git/refs/heads/'+BRANCH,'PATCH',{'sha':commit['sha'],'force':False});result=dict(published_at_utc=now(),commit=commit['sha'],negative_run_url=negative[0]['html_url'],branch=BRANCH,merged=False,deployed=False);dump('publicacao_correcao.json',result);print(json.dumps(result))
if __name__=='__main__':
    try:main()
    except Exception as exc:
        OUT.mkdir(parents=True,exist_ok=True);record=dict(recorded_at_utc=now(),command=sys.argv,error=str(exc),remote_ci_approved=False,credential_printed=False);dump('bloqueio_publicacao.json',record);print(str(exc),file=sys.stderr);raise SystemExit(1)
