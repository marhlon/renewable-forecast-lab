# Bloco 3 — ampliação, sustentação e avaliação final

26/11/2026 · Renewcast/P1 · etapas 7–9 · execução de engenharia aplicada.

Os **18 IDs do último bloco foram abrangidos**. Há **12 entregas integralmente demonstradas no escopo aplicado**, mais três aceites técnicos parciais de drift, segurança e capacidade local. Seis IDs operacionais continuam abertos. Não se converteu preparação de infraestrutura em comprovação de operação real.

A decisão principal da avaliação final é **manter a persistência como referência para o objetivo MAE neste recorte e não promover automaticamente os modelos aprendidos**. O Chronos ficou próximo na MAE, com RMSE menor; o candidato HGB previamente escolhido não atingiu o critério de ganho. Os intervalos e as probabilidades também revelaram problemas de transferência. O resultado negativo foi preservado, sem repetir seleção, ajustar limiar ou escolher uma semente depois do teste.

## 1. O que foi executado em cada etapa

| Etapa | Entregas | Estado demonstrado |
| --- | --- | --- |
| 7 — Dados e alternativas | M07-01/02/03, M05-04/05 | Bronze/silver/gold; incremento e recuperação; escala local medida; quatro séries reais com modelo global/local; LightGBM e CatBoost comparados |
| 8 — Sustentação | M06-02–09 | Registry MLflow real; serviço HTTP protegido, carga, ledger e drift verificados localmente; CI remoto executado e auditado; plano cloud preparado. Shadow, continuidade e homologação do ambiente alvo permanecem abertos |
| 9 — Avaliação e aplicação | M03-04, M08-02/03, M09-02/04 | Reanálise de GRUs; nova janela/batching; novo contexto Transformer e vazamento indireto; comparação congelada de 14 variantes em 671 origens de setembro |

As fontes, runs e códigos congelados dos blocos 1 e 2 permaneceram preservados. As soluções desta rodada são fornecidas com assistência técnica registrada; não se exige resposta do usuário nem se certifica autoria ou domínio independentes.

## 2. Camadas de dados, incremento e escala — M07

Foi reutilizado o Parquet oficial ONS de outubro já obtido no bloco 2: **537.384 registros**, 4.629.118 bytes. A bronze é endereçada pelo SHA-256 do conteúdo, confere a cópia e recusa sobrescrever uma versão divergente. O bruto foi preservado.

A silver aplica esquema, chaves `id_ons/event_time`, alinhamento horário, finitude, duplicidade e geração negativa. O resultado foi:

| Destino | Linhas | Motivo |
| --- | ---: | --- |
| Silver válida | 389.304 | Registros elegíveis segundo o contrato desta rodada |
| Quarentena | 148.080 | 87.048 sem identificador ONS e 61.032 sem geração finita |

Não se completaram valores ausentes com zero nem se agregaram duplicatas silenciosamente. A linhagem mantém `source_row`, fonte e hashes até a gold. O reprocessamento produziu os mesmos hashes físicos e lógicos de silver, quarentena e gold.

A gold de quatro séries tem 2.976 linhas. Os lags usam **junção exata por série e timestamp**, e conferem a disponibilidade de cada contribuição; uma lacuna não transforma uma posição anterior no vizinho horário. O atraso de duas horas foi declarado como hipótese, não extraído de uma chegada histórica que a fonte não fornece.

O armazenamento incremental foi exercitado com quatro commits, repetição sem efeito, conflito de payload, dado atrasado e falha depois do estágio e antes do commit. Após recuperação, as 2.976 linhas coincidiram com a referência que usa as mesmas chegadas hipotéticas. Os atrasos e falhas injetados são contraprovas sintéticas separadas dos dados reais. O armazenamento é local, de um escritor; não demonstra concorrência distribuída, broker, durabilidade `fsync` ou operação contínua.

### Escala medida, sem transformar o recorte em cluster

Foram executados **18 processos de medição**: três coortes reais, três repetições, pandas e DuckDB. Os volumes elegíveis foram 149.568, 266.664 e 389.304 linhas. O escopo cronometrado inclui leitura da silver, filtro, janela/agregação e escrita materializada. Ambos leem o mesmo arquivo físico; variam as séries processadas. Não são três arquivos de armazenamento crescentes nem uma ampliação por duplicação sintética.

| Linhas elegíveis | Mediana pandas | Mediana DuckDB |
| ---: | ---: | ---: |
| 149.568 | 0,247 s | 0,326 s |
| 266.664 | 0,397 s | 0,250 s |
| 389.304 | 0,215 s | 0,223 s |

