# M04-05 — parecer point-in-time

25/11/2026 · Auditoria e interpretação preparadas com assistência Codex. Não constituem homologação ou prova de transferência independente.

A conferência leu os arquivos existentes da coorte `h24_d2_july_development`, a seleção meteorológica correspondente e os metadados cadastrais. `auditoria_temporal.json` registra o método executado, hashes, contagens, regras conferidas e uma emissão concreta. Não importou o pipeline do projeto, refez features ou executou modelos.

Nas 744 origens, com 11.160 linhas meteorológicas de 15 usinas, não houve divergências de horizonte, atraso declarado, validade/alvo ou última rodada elegível sob a hipótese. Os três cortes de ajuste respeitam a disponibilidade de rótulos registrada; o alvo não integra as 32 features declaradas. Os hashes comparados coincidem. Esses resultados são controles internos, não comprovação das hipóteses externas.

Na primeira emissão, 01/07/2026 06h UTC, a tabela usa histórico até 04h UTC e alvo em 02/07/2026 06h UTC. O alvo fica disponível às 08h pela hipótese de atraso de duas horas. A meteorologia vem da rodada de 00h, tratada como disponível às 06h por hipótese; sua coleta foi registrada em setembro. O cadastro é uma versão consultada posteriormente, com validade histórica não confirmada.

Esse exemplo conecta geração, meteorologia, cadastro, alvo e disponibilidade na mesma origem. A coerência das contas não prova o significado físico do relógio de geração nem a publicação que de fato ocorreu. Uma coleta tardia de arquivo não demonstra, por si só, que a previsão estava indisponível antes; o ponto é a ausência de prova suficiente.

**Integridade:** comparar os bytes com os hashes registrados. **Compatibilidade:** conferir chaves, horizontes, seleção e atrasos declarados. **Atualidade:** verificar se o resultado serve à decisão presente. As emissões de julho são histórico para esta auditoria, não previsões para decidir agora.

A documentação [ONS](https://dados.ons.org.br/dataset/geracao-usina-2) e [Open-Meteo](https://open-meteo.com/en/docs/model-updates) consultada não elimina os bloqueios específicos registrados nos itens anteriores. O cadastro também mantém `historical_snapshot_verified=false`.

C1 dispõe de uma auditoria integrada sob hipóteses, não de confirmação operacional. C2 mantém as três verificações distintas e a restrição de uso. A recomendação é **bloqueado**, dependendo da resolução de M04-02, M04-03 e M04-04 e da revisão das demais dependências do cadastro. Nenhum aceite técnico anterior foi reaberto.
