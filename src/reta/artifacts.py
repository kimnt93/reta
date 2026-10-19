"""Hash-verified, atomically published research bundles."""

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from reta.contracts import RetaError


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: Any) -> None:
    content = json.dumps(value, indent=2, sort_keys=True, allow_nan=False)
    path.write_text(content + "\n", encoding="utf-8")
    path.chmod(0o600)


@contextmanager
def bundle_directory(
    root: Path,
    prefix: str,
) -> Iterator[tuple[Path, Path]]:
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=root))
    staging.chmod(0o700)
    destination = root / prefix
    try:
        yield staging, destination
        if destination.exists():
            raise RetaError("output_exists", "Bundle destination exists")
        os.rename(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def publish_manifest(directory: Path, metadata: dict[str, Any]) -> None:
    files = {}
    for path in sorted(directory.iterdir()):
        if path.is_file():
            path.chmod(0o600)
            files[path.name] = digest(path)
    write_json(directory / "manifest.json", {**metadata, "files": files})


def verify_bundle(directory: Path) -> dict[str, Any]:
    manifest = json.loads((directory / "manifest.json").read_text())
    files = manifest.get("files", {})
    if not files:
        raise RetaError("invalid_bundle", "Bundle has no artifact hashes")
    required = set()
    if manifest.get("kind") in {
        "reverse_engineering",
        "conversion",
        "backtest",
    }:
        required.update({"evaluation.json", "bars.parquet"})
    if manifest.get("outcome") in {"succeeded", "converted", "backtested"}:
        required.update({"model.py", "spec.json", "positions.parquet"})
    if not required.issubset(files):
        raise RetaError(
            "invalid_bundle", "Required artifact hashes are missing"
        )
    for name, expected in files.items():
        path = directory / name
        if Path(name).name != name:
            raise RetaError("invalid_bundle", "Unsafe artifact name")
        if path.is_symlink():
            raise RetaError("invalid_bundle", "Symlink artifact rejected")
        if not path.is_file():
            raise RetaError("invalid_bundle", f"Missing artifact: {name}")
        if digest(path) != expected:
            raise RetaError("integrity_mismatch", f"Changed artifact: {name}")
    return manifest
