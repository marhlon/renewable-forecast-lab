from __future__ import annotations

import io

import torch
from torch import nn

from renewable_forecast.transformer_blocks import (
    DecoderBlock, EncoderBlock, MultiHeadAttention, TransformerDidatico,
    causal_mask, sinusoidal_positions,
)


def copiar_atencao(source, target):
    """Transfere as quatro projeções explícitas para a MHA do PyTorch."""
    with torch.no_grad():
        target.in_proj_weight.copy_(torch.cat([
            source.q_proj.weight, source.k_proj.weight, source.v_proj.weight,
        ]))
        target.in_proj_bias.copy_(torch.cat([
            source.q_proj.bias, source.k_proj.bias, source.v_proj.bias,
        ]))
        target.out_proj.load_state_dict(source.out_proj.state_dict())


def copiar_encoder(source, target):
    copiar_atencao(source.attention, target.self_attn)
    for name in ("linear1", "linear2", "norm1", "norm2"):
        getattr(target, name).load_state_dict(getattr(source, name).state_dict())


def copiar_decoder(source, target):
    copiar_atencao(source.self_attention, target.self_attn)
    copiar_atencao(source.cross_attention, target.multihead_attn)
    for name in ("linear1", "linear2", "norm1", "norm2", "norm3"):
        getattr(target, name).load_state_dict(getattr(source, name).state_dict())


