"""Explicit project-local tool installation; never rewrite shell profiles."""

import argparse
import hashlib
import io
import json
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".tools"
RELEASES = "https://github.com/Tencent/BrowserSkill/releases/download"


def download(url: str, limit: int = 100_000_000) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "reta-setup"})
    with urllib.request.urlopen(request, timeout=120) as response:
        content = response.read(limit + 1)
    if len(content) > limit:
        raise SystemExit("Tool download exceeds configured bound")
    return content


def npm_install(package: str, executable: str) -> None:
    if shutil.which(executable):
        print(f"Reusing installed {executable}; no automatic upgrade")
        subprocess.run([executable, "--version"], check=True)
        return
    subprocess.run(
        [
            "npm",
            "install",
            "--prefix",
            str(TOOLS / "npm"),
            "--no-audit",
            "--no-fund",
            package,
        ],
        check=True,
    )
    subprocess.run(
        [
            str(TOOLS / "npm/node_modules/.bin" / executable),
            "--version",
        ],
        check=True,
    )


def install_bsk(version: str) -> None:
    if shutil.which("bsk"):
        print("Reusing installed bsk; no automatic upgrade")
        return
    operating_system = {"Linux": "linux", "Darwin": "darwin"}.get(
        platform.system()
    )
    architecture = {"x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(
        platform.machine(),
    )
    if not operating_system or not architecture:
        raise SystemExit("This installer supports Linux/macOS x64/arm64")
    manifest = json.loads(download(f"{RELEASES}/cli-v{version}/version.json"))
    asset = manifest["assets"][f"{operating_system}-{architecture}"]
    expected_prefix = f"{RELEASES}/cli-v{version}/"
    if not asset["url"].startswith(expected_prefix):
        raise SystemExit("BrowserSkill asset origin/version mismatch")
    archive = download(asset["url"])
    if hashlib.sha256(archive).hexdigest() != asset["sha256"]:
        raise SystemExit("BrowserSkill SHA-256 mismatch")
    destination = TOOLS / "bin/bsk"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
        member = bundle.getmember("bsk")
        if not member.isfile():
            raise SystemExit("Expected a regular bsk executable")
        stream = bundle.extractfile(member)
        if stream is None:
            raise SystemExit("Missing bsk executable")
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, delete=False
        ) as staged:
            shutil.copyfileobj(stream, staged)
            staged_path = Path(staged.name)
    staged_path.chmod(0o755)
    staged_path.replace(destination)
    subprocess.run([str(destination), "--version"], check=True)
    print(
        "Install/pair the Chrome or Edge extension separately; "
        "no profile changes made"
    )


def install_harness(name: str) -> None:
    if name == "codex":
        npm_install("@openai/codex", "codex")
    elif name == "claude":
        npm_install("@anthropic-ai/claude-code", "claude")
    elif shutil.which("hermes"):
        subprocess.run(["hermes", "--version"], check=True)
    else:
        script = TOOLS / "hermes-install.sh"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_bytes(
            download("https://hermes-agent.nousresearch.com/install.sh")
        )
        print(f"Running official Hermes installer saved at {script}")
        subprocess.run(
            [
                "bash",
                str(script),
                "--non-interactive",
                "--skip-browser",
                "--skip-computer-use",
                "--dir",
                str(TOOLS / "hermes-agent"),
            ],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", choices=["harness", "rea", "browser-skill"])
    parser.add_argument(
        "--harness", choices=["codex", "claude", "hermes"], default="codex"
    )
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.tool == "harness":
        install_harness(args.harness)
    elif args.tool == "rea":
        npm_install(f"rea-agents@{args.version or '6.7.0'}", "rea")
    else:
        install_bsk(args.version or "0.3.3")


if __name__ == "__main__":
    main()
