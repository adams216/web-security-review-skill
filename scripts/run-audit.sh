#!/usr/bin/env bash
# run-audit.sh - Web Security Review CLI wrapper
#
# Runs a security audit on a codebase using Claude, OpenAI, or Gemini API.
# Saves the output as SECURITY_REPORT.md in the target directory.
#
# Usage:
#   ./scripts/run-audit.sh --model claude --dir ./my-project
#   ./scripts/run-audit.sh --model openai --dir ./my-project --type quick
#   ./scripts/run-audit.sh --model gemini --dir ./my-project --type full
#   ./scripts/run-audit.sh --model openai --dir ./my-project --type single-file --file src/auth/login.ts
#   ./scripts/run-audit.sh --model claude --dir ./my-project --type ci-check
#
# Requirements:
#   - Python 3.9+
#   - anthropic / openai / google-generativeai package installed
#   - API key set as env var: ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

MODEL="claude"
MODEL_NAME=""
AUDIT_DIR="."
AUDIT_TYPE="quick"
TARGET_FILE=""
OUTPUT_FILE="SECURITY_REPORT.md"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run-audit.sh --model [claude|openai|gemini] --dir <path> [options]

Options:
  --type quick|full|single-file|ci-check
      quick       Critical/High first pass
      full        Full engineering audit
      single-file Deep review of one file (requires --file)
      ci-check    CI/CD and infrastructure focused review
  --file <path>      Target file for --type single-file
  --output <file>    Output path. Relative paths are written under --dir
  --model-name <id>  Override the provider-specific default model
  --help             Show this message

Examples:
  ./scripts/run-audit.sh --model claude --dir ./my-project --type quick
  ./scripts/run-audit.sh --model openai --dir ./my-project --type full
  ./scripts/run-audit.sh --model openai --dir ./my-project --type single-file --file src/auth/login.ts
  ./scripts/run-audit.sh --model gemini --dir ./my-project --type ci-check
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --model-name) MODEL_NAME="$2"; shift 2 ;;
    --dir) AUDIT_DIR="$2"; shift 2 ;;
    --type) AUDIT_TYPE="$2"; shift 2 ;;
    --file) TARGET_FILE="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$MODEL" in
  claude|openai|gemini) ;;
  *)
    echo "ERROR: --model must be one of: claude, openai, gemini" >&2
    exit 1
    ;;
esac

case "$AUDIT_TYPE" in
  quick|full|single-file|single|ci-check|ci) ;;
  *)
    echo "ERROR: --type must be one of: quick, full, single-file, ci-check" >&2
    exit 1
    ;;
esac

if [[ "$AUDIT_TYPE" == "single" ]]; then
  AUDIT_TYPE="single-file"
fi

if [[ "$AUDIT_TYPE" == "ci" ]]; then
  AUDIT_TYPE="ci-check"
fi

if [[ ! -d "$AUDIT_DIR" ]]; then
  echo "ERROR: directory not found: $AUDIT_DIR" >&2
  exit 1
fi

if [[ "$AUDIT_TYPE" == "single-file" && -z "$TARGET_FILE" ]]; then
  echo "ERROR: --file is required when --type single-file is used" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "ERROR: python3 or python must be available on PATH" >&2
    exit 1
  fi
fi

echo "Web Security Review"
echo "  Provider: $MODEL"
echo "  Target:   $AUDIT_DIR"
echo "  Type:     $AUDIT_TYPE"
if [[ -n "$TARGET_FILE" ]]; then
  echo "  File:     $TARGET_FILE"
fi
echo "  Output:   $OUTPUT_FILE"
echo ""

export WSR_MODEL="$MODEL"
export WSR_MODEL_NAME="$MODEL_NAME"
export WSR_AUDIT_DIR="$AUDIT_DIR"
export WSR_AUDIT_TYPE="$AUDIT_TYPE"
export WSR_TARGET_FILE="$TARGET_FILE"
export WSR_OUTPUT_FILE="$OUTPUT_FILE"
export WSR_SKILL_DIR="$SKILL_DIR"

"$PYTHON_BIN" - <<'PYTHON'
import os
import pathlib
import sys


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


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


def normalize_output(text: str) -> str:
    cleaned = text.strip()
    for heading in ("# Security Audit Report", "# Security Audit", "## Security Audit Report"):
        index = cleaned.find(heading)
        if index != -1:
            return strip_trailing_fence(cleaned[index:].lstrip())
    return strip_fence(cleaned)


