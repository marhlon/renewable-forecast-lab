# Aula 1 — medir um desvio sem deixar o extremo definir o que é normal

**Problema.** Suponha que um canal passou de 0,75 para 0,80. O aumento é grande para ele? Só a diferença absoluta não responde. Um sensor varia muito por natureza; outro muda pouco. Antes de combinar três sensores, precisamos de uma referência de localização e escala para cada um. A primeira referência desta rodada depende da distribuição histórica, sem usar o sensor mais variável como régua dos demais.

## 1. Quem aprende o quê, e em que período

Usamos os mesmos canais 50, 51 e 52 de M10.1. Agora há mais anos para separar ajuste e desenvolvimento. Os cortes e parâmetros foram definidos antes de calcular os escores desta rodada.

| Partição | Intervalo UTC, fim excluído | Uso |
| --- | --- | --- |
| Ajuste | 01/01/2004 → 01/01/2008 | Aprender mediana, MAD, PCA, Isolation Forest e centros do K-means. |
| Desenvolvimento | 01/01/2008 → 01/01/2011 | Comparar rankings dos três escores já ajustados. |
| Período posterior | 01/01/2011 → 01/01/2014 | Fora do pacote; nenhum escore calculado para ele nesta rodada. |

O recorte está em uma grade de **15 minutos** para inspecionar e executar localmente. Não confunda a grade com a cadência típica de 90 s da fonte. Em cada instante retemos a última amostra no mesmo período, se tiver no máximo **180 s** de idade. A coleta anterior ao início da partição fica fora. Na primeira linha de cada período pode haver ausência perfeitamente legítima. Não há interpolação entre dois instantes.

Para conferir: às 12:00:00, duas amostras foram medidas às 11:56:55 e às 12:00:01. A primeira tem 185 s de idade e expirou; a segunda ainda é futura. A saída é ausente. Trocar por 11:57:00 muda a decisão: 180 s é uma idade válida. Essa fronteira foi escolhida para o exercício; não é um SLA da ESA. Como no M10.1, UTC e disponibilidade na medição são hipóteses. Os valores e unidades não identificam grandezas físicas.

**Ajuste** usa os instantes com os três canais preenchidos que não caem em intervalos `Anomaly`, `Rare Event` ou `Communication Gap`. Isso usa anotações *retrospectivas* para curar a referência histórica; não é uma simulação de treinamento que só conhecia rótulos disponíveis em tempo real. Os modelos recebem só três colunas numéricas, nunca IDs ou classes. A grade completa e a anotação original são mantidas em arquivos separados.

**Desenvolvimento** usa a mesma regra de três canais disponíveis para todos os métodos. Para medir ranking, `Anomaly` é positivo, sem anotação é negativo provisório, e pontos marcados como `Rare Event` ou `Communication Gap` ficam fora. Se categorias se sobrepuserem, vale a exclusão do ranking. Os escores são calculados antes de associar o rótulo para avaliação. Um alarme futuro pode exigir outra coorte; isso precisa estar documentado.

## 2. Uma régua resistente a extremos

Para cada canal \(j\), com exemplos históricos \(x_{ij}\), estime localização \(m_j\) e escala \(s_j\):

\[
m_j=\operatorname{mediana}_i(x_{ij}),\quad
\operatorname{MAD}_j=\operatorname{mediana}_i|x_{ij}-m_j|,\quad
s_j=1{,}4826\operatorname{MAD}_j.
\]

MAD é a mediana das distâncias absolutas **em relação à mediana**. O fator 1,4826 vem da relação entre MAD e desvio padrão sob uma normal: para \(Z\sim N(0,1)\), \(P(|Z|\le a)=0{,}5\) implica \(\Phi(a)=0{,}75\), logo \(a\approx0{,}67449\). Tomamos seu inverso. Usar esse fator não supõe normalidade para detectar; também não faz de 3 um limiar calibrado. Se MAD for zero, dividir não é válido. O laboratório sinaliza o problema em vez de criar um divisor arbitrário.

**Conta manual:** com `[9, 10, 10, 11, 100]`, a média é 28; a mediana é 10 e as distâncias, em ordem, são `[0, 0, 1, 1, 90]`. MAD vale 1. O 100 muda muito a média, mas a mediana e o MAD resumem o miolo. Um valor 13 ficaria a \((13-10)/1{,}4826\approx2{,}02\) unidades da escala robusta. A robustez é em relação a uma proporção de contaminação; não protege de todo desvio de regime ou de uma referência histórica inadequada.

A medida por instante é:

\[
z_j=(x_j-m_j)/s_j,\qquad S_{\mathrm{rob}}(x)=\max_j |z_j|.
\]

`max` responde “qual dos canais se afastou mais de sua faixa histórica?”. Preserva um canal muito distante mesmo se os outros dois estiverem próximos do centro. Porém, duas observações moderadas isoladamente podem formar uma combinação improvável. O máximo não modela covariância, nem muda a expectativa conforme o contexto.

## 3. Leia o código com o eixo certo

Abra `C:\renewable-forecast-lab\satellite-anomaly-monitor\src\satmon\detectores_m10_2.py`. Em `ajustar`, `x_ajuste` tem shape `[n, 3]`. `np.median(..., axis=0)` remove a dimensão de linhas e retorna três valores. Em `pontuar`, `x - self.mediana` subtrai a mediana correspondente de cada coluna. A escala é congelada. `np.abs(z).max(axis=1)` deixa **um escore por instante**, shape `[n]`.

Se computarmos mediana e MAD usando também 2008–2010, uma mudança de regime pode inflar o MAD e baixar o escore no período em que deveria ser diagnosticada. É o equivalente, para detecção, a ajustar o scaler do seu modelo de previsão sobre a validação. Se os valores não estiverem disponíveis, o pipeline não os imputa para fabricar um escore; a linha sem escore fica registrada.

**Antes da Aula 2:** para `z_A = [2, 2]` e `z_B = [1, −1]`, calcule o máximo absoluto e marque qual suspeitaria primeiro. Agora acrescente a informação: “quando a operação é habitual, os dois canais sobem e descem juntos”. Qual ponto você passaria a investigar? A próxima aula transforma exatamente essa mudança de julgamento em álgebra.

**Cheque de entendimento:** você deve conseguir reconstruir o MAD de cinco valores, distinguir o eixo de ajuste do eixo do escore e explicar por que um máximo grande não é uma probabilidade. A atividade autoral usa a mesma matriz padronizada na aula seguinte.

Fonte dos dados: [ESA Anomaly Dataset v2, Mission1](https://zenodo.org/records/15237121), European Space Agency; licença [CC BY 3.0 IGO](https://creativecommons.org/licenses/by/3.0/igo/). `protocolo.json` identifica os membros originais e os CSVs derivados. Este é um recorte adaptado para a aula, sem endosso da ESA e sem equivalência ao benchmark oficial.
