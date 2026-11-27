# Instruções do repositório

## Modo de entrega solicitado pelo usuário

Em 25/11/2026, o usuário esclareceu que esta retomada é uma entrega de engenharia: aplicar correções, executar as análises e explicar minuciosamente o que foi feito. Não exigir exercícios, provas, respostas do aluno ou aceite de professor como condição dessa entrega. As soluções podem ser fornecidas integralmente, com atribuição correta; isso não certifica autonomia pessoal. Preserve os critérios pedagógicos antigos como histórico e use o portão `engenharia` para a entrega aplicada. As comprovações externas ainda ausentes permanecem no portão `operacao` e não podem ser inventadas para aprovar produção.

## Fechamento M00–M09

Para trabalho que altere os módulos M00–M09 ou declare o seu fechamento:

1. Consulte `docs/ROADMAP_M00_M09.md` e `config/roadmap_m00_m09.json`. Identifique os IDs abrangidos; preserve os aceites e os runs históricos.
2. Separe construção, execução, auditoria, interpretação, transferência independente e operação. A ausência em uma revisão antiga não prova ausência no disco atual.
3. Não declare autonomia a partir de uma solução fornecida. Registre assistência e atribua a resposta e a revisão a quem efetivamente as realizou.
4. Registre hipóteses, recorte, disponibilidade dos dados e critérios antes de um novo teste. Um período já examinado não pode ser apresentado como intocado.
5. Só marque `validado` com critérios atendidos, entregáveis e parecer existentes, hashes e revisão registrada. Nunca crie recibos para execuções que não ocorreram.
6. Depois de alterar o cadastro, execute `python scripts/verificar_roadmap.py`. Antes de declarar encerramento formativo ou operacional, execute também o `--gate` correspondente. Relate qualquer portão ainda aberto.
7. Templates, replay, inferência local e governança estatística não demonstram CI remoto, shadow ao vivo ou sustentação. Não classifique um deles como o outro.
8. Reparos necessários à reprodução têm prioridade sobre novos benchmarks. Recupere a evidência antes de repetir treinos aceitos; registre limites de acesso sem inventar perda ou restauração.

A execução autorizada está agrupada em blocos: 1 = etapas 1–3, 2 = etapas 4–6, 3 = etapas 7–9. Consulte `docs/roadmap_m00_m09/Bloco_1_Execucao.md` e o estado atual do cadastro. Use `--bloco 1 --gate engenharia` para conferir o fechamento aplicado. `--exigir-fechamento` sem recorte de portão exige todos os itens do bloco, inclusive as comprovações operacionais. Informe ao usuário a necessidade concreta de intervenção humana ou de abrir aplicativos, inclusive Docker; não atribua uma resposta independente sem recebê-la e revisá-la.

Essas regras incorporam o plano às próximas mudanças do P1. Não bloqueiam o trabalho autorizado de M10–M14. O verificador é local e documental: não substitui avaliação humana, autorização de implantação nem configuração de CI remoto. A ativação de recursos externos e o envio de mensagens continuam sujeitos às instruções do usuário e às permissões do ambiente.

## Estado após o bloco 2

As etapas 4–6 foram executadas em rodada própria, com protocolos e congelamento antes da obtenção do snapshot ONS de outubro/2026. Consulte `docs/roadmap_m00_m09/Bloco_2_Execucao.md` e `Relatorio_Engenharia_Bloco2.md`; use `--bloco 2 --gate engenharia`. Os resultados negativos fazem parte do aceite técnico: não alterar modelo, calibrador ou limiar para melhorar o teste já examinado. O período é retrospectivo, posterior ao ajuste, sem comprovação de disponibilidade histórica da versão dos dados e sem shadow ao vivo.

M05-01/M05-02 têm aceite aplicado; os requisitos prospectivos não comprovados foram preservados como critérios C3/C4 não atendidos de M06-05, no portão operacional, com origem e dependências explícitas. Mantenha essa separação nas próximas alterações. Não aprovar operação pela migração de critérios nem apagar o snapshot anterior do cadastro. Os 45 IDs foram preservados. O bloco 3 é a próxima etapa planejada; não classificar recursos externos, CI remoto ou operação contínua como executados sem evidência real.

## Estado após a execução local do bloco 3

Em 26/11/2026, os 18 IDs das etapas 7–9 foram abrangidos com 12 aceites integrais de engenharia e seis IDs operacionais abertos; três desses têm demonstração local parcial de drift, segurança e capacidade. Consulte `docs/roadmap_m00_m09/Relatorio_Engenharia_Bloco3.md`, a revisão integrada, o cadastro e os recibos. Use `--bloco 3 --gate engenharia` para as 12 entregas aplicadas. Os critérios anteriores e o snapshot integral foram preservados. Não interpretar o portão de engenharia como encerramento dos 18 itens ou autorização de produção.

M06-04/05/06/07/08/09 e os quatro bloqueios M04 continuam abertos. Não transferir segurança/capacidade para depois do shadow; não inverter M06-06→M06-05 criando ciclo. M06-02 passou em dois runs Actions reais: falha temporal esperada e correção com16testes. A checagem canônica/autenticação fora da restrição resolveu o acesso; os diagnósticos anteriores e o erro de URL foram preservados. A main não foi alterada; o aceite limita-se aos commits verificados, sem proteção de branch ou produção presumidas. Cloud recebeu somente plano. Os mecanismos locais e a carga finita não demonstram continuidade/custo operacional.

A avaliação final usa snapshot de setembro obtido após congelar29arquivos, com671origens. O candidato HGB falhou no critério de ganho; preservação da decisão negativa e das três sementes neurais é obrigatória. A falha de consoleCP1252 e a recuperação somente da sínteseUTF8 são eventos distintos documentados; não mudar o código congelado nem repetir inferência para esconder o retorno1. Antes de uma nova rodada, usar UTF8 no pai e nos subprocessos. Nenhuma solução fornecida certifica autoria ou aprendizagem independente do usuário.
