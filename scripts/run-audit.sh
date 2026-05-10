#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ -x "$PYTHON_BIN" ]]; then
  :
elif ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "ERROR: python3 or python must be available on PATH" >&2
    exit 1
  fi
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/run_audit.py" "$@"
