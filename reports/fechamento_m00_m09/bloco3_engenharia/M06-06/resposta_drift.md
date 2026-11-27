# Resposta a drift

Referência e limiares foram fixados no protocolo antes do cálculo. Referência: primeiras 24 linhas completas de junho, já examinadas; corrente: 24 seguintes. Contraprovas alteram somente a variável descrita e não são dados de operação.

Alertas de missing/atraso abrem investigação da fonte; não se atribui queda do modelo a rótulo ainda ausente. Mudança de entrada sem aumento de erro abre investigação de cobertura/distribuição; queda de desempenho com entrada estável abre investigação do modelo/coorte. Erro, viés, intervalos e classes requerem alvos realmente conciliados. No máximo uma investigação por variável/janela diária; esse orçamento de triagem não garante probabilidade de falso positivo e não foi calibrado numa sequência prospectiva. O protótipo retorna uma decisão por chamada; deduplicação entre dias/plantões deve ser integrada ao sistema de incidentes antes de operação.

Interromper novas emissões quando origem/chegada/vintage falharem; preservar journal e identidade; avaliar o baseline congelado; rollback somente após revisão humana de integridade e efeito. Não retreinar, recalibrar ou promover automaticamente. Operação real depende de M06-05 e responsável designado.

Construção, execução e parecer: Codex.