#!/usr/bin/env python3
"""Build a clean .skill artifact from the repo source."""

from __future__ import annotations

import argparse
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE_ROOT = "web-security-review"

PACKAGE_PATHS = [
    "SKILL.md",
    "system-prompt.md",
    "agents",
    "adapters",
    "assets",
    "prompt-templates",
    "references",
    "scripts/collect_evidence.py",
    "scripts/extract-report.py",
    "scripts/run_audit.py",
    "scripts/run-audit.sh",
    "scripts/run-audit.ps1",
]


def iter_package_files(root: pathlib.Path):
    for entry in PACKAGE_PATHS:
        path = root / entry
        if not path.exists():
            continue
        if path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file():
                    yield file_path
        else:
            yield path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the packaged web-security-review.skill artifact.")
    parser.add_argument(
        "--output",
        default=str(ROOT / "web-security-review.skill"),
        help="Destination .skill path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = pathlib.Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{PACKAGE_ROOT}/", "")
        directory_entries: set[str] = set()
        for file_path in iter_package_files(ROOT):
            relative = file_path.relative_to(ROOT).as_posix()
            parent_parts = pathlib.PurePosixPath(relative).parents
            for parent in parent_parts:
                parent_text = parent.as_posix()
                if parent_text == ".":
                    continue
                entry_name = f"{PACKAGE_ROOT}/{parent_text}/"
                if entry_name not in directory_entries:
                    archive.writestr(entry_name, "")
                    directory_entries.add(entry_name)
            archive.write(file_path, arcname=f"{PACKAGE_ROOT}/{relative}")

    print(f"Built skill artifact: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