Os nove pares produziram resultados equivalentes, com diferença máxima de arredondamento de 3,18×10⁻¹². Todos os picos RSS amostrados ficaram abaixo do orçamento de 512 MiB dos trials. O construtor completo das camadas tem outro escopo de memória. O RSS incremental inclui preparação da conexão anterior ao cronômetro; o pico absoluto é o indicador apropriado para o teto.

Não houve crescimento monotônico ou vantagem consistente. Tempos subsegundo, cache, otimização de filtro e atividade do host limitam a interpretação. O plano observado é `EXPLAIN ANALYZE` do DuckDB, não um plano Spark/AQE. Não se infere necessidade ou desempenho de um cluster a partir desses números. Docker não foi necessário.

Detalhes e arquivos: [Bloco_3_Dados.md](Bloco_3_Dados.md).

## 3. Modelo global e alternativas de boosting — M05

### Quatro séries reais

Foram escolhidas **CEECVA, CEEMAU, CEUCZ e CEUFM**, por ordem lexicográfica entre séries eólicas com cobertura completa de 744 timestamps; a seleção não usou desempenho. A cobertura do mês inteiro é informação retrospectiva e não comprova que o cadastro estivesse disponível na origem. A série principal CJU_BA5EIGT foi excluída dessa seleção.

O problema é próprio: geração em `origem+1h`, com histórico disponível até `origem−2h`. O rótulo só fica disponível em `origem+3h`. O treino tem 1.332 linhas, com disponibilidade estritamente anterior a 16/10; a última é 15/10 às 23h. Há 576 linhas de validação e **956 de teste**, 239 origens por série. O período de outubro já estava no disco: é estudo exploratório retrospectivo, não outro holdout intocado.

| Modelo | MAE agregado — MWmed |
| --- | ---: |
| HGB global | **5,980751** |
| HGBs locais | 6,176272 |
| Persistência disponível | 8,063423 |

O agregado não vale para cada série: o global venceu a persistência em CEEMAU e CEUFM e perdeu em CEECVA e CEUCZ. A média do viés também esconde sinais diferentes entre séries. O global venceu três dos quatro modelos locais no teste, mas teve MAE de validação maior que a dos locais. Não houve seleção pelo teste.

O código evita lags entre séries e usa a mesma coorte/alvo em cada comparação. O modelo global foi ajustado nas quatro séries conhecidas; isso não demonstra desempenho numa quinta série nunca vista, em outro ano ou no P1 principal. A magnitude desses MAEs h+1 não deve ser comparada diretamente aos MAEs h+24 da série principal.

### LightGBM e CatBoost

As bibliotecas ausentes foram instaladas em `.venvs/bloco3-packages`, com versões **LightGBM 4.6.0 e CatBoost 1.2.8**. O Conda original não recebeu atualização. A execução precisou de leitura fora da restrição do sandbox para acessar esses pacotes privados.

Foram fixadas duas configurações por família, 60 ou 120 árvores, e três folds de junho idênticos aos do bloco 2. As 28 features são os 24 lags e o calendário já selecionados. Cada treino usa apenas rótulos disponíveis antes de seu corte. A MAE agregada de desenvolvimento escolheu **120 árvores nas duas famílias**; foram ajustadas 7.221 linhas no modelo final, com última disponibilidade de alvo em 30/06 às 23h.

Em outubro, LightGBM teve MAE 18,058893 e CatBoost 18,421708 MWmed, melhores numericamente que a persistência de 19,218456. Outubro já havia sido examinado; esses números foram tratados como exploratórios. Nenhum deles selecionou a configuração ou mudou o protocolo da avaliação final.

## 4. Transferência neural e atenção — M08 e M09

A comparação antiga de 168 origens foi recalculada sem retreinar. O HGB tem MAE 32,323956 e RMSE 44,221683. As GRUs 17/29/41 têm MAEs 35,675970/34,911227/34,573202; as sementes 29 e 41 melhoram RMSE, mas não MAE. Todos os casos e sementes foram preservados. Ganhos em alguns erros grandes explicam a discordância entre critérios; escolher só a melhor semente no teste ocultaria essa dispersão.

Foi executada uma adaptação nova de contrato: **janela 12, hidden size 8, 273 parâmetros e 11 exemplos em lotes 4/4/3**. Os shapes foram escritos antes da execução: entrada `[B,12,1]`, saída recorrente `[B,12,8]`, estado `[1,B,8]` e previsão `[B,1]`. O MSE correto foi 5,603784; tirar a média simples das três perdas de lote produziria 6,324716, porque o lote final é menor. Modos mistos, pesos, gradientes, entradas e falhas foram conferidos. São pesos aleatórios e exemplos de contrato; não foi alegada qualidade preditiva desse modelo.

No Transformer, o exemplo tem contexto 12, cinco slots de consulta, dimensão 12 e três cabeças de dimensão 4. Foram conferidos Q/K/V, normalização por chave, residual, normas e feed-forward. Os slots são sintéticos; cinco slots não significam automaticamente cinco horizontes horários.

A contraprova central alterou uma observação posterior ao prefixo permitido. **Mascarar somente o cross-attention ainda deixou vazamento indireto pelo encoder livre**, diferença de 0,590814 na primeira saída. Restringir encoder e cross-attention resultou em diferença zero. A máscara causal do decoder também preservou o prefixo, enquanto a atenção livre permitiu uma diferença de 1,222385. Consultar todas as observações já disponíveis numa origem de previsão é um contrato diferente de respeitar cada prefixo interno.

Veja [Bloco_3_Transferencia_Neural.md](Bloco_3_Transferencia_Neural.md). O sinal do viés deve acompanhar seu rótulo: alguns arquivos históricos usam observado−previsto; a reanálise didática usa previsto−alvo. Nenhuma mudança de convenção foi apresentada como mudança do modelo.

## 5. Avaliação final congelada — M03-04 e M09-04

### Fonte, preservação e recuperação do console

Foi predefinido **setembro/2026**, ainda não obtido localmente na preparação deste estudo. Julho/agosto eram desenvolvimento conhecido e outubro já havia sido aberto no bloco 2. Foram selados **29 arquivos de código, modelos, escaladores, calibradores, política e protocolos** antes de obter o recurso ONS `c6d1f291-c114-4872-b69d-b487f7410e5c`.

O snapshot contém **720 horas únicas e finitas** da usina principal. O contexto vai de origem−25h a origem−2h; o alvo é origem+24h. Isso deixa **671 origens comuns**, de 02/09 às 01h até 29/09 às 23h. O último alvo é 30/09 às 23h. O Chronos prevê 26 passos após o fim do histórico; o alvo correto é o índice 25. Seus pesos locais foram reutilizados offline, sem fine-tuning.

Antes do teste, o novo adaptador foi conferido em seis origens antigas. Linear/HGB diferiram por aproximadamente 7×10⁻¹⁵ MWmed; as redes, no máximo 1,03×10⁻⁵, dentro da tolerância pré-fixada de 10⁻⁴. Os checkpoints e escaladores mantiveram os mesmos bytes. Os modelos neurais antigos e os modelos novos têm cortes de ajuste diferentes, declarados nos protocolos; a comparação não finge um treino único ou features idênticas.

A primeira execução completa retornou **1** ao imprimir o stdout do processo Chronos em console CP1252, depois de gravar as previsões locais e o NPZ/metadata do Chronos. O recibo e o log dessa falha foram preservados. A recuperação executou apenas `python -X utf8 notebooks/bloco3_benchmark.py sintetizar`, com retorno **0**. Nenhuma inferência, treinamento, calibração, seleção ou política foi repetida. O código congelado não foi alterado; o adendo da recuperação documenta esses dois eventos distintos. Em nova rodada, `PYTHONUTF8=1` deve ser definido antes de iniciar pai e subprocesso.

Esta é uma avaliação **retrospectiva em snapshot recém-obtido após o congelamento**, não coleta prospectiva. O relógio físico, a latência real, o intervalo ONS e a versão publicada disponível em cada origem continuam sem comprovação operacional. A sobreposição com o pré-treino do Chronos continua desconhecida.

### Comparação das mesmas origens

Unidade: MWmed. Viés nesta tabela = observado−previsto; positivo significa subestimação média.

