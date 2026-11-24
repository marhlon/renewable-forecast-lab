# Devolutiva — M10.3

Execução Windows **`20261123T195301Z_332fb306`**, usando o M10.2
`20261119T101049Z_253ff59f`. O comando autoral foi executado uma vez.
A implementação está em
[`m10_3_alarme_autoral.py`](../../notebooks/m10_3_alarme_autoral.py):

```python
import numpy as np

def iniciar_alarmes(escores, utilizavel, *, limiar, consecutivos):
    escores = np.asarray(escores, dtype=float)
    utilizavel = np.asarray(utilizavel, dtype=bool)
    inicios = np.zeros(escores.shape, dtype=bool)
    contagem = 0
    for i in range(len(escores)):
        if utilizavel[i] and escores[i] >= limiar:
            contagem += 1
            if contagem == consecutivos:
                inicios[i] = True
        else:
            contagem = 0
    return inicios
```

## 1. Sequência e causalidade

Com limiar 0,70 e duas confirmações, os índices que disparam são
**`[1, 5, 8]`**:

| Índice | Escore | Utilizável | Contagem | Início |
|---|---:|---|---:|---|
| 0 | 0,70 | Sim | 1 | Não |
| 1 | 0,80 | Sim | 2 | **Sim** |
| 2 | 0,90 | Sim | 3 | Não |
| 3 | 0,95 | **Não** | **0** | Não |
| 4 | 0,88 | Sim | 1 | Não |
| 5 | 0,89 | Sim | 2 | **Sim** |
| 6 | 0,65 | Sim | **0** | Não |
| 7 | 0,71 | Sim | 1 | Não |
| 8 | 0,71 | Sim | 2 | **Sim** |

A igualdade ao limiar conta. O índice 3 reinicia a sequência mesmo tendo
escore finito, porque a leitura não é utilizável. O índice 6 também
reinicia, por estar abaixo do corte. O alarme só existe na confirmação;
não volto seu timestamp para o primeiro ponto nem sinalizo novamente
enquanto a mesma sequência continua.

Se eu filtrasse a linha 3, apagaria o reset. Os índices originais 4 e 5
seriam tratados como continuação da sequência iniciada em 0, e o disparo
original de **5 desapareceria**. Na tabela filtrada os disparos ficariam
nos índices 1 e 7, correspondentes aos índices originais **1 e 8**. Além
de mudar a regra, a filtragem esconderia a lacuna no relógio.

A função usa apenas o prefixo já disponível e preserva os argumentos. Não
recebe categorias ou IDs: uma anotação retrospectiva não interrompe a
contagem se a medição continua utilizável.

## 2. Alarme e exposição

No desenvolvimento, há **101.133 instantes utilizáveis fora de todas as
categorias anotadas**. Cada instante representa 900 s de exposição:

```text
exposição = 101.133 × 900 / 86.400
          = 101.133 / 96
          = 1.053,46875 dias equivalentes

taxa = 4 / 1.053,46875
     = 0,003796980214 alarmes sem anotação por dia equivalente
```

A taxa fica abaixo do teto de **0,50 alarme sem anotação por dia
equivalente**, usando a mesma unidade. Não divido pelos dias de calendário,
pelos oito IDs ou pelo total de leituras acima do corte. A cobertura e a
exclusão das categorias definem o denominador. O teto é didático e não
comprova capacidade operacional da missão.

Os **15 inícios** do desenvolvimento se dividem em três primeiros créditos,
seis repetições no mesmo evento, quatro sem anotação e dois ignorados por
categoria. A precisão entre inícios avaliáveis é, portanto,
`3 / (15 - 2) = 3/13 = 23,0769%`. Os 2.822 pontos acima do limiar não
representam 2.822 notificações. O orçamento de alarmes sem anotação também
não controla sozinho repetições e carga total.

O atraso mediano dos três IDs detectados foi **26,82835 min**, e o P90,
**98,46783 min**. Essas medidas descrevem somente os detectados, contadas
desde o primeiro início anotado do respectivo ID; não incluem os perdidos
como se tivessem atraso zero.

No teste, houve exposição positiva de **1.065,208333 dias equivalentes** e
zero alarmes sem anotação. A taxa é `0 / exposição = 0`. Já a precisão
seria `0 / 0`, pois não existe início avaliável: fica **indefinida**. Mediana
e P90 do atraso também ficam indefinidos. Essas situações são compatíveis;
o silêncio não demonstra precisão perfeita nem compensa os oito IDs perdidos.

