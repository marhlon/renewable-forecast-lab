# Entrega M10.3 — inícios de alarme e transferência temporal

A [função](notebooks/m10_3_alarme_autoral.py) foi usada na execução Windows
`20261123T195301Z_332fb306`. O laboratório foi executado uma vez, a partir
do M10.2 `20261119T101049Z_253ff59f` preservado. Passaram os exemplos do
runner, a comparação em todas as candidatas de desenvolvimento e na política
congelada do teste, além de dez testes adicionais.

Leia a [resposta preenchida](docs/m10_3/Resposta_M10_3.md), com a função e
os três itens pedidos, e o [guia](docs/m10_3/Explicacao_Passo_a_Passo.md).
O [relatório HTML](reports/m10_3/20261123T195301Z_332fb306/relatorio.html)
e o [resultado.json](reports/m10_3/20261123T195301Z_332fb306/resultado.json)
identificam a política e as métricas locais.

A política escolhida detectou 3/8 IDs no desenvolvimento e 0/8 no teste.
O maior escore utilizável do teste ficou abaixo do limiar, sem qualquer
cruzamento. Precisão e atraso ficaram indefinidos. O resultado foi preservado;
nenhum limiar alternativo ou ablação foi executado no teste nesta entrega.

## Conferir sem nova avaliação ou ajuste

Na raiz `C:\renewable-forecast-lab`, com o ambiente existente ativo:

```powershell
python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_3_alarme_autoral.py -v
python satellite-anomaly-monitor/docs/evidencias_m10_3_local/auditar_resultados.py
```

A auditoria recalcula as candidatas apenas no desenvolvimento e faz o
replay da política congelada no teste, usando os escores persistidos.
Não reconstitui a floresta. O laboratório original reconstituiu somente
essa floresta com o ajuste de 2004–2007 e verificou os escores no desenvolvimento.

## Conteúdo e rastreabilidade

O ZIP reúne função, respostas, explicação, testes, código, protocolo e
dados da rodada, além da execução M10.2 fixada e de suas dependências
locais para conferir os arquivos. Não inclui ambiente Python instalado.
A atribuição dos dados ESA permanece nas aulas e na proveniência.
O manifesto `ENTREGA_M10_3_SHA256.json` identifica os membros incluídos,
exceto o próprio manifesto. Os arquivos das execuções foram preservados.

A abertura do HTML foi solicitada ao Windows; não houve inspeção visual
automatizada do navegador. A auditoria registra seus limites: hashes e
cronologia de gravação não são um log independente da primeira leitura do
teste, nem comprovam latência física ou completude das anotações.
