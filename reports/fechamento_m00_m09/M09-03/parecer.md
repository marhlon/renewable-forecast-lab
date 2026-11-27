# M09-03 — parecer sobre sobreposição de pré-treino

25/11/2026 · Auditoria e interpretação assistidas: Codex. A revisão seguinte decide o cadastro; não se atribui resposta independente ao aluno.

A revisão do modelo e seus documentos locais foram identificados por hash. O [model card congelado](https://huggingface.co/amazon/chronos-bolt-tiny/blob/a0e552de83495b5c28c14c71c374f3e33280b340/README.md) não fornece, no material examinado, evidência suficiente para decidir a presença ou ausência da série ONS no corpus. O campo `pretraining_overlap_verified` permanece **false**.

Isso não comprova contaminação. Também impede apresentar o comparativo como prova de ausência de contaminação. A afirmação do documento sobre seu próprio benchmark não foi transferida para o Renewcast.

A execução local aceita usou uma semana de desenvolvimento já explorada, sem ajuste dos pesos Chronos. Seus números continuam sendo evidência condicional daquele recorte, sem promover o resultado a avaliação externa ou operacional. Não foram repetidos inferência, treinamento ou métricas.

O limite explícito de C2 é suficiente para impedir a conclusão indevida: identidade binária, uso sem fine-tuning e comparação pareada não resolvem o corpus desconhecido. Uma avaliação futura exigiria protocolo anterior aos alvos, modelos e política congelados, período ainda não examinado e contratos point-in-time sustentados. Esse plano **não foi executado nem teve período reservado**.

C1 tem investigação da documentação identificada; C2 tem a incerteza e a restrição registradas. A recomendação é encaminhar a **delimitação concluída para revisão**. Aceitar essa delimitação não certifica ausência de sobreposição nem libera operação. Os limites externos de M04 permanecem.