| Variante congelada | MAE | RMSE | Viés |
| --- | ---: | ---: | ---: |
| Persistência | **35,616479** | 50,351806 | −0,118539 |
| Chronos P50 | 35,689509 | 47,649804 | +3,594809 |
| MLP 17 | 35,798434 | 46,331283 | +13,530202 |
| MLP 29 | 36,071127 | 46,324847 | +16,434027 |
| MLP 41 | 36,078965 | 46,057445 | +16,998245 |
| GRU 41 | 36,550595 | **45,015515** | +20,323878 |
| Linear antigo | 36,773465 | 46,863352 | +19,237325 |
| GRU 17 | 37,262908 | 46,370827 | +23,423832 |
| GRU 29 | 38,939038 | 47,425211 | +25,320816 |
| LightGBM | 39,935226 | 48,006647 | +23,808183 |
| HGB escolhido no bloco 2 | 40,160344 | 48,084892 | +27,001884 |
| CatBoost | 40,853216 | 48,483520 | +26,829121 |
| HGB quantílico P50 | 42,338754 | 51,419292 | +29,446851 |
| HGB antigo | 42,971842 | 52,854430 | +25,951265 |

O candidato fixado no protocolo era o HGB do bloco 2. O ganho médio contra a persistência foi **−4,543865 MWmed**, IC percentil condicional 95% **[−10,208299; 1,388840]**. O ganho mínimo requerido era +2 MWmed e o limite inferior deveria ser positivo: ambos falharam. Para o Chronos, o ganho foi −0,073030, IC **[−3,151100; 2,969704]**. Não há evidência convincente de ganho de MAE sobre a persistência nessa comparação.

O bootstrap usa blocos circulares pareados de 24h, 2.000 réplicas e semente 31, conforme o protocolo anterior à obtenção do snapshot. Os intervalos são condicionais às previsões e ao recorte; não refazem ajuste ou seleção e não fornecem p-valores. A semente GRU41 é mostrada porque todas as sementes são mostradas, não porque será escolhida retrospectivamente pelo RMSE.

### Intervalos e classe não se transferiram uniformemente

| Intervalo | Cobertura | Largura média | Interval score |
| --- | ---: | ---: | ---: |
| HGB P10–P90 ordenado | 56,04% | 104,964631 | 203,092002 |
| HGB com CQR congelado | 76,15% | 135,212583 | **183,036569** |
| Chronos P10–P90 bruto | 67,51% | 80,770920 | 192,696013 |

O CQR melhorou cobertura/score nesse mês, mas ultrapassou o limite de largura de 100 MWmed fixado antes do teste. Em outubro o mesmo calibrador havia dado 98,71% de cobertura e intervalos largos; setembro e outubro, portanto, não sustentam calibração nominal estável. O Chronos ficou abaixo da meta nominal de 80%. Não se recalibrou nenhum dos dois meses para aparentar estabilidade.

No classificador congelado do evento entre extremidades separadas por 26h, houve **181 positivos em 671 origens**, prevalência de 26,97%. O Brier foi 0,295863 bruto, 0,256556 calibrado e **0,202469 na frequência constante do treino**. Platt melhorou o bruto, mas ambos ficaram piores que o baseline constante; isso limita o uso das probabilidades, apesar de sua AP de 0,427057 superar a prevalência.

A política calibrada em 0,3 produziu 160 alarmes, 62 TP, 98 FP e 119 FN, custo hipotético `98+4×119=574`, contra 724 de nunca alarmar. O limite de seis alarmes por dia foi conferido explicitamente. O custo menor não elimina recall limitado, falsa precisão probabilística nem a ausência de contrato operacional comprovado.

Sob custo de subestimar quatro vezes maior, a ação Chronos P80 teve perda 70,466801, contra 88,863390 da persistência. Sob custo simétrico, a persistência foi a menor perda observada. Sob custo de superestimar quatro vezes maior, a menor perda dessa amostra foi da GRU17, 58,021522; isso não autoriza escolhê-la pelo teste. O quantil decisório teórico continua 0,8 ou 0,2 conforme a razão de custos, condicionado a uma distribuição preditiva válida. Os custos são relativos hipotéticos, sem conversão para reais.

**Decisão aplicada:** conservar a persistência como referência simples para MAE; manter os modelos e intervalos como alternativas de estudo; não promover o HGB congelado. Para custos assimétricos, a escolha precisa de critério de negócio e nova confirmação, preservando esta avaliação como já examinada. Fonte point-in-time, segurança, capacidade no ambiente alvo e operação contínua continuam pré-condições.

## 6. Registry, serviço, capacidade e preparo operacional — M06

### Registry real, não apenas tracking

O MLflow **3.16.0** criou um Registered Model e versões 1/2, com assinatura, identidade e resolução por alias. O alias `active` percorreu **1→2→1**, com recarga e diferença máxima de inferência **zero** em 48 entradas de 28 atributos.