def fence_language(path: pathlib.Path) -> str:
    if path.name.startswith("Dockerfile"):
        return "dockerfile"

    mapping = {
        ".js": "js",
        ".ts": "ts",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".py": "python",
        ".php": "php",
        ".go": "go",
        ".rb": "ruby",
        ".sh": "bash",
        ".json": "json",
        ".toml": "toml",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".md": "markdown",
        ".sql": "sql",
        ".graphql": "graphql",
        ".tf": "hcl",
    }
    return mapping.get(path.suffix.lower(), "")


model = os.environ["WSR_MODEL"]
model_name_override = os.environ.get("WSR_MODEL_NAME", "").strip()
audit_dir = pathlib.Path(os.environ["WSR_AUDIT_DIR"]).expanduser().resolve()
audit_type = os.environ["WSR_AUDIT_TYPE"]
target_file_raw = os.environ.get("WSR_TARGET_FILE", "").strip()
output_file = os.environ["WSR_OUTPUT_FILE"]
skill_dir = pathlib.Path(os.environ["WSR_SKILL_DIR"]).expanduser().resolve()

if not audit_dir.exists() or not audit_dir.is_dir():
    fail(f"audit directory not found: {audit_dir}")

system_prompt_path = skill_dir / "system-prompt.md"
adapter_path = skill_dir / "adapters" / f"{model}.md"

if not system_prompt_path.exists():
    fail(f"system-prompt.md not found at {system_prompt_path}")

if not adapter_path.exists():
    fail(f"adapter not found for model '{model}': {adapter_path}")

template_names = {
    "quick": "quick-scan",
    "full": "full-audit",
    "single-file": "single-file",
    "ci-check": "ci-check",
}

if audit_type not in template_names:
    fail(f"unsupported audit type: {audit_type}")

template_path = skill_dir / "prompt-templates" / f"{template_names[audit_type]}.md"
if not template_path.exists():
    fail(f"prompt template not found: {template_path}")

system = read_text(system_prompt_path)
adapter = read_text(adapter_path)
template = read_text(template_path)

default_model_names = {
    "claude": {
        "quick": "claude-sonnet-4-5",
        "full": "claude-opus-4-5",
        "single-file": "claude-sonnet-4-5",
        "ci-check": "claude-sonnet-4-5",
    },
    "openai": {
        "quick": "gpt-4o-mini",
        "full": "gpt-4o",
        "single-file": "gpt-4o",
        "ci-check": "gpt-4o",
    },
    "gemini": {
        "quick": "gemini-2.0-flash",
        "full": "gemini-2.5-pro",
        "single-file": "gemini-2.5-flash",
        "ci-check": "gemini-2.5-flash",
    },
}

model_name = model_name_override or default_model_names[model][audit_type]
print(f"  Model name: {model_name}")

skip_dirs = {
    "node_modules",
    ".git",
    "dist",
    "build",
    ".next",
    "__pycache__",
    "vendor",
    ".venv",
    ".turbo",
    ".cache",
}

source_extensions = {
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".vue",
    ".svelte",
    ".py",
    ".php",
    ".go",
    ".rb",
    ".java",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".sh",
    ".sql",
    ".graphql",
    ".ini",
    ".cfg",
    ".conf",
    ".tf",
}

always_include_names = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "composer.json",
    "composer.lock",
    "go.mod",
    "go.sum",
    "Gemfile",
    "Gemfile.lock",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    ".env.example",
    ".gitlab-ci.yml",
    "bitbucket-pipelines.yml",
    "azure-pipelines.yml",
}

ci_names = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    ".gitlab-ci.yml",
    "bitbucket-pipelines.yml",
    "azure-pipelines.yml",
    "Chart.yaml",
    "Chart.yml",
}


def should_skip(path: pathlib.Path) -> bool:
    return any(part in skip_dirs for part in path.parts)


def is_general_candidate(path: pathlib.Path) -> bool:
    if path.name in always_include_names:
        return True
    if path.name.startswith("Dockerfile."):
        return True
    if path.name.endswith(".env.example") or path.name.endswith(".env.sample"):
        return True
    return path.suffix.lower() in source_extensions


