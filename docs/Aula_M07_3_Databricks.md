# M07.3 — reproduzir uma transformação do Renewcast no Databricks

Marlon Alves Bomfim · 29/10/2026 · P1/Renewcast · continuação de M07.1–M07.2.

## 1. O que foi concluído e o que muda agora

A entrega técnica de M07.2 está aceita pelo log enviado: o planejador identificou os mesmos conjuntos de origens que o CSV do Spark, com sete origens afetadas e duas pertencentes ao treino. A geração passou de 165,522 para 177,522 apenas na tabela de correção simulada; a versão 0 continuou reproduzível. Não repetir esse exercício.

Nesta unidade, a pergunta é: **a mesma transformação continua produzindo exatamente o treino aceito quando sai do Docker local e passa a usar uma plataforma gerenciada?** O critério é a igualdade dos dados, não a quantidade de telas ou comandos executados.

Ao concluir, você terá:

- arquivos de entrada com hashes conferidos após o envio;
- tabela Delta de geração e tabela Delta de treino registradas em Unity Catalog;
- treino com 7.485 linhas comparado integralmente ao resultado local;
- nomes, IDs e versões das tabelas registrados em um recibo;
- planos e durações sob duas configurações de shuffle, sem confundir esse ensaio com um benchmark conclusivo;
- uma decisão sua sobre onde essa transformação deve rodar e por quê.

Não há treino de modelo, alteração de hiperparâmetros nem promessa de melhoria no MAE. Aprendemos portabilidade de processamento, identidade de dados e leitura crítica da execução.

## 2. Entender os componentes antes de abrir o ambiente

| Componente | Responsabilidade nesta aula | Exemplo |
|---|---|---|
| Workspace | Lugar de notebooks, configurações e execuções | O notebook que você importa |
| Compute serverless | Executa Python/Spark sem você escolher máquinas ou configurar um cluster | Recurso selecionado no notebook |
| Unity Catalog | Organiza objetos de dados e suas permissões | Catálogo do seu workspace |
| Schema | Agrupa os objetos da aplicação | `renewcast_m07` |
| Volume | Guarda arquivos acessíveis por caminho | Parquet de entrada, manifesto e recibo |
| Tabela Delta gerenciada | Guarda dados tabulares e histórico transacional sob gerenciamento da plataforma | `catalogo.renewcast_m07.geracao_m073_<id>` |
| Snapshot | Versão específica de uma tabela identificada | ID da tabela + versão consultada |

Um volume não é sinônimo de tabela. Enviar `geracao.parquet` a um volume apenas disponibiliza um arquivo. A criação posterior da tabela registra um objeto tabular que pode ser consultado por SQL. Para tabelas gerenciadas, a plataforma escolhe a localização física; o notebook não grava os arquivos internos da tabela dentro do volume de entrada.

O nome facilita o uso; o ID distingue a identidade do objeto; a versão identifica um estado desse objeto. Se alguém apagar e recriar uma tabela com o mesmo nome, uma versão numérica igual não significa continuidade da tabela antiga. Por isso, o recibo inclui os três.

## 3. Ambiente escolhido e limites conhecidos

O caminho principal desta aula é **Databricks Free Edition**, destinado a aprendizado e com recursos serverless sujeitos a quota. Se ainda não tiver conta, use o acesso indicado pela documentação oficial: https://login.databricks.com/?dbx_source=docs&intent=CE_SIGN_UP . A documentação de entrada está em https://docs.databricks.com/aws/en/getting-started/free-edition . Use a opção Free Edition; a aula não exige um trial pago nem uma conta própria AWS/Azure.

Se já tiver um workspace gravável com Unity Catalog e serverless, pode usá-lo, ajustando o catálogo e o campo `EDICAO` do notebook para refletir seu ambiente. Um workspace empresarial pode ter permissões ou cobrança próprias. Não se registra custo zero se ele não foi medido.

Diferenças frente ao laboratório local:

- `spark` já existe. Não criar `SparkSession.builder.master("local[2]")`, não usar Docker dentro do notebook e não configurar host/porta do driver.
- Delta já faz parte do ambiente. Não instalar os dois JARs do laboratório local nem trocar a versão do PySpark fornecida pela plataforma.
- Usaremos DataFrames e SQL compatíveis com Spark Connect. Não dependemos de RDD, `_jvm` ou APIs internas.
- O caminho dos dados será `/Volumes/...`; `C:\renewable-forecast-lab` não existe no servidor cloud.
- A propriedade `spark.sql.shuffle.partitions` é configurável no serverless. Isso não autoriza configurar livremente todas as propriedades do Spark.
- O ambiente gerenciado pode ter uma versão de Spark diferente da local. Vamos registrá-la e comparar resultados; não afirmamos que os ambientes são idênticos.

