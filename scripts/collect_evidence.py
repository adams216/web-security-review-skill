#!/usr/bin/env python3
"""Collect local evidence for the web-security-review skill."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

SKIP_DIRS = {
    ".git",
    ".next",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}

SOURCE_EXTENSIONS = {
    ".cfg",
    ".conf",
    ".env",
    ".example",
    ".go",
    ".graphql",
    ".hcl",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".sh",
    ".sql",
    ".tf",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".yaml",
    ".yml",
}

MANIFEST_NAMES = {
    "package.json",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "Pipfile",
    "composer.json",
    "go.mod",
    "Gemfile",
}

LOCKFILE_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "go.sum",
    "Gemfile.lock",
}

DOCKER_NAMES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
}

CI_NAMES = {
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
}

MAX_SCANNER_OUTPUT_CHARS = 12000
MAX_SECRET_SCAN_FILE_BYTES = 512 * 1024

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("slack-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    (
        "generic-secret-assignment",
        re.compile(
            r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token|client[_-]?secret|private[_-]?key)\b"
            r"[^=\n:]{0,20}[:=]\s*['\"]?([^\s'\"\n]{6,})"
        ),
    ),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def display_path(path: pathlib.Path, root: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip(path: pathlib.Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def list_repo_files(root: pathlib.Path) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for path in sorted(root.rglob("*")):
        if should_skip(path) or not path.is_file():
            continue
        files.append(path)
    return files


def detect_languages(paths: list[pathlib.Path]) -> list[str]:
    names: set[str] = set()
    for path in paths:
        if path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
            names.add("javascript-typescript")
        elif path.suffix == ".py":
            names.add("python")
        elif path.suffix == ".php":
            names.add("php")
        elif path.suffix == ".go":
            names.add("go")
        elif path.suffix == ".rb":
            names.add("ruby")
        elif path.suffix == ".tf":
            names.add("terraform")
        elif path.name in DOCKER_NAMES or path.name.startswith("Dockerfile"):
            names.add("docker")
        elif path.suffix in {".yaml", ".yml"}:
            names.add("yaml")
    return sorted(names)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        return json.loads(read_text(path))
    except Exception:
        return {}


def build_inventory(root: pathlib.Path, paths: list[pathlib.Path]) -> dict[str, Any]:
    manifests = [display_path(path, root) for path in paths if path.name in MANIFEST_NAMES]
    lockfiles = [display_path(path, root) for path in paths if path.name in LOCKFILE_NAMES]
    docker_files = [
        display_path(path, root)
        for path in paths
        if path.name in DOCKER_NAMES or path.name.startswith("Dockerfile")
    ]
    ci_files = [
        display_path(path, root)
        for path in paths
        if path.name in CI_NAMES or display_path(path, root).startswith(".github/workflows/")
    ]
    kubernetes_files = [
        display_path(path, root)
        for path in paths
        if any(part in {"k8s", "kubernetes", "helm"} for part in path.parts)
        and path.suffix.lower() in {".yaml", ".yml", ".json", ".tpl"}
    ]

    return {
        "root": str(root),
        "total_files": len(paths),
        "languages": detect_languages(paths),
        "manifests": manifests,
        "lockfiles": lockfiles,
        "docker_files": docker_files,
        "ci_files": ci_files,
        "kubernetes_files": kubernetes_files,
    }


def detect_stacks(root: pathlib.Path, paths: list[pathlib.Path]) -> list[str]:
    stacks: set[str] = set()
    package_json_paths = [path for path in paths if path.name == "package.json"]

    package_docs = [load_json(path) for path in package_json_paths]
    package_deps: set[str] = set()
    for package_doc in package_docs:
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            values = package_doc.get(section, {}) or {}
            if isinstance(values, dict):
                package_deps.update(values.keys())

    rel_paths = {display_path(path, root) for path in paths}

    if "next" in package_deps or any(path.name.startswith("next.config.") for path in paths):
        stacks.add("nextjs-react")
    elif "react" in package_deps or any(path.suffix in {".jsx", ".tsx"} for path in paths):
        stacks.add("nextjs-react")

    if "express" in package_deps or any("/routes/" in rel for rel in rel_paths):
        stacks.add("nodejs-express")

    if any(path.suffix == ".py" for path in paths) or any(
        name in rel_paths for name in {"requirements.txt", "pyproject.toml"}
    ):
        stacks.add("python-backend")

    if any(
        path.name == "wp-config.php"
        or "wp-content" in path.parts
        or "wp-admin" in path.parts
        for path in paths
    ):
        stacks.add("wordpress-php")

    return sorted(stacks)


def truncate_text(value: str) -> tuple[str, bool]:
    if len(value) <= MAX_SCANNER_OUTPUT_CHARS:
        return value, False
    return value[:MAX_SCANNER_OUTPUT_CHARS] + "\n[truncated]", True


def summarize_scanner(name: str, stdout_text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(stdout_text)
    except Exception:
        return None

    if name in {"npm-audit", "pnpm-audit"}:
        return payload.get("metadata", {}).get("vulnerabilities")

    if name == "pip-audit" and isinstance(payload, list):
        return {"dependency_findings": len(payload)}

    if name == "composer-audit":
        advisories = payload.get("advisories", {})
        if isinstance(advisories, dict):
            count = sum(len(value) for value in advisories.values() if isinstance(value, list))
            return {"advisories": count}

    if name == "trivy-fs":
        count = 0
        for result in payload.get("Results", []) or []:
            vulnerabilities = result.get("Vulnerabilities") or []
            if isinstance(vulnerabilities, list):
                count += len(vulnerabilities)
        return {"vulnerabilities": count}

    return None


def run_command(name: str, command: list[str], cwd: pathlib.Path, timeout: int) -> dict[str, Any]:
    executable = command[0]
    resolved_executable = shutil.which(executable)
    if resolved_executable is None:
        return {
            "name": name,
            "status": "unavailable",
            "command": command,
            "reason": f"{executable} not found on PATH",
        }
    command = [resolved_executable, *command[1:]]

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "status": "timeout",
            "command": command,
            "timeout_seconds": timeout,
        }

    stdout_excerpt, stdout_truncated = truncate_text(completed.stdout or "")
    stderr_excerpt, stderr_truncated = truncate_text(completed.stderr or "")
    summary = summarize_scanner(name, completed.stdout or "")

    return {
        "name": name,
        "status": "ok" if completed.returncode == 0 else "error",
        "command": command,
        "exit_code": completed.returncode,
        "summary": summary,
        "stdout_excerpt": stdout_excerpt,
        "stderr_excerpt": stderr_excerpt,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }


def collect_scanner_results(root: pathlib.Path, inventory: dict[str, Any], timeout: int) -> list[dict[str, Any]]:
    manifest_set = set(inventory["manifests"])
    lockfile_set = set(inventory["lockfiles"])
    results: list[dict[str, Any]] = []

    if "package.json" in manifest_set:
        if "pnpm-lock.yaml" in lockfile_set:
            results.append(run_command("pnpm-audit", ["pnpm", "audit", "--json"], root, timeout))
        elif "yarn.lock" in lockfile_set:
            results.append(run_command("yarn-audit", ["yarn", "npm", "audit", "--json"], root, timeout))
        else:
            results.append(run_command("npm-audit", ["npm", "audit", "--json"], root, timeout))

    if "requirements.txt" in manifest_set:
        results.append(
            run_command(
                "pip-audit",
                ["pip-audit", "-r", "requirements.txt", "--format", "json"],
                root,
                timeout,
            )
        )

    if "composer.json" in manifest_set:
        results.append(run_command("composer-audit", ["composer", "audit", "--format=json"], root, timeout))

    if "go.mod" in manifest_set:
        results.append(run_command("govulncheck", ["govulncheck", "-json", "./..."], root, timeout))

    if inventory["docker_files"] or inventory["kubernetes_files"]:
        results.append(run_command("trivy-fs", ["trivy", "fs", "--format", "json", "."], root, timeout))

    return results


def redact_excerpt(line: str) -> str:
    redacted = line.rstrip()
    redacted = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA****************", redacted)
    redacted = re.sub(r"gh[pousr]_[A-Za-z0-9_]{20,}", "ghp_<redacted>", redacted)
    redacted = re.sub(r"xox[baprs]-[A-Za-z0-9-]{10,}", "xoxb-<redacted>", redacted)
    redacted = re.sub(
        r"(?i)(\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token|client[_-]?secret|private[_-]?key)\b"
        r"[^=\n:]{0,20}[:=]\s*['\"]?)([^\s'\"\n]+)",
        r"\1<redacted>",
        redacted,
    )
    return redacted


def secret_scan(paths: list[pathlib.Path], root: pathlib.Path, max_matches: int) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []

    for path in paths:
        if len(matches) >= max_matches:
            break
        if path.suffix.lower() not in SOURCE_EXTENSIONS and path.name not in MANIFEST_NAMES | LOCKFILE_NAMES:
            continue
        if path.stat().st_size > MAX_SECRET_SCAN_FILE_BYTES:
            continue

        try:
            content = read_text(path)
        except Exception:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            for pattern_name, pattern in SECRET_PATTERNS:
                if not pattern.search(line):
                    continue
                matches.append(
                    {
                        "file": display_path(path, root),
                        "line": line_number,
                        "pattern": pattern_name,
                        "excerpt_redacted": redact_excerpt(line),
                    }
                )
                if len(matches) >= max_matches:
                    break
            if len(matches) >= max_matches:
                break

    return {
        "status": "ok",
        "match_count": len(matches),
        "max_matches": max_matches,
        "matches": matches,
        "truncated": len(matches) >= max_matches,
    }


def collect_evidence(
    root: pathlib.Path,
    audit_type: str = "full",
    target_file: pathlib.Path | None = None,
    timeout: int = 20,
    max_secret_matches: int = 50,
) -> dict[str, Any]:
    paths = list_repo_files(root)
    inventory = build_inventory(root, paths)
    stacks = detect_stacks(root, paths)
    scanners = collect_scanner_results(root, inventory, timeout)
    secrets = secret_scan(paths, root, max_secret_matches)

    evidence: dict[str, Any] = {
        "generated_at": now_utc(),
        "audit_type": audit_type,
        "root": str(root),
        "target_file": str(target_file) if target_file else None,
        "inventory": inventory,
        "stacks": stacks,
        "scanners": scanners,
        "secret_scan": secrets,
    }
    return evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect local security review evidence.")
    parser.add_argument("path", help="Path to the repository or audit target.")
    parser.add_argument("--audit-type", default="full", help="quick, full, single-file, or ci-check")
    parser.add_argument("--file", help="Optional target file for single-file audits.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout per external scanner command.")
    parser.add_argument(
        "--max-secret-matches",
        type=int,
        default=50,
        help="Maximum number of redacted secret-scan matches to keep.",
    )
    parser.add_argument("--output", help="Optional JSON output path. Defaults to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: path not found or not a directory: {root}", file=sys.stderr)
        return 1

    target_file = pathlib.Path(args.file).expanduser().resolve() if args.file else None
    evidence = collect_evidence(
        root=root,
        audit_type=args.audit_type,
        target_file=target_file,
        timeout=args.timeout,
        max_secret_matches=args.max_secret_matches,
    )

    payload = json.dumps(evidence, indent=2)
    if args.output:
        output_path = pathlib.Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        sys.stdout.write(payload)
        if not payload.endswith("\n"):
            sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
