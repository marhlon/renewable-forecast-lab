# Aula 01 — Do registro que você lê ao vetor que o modelo usa

No SatMon, o dado era um número com unidade e concepção definida: 0,716436 era um escore. Num LLM de texto, a escrita `0.716436` entra como **uma sequência de tokens**. O modelo recebe IDs discretos e vetores, sem um tipo especial “número acima/abaixo do limiar”. Por isso a comparação decimal do projeto continua em Python. A geração serve para testar como uma evidência vira texto.

O laboratório usa [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/tree/12fd25f77366fa6b3b4b768ec3050bf629380bac), modelo de texto pré-treinado e ajustado para instruções, disponível publicamente com licença Apache-2.0. A descrição indica inglês; as instruções deste ensaio usam inglês, enquanto a análise da tokenização inclui português. O tamanho foi escolhido para rodar em CPU. Não se infere capacidade em português nem se generaliza a outros LLMs.

## Da mensagem ao ID

O código constrói mensagens com papéis `system` e `user`. `apply_chat_template(..., add_generation_prompt=True)` converte a conversa no formato que o modelo espera e abre o turno de resposta. Veja a string completa em `trilha_tokens.json`. O tamanho cobrado da janela inclui a mensagem de sistema, as regras, os marcadores de papel e o registro. O código compara duas rotas de renderização e tokenização para não duplicar marcadores especiais.

Depois, o tokenizer do modelo divide o texto em peças. Um ID é um endereço de vocabulário, sem relação ordinal com o valor do texto: o ID do caractere `9` não informa se um escore é maior que o corte inteiro. Em `tokens.csv`, `peca_bpe` é a peça como o tokenizer a armazena (inclusive marcações de espaço e bytes); `decode_individual` pode mostrar texto estranho se a peça completar um caractere apenas quando concatenada. O teste correto decodifica a sequência inteira e compara com a string de entrada.

Abra `embeddings.json` e compare os probes 0, 1 e 2. O probe 1 troca acentos; o 2 troca só a vírgula decimal por ponto. Compare caracteres, bytes UTF-8, IDs e quantidade de tokens. Mesmo quando a quantidade fica igual, a sequência de IDs pode mudar. Isso importa para a reprodutibilidade do prompt; não estabelece que tirar acentos melhora a resposta.

## Embedding de entrada e representação após contexto

A matriz de entrada tem uma linha para cada ID do vocabulário. Para `input_ids` de shape `[1,L]`, `model.get_input_embeddings()(input_ids)` seleciona `L` linhas e devolve `[1,L,576]`. No fechamento de cada frase no experimento, o último token é o mesmo `:`, ID 42:

```text
An alarm is rejected.
Status:
```

```text
An alarm is allowed.
Status:
```

O vetor de entrada final é igual nos dois prompts. Após as camadas causais, os vetores diferem: o token nessa posição pôde receber informação de seu prefixo. Isso é uma contraprova de que o vetor contextual depende do texto anterior. O cosseno entre esses vetores não mede semelhança de incidentes nem serve para justificar um índice vetorial; M12 tratará embeddings próprios da recuperação.

**Pergunta para sua devolutiva:** encontre a posição em que a vírgula e o ponto decimal se distinguem. Compare os IDs e veja em qual etapa o último token das duas frases ganha contexto. Use os valores da sua execução e explique por que continuar comparando escores com `Decimal` no programa.
