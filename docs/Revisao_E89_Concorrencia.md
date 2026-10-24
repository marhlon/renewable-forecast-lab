# E89 — revisão da concorrência e da autoria

Marlon Alves Bomfim · 14/10/2026 · run informado `20261014T000751Z_15fe13d2`

**Decisão: função autoral aceita no contrato desta atividade; recomendação experimental de quatro clientes.** A leitura já garante nove pares únicos de rodada/concorrência e o protocolo fornece 250 ms e 0,95. Não é necessário reescrever a função para continuar.

A revisão utiliza o código colado e os números arredondados do console. Não foram recebidos nesta mensagem o `summary.csv`, o recibo nem o `decisao.json` deste run. Portanto, não se atribui à revisão uma nova conferência de hashes ou recálculo dos P95 a partir das tentativas individuais.

| Clientes | Mediana da vazão útil, req/s | Pior P95, ms | Elegível nas três rodadas? |
| --- | ---: | ---: | --- |
| 1 | 20,49 | 80,30 | Sim |
| 4 | 33,45 | 219,64 | Sim |
| 8 | 30,46 | 392,36 | Não |

O corte de vazão é `0,95 × 33,45 = 31,7775 req/s`. Somente quatro clientes o alcançam entre os elegíveis. As nove fases informam 120/120 respostas corretas: 1.080/1.080 no log. Isso não estima uma taxa universal de falhas nula.

## O que foi demonstrado no código

Agrupamento por nível; rejeição se qualquer rodada falha ou tem P95 ausente/não finito/excessivo; mediana apenas das opções elegíveis; busca crescente da menor opção que retém 95%; ausência de candidato com justificativa. A implementação foi executada com a transcrição do console e quatro contraprovas explicitamente sintéticas: nível menor retendo 95%, nenhum elegível, P95 ausente e limite inclusivo de 250 ms. Resultado: decisões esperadas em todos os casos.

Se a função virar API genérica, deverá validar parâmetros e unicidade das rodadas dentro dela. Nesta atividade isso já pertence ao carregador/protocolo. Essa possível extensão não invalida a autoria recebida.

## Ajustes do parecer

1. **Escopo da escolha.** “Recomendação experimental de quatro clientes no protocolo local.” Não configura quatro workers, quatro threads nem um teto de admissão na API. O limite didático não é um SLA comercial.
2. **Agregação.** A razão entre medianas da vazão produz +63,25%. Na comparação pareada, os ganhos 4 versus 1 são +74,86%, +35,77% e −1,79%. A terceira rodada não confirma ganho. A rotação de ordem ajuda a distribuir efeitos de posição, mas três rodadas não isolam a causa da variação.
3. **Latência.** Comparando os piores P95, `219,64 / 80,30 = 2,735`, não exatamente três. Piores P95 por nível são uma regra conservadora entre rodadas, não P95 agregado das 360 chamadas. A latência no cliente inclui transporte local, processamento, serialização e possíveis esperas; não decompõe tempo de fila.
4. **Arquitetura.** Chamada síncrona direta dentro de `async def` ocupa o event loop durante essa execução. Isso é consistente com a fonte anteriormente entregue e com sua inspeção relatada. Não comprova CPU saturada. Um processo Uvicorn ainda pode usar threads de bibliotecas nativas; quota de duas CPUs não informa quantas estavam ocupadas.
5. **Decisão de engenharia.** Oito clientes não satisfazem a regra. Não há necessidade demonstrada de alterar o servidor agora: quatro atendem ao exercício, e ainda falta uma demanda real de tráfego que justifique otimização adicional.

## Fechamento sem repetir o benchmark

Se ainda não salvou a decisão, execute na raiz do projeto:

```powershell
python notebooks/analise_concorrencia.py --run-dir reports/performance/CJU_BA5EIGT/h24_event_concurrency_v1/20261014T000751Z_15fe13d2 --autoria
```

A saída deve selecionar `concurrency: 4`, usando os valores completos do CSV. O registro local mantém a distinção entre formato conferido pelo programa e revisão semântica do professor registrada nesta E89. Preserve o seu parecer original; acrescente as ressalvas acima à versão de trabalho. O pacote seguinte não substitui seu notebook autoral nem reexecuta a carga.

**Próxima competência:** M06.5, cliente Windows distribuível, independente do Conda na execução. M06.4 conserva CI remoto pendente; essa pendência não exige repetir compatibilidade ou concorrência.

Fonte técnica: [FastAPI — funções síncronas chamadas dentro de funções async](https://fastapi.tiangolo.com/async/).
