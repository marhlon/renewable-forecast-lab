from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import duckdb
import pyarrow.parquet as pq


EXPECTED_COLUMNS = {
    "din_instante",
    "id_subsistema",
    "nom_subsistema",
    "id_estado",
    "nom_estado",
    "cod_modalidadeoperacao",
    "nom_tipousina",
    "nom_tipocombustivel",
    "nom_usina",
    "id_ons",
    "ceg",
    "val_geracao",
}


def discover_parquet_files(raw_dir: Path) -> list[Path]:
    """Encontra os arquivos Parquet existentes na pasta raw."""

    if not raw_dir.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {raw_dir}")

    files = sorted(raw_dir.glob("*.parquet"))

    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo Parquet encontrado em: {raw_dir}"
        )

    return files


def inspect_schemas(files: Sequence[Path]) -> dict[str, Any]:
    """Compara colunas e tipos físicos dos arquivos Parquet."""

    schemas: dict[str, list[tuple[str, str]]] = {}
    missing_columns: dict[str, list[str]] = {}

    for file in files:
        schema = pq.read_schema(file)

        schemas[file.name] = [
            (field.name, str(field.type))
            for field in schema
        ]

        available_columns = set(schema.names)

        missing_columns[file.name] = sorted(
            EXPECTED_COLUMNS - available_columns
        )

    reference_file = files[0].name
    reference_schema = schemas[reference_file]

    different_from_reference = {
        filename: schema
        for filename, schema in schemas.items()
        if schema != reference_schema
    }

    return {
        "reference_file": reference_file,
        "consistent_between_files": not different_from_reference,
        "different_from_reference": different_from_reference,
        "missing_expected_columns": {
            filename: columns
            for filename, columns in missing_columns.items()
            if columns
        },
        "schemas": schemas,
    }

