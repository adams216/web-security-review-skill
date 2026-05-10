# Web Security Review Skill

An engineering-grade security review skill for web applications, APIs, and deployment
configurations. This repo now ships both:

- source files for maintaining the skill
- a packaged `.skill` artifact for direct installation or release downloads

## What is new in v0.2

- leaner `SKILL.md` with progressive disclosure
- dedicated reference files for methodology, vulnerability coverage, and reporting
- local evidence collection before model inference
- structured JSON output as the canonical internal format
- local Markdown and SARIF rendering
- CI fail thresholds
- Windows and Unix wrappers
- build and validation scripts
- fixture-based dry-run validation in GitHub Actions

## Repository layout

```text
web-security-review-skill/
|-- SKILL.md
|-- system-prompt.md
|-- adapters/
|-- agents/
|-- prompt-templates/
|-- references/
|-- scripts/
|   |-- collect_evidence.py
|   |-- run_audit.py
|   |-- run-audit.sh
|   |-- run-audit.ps1
|   |-- extract-report.py
|   |-- build_skill.py
|   `-- validate_skill.py
|-- tests/
|   `-- fixtures/
|-- .github/workflows/validate-skill.yml
`-- web-security-review.skill
```

## Packaged artifact

The packaged skill is built from source and intentionally excludes repo-only files such as:

- `README.md`
- `tests/`
- `.github/`
- `build/`
- maintenance scripts not needed by end users

Build it with:

```bash
python scripts/build_skill.py
```

## Main runners

Use whichever entrypoint fits your environment:

```bash
python scripts/run_audit.py --model openai --dir ./my-app --type full
./scripts/run-audit.sh --model claude --dir ./my-app --type quick
pwsh ./scripts/run-audit.ps1 --model gemini --dir . --type ci-check
```

If Python is not on your PATH, set `PYTHON_BIN` to a concrete interpreter path first.

Supported audit modes:

- `quick`
- `full`
- `single-file`
- `ci-check`

Supported output formats:

- `markdown`
- `json`
- `sarif`

Useful flags:

- `--dry-run` to build the request bundle without calling a model
- `--fail-on high` to fail CI when confirmed findings reach a threshold
- `--evidence-out evidence.json` to save local evidence separately
- `--model-name ...` to override the default provider model

## Local evidence collection

The runner uses `scripts/collect_evidence.py` to gather:

- manifest and lockfile inventory
- stack detection
- Docker, CI, and Kubernetes file presence
- external scanner output when tools are installed
- redacted secret-scan hits

Run it directly if you want the evidence bundle by itself:

```bash
python scripts/collect_evidence.py ./my-app --audit-type full --output evidence.json
```

## Structured output model

The runner asks the model for structured JSON and then renders:

- Markdown reports for humans
- JSON for automation
- SARIF for code-scanning and CI systems

This avoids brittle Markdown parsing and makes fail thresholds deterministic.

## Validation

Run the full local validation suite with:

```bash
python scripts/validate_skill.py
```

Validation covers:

- Python syntax checks
- Bash wrapper syntax
- dry-run bundles for full, single-file, and CI audit modes
- clean `.skill` package generation
- artifact content checks to ensure repo-only files do not leak into the package

GitHub Actions runs the same flow on pushes and pull requests via
`.github/workflows/validate-skill.yml`.

## Prompt templates

The prompt templates remain useful for direct manual use in model UIs:

- `prompt-templates/quick-scan.md`
- `prompt-templates/full-audit.md`
- `prompt-templates/single-file.md`
- `prompt-templates/ci-check.md`

## Supported stacks

Current stack references cover:

- Next.js and React
- Node.js and Express
- Django and FastAPI
- WordPress and PHP

The runner also reviews Docker, CI, IAM-style policy files, and Terraform-shaped
infrastructure files when present.

## Release workflow

The tracked `web-security-review.skill` file should be regenerated from source before
release or push when the packaged contents change:

```bash
python scripts/build_skill.py --output web-security-review.skill
```

## License

MIT. Use freely; attribution is appreciated.
