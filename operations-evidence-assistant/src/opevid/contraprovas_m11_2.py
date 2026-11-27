"""Casos controlados: positivos, omissões e erros factuais com JSON válido."""
from copy import deepcopy
import json

from opevid.estruturado_m11_2 import (avaliar_resposta, conferir_fidelidade, esperado_da_fonte)


def exercitar(func=conferir_fidelidade):
    src = {"id":"caso_s2", "k":2, "usable":True, "cutoff":"0.70", "s1":"0.80", "s2":"0.62"}
    missing = dict(src, id="caso_sem_dado", usable=False, s1=None, s2=None)
    exact_cut = dict(src, id="caso_igualdade", s2="0.700")
    close = dict(src, id="caso_precisao", cutoff="0.70", s2="0.6999999999999999999")
    ready = esperado_da_fonte(src)
    valid = json.dumps(ready)
    fixtures = [
        ("fiel",src,valid,"fiel",[]),
        ("decimais_equivalentes",src,json.dumps(dict(ready,cutoff="0.700",s1="0.800")),"fiel",[]),
        ("json_incompleto",src,valid[:-1],"json_invalido",["json_malformado"]),
        ("cerca_markdown",src,"```json\n"+valid+"\n```","json_invalido",["json_malformado"]),
        ("chave_duplicada",src,valid[:-1]+',"cutoff":"0.10"}',"json_invalido",["chave_duplicada"]),
        ("numero_nao_json",src,valid.replace('"0.70"', "NaN"),"json_invalido",["constante_nao_json"]),
        ("omissao_s2",src,json.dumps({k:v for k,v in ready.items() if k!="s2"}),"esquema_invalido",["missing:s2"]),
        ("coercao_float",src,json.dumps(dict(ready,s1=.8)),"esquema_invalido",["string_type:s1"]),
        ("campo_extra",src,json.dumps(dict(ready,observacao="not verified")),"esquema_invalido",["extra_forbidden:observacao"]),
        ("pico_virou_corte",src,json.dumps(dict(ready,cutoff="0.80")),"divergencia",["numero_divergente:cutoff"]),
        ("causa_nao_sustentada",src,json.dumps(dict(ready,reason="physical_cause")),"divergencia",["razao_sem_suporte"]),
        ("citacao_incompleta_e_extra",src,json.dumps(dict(ready,refs=["k","s1","cutoff","usable","s1"])),"divergencia",
         ["citacao_ausente:s2","citacao_extra:usable","citacao_repetida"]),
        ("sem_dado_nao_e_zero",missing,json.dumps(dict(esperado_da_fonte(missing),s1="0")),"divergencia",["numero_divergente:s1"]),
        ("id_e_classe_trocados",src,json.dumps(dict(ready,id="outro_caso",code="ELIGIBLE")),"divergencia",
         ["id_divergente","classe_divergente"]),
        ("igualdade_inclusiva",exact_cut,json.dumps(esperado_da_fonte(exact_cut)),"fiel",[]),
        ("arredondamento_muda_regra",close,json.dumps(dict(esperado_da_fonte(close),s2="0.70",code="ELIGIBLE")),"divergencia",
         ["classe_divergente","numero_divergente:s2"]),
    ]
    assert esperado_da_fonte(exact_cut)["code"] == "ELIGIBLE"
    assert esperado_da_fonte(close)["code"] == "ISOLATED"
    rows = []
    for name, evidence, raw, want, expected_errors in fixtures:
        got = avaliar_resposta(raw, evidence, func)
        if (got["etapa"],got["erros"]) != (want,sorted(expected_errors)):
            raise ValueError(f"Contraprova {name}: esperado {want}, {expected_errors}; obtido {got!r}.")
        final = got["publicado"]
        if final["origem"] != ("conferido" if want=="fiel" else "fallback"):
            raise ValueError(f"Rota final incorreta na contraprova {name}.")
        out = {k:final[k] for k in esperado_da_fonte(evidence)}
        if out != esperado_da_fonte(evidence):
            raise ValueError(f"Números ou classe da fonte não preservados em {name}.")
        rows.append({"teste":name, "fonte": deepcopy(evidence), "texto":raw, **got})
    return rows