## 3. O que explica imediatamente o 0/8 e o que investigar

A política escolhida no desenvolvimento foi Isolation Forest, com
**limiar 0,7199442558330269 e duas leituras consecutivas**. Dos 33 candidatos,
29 foram viáveis. A política foi gravada e o pontuador reproduziu o
desenvolvimento com diferença máxima de escore **zero**, antes de liberar
a avaliação do período reservado.

| Evidência local | Desenvolvimento | Teste |
|---|---:|---:|
| Maior escore utilizável | 0,7593997320951837 | **0,7164359650668679** |
| Pontos que atingiram o corte | 2.822 | **0** |
| Inícios de alarme | 15 | **0** |
| IDs detectados / observáveis | 3/8 | **0/8** |

No teste, **o maior escore já fica abaixo do limiar**. Não houve sequer
um cruzamento, portanto o problema imediato não é uma coleção de picos
isolados que falhou na confirmação. Reduzir de duas para uma leitura,
mantendo esse limiar, não poderia criar um disparo. Essa conclusão vem da
desigualdade observada, sem executar outra política no teste.

Os oito IDs tinham oportunidade de observação na coorte global e foram
classificados como perdidos. Não os confundo com IDs sem nenhum instante
elegível. A disponibilidade global pela união dos canais também não torna
todos os IDs observáveis em cada visão de canal, nem permite somar essas
visões como eventos diferentes.

**Hipótese para M10.4:** as combinações dos três canais nas anomalias de
2011–2013 ocupam regiões consideradas menos raras pela floresta original
do que os episódios que determinaram o corte no desenvolvimento. Uma
mudança da distribuição conjunta ou da contribuição de um canal pode
reduzir os escores. Isso é uma hipótese estatística; os números não
identificam mudança física de regime, manutenção ou defeito instrumental.

Eu compararia os canais padronizados pela mediana/MAD originais e a
distribuição dos escores por blocos temporais, separando intervalos
anotados e sem anotação. No desenvolvimento, definiria ablações por canal
e por pares, mantendo períodos, grade, frescor, regra de confirmação,
orçamento e métricas por ID sob controle. Cada alternativa teria sua
seleção restrita ao desenvolvimento; a política original e este resultado
ficariam preservados.

Evidência favorável à hipótese seria localizar uma mudança consistente
nas combinações ou contribuições dos canais associada à queda dos
escores, com ablações controladas sustentando essa explicação. Para mudar
a decisão de **não promover a política**, exigiria uma alternativa
congelada que detectasse mais IDs em período ainda não usado, respeitando
o orçamento e apresentando os atrasos e a cobertura. A mera ausência de
alarmes sem anotação não bastaria.

Não executei ablação ou limiar alternativo em 2011–2013 nesta entrega.
Esse recorte agora foi observado; uma regra formulada a partir dele
precisa de outra avaliação independente.

## Arquivos e conferência

Passaram os exemplos do runner, a comparação autoral de cada candidato
em desenvolvimento e da política congelada no teste, além dos dez testes
adicionais. O guia está em [Explicacao_Passo_a_Passo.md](Explicacao_Passo_a_Passo.md).

Evidências da execução:
[resultado.json](../../reports/m10_3/20261123T195301Z_332fb306/resultado.json),
[política congelada](../../reports/m10_3/20261123T195301Z_332fb306/politica_congelada.json),
[métricas](../../reports/m10_3/20261123T195301Z_332fb306/metricas_episodios.csv),
[IDs do teste](../../reports/m10_3/20261123T195301Z_332fb306/eventos_teste.csv)
e [relatório HTML](../../reports/m10_3/20261123T195301Z_332fb306/relatorio.html).

A [auditoria independente](../evidencias_m10_3_local/auditoria_resultados.json)
recalculou as 33 candidatas exclusivamente no desenvolvimento e fez
somente o replay da política congelada no teste. Conferiu hashes,
exposição e associação por ID, sem reajustar modelos. A cronologia dos
arquivos e a ordem declarada no código não constituem um registro
independente do primeiro acesso de leitura ao teste; esse limite está
registrado no JSON da auditoria.
