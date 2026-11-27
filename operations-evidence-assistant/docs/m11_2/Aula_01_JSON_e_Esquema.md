# Aula 01 — O que um JSON válido realmente garante?

Na M11.1, o SmolLM2 começou a escrever `0.7164359…` no campo do corte do SatMon. Esse prefixo era do pico; o corte era `0.7199442558330269`. Se o modelo devolver essa troca em um objeto bem escrito, um parser JSON não tem como descobrir o erro. Nesta rodada a resposta passa por três perguntas, em ordem.

| Porta | Pergunta | Exemplo que não passa |
| --- | --- | --- |
| JSON restrito do laboratório | A resposta inteira é um valor JSON aceito pelo parser, sem chaves duplicadas nem números não padronizados? | Uma cerca Markdown em torno do objeto, um objeto cortado, duas chaves `cutoff`, `NaN`. |
| Esquema Pydantic | É um objeto com os campos exigidos e os tipos e domínios definidos? | `s2` omitido; `s1: 0.8` em vez de `"0.8"`; campo extra. |
| Fidelidade | Os valores, a classe, a razão e as citações concordam com a fonte deste caso? | Trocar `s1` por `cutoff` mantendo ambos como strings decimais. |

O parâmetro `object_pairs_hook` do [parser da biblioteca padrão](https://docs.python.org/3.12/library/json.html) recebe os pares antes de virarem um dicionário. É ali que o laboratório evita a perda silenciosa de uma chave repetida. `parse_constant` rejeita constantes que o comportamento padrão aceitaria, como `NaN`. Temos também um limite de texto; não tentamos extrair o primeiro objeto encontrado, remover cercas, completar chaves ou chamar o modelo de novo. Tentar consertar a saída seria outra intervenção, com outra taxa de falha a medir.

O [modo estrito do Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) e a opção [`extra="forbid"`](https://docs.pydantic.dev/latest/api/config/) mantêm um contrato visível. `Relatorio.model_validate(raw)` recebe o dicionário já decodificado. As métricas são texto decimal por desenho para poder confrontar o valor sem passar por um `float`; `s1` e `s2` são chaves obrigatórias que aceitam `null`. Isso deixa distintos “campo omitido”, “medição ausente” e “medição com valor zero”.

## Contraprova guiada

Para a fonte com duas leituras exigidas, pico `0.80`, melhor par `0.62` e corte `0.70`, o par não confirma o alarme. A resposta esperada tem `code="ISOLATED"`. Este objeto é sintática e estruturalmente aceitável:

```json
{"id":"caso_s2","code":"ISOLATED","cutoff":"0.80","s1":"0.80","s2":"0.62","reason":"pair_below","refs":["k","s1","s2","cutoff"]}
```

O corte copiou o pico. A classe e a razão continuam possíveis na **fonte real**, mas o campo publicado ainda seria falso. O verificador detecta `numero_divergente:cutoff`. Abra `contraprovas.json`: no teste `omissao_s2`, a falha acontece uma etapa antes; em `pico_virou_corte`, chega à comparação factual. No segundo caso, a resposta final volta a mostrar o corte original `0.70`.

**Teste de transferência:** a interface exibe um JSON perfeito com um ID diferente e as métricas iguais. O tipo do ID está certo. Em qual etapa o erro deve ser contado e como ele aparece separado da validade estrutural?
