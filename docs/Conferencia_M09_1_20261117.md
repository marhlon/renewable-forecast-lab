# Conferência M09.1 — 17/11/2026

A versão do laboratório que contém o formatador HTML foi executada com a
função NumPy indicada, concluindo com código 0 e stderr vazio. O comando
registrado foi:

```powershell
python -W error::UserWarning notebooks/laboratorio_atencao.py --autoria notebooks/m09_atencao_autoral.py
```

O [recibo de execução](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/comprovacao_20261117T144147Z_e63fc0be/execucao.json)
preserva o argv literal, o caminho do interpretador, o diretório de trabalho,
os códigos de retorno e os hashes dos logs. `UserWarning` foi tratado como
erro. Sem `--verificar`, esse comando aplica a função também à janela real.

## Formatação conferida

A linha abaixo já estava corrigida ao início deste trabalho e foi validada
como parte da versão executada do [laboratório](../notebooks/laboratorio_atencao.py):

```python
context.to_html(index=False, float_format=lambda valor: f"{valor:.6f}")
```

`float_format` define a apresentação dos números float na tabela HTML com
seis casas decimais. O formatador produz texto, sem alterar os valores do
DataFrame ou o cálculo da atenção. Ele não define a formatação dos outros
elementos do relatório, como os pesos nos tooltips do SVG.

Na nova saída, 72 células float foram conferidas contra `f"{valor:.6f}"`;
os 24 timestamps foram preservados e as posições inteiras permaneceram
corretas. A [validação HTML](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/comprovacao_20261117T144147Z_e63fc0be/validacao_html_autoria.json)
registra esses achados. A comparação com o ZIP distribuído encontrou
somente essa alteração de formatação, documentada no
[patch](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/comprovacao_20261117T144147Z_e63fc0be/correcao_html.patch).

## Código e resultados vinculados

O [resultado da janela real](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/20261117T144205Z_917f4acf/resultado.json)
registra o SHA-256 do laboratório executado:
`1a29a0efece482587228aacffeadfdd585135afd36e2e3892b38616cbef254a8`.
O campo `authorship_sha256` coincide com o hash da
[função NumPy](../notebooks/m09_atencao_autoral.py):
`97d73011dbaa0cc1cb529223da35eb74766ed125369c5aa1d60a0440dee63fea`.
Isso vincula o conteúdo da implementação à execução identificada.

A [conferência integrada](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/20261117T144205Z_917f4acf/conferencia.json)
aprovou oito grupos, com diferença máxima de `4,440892098500626e-16` para
PyTorch, abaixo da tolerância `1e-12`. Os seis testes adicionais também
passaram, conforme o [log do unittest](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/comprovacao_20261117T144147Z_e63fc0be/testes_stderr.log)
e o código de retorno 0 no recibo. O
[stdout do laboratório](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/comprovacao_20261117T144147Z_e63fc0be/laboratorio_stdout.log)
identifica a janela e a pasta do [relatório HTML](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/20261117T144205Z_917f4acf/relatorio.html).

Os arquivos `pesos_livres.csv`, `pesos_causais.csv`,
`janela_e_representacoes.csv` e `projecoes.json` são byte a byte iguais
aos da execução de 16/11/2026. Todos os hashes das entradas e saídas
foram validados.

O escopo é a formatação e comprovação de M09.1. Não foi encontrado material
executável de M09.2 no inventário consultado; esta execução não monta um
Transformer nem realiza treinamento ou avaliação de previsão.
