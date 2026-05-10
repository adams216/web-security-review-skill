# Web Security Review Skill

[![Release](https://img.shields.io/github/v/release/adams216/web-security-review-skill?display_name=tag)](https://github.com/adams216/web-security-review-skill/releases/latest)
[![Validate Skill](https://github.com/adams216/web-security-review-skill/actions/workflows/validate-skill.yml/badge.svg)](https://github.com/adams216/web-security-review-skill/actions/workflows/validate-skill.yml)

Evidence-backed AI security review for web applications, APIs, and delivery pipelines.

This repository ships both a portable `web-security-review.skill` artifact and the full source used to maintain it: prompts, adapters, references, evidence collection, CI validation, and build tooling.

## Why this project exists

Most AI security prompts produce vague bug lists. `web-security-review` is designed to produce engineering-grade output that a team can triage and ship against:

- threat model first, not isolated bug bingo
- evidence-backed findings with file and line references
- `confirmed` versus `suspected` issue separation
- CWE and CVSS metadata
- governance gate decisions for stricter review flows
- AI-agent, MCP, and prompt-surface coverage
- remediation guidance sized for delivery teams
- Markdown, JSON, and SARIF output for humans and CI

## What ships in this repo

| Component | Purpose |
| --- | --- |
| `web-security-review.skill` | Portable packaged artifact for release downloads and installation |
| `SKILL.md` and `system-prompt.md` | Core review behavior and output contract |
| `references/` | Methodology, reporting rules, vulnerability catalog, and stack-specific guidance |
| `adapters/` | Provider-specific prompting for OpenAI, Claude, and Gemini |
| `scripts/run_audit.py` | Canonical audit CLI |
| `scripts/collect_evidence.py` | Local evidence gathering and scanner orchestration |
| `scripts/run-audit.sh` and `scripts/run-audit.ps1` | Thin Unix and Windows wrappers |
| `prompt-templates/owasp/` | Focused micro-prompts for targeted vulnerability review |
| `tests/fixtures/` | Intentionally insecure fixtures for dry-run validation |

## Installation paths

Choose the path that fits your workflow.

### Use the packaged release

Download the latest `web-security-review.skill` asset from [Releases](https://github.com/adams216/web-security-review-skill/releases/latest) when you want the portable package.

### Work from source

Clone the repository when you want to customize prompts, adapters, or runner behavior:

```bash
git clone https://github.com/adams216/web-security-review-skill.git
cd web-security-review-skill
python scripts/build_skill.py
```

The build step regenerates `web-security-review.skill` from source and intentionally excludes repo-only files such as `README.md`, `tests/`, `.github/`, and `build/`.

## Using the skill in Codex

After installing the packaged artifact, prompt Codex with:

```text
Use $web-security-review to perform an evidence-backed security audit of this web application.
```

## Requirements

- Python 3.10 or later
- One provider SDK plus its API key
- Optional local scanners on `PATH` for richer evidence

Provider setup:

- `openai` with `OPENAI_API_KEY`
- `anthropic` with `ANTHROPIC_API_KEY`
- `google-generativeai` with `GOOGLE_API_KEY`

Install the provider clients:

```bash
python -m pip install openai anthropic google-generativeai
```

Optional local scanners that the evidence collector will use automatically when present:

- `npm`, `pnpm`, or `yarn` for JavaScript dependency audits
- `pip-audit` for Python dependency audits
- `composer` for PHP dependency audits
- `govulncheck` for Go dependency audits
- `trivy` for filesystem, container, and infra scans

## Quick start

Run a full audit and render a Markdown report:

```bash
python scripts/run_audit.py --model openai --dir ./my-app --type full --output SECURITY_REPORT.md
```

Run a deep review of a single file and keep JSON output:

```bash
python scripts/run_audit.py --model claude --dir ./my-app --type single-file --file src/auth/session.ts --format json --output findings.json
```

Run a CI and container review that fails the job on High or above:

```bash
python scripts/run_audit.py --model gemini --dir ./my-app --type ci-check --format sarif --output results.sarif --fail-on high
```

Run a strict AI-agent and MCP review that behaves like a release gate:

```bash
python scripts/run_audit.py --model openai --dir ./my-agent --type ai-agent --governance-profile strict --format json --output agent-review.json
```

Build the prompt bundle without calling a model:

```bash
python scripts/run_audit.py --model openai --dir ./my-app --type full --dry-run --output bundle.json --evidence-out evidence.json
```

Wrapper entrypoints are also available:

```bash
./scripts/run-audit.sh --model openai --dir ./my-app --type quick
pwsh ./scripts/run-audit.ps1 --model openai --dir ./my-app --type quick
```

If Python is not on your `PATH`, set `PYTHON_BIN` before using the shell wrappers.

## Audit modes

| Mode | Purpose | Typical use |
| --- | --- | --- |
| `quick` | Critical and High issue triage | PR review, pre-merge checks, fast screening |
| `full` | Full application and platform review | Release readiness, scheduled audits, deeper AppSec review |
| `single-file` | Line-by-line deep dive of one file | Auth handlers, upload flows, payment code, risky routes |
| `ci-check` | CI, Docker, and deployment review | Pipeline hardening, supply-chain review, platform checks |
| `ai-agent` | Prompt, MCP, tool, and provider-boundary review | Agent platforms, tool runners, skills, plugins, prompt packs |

## Output formats

| Format | Use case |
| --- | --- |
| `markdown` | Human-readable report for engineers and pull requests |
| `json` | Canonical machine-readable result for automation and dashboards |
| `sarif` | Code scanning and CI integrations |

`--fail-on` evaluates the normalized finding severity after the model response is parsed, which makes CI gating deterministic across output formats.

`--governance-profile strict` upgrades the run from an advisory audit to a gate-oriented review with an explicit `approve`, `approve-with-conditions`, or `block` decision.

## How it works

1. `collect_evidence.py` inventories the repo, detects stacks, including AI-agent and MCP surfaces, runs available local scanners, and performs redacted secret discovery.
2. `run_audit.py` selects the most relevant files for the chosen audit mode.
3. The runner loads the system prompt, provider adapter, prompt template, and only the references relevant to the detected stack.
4. The model is asked to return structured JSON, not free-form prose.
5. The result is normalized and rendered as Markdown, JSON, or SARIF.

This keeps the workflow reproducible and makes downstream automation much easier than parsing ad hoc markdown output.

## Supported stacks and surfaces

Current reference coverage includes:

- Next.js and React
- Node.js and Express
- Python backends, including Django and FastAPI-style review patterns
- WordPress and PHP
- AI agents, MCP servers, prompt packs, plugins, and tool workflows

The runner also reviews these supporting surfaces when present:

- dependency manifests and lockfiles
- Dockerfiles and compose files
- GitHub Actions and other CI configs
- Kubernetes-shaped manifests
- Terraform and related infrastructure files

## Evidence collection

The local evidence layer is one of the main differences between this project and a plain prompt pack.

It gathers:

- manifest and lockfile inventory
- detected languages and stack hints
- Docker, CI, and Kubernetes file presence
- scanner summaries and output excerpts when local tools are installed
- redacted secret-scan matches

Collected evidence can be saved separately with:

```bash
python scripts/collect_evidence.py ./my-app --audit-type full --output evidence.json
```

## Focused prompt library

The packaged skill now also includes smaller deep-dive prompts for targeted review:

- `prompt-templates/owasp/injection.md`
- `prompt-templates/owasp/auth-and-authorization.md`
- `prompt-templates/owasp/xss-and-template-injection.md`
- `prompt-templates/owasp/ssrf-and-egress.md`
- `prompt-templates/owasp/secrets-and-supply-chain.md`
- `prompt-templates/governance-gate.md`

These are useful when you want a narrow second-pass review instead of a full repo audit.

## Development workflow

Validate the repo locally:

```bash
python scripts/validate_skill.py
```

Rebuild the packaged artifact:

```bash
python scripts/build_skill.py --output web-security-review.skill
```

The validation flow checks:

- Python syntax
- Bash wrapper syntax
- dry-run bundle generation
- artifact packaging
- package-content boundaries so repo-only files do not leak into the `.skill`

GitHub Actions runs the same validation on pushes and pull requests via `.github/workflows/validate-skill.yml`.

## Professional use notes

This project is meant to improve review quality and consistency, not to replace hands-on security testing. Treat `suspected` findings as leads that need runtime validation, and confirm any critical remediation plan against the real architecture before shipping changes.

## License

MIT.
