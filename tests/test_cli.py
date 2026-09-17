from __future__ import annotations
from pathlib import Path

from renewable_forecast.cli import build_parser


def test_cli_accepts_calibrate_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "calibrate",
            "--backtest-dir",
            "reports/backtest",
        ]
    )

    assert args.command == "calibrate"
    assert args.backtest_dir == Path("reports/backtest")


def test_cli_accepts_govern_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "govern",
            "--calibration-dir",
            "reports/calibration",
        ]
    )

    assert args.command == "govern"
    assert args.calibration_dir == Path("reports/calibration")