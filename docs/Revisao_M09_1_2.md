# M09.1 e M09.2 — revisão e avanço

17/11/2026 · Marlon A. Bomfim

**Sim: montar o laboratório Transformer foi uma continuação pertinente.** Ele corresponde à unidade M09.2 prevista. A orientação anterior precisava trazer a sequência concreta, os arquivos e o critério de encerramento; não cabia ao aluno adivinhar essa passagem.

## Atenção autoral

A função e os seis casos apresentados em 16/11 foram transcritos e executados nesta revisão: seis aprovados. A função também passou nos oito grupos do comparador NumPy/PyTorch, com maior diferença `4,44e-16`. Lotes, eixo de chaves, máscara antes da normalização, softmax estável e validações estão corretos. Não se pede alteração do algoritmo nem repetição do exercício.

O erro de CLI decorre de um argumento faltante. Na versão recebida, `--autoria` exige o caminho:

```powershell
python notebooks/laboratorio_atencao.py --autoria notebooks/m09_atencao_autoral.py --verificar
```

Executar sem `--autoria` chama a referência do laboratório. Seus logs Windows `20261116T225653Z_d6086b39` e `20261117T150330Z_b5b7c30d` confirmam o modo normal. A validação da função recebida foi feita agora na revisão Linux; não é falsamente atribuída àqueles logs. O código é aceito no contrato da unidade; autoria independente não é certificada por coincidência numérica.

## Composição Transformer recebida

Recebidos dois arquivos de texto: o runner `laboratorio_transformer.py` e o verificador `m09_transformer_verificacao.py`. Ambos compilam como Python. O módulo `renewable_forecast.transformer_blocks` não foi anexado; portanto as treze conferências não foram reexecutadas independentemente nesta sessão. O código de orquestração/verificação foi revisado e os logs Windows são reconhecidos como evidência relatada de execução.

Execuções relatadas: `20261117T154658Z_0897bf5a` completa, e `20261117T154706Z_6cd8d15b` em modo `--verificar`. Treze grupos aprovados, maior diferença `6,66e-16`; prefixo e recarregamento com diferença zero. Não é necessário repetir esses comandos para avançar.

| Elemento recebido | Interpretação correta |
| --- | --- |
| Encoder `[1,24,16]` | Uma janela com 24 posições, cada uma representada por 16 coordenadas. Não são 16 variáveis meteorológicas observadas. |
| Quatro cabeças | Cada cabeça opera com dimensão4 quando `d_model=16`; as saídas são combinadas pela projeção final. |
| Decoder `[1,6,16]` | Seis consultas sintéticas com posição; não seis horizontes futuros e não previsões em MWmed. |
| Cross-attention | Q vem das consultas do decoder; K/V vêm da memória do encoder. |
| Blocos post-norm | A soma residual precede LayerNorm em cada subcamada. FFN atua nas coordenadas de cada posição, sem ser uma nova consulta entre horários. |
| Máscara do comparador | O contrato próprio usa True=permitido; o comparador converte para `~allowed` ao chamar `nn.MultiheadAttention`/camadas Transformer. A inversão está explícita. |
| Perturbação de consultas futuras | Prefixos permanecem iguais com memória fixa e máscara causal. Isso não protegeria uma memória que já contivesse alvos futuros indevidos. |
| Gradiente da sonda | `backward()` verifica conectividade do grafo; sem `optimizer.step()` os pesos não são ajustados. |
| Checkpoint recarregado | Demonstra persistência da configuração/inicialização no protocolo; não qualidade preditiva. |

O verificador também aborda a sutileza do empilhamento: a última consulta pode coincidir entre máscara livre/causal em uma camada e diferir depois de duas, porque as representações intermediárias diferem. Isso é uma continuação substantiva do M09.1, não outro exercício de contagem.

## Aceite e próximo trabalho

M09.1: implementação e casos recebidos aceitos, função executada nesta revisão. M09.2: reprodução Windows relatada e runner/verificador recebidos reconhecidos no escopo acima. Os artefatos completos do módulo e da execução não foram auditados byte a byte. Não se pede reenviar o que já foi demonstrado para começar a próxima unidade.

M09.3 entrega previsões com pesos pré-treinados, alinhamento de26 passos para h24/d2 e comparação com os mesmos baselines. O parecer integrado dessa unidade poderá consolidar a interpretação ainda pendente, sem uma sequência adicional de microtarefas retrospectivas.
