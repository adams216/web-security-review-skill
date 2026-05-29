#!/usr/bin/env python3
"""Validate the web-security-review skill package and dry-run fixtures."""

from __future__ import annotations

import json
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


def find_powershell() -> str | None:
    for candidate in ("pwsh", "powershell"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        ROOT / "SKILL.md",
        ROOT / "system-prompt.md",
        ROOT / "install.ps1",
        ROOT / "install.sh",
        ROOT / "wsr",
        ROOT / "wsr.ps1",
        ROOT / "action.yml",
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / "agents" / "openai.yaml",
        ROOT / "scripts" / "audit.py",
        ROOT / "scripts" / "audit.ps1",
        ROOT / "scripts" / "audit.sh",
        ROOT / "scripts" / "install-gemini.ps1",
        ROOT / "scripts" / "install-gemini.sh",
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

    with (ROOT / ".claude-plugin" / "marketplace.json").open("r", encoding="utf-8") as handle:
        marketplace = json.load(handle)
    if not marketplace.get("plugins"):
        raise SystemExit(".claude-plugin/marketplace.json must define at least one plugin entry")
    action_text = (ROOT / "action.yml").read_text(encoding="utf-8")
    for required_text in ("using: composite", "scripts/audit.py", "fail-on"):
        if required_text not in action_text:
            raise SystemExit(f"action.yml is missing expected content: {required_text}")

    for python_file in sorted(SCRIPTS_DIR.glob("*.py")):
        pyc_dir = BUILD_DIR / "pyc"
        pyc_dir.mkdir(parents=True, exist_ok=True)
        cfile = pyc_dir / f"{python_file.stem}.pyc"
        py_compile.compile(str(python_file), cfile=str(cfile), doraise=True)

    bash = find_bash()
    if bash:
        run([bash, "-n", str(ROOT / "install.sh")])
        run([bash, "-n", str(ROOT / "wsr")])
        run([bash, "-n", str(SCRIPTS_DIR / "audit.sh")])
        run([bash, "-n", str(SCRIPTS_DIR / "install-gemini.sh")])
        run([bash, "-n", str(SCRIPTS_DIR / "install.sh")])
        run([bash, "-n", str(SCRIPTS_DIR / "run-audit.sh")])
        run([bash, "-n", str(SCRIPTS_DIR / "scan.sh")])
    powershell = find_powershell()

    run([sys.executable, str(SCRIPTS_DIR / "audit.py"), "--help"])
    run([sys.executable, str(SCRIPTS_DIR / "audit.py"), "doctor"])
    run([sys.executable, str(SCRIPTS_DIR / "audit.py"), "setup", "--dest", str(BUILD_DIR / "test-setup-home" / "skills")])
    setup_skill = BUILD_DIR / "test-setup-home" / "skills" / "web-security-review" / "SKILL.md"
    if not setup_skill.exists():
        raise SystemExit(f"Setup shortcut did not create expected skill at: {setup_skill}")
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
    gemini_user_dir = BUILD_DIR / "test-gemini-home" / ".gemini" / "skills"
    run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "audit.py"),
            "install",
            "--host",
            "gemini",
            "--dest",
            str(gemini_user_dir),
        ]
    )
    gemini_user_skill = gemini_user_dir / "web-security-review" / "SKILL.md"
    if not gemini_user_skill.exists():
        raise SystemExit(f"Gemini user install did not create expected skill at: {gemini_user_skill}")
    gemini_workspace_root = BUILD_DIR / "gemini-workspace"
    run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "audit.py"),
            "install",
            "--host",
            "gemini",
            "--scope",
            "workspace",
            "--layout",
            "agents",
            "--workspace-root",
            str(gemini_workspace_root),
        ]
    )
    gemini_workspace_skill = gemini_workspace_root / ".agents" / "skills" / "web-security-review" / "SKILL.md"
    if not gemini_workspace_skill.exists():
        raise SystemExit(f"Gemini workspace install did not create expected skill at: {gemini_workspace_skill}")
    if powershell:
        ps_root_codex_dir = BUILD_DIR / "test-root-codex-ps" / "skills"
        run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(ROOT / "install.ps1"),
                "-Dest",
                str(ps_root_codex_dir),
            ]
        )
        ps_root_codex_skill = ps_root_codex_dir / "web-security-review" / "SKILL.md"
        if not ps_root_codex_skill.exists():
            raise SystemExit(f"Root PowerShell install did not create expected skill at: {ps_root_codex_skill}")
        ps_root_gemini_dir = BUILD_DIR / "test-root-gemini-ps" / ".gemini" / "skills"
        run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(ROOT / "install.ps1"),
                "-Host",
                "gemini",
                "-Dest",
                str(ps_root_gemini_dir),
            ]
        )
        ps_root_gemini_skill = ps_root_gemini_dir / "web-security-review" / "SKILL.md"
        if not ps_root_gemini_skill.exists():
            raise SystemExit(f"Root PowerShell Gemini install did not create expected skill at: {ps_root_gemini_skill}")
        run([powershell, "-NoLogo", "-NoProfile", "-File", str(ROOT / "wsr.ps1"), "doctor"])
        ps_codex_dir = BUILD_DIR / "test-codex-home-ps" / "skills"
        run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(SCRIPTS_DIR / "install.ps1"),
                "--dest",
                str(ps_codex_dir),
            ]
        )
        ps_codex_skill = ps_codex_dir / "web-security-review" / "SKILL.md"
        if not ps_codex_skill.exists():
            raise SystemExit(f"PowerShell Codex install did not create expected skill at: {ps_codex_skill}")
        ps_gemini_dir = BUILD_DIR / "test-gemini-home-ps" / ".gemini" / "skills"
        run(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(SCRIPTS_DIR / "install-gemini.ps1"),
                "--dest",
                str(ps_gemini_dir),
            ]
        )
        ps_gemini_skill = ps_gemini_dir / "web-security-review" / "SKILL.md"
        if not ps_gemini_skill.exists():
            raise SystemExit(f"PowerShell Gemini install did not create expected skill at: {ps_gemini_skill}")
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
            "web-security-review/action.yml",
        )
        forbidden = sorted(entry for entry in entries if entry.startswith(forbidden_prefixes))
        if forbidden:
            raise SystemExit("Built artifact contains repo-only files:\n" + "\n".join(forbidden))

    print("Validation completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
