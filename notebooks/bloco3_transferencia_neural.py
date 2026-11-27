"""Bloco 3: reanálise histórica e contratos neurais novos, sem treino.

Execute --protocol antes de --run. As soluções são fornecidas pelo Codex;
não há resposta independente do usuário nem certificação de autonomia.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from renewable_forecast.neural_gru import avaliar_lotes
from renewable_forecast.transformer_blocks import EncoderBlock, DecoderBlock, causal_mask

OUT = ROOT / "reports/fechamento_m00_m09/bloco3_engenharia"
HISTORICAL = ROOT / "reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f"
IDS = ("M08-02", "M08-03", "M09-02")
CODE = [Path(__file__), ROOT / "tests/test_bloco3_transferencia_neural.py",
        ROOT / "src/renewable_forecast/neural_gru.py",
        ROOT / "src/renewable_forecast/transformer_blocks.py"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def hashes(paths):
    return {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in paths}


def versions():
    return {"python": platform.python_version(), "torch": torch.__version__,
            "numpy": np.__version__, "pandas": pd.__version__, "platform": platform.platform()}


def protocol():
    common = {"schema": "bloco3-neural-protocol-v1", "registered_at_utc": now(),
              "authorship": "Solução e revisão técnica fornecidas pelo Codex; sem resposta independente do usuário",
              "training_performed": False, "optimizer_steps": 0,
              "new_untouched_holdout": False, "operational_evidence": False,
              "code_sha256": hashes(CODE), "versions_at_registration": versions()}
    plans = {
        "M08-02": {
            "hypothesis": "A ordenação GRU/HGB pode discordar entre MAE e RMSE; o sinal do viés não decide a dispersão.",
            "scope": "Reanálise das mesmas 168 origens de desenvolvimento já examinadas, sem refazer treino ou selecionar semente",
            "inputs_sha256": hashes([HISTORICAL / f for f in ["predictions.csv", "protocol.json", "resultado.json"]]),
            "criteria": ["Recalcular MAE/RMSE/viés com prediction-target e conferir erros salvos",
                         "Parear exatamente as mesmas 168 origens para HGB e GRU 17/29/41",
                         "Reportar cada semente, dispersão e todas as perdas por origem",
                         "Explicar escolha sob prioridade MAE e custo de cauda; indicar evidência futura que mudaria a decisão"],
            "decision_rule": "Sob prioridade MAE em CPU e ausência de benefício consistente nas três sementes, manter HGB como referência de desenvolvimento. Uma preferência RMSE é condicional ao custo e requer confirmação futura congelada.",
            "availability": "Histórico com atraso assumido 2h, h24; timestamps/fuso físicos e versões históricas não comprovados por este recálculo",
        },
        "M08-03": {
            "hypothesis": "GRU nova de janela12 e hidden8 mantém independência das janelas e avaliação por exemplo em lotes4/4/3",
            "scope": "11 exemplos determinísticos sintéticos, seed8303, pesos aleatórios float64; qualidade preditiva não avaliada",
            "predicted_shapes_before_execution": {"input": [11, 12, 1], "batches": [4, 4, 3],
                "recurrent_output": ["B", 12, 8], "hidden": [1, "B", 8], "last_hidden": ["B", 8],
                "prediction": ["B", 1], "gru_weight_ih": [24, 1], "gru_weight_hh": [24, 8], "head_weight": [1, 8]},
            "predicted_parameters": 273,
            "criteria": ["Comparar avaliador com soma quadrática global/11, demonstrando erro da média por lote",
                         "Preservar pesos, gradientes preexistentes, estado, flags mistas e RNG no sucesso e nas falhas",
                         "Repetição/permutação não carregam estado; mudar futuro indisponível não muda janela",
                         "Rejeitar shape, alvo inválido, não finito e loader vazio; conferir três portas em 12 passos"],
            "temporal_contract": "Série sintética horária: origem t14, atraso4h, janela t-1..t10; alvo h1 t15 está separado. Só available_at<=origem entra na janela.",
            "absolute_tolerance": 1e-12,
        },
        "M09-02": {
            "hypothesis": "Máscara só na cross-attention vaza fonte indisponível via encoder livre; encoder causal mais cross por disponibilidade elimina o caminho",
            "scope": "Contexto12, cinco slots sintéticos, E12/H3, dff24, duas camadas, seed9023 float64, pesos aleatórios sem cabeça de previsão",
            "predicted_shapes_before_execution": {"source": [2, 12, 12], "queries": [2, 5, 12],
                "encoder_QKV_heads": [2, 3, 12, 4], "decoder_self_QKV_heads": [2, 3, 5, 4],
                "cross_Q_heads": [2, 3, 5, 4], "cross_KV_heads": [2, 3, 12, 4],
                "encoder_probabilities": [2, 3, 12, 12], "cross_probabilities": [2, 3, 5, 12],
                "decoder_self_probabilities": [2, 3, 5, 5], "memory": [2, 12, 12],
                "output": [2, 5, 12], "encoder_FFN_hidden": [2, 12, 24], "decoder_FFN_hidden": [2, 5, 24]},
            "criteria": ["Explicitar Q/K/V e verificar projeções, softmax/escalonamento e eixos",
                         "Demonstrar soma residual, LayerNorm por token e FFN posição a posição",
                         "Perturbar fonte indisponível: seguro invariante e controle só-cross muda",
                         "Perturbar slots futuros: prefixo causal invariante; self livre muda",
                         "Histórico todo disponível na emissão permite encoder livre para previsão única; prefixos históricos exigem regras próprias"],
            "availability_contract": {"source_event_indices": list(range(12)), "delay_steps_assumed": 4,
                "synthetic_query_origin_indices": [7, 8, 9, 10, 11], "last_available_source_indices": [3, 4, 5, 6, 7],
                "slot_meaning": "Consultas sintéticas em origens sucessivas para testar disponibilidade; não equivalem a cinco horizontes horários de previsão"},
            "absolute_tolerance": 1e-12, "positive_control_minimum_change": 1e-8,
        },
    }
    for item, plan in plans.items():
        path = OUT / item / "protocolo.json"
        if path.exists():
            raise FileExistsError(f"Protocolo já existe; preservar antes de revisar: {path}")
        write_json(path, dict(common, item=item, **plan))
    return {"registered": list(plans), "code_sha256": common["code_sha256"]}


class GRU12(nn.Module):
    """Adaptação nova: [B,12,1] -> [B,12,8] -> [1,B,8] -> [B,1]."""
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(1, 8, batch_first=True)
        self.dropout = nn.Dropout(.25)
        self.head = nn.Linear(8, 1)

    def forward(self, x):
        if x.ndim != 3 or len(x) == 0 or x.shape[1:] != (12, 1):
            raise ValueError("GRU12 exige [B,12,1] não vazio")
        _, hidden = self.gru(x)  # zero novo, sem hidden guardado entre lotes
        return self.head(self.dropout(hidden[-1]))


def capture(model):
    return {"weights": {k: v.clone() for k, v in model.state_dict().items()},
            "grads": [None if p.grad is None else p.grad.clone() for p in model.parameters()],
            "modes": [m.training for m in model.modules()], "rng": torch.get_rng_state().clone()}


def assert_preserved(model, before):
    for k, value in model.state_dict().items():
        torch.testing.assert_close(value, before["weights"][k], rtol=0, atol=0)
    for p, grad in zip(model.parameters(), before["grads"]):
        if grad is None:
            assert p.grad is None
        else:
            torch.testing.assert_close(p.grad, grad, rtol=0, atol=0)
    assert [m.training for m in model.modules()] == before["modes"]
    assert torch.equal(torch.get_rng_state(), before["rng"])


def gru_contract():
    from m08_gru_autoral import passo_gru
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(8303)
        model = GRU12().double()
        # Configuração mista deliberada: a avaliação deve restaurar cada módulo.
        model.train()
        model.gru.eval()
        model.head.eval()
        for i, p in enumerate(model.parameters()):
            if i % 2 == 0:
                p.grad = torch.full_like(p, (i + 1) / 10)
        x = torch.arange(132, dtype=torch.float64).reshape(11, 12, 1) / 30 - 2
        y = torch.linspace(-2, 5, 11, dtype=torch.float64)[:, None]
        batches = [(x[i:i+4], y[i:i+4]) for i in range(0, 11, 4)]
        before = capture(model)
        result = avaliar_lotes(model, batches)
        assert_preserved(model, before)
        model.eval()
        with torch.no_grad():
            recurrent, hidden = model.gru(x)
            predictions = model(x)
            repeated = model(x)
            permutation = torch.arange(10, -1, -1)
            permuted = model(x[permutation])
            torch.testing.assert_close(repeated, predictions, rtol=0, atol=0)
            torch.testing.assert_close(permuted, predictions[permutation], rtol=0, atol=1e-12)
        manual = float(((predictions-y).square()).sum() / 11)
        wrong = float(torch.stack([(predictions[i:i+4]-y[i:i+4]).square().mean() for i in range(0, 11, 4)]).mean())
        assert abs(result["mse"] - manual) < 1e-12 and abs(wrong-manual) > 1e-8
        assert recurrent.shape == (11, 12, 8) and hidden.shape == (1, 11, 8)
        assert sum(p.numel() for p in model.parameters()) == 273
        # Célula NumPy independente, mesma ordem r,z,n e fórmula PyTorch.
        params = [getattr(model.gru, name).detach().numpy() for name in [
            "weight_ih_l0", "weight_hh_l0", "bias_ih_l0", "bias_hh_l0"]]
        state = np.zeros((11, 8))
        max_gate_difference = 0.
        for step in range(12):
            gates = passo_gru(x[:, step].numpy(), state, *params)
            state = gates["h"]
            max_gate_difference = max(max_gate_difference, float(np.max(np.abs(state-recurrent[:, step].numpy()))))
        assert max_gate_difference < 1e-12
        model.train()
        model.gru.eval()
        model.head.eval()
        failure_names = []
        malformed = y[4:8, 0]
        nonfinite = y[4:8].clone()
        nonfinite[0, 0] = float("nan")
        cases = {"alvo_shape_apos_lote_valido": [batches[0], (x[4:8], malformed)],
                 "nan_apos_lote_valido": [batches[0], (x[4:8], nonfinite)],
                 "loader_vazio": [], "janela_incorreta": [(x[:, :11], y)]}
        for name, loader in cases.items():
            before = capture(model)
            try:
                avaliar_lotes(model, loader)
            except ValueError:
                failure_names.append(name)
            else:
                raise AssertionError(f"Falha esperada não ocorreu: {name}")
            assert_preserved(model, before)
        # Contrato t14, delay4: só t<=10 é disponível; contexto começa t-1.
        times = torch.arange(-1, 20)
        series = torch.sin(times.double()/3)
        available = times+4 <= 14
        window = series[available][-12:].reshape(1, 12, 1)
        changed = series.clone()
        changed[~available] += 100
        changed_window = changed[available][-12:].reshape(1, 12, 1)
        assert times[available][-12:].tolist() == list(range(-1, 11))
        model.eval()
        with torch.no_grad():
            original = model(window)
            future_changed = model(changed_window)
            torch.testing.assert_close(original, future_changed, rtol=0, atol=0)
            # Controle: incluir t11..14 indevidamente altera a saída.
            leaked = changed[times <= 14][-12:].reshape(1, 12, 1)
            leaked_delta = float((model(leaked)-original).abs().max())
        assert leaked_delta > 1e-8
        rows = pd.DataFrame({"example": range(11), "batch": [0]*4+[1]*4+[2]*3,
                             "target": y[:, 0].numpy(), "prediction": predictions[:, 0].numpy()})
        rows["squared_error"] = (rows.prediction-rows.target)**2
    return {"passed": True, "rows": 11, "batch_sizes": [4, 4, 3], "mse": result["mse"],
            "mse_global_reference": manual, "incorrect_unweighted_batch_mse": wrong,
            "parameter_count": 273, "observed_shapes": {"input": [11, 12, 1], "recurrent": list(recurrent.shape),
                "hidden": list(hidden.shape), "prediction": list(predictions.shape)},
            "max_numpy_recurrence_difference": max_gate_difference,
            "preservation_success_and_failures": True, "rejected_cases": failure_names,
            "zero_reset_repeat_and_batch_permutation": True, "future_mutation_safe_delta": 0,
            "unavailable_input_positive_control_delta": leaked_delta,
            "checks_count": 12, "random_weights_only_contract_no_quality_claim": True}, rows


def transformer_contract():
    differences, observed, trace_rows = {}, {}, []
    def same(name, a, b):
        delta = float((a-b).abs().max())
        assert delta <= 1e-12, (name, delta)
        differences[name] = delta
    with torch.random.fork_rng(devices=[]), torch.no_grad():
        torch.manual_seed(9023)
        encoders = nn.ModuleList([EncoderBlock(12, 3, 24, 0).double().eval() for _ in range(2)])
        decoders = nn.ModuleList([DecoderBlock(12, 3, 24, 0).double().eval() for _ in range(2)])
        source = torch.randn(2, 12, 12, dtype=torch.float64)
        queries = torch.randn(2, 5, 12, dtype=torch.float64)
        # source[j] disponível em j+4; slots r têm origem7+r.
        origins = torch.arange(7, 12)
        cross = torch.arange(12)[None, :]+4 <= origins[:, None]
        causal_source, causal_query = causal_mask(12), causal_mask(5)
        def run(src, query, *, causal_encoder=True, causal_decoder=True):
            memory, et = src, []
            for layer in encoders:
                memory, trace = layer(memory, causal_source if causal_encoder else None, return_trace=True)
                et.append(trace)
            state, dt = query, []
            for layer in decoders:
                state, trace = layer(state, memory, causal_query if causal_decoder else torch.ones(5, 5, dtype=torch.bool), cross, True)
                dt.append(trace)
            return state, et, dt
        base, et, dt = run(source, queries)
        for group, traces, layers in [("encoder", et, encoders), ("decoder", dt, decoders)]:
            for idx, (trace, layer) in enumerate(zip(traces, layers)):
                for key, value in trace.items():
                    observed[f"{group}{idx}.{key}"] = list(value.shape)
                if group == "encoder":
                    same(f"encoder{idx}.residual_attention", trace["residual_attention"], trace["input"]+trace["attention"])
                    same(f"encoder{idx}.norm1", trace["after_attention"], layer.norm1(trace["residual_attention"]))
                    same(f"encoder{idx}.residual_ffn", trace["residual_ffn"], trace["after_attention"]+trace["feed_forward"])
                    same(f"encoder{idx}.norm2", trace["output"], layer.norm2(trace["residual_ffn"]))
                    same(f"encoder{idx}.ffn", trace["feed_forward"], layer.linear2(torch.relu(layer.linear1(trace["after_attention"]))))
                else:
                    same(f"decoder{idx}.residual_self", trace["residual_self"], trace["input"]+trace["self_attention"])
                    same(f"decoder{idx}.norm1", trace["after_self"], layer.norm1(trace["residual_self"]))
                    same(f"decoder{idx}.residual_cross", trace["residual_cross"], trace["after_self"]+trace["cross_attention"])
                    same(f"decoder{idx}.norm2", trace["after_cross"], layer.norm2(trace["residual_cross"]))
                    same(f"decoder{idx}.residual_ffn", trace["residual_ffn"], trace["after_cross"]+trace["feed_forward"])
                    same(f"decoder{idx}.norm3", trace["output"], layer.norm3(trace["residual_ffn"]))
                    same(f"decoder{idx}.ffn", trace["feed_forward"], layer.linear2(torch.relu(layer.linear1(trace["after_cross"]))))
        # Reconstrução independente da atenção cruzada: Q=estado decoder;
        # K,V=memória encoder. Softmax normaliza as chaves, eixo final.
        att = decoders[0].cross_attention
        q = att.q_proj(dt[0]["after_self"]).reshape(2, 5, 3, 4).transpose(1, 2)
        k = att.k_proj(et[-1]["output"]).reshape(2, 12, 3, 4).transpose(1, 2)
        v = att.v_proj(et[-1]["output"]).reshape(2, 12, 3, 4).transpose(1, 2)
        scores = (q @ k.transpose(-1, -2))/math.sqrt(4)
        weights = scores.masked_fill(~cross[None, None], -torch.inf).softmax(-1)
        joined = (weights @ v).transpose(1, 2).reshape(2, 5, 12)
        same("cross_weights_reconstruction", weights, dt[0]["cross_attention_weights"])
        same("cross_output_reconstruction", att.out_proj(joined), dt[0]["cross_attention"])
        same("cross_row_sums", weights.sum(-1), torch.ones(2, 3, 5))
        assert (weights[:, :, ~cross] == 0).all()
        # Origem7: só fonte0..3 pode influenciar a primeira consulta.
        changed_source = source.clone()
        changed_source[:, 4:] += torch.linspace(-9, 13, 12, dtype=torch.float64)
        safe_changed, _, _ = run(changed_source, queries)
        same("safe_source_unavailable_first_slot", base[:, :1], safe_changed[:, :1])
        unsafe, _, _ = run(source, queries, causal_encoder=False)
        unsafe_changed, _, _ = run(changed_source, queries, causal_encoder=False)
        indirect_delta = float((unsafe[:, :1]-unsafe_changed[:, :1]).abs().max())
        assert indirect_delta > 1e-8
        # Origem9: só fonte0..5; primeiros três slots não veem fonte6..11.
        changed_later = source.clone()
        changed_later[:, 6:] *= -7
        later_output, _, _ = run(changed_later, queries)
        same("safe_source_first_three_slots", base[:, :3], later_output[:, :3])
        changed_queries = queries.clone()
        changed_queries[:, 3:] += torch.linspace(-5, 7, 12, dtype=torch.float64)
        future_output, _, _ = run(source, changed_queries)
        same("causal_decoder_prefix", base[:, :3], future_output[:, :3])
        future_delta = float((base[:, 3:]-future_output[:, 3:]).abs().max())
        assert future_delta > 1e-8
        unmasked, _, _ = run(source, queries, causal_decoder=False)
        unmasked_changed, _, _ = run(source, changed_queries, causal_decoder=False)
        prefix_leak_delta = float((unmasked[:, :3]-unmasked_changed[:, :3]).abs().max())
        assert prefix_leak_delta > 1e-8
        # Emissão única com todos os 12 valores já disponíveis: encoder livre
        # é admissível; máscara de prefixo não representa disponibilidade igual.
        all_available, _, _ = run(source, queries, causal_encoder=False)
        assert torch.isfinite(all_available).all()
        for r in range(5):
            for j in range(12):
                trace_rows.append({"slot": r, "origin_index": int(origins[r]), "source_index": j,
                                   "available_at_index": j+4, "allowed_cross": bool(cross[r, j]),
                                   "first_head_weight": float(weights[0, 0, r, j])})
        for group, traces, masks in [("encoder", et, causal_source), ("decoder_self", dt, causal_query)]:
            for idx, trace in enumerate(traces):
                w = trace["attention_weights" if group == "encoder" else "self_attention_weights"]
                assert (w[:, :, ~masks] == 0).all()
                same(f"{group}{idx}.row_sums", w.sum(-1), torch.ones_like(w.sum(-1)))
    return {"passed": True, "shapes": observed, "Q_heads": list(q.shape), "K_heads": list(k.shape), "V_heads": list(v.shape),
            "output_shape": list(base.shape), "max_equation_difference": max(differences.values()), "differences": differences,
            "only_cross_indirect_leak_delta_first_slot": indirect_delta,
            "causal_encoder_and_cross_safe_delta_first_slot": differences["safe_source_unavailable_first_slot"],
            "causal_decoder_prefix_delta": differences["causal_decoder_prefix"],
            "future_slots_positive_control_delta": future_delta, "unmasked_self_prefix_leak_delta": prefix_leak_delta,
            "checks_count": 16, "slots_are_not_forecast_horizons": True,
            "parameter_count": sum(p.numel() for p in encoders.parameters())+sum(p.numel() for p in decoders.parameters())}, pd.DataFrame(trace_rows)


def historical_analysis():
    data = pd.read_csv(HISTORICAL / "predictions.csv")
    groups, comparisons, per_origin = [], [], []
    target_hgb = data.loc[data.method.eq("hgb_24h")].copy().set_index("forecast_origin")
    assert len(target_hgb) == 168 and target_hgb.index.is_unique
    for (method, seed), frame in data.groupby(["method", "seed"], dropna=False):
        error = frame.prediction-frame.target_generation
        np.testing.assert_allclose(error.abs(), frame.absolute_error, rtol=0, atol=1e-10)
        np.testing.assert_allclose(error**2, frame.squared_error, rtol=0, atol=1e-9)
        groups.append({"method": method, "seed": "" if pd.isna(seed) else int(seed), "rows": len(frame),
                       "mae": float(error.abs().mean()), "rmse": float(np.sqrt((error**2).mean())),
                       "bias_prediction_minus_target": float(error.mean()),
                       "centered_rmse": float(np.sqrt(((error-error.mean())**2).mean())),
                       "p90_absolute_error": float(error.abs().quantile(.9)), "max_absolute_error": float(error.abs().max())})
    for seed in (17, 29, 41):
        gru = data.loc[data.method.eq("gru_24h") & data.seed.eq(seed)].set_index("forecast_origin")
        assert len(gru) == 168 and gru.index.is_unique and set(gru.index) == set(target_hgb.index)
        gru = gru.loc[target_hgb.index]
        np.testing.assert_allclose(gru.target_generation, target_hgb.target_generation, rtol=0, atol=0)
        delta_ae = gru.absolute_error-target_hgb.absolute_error
        delta_se = gru.squared_error-target_hgb.squared_error
        ordered = delta_se.sort_values()
        comparisons.append({"seed": seed, "origins": 168, "mae_delta_gru_minus_hgb": float(delta_ae.mean()),
                            "mse_delta_gru_minus_hgb": float(delta_se.mean()),
                            "origins_gru_smaller_absolute_error": int((delta_ae < 0).sum()),
                            "origins_gru_larger_absolute_error": int((delta_ae > 0).sum()),
                            "five_most_favorable_squared_loss_delta_sum": float(ordered.iloc[:5].sum()),
                            "remaining_163_squared_loss_delta_sum": float(ordered.iloc[5:].sum())})
        for origin in target_hgb.index:
            per_origin.append({"forecast_origin": origin, "seed": seed,
                "target": float(gru.loc[origin, "target_generation"]), "gru_prediction": float(gru.loc[origin, "prediction"]),
                "hgb_prediction": float(target_hgb.loc[origin, "prediction"]),
                "gru_absolute_error": float(gru.loc[origin, "absolute_error"]),
                "hgb_absolute_error": float(target_hgb.loc[origin, "absolute_error"]),
                "delta_absolute_error_gru_minus_hgb": float(delta_ae.loc[origin]),
                "delta_squared_error_gru_minus_hgb": float(delta_se.loc[origin])})
    metrics = pd.DataFrame(groups)
    seed_metrics = metrics.loc[metrics.method.eq("gru_24h")]
    spread = {key: {"min": float(seed_metrics[key].min()), "median": float(seed_metrics[key].median()),
                    "max": float(seed_metrics[key].max()), "sd_across_3_seeds_ddof1": float(seed_metrics[key].std(ddof=1))}
              for key in ["mae", "rmse", "bias_prediction_minus_target"]}
    historical = json.loads((HISTORICAL / "resultado.json").read_text(encoding="utf-8"))
    assert digest(HISTORICAL / "predictions.csv") == historical["output_sha256"]["predictions.csv"]
    return {"passed": True, "origins": 168, "gru_seeds": [17, 29, 41], "paired_comparisons": comparisons,
            "gru_seed_spread_not_confidence_interval": spread, "metrics": groups,
            "historical_predictions_hash_matched_receipt": True,
            "new_untouched_holdout": False, "retraining_performed": False,
            "checks_count": 8}, metrics, pd.DataFrame(per_origin)


def run():
    registered = {}
    for item in IDS:
        path = OUT / item / "protocolo.json"
        plan = json.loads(path.read_text(encoding="utf-8"))
        assert plan["code_sha256"] == hashes(CODE), "Código mudou depois do protocolo"
        for rel, expected in plan.get("inputs_sha256", {}).items():
            assert digest(ROOT / rel) == expected, f"Entrada alterada: {rel}"
        registered[item] = plan
    started = now()
    torch.set_num_threads(2)
    results = {}
    historical, metrics, paired = historical_analysis()
    metrics.to_csv(OUT / "M08-02/metricas.csv", index=False)
    paired.to_csv(OUT / "M08-02/perdas_por_origem.csv", index=False)
    gru, gru_rows = gru_contract()
    gru_rows.to_csv(OUT / "M08-03/avaliacao_11_exemplos.csv", index=False)
    transformer, attention_rows = transformer_contract()
    attention_rows.to_csv(OUT / "M09-02/disponibilidade_e_atencao.csv", index=False)
    for item, result in zip(IDS, [historical, gru, transformer]):
        result.update(item=item, started_at_utc=started, completed_at_utc=now(),
                      protocol_sha256=digest(OUT / item / "protocolo.json"),
                      code_sha256=hashes(CODE), versions=versions(), training_performed=False, optimizer_steps=0,
                      authorship="Codex, solução técnica fornecida e executada; sem autonomia pessoal certificada",
                      operational_evidence=False)
        result["output_sha256"] = hashes(sorted((OUT / item).glob("*.csv")))
        write_json(OUT / item / "resultado.json", result)
        results[item] = {"passed": result["passed"], "checks_count": result["checks_count"]}
    write_json(OUT / "execucao_transferencia_neural.json", {"started_at_utc": started, "completed_at_utc": now(),
               "command": "python notebooks/bloco3_transferencia_neural.py --run", "exit_code": 0,
               "results": results, "versions": versions(), "code_sha256": hashes(CODE),
               "output_sha256": hashes([OUT/item/"resultado.json" for item in IDS])})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.protocol == args.run:
        parser.error("Escolha exatamente --protocol ou --run")
    print(json.dumps(protocol() if args.protocol else run(), ensure_ascii=False))
