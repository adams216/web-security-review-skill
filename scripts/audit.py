#!/usr/bin/env python3
"""Friendly launcher for the web-security-review skill."""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
HOST_CHOICES = ("codex", "gemini")
GEMINI_LAYOUT_CHOICES = ("native", "agents")

PROVIDER_ALIASES = {
    "anthropic": "claude",
    "claude": "claude",
    "gemini": "gemini",
    "google": "gemini",
    "openai": "openai",
}

SCANNER_TOOLS = [
    "npm",
    "pnpm",
    "yarn",
    "pip-audit",
    "composer",
    "govulncheck",
    "trivy",
]


def normalize_provider(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = PROVIDER_ALIASES.get(value.strip().lower())
    if normalized is None:
        raise SystemExit(f"Unsupported provider '{value}'. Use openai, claude, anthropic, gemini, or google.")
    return normalized


def detect_provider() -> str | None:
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    if os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    return None


def choose_provider(explicit: str | None, dry_run: bool) -> str:
    provider = normalize_provider(explicit) or detect_provider()
    if provider:
        return provider
    if dry_run:
        return "openai"
    raise SystemExit(
        "No provider detected. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY, or pass --provider."
    )


def output_suffix(output_format: str) -> str:
    return {
        "json": ".json",
        "markdown": ".md",
        "sarif": ".sarif",
    }[output_format]


def safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")
    return cleaned or "file"


def default_output(path: pathlib.Path, audit_type: str, output_format: str, target_file: str | None = None) -> pathlib.Path:
    names = {
        "quick": "SECURITY_QUICK",
        "full": "SECURITY_REPORT",
        "ci-check": "SECURITY_CI",
        "ai-agent": "SECURITY_AGENT",
        "single-file": "SECURITY_FILE",
    }
    base_name = names[audit_type]
    if audit_type == "single-file" and target_file:
        base_name = f"{base_name}_{safe_name(pathlib.Path(target_file).stem)}"
    return path / f"{base_name}{output_suffix(output_format)}"


def run_python(script_name: str, extra_args: list[str]) -> int:
    command = [sys.executable, str(SCRIPTS_DIR / script_name), *extra_args]
    completed = subprocess.run(command)
    return completed.returncode


def codex_home() -> pathlib.Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return pathlib.Path(configured).expanduser().resolve()
    return (pathlib.Path.home() / ".codex").resolve()


def gemini_skills_dir(scope: str, layout: str, workspace_root: pathlib.Path | None = None) -> pathlib.Path:
    container = ".agents" if layout == "agents" else ".gemini"
    if scope == "user":
        return (pathlib.Path.home() / container / "skills").resolve()
    root = workspace_root.resolve() if workspace_root else pathlib.Path.cwd().resolve()
    return (root / container / "skills").resolve()


def ensure_within(parent: pathlib.Path, child: pathlib.Path) -> None:
    parent = parent.resolve()
    child = child.resolve()
    try:
        child.relative_to(parent)
    except ValueError as exc:
        raise SystemExit(f"Refusing to operate outside {parent}: {child}") from exc


def safe_extract(archive_path: pathlib.Path, destination: pathlib.Path) -> None:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as archive:
        for member in archive.namelist():
            target = (destination / member).resolve()
            ensure_within(destination, target)
        archive.extractall(destination)


def resolved_format(args: argparse.Namespace) -> str:
    if getattr(args, "sarif", False):
        return "sarif"
    if getattr(args, "json", False):
        return "json"
    return getattr(args, "format", "markdown")


def common_run_parser(parser: argparse.ArgumentParser, *, default_format: str = "markdown") -> None:
    parser.add_argument("path", nargs="?", default=".", help="Path to the repository or audit target. Defaults to the current directory.")
    parser.add_argument("--provider", help="Provider to use: openai, claude, anthropic, gemini, or google. Defaults to auto-detect.")
    parser.add_argument("--model-name", help="Override the provider-specific model name.")
    parser.add_argument("--output", help="Optional output path. Defaults to a mode-specific filename in the target directory.")
    parser.add_argument("--format", choices=["markdown", "json", "sarif"], default=default_format, help="Output format.")
    parser.add_argument("--json", action="store_true", help="Shortcut for --format json.")
    parser.add_argument("--sarif", action="store_true", help="Shortcut for --format sarif.")
    parser.add_argument("--fail-on", choices=["none", "low", "medium", "high", "critical"], default="none", help="Exit non-zero if findings meet or exceed this severity.")
    parser.add_argument("--strict", action="store_true", help="Use strict governance gating.")
    parser.add_argument("--dry-run", action="store_true", help="Build the prompt bundle without calling a model.")
    parser.add_argument("--evidence-out", help="Optional path to write collected evidence JSON.")
    parser.add_argument("--max-files", type=int, default=200, help="Maximum number of files to include in model context.")
    parser.add_argument("--scanner-timeout", type=int, default=20, help="Timeout in seconds per external scanner command.")


def build_run_args(args: argparse.Namespace, audit_type: str, *, target_file: str | None = None) -> list[str]:
    target_path = pathlib.Path(args.path).expanduser().resolve()
    output_format = resolved_format(args)
    output_path = pathlib.Path(args.output).expanduser().resolve() if args.output else default_output(
        target_path,
        audit_type,
        output_format,
        target_file=target_file,
    )
    provider = choose_provider(args.provider, args.dry_run)

    command = [
        "--model",
        provider,
        "--dir",
        str(target_path),
        "--type",
        audit_type,
        "--output",
        str(output_path),
        "--format",
        output_format,
        "--fail-on",
        args.fail_on,
        "--governance-profile",
        "strict" if args.strict else "standard",
        "--max-files",
        str(args.max_files),
        "--scanner-timeout",
        str(args.scanner_timeout),
    ]

    if args.model_name:
        command.extend(["--model-name", args.model_name])
    if args.dry_run:
        command.append("--dry-run")
    if args.evidence_out:
        command.extend(["--evidence-out", args.evidence_out])
    if target_file:
        command.extend(["--file", target_file])
    return command


def cmd_run(args: argparse.Namespace, audit_type: str, *, target_file: str | None = None) -> int:
    return run_python("run_audit.py", build_run_args(args, audit_type, target_file=target_file))


def cmd_quick(args: argparse.Namespace) -> int:
    return cmd_run(args, "quick")


def cmd_full(args: argparse.Namespace) -> int:
    return cmd_run(args, "full")


def cmd_ci(args: argparse.Namespace) -> int:
    return cmd_run(args, "ci-check")


def cmd_agent(args: argparse.Namespace) -> int:
    return cmd_run(args, "ai-agent")


def cmd_file(args: argparse.Namespace) -> int:
    return cmd_run(args, "single-file", target_file=args.file)


def cmd_collect(args: argparse.Namespace) -> int:
    target_path = pathlib.Path(args.path).expanduser().resolve()
    output_path = pathlib.Path(args.output).expanduser().resolve() if args.output else target_path / "security-evidence.json"
    command = [
        str(target_path),
        "--audit-type",
        args.audit_type,
        "--output",
        str(output_path),
        "--timeout",
        str(args.scanner_timeout),
    ]
    if args.file:
        command.extend(["--file", args.file])
    return run_python("collect_evidence.py", command)


def cmd_validate(_: argparse.Namespace) -> int:
    return run_python("validate_skill.py", [])


def cmd_build(args: argparse.Namespace) -> int:
    output_path = pathlib.Path(args.output).expanduser().resolve() if args.output else ROOT / "web-security-review.skill"
    return run_python("build_skill.py", ["--output", str(output_path)])


def cmd_install(args: argparse.Namespace) -> int:
    host = args.host
    if host == "codex":
        if args.layout is not None:
            raise SystemExit("--layout is only supported for Gemini installs. Codex workspace installs use .agents/skills.")
    workspace_root = pathlib.Path(args.workspace_root).expanduser().resolve() if args.workspace_root else None
    layout = args.layout or "native"
    if args.dest:
        skills_dir = pathlib.Path(args.dest).expanduser().resolve()
    elif host == "codex" and args.scope == "user":
        skills_dir = codex_home() / "skills"
    elif host == "codex":
        root = workspace_root or pathlib.Path.cwd().resolve()
        skills_dir = root / ".agents" / "skills"
    else:
        skills_dir = gemini_skills_dir(args.scope, layout, workspace_root=workspace_root)
    skills_dir.mkdir(parents=True, exist_ok=True)

    if args.artifact:
        artifact_path = pathlib.Path(args.artifact).expanduser().resolve()
        if not artifact_path.exists():
            raise SystemExit(f"Artifact not found: {artifact_path}")
    else:
        artifact_path = ROOT / "build" / "install" / "web-security-review.skill"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        exit_code = run_python("build_skill.py", ["--output", str(artifact_path)])
        if exit_code != 0:
            return exit_code

    install_target = skills_dir / "web-security-review"
    ensure_within(skills_dir, install_target)
    if install_target.exists():
        shutil.rmtree(install_target)

    safe_extract(artifact_path, skills_dir)
    print(f"Installed web-security-review to: {install_target}")
    if host == "codex":
        if args.scope == "workspace":
            print("Codex workspace install: restart the Codex session or refresh skills, then try:")
        else:
            print("Codex user install: restart the Codex app/session if the skill is not listed, then try:")
        print("  Use $web-security-review for a quick security review of this repo.")
        return 0

    location_label = ".agents/skills" if layout == "agents" else ".gemini/skills"
    print(f"Gemini install scope: {args.scope} ({location_label})")
    if args.scope == "workspace":
        print("If Gemini CLI does not show the skill yet, trust the workspace if needed and run /skills reload.")
    else:
        print("If Gemini CLI is already running, use /skills reload to refresh discovered skills.")
    print("Try it in Gemini CLI with:")
    print("  /skills list")
    print("  /skills reload")
    print("  Use the web-security-review skill to review this repo for security issues.")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    exit_code = cmd_install(args)
    if exit_code != 0:
        return exit_code

    print("")
    cmd_doctor(args)
    print("")
    print("First scan:")
    print("  wsr scan")
    print("  python scripts/audit.py scan")
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    provider = detect_provider()
    print("Web Security Review Doctor")
    print(f"- Python: {sys.executable}")
    print(f"- Repo: {ROOT}")
    print(f"- Codex home: {codex_home()}")
    print(f"- Gemini user skills (.gemini): {gemini_skills_dir('user', 'native')}")
    print(f"- Gemini user skills (.agents): {gemini_skills_dir('user', 'agents')}")
    print(f"- Gemini workspace skills (.gemini): {gemini_skills_dir('workspace', 'native')}")
    print(f"- Gemini workspace skills (.agents): {gemini_skills_dir('workspace', 'agents')}")
    print(f"- Detected provider: {provider or 'none'}")
    print(f"- OPENAI_API_KEY: {'set' if os.environ.get('OPENAI_API_KEY') else 'missing'}")
    print(f"- ANTHROPIC_API_KEY: {'set' if os.environ.get('ANTHROPIC_API_KEY') else 'missing'}")
    print(f"- GOOGLE_API_KEY: {'set' if os.environ.get('GOOGLE_API_KEY') else 'missing'}")
    print("- Scanner tools:")
    for tool in SCANNER_TOOLS:
        status = shutil.which(tool)
        print(f"  - {tool}: {'found' if status else 'missing'}")
    print("- Try one of these:")
    print("  - ./wsr setup")
    print("  - ./wsr scan")
    print("  - python scripts/audit.py install")
    print("  - python scripts/audit.py install --scope workspace --workspace-root .")
    print("  - python scripts/audit.py install --host gemini")
    print("  - python scripts/audit.py install --host gemini --layout agents")
    print("  - python scripts/audit.py install --host gemini --scope workspace")
    print("  - python scripts/audit.py scan")
    print("  - python scripts/audit.py quick .")
    print("  - python scripts/audit.py full .")
    print("  - python scripts/audit.py agent . --strict")
    print("  - python scripts/audit.py validate")
    print(r"  - powershell -File .\scripts\install.ps1")
    print(r"  - powershell -File .\scripts\install-gemini.ps1")
    print(r"  - powershell -File .\scripts\scan.ps1")
    print(r"  - powershell -File .\wsr.ps1 scan")
    print("  - Claude Code: /plugin marketplace add adams216/web-security-review-skill")
    print("  - Claude Code: /plugin install web-security-review@adams216-security-skills")
    print("  - Gemini CLI: gemini skills install https://github.com/adams216/web-security-review-skill.git --consent")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Friendly launcher for the web-security-review skill.",
        epilog="Examples: audit.py setup | audit.py scan | audit.py install --host gemini | audit.py agent . --strict | audit.py validate",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    quick = subparsers.add_parser("quick", aliases=["scan"], help="Run a fast High/Critical scan on the current repo or a target path.")
    common_run_parser(quick)
    quick.set_defaults(func=cmd_quick)

    full = subparsers.add_parser("full", help="Run a full application security audit.")
    common_run_parser(full)
    full.set_defaults(func=cmd_full)

    ci = subparsers.add_parser("ci", help="Run a CI, Docker, and deployment-focused security review.")
    common_run_parser(ci)
    ci.set_defaults(func=cmd_ci)

    agent = subparsers.add_parser("agent", help="Run an AI-agent, MCP, and prompt-surface review.")
    common_run_parser(agent)
    agent.set_defaults(func=cmd_agent)

    file_parser = subparsers.add_parser("file", help="Deep review a single file. Run from the repo root or pass a target path.")
    file_parser.add_argument("file", help="Target file relative to the repo root.")
    common_run_parser(file_parser)
    file_parser.set_defaults(func=cmd_file)

    collect = subparsers.add_parser("collect", help="Collect local evidence without calling a model.")
    collect.add_argument("path", nargs="?", default=".", help="Path to the repository or audit target. Defaults to the current directory.")
    collect.add_argument("--audit-type", choices=["quick", "full", "single-file", "ci-check", "ai-agent"], default="full", help="Evidence collection context.")
    collect.add_argument("--file", help="Optional target file for single-file collection.")
    collect.add_argument("--output", help="Optional output path. Defaults to security-evidence.json in the target directory.")
    collect.add_argument("--scanner-timeout", type=int, default=20, help="Timeout in seconds per external scanner command.")
    collect.set_defaults(func=cmd_collect)

    validate = subparsers.add_parser("validate", aliases=["test"], help="Run the full local validation suite.")
    validate.set_defaults(func=cmd_validate)

    build = subparsers.add_parser("build", aliases=["pack"], help="Build the packaged .skill artifact.")
    build.add_argument("--output", help="Optional output path for the built .skill artifact.")
    build.set_defaults(func=cmd_build)

    def add_install_options(target: argparse.ArgumentParser) -> None:
        target.add_argument("--artifact", help="Optional existing .skill file to install. Defaults to building from current source.")
        target.add_argument("--dest", help="Optional skills directory. Overrides the host-specific default install location.")
        target.add_argument("--host", choices=HOST_CHOICES, default="codex", help="Install target. Defaults to codex.")
        target.add_argument("--scope", choices=["user", "workspace"], default="user", help="For Gemini installs, choose user or workspace scope.")
        target.add_argument(
            "--layout",
            choices=GEMINI_LAYOUT_CHOICES,
            help="For Gemini installs, choose the standard .gemini/skills path or the interoperable .agents/skills alias.",
        )
        target.add_argument(
            "--workspace-root",
            help="For Gemini workspace installs, choose the workspace root. Defaults to the current working directory.",
        )

    setup = subparsers.add_parser("setup", help="Install the skill, run environment checks, and show the first scan command.")
    add_install_options(setup)
    setup.set_defaults(func=cmd_setup)

    install = subparsers.add_parser("install", help="Build and install the skill into Codex or Gemini skill directories.")
    add_install_options(install)
    install.set_defaults(func=cmd_install)

    doctor = subparsers.add_parser("doctor", help="Check provider keys, scanner availability, and quick-start commands.")
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