def classify_schema_drift(
    schema_report: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    """Classifica diferenças físicas como compatíveis ou incompatíveis."""

    reference_file = schema_report["reference_file"]
    reference_schema = dict(
        schema_report["schemas"][reference_file]
    )

    compatible: list[dict[str, str]] = []
    incompatible: list[dict[str, str]] = []

    allowed_target_types = {
        "string",
        "float",
        "double",
    }

    for filename, fields in schema_report["schemas"].items():
        current_schema = dict(fields)

        missing = set(reference_schema) - set(current_schema)
        extra = set(current_schema) - set(reference_schema)

        for column in sorted(missing):
            incompatible.append({
                "file": filename,
                "column": column,
                "change": "missing_column",
            })

        for column in sorted(extra):
            incompatible.append({
                "file": filename,
                "column": column,
                "change": "extra_column",
            })

        common_columns = set(reference_schema) & set(current_schema)

        for column in sorted(common_columns):
            expected_type = reference_schema[column]
            actual_type = current_schema[column]

            if expected_type == actual_type:
                continue

            change = {
                "file": filename,
                "column": column,
                "reference_type": expected_type,
                "actual_type": actual_type,
            }

            target_transition_is_allowed = (
                column == "val_geracao"
                and expected_type in allowed_target_types
                and actual_type in allowed_target_types
            )

            if target_transition_is_allowed:
                compatible.append(change)
            else:
                incompatible.append(change)

    return {
        "compatible": compatible,
        "incompatible": incompatible,
    }

def _fetch_records(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    parameters: list[Any] | None = None,
) -> list[dict[str, Any]]:
    """Converte o resultado de uma consulta DuckDB em dicionários."""

    cursor = connection.execute(query, parameters or [])
    columns = [description[0] for description in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

TARGET_AS_DOUBLE_SQL = """
TRY_CAST(
    NULLIF(
        TRIM(CAST(val_geracao AS VARCHAR)),
        ''
    )
    AS DOUBLE
)
"""


def register_generation_views(
    connection: duckdb.DuckDBPyConnection,
    files: Sequence[Path],
) -> None:
    """Registra as camadas raw e normalizada no DuckDB."""

    paths = [str(file.resolve()) for file in files]

    relation = connection.read_parquet(
        paths,
        union_by_name=True,
        filename=True,
    )

    relation.create_view(
        "raw_generation",
        replace=True,
    )

    connection.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW generation_normalized AS
        SELECT
            * EXCLUDE (val_geracao),
            {TARGET_AS_DOUBLE_SQL} AS val_geracao
        FROM raw_generation
        """
    )

def validate_dataset(
    files: Sequence[Path],
    plant_id: str | None = None,
) -> dict[str, Any]:
    """Valida cobertura, ausências, timestamps e duplicações."""

    if not files:
        raise ValueError("A lista de arquivos está vazia.")

    schema_report = inspect_schemas(files)

    schema_compatibility = classify_schema_drift(
        schema_report
    )

    connection = duckdb.connect()

    try:
        register_generation_views(
            connection=connection,
            files=files,
        )

        target_cast_summary = _fetch_records(
            connection,
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE val_geracao IS NULL
                ) AS valores_nulos_originais,

                COUNT(*) FILTER (
                    WHERE val_geracao IS NOT NULL
                    AND TRIM(CAST(val_geracao AS VARCHAR)) = ''
                ) AS strings_vazias,

                COUNT(*) FILTER (
                    WHERE NULLIF(
                        TRIM(CAST(val_geracao AS VARCHAR)),
                        ''
                    ) IS NOT NULL
                    AND TRY_CAST(val_geracao AS DOUBLE) IS NULL
                ) AS valores_invalidos_nao_vazios
            FROM raw_generation
            """,
        )[0]

        invalid_target_samples = _fetch_records(
            connection,
            """
            SELECT
                CAST(val_geracao AS VARCHAR) AS valor_original,
                filename,
                COUNT(*) AS ocorrencias
            FROM raw_generation
            WHERE NULLIF(
                    TRIM(CAST(val_geracao AS VARCHAR)),
                    ''
                ) IS NOT NULL
            AND TRY_CAST(val_geracao AS DOUBLE) IS NULL
            GROUP BY valor_original, filename
            ORDER BY ocorrencias DESC
            LIMIT 20
            """,
        )

        dataset_summary = _fetch_records(
            connection,
            """
            SELECT
                COUNT(*) AS registros,
                COUNT(DISTINCT filename) AS arquivos,
                MIN(din_instante) AS inicio,
                MAX(din_instante) AS fim,
                COUNT(DISTINCT din_instante) AS instantes,
                SUM(
                    CASE WHEN val_geracao IS NULL THEN 1 ELSE 0 END
                ) AS target_ausente,
                SUM(
                    CASE WHEN id_ons IS NULL THEN 1 ELSE 0 END
                ) AS id_ons_ausente
            FROM generation_normalized
            """,
        )[0]

        file_summary = _fetch_records(
            connection,
            """
            SELECT
                filename,
                COUNT(*) AS registros,
                MIN(din_instante) AS inicio,
                MAX(din_instante) AS fim,
                COUNT(DISTINCT din_instante) AS instantes,
                SUM(
                    CASE WHEN val_geracao IS NULL THEN 1 ELSE 0 END
                ) AS target_ausente,
                SUM(
                    CASE WHEN id_ons IS NULL THEN 1 ELSE 0 END
                ) AS id_ons_ausente,
                SUM(
                    CASE
                        WHEN EXTRACT(MINUTE FROM din_instante) <> 0
                          OR EXTRACT(SECOND FROM din_instante) <> 0
                        THEN 1
                        ELSE 0
                    END
                ) AS timestamps_fora_da_hora
            FROM generation_normalized
            GROUP BY filename
            ORDER BY inicio
            """,
        )

        duplicate_summary = _fetch_records(
            connection,
            """
            WITH duplicate_keys AS (
                SELECT
                    din_instante,
                    id_ons,
                    COUNT(*) AS quantidade
                FROM raw_generation
                WHERE id_ons IS NOT NULL
                GROUP BY din_instante, id_ons
                HAVING COUNT(*) > 1
            )
            SELECT
                COUNT(*) AS grupos_duplicados,
                COALESCE(
                    SUM(quantidade - 1),
                    0
                ) AS registros_excedentes
            FROM duplicate_keys
            """,
        )[0]

        plant_summary = None

        if plant_id is not None:
            plant_summary = _fetch_records(
                connection,
                """
                SELECT
                    MIN(id_ons) AS id_ons,
                    MIN(nom_usina) AS nom_usina,
                    COUNT(*) AS registros,
                    COUNT(DISTINCT din_instante) AS instantes,
                    MIN(din_instante) AS inicio,
                    MAX(din_instante) AS fim,
                    SUM(
                        CASE WHEN val_geracao IS NULL THEN 1 ELSE 0 END
                    ) AS target_ausente,
                    CASE
                        WHEN COUNT(*) = 0 THEN 0
                        ELSE DATE_DIFF(
                            'hour',
                            MIN(din_instante),
                            MAX(din_instante)
                        ) + 1
                    END AS horas_esperadas
                FROM generation_normalized
                WHERE id_ons = ?
                """,
                [plant_id],
            )[0]

            expected = plant_summary["horas_esperadas"]
            observed = plant_summary["instantes"]

            plant_summary["cobertura_percentual"] = (
                round(observed / expected * 100, 4)
                if expected
                else 0.0
            )

        issues: list[dict[str, str]] = []

        if schema_compatibility["compatible"]:
            issues.append({
                "severity": "warning",
                "message": (
                    "Foi encontrado schema drift físico compatível. "
                    "Os valores foram submetidos à validação numérica."
                ),
            })

        if schema_compatibility["incompatible"]:
            issues.append({
                "severity": "error",
                "message": (
                    "Foi encontrado schema drift incompatível."
                ),
            })

        if target_cast_summary["strings_vazias"] > 0:
            issues.append({
                "severity": "warning",
                "message": (
                    "Strings vazias em val_geracao foram "
                    "normalizadas explicitamente para NULL."
                ),
            })

        if target_cast_summary["valores_invalidos_nao_vazios"] > 0:
            issues.append({
                "severity": "error",
                "message": (
                    "Há valores não vazios de val_geracao "
                    "que não podem ser convertidos para DOUBLE."
                ),
            })

        if schema_report["missing_expected_columns"]:
            issues.append({
                "severity": "error",
                "message": "Há colunas obrigatórias ausentes.",
            })

        if duplicate_summary["grupos_duplicados"] > 0:
            issues.append({
                "severity": "error",
                "message": (
                    "Foram encontradas chaves "
                    "din_instante + id_ons duplicadas."
                ),
            })

        off_hour_total = sum(
            row["timestamps_fora_da_hora"]
            for row in file_summary
        )

        if off_hour_total > 0:
            issues.append({
                "severity": "warning",
                "message": "Há timestamps fora de horas inteiras.",
            })

        if plant_summary and plant_summary["registros"] == 0:
            issues.append({
                "severity": "error",
                "message": f"A planta {plant_id} não foi encontrada.",
            })

        if (
            plant_summary
            and plant_summary["registros"] > 0
            and plant_summary["cobertura_percentual"] < 100
        ):
            issues.append({
                "severity": "warning",
                "message": (
                    f"A série {plant_id} não possui "
                    "cobertura horária completa."
                ),
            })

        status = (
            "failed"
            if any(issue["severity"] == "error" for issue in issues)
            else "passed"
        )

        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "file_count": len(files),
            "schema": schema_report,
            "dataset": dataset_summary,
            "files": file_summary,
            "duplicates": duplicate_summary,
            "plant": plant_summary,
            "issues": issues,
            "schema_compatibility": schema_compatibility,
            "target_cast": target_cast_summary,
            "invalid_target_samples": invalid_target_samples,
        }

    finally:
        connection.close()


