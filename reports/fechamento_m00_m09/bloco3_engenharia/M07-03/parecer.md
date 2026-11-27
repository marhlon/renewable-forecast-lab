# Parecer de engenharia — incremento

Replay local fornecido/executado por Codex em quatro versões de estado, 2976 eventos reais de quatro séries. Um evento foi atrasado sinteticamente por sete dias; suas contribuições indisponíveis em origens anteriores permanecem nulas mesmo depois do reprocessamento. Não se infere chegada histórica do arquivo.

Falha sintética após materializar estágio e antes de trocar o ponteiro preservou o estado; nova instância recuperou e concluiu o lote. Repetições foram noop e conflito de mesma chave foi rejeitado. Gold incremental e referência compartilham SHA256 lógico 1990d7e5ebb72034fd5e6d18a5eebe1b8ec36c87e94b57c4f164d4776bbd8989; mutação de outra série não altera a primeira. Aceite técnico local C1/C2, sem comprovar serviço distribuído, broker ou shadow.

A referência usa os mesmos horários de disponibilidade da simulação, incluindo o atraso, e não uma referência ideal com chegada imediata. Em CEECVA, o evento 05/10 12h só ficou disponível em 12/10 14h. A feature lag2 da origem 05/10 14h continuou nula após o backfill: recomputar o histórico não torna o evento conhecido antes de sua chegada declarada. O target conserva separadamente seu próprio label_available_at.

O estado é um arquivo Parquet por versão e um ponteiro JSON trocado com os.replace. A demonstração reinicializa uma instância leitora depois da exceção injetada; não é um reinício de máquina/serviço. O desenho pressupõe um escritor e snapshot append-only com rejeição de correções conflitantes. Não demonstra fsync/power-loss, locking entre escritores, atualização retroativa ou durabilidade distribuída. Esses limites permanecem separados do aceite deste replay local.
