# Parecer de engenharia — camadas

Execução atribuída a Codex, não a resposta independente do usuário. Bronze preservou os 4,629,118 bytes e SHA256 original; silver tem 389,304 linhas, quarentena 148,080, gold 2,976. Duplicatas inteiras, ids ausentes, MW negativos/não finitos e horários inválidos não recebem imputação. A linhagem usa source_row na bronze e joins exatos de série/tempo na gold.

Segunda construção de silver/quarentena/gold efetivamente executada; hashes lógicos e físicos iguais registrados em resultado.json. A disponibilidade t+2h é hipótese de estudo, não fonte histórica. Contraprova sintética separada testa rejeição. Aceite técnico local dos critérios C1/C2; sem Delta distribuído nem aprovação operacional.

Dos 537.384 registros brutos, 389.304 passaram pelo contrato; 87.048 ficaram em quarentena por id_ons ausente e 61.032 por geração não finita/ausente. A soma fecha o inventário. Nenhuma chave substituta foi inventada para agregados sem id, nem ausência de geração virou zero. As regras de negativo, duplicata e hora inválida foram exercitadas nos testes pequenos; não foram observadas nesses grupos reais.

Bronze é escrita uma vez por contrato de aplicação em caminho endereçado por hash, e uma reutilização confere novamente os bytes. Não há proteção WORM de armazenamento nem proibição de escrita fora do programa. Os hashes publicados detectam uma alteração posterior; não são uma política de acesso do sistema operacional.
