# Bloco 2 — do erro de previsão à decisão sob risco

25/11/2026 · M02-06 · etapas 4–6 do fechamento M00–M09

Foi recuperada e executada a clínica de decisão que já estava em Downloads. A entrega conecta a perda da previsão à ação escolhida, e aplica custos de falso positivo e falso negativo às probabilidades já salvas. Os números foram conferidos sem repetir treinos ou previsões. A implementação, a aplicação e esta explicação foram fornecidas com assistência de Codex, no modo de entrega de engenharia solicitado pelo usuário.

O resultado central é concreto: quando subestimar geração custa quatro vezes mais que superestimar, usar o P80 do Chronos reduz o custo médio observado para **58,740425**, contra **82,795464** do P50 e **100,488448** do HGB. O P80, entretanto, tem MAE maior. No estudo separado de classificação, baixar o corte do HGB de 0,5 para 0,2 reduz o custo histórico de 191 para 158, mas gera 156 alarmes e ultrapassa o orçamento de 120 da seleção anterior.

## Arquivos e fontes

A pasta desta entrega é [M02-06](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/). Ela contém:

| Arquivo | Papel |
| --- | --- |
| [protocolo.json](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/protocolo.json) | Fontes, recortes, três cenários por estudo e critérios definidos antes da clínica |
| [adendo_verificacao.json](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/adendo_verificacao.json) | Código, comando e escopo da conferência independente, fixados antes de executá-la |
| [custos.csv](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/custos.csv) | 36 combinações de 12 ações com três cenários contínuos |
| [custos_alarmes.csv](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/custos_alarmes.csv) | 66 linhas com contagens e custos dos classificadores, por fold e no agregado, mais ações constantes |
| [resultado.json](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/resultado.json) | Recibo da execução, fontes, hashes e verificações |
| [parecer.md](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/parecer.md) e [respostas.md](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/respostas.md) | Interpretação e decisão aplicadas |

O arquivo [clinica_decisao_forecast.py](../../notebooks/clinica_decisao_forecast.py) foi copiado sem alterações de `D:\Downloads`. Os 8.024 bytes têm o mesmo SHA-256 nas duas localizações: `5d129c89a32bc782390a7f56de74e7faa39b5c390b30f353085ca74bcc3692ec`. A autoria original não foi estabelecida pelo conteúdo. A clínica executada está em `reports/fechamento_m00_m09/bloco2_engenharia/M02-06/clinica/20261125T162028Z_f0f4439d`.

A primeira fonte é o run M09.3 `20261117T213329Z_3b201a01`, com 168 origens de 03/07/2026 às 04h até 10/07/2026 às 03h, no formato de timestamp original. Foram lidos `predictions.csv`, `alinhamento_alvos.csv` e `quantis_26_passos.npz`. As dez variantes pontuais arquivadas são persistência, linear, HGB, três sementes de MLP, três de GRU e Chronos P50. Foram acrescentadas duas ações já disponíveis nos quantis: Chronos P20 e P80.

A segunda fonte é `reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1`. São 504 origens por método, de 11/07/2026 às 06h até 01/08/2026 às 05h, com 113 positivos e 391 negativos. Os métodos são frequência histórica, regressão logística com meteorologia e classificador HGB com meteorologia. Essa coorte difere da anterior; as perdas dos dois estudos não foram misturadas.

Os estudos já foram examinados anteriormente. A nova execução reaplica regras às previsões guardadas: não transforma julho em um teste novo, não ajusta modelos e não escolhe uma política final depois de olhar um período apresentado como intocado.

## Como os timestamps e os quantis foram tratados

Cada uma das 12 ações contínuas foi alinhada pelas mesmas origens e pelos mesmos alvos. O observado de cada modelo teve de coincidir com o da tabela de alinhamento. Não se permitiu comparar uma previsão com o alvo de outra linha ou excluir horas de uma política para melhorar sua média.

O contrato é horizonte de 24 horas a partir da origem, com atraso assumido de disponibilidade de duas horas. Portanto, a última geração disponível e a geração alvo ficam separadas por 26 horas. O arquivo quantílico tem forma `[168, 9, 26]`: 168 origens, nove níveis de 0,1 a 0,9 e 26 passos. Foi utilizado o último passo, índice 25 começando em zero. Os níveis 0,2, 0,5 e 0,8 aparecem diretamente nos índices 1, 4 e 7. Não houve interpolação, ordenação corretiva dos quantis, truncamento de valores ou criação de uma distribuição a partir de poucos pontos.

A mediana extraída do NPZ foi comparada à previsão pontual Chronos arquivada e coincidiu dentro de `1e-10`. Esses controles tornam a comparação internamente compatível com o contrato. Não comprovam o fuso oficial, a borda do intervalo de geração, a publicação histórica da meteorologia ou a vigência do cadastro. Essas restrições de operação permanecem abertas.

## Por que a perda muda a ação