As duas versões usam o **mesmo artefato HGB congelado**. Isso demonstra o mecanismo de registro/promoção/rollback de pacote, não ganho de qualidade ou retreino. A primeira tentativa falhou pela exigência de confiança explícita do tipo interno `TreePredictor` no skops. A falha/DB foram preservadas; um adendo anterior à segunda tentativa restringiu a confiança ao tipo desse bundle com hash conferido. Modelo, amostra, SLO e limiares não foram alterados para passar.

### HTTP e recursos medidos

O serviço foi realmente aberto em `127.0.0.1`, protegido por chave efêmera em memória, limite de corpo incluindo stream chunked, validação de contrato e rate limit. Foram aprovadas oito contraprovas HTTP, incluindo 401, 413, 422 e 429. O token não foi registrado nos logs. O serviço foi encerrado ao final; não ficou publicado.

| Carga pré-fixada | Requisições | p95 | Vazão | Erros | RSS do processo — MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Concorrência 1 | 240 | 18,18 ms | 70,89 req/s | 0 | 430,76 |
| Concorrência 4 | 240 | 79,37 ms | 61,93 req/s | 0 | 431,68 |

Os SLOs locais definidos antes da medição foram atendidos: p95≤500 ms, erros≤1% e RSS≤2.048 MiB. Os campos do executor chamados `rss_peak_mb`/`rss_mb_max` usam bytes divididos por 1024²; a unidade efetiva é MiB, explicitada aqui sem alterar os recibos. Mais concorrência piorou p95 e vazão neste ensaio. É uma carga curta de 480 requisições, não capacidade sustentada de produção. O teto de gasto externo foi zero e não se criaram recursos cloud. Energia/depreciação local não foram tarifadas; não se publicou uma estimativa como cobrança real.

### Shadow, continuidade, drift e cloud

O ledger foi exercitado com **48 emissões e 48 reconciliações em replay**, com origem, chegada, vintage, alvo, modelo e trace. Recusou dado futuro, vintage posterior, reconciliação antes de o alvo chegar e a ativação live sem contrato M04. Isso demonstra controles do coletor, não chegadas reais ao vivo.

O detector de drift distinguiu mudança de entrada, degradação de erro, falta de dados e atraso de rótulo em contraprovas separadas. A resposta é investigação; não existe retreino/promoção automática. O orçamento de investigações documentado não é um controle probabilístico de falsos positivos nem uma deduplicação diária implementada. A estabilidade ao vivo continua não comprovada.

Existe plano de janela prospectiva de sete dias, mínimo de 144 emissões, conciliação posterior e observação de intervalos/classes. Ele não foi executado. Abrir Docker não resolveria os bloqueios de fonte, acesso e tempo de observação.

O plano cloud define conta/titular, região, teto financeiro, teste, reversão e encerramento antes de criar qualquer recurso. Nenhum recurso foi criado. Sem ambiente alvo, credenciais e autorização de gasto, não se inventa uma implantação.

Detalhes: [Bloco_3_Operacao_Local.md](Bloco_3_Operacao_Local.md).

## 7. CI remoto — falha controlada e sucesso reais

O usuário confirmou `marhlon/renewable-forecast-lab`. A listagem inicial do conector não identificou instalações/repositórios e a primeira consulta retornou 404; isso não provou inexistência ou ausência definitiva de acesso. A checagem fora da restrição encontrou autenticação Git utilizável, sem mostrar ou gravar valores. A URL canônica confirmou o repositório público e permitido.

A primeira tentativa do publicador parou no GET inicial: uma barra final indevida na URL raiz da API provoca 404. O comportamento foi confirmado num repositório público de controle. O recibo foi arquivado, a URL corrigida e o adendo registrado antes da nova tentativa. Não houve POST ou criação de branch nessa tentativa inicial. Os modelos e o benchmark congelado não foram alterados.

Na branch `codex/bloco3-ci-20261126`, a execução autorizada produziu:

- [Falha controlada — run 45889419488](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889419488), commit `047d8662158793f3e0e393957f1a6b382f8f3296`: o passo **Verificar contrato temporal** rejeitou lag2=29 quando o correto era 28. A falha não foi de instalação ou infraestrutura.
- [Rodada corrigida — run 45889590759](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889590759), commit `a487f7c9f37951102cc2be9ff38830ea04ad5f52`: contrato normal, contraprova negativa e **16 testes aprovados**, em 2,50 s para o pytest.