def save_report(report: dict[str, Any], output_path: Path) -> None:
    """Salva o relatório em JSON."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

def materialize_plant_series(
    files: Sequence[Path],
    plant_id: str,
    output_path: Path,
) -> dict[str, Any]:
    """Cria uma série horária validada e tipada para uma planta."""

    connection = duckdb.connect()

    try:
        register_generation_views(
            connection=connection,
            files=files,
        )

        summary = _fetch_records(
            connection,
            """
            SELECT
                COUNT(*) AS registros,
                COUNT(DISTINCT din_instante) AS instantes,
                MIN(din_instante) AS inicio,
                MAX(din_instante) AS fim,

                COUNT(*) FILTER (
                    WHERE val_geracao IS NULL
                ) AS target_ausente,

                COUNT(*) -
                COUNT(DISTINCT din_instante)
                    AS timestamps_duplicados,

                DATE_DIFF(
                    'hour',
                    MIN(din_instante),
                    MAX(din_instante)
                ) + 1 AS horas_esperadas
            FROM generation_normalized
            WHERE id_ons = ?
            """,
            [plant_id],
        )[0]

        if summary["registros"] == 0:
            raise ValueError(
                f"Planta não encontrada: {plant_id}"
            )

        if summary["target_ausente"] > 0:
            raise ValueError(
                f"A planta possui "
                f"{summary['target_ausente']} targets ausentes."
            )

        if summary["timestamps_duplicados"] > 0:
            raise ValueError(
                "A série possui timestamps duplicados."
            )

        if summary["instantes"] != summary["horas_esperadas"]:
            raise ValueError(
                "A série possui lacunas temporais."
            )

        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE selected_plant AS
            SELECT
                din_instante,
                id_subsistema,
                nom_subsistema,
                id_estado,
                nom_estado,
                cod_modalidadeoperacao,
                nom_tipousina,
                nom_tipocombustivel,
                nom_usina,
                id_ons,
                ceg,
                val_geracao
            FROM generation_normalized
            WHERE id_ons = ?
            ORDER BY din_instante
            """,
            [plant_id],
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        safe_output_path = str(
            output_path.resolve()
        ).replace("'", "''")

        connection.execute(
            f"""
            COPY selected_plant
            TO '{safe_output_path}'
            (
                FORMAT PARQUET,
                COMPRESSION ZSTD
            )
            """
        )

        summary["output"] = str(output_path)
        return summary

    finally:
        connection.close()