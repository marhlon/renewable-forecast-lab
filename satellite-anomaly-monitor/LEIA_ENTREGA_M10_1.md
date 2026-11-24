# Entrega M10.1 — grade causal de telemetria

A implementação está em `notebooks/m10_sincronizacao_autoral.py`. A execução
Windows `20261118T203614Z_7e13daae` usou esse arquivo e terminou com código zero.
Passaram cinco grupos de conferência, dez testes adicionais e a comparação
integral com a referência. A auditoria por searchsorted confere os arquivos
salvos sem importar o sincronizador.

Leia a [explicação passo a passo](docs/Explicacao_M10_1_Passo_a_Passo.md) e
o [parecer com as quatro respostas](reports/parecer_m10_1.md).
O [relatório HTML](reports/m10_1/20261118T203614Z_7e13daae/relatorio.html),
o [resultado.json](reports/m10_1/20261118T203614Z_7e13daae/resultado.json)
e o [perfil dos canais](reports/m10_1/20261118T203614Z_7e13daae/perfil_canais.csv)
identificam a execução completa.

## Repetir no ambiente existente

Na raiz `C:\renewable-forecast-lab`, com `renewable-forecast` ativo:

```powershell
python satellite-anomaly-monitor/scripts/executar_m10_1.py --autoria satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py --verificar
python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_sincronizacao_autoral.py -v
python satellite-anomaly-monitor/docs/evidencias_m10_1_local/auditar_resultados.py
```

Uma nova execução anual usa o mesmo comando sem `--verificar`. Ela cria outra
pasta e atualiza `latest_run.json`. A auditoria desta entrega fixa o run acima;
o ponteiro precisa corresponder ao run auditado, ou a verificação interrompe.

## O que foi preservado

Foram incluídos os CSVs derivados e os metadados fornecidos, com atribuição
e hashes da fonte, além do código e das saídas da execução concluída.
Não há download, novo ambiente ou treinamento nesses comandos.

O executor recebeu um ajuste de compatibilidade no pandas 3: a grade é
explicitamente UTC/ns, evitando confundir igualdade dos instantes com a
diferença de resolução us/ns. O backup anterior e o log da primeira tentativa
estão em `docs/evidencias_m10_1_local`. As datas e a regra causal permanecem
as mesmas.

`ENTREGA_M10_1_SHA256.json` identifica todos os membros do ZIP, exceto o próprio
manifesto. Os arquivos da execução não foram editados. As contagens de
frescor não comprovam funcionamento normal e nenhum detector foi treinado.
O checksum do arquivo público completo de 3,8 GB continua não verificado,
conforme `data/reference/esa_mission1_2007/source.json`.
