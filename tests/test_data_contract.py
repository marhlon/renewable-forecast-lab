from pathlib import Path

import pandas as pd

from renewable_forecast.data_contract import (
    discover_parquet_files,
    validate_dataset,
    classify_schema_drift,
)


def test_discover_parquet_files(tmp_path: Path) -> None:
    first_file = tmp_path / "2026_01.parquet"
    second_file = tmp_path / "2026_02.parquet"

    pd.DataFrame({"value": [1]}).to_parquet(first_file)
    pd.DataFrame({"value": [2]}).to_parquet(second_file)

    files = discover_parquet_files(tmp_path)

    assert files == [first_file, second_file]


def test_detects_duplicate_key(tmp_path: Path) -> None:
    file = tmp_path / "generation.parquet"

    data = pd.DataFrame({
        "din_instante": pd.to_datetime([
            "2026-01-01 00:00:00",
            "2026-01-01 00:00:00",
        ]),
        "id_ons": ["PLANT_A", "PLANT_A"],
        "val_geracao": [10.0, 10.0],
    })

    data.to_parquet(file, index=False)

    report = validate_dataset([file])

    assert report["duplicates"]["grupos_duplicados"] == 1
    assert report["duplicates"]["registros_excedentes"] == 1
    assert report["status"] == "failed"


def test_detects_timestamp_outside_full_hour(
    tmp_path: Path,
) -> None:
    file = tmp_path / "generation.parquet"

    data = pd.DataFrame({
        "din_instante": pd.to_datetime([
            "2026-01-01 00:30:00",
        ]),
        "id_ons": ["PLANT_A"],
        "val_geracao": [10.0],
    })

    data.to_parquet(file, index=False)

    report = validate_dataset([file])

    assert report["files"][0]["timestamps_fora_da_hora"] == 1


def test_accepts_string_to_double_for_target() -> None:
    schema_report = {
        "reference_file": "old.parquet",
        "schemas": {
            "old.parquet": [
                ("din_instante", "timestamp[ns]"),
                ("val_geracao", "string"),
            ],
            "new.parquet": [
                ("din_instante", "timestamp[ns]"),
                ("val_geracao", "double"),
            ],
        },
    }

    result = classify_schema_drift(schema_report)

    assert len(result["compatible"]) == 1
    assert result["compatible"][0]["column"] == "val_geracao"
    assert result["incompatible"] == []

def test_treats_blank_target_as_missing(
    tmp_path: Path,
) -> None:
    file = tmp_path / "generation.parquet"

    data = pd.DataFrame({
        "din_instante": pd.to_datetime([
            "2026-01-01 00:00:00",
        ]),
        "id_ons": ["PLANT_A"],
        "val_geracao": [""],
    })

    data.to_parquet(file, index=False)

    report = validate_dataset([file])

    assert report["target_cast"]["strings_vazias"] == 1
    assert (
        report["target_cast"]
        ["valores_invalidos_nao_vazios"]
        == 0
    )
    assert report["files"][0]["target_ausente"] == 1