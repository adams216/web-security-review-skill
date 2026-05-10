#!/usr/bin/env python3
"""Extract the markdown security report from raw model output."""

from __future__ import annotations

import argparse
import pathlib
import sys


HEADINGS = (
    "# Security Audit Report",
    "# Security Audit",
    "## Security Audit Report",
)


def strip_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def strip_trailing_fence(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[-1].strip() == "```":
        return "\n".join(lines[:-1]).rstrip()
    return text.strip()


def extract_report(text: str) -> str:
    cleaned = text.strip()
    for heading in HEADINGS:
        index = cleaned.find(heading)
        if index != -1:
            return strip_trailing_fence(cleaned[index:].lstrip())
    return strip_fence(cleaned)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract SECURITY_REPORT.md content from raw model output."
    )
    parser.add_argument("input", help="Path to the raw model output file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to write the extracted report. Defaults to stdout.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = pathlib.Path(args.input).expanduser()

    if not input_path.exists() or not input_path.is_file():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 1

    raw_text = input_path.read_text(encoding="utf-8", errors="ignore")
    report = extract_report(raw_text)

    if not report.strip():
        print("ERROR: extracted report is empty", file=sys.stderr)
        return 1

    if args.output:
        output_path = pathlib.Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report + "\n", encoding="utf-8")
    else:
        sys.stdout.write(report)
        if not report.endswith("\n"):
            sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
