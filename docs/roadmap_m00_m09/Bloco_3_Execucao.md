# Bloco 3 — etapas 7, 8 e 9

26/11/2026 · [relatório completo](Relatorio_Engenharia_Bloco3.md).

O último bloco abrangeu 18 IDs. Doze têm entrega integral de engenharia; três outros têm construção/teste local aceitos parcialmente. Seis IDs operacionais continuam abertos. Nenhum exercício do usuário é exigido para o aceite aplicado.

| Área | O que foi executado | O que continua limitado |
| --- | --- | --- |
| Dados | Bronze imutável, silver/quarentena, gold causal, replay/idempotência/recuperação e 18 medições reais | Um host, um mês, chegada hipotética; sem cluster ou continuidade demonstrados |
| Modelos | Global/local em quatro séries; LightGBM/CatBoost; GRU12/lotes4/4/3; Transformer12/5/E12/H3 | Novo modelo global não validado em séries desconhecidas; adaptações neurais são verificações de contrato |
| Avaliação final | 14 variantes congeladas sobre 671 origens de setembro obtido depois do freeze | Snapshot retrospectivo, hipóteses M04 e sobreposição de pré-treino desconhecida |
| Registry | MLflow versões1/2, alias1→2→1 e inferência equivalente | Duas versões do mesmo pacote; nenhuma melhoria de modelo presumida |
| Serviço | HTTP real protegido e 480 requisições locais | Sem publicação ou sustentação contínua |
| CI | Dois runs Actions reais: erro causal esperado e correção com16testes; logs/commits conferidos | Branch isolada; sem merge/deploy ou proteção de main ativada |
| Operação | Coletor/drift/replay e plano cloud preparados | Shadow, monitoramento ao vivo, ambiente alvo e implantação ainda não demonstrados |

O HGB candidato não atingiu o critério de ganho de MAE. Persistência teve35,616479MWmed e Chronos35,689509; o HGB do bloco2 teve40,160344. Nenhum teste foi reajustado. O resultado completo inclui vieses, intervalos, probabilidades, custo e as três sementes neurais.

Confira sem repetir treino ou inferência:

```powershell
python scripts/verificar_roadmap.py --bloco 3 --gate engenharia
python scripts/conferir_bloco3.py
```

Intervenções necessárias para encerrar o restante:

1. **CI remoto já executado:** revisar a branch `codex/bloco3-ci-20261126` para eventual integração à main. Os dois commits/runs foram aprovados no escopo do CI; não houve merge ou deploy. Abrir PR acionará uma nova rodada e depende da próxima ação do titular.
2. **Fonte operacional:** comprovar fuso/intervalo, chegada/vintage e cadastro, preservando os quatro bloqueios M04.
3. **Ambiente alvo:** definir exposição, responsável, custos e capacidade; homologar segurança e carga nesse ambiente, preservando M06-07/08 como pré-condições do shadow.
4. **Observação real:** operar a janela prospectiva predefinida e reconciliar alvos; observar cobertura, Brier, alarmes e drift sem retreinar/promover automaticamente.
5. **Cloud, se executada:** titular/conta/região/teto financeiro e autorização antes de criar recursos. O plano atual não criou recursos nem cobrança cloud.

Não foi necessário abrir Docker. Os controles locais não substituem essas comprovações. A próxima ação concreta depende de acesso/ambiente e observação real, não de repetir implementações já aceitas.
