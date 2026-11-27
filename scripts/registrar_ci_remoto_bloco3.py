"""Reconcilia o aceite CI posterior, preservando a fotografia local anterior."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json
from conferir_ci_remoto_bloco3 import verify_remote
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reports/fechamento_m00_m09/bloco3_engenharia';CI=BASE/'M06-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def replace(path,old,new):
    text=path.read_text(encoding='utf-8')
    if old not in text:raise ValueError(f'Trecho não localizado em {path}: {old[:90]}')
    path.write_text(text.replace(old,new),encoding='utf-8')
def main():
    assert verify_remote()['valid']
    registry=ROOT/'config/roadmap_m00_m09.json';snapshot=BASE/'cadastro_antes_aceite_ci_remoto.json'
    if (BASE/'aceite_ci_remoto.json').exists():raise FileExistsError('Aceite posterior já registrado.')
    if registry.read_bytes()!=snapshot.read_bytes():raise ValueError('Cadastro mudou depois do snapshot; revisar diferença antes da migração.')
    audit=BASE/'auditoria_com_ci_remoto.json';assert json.loads(audit.read_text(encoding='utf-8'))['valid']
    review=ROOT/'docs/roadmap_m00_m09/Revisao_CI_Remoto_Bloco3.md';assert review.is_file()
    data=json.loads(registry.read_text(encoding='utf-8'));item=next(i for i in data['items'] if i['id']=='M06-02');item['historico_aceite_ci_remoto']={'snapshot':rel(snapshot),'estado':item['estado'],'criterios':deepcopy(item['criterios']),'bloqueio':deepcopy(item['bloqueio']),'revisao':item['revisao']}
    report=ROOT/'docs/roadmap_m00_m09/Relatorio_Engenharia_Bloco3.md';guide=ROOT/'docs/roadmap_m00_m09/Bloco_3_Execucao.md';readme=ROOT/'README.md';roadmap=ROOT/'docs/ROADMAP_M00_M09.md';agents=ROOT/'AGENTS.md'
    replace(report,'**11 entregas integralmente demonstradas no escopo aplicado**','**12 entregas integralmente demonstradas no escopo aplicado**')
    replace(report,'Sete IDs operacionais continuam abertos.','Seis IDs operacionais continuam abertos.')
    replace(report,'pacote CI testado; plano cloud preparado. CI remoto, shadow, continuidade e homologação do ambiente alvo permanecem abertos','CI remoto executado e auditado; plano cloud preparado. Shadow, continuidade e homologação do ambiente alvo permanecem abertos')
    text=report.read_text(encoding='utf-8');start=text.index('## 7. CI:');stop=text.index('## 8. Estado que fica imposto ao projeto')
    ci_section='''## 7. CI remoto — falha controlada e sucesso reais

O usuário confirmou `marhlon/renewable-forecast-lab`. A listagem inicial do conector não identificou instalações/repositórios e a primeira consulta retornou 404; isso não provou inexistência ou ausência definitiva de acesso. A checagem fora da restrição encontrou autenticação Git utilizável, sem mostrar ou gravar valores. A URL canônica confirmou o repositório público e permitido.

A primeira tentativa do publicador parou no GET inicial: uma barra final indevida na URL raiz da API provoca 404. O comportamento foi confirmado num repositório público de controle. O recibo foi arquivado, a URL corrigida e o adendo registrado antes da nova tentativa. Não houve POST ou criação de branch nessa tentativa inicial. Os modelos e o benchmark congelado não foram alterados.

Na branch `codex/bloco3-ci-20261126`, a execução autorizada produziu:

- [Falha controlada — run 45889419488](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889419488), commit `047d8662158793f3e0e393957f1a6b382f8f3296`: o passo **Verificar contrato temporal** rejeitou lag2=29 quando o correto era 28. A falha não foi de instalação ou infraestrutura.
- [Rodada corrigida — run 45889590759](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889590759), commit `a487f7c9f37951102cc2be9ff38830ea04ad5f52`: contrato normal, contraprova negativa e **16 testes aprovados**, em 2,50 s para o pytest.

O segundo commit é filho direto do primeiro e altera somente `config/ci_bloco3.json`, restaurando o controle de falha para falso. Workflow, guard e testes não foram removidos. Os logs reais foram salvos e conferidos por SHA-256. Os runners usaram Ubuntu 26.04, Python 3.12.16 e PyTorch 2.7.1+cpu, com dependências instaladas no ambiente hospedado; não foi ativado o Conda ou uma venv local do projeto.

O pacote seleciona 14 arquivos, dos quais 13 fontes permanecem equivalentes e um é a configuração do controle negativo. Dez arquivos aparecem como adicionados no commit inicial; os demais já existiam no parent. O checkout remoto contém também a árvore histórica rastreada, inclusive artefatos/venvs antigos. O workflow não os ativa: os contratos usam fixtures, e a cópia local contendo somente as 14 fontes também passou. Não se chama a árvore completa de checkout de um pacote de apenas 14 arquivos.

A primeira cópia local omitiu `m08_gru_autoral.py` e registrou 15 testes aprovados/um erro; o empacotamento foi corrigido em adendo antes da cópia posterior, sem alterar os testes. Esse histórico e o `resultado.json` da fase local foram preservados. O recibo atual da execução remota é `M06-02/execucao_ci_remoto.json`, e a [revisão específica](Revisao_CI_Remoto_Bloco3.md) aprova C1/C2 no escopo dos contratos executados.

Não houve merge, PR ou deploy; a `main` permaneceu no parent anterior. A [branch está disponível para revisão](https://github.com/marhlon/renewable-forecast-lab/compare/main...codex/bloco3-ci-20261126). Criar um PR acionaria outra rodada pelo trigger `pull_request`; nenhuma terceira rodada foi aberta por esta execução. O workflow reage a essa branch de ensaio e a PRs: integração à `main` e política de proteção continuam sujeitas à revisão do titular. Este aceite vale para os commits testados, sem aprovar versões futuras, modelos ou produção. Não foi apurada cobrança monetária de Actions.

'''
    report.write_text(text[:start]+ci_section+text[stop:],encoding='utf-8')
    replace(report,'Os 11 IDs de engenharia integralmente demonstrados neste bloco são M03-04, M05-04, M05-05, M06-03,','Os 12 IDs de engenharia integralmente demonstrados neste bloco são M03-04, M05-04, M05-05, M06-02, M06-03,')
    replace(report,'**M06-02/04/05/06/07/08/09 ficam abertos**','**M06-04/05/06/07/08/09 ficam abertos**')
    replace(report,'**34 itens validados no escopo declarado e 11 bloqueados**','**35 itens validados no escopo declarado e 10 bloqueados**')
    replace(report,'as sete pendências finais','as seis pendências operacionais finais')
    replace(report,'Os mesmos 16 foram repetidos com propósito distinto na cópia isolada do CI, para detectar dependências ocultas; não são 32 casos independentes.','Os mesmos 16 casos foram repetidos na cópia isolada e no Actions para conferir empacotamento/ambiente; não são 48 casos independentes.')
    replace(report,'Não executar o auditor diretamente sem `--output` novo: o padrão dele regrava seu recibo e invalidaria a identidade registrada no cadastro.','A versão posterior do auditor também exige arquivo novo e reconhece o recibo CI remoto; a fonte anterior foi arquivada junto da auditoria histórica, sem sobrescrever seu recibo.')
    replace(report,'não foi instalado bloqueio de push nem simulado CI remoto.','não foi instalado bloqueio de push; os dois runs de CI remoto foram efetivamente executados.')
    replace(guide,'Onze têm entrega integral de engenharia; três outros têm construção/teste local aceitos parcialmente. Sete IDs operacionais continuam abertos.','Doze têm entrega integral de engenharia; três outros têm construção/teste local aceitos parcialmente. Seis IDs operacionais continuam abertos.')
    replace(guide,'| CI | Workflow e cópia isolada com16testes; falha causal detectada | Conexão GitHub sem repositórios liberados; nenhuma execução remota |','| CI | Dois runs Actions reais: erro causal esperado e correção com16testes; logs/commits conferidos | Branch isolada; sem merge/deploy ou proteção de main ativada |')
    replace(guide,'1. **CI remoto:** conceder à conexão GitHub acesso a `marhlon/renewable-forecast-lab`; workflow/pacote/publicador já preparados. A conta foi confirmada, mas a conexão não possui instalações ou repositórios acessíveis e não há credencial em cache. Não foi criado commit remoto.','1. **CI remoto já executado:** revisar a branch `codex/bloco3-ci-20261126` para eventual integração à main. Os dois commits/runs foram aprovados no escopo do CI; não houve merge ou deploy. Abrir PR acionará uma nova rodada e depende da próxima ação do titular.')
    replace(readme,'**11 IDs integralmente validados e sete operacionais ainda abertos**','**12 IDs integralmente validados e seis operacionais ainda abertos**')
    replace(readme,'34 validados\nno escopo declarado e 11 bloqueados','35 validados\nno escopo declarado e 10 bloqueados')
    replace(readme,'O [workflow CI](.github/workflows/bloco3-contratos.yml) e a cópia de fonte isolada passaram\nnas verificações locais; a conexão GitHub não possui repositórios liberados, e não há\nexecução remota alegada.','O [workflow CI](.github/workflows/bloco3-contratos.yml) teve duas rodadas reais:\n[falha causal controlada](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889419488) e\n[correção com16testes aprovados](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889590759).\nA branch está separada; não houve merge ou deploy.')
    replace(roadmap,'11 IDs integralmente demonstrados e sete operacionais abertos','12 IDs integralmente demonstrados e seis operacionais abertos')
    replace(roadmap,'34 validados no escopo declarado e 11 bloqueados','35 validados no escopo declarado e 10 bloqueados')
    replace(roadmap,'M06-02/04/05/06/07/08/09 mantêm operação aberta','M06-04/05/06/07/08/09 mantêm operação aberta')
    replace(roadmap,'Workflow CI e plano cloud preparados não comprovam suas execuções remotas.','O CI passou nas duas rodadas remotas controladas, com revisão própria; o plano cloud continua sem implantação. A main não foi alterada.')
    replace(agents,'11 aceites integrais de engenharia e sete IDs operacionais abertos','12 aceites integrais de engenharia e seis IDs operacionais abertos')
    replace(agents,'para as 11 entregas aplicadas','para as 12 entregas aplicadas')
    replace(agents,'M06-02/04/05/06/07/08/09 e os quatro bloqueios M04 continuam abertos.','M06-04/05/06/07/08/09 e os quatro bloqueios M04 continuam abertos.')
    replace(agents,'A conexão GitHub retornou404 e zero instalações/repositórios; pacote CI/cópia isolada não são Actions remoto.','M06-02 passou em dois runs Actions reais: falha temporal esperada e correção com16testes. A checagem canônica/autenticação fora da restrição resolveu o acesso; os diagnósticos anteriores e o erro de URL foram preservados. A main não foi alterada; o aceite limita-se aos commits verificados, sem proteção de branch ou produção presumidas.')
    item['estado']='validado';item['portoes']=['engenharia','operacao'];item['natureza']='execucao_remota_de_contratos';item['titulo']='Executar CI remoto com falha controlada e correção verificadas';item['constatacao']='Dois runs reais no GitHub Actions, falha do guard temporal e sucesso dos16contratos em ambiente hospedado, com commits/logs/clone documentados. Sem merge/deploy ou aprovação de produção.'
    for c in item['criterios']:c['atendido']=True
    item['bloqueio']=None;item['revisao']={'responsavel':'Codex — revisão técnica separada de CI remoto e integração do agente principal','data':'2026-11-26','parecer':rel(review),'decisao':'aprovado'};item['fonte_estado_ci']=rel(CI/'execucao_ci_remoto.json')
    item['historico_ci_local_preservado']=rel(CI/'resultado.json')
    new_paths=[p for p in CI.iterdir() if p.is_file() and p.suffix in ['.json','.md','.log']]+[review,audit,ROOT/'scripts/conferir_ci_remoto_bloco3.py',ROOT/'scripts/executar_ci_remoto_bloco3.py',BASE/'auditar_bloco3_antes_ci_remoto.py.txt']
    names={e['path'] for e in item['evidencias']}
    item['evidencias'] += [{'path':rel(p),'sha256':sha(p),'kind':'prova_CI_remoto_posterior_ao_aceite_local'} for p in new_paths if rel(p) not in names]
    item['entregaveis'] += [rel(CI/'execucao_ci_remoto.json'),rel(CI/'publicacao_falha.json'),rel(CI/'publicacao_correcao.json')]
    for i in data['items']:
        if 'historico_bloco3' not in i:continue
        for e in i['evidencias']:
            if e['path'] in [rel(report),'scripts/auditar_bloco3.py']:e['sha256']=sha(ROOT/e['path'])
        extra=[audit,BASE/'auditar_bloco3_antes_ci_remoto.py.txt',ROOT/'scripts/conferir_ci_remoto_bloco3.py']
        known={e['path'] for e in i['evidencias']}
        i['evidencias'] += [{'path':rel(p),'sha256':sha(p),'kind':'auditoria_posterior_sem_alterar_produtores_congelados'} for p in extra if rel(p) not in known]
    mode=data['modo_de_execucao']['escopo_engenharia_bloco3'];mode['aceites_integrais']=12;mode['ids_operacionais_abertos'].remove('M06-02');mode['ci_remoto_comprovado']=True
    dump(registry,data)
    dump(BASE/'aceite_ci_remoto.json',{'registered_at_utc':datetime.now(timezone.utc).isoformat(),'previous_registry_snapshot':rel(snapshot),'previous_registry_sha256':sha(snapshot),'new_registry_sha256':sha(registry),'M06-02_criteria_satisfied':['C1','C2'],'block3_validated_ids':12,'block3_open':6,'total_validated':35,'total_blocked':10,'old_local_and_audit_receipts_preserved':True,'review_ci_sha256':sha(review),'old_auditor_source_sha256':sha(BASE/'auditar_bloco3_antes_ci_remoto.py.txt'),'current_auditor_source_sha256':sha(ROOT/'scripts/auditar_bloco3.py'),'new_audit_sha256':sha(audit),'models_retrained_or_final_data_retuned':False,'main_merged':False,'deployed':False,'operational_approval':False})
    print('CI real registrado:12 aceites de engenharia neste bloco;6 itens operacionais abertos;35/45 validados no escopo declarado.')
if __name__=='__main__':main()
