"""Trusted conversion, bundle export and hash-verified model replay."""

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import polars as pl

from reta import __version__, kernel
from reta.artifacts import (
    bundle_directory,
    publish_manifest,
    verify_bundle,
    write_json,
)
from reta.backtesting import export_backtests
from reta.contracts import AlphaSpec, BacktestConfig, RetaError
from reta.data import load_bars
from reta.reporting import backtest_markdown


def positions_for(bars: pl.DataFrame, spec: AlphaSpec) -> pl.DataFrame:
    frame = kernel.generate_positions(
        bars.lazy(),
        spec=spec.model_dump(),
    ).collect()
    if frame.height == 0:
        raise RetaError("insufficient_evidence", "No decisions after warmup")
    if frame["effective_ts"].null_count():
        raise RetaError(
            "missing_schedule", "Delayed decision exceeds schedule"
        )
    key = ["instrument_id", "decision_ts"]
    if frame.unique(subset=key).height != frame.height:
        raise RetaError("ambiguous_decisions", "Duplicate decision instants")
    return frame


def export_model(
    directory: Path,
    spec: AlphaSpec,
    positions: pl.DataFrame,
) -> None:
    write_json(directory / "spec.json", spec.model_dump())
    positions.write_parquet(directory / "positions.parquet")
    shutil.copyfile(Path(kernel.__file__), directory / "model.py")
    (directory / "requirements.txt").write_text("polars==2.0.0\n")


def convert(
    spec_path: Path,
    bars_path: Path,
    output_root: Path,
    *,
    backtest: BacktestConfig | None = None,
) -> dict[str, Any]:
    spec = AlphaSpec.model_validate_json(spec_path.read_text())
    bars = load_bars(bars_path)
    positions = positions_for(bars, spec)
    run_name = f"converted-{uuid.uuid4().hex[:12]}"
    with bundle_directory(output_root, run_name) as (directory, destination):
        export_model(directory, spec, positions)
        bars.write_parquet(directory / "bars.parquet")
        financial = export_backtests(
            directory,
            bars,
            positions,
            backtest or BacktestConfig(),
        )
        write_json(
            directory / "evaluation.json",
            {
                "status": "conversion_only",
                "held_out_validation": False,
                "limitation": "Explicit rules converted; not blind recovery",
                "backtest": financial,
            },
        )
        (directory / "report.md").write_text(
            "# Explicit alpha conversion\n\n"
            "Trusted typed rules converted to Python/Polars.\n"
            "No claim of held-out recovery or profitability.\n\n"
            + backtest_markdown(financial),
        )
        publish_manifest(
            directory,
            {
                "schema_version": "1",
                "reta_version": __version__,
                "kind": "conversion",
                "outcome": "converted",
            },
        )
    return {
        "outcome": "converted",
        "bundle": str(destination),
        "backtest": financial,
    }


def replay(
    bundle: Path,
    bars_path: Path,
    destination: Path,
) -> dict[str, Any]:
    manifest = verify_bundle(bundle)
    if manifest["outcome"] not in {"succeeded", "converted", "backtested"}:
        raise RetaError("no_promoted_model", "This bundle contains no model")
    spec = AlphaSpec.model_validate_json((bundle / "spec.json").read_text())
    bars = load_bars(bars_path)
    positions = positions_for(bars, spec)
    if destination.exists():
        raise RetaError("output_exists", "Positions already exist")
    destination.parent.mkdir(parents=True, exist_ok=True)
    positions.write_parquet(destination)
    destination.chmod(0o600)
    return {"path": str(destination), "positions": positions.height}


def backtest_bundle(
    bundle: Path,
    output_root: Path,
    *,
    bars_path: Path | None = None,
    config_path: Path | None = None,
) -> dict[str, Any]:
    manifest = verify_bundle(bundle)
    if manifest["outcome"] not in {"succeeded", "converted", "backtested"}:
        raise RetaError("no_promoted_model", "This bundle contains no model")
    spec = AlphaSpec.model_validate_json((bundle / "spec.json").read_text())
    config = _backtest_config(bundle, manifest, config_path)
    bars = load_bars(
        bars_path if bars_path is not None else bundle / "bars.parquet"
    )
    positions = positions_for(bars, spec)
    name = f"backtested-{uuid.uuid4().hex[:12]}"
    with bundle_directory(output_root, name) as (directory, destination):
        export_model(directory, spec, positions)
        bars.write_parquet(directory / "bars.parquet")
        financial = export_backtests(directory, bars, positions, config)
        write_json(
            directory / "evaluation.json",
            {
                "status": "backtest_only",
                "held_out_validation": False,
                "source_model_outcome": manifest["outcome"],
                "backtest": financial,
            },
        )
        (directory / "report.md").write_text(
            "# Exported alpha backtest\n\n"
            "Trusted spec replay; no new behavioral validation "
            "or promotion.\n\n" + backtest_markdown(financial),
        )
        publish_manifest(
            directory,
            {
                "schema_version": "1",
                "reta_version": __version__,
                "kind": "backtest",
                "outcome": "backtested",
            },
        )
    return {
        "outcome": "backtested",
        "bundle": str(destination),
        "backtest": financial,
    }


def _backtest_config(
    bundle: Path,
    manifest: dict[str, Any],
    config_path: Path | None,
) -> BacktestConfig:
    if config_path is not None:
        return BacktestConfig.model_validate_json(config_path.read_text())
    if "backtest.json" in manifest["files"]:
        saved = json.loads((bundle / "backtest.json").read_text())
        return BacktestConfig.model_validate(saved["config"])
    return BacktestConfig()
