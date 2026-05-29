#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

HOST_NAME="${WSR_HOST:-codex}"
SCOPE="${WSR_SCOPE:-user}"
LAYOUT="${WSR_LAYOUT:-native}"
DEST="${WSR_DEST:-}"
WORKSPACE_ROOT="${WSR_WORKSPACE_ROOT:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST_NAME="$2"
      shift 2
      ;;
    --scope)
      SCOPE="$2"
      shift 2
      ;;
    --layout)
      LAYOUT="$2"
      shift 2
      ;;
    --dest)
      DEST="$2"
      shift 2
      ;;
    --workspace-root)
      WORKSPACE_ROOT="$2"
      shift 2
      ;;
    *)
      echo "ERROR: unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -f "$SCRIPT_DIR/scripts/audit.sh" ]]; then
  args=(install --host "$HOST_NAME" --scope "$SCOPE")
  if [[ "$HOST_NAME" == "gemini" ]]; then
    args+=(--layout "$LAYOUT")
  fi
  if [[ -n "$DEST" ]]; then
    args+=(--dest "$DEST")
  fi
  if [[ -n "$WORKSPACE_ROOT" ]]; then
    args+=(--workspace-root "$WORKSPACE_ROOT")
  fi
  exec bash "$SCRIPT_DIR/scripts/audit.sh" "${args[@]}"
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required for remote installation." >&2
  exit 1
fi
if ! command -v unzip >/dev/null 2>&1; then
  echo "ERROR: unzip is required for remote installation." >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

artifact="$tmp_dir/web-security-review.skill"
extract_root="$tmp_dir/extract"
mkdir -p "$extract_root"
curl -fsSL "https://github.com/adams216/web-security-review-skill/releases/latest/download/web-security-review.skill" -o "$artifact"

if [[ -n "$DEST" ]]; then
  skills_dir="$DEST"
elif [[ "$HOST_NAME" == "codex" && "$SCOPE" == "user" ]]; then
  skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
elif [[ "$HOST_NAME" == "codex" ]]; then
  skills_dir="${WORKSPACE_ROOT:-$PWD}/.agents/skills"
else
  container=".gemini"
  if [[ "$LAYOUT" == "agents" ]]; then
    container=".agents"
  fi
  if [[ "$SCOPE" == "workspace" ]]; then
    skills_dir="${WORKSPACE_ROOT:-$PWD}/$container/skills"
  else
    skills_dir="$HOME/$container/skills"
  fi
fi

mkdir -p "$skills_dir"
unzip -q "$artifact" -d "$extract_root"
rm -rf "$skills_dir/web-security-review"
mv "$extract_root/web-security-review" "$skills_dir/web-security-review"

echo "Installed web-security-review to: $skills_dir/web-security-review"
if [[ "$HOST_NAME" == "codex" ]]; then
  if [[ "$SCOPE" == "workspace" ]]; then
    echo "Restart the Codex session or refresh skills if it is already open."
  else
    echo "Restart the Codex app/session if the skill is not listed."
  fi
  echo 'Try: Use $web-security-review for a quick security review of this repo.'
else
  echo "Try in Gemini CLI: /skills reload"
  echo "Then ask: Use the web-security-review skill to review this repo."
fi
