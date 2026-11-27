"""A comparação muda uma única coisa: acrescentar um exemplo formatado."""
import json

from opevid.estruturado_m11_2 import esperado_da_fonte

VARIANTES = ("zero_shot", "um_exemplo")
SYSTEM = "You are a JSON formatter for a monitoring report. Reply with exactly one JSON object and nothing else."
RULES = '''Read the record. Copy id, cutoff, s1, s2 verbatim (decimal strings or null). Set code, reason and refs by these rules in order:
unusable: INSUFFICIENT, unavailable, ["usable"].
s1 < cutoff: BELOW, below, ["s1","cutoff"].
k=2, s1 >= cutoff, s2=null: ISOLATED, no_pair, ["k","s1","s2","cutoff"].
k=2, s1 >= cutoff, s2 < cutoff: ISOLATED, pair_below, ["k","s1","s2","cutoff"].
k=1, s1 >= cutoff: ELIGIBLE, single_met, ["k","s1","cutoff"].
k=2, s2 >= cutoff: ELIGIBLE, pair_met, ["k","s2","cutoff"].
Required JSON keys: id, code, cutoff, s1, s2, reason, refs. JSON only.'''
EXAMPLE = {"id":"demo_prompt","cutoff":"0.62","s1":"0.53","s2":"0.49","usable":True,"k":2}


def compact(record):
    return json.dumps(record, ensure_ascii=True, separators=(",", ":"))


def mensagens(variante, registro):
    if variante not in VARIANTES:
        raise ValueError(f"Prompt desconhecido: {variante}")
    user = RULES+"\n"
    if variante=="um_exemplo":
        user+=f"Example record: {compact(EXAMPLE)}\nExample response: {compact(esperado_da_fonte(EXAMPLE))}\n"
    return [{"role":"system","content":SYSTEM},
            {"role":"user","content":user+"Record: "+compact(registro)+"\nJSON response:"}]
