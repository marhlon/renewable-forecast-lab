# Fontes e limites temporais do P1

25/11/2026 · Auditoria documental e de arquivos locais preparada com assistência Codex. Não é resposta independente do aluno, homologação operacional ou novo aceite do professor.

Esta conferência separa preservação de arquivos, coerência do contrato e evidência da fonte. Os protocolos existentes foram preservados. Não foram coletados novos dados, enviados contatos, treinados modelos ou reexecutados laboratórios.

| Item | O que a evidência sustenta | Limite que permanece |
| --- | --- | --- |
| M04-02 | Granularidade horária, campo de referência e unidade MWmed | Fuso físico, borda do intervalo e publicação histórica não confirmados |
| M04-03 | Rodadas arquivadas, coleta registrada e seleção sob a hipótese de seis horas | Ausência de horário de publicação observado para as origens históricas |
| M04-05 | Comparação dos hashes e regras temporais dos arquivos h24 existentes | Contratos de geração, meteorologia e versões cadastrais ainda não sustentam operação |
| M09-03 | Revisão e model card congelados identificados; conclusão limitada ao recorte explorado | Sobreposição de pré-treino indeterminada; não há prova de contaminação nem de sua ausência |

## Fontes consultadas

O [dicionário ONS](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/DicionarioDados_GeracaoPorUsina.pdf), datado de 09/06/2023, identifica o campo temporal e MWmed. Nas três páginas consultadas não encontrei definição de fuso ou de início/fim do intervalo. Essa observação é restrita ao documento; não prova inexistência de outra norma. O [portal do conjunto](https://dados.ons.org.br/dataset/geracao-usina-2) informa que os dados podem mudar após a publicação.

A documentação [Single Runs](https://open-meteo.com/en/docs/single-runs-api) identifica rodadas pela inicialização UTC, distinta da disponibilização. A página [Model Updates](https://open-meteo.com/en/docs/model-updates) separa inicialização, conversão e acesso na API e descreve diferenças temporárias entre servidores. São descrições do serviço, não recibos históricos das consultas do projeto.

O [model card da revisão congelada](https://huggingface.co/amazon/chronos-bolt-tiny/blob/a0e552de83495b5c28c14c71c374f3e33280b340/README.md) foi lido na cópia local e comparado ao manifesto. Sua declaração sobre os datasets do benchmark publicado não é uma declaração sobre Renewcast/ONS. A identidade dos pesos não resolve a identidade das séries do corpus.

As páginas foram consultadas em 25/11/2026 por leitura de documentação primária. Os bytes das páginas remotas não foram arquivados nem receberam um hash binário nesta entrega. Os hashes locais efetivamente medidos estão nos recibos; não foram apresentados como autenticação do relógio do provedor.

## Como interpretar os relógios

| Campo | Significado nesta auditoria |
| --- | --- |
| `run_time` | Inicialização/referência da rodada meteorológica |
| `valid_time` | Hora prevista pelo valor meteorológico |
| `available_at` | No cache atual, inicialização mais seis horas: hipótese |
| `fetched_at` | Momento registrado da coleta bem-sucedida, posterior às origens de julho |
| Disponibilização observada | Informação que não foi localizada nos recibos históricos |

Uma coleta posterior não comprova que o valor estava disponível antes. Também não demonstra que estava indisponível: a rodada arquivada pode ter existido então. O estado correto é desconhecido, até obter evidência adequada.

O cadastro local declara `historical_snapshot_verified=false`: datas de pertencimento na versão consultada não comprovam quais coordenadas, capacidades ou associações eram conhecidas naquela época. Essa dependência continua em M04-04.

**Integridade** responde se os bytes foram preservados; **compatibilidade**, se atendem às regras declaradas; **atualidade**, se servem para a decisão presente. Previsões históricas podem passar nas duas primeiras verificações e não servir para uma emissão de agora. Uma regra coerente sob hipótese também não transforma a hipótese em fato observado.

## Fechamento possível e evidência ainda necessária

M04-02, M04-03 e M04-05 permanecem bloqueados para operação. Os respectivos pareceres registram as perguntas que podem ser encaminhadas ao provedor; nada foi enviado. Documentar a ausência de confirmação não equivale a concluir o contrato.

M09-03 permite concluir a **delimitação**, sujeita à revisão: manter a sobreposição desconhecida e impedir alegações de benchmark incontaminado ou de generalização externa. O plano prospectivo é apenas proposto; não foi reservado nem executado um período novo.

Os detalhes estão em `reports/fechamento_m00_m09/M04-02`, `M04-03`, `M04-05` e `M09-03`. As tabelas existentes foram lidas; modelos, métricas preditivas e configurações aceitas foram preservados.
