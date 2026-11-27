"""Empacota somente os arquivos necessarios e testa uma copia sem dados/modelos."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/fechamento_m00_m09/bloco3_engenharia/M06-02'
FILES=['.github/workflows/bloco3-contratos.yml','config/requirements_ci_bloco3.txt','config/ci_bloco3.json','scripts/verificar_ci_bloco3.py','src/renewable_forecast/__init__.py','src/renewable_forecast/bloco3_data.py','src/renewable_forecast/bloco3_ops.py','src/renewable_forecast/neural_gru.py','src/renewable_forecast/transformer_blocks.py','notebooks/bloco3_transferencia_neural.py','notebooks/m08_gru_autoral.py','tests/test_bloco3_data.py','tests/test_bloco3_ops.py','tests/test_bloco3_transferencia_neural.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    OUT.mkdir(parents=True,exist_ok=True);attempt=1
    while (OUT/f'copia_isolada_{attempt}').exists():attempt+=1
    target=OUT/f'copia_isolada_{attempt}'
    protocol=OUT/'protocolo.json' if not (OUT/'protocolo.json').exists() else OUT/f'adendo_copia_{attempt}.json'
    dump(protocol,dict(created_at_utc=now(),scope='CI package, isolated source-only copy and actual contract failures; no remote run claimed',repository='marhlon/renewable-forecast-lab',branch='codex/bloco3-ci-20261126',source_files={p:sha(ROOT/p) for p in FILES},tests='5 data +9ops +2neural; synthetic contracts only',ignored_inputs_included=False,previous_failure_preserved='First copy missed transitive dependency notebooks/m08_gru_autoral.py; corrected packaging, not model/test changes' if protocol.name!='protocolo.json' else None,remote_plan='two commits/runs, first deliberate lag failure then corrected; at most15minutes each, no merge/deploy',remote_access='GitHub connector returned404; owner confirmed destination; cached local auth may be checked only with approved publisher',operational_approval=False))
    for name in FILES:
        output=target/name;output.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,output)
    environment=os.environ.copy();environment['PYTHONPATH']=str(target/'src');environment['PYTHONNOUSERSITE']='1'
    commands=[([sys.executable,'scripts/verificar_ci_bloco3.py'],0),([sys.executable,'scripts/verificar_ci_bloco3.py','--contraprova'],1),([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','tests/test_bloco3_data.py','tests/test_bloco3_ops.py','tests/test_bloco3_transferencia_neural.py'],0)]
    executions=[]
    for i,(cmd,expected) in enumerate(commands):
        started=now();r=subprocess.run(cmd,cwd=target,env=environment,capture_output=True,text=True,encoding='utf-8',errors='replace');log=OUT/f'copia{attempt}_comando{i}.log';log.write_text(r.stdout+r.stderr,encoding='utf-8')
        executions.append(dict(command=cmd,started_at_utc=started,completed_at_utc=now(),exit_code=r.returncode,expected_exit=expected,log=log.name,log_sha256=sha(log)))
        if r.returncode!=expected:raise RuntimeError(f'Validacao isolada falhou: {log}')
        if expected==1:
            negative=json.loads(r.stdout);assert negative['invariant']=='lag2_exact_timestamp' and negative['passed'] is False
    dump(OUT/'manifesto_pacote_ci.json',dict(created_at_utc=now(),files={p:sha(ROOT/p) for p in FILES},all_bytes_match_isolated_copy=all(sha(ROOT/p)==sha(target/p) for p in FILES)))
    dump(OUT/'resultado.json',dict(completed_at_utc=now(),local_package_complete=True,isolated_source_copy_verified=True,environment='existing Conda packages, not a newly installed clean Python',executions=executions,remote_ci_executed=False,remote_access_pending=True,actual_failure_and_success_in_local_copy=True,ignored_models_or_raw_data_used=False,operational_approval=False))
    (OUT/'parecer.md').write_text('# CI remoto — pacote preparado e verificado localmente\n\nQuatorze arquivos explícitos compõem o workflow e seus contratos. A cópia isolada contém somente fonte/testes/configuração, sem brutos, modelos, cache ou recibos anteriores. O contrato normal passou, a contraprova retornou1 pela divergência lag2, e os16 testes passaram. A primeira cópia falhou por faltar a dependência transitiva m08_gru_autoral.py; o log foi preservado e o empacotamento corrigido antes da cópia posterior. A execução usa dependências já instaladas; não foi apresentada como instalação limpa em outro sistema. O YAML prevê Python3.12, dependências fixadas, PyTorchCPU2.7.1 e limite15min, sem merge/deploy.\n\nGitHub conectado retornou404 para o repositório confirmado pelo usuário. Sem URL/commit/log de Actions ainda, o aceite remoto permanece aberto. A publicação exige acesso do titular e não foi simulada por estes logs.\n',encoding='utf-8')
    print('Pacote CI pronto; copia sem dados/modelos validada, inclusive falha controlada. Sem execucao remota declarada.')
if __name__=='__main__':main()