O segundo commit é filho direto do primeiro e altera somente `config/ci_bloco3.json`, restaurando o controle de falha para falso. Workflow, guard e testes não foram removidos. Os logs reais foram salvos e conferidos por SHA-256. Os runners usaram Ubuntu 26.04, Python 3.12.16 e PyTorch 2.7.1+cpu, com dependências instaladas no ambiente hospedado; não foi ativado o Conda ou uma venv local do projeto.

O pacote seleciona 14 arquivos, dos quais 13 fontes permanecem equivalentes e um é a configuração do controle negativo. Dez arquivos aparecem como adicionados no commit inicial; os demais já existiam no parent. O checkout remoto contém também a árvore histórica rastreada, inclusive artefatos/venvs antigos. O workflow não os ativa: os contratos usam fixtures, e a cópia local contendo somente as 14 fontes também passou. Não se chama a árvore completa de checkout de um pacote de apenas 14 arquivos.

A primeira cópia local omitiu `m08_gru_autoral.py` e registrou 15 testes aprovados/um erro; o empacotamento foi corrigido em adendo antes da cópia posterior, sem alterar os testes. Esse histórico e o `resultado.json` da fase local foram preservados. O recibo atual da execução remota é `M06-02/execucao_ci_remoto.json`, e a [revisão específica](Revisao_CI_Remoto_Bloco3.md) aprova C1/C2 no escopo dos contratos executados.

Não houve merge, PR ou deploy; a `main` permaneceu no parent anterior. A [branch está disponível para revisão](https://github.com/marhlon/renewable-forecast-lab/compare/main...codex/bloco3-ci-20261126). Criar um PR acionaria outra rodada pelo trigger `pull_request`; nenhuma terceira rodada foi aberta por esta execução. O workflow reage a essa branch de ensaio e a PRs: integração à `main` e política de proteção continuam sujeitas à revisão do titular. Este aceite vale para os commits testados, sem aprovar versões futuras, modelos ou produção. Não foi apurada cobrança monetária de Actions.

## 8. Estado que fica imposto ao projeto

O cadastro preserva os **45 IDs**, dependências e critérios históricos em snapshot. Os 12 IDs de engenharia integralmente demonstrados neste bloco são M03-04, M05-04, M05-05, M06-02, M06-03, M07-01, M07-02, M07-03, M08-02, M08-03, M09-02 e M09-04.

**M06-04/05/06/07/08/09 ficam abertos**, com entregas locais e condições concretas de conclusão registradas. M06-06/07/08 recebem aceite técnico parcial, sem apagar requisitos do ambiente real. Segurança e capacidade continuam pré-condições do shadow; drift continua dependente da continuidade. Transferir tudo para M06-05 enfraqueceria essa ordem e poderia criar ciclo, portanto não foi feito.

Os quatro bloqueios externos M04 do bloco 1 também permanecem. Ao final da retomada, o estado esperado é **35 itens validados no escopo declarado e 10 bloqueados**, não um percentual de domínio profissional ou de produto em produção. O aceite dos três blocos de engenharia aplicada não certifica operação nem transforma as seis pendências operacionais finais em entregas concluídas.

Foram executados cinco testes de dados, nove de controles e dois neurais. Os mesmos 16 casos foram repetidos na cópia isolada e no Actions para conferir empacotamento/ambiente; não são 48 casos independentes. Há ainda contraprovas nos executores, recibos, hashes e auditoria final de métricas. Os aceites dos blocos 1 e 2 devem continuar passando no verificador.

Para conferir os arquivos existentes, sem repetir os experimentos:

```powershell
python scripts/verificar_roadmap.py
python scripts/verificar_roadmap.py --bloco 3 --gate engenharia
python scripts/verificar_roadmap.py --gate operacao
python scripts/conferir_bloco3.py
```

O conferidor gera um arquivo novo em `reverificacoes/` e verifica que a auditoria original permaneceu com o mesmo hash. A versão posterior do auditor também exige arquivo novo e reconhece o recibo CI remoto; a fonte anterior foi arquivada junto da auditoria histórica, sem sobrescrever seu recibo. O portão operacional deve continuar recusando o encerramento. O [guia final](Bloco_3_Execucao.md) resume as entregas, os arquivos e a intervenção necessária. A [revisão integrada](Revisao_Engenharia_Bloco3.md) e os recibos de `reports/fechamento_m00_m09/bloco3_engenharia` delimitam o aceite. README, roadmap e instruções incorporam o estado atual; não foi instalado bloqueio de push; os dois runs de CI remoto foram efetivamente executados.
