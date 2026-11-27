"""Registra 11 aceites aplicados; conserva sete IDs operacionais abertos."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reports/fechamento_m00_m09/bloco3_engenharia'
VALID=['M03-04','M05-04','M05-05','M06-03','M07-01','M07-02','M07-03','M08-02','M08-03','M09-02','M09-04']
OPEN=['M06-02','M06-04','M06-05','M06-06','M06-07','M06-08','M06-09']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    registry=ROOT/'config/roadmap_m00_m09.json';before=registry.read_bytes();data=json.loads(before);snapshot=BASE/'cadastro_antes_alteracao.json'
    if snapshot.exists():raise FileExistsError('Migração já registrada; preservar histórico.')
    review=ROOT/'docs/roadmap_m00_m09/Revisao_Engenharia_Bloco3.md';report=ROOT/'docs/roadmap_m00_m09/Relatorio_Engenharia_Bloco3.md'
    audit=BASE/'auditoria_bloco3.json'
    for p in [review,report,audit]:
        if not p.is_file():raise FileNotFoundError(p)
    if json.loads(audit.read_text(encoding='utf-8')).get('valid') is not True:raise ValueError('Auditoria independente precisa aprovar os artefatos.')
    titles={'M03-04':'Avaliar modelos congelados em snapshot reservado retrospectivo','M06-03':'Demonstrar Model Registry e rollback no ambiente local','M07-02':'Medir coortes reais em um host sob recursos controlados','M08-03':'Aplicar adaptação neural e conferir preservação em novo contexto','M09-02':'Aplicar novo contrato de atenção e verificar vazamento indireto'}
    blocked={
        'M06-02':('Workflow e cópia de fonte isolada verificados; GitHub conectado retornou404 e listou zero instalações/repositórios; credencial Git em cache ausente. Não houve Actions remoto.','Liberar acesso do titular ao repositório confirmado, executar falha/sucesso reais e registrar URLs/commits/logs e clone com dependências limpas.'),
        'M06-04':('Ledger/replay local testados; contratos M04, CI, ambiente alvo e janela live ainda não comprovados.','Comprovar pré-condições M04/M06-02/07/08, congelar janela/modelo/política e observar emissões/chegadas reais e alvos conciliados sem comando de equipamentos.'),
        'M06-05':('48 emissões/reconciliações em replay não são continuidade; cobertura/classes prospectivas C3/C4 continuam sem observação real.','Operar a janela prospectiva com incidentes/recuperação e rótulos conciliados, medindo disponibilidade, latência, erro, intervalos e probabilidades, preservando C3/C4.'),
        'M06-06':('Detector, referência, contraprovas e resposta local construídos; não se demonstrou sustentação/triagem em fluxo vivo nem controle probabilístico de falsos alertas.','Após M06-05, observar drift no fluxo operacional e testar resposta do responsável sob orçamento implementado, sem retreino/promoção automática indevida.'),
        'M06-07':('Autenticação, limites e contrato passaram em loopback; o futuro ambiente de implantação não foi definido/homologado.','Definir exposição e ambiente alvo, responsável e ameaças; verificar novamente controles/segredos/incidentes nesse ambiente antes do shadow.'),
        'M06-08':('480 requisições e SLO local passaram; ensaio curto não comprova capacidade sustentada/custos reais e serviços acessórios do ambiente implantado.','Definir carga/SLO/teto no alvo e medir recursos, falhas, duração e custo observado; conservar a distinção entre estimativa e cobrança.'),
        'M06-09':('Plano cloud preparado; nenhum recurso, região/conta autorizada ou cobrança real foi produzido.','Titular definir conta/projeto/região/teto e autorizar criação delimitada; depois implantar/testar/reverter/encerrar recursos registrando custo real.')}
    for item in data['items']:
        ident=item['id']
        if ident not in VALID+OPEN:continue
        folder=BASE/ident
        for name in ['protocolo.json','resultado.json','parecer.md']:
            if not (folder/name).is_file():raise FileNotFoundError(folder/name)
        item['historico_bloco3']={k:deepcopy(item.get(k)) for k in ['titulo','natureza','estado','constatacao','portoes','depende_de','entregaveis','criterios','evidencias','revisao','bloqueio']};item['historico_bloco3']['snapshot']=rel(snapshot)
        item['modo_entrega']='engenharia_aplicada';item['human_response_required']=False;item['independent_learning_certified']=False;item['operational_approval']=False
        item['escopo_local']='Estudo local/retrospectivo ou contraprova explicitamente declarado; não certifica fonte operacional nem produção.'
        if ident in VALID:
            item['titulo']=titles.get(ident,item['titulo']);item['natureza']='entrega_de_engenharia';item['estado']='validado'
            item['constatacao']='Construção, execução e análise técnica demonstradas no recorte registrado; resultados negativos preservados. Sem certificação de autonomia ou produção.'
            other=[g for g in item['portoes'] if g=='ampliacao' or (ident=='M06-03' and g=='operacao')];item['portoes']=['engenharia',*other]
            for criterion in item['criterios']:criterion['atendido']=True
            if ident=='M03-04':item['criterios'][0]['descricao']='Congelar código, artefatos e critérios antes de obter snapshot reservado posterior aos ajustes, explicitando avaliação retrospectiva e ausência de comprovação de vintage histórico.'
            if ident=='M07-02':
                item['criterios'][0]['descricao']='Fixar três coortes reais, recursos, três repetições por motor, materialização e escopo de leitura/filtro/janela/agregação/escrita antes de medir; sem replicação sintética.'
                item['criterios'][1]['descricao']='Conferir nove pares e tempo/RSS, com plano observado DuckDB e limites de coorte/cache/um host; sem inferir AQE ou desempenho distribuído.'
            if ident=='M08-03':item['criterios'][1]['descricao']='Preservar modos mistos, parâmetros, gradientes, entradas e separação temporal; fornecer solução/análise assistida e contraprovas sem exigir resposta do usuário ou certificar autonomia.'
            if ident=='M09-02':item['criterios'][1]['descricao']='Fornecer e executar adaptação de contexto/máscaras, distinguindo disponibilidade na origem e no prefixo e demonstrando vazamento indireto; não certificar aprendizagem independente.'
            item['revisao']={'responsavel':'Codex — revisão técnica assistida e integração pelo agente principal','data':'2026-11-26','parecer':rel(review),'decisao':'aprovado'};item['bloqueio']=None
        else:
            item['estado']='bloqueado';item['bloqueio']={'motivo':blocked[ident][0],'condicao_desbloqueio':blocked[ident][1]};item['constatacao']=blocked[ident][0];item['revisao']=None
            item['aceite_local_parcial']={'demonstrado':True,'escopo':'Construção e evidências locais dos recibos; não satisfaz o aceite operacional integral do ID.','parecer_local':rel(folder/'parecer.md'),'criterios_operacionais_anteriores_preservados':True,'revisao_integrada':rel(review)}
        paths=[p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in ['.json','.md','.csv','.csv.gz','.npz','.npy','.py','.joblib','.pt','.skops','.txt','.yml','.yaml'] and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and 'copia_isolada' not in str(p)]
        common=[review,report,audit,ROOT/'scripts/auditar_bloco3.py',BASE/'congelamento_final.json',BASE/'dados_final/fonte.json',BASE/'recuperacao_relatorio_final.json']
        source={
            'M03-04':['notebooks/bloco3_benchmark.py','notebooks/bloco3_chronos_inferencia.py'],
            'M09-04':['notebooks/bloco3_benchmark.py','notebooks/bloco3_chronos_inferencia.py'],
            'M05-04':['notebooks/bloco3_alternativas.py'],
            'M05-05':['src/renewable_forecast/bloco3_data.py','notebooks/bloco3_dados_execucao.py','tests/test_bloco3_data.py','docs/roadmap_m00_m09/Bloco_3_Dados.md'],
        }.get(ident,[])
        if ident.startswith('M07-'):source+=['src/renewable_forecast/bloco3_data.py','notebooks/bloco3_dados_execucao.py','tests/test_bloco3_data.py','docs/roadmap_m00_m09/Bloco_3_Dados.md']
        if ident in ['M08-02','M08-03','M09-02']:source+=['notebooks/bloco3_transferencia_neural.py','tests/test_bloco3_transferencia_neural.py','docs/roadmap_m00_m09/Bloco_3_Transferencia_Neural.md']
        if ident.startswith('M06-') and ident!='M06-02':source+=['src/renewable_forecast/bloco3_ops.py','scripts/bloco3_operacao_local.py','tests/test_bloco3_ops.py','docs/roadmap_m00_m09/Bloco_3_Operacao_Local.md']
        if ident=='M06-02':source+=['.github/workflows/bloco3-contratos.yml','scripts/preparar_ci_bloco3.py','scripts/publicar_ci_bloco3.py','scripts/verificar_ci_bloco3.py','config/requirements_ci_bloco3.txt','config/ci_bloco3.json']
        paths=sorted(set(paths+common+[ROOT/p for p in source]));item['evidencias']=[{'path':rel(p),'sha256':sha(p),'kind':'evidencia_local_bloco3_com_escopo_declarado'} for p in paths]
        item['entregaveis']=[rel(p) for p in paths if p.parent==folder and p.suffix in ['.json','.md','.csv']]
    data['updated_at']='2026-11-26';data['modo_de_execucao'].update(bloco_ativo=3,blocos_engenharia_concluidos=[1,2,3],escopo_engenharia_bloco3={'aceites_integrais':11,'aceites_parciais_locais':['M06-06','M06-07','M06-08'],'ids_operacionais_abertos':OPEN,'fechamento_integral_operacional':False},proximo_bloco_planejado=None)
    snapshot.write_bytes(before);dump(registry,data);dump(BASE/'migracao_cadastro.json',dict(created_at_utc=datetime.now(timezone.utc).isoformat(),previous_registry_path=rel(snapshot),previous_registry_sha256=sha(snapshot),new_registry_sha256=sha(registry),validated=VALID,operational_open=OPEN,item_count_preserved=len(data['items']),dependencies_preserved=True,partial_operational_criteria_not_transferred=True))
    print('Cadastro:11 aceites de engenharia;7 IDs operacionais abertos;45 IDs preservados.')
if __name__=='__main__':main()
