"""Trusted conversion, bundle export and hash-verified model replay."""

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
from reta.contracts import AlphaSpec, RetaError
from reta.data import load_bars


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
) -> dict[str, Any]:
    spec = AlphaSpec.model_validate_json(spec_path.read_text())
    bars = load_bars(bars_path)
    positions = positions_for(bars, spec)
    run_name = f"converted-{uuid.uuid4().hex[:12]}"
    with bundle_directory(output_root, run_name) as (directory, destination):
        export_model(directory, spec, positions)
        bars.write_parquet(directory / "bars.parquet")
        write_json(
            directory / "evaluation.json",
            {
                "status": "conversion_only",
                "held_out_validation": False,
                "limitation": "Explicit rules converted; not blind recovery",
            },
        )
        (directory / "report.md").write_text(
            "# Explicit alpha conversion\n\n"
            "Trusted typed rules converted to Python/Polars.\n"
            "No claim of held-out recovery or profitability.\n",
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
    return {"outcome": "converted", "bundle": str(destination)}


def replay(
    bundle: Path,
    bars_path: Path,
    destination: Path,
) -> dict[str, Any]:
    manifest = verify_bundle(bundle)
    if manifest["outcome"] not in {"succeeded", "converted"}:
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