O perfil da consulta é a ferramenta da plataforma para inspecionar a execução serverless. O plano impresso é útil, mas não equivale a uma medição do uso de CPU ou memória.

## 4. Arquivos e primeira execução no Windows

Extraia o pacote uma vez na raiz do projeto. Ele acrescenta:

```text
scripts/preparar_m07_databricks.py
notebooks/databricks/m07_3_reproducao.ipynb
docs/Aula_M07_3_Databricks.md
docs/Verificacao_M07_3_Professor.json
```

No PowerShell:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m07_databricks.zip -DestinationPath .
python scripts/preparar_m07_databricks.py
```

O preparador usa o PyArrow do ambiente do projeto. Ele lê o Parquet original, o treino aceito e `snapshot_treino.json`, confere o recorte e grava somente três arquivos em:

```text
C:\renewable-forecast-lab\dist\databricks\CJU_BA5EIGT\m07_3\
    geracao.parquet
    treino_referencia.parquet
    manifesto_entrada.json
```

Não gera dados sintéticos, não lê a geração com a correção simulada e não altera as entradas. Se você executar novamente, confere e reutiliza o mesmo pacote; um destino com conteúdo diferente causa erro explícito. Não precisa fazer backups de notebooks anteriores.

**Por que mandar o treino local?** Ele é a referência independente do novo ambiente. Conferir apenas7.485 linhas seria fraco: valores errados podem preservar a contagem. O notebook confronta as chaves, todas as colunas e seus valores.

## 5. Abrir o notebook no Databricks

1. Entre no workspace Free Edition. Em **Workspace**, abra sua pasta de usuário, escolha **Import** e selecione `C:\renewable-forecast-lab\notebooks\databricks\m07_3_reproducao.ipynb`.
2. Abra o notebook e selecione **Serverless** no seletor de compute, se ainda não estiver selecionado. Não crie um cluster clássico.
3. Execute somente a célula de código da seção **1. Catálogo, schema e volume**. Ela obtém o catálogo atual, cria o schema/volume da aula se necessário e imprime o caminho de upload. Se o catálogo não for gravável, use o catálogo do seu workspace mostrado em **Catalog** no widget `catalogo`.
4. Vá a **New → Add or upload data → Upload files to a volume**. Envie os três arquivos de `dist\databricks\CJU_BA5EIGT\m07_3` para o caminho impresso, terminado em `/arquivos/entrada_m073`. Não envie o ZIP inteiro e não escolha a opção de criar tabela automaticamente.
5. Volte ao notebook e execute as células a partir da seção **2**. Leia a saída de cada seção na primeira execução. Depois do upload correto, também é possível usar Run all.

A documentação da interface pode apresentar pequenos ajustes de rótulo. Os objetos e caminhos são os acima; não selecione um catálogo aleatório nem substitua volume por DBFS.

## 6. Ler o código sem tratar o notebook como uma caixa-preta

### Células 1–2: configuração, transferência e identidade

`dbutils.widgets` cria um parâmetro editável no notebook. Não é uma variável do PowerShell. `CREATE SCHEMA IF NOT EXISTS` e `CREATE VOLUME IF NOT EXISTS` permitem retomar a configuração sem recriar objetos existentes.

O manifesto registra parâmetros, tamanho e hash dos dois Parquets. O notebook recalcula os hashes depois do upload. `package_id` é derivado desse contrato; parte dele entra no nome das tabelas para evitar misturar recortes diferentes.

O código converte timestamps explicitamente para `timestamp_ntz`. Isso conserva os rótulos sem fuso do laboratório; não descobre nem corrige o fuso físico da geração. Configurar a sessão em UTC não transforma uma hipótese sobre a fonte em fato verificado.

### Célula 3: mesma transformação aceita

`validar_entrada` rejeita duplicação de timestamps, horários fora da hora cheia e valores não finitos. `completar_horas` constrói a grade esperada e preserva ausência como ausência. `construir_features` usa histórico em `o−2h`, média de seis horas e alvo em `o+24h`. `selecionar_treino` exige alvo disponível antes do corte.

As funções são reaproveitadas do laboratório, com uma adaptação importante na representação do corte:

```python
F.col("target_available_at") < F.lit(corte.isoformat()).cast("timestamp_ntz")
```

O texto conserva o rótulo `2026-07-11T06:00:00`; o cast explicita seu tipo sem fuso. Passar um datetime Python ingênuo diretamente a `F.lit` pode introduzir uma interpretação dependente do fuso do processo antes da comparação. O contrato continua estrito; corrigimos a representação do literal, não a janela de treino. Não se insere `collect()` sobre a série completa, UDF Python ou uma lógica diferente apenas porque o ambiente mudou.

### Célula 4: publicar e fixar uma versão

`publicar_uma_vez` cria uma tabela gerenciada com propriedades que identificam o pacote, a finalidade e a implementação. Se ela já existe, essas propriedades devem coincidir. Em seguida, `DESCRIBE DETAIL` fornece o ID e `DESCRIBE HISTORY` fornece a versão.

```python
fonte_fixada = spark.read.option("versionAsOf", versao).table(nome)
```

Essa leitura se refere à tabela identificada pelo nome e à versão registrada. A igualdade com o arquivo de entrada também é conferida. A propriedade escrita pelo programa, sozinha, não prova o conteúdo.

O experimento presume um único escritor. Validar propriedades e depois criar/consultar objetos não constitui uma transação atômica entre várias tabelas. Esse escopo é suficiente para a reprodução didática, sem simular uma garantia de concorrência que não implementamos.

### Célula 5: configurações 2 e 4

O loop muda `spark.sql.shuffle.partitions`, reconstrói o plano e compara o resultado com a referência. A comparação é uma action: o Spark precisa produzir os valores para confrontá-los. Medir somente a construção do DataFrame mediria planejamento, não toda a transformação.

`comparar_frames` rejeita chave duplicada, confere tipos e realiza um FULL JOIN. Ele detecta linhas ausentes, linhas extras, diferença entre NULL e valor e diferença nos valores. O limite de 1e−9 para doubles admite apenas variação numérica muito pequena; não encobre diferenças relevantes em MWmed.

O tempo chamado `comparison_seconds` inclui validação, leitura, transformação e comparação. Não é tempo de treino nem latência de uma API. Não compare diretamente esses tempos aos números de M06 ou a um tempo local medido com outro escopo.

### Células 6–7: tabela de treino e recibo

O treino é materializado como tabela nomeada e relido por versão. A comparação integral ocorre depois da gravação. A consulta SQL mostra quantidade, limites das origens e última disponibilidade do alvo.

O recibo inclui configuração, versões observadas, contagens e divergências, durações e planos. `cost_amount=null` significa custo não medido. No Free Edition não há uma fatura de computação atribuída pelo notebook; isso não significa que o mesmo trabalho teria custo zero em um ambiente comercial.

O hash do notebook distribuído identifica a entrega original; não prova automaticamente que o código executado permaneceu inalterado. Por isso, a entrega inclui o notebook exportado **com suas saídas**.

## 7. Resultados que autorizam o aceite técnico

| Verificação | Esperado |
|---|---|
| Arquivos após transferência | Dois hashes e tamanhos iguais ao manifesto |
| Geração registrada | 8.760 linhas; comparação integral sem divergência |
| Treino, configuração 2 | 7.485 linhas; zero divergências |
| Treino, configuração 4 | 7.485 linhas; zero divergências |
| Treino gravado e relido | Igual à referência local |
| Primeira origem | 2025-09-01 07:00:00 |
| Última origem | 2026-07-10 03:00:00 |
| Última disponibilidade de alvo | 2026-07-11 05:00:00 |
| Identidade | Nome, ID e versão das duas tabelas no recibo |

Os nomes terminam com um identificador calculado na sua máquina; o sufixo pode diferir do teste do professor. O número da versão cloud também não deve ser copiado da versão do laboratório local. O notebook consulta o valor real.

Reexecutar o notebook confere e reutiliza as tabelas compatíveis, sem duplicar suas linhas. Um novo recibo documenta cada execução. Uma tabela que tenha sido modificada incompatibilmente deve provocar erro, não ser automaticamente substituída.

## 8. Sua autoria: decidir com base no plano e na medição

A tarefa não é copiar um resultado pronto. Produza `C:\renewable-forecast-lab\reports\scale_comparison.md` com quatro partes curtas, usando a execução:

1. **Identidade e reprodução.** Cite nome, ID e versão da fonte e do treino. Explique em que situação usaria o snapshot fixado e em que situação aceitaria dados revisados para um novo experimento. A hora da medição e a hora em que sua revisão ficou conhecida têm funções diferentes. Esta parte consolida a interpretação de M07.2, sem outro exercício separado.
2. **Distribuição real do trabalho.** Localize no plano um `Exchange` próximo do `Window`. Diga qual chave precisa permanecer junta. Explique o erro de repartir a janela por dia para tentar ganhar paralelismo.
3. **Limite da medição.** Registre os dois tempos, seu escopo e as zero divergências. Não eleja uma configuração por uma única observação; discuta ordem, aquecimento e otimização adaptativa.
4. **Escolha de ambiente.** Para uma série de 8.760 horas, onde manteria a exploração cotidiana? Que necessidade concreta justificaria Databricks: colaboração, permissões, pipelines compartilhados, mais séries ou integração com dados já residentes? Relacione a complexidade acrescentada ao benefício.

Um argumento relevante: a distribuição de várias usinas pode paralelizar por série. Uma única série exige manter a ordem e reunir sua partição de janela. Aumentar a quantidade configurada de partições não cria independência estatística nem algorítmica entre as horas. Cortar por dia sem transportar o histórico necessário muda o cálculo, em vez de apenas acelerá-lo.

Não há vencedor antecipado no parecer. O aluno deve distinguir um fato do plano, um resultado medido e uma hipótese sobre o gargalo.

## 9. Entrega e retomada

No Databricks, exporte o notebook em **File → Export → IPython notebook**, mantendo **Include outputs**. O recibo fica no volume, no caminho impresso pelo programa, sob `evidencias_m073`. Baixe-o pelo Catalog Explorer.

Entregue uma vez: **notebook com saídas, recibo JSON e scale_comparison.md**. Para o primeiro retorno, pode enviar a saída do preparador e o log do notebook; se houver falha, mantenha a primeira mensagem de erro e a célula onde ocorreu.

Aceite técnico: transformação reproduzida no Databricks, comparação integral, identificação de versões e rastreabilidade da execução. Aceite de aprendizagem: interpretar o plano e defender a escolha de ambiente. O teste local do professor não conta como execução sua no Databricks. A próxima unidade curricular é M08 — PyTorch e treinamento de uma rede temporal, após essa entrega delimitada.

## 10. Diagnóstico sem criar outra trilha de setup

| Sintoma | Significado e ação localizada |
|---|---|
| Preparador não encontra entrada | Confirmar a raiz do projeto e os caminhos indicados por `--help`; não procurar outro experimento automaticamente |
| `CREATE SCHEMA`/`CREATE VOLUME` sem permissão | Usar o catálogo gravável do seu workspace; em ambiente empresarial, solicitar a permissão correspondente |
| Arquivo ausente em `/Volumes/...` | Conferir se o upload foi para `arquivos/entrada_m073`, sem uma subpasta extra |
| Hash divergente | Enviar o arquivo indicado pelo preparador; não editar o manifesto para fazê-lo passar |
| Quota Free Edition esgotada | Aguardar a renovação da quota; não recriar conta, tabelas ou habilitar cobrança para contornar a aula |
| Comparação apresenta divergências | Preservar o erro; não aumentar tolerância nem remover a coluna discordante sem diagnóstico |
| Tabela preexistente de outro pacote/finalidade | Conferir catálogo/schema e pacote; não usar overwrite como correção genérica |

Time travel depende da retenção do histórico e dos arquivos de dados. Tabela versionada não é backup permanente. Não executar `VACUUM` nem apagar arquivos internos para esta aula; os Parquets de entrada aceitos continuam sendo preservados localmente.

## 11. Fontes primárias e alcance da verificação

Consultadas em 29/10/2026:

- Free Edition: https://docs.databricks.com/aws/en/getting-started/free-edition
- Limites da edição: https://docs.databricks.com/aws/en/getting-started/free-edition-limitations
- Importar/exportar notebook: https://docs.databricks.com/aws/en/notebooks/notebook-export-import
- Arquivos em volumes: https://docs.databricks.com/aws/en/volumes/volume-files
- Criar volumes: https://docs.databricks.com/aws/en/volumes/utility-commands
- Limitações serverless: https://docs.databricks.com/aws/en/compute/serverless/limitations
- Configurações admitidas: https://docs.databricks.com/aws/en/spark/conf
- Histórico e versões: https://docs.databricks.com/aws/en/tables/history

O relatório `docs/Verificacao_M07_3_Professor.json` delimita os testes efetivamente executados. Não foi acessado seu workspace Databricks, criado recurso em sua conta ou medida uma duração cloud em seu nome.
