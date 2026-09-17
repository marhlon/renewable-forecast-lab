from __future__ import annotations

import argparse
import json
from pathlib import Path

from renewable_forecast.backtest import (
    run_backtest,
    save_backtest_results,
)
from renewable_forecast.calibration import run_calibration
from renewable_forecast.data_contract import (
    discover_parquet_files,
    materialize_plant_series,
    save_report,
    validate_dataset,
)
from renewable_forecast.evaluation import run_evaluation
from renewable_forecast.governance import run_governance
from renewable_forecast.modeling import (
    predict_next,
    train_final_model,
    tune_model,
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
    prepare_parser.add_argument("--raw-dir", type=Path, required=True)
    prepare_parser.add_argument("--plant-id", required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)

    backtest_parser = commands.add_parser(
        "backtest",
        help="Executa o backtesting temporal.",
    )
    backtest_parser.add_argument("--input", type=Path, required=True)
    backtest_parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )

    evaluate_parser = commands.add_parser(
        "evaluate",
        help="Avalia estabilidade temporal dos modelos.",
    )
    evaluate_parser.add_argument(
        "--backtest-dir",
        type=Path,
        required=True,
    )
    evaluate_parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )

    tune_parser = commands.add_parser(
        "tune",
        help="Seleciona hiperparâmetros temporalmente.",
    )
    tune_parser.add_argument("--input", type=Path, required=True)
    tune_parser.add_argument("--experiment", default="renewable-h1")
    tune_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/tuning"),
    )

    train_parser = commands.add_parser(
        "train",
        help="Treina e persiste o modelo final.",
    )
    train_parser.add_argument("--input", type=Path, required=True)
    train_parser.add_argument(
        "--params",
        type=Path,
        default=Path("reports/tuning/best_params.json"),
    )
    train_parser.add_argument("--output", type=Path, required=True)
    train_parser.add_argument("--experiment", default="renewable-h1")

    predict_parser = commands.add_parser(
        "predict",
        help="Prevê a próxima hora.",
    )
    predict_parser.add_argument("--model", type=Path, required=True)
    predict_parser.add_argument("--input", type=Path, required=True)

    calibrate_parser = commands.add_parser(
        "calibrate",
        help="Calibra o viés usando somente folds anteriores.",
    )
    calibrate_parser.add_argument(
        "--backtest-dir",
        type=Path,
        required=True,
    )
    calibrate_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/calibration"),
    )
    calibrate_parser.add_argument(
        "--candidate",
        default="hist_gradient_boosting",
    )
    calibrate_parser.add_argument(
        "--baseline",
        default="persistence_1h",
    )
    calibrate_parser.add_argument(
        "--history-window",
        type=int,
        default=672,
        help="Máximo de resíduos passados usados (672 = 28 dias).",
    )
    calibrate_parser.add_argument(
        "--min-history",
        type=int,
        default=168,
        help="Histórico mínimo antes de aplicar correção.",
    )
    calibrate_parser.add_argument(
        "--ramp-threshold",
        type=float,
        default=30.0,
    )

    govern_parser = commands.add_parser(
        "govern",
        help="Aplica os gates champion-challenger.",
    )
    govern_parser.add_argument(
        "--calibration-dir",
        type=Path,
        required=True,
    )
    govern_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/governance"),
    )
    govern_parser.add_argument(
        "--candidate",
        default="hist_gradient_boosting_calibrated_mean",
    )
    govern_parser.add_argument(
        "--baseline",
        default="persistence_1h",
    )
    govern_parser.add_argument(
        "--mae-tolerance",
        type=float,
        default=0.02,
    )
    govern_parser.add_argument(
        "--max-absolute-bias",
        type=float,
        default=2.0,
    )
    govern_parser.add_argument(
        "--min-rmse-improvement-pct",
        type=float,
        default=5.0,
    )
    govern_parser.add_argument(
        "--min-ramp-improvement-pct",
        type=float,
        default=20.0,
    )
    govern_parser.add_argument(
        "--min-win-rate-pct",
        type=float,
        default=60.0,
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

    report = validate_dataset(files=files, plant_id=args.plant_id)
    save_report(report=report, output_path=args.output)

    print(f"Status: {report['status']}")
    print(f"Registros: {report['dataset']['registros']:,}")
    print("Duplicidades:", report["duplicates"]["grupos_duplicados"])

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


def run_backtest_command(args: argparse.Namespace) -> int:
    predictions, fold_metrics, summary = run_backtest(args.input)
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


def run_evaluation_command(args: argparse.Namespace) -> int:
    stability, _ = run_evaluation(
        backtest_dir=args.backtest_dir,
        output_dir=args.output_dir,
    )

    print("\nEstabilidade contra a persistência:\n")
    print(stability.round(3).to_string(index=False))
    print(f"\nMétricas mensais salvas em: {args.output_dir}")
    return 0


def run_tune_command(args: argparse.Namespace) -> int:
    result = tune_model(
        input_path=args.input,
        output_dir=args.output_dir,
        experiment=args.experiment,
    )

    print("\nMelhores parâmetros:\n")
    print(json.dumps(result["best_params"], indent=2))
    print("\nValidação temporal:\n")
    print(json.dumps(result["metrics"], indent=2))
    print(f"\nMLflow run: {result['run_id']}")
    return 0


def run_train_command(args: argparse.Namespace) -> int:
    metadata = train_final_model(
        input_path=args.input,
        params_path=args.params,
        output_dir=args.output,
        experiment=args.experiment,
    )

    print("\nModelo treinado e persistido:\n")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    return 0


def run_predict_command(args: argparse.Namespace) -> int:
    prediction = predict_next(
        model_dir=args.model,
        input_path=args.input,
    )

    print("\nPrevisão:\n")
    print(json.dumps(prediction, indent=2, ensure_ascii=False))
    return 0


def run_calibrate_command(args: argparse.Namespace) -> int:
    summary, _, metadata = run_calibration(
        backtest_dir=args.backtest_dir,
        output_dir=args.output_dir,
        candidate_model=args.candidate,
        baseline_model=args.baseline,
        history_window=args.history_window,
        min_history=args.min_history,
        ramp_threshold=args.ramp_threshold,
    )

    print("\nResultado da calibração:\n")
    print(summary.round(3).to_string(index=False))
    print(f"\nEscopo temporal: {metadata['calibration_scope']}")
    print(f"Resultados salvos em: {args.output_dir}")
    return 0


def run_govern_command(args: argparse.Namespace) -> int:
    report = run_governance(
        calibration_dir=args.calibration_dir,
        output_dir=args.output_dir,
        candidate_model=args.candidate,
        baseline_model=args.baseline,
        mae_tolerance=args.mae_tolerance,
        max_absolute_bias=args.max_absolute_bias,
        min_rmse_improvement_pct=args.min_rmse_improvement_pct,
        min_ramp_improvement_pct=args.min_ramp_improvement_pct,
        min_win_rate_pct=args.min_win_rate_pct,
    )

    print("\nDecisão de governança:\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nRelatório salvo em: {args.output_dir}")
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "validate": run_validation,
        "prepare": run_preparation,
        "backtest": run_backtest_command,
        "evaluate": run_evaluation_command,
        "tune": run_tune_command,
        "train": run_train_command,
        "predict": run_predict_command,
        "calibrate": run_calibrate_command,
        "govern": run_govern_command,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.error("Comando desconhecido.")
        return

    raise SystemExit(handler(args))


if __name__ == "__main__":
    main()
