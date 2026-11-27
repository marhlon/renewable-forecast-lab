# Parecer técnico M06-07

HTTP real em socket 127.0.0.1; chave efêmera somente em memória, comparação constante, limite de bytes lidos inclusive chunked, taxa limitada e contrato de atributos. Contraprovas registradas em contraprovas.json. O log exclui token/cabeçalhos/corpo e a ausência do token foi conferida. Sem portas públicas, TLS, RBAC ou certificação geral. Incidente: interromper processo, invalidar chave por reinício, preservar logs sem segredos e investigar antes de reabrir. Construção, execução e parecer: Codex.