def is_ci_candidate(path: pathlib.Path) -> bool:
    rel = path.relative_to(audit_dir).as_posix()
    if path.name in ci_names or path.name.startswith("Dockerfile."):
        return True
    if rel.startswith(".github/workflows/") and path.suffix.lower() in {".yml", ".yaml"}:
        return True
    if rel.startswith(".circleci/") and path.suffix.lower() in {".yml", ".yaml"}:
        return True
    if any(part in {"k8s", "kubernetes", "helm"} for part in path.parts):
        return path.suffix.lower() in {".yml", ".yaml", ".json", ".tpl"}
    if path.suffix.lower() in {".tf", ".tfvars"} or path.name.endswith(".tf.json"):
        return True
    if path.name.endswith(".policy.json") or path.name == "iam-policy.json":
        return True
    return False


def display_path(path: pathlib.Path) -> str:
    try:
        return path.relative_to(audit_dir).as_posix()
    except ValueError:
        return str(path)


def build_block(path: pathlib.Path) -> str:
    content = read_text(path)
    if not content.strip():
        return ""
    language = fence_language(path)
    opening = f"```{language}" if language else "```"
    return f"### File: {display_path(path)}\n{opening}\n{content}\n```"


def collect_paths(predicate):
    paths = []
    for path in sorted(audit_dir.rglob("*")):
        if should_skip(path) or not path.is_file():
            continue
        if predicate(path):
            paths.append(path)
    return paths


parts = []
context_label = "CODEBASE"

if audit_type == "single-file":
    target_path = pathlib.Path(target_file_raw).expanduser()
    if not target_path.is_absolute():
        target_path = (audit_dir / target_path).resolve()
    else:
        target_path = target_path.resolve()

    if not target_path.exists() or not target_path.is_file():
        fail(f"target file not found: {target_path}")

    block = build_block(target_path)
    if not block:
        fail(f"target file is empty or unreadable: {target_path}")

    parts = [block]
    context_label = f"TARGET FILE: {display_path(target_path)}"
elif audit_type == "ci-check":
    parts = [build_block(path) for path in collect_paths(is_ci_candidate)]
    parts = [part for part in parts if part]
    context_label = "INFRASTRUCTURE FILES"
else:
    parts = [build_block(path) for path in collect_paths(is_general_candidate)]
    parts = [part for part in parts if part]

if not parts:
    fail(f"no eligible files found for audit type '{audit_type}' under {audit_dir}")

codebase = "\n\n".join(parts)
token_estimate = len(codebase) // 4
print(f"  Loaded {len(parts)} files (~{token_estimate:,} tokens estimated)")

user_message = f"{template}\n\n---\n\n{context_label}:\n\n{codebase}"

if model == "claude":
    try:
        import anthropic
    except ImportError:
        fail("anthropic package is not installed. Run: pip install anthropic")

    client = anthropic.Anthropic()
    print("  Sending to Claude...")
    response = client.messages.create(
        model=model_name,
        max_tokens=12000 if audit_type in {"full", "ci-check"} else 8192,
        system=system + "\n\n" + adapter,
        messages=[{"role": "user", "content": user_message}],
    )
    result = "\n\n".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()
elif model == "openai":
    try:
        from openai import OpenAI
    except ImportError:
        fail("openai package is not installed. Run: pip install openai")

    client = OpenAI()
    print("  Sending to OpenAI...")
    response = client.chat.completions.create(
        model=model_name,
        max_tokens=8192 if audit_type in {"full", "ci-check"} else 4096,
        temperature=0,
        messages=[
            {"role": "system", "content": system + "\n\n" + adapter},
            {"role": "user", "content": user_message},
        ],
    )
    result = (response.choices[0].message.content or "").strip()
elif model == "gemini":
    try:
        import google.generativeai as genai
    except ImportError:
        fail("google-generativeai package is not installed. Run: pip install google-generativeai")

    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
    print("  Sending to Gemini...")
    gem_model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system + "\n\n" + adapter,
        generation_config=genai.GenerationConfig(temperature=0),
    )
    response = gem_model.generate_content(user_message)
    result = response.text.strip()
else:
    fail(f"unsupported provider: {model}")

if not result:
    fail("model returned an empty response")

final_text = normalize_output(result)
out_path = pathlib.Path(output_file).expanduser()
if not out_path.is_absolute():
    out_path = audit_dir / out_path
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(final_text + "\n", encoding="utf-8")

print(f"\nSaved report to: {out_path}")
print("\n--- Report preview ---")
print("\n".join(final_text.splitlines()[:20]))
print("...")
PYTHON
