#!/usr/bin/env python3
"""Validate the web-security-review skill package and dry-run fixtures."""

from __future__ import annotations

import pathlib
import py_compile
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
BUILD_DIR = ROOT / "build"


def run(command: list[str], cwd: pathlib.Path | None = None) -> None:
    subprocess.run(command, cwd=str(cwd or ROOT), check=True)


def find_bash() -> str | None:
    for candidate in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe", "bash"):
        resolved = shutil.which(candidate) if ":" not in candidate else candidate
        if resolved and pathlib.Path(resolved).exists():
            return resolved
    return None


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        ROOT / "SKILL.md",
        ROOT / "system-prompt.md",
        ROOT / "agents" / "openai.yaml",
        ROOT / "scripts" / "audit.py",
        ROOT / "scripts" / "audit.ps1",
        ROOT / "scripts" / "audit.sh",
        ROOT / "scripts" / "install.ps1",
        ROOT / "scripts" / "install.sh",
        ROOT / "scripts" / "run_audit.py",
        ROOT / "scripts" / "scan.ps1",
        ROOT / "scripts" / "scan.sh",
        ROOT / "scripts" / "collect_evidence.py",
        ROOT / "references" / "core-methodology.md",
        ROOT / "references" / "ai-agent-security.md",
        ROOT / "references" / "governance-gates.md",
        ROOT / "references" / "reporting-standard.md",
        ROOT / "references" / "vulnerability-catalog.md",
        ROOT / "prompt-templates" / "ai-agent.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required files:\n" + "\n".join(missing))

    for python_file in sorted(SCRIPTS_DIR.glob("*.py")):
        pyc_dir = BUILD_DIR / "pyc"
        pyc_dir.mkdir(parents=True, exist_ok=True)
        cfile = pyc_dir / f"{python_file.stem}.pyc"
        py_compile.compile(str(python_file), cfile=str(cfile), doraise=True)

    bash = find_bash()
    if bash:
        run([bash, "-n", str(SCRIPTS_DIR / "audit.sh")])
        run([bash, "-n", str(SCRIPTS_DIR / "install.sh")])
        run([bash, "-n", str(SCRIPTS_DIR / "run-audit.sh")])
        run([bash, "-n", str(SCRIPTS_DIR / "scan.sh")])

    run([sys.executable, str(SCRIPTS_DIR / "audit.py"), "--help"])
    run([sys.executable, str(SCRIPTS_DIR / "audit.py"), "doctor"])
    run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "audit.py"),
            "install",
            "--dest",
            str(BUILD_DIR / "test-codex-home" / "skills"),
        ]
    )
    installed_skill = BUILD_DIR / "test-codex-home" / "skills" / "web-security-review" / "SKILL.md"
    if not installed_skill.exists():
        raise SystemExit(f"Install shortcut did not create expected skill at: {installed_skill}")
    run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "audit.py"),
            "scan",
            str(ROOT / "tests" / "fixtures" / "node-express-vulnerable"),
            "--dry-run",
            "--output",
            str(BUILD_DIR / "easy-scan-bundle.json"),
        ]
    )

    run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "run_audit.py"),
            "--model",
            "openai",
            "--dir",
            str(ROOT / "tests" / "fixtures" / "node-express-vulnerable"),
            "--type",
            "full",
            "--dry-run",
            "--output",
            str(BUILD_DIR / "full-bundle.json"),
        ]
    )
    run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "run_audit.py"),
            "--model",
            "openai",
            "--dir",
            str(ROOT / "tests" / "fixtures" / "node-express-vulnerable"),
            "--type",
            "single-file",
            "--file",
            "src/server.js",
            "--dry-run",
            "--output",
            str(BUILD_DIR / "single-file-bundle.json"),
        ]
    )
    run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "run_audit.py"),
            "--model",
            "openai",
            "--dir",
            str(ROOT / "tests" / "fixtures" / "ci-insecure"),
            "--type",
            "ci-check",
            "--dry-run",
            "--output",
            str(BUILD_DIR / "ci-bundle.json"),
        ]
    )
    run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "run_audit.py"),
            "--model",
            "openai",
            "--dir",
            str(ROOT / "tests" / "fixtures" / "ai-agent-insecure"),
            "--type",
            "ai-agent",
            "--governance-profile",
            "strict",
            "--dry-run",
            "--output",
            str(BUILD_DIR / "ai-agent-bundle.json"),
        ]
    )

    artifact_path = BUILD_DIR / "web-security-review.skill"
    run([sys.executable, str(SCRIPTS_DIR / "build_skill.py"), "--output", str(artifact_path)])

    with zipfile.ZipFile(artifact_path, "r") as archive:
        entries = set(archive.namelist())
        required_entries = {
            "web-security-review/SKILL.md",
            "web-security-review/system-prompt.md",
            "web-security-review/agents/openai.yaml",
            "web-security-review/scripts/audit.py",
            "web-security-review/scripts/audit.sh",
            "web-security-review/scripts/audit.ps1",
            "web-security-review/scripts/run_audit.py",
            "web-security-review/scripts/collect_evidence.py",
            "web-security-review/references/ai-agent-security.md",
            "web-security-review/references/governance-gates.md",
            "web-security-review/prompt-templates/ai-agent.md",
        }
        missing_entries = sorted(required_entries - entries)
        if missing_entries:
            raise SystemExit("Built artifact is missing entries:\n" + "\n".join(missing_entries))

        forbidden_prefixes = (
            "web-security-review/tests/",
            "web-security-review/.github/",
            "web-security-review/build/",
        )
        forbidden = sorted(entry for entry in entries if entry.startswith(forbidden_prefixes))
        if forbidden:
            raise SystemExit("Built artifact contains repo-only files:\n" + "\n".join(forbidden))

    print("Validation completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
