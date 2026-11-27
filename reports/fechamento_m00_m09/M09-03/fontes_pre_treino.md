# M09-03 — fonte congelada e alcance do pré-treino

25/11/2026 · Leitura e conferência assistidas: Codex.

Foi lido o [model card da revisão `a0e552de83495b5c28c14c71c374f3e33280b340`](https://huggingface.co/amazon/chronos-bolt-tiny/blob/a0e552de83495b5c28c14c71c374f3e33280b340/README.md), na cópia local de `models/pretrained/chronos-bolt-tiny/`. Não foi substituído por uma versão móvel de `main`.

O README tem 8.659 bytes e SHA-256 `cc7f60bc7290b5e6146589dae9842a3c9b59d254e9d1d65fc2ef127f3c2498cd`, coincidente com `docs/model_source_m09_3.json`. `limites_avaliacao.json` também contém a conferência dos artefatos previstos pelo manifesto.

O documento descreve pré-treino amplo de séries temporais e apresenta resultados de um benchmark próprio. A declaração sobre ausência de exposição aos datasets daquele benchmark não identifica a série CJU_BA5EIGT nem certifica o experimento Renewcast. Não há, no model card examinado, um manifesto por série que permita resolver essa correspondência.

Os recibos locais M09.3 preservam `pretraining_overlap_verified=false`. Não ajustar os pesos no laboratório resolve a questão do ajuste local, mas não prova exclusão do corpus de pré-treino.

## Evidência que permitiria avançar

As perguntas abaixo estão preparadas, não enviadas:

- Existe manifesto de séries e versões de dados associado a esses pesos, com datas-limite e exclusões verificáveis?
- É possível confirmar especificamente a presença ou exclusão das séries ONS e do período usado aqui, distinguindo pré-treino, avaliação e eventuais versões derivadas?

Até obter evidência suficiente, a sobreposição fica indeterminada. O plano de avaliação prospectiva em `limites_avaliacao.json` é apenas proposto: nenhum período foi reservado e nenhuma nova inferência ocorreu.