Considere `r = y − a`, em que `y` é a geração observada e `a` é a ação baseada na previsão. Se `r > 0`, a ação ficou abaixo do observado; se `r < 0`, ficou acima. A perda utilizada é:

```text
L(y, a) = cu × max(y − a, 0) + co × max(a − y, 0)
```

`cu` pesa a subestimação e `co` pesa a superestimação. Com ambos iguais a 1, a fórmula é o erro absoluto, cuja média é o MAE. Se `cu=4` e `co=1`, errar 10 MWmed para baixo custa 40 unidades relativas; errar os mesmos 10 para cima custa 10. O valor observado não mudou: mudou a regra usada para avaliar a consequência da ação.

Uma conta simples, conferida pela clínica, mostra por que isso importa. Se a geração fosse 0 com probabilidade 0,7 e 100 com probabilidade 0,3, a ação 0 teria perda média simétrica 30; a ação 100, perda 70. Com subestimação quatro vezes mais cara, a ação 0 teria perda 120, enquanto a ação 100 continuaria com perda 70. A ação preferida se inverte sem que as probabilidades mudem.

Sob essa perda linear assimétrica, um quantil condicional de nível `tau = cu / (cu + co)` minimiza o custo esperado. Logo, 1:1 aponta para P50; 4:1 para P80; e 1:4 para P20. Isso é uma propriedade da perda e da distribuição verdadeira. Um quantil produzido por modelo é uma estimativa e pode estar descalibrado.

A identidade utilizada na conferência foi `L = (cu + co) × Pinball_tau`. O script independente recalculou essa igualdade amostra por amostra e comparou cada média com o CSV produzido pela clínica. A tolerância para as médias foi `1e-10`; para a identidade por amostra, `rtol=1e-13` e `atol=1e-12`.

## Resultados da previsão contínua

| Ação | MAE — MWmed | Custo 1:1 | Custo 4:1 | Custo 1:4 |
| --- | ---: | ---: | ---: | ---: |
| Persistência | 37,991646 | 37,991646 | 90,453807 | 99,504423 |
| Linear | 33,678664 | 33,678664 | 106,919681 | 61,473637 |
| HGB, semente 17 | 32,323956 | 32,323956 | 100,488448 | 61,131333 |
| Chronos P50 | 31,340738 | 31,340738 | 82,795464 | 73,908228 |
| Chronos P20 | 38,144130 | 38,144130 | 136,147486 | 54,573165 |
| Chronos P80 | 39,016937 | 39,016937 | 58,740425 | 136,344261 |

MLP e GRU continuam integralmente em `custos.csv`, com todas as sementes, sem escolher apenas a execução mais favorável. Entre as 12 ações, o menor custo observado de cada cenário foi P50 no simétrico, P80 quando subestimar custa quatro vezes mais e P20 quando superestimar custa quatro vezes mais.

P80 eleva a ação. Seu viés, definido aqui como `observado − ação`, é −25,867945 MWmed: em média, a ação fica acima da geração. Ele subestimou em 16,07% das origens. Isso explica a redução da perda quando subestimar é caro e o aumento quando superestimar é caro. A mesma ação tem MAE 39,016937, pior que o P50 de 31,340738. Menor custo num cenário e menor erro absoluto são perguntas diferentes.

As 168 emissões foram também divididas em sete blocos cronológicos de 24. No cenário 4:1, P80 teve custo menor que P50 em seis dos sete blocos. No quarto bloco, P50 custou 40,340159 e P80, 59,054348. No sexto, os custos foram 167,668077 e 110,806826. No agregado 1:1, P50 fica à frente do HGB, mas teve MAE menor em quatro dos sete blocos. A liderança agregada não significa vitória em todos os períodos. Esses blocos são descrições da mesma semana, não sete testes independentes ou uma estimativa de confiança futura.

## Como probabilidade e custo definem o alarme

O evento salvo é uma queda de pelo menos 22,77 MWmed entre a última geração disponível e a geração alvo. As extremidades estão separadas por 26 horas. Esse rótulo não mede uma rampa de uma hora, nem identifica quando a queda ocorreu no intervalo.

Os cálculos utilizaram somente `p_event` dos classificadores já salvos. P10, P50 e P90 não definem uma distribuição completa e não bastam para obter, sem hipóteses adicionais, a probabilidade de um evento arbitrário. Nenhuma probabilidade foi deduzida deles.

Para uma emissão com probabilidade `p`, o custo esperado de alarmar é `cFP × (1 − p)`; o de não alarmar é `cFN × p`. Comparar as expressões leva à regra `p >= cFP / (cFP + cFN)`. Os cortes considerados foram 0,5, 0,2 e 0,8, conforme os custos. A igualdade foi tratada com `>=`. O cálculo não prova que os valores de `p_event` estejam calibrados para operação.

