"""Contraprovas em novo contexto, sem reproduzir os treinos históricos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "notebooks"))
from bloco3_transferencia_neural import gru_contract, transformer_contract


def test_gru_12_preserves_evaluator_and_temporal_contract():
    result, rows = gru_contract()
    assert result["passed"] and result["batch_sizes"] == [4, 4, 3]
    assert len(rows) == 11 and result["preservation_success_and_failures"]
    assert result["mse"] != result["incorrect_unweighted_batch_mse"]


def test_cross_mask_alone_leaks_through_unmasked_encoder():
    result, rows = transformer_contract()
    assert result["passed"] and result["only_cross_indirect_leak_delta_first_slot"] > 1e-8
    assert result["causal_encoder_and_cross_safe_delta_first_slot"] <= 1e-12
    assert result["unmasked_self_prefix_leak_delta"] > 1e-8
    assert len(rows) == 60
