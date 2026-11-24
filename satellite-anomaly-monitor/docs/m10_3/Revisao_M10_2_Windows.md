# Revisão da entrega M10.2 — 23/11/2026

**Aceite técnico da rodada Windows `20261119T101049Z_253ff59f`.** Não é necessário rodar ou empacotar M10.2 novamente para avançar.

## Função e saída

O SHA-256 do código colado coincide com `authorship_sha256` do recibo. O runner e o núcleo declarados também coincidem com o pacote M10.2 fornecido. As sete saídas anexadas conferem com os hashes; os nomes com sufixo da interface foram reconciliados sem alterar bytes.

A função centraliza com o **centro do PCA ajustado**, projeta com as componentes nas linhas, reconstrói e soma quadrados em `axis=1`. Isso entrega um escore por instante. Não recalcula centro nem modifica argumentos. Ela passou nas duas contas geométricas em leitura somente, e reproduziu exatamente os 105.165 escores PCA exportados. A segunda conferência, independente, calculou a distância ao plano pelo produto interno com o vetor normal. O delta **(3{,}73\times10^{-14})** do recibo é a comparação Windows com scikit-learn; o delta zero desta conferência é contra os escores persistidos da própria função, uma comparação diferente.

## Evidência interpretada

| Método | AP completa, mesma coorte | AP sem `id_134` |
| --- | ---: | ---: |
| Constante | 0,037214 | 0,009539 |
| Robusto | 0,716427 | **0,356114** |
| PCA | 0,502013 | 0,017142 |
| Isolation Forest | **0,758149** | 0,324910 |

Recalculei AP em ambas as coortes com agrupamento de empates. O ID dominante continha 2.935 de 3.909 pontos positivos, 75,08%. A ordem entre floresta e robusto se inverte ao retirar esse episódio. Não houve reajuste na auditoria. Em 12/06/2009 às 16h UTC, o mesmo instante anotado ficou no percentil 98,25 no robusto e 0,83 no PCA: os canais podem estar afastados das medianas e próximos do plano conjunto. Isso é uma explicação compatível com a geometria, não uma causa física comprovada.

## Empacotador

O modo de gravação `"x"` preserva a primeira entrega, e reabrir o ZIP para verificar cada tamanho e hash é uma boa verificação dos bytes empacotados. Os campos `exit_code=0`, `passed=8` e a contagem de execuções são valores escritos no registro: o empacotador não executa o laboratório ou os testes para produzi-los. Diferencie **declarado em log/registro** de **reexecutado nesta auditoria**. Não recebi o ZIP de entrega nem o arquivo de respostas citado no código, então não atribuí nota às respostas nem tratei os oito testes adicionais como reexecutados. A continuação usa os resultados já conferidos.