| Cenário | Método e corte | TP | FP | FN | Alarmes | Custo total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| FP=1, FN=1 | Logística, 0,5 | 53 | 28 | 60 | 81 | 88 |
| FP=1, FN=1 | HGB, 0,5 | 74 | 35 | 39 | 109 | 74 |
| FP=1, FN=4 | Logística, 0,5 | 53 | 28 | 60 | 81 | 268 |
| FP=1, FN=4 | Logística, 0,2 | 78 | 68 | 35 | 146 | 208 |
| FP=1, FN=4 | HGB, 0,5 | 74 | 35 | 39 | 109 | 191 |
| FP=1, FN=4 | HGB, 0,2 | 90 | 66 | 23 | 156 | 158 |
| FP=4, FN=1 | Logística, 0,5 | 53 | 28 | 60 | 81 | 172 |
| FP=4, FN=1 | Logística, 0,8 | 27 | 6 | 86 | 33 | 110 |
| FP=4, FN=1 | HGB, 0,5 | 74 | 35 | 39 | 109 | 179 |
| FP=4, FN=1 | HGB, 0,8 | 49 | 17 | 64 | 66 | 132 |

`TP` conta eventos com alarme; `FP`, alarmes sem evento; e `FN`, eventos sem alarme. O custo é `cFP × FP + cFN × FN`. Por exemplo, no cenário de FN caro, HGB com corte 0,2 custa `66 + 4 × 23 = 158`. O custo por emissão é `158 / 504 = 0,313492` unidade relativa. Não há conversão desse valor para MWmed ou moeda.

As ações constantes evitam avaliar só modelos complexos. Nunca alarmar custa 113, 452 e 113 nos três cenários. Sempre alarmar custa 391, 391 e 1.564. Com FP caro, a logística em 0,8 custa 110, próxima da ação de nunca alarmar; o HGB em 0,8 custa 132 e perde dessa referência simples. Isso mostra que a preferência entre modelos depende do custo e de quais ações são permitidas.

A política arquivada selecionou HGB no corte 0,5 com teto de 120 alarmes sobre as 504 emissões: foram 109 alarmes e custo 191. O corte analítico 0,2 reduz o custo observado para 158, mas produz 156 alarmes, acima do teto. Ele não atende à mesma restrição. Além disso, o arquivo antigo registra `capacity_enforced_at_runtime=false`: o teto da seleção não é um mecanismo executável de controle de alarmes futuros. Nenhuma dessas políticas foi substituída pela análise atual.

## O que foi executado e preservado

A clínica terminou com código 0 e gravou 36 linhas de cenários e 252 linhas de blocos. A verificação independente terminou com código 0, recalculou as 36 médias, conferiu as coortes e produziu 66 linhas de classificação. Dessas, 60 são comparações por método, regra e fold/agregado; seis são as ações constantes agregadas. O corte 0,5 idêntico no cenário simétrico aparece uma vez, evitando duplicar a mesma regra.

Antes e depois do cálculo foram conferidos os hashes das saídas declaradas nos recibos das fontes. Os modelos anteriores, seus resultados e seus critérios históricos foram preservados. A clínica não foi executada de novo durante a verificação. Os logs reais estão em `execucao_clinica.log` e `execucao_verificacao.log`. A captura do console da clínica perdeu alguns acentos; os arquivos numéricos têm hashes registrados e não foram alterados por esse problema de apresentação.

A verificação pode ser lida em [aplicar_custos.py](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/aplicar_custos.py). Seu lançador [executar_verificacao.py](../../reports/fechamento_m00_m09/bloco2_engenharia/M02-06/executar_verificacao.py) registra comando, início do protocolo, código de saída e log. Ele recusa sobrescrever esta execução. Não é necessário repeti-la para consultar os resultados.

Não foi preciso abrir Docker, instalar pacotes, baixar pesos, chamar nuvem, publicar mudanças ou acionar equipamentos. A análise usa NumPy e arquivos locais. A clínica recuperada continua disponível para um estudo futuro com outro diretório de saída e protocolo adequado.

## Aplicação ao projeto

O item M02-06 passa a ter evidência executada de perda assimétrica, conexão entre custo e quantil, comparação explícita de FP/FN e interpretação das limitações. As respostas técnicas foram entregues integralmente em `respostas.md`; não são respostas independentes do usuário.

Para uma política operacional futura, precisam ser definidos antes da nova avaliação: os custos reais ou cenários aprovados, a definição e o horizonte do evento, o orçamento de alarmes e seu mecanismo de execução, os cortes ou quantis escolhidos e o período de acompanhamento. Será necessário observar calibração, custo, quantidade de alarmes e estabilidade ao longo do tempo. A janela já explorada não pode ser reutilizada como evidência independente de generalização.

Integridade foi verificada pelos hashes; compatibilidade, pelo alinhamento e pelas fórmulas. A atualidade da previsão e a sustentação da política precisam de medições novas em operação. Este fechamento técnico não transforma arquivos históricos em shadow ao vivo, CI remoto, monitoramento contínuo ou aprovação de produção.
