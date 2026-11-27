"""Confere recibos/logs reais do Actions sem rede, credencial ou sobrescrita."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/fechamento_m00_m09/bloco3_engenharia/M06-02'
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def verify_remote():
    result=read('execucao_ci_remoto.json')
    assert result['exit_code']==0 and result['negative_temporal_contract_confirmed'] and result['positive_run_confirmed']
    assert not result['merged'] and not result['deployed'] and not result['credentials_printed_or_persisted']
    negative,positive=result['runs'];assert [negative['conclusion'],positive['conclusion']]==['failure','success']
    assert negative['commit']==read('publicacao_falha.json')['commit'] and positive['commit']==read('publicacao_correcao.json')['commit']
    for run in result['runs']:
        assert run['html_url']==f'https://github.com/marhlon/renewable-forecast-lab/actions/runs/{run["run_id"]}'
        for entry in run['logs']:assert hashlib.sha256((OUT/entry['file']).read_bytes()).hexdigest()==entry['sha256']
    nj=read(negative['jobs_file'])['jobs'];pj=read(positive['jobs_file'])['jobs']
    assert any(s['name']=='Verificar contrato temporal' and s['conclusion']=='failure' for j in nj for s in j['steps'])
    assert all(s['conclusion']=='success' for j in pj for s in j['steps'])
    plain='\n'.join((OUT/e['file']).read_text(encoding='utf-8',errors='replace') for e in positive['logs'])
    plain=re.sub(r'\x1b\[[0-9;]*m','',plain)
    assert re.search(r'\b16 passed\b',plain)
    assert '3.12' in plain and 'torch' in plain
    return {'valid':True,'actual_remote_runs':2,'negative_temporal_guard_confirmed':True,'positive_tests':16,'logs_sha256_verified':True,'checker_models_executed':False,'checker_credentials_read':False,'merged':False,'deployed':False}
def main():print(json.dumps(verify_remote()))
if __name__=='__main__':main()
