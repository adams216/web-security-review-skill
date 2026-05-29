#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ -x "$PYTHON_BIN" ]]; then
  :
elif ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v py >/dev/null 2>&1; then
    PYTHON_BIN="py"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "ERROR: python3, py, or python must be available on PATH" >&2
    exit 1
  fi
elif [[ "$PYTHON_BIN" == "python3" ]] && "$PYTHON_BIN" -c "import sys" >/dev/null 2>&1; then
  :
elif [[ "$PYTHON_BIN" == "python3" ]]; then
  if command -v py >/dev/null 2>&1; then
    PYTHON_BIN="py"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "ERROR: python3, py, or python must be available on PATH" >&2
    exit 1
  fi
fi

if ! "$PYTHON_BIN" -c "import sys" >/dev/null 2>&1; then
  if [[ "$PYTHON_BIN" != "py" ]] && command -v py >/dev/null 2>&1 && py -c "import sys" >/dev/null 2>&1; then
    PYTHON_BIN="py"
  elif [[ "$PYTHON_BIN" != "python" ]] && command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "ERROR: selected Python command does not run: $PYTHON_BIN" >&2
    exit 1
  fi
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/audit.py" "$@"
