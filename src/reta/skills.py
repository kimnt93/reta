"""Install complete skill packs without overwriting harness-owned content."""

import os
import shutil
import tempfile
from pathlib import Path

from reta.artifacts import digest
from reta.contracts import RetaError

HARNESS_ROOTS = {
    "codex": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
    "hermes": Path(".hermes/skills"),
    "omp": Path(".agents/skills"),
}


def _source() -> Path:
    packaged = Path(__file__).parent / "skillpacks"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parents[2] / "skills"


def _same_tree(source: Path, destination: Path) -> bool:
    original = {
        path.relative_to(source)
        for path in source.rglob("*")
        if path.is_file()
    }
    installed = {
        path.relative_to(destination)
        for path in destination.rglob("*")
        if path.is_file()
    }
    if original != installed:
        return False
    for relative in original:
        target = destination / relative
        if target.is_symlink():
            return False
        if digest(source / relative) != digest(target):
            return False
    return True


def install_skills(
    harness: str,
    destination: Path | None = None,
) -> dict[str, object]:
    if destination is None:
        if harness not in HARNESS_ROOTS:
            raise RetaError(
                "unknown_harness", "Supply an explicit destination"
            )
        destination = Path.home() / HARNESS_ROOTS[harness]
    for ancestor in [destination, *destination.parents]:
        if ancestor.is_symlink():
            raise RetaError("unsafe_destination", "Linked skill root rejected")
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    sources = sorted(_source().glob("reta-*"))
    if not sources:
        raise RetaError("missing_skills", "Skill packs not found")
    for source in sources:
        target = destination / source.name
        if target.exists():
            if target.is_symlink() or not _same_tree(source, target):
                raise RetaError(
                    "skill_conflict", f"Preserving existing {target}"
                )
            results.append({"path": str(target), "status": "unchanged"})
            continue
        with tempfile.TemporaryDirectory(dir=destination) as temporary:
            staged = Path(temporary) / source.name
            shutil.copytree(source, staged)
            os.rename(staged, target)
        results.append({"path": str(target), "status": "installed"})
    return {"harness": harness, "skills": results}