def conferir():
    """Usa pesos iguais e float64; tolerância absoluta 1e-12, relativa zero."""
    checks, differences = [], {}
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(2092)
        dtype = torch.float64
        x = torch.randn(2, 6, 8, dtype=dtype)
        memory = torch.randn(2, 9, 8, dtype=dtype)
        allowed = torch.ones(6, 9, dtype=torch.bool)
        allowed[:, -2:] = False
        triangular = causal_mask(6)

        def compare(name, actual, expected):
            torch.testing.assert_close(actual, expected, rtol=0, atol=1e-12)
            differences[name] = float((actual - expected).abs().max().item())

        attention = MultiHeadAttention(8, 2, 0.1).double().eval()
        reference_attention = nn.MultiheadAttention(8, 2, dropout=0.1, batch_first=True).double().eval()
        copiar_atencao(attention, reference_attention)
        with torch.no_grad():
            out, weights = attention(x, memory, memory, allowed)
            ref_out, ref_weights = reference_attention(
                x, memory, memory, attn_mask=~allowed, average_attn_weights=False,
            )
        compare("mha_output", out, ref_out)
        compare("mha_weights", weights, ref_weights)
        compare("mha_row_sums", weights.sum(-1), torch.ones(2, 2, 6, dtype=dtype))
        assert torch.all(weights[:, :, ~allowed] == 0)
        checks.append("multiplas_cabecas_retangulares_e_mascara_vs_pytorch")

        encoder = EncoderBlock(8, 2, 16, 0.1).double().eval()
        reference_encoder = nn.TransformerEncoderLayer(
            8, 2, 16, 0.1, activation="relu", batch_first=True, norm_first=False,
        ).double().eval()
        copiar_encoder(encoder, reference_encoder)
        with torch.no_grad():
            compare("encoder_free", encoder(x), reference_encoder(x))
            compare("encoder_causal", encoder(x, triangular), reference_encoder(x, src_mask=~triangular))
            _, trace = encoder(x, return_trace=True)
            compare("residual_attention", trace["residual_attention"], x + trace["attention"])
            compare("residual_ffn", trace["residual_ffn"], trace["after_attention"] + trace["feed_forward"])
            compare("norm1", trace["after_attention"], encoder.norm1(trace["residual_attention"]))
            compare("norm2", trace["output"], encoder.norm2(trace["residual_ffn"]))
        checks += ["encoder_post_norm_vs_pytorch", "residuais_e_normalizacao_por_token"]

        decoder = DecoderBlock(8, 2, 16, 0.1).double().eval()
        reference_decoder = nn.TransformerDecoderLayer(
            8, 2, 16, 0.1, activation="relu", batch_first=True, norm_first=False,
        ).double().eval()
        copiar_decoder(decoder, reference_decoder)
        with torch.no_grad():
            actual = decoder(x, memory, memory_mask=allowed)
            expected = reference_decoder(x, memory, tgt_mask=~triangular, memory_mask=~allowed)
            compare("decoder", actual, expected)
            changed_memory = memory.clone()
            changed_memory[:, -2:] += 25
            compare("cross_mask", actual, decoder(x, changed_memory, memory_mask=allowed))
        checks += ["decoder_self_cross_ffn_vs_pytorch", "cross_attention_respeita_mascara_de_memoria"]

        config = dict(input_size=1, d_model=16, n_heads=4, d_ff=32, n_layers=2, dropout=0.1)
        model = TransformerDidatico(**config).double().eval()
        source = torch.randn(2, 24, 1, dtype=dtype)
        queries = torch.randn(2, 6, 1, dtype=dtype)
        with torch.no_grad():
            result = model(source, queries)
            ref_memory = result["source_embedding"]
            for layer in model.encoders:
                ref_layer = nn.TransformerEncoderLayer(
                    16, 4, 32, 0.1, activation="relu", batch_first=True, norm_first=False,
                ).double().eval()
                copiar_encoder(layer, ref_layer)
                ref_memory = ref_layer(ref_memory)
            ref_decoder = result["query_embedding"]
            for layer in model.decoders:
                ref_layer = nn.TransformerDecoderLayer(
                    16, 4, 32, 0.1, activation="relu", batch_first=True, norm_first=False,
                ).double().eval()
                copiar_decoder(layer, ref_layer)
                ref_decoder = ref_layer(ref_decoder, ref_memory, tgt_mask=~causal_mask(6))
            compare("stack_memory", result["memory"], ref_memory)
            compare("stack_decoder", result["decoder"], ref_decoder)
        assert sum(p.numel() for p in model.parameters()) == 11200
        checks.append("duas_camadas_encoder_decoder_vs_pilhas_pytorch")

        with torch.no_grad():
            changed = queries.clone()
            changed[:, -2:] += 7
            before, _ = model.decode(queries, result["memory"])
            after, _ = model.decode(changed, result["memory"])
            compare("decoder_prefix", before[:, :-2], after[:, :-2])
            future_delta = float((before[:, -2:] - after[:, -2:]).abs().max())
            assert future_delta > 1e-8
            permutation = torch.tensor([1, 0])
            permuted = model(source[permutation], queries[permutation])
            compare("batch_permutation", permuted["decoder"], result["decoder"][permutation])
        checks += ["decoder_duas_camadas_preserva_prefixo_com_memoria_fixa", "batch_nao_mistura_origens"]

        with torch.no_grad():
            perm = torch.tensor([5, 1, 3, 0, 2, 4])
            free = encoder(x)
            compare("without_position", encoder(x[:, perm]), free[:, perm])
            pos = sinusoidal_positions(6, 8, dtype=dtype)[None]
            with_pos = encoder(x + pos)
            fixed = encoder(x[:, perm] + pos)
            fixed_position_delta = float((fixed - with_pos[:, perm]).abs().max())
            assert fixed_position_delta > 1e-8
            first_free = encoder(x)
            first_causal = encoder(x, triangular)
            compare("last_query_one_layer", first_free[:, -1], first_causal[:, -1])
            second = EncoderBlock(8, 2, 16, 0.1).double().eval()
            last_two_layers_delta = float((second(first_free)[:, -1] - second(first_causal, triangular)[:, -1]).abs().max())
            assert last_two_layers_delta > 1e-8
        checks += ["posicao_fixa_altera_equivariancia_do_encoder", "ultima_consulta_pode_mudar_apos_empilhamento"]

        for bad_mask in (torch.zeros(6, 9, dtype=torch.bool), torch.ones(6, 9), torch.ones(2, 6, 9, dtype=torch.bool)):
            try:
                attention(x, memory, memory, bad_mask)
            except ValueError:
                pass
            else:
                raise AssertionError("Máscara inválida foi aceita.")
        try:
            MultiHeadAttention(10, 4)
        except ValueError:
            pass
        else:
            raise AssertionError("Divisão incompatível em cabeças foi aceita.")
        odd = sinusoidal_positions(3, 7, dtype=dtype)
        assert odd.shape == (3, 7) and torch.isfinite(odd).all()
        checks.append("contratos_de_cabecas_mascaras_e_posicao_impar")

        snapshot = {key: value.clone() for key, value in model.state_dict().items()}
        probe = torch.randn(2, 6, 16, dtype=dtype)
        (model(source, queries)["decoder"] * probe).sum().backward()
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
        gradient_paths = {
            "source_projection": float(model.source_projection.weight.grad.abs().max()),
            "encoder_value_projection": float(model.encoders[0].attention.v_proj.weight.grad.abs().max()),
            "decoder_cross_value_projection": float(model.decoders[0].cross_attention.v_proj.weight.grad.abs().max()),
        }
        assert all(value > 0 for value in gradient_paths.values())
        for key, value in model.state_dict().items():
            torch.testing.assert_close(value, snapshot[key], rtol=0, atol=0)
        checks.append("gradientes_atravessam_blocos_sem_atualizar_parametros")

        buffer = io.BytesIO()
        torch.save({"config": config, "state_dict": model.state_dict()}, buffer)
        buffer.seek(0)
        restored = torch.load(buffer, map_location="cpu", weights_only=True)
        recovered = TransformerDidatico(**restored["config"]).double().eval()
        recovered.load_state_dict(restored["state_dict"])
        with torch.no_grad():
            compare("reload", recovered(source, queries)["decoder"], result["decoder"])
        checks.append("recarregamento_configuracao_e_pesos")

    return {
        "passed": True, "checks": checks, "checks_count": len(checks),
        "tolerance": 1e-12, "max_difference": max(differences.values()),
        "differences": differences, "gradient_paths": gradient_paths,
        "future_decoder_delta": future_delta,
        "fixed_position_delta": fixed_position_delta,
        "last_query_two_layers_delta": last_two_layers_delta,
        "parameter_count": 11200, "optimizer_steps": 0,
        "training_performed": False,
    }
