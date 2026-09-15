from __future__ import annotations

import argparse
from pathlib import Path

from renewable_forecast.backtest import (
    run_backtest,
    save_backtest_results,
)
from renewable_forecast.data_contract import (
    discover_parquet_files,
    materialize_plant_series,
    save_report,
    validate_dataset,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="renewcast",
        description="Ferramentas para previsão de geração renovável.",
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    validate_parser = commands.add_parser(
        "validate",
        help="Valida os arquivos brutos de geração.",
    )

    validate_parser.add_argument(
        "--raw-dir",
        type=Path,
        required=True,
        help="Diretório que contém os arquivos Parquet.",
    )

    validate_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Arquivo JSON que receberá o relatório.",
    )

    validate_parser.add_argument(
        "--plant-id",
        default="CJU_BA5EIGT",
        help="Identificador ONS cuja cobertura será verificada.",
    )

    prepare_parser = commands.add_parser(
        "prepare",
        help="Materializa uma série horária normalizada.",
    )

    prepare_parser.add_argument(
        "--raw-dir",
        type=Path,
        required=True,
    )

    prepare_parser.add_argument(
        "--plant-id",
        required=True,
    )

    prepare_parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    backtest_parser = commands.add_parser(
        "backtest",
        help="Executa o backtesting temporal.",
    )

    backtest_parser.add_argument(
        "--input",
        type=Path,
        required=True,
    )

    backtest_parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )

    return parser


def run_preparation(args: argparse.Namespace) -> int:
    files = discover_parquet_files(args.raw_dir)

    summary = materialize_plant_series(
        files=files,
        plant_id=args.plant_id,
        output_path=args.output,
    )

    print("Série materializada com sucesso.")
    print(f"Registros: {summary['registros']:,}")
    print(f"Início: {summary['inicio']}")
    print(f"Fim: {summary['fim']}")
    print(f"Target ausente: {summary['target_ausente']}")
    print(f"Arquivo: {summary['output']}")

    return 0


def run_validation(args: argparse.Namespace) -> int:
    files = discover_parquet_files(args.raw_dir)

    print(f"Arquivos encontrados: {len(files)}")
    print("Executando validações...")

    report = validate_dataset(
        files=files,
        plant_id=args.plant_id,
    )

    save_report(
        report=report,
        output_path=args.output,
    )

    print(f"Status: {report['status']}")
    print(f"Registros: {report['dataset']['registros']:,}")
    print(
        "Duplicidades:",
        report["duplicates"]["grupos_duplicados"],
    )

    if report["plant"] is not None:
        print(
            f"Cobertura de {args.plant_id}: "
            f"{report['plant']['cobertura_percentual']:.2f}%"
        )

    print(f"Relatório salvo em: {args.output}")

    if report["issues"]:
        print("\nProblemas encontrados:")

        for issue in report["issues"]:
            print(
                f"- [{issue['severity'].upper()}] "
                f"{issue['message']}"
            )

    return 0 if report["status"] == "passed" else 1


def run_backtest_command(
    args: argparse.Namespace,
) -> int:
    predictions, fold_metrics, summary = run_backtest(
        args.input
    )

    save_backtest_results(
        predictions=predictions,
        fold_metrics=fold_metrics,
        summary=summary,
        output_dir=args.output_dir,
    )

    print("\nResumo do backtesting:\n")
    print(summary.round(3).to_string(index=False))
    print(f"\nResultados salvos em: {args.output_dir}")

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "validate":
        exit_code = run_validation(args)

    elif args.command == "prepare":
        exit_code = run_preparation(args)

    elif args.command == "backtest":
        exit_code = run_backtest_command(args)

    else:
        parser.error("Comando desconhecido.")
        return

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
