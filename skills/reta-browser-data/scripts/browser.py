"""Run reviewed browser login or collection without exposing credentials."""

import os
import subprocess
import sys
from pathlib import Path

root = Path(os.environ.get("RETA_PROJECT_ROOT", Path(__file__).parents[3]))
if not (root / "pyproject.toml").is_file():
    raise SystemExit("Set RETA_PROJECT_ROOT to the RETA checkout")
command = ["uv", "run", "--directory", str(root), "reta", "browser"]
raise SystemExit(subprocess.call([*command, *sys.argv[1:]], cwd=root))
