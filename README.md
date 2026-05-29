# Web Security Review Skill

[![Release](https://img.shields.io/github/v/release/adams216/web-security-review-skill?display_name=tag)](https://github.com/adams216/web-security-review-skill/releases/latest)
[![Validate Skill](https://github.com/adams216/web-security-review-skill/actions/workflows/validate-skill.yml/badge.svg)](https://github.com/adams216/web-security-review-skill/actions/workflows/validate-skill.yml)

Evidence-backed AI security review for web apps, APIs, CI/CD, Docker, and AI-agent/MCP workflows.

`web-security-review` is built to feel closer to an AppSec teammate than a loose security prompt: it collects local evidence, asks for structured findings, separates confirmed and suspected issues, and can produce Markdown, JSON, or SARIF output for humans and CI.

## Install

### Windows

Install the latest release into Codex:

```powershell
irm https://raw.githubusercontent.com/adams216/web-security-review-skill/main/install.ps1 | iex
```

Install into Gemini instead:

```powershell
$env:WSR_HOST="gemini"
irm https://raw.githubusercontent.com/adams216/web-security-review-skill/main/install.ps1 | iex
```

### macOS / Linux

Install the latest release into Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/adams216/web-security-review-skill/main/install.sh | bash
```

Install into Gemini instead:

```bash
curl -fsSL https://raw.githubusercontent.com/adams216/web-security-review-skill/main/install.sh | bash -s -- --host gemini
```

### From Source

Clone the repo when you want to run scans locally, customize prompts, or develop the skill:

```bash
git clone https://github.com/adams216/web-security-review-skill.git
cd web-security-review-skill
./install.sh
./wsr setup
```

On Windows:

```powershell
git clone https://github.com/adams216/web-security-review-skill.git
cd web-security-review-skill
.\install.ps1
.\wsr.ps1 setup
```

## First Scan

Set one provider key:

```bash
export OPENAI_API_KEY="your-key"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key"
```

Run the scan:

```bash
./wsr scan
```

Windows:

```powershell
.\wsr.ps1 scan
```

The default quick scan writes a Markdown report into the target repo.

## Daily Commands

| Command | Purpose |
| --- | --- |
| `./wsr setup` | Install the skill and check your environment |
| `./wsr doctor` | Check API keys, Python, scanners, and install paths |
| `./wsr scan` | Quick high-signal security scan of the current repo |
| `./wsr full ./app` | Full engineering-grade application audit |
| `./wsr ci ./app --sarif --fail-on high` | CI, Docker, and pipeline review |
| `./wsr agent ./agent --strict` | AI-agent, MCP, prompt, and tool review |
| `./wsr file src/auth/session.ts ./app` | Deep review of one file |
| `./wsr validate` | Run the local validation suite |

Use `.\wsr.ps1` instead of `./wsr` on Windows PowerShell.

## Native Host Usage

### Codex

Install globally for your user:

```bash
./wsr install
```

Install into the current repo so Codex sees it as a project skill:

```bash
./wsr install --scope workspace --workspace-root .
```

Windows:

```powershell
.\wsr.ps1 install --scope workspace --workspace-root .
```

Use in Codex:

```text
Use $web-security-review for a quick security review of this repo.
Use $web-security-review for a full audit before release.
Use $web-security-review in ai-agent mode with strict governance.
```

Expected Codex app output:

- A Markdown report file in the workspace, such as `SECURITY_QUICK.md`, `SECURITY_REPORT.md`, or `SECURITY_AGENT.md`.
- A short chat summary with the report path and the highest-priority actions.
- A `Best Actions` section near the top of the report with concrete fixes, owners, and verification steps.

Most explicit prompt:

```text
Use $web-security-review for a full security audit of this repo. Write the detailed Markdown report to SECURITY_REPORT.md and include a Best Actions section with prioritized fixes.
```

If Codex says the skill is not available, restart the Codex app/session after installing. For the Codex app, the most reliable path is the workspace install above because it places the skill at `.agents/skills/web-security-review` inside the project.

Quick repair command for a repo where Codex cannot see the skill:

```powershell
.\wsr.ps1 install --scope workspace --workspace-root C:\path\to\your\repo
```

Then open a new Codex session in that repo and ask:

```text
Use $web-security-review for a quick security review of this repo.
```

### Gemini CLI

Install:

```bash
./wsr install --host gemini
```

Workspace install:

```bash
./wsr install --host gemini --scope workspace --workspace-root /path/to/repo
```

Use the interoperable `.agents/skills` layout:

```bash
./wsr install --host gemini --layout agents
```

Then in Gemini CLI:

```text
/skills reload
Use the web-security-review skill to review this repo for security issues.
```

### Claude Code

Add the plugin marketplace:

```text
/plugin marketplace add adams216/web-security-review-skill
```

Install the skill plugin:

```text
/plugin install web-security-review@adams216-security-skills
```

Then ask Claude Code:

```text
Use the web-security-review skill to run a full security audit on this repo.
```

## GitHub Actions

Use the bundled composite action for pull requests or release checks:

```yaml
name: Security Review

on:
  pull_request:
  workflow_dispatch:

jobs:
  security-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: adams216/web-security-review-skill@main
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        with:
          mode: ci
          format: sarif
          output: security-results.sarif
          fail-on: high
      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: security-results.sarif
```

For AI-agent and MCP review:

```yaml
- uses: adams216/web-security-review-skill@main
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  with:
    mode: agent
    strict: "true"
    format: json
    output: agent-review.json
    fail-on: high
```

## Provider Setup

Install the provider clients you plan to use:

```bash
python -m pip install openai anthropic google-generativeai
```

Set one API key:

| Provider | Environment variable |
| --- | --- |
| OpenAI | `OPENAI_API_KEY` |
| Claude | `ANTHROPIC_API_KEY` |
| Gemini | `GOOGLE_API_KEY` |

The runner auto-detects the provider from your environment. You can force one with `--provider openai`, `--provider claude`, or `--provider gemini`.

## What It Reviews

- Web apps and APIs: React, Next.js, Node/Express, Django/FastAPI-style Python, PHP, and WordPress
- Delivery: GitHub Actions, CI/CD config, Docker, compose, Kubernetes-shaped manifests, and Terraform-style infra files
- Supply chain: dependency manifests, lockfiles, local scanner output, and package audit summaries
- AI systems: prompts, MCP servers, tools, plugin boundaries, retrieval, memory, provider egress, and approval flows

## Output Formats

| Format | Command |
| --- | --- |
| Markdown | `./wsr full ./app` |
| JSON | `./wsr full ./app --json --output findings.json` |
| SARIF | `./wsr ci ./app --sarif --output results.sarif` |

Use `--fail-on high` or `--fail-on critical` when the result should gate CI.

Strict governance mode adds an explicit `approve`, `approve-with-conditions`, or `block` decision:

```bash
./wsr agent ./my-agent --strict --json --output agent-review.json
```

## How It Works

1. `collect_evidence.py` inventories the repo, detects stacks, runs available local scanners, and redacts secret-like values.
2. `run_audit.py` selects the relevant files and references for the requested mode.
3. The model receives a structured audit request and returns normalized JSON.
4. The runner renders Markdown, JSON, or SARIF and applies deterministic `--fail-on` gating.

Optional scanners are used automatically when available: `npm`, `pnpm`, `yarn`, `pip-audit`, `composer`, `govulncheck`, and `trivy`.

## Development

Validate everything:

```bash
./wsr validate
```

Build the packaged skill:

```bash
./wsr build
```

Advanced CLI access is still available:

```bash
python scripts/run_audit.py --model openai --dir ./my-app --type full --output SECURITY_REPORT.md
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Skill trigger metadata and compact operating instructions |
| `system-prompt.md` | Cross-provider security review contract |
| `references/` | Methodology, reporting rules, vulnerability catalog, and stack guidance |
| `prompt-templates/` | Quick, full, file, CI, AI-agent, governance, and OWASP-focused prompts |
| `scripts/audit.py` | Friendly command launcher behind `wsr` |
| `scripts/run_audit.py` | Canonical audit runner |
| `scripts/collect_evidence.py` | Local evidence collection |
| `tests/fixtures/` | Intentionally insecure dry-run fixtures |
| `action.yml` | GitHub composite action for CI use |

## Professional Use

This project improves review consistency, but it does not replace hands-on security testing. Treat suspected findings as leads, verify critical issues against the running system, and review remediation plans against the real architecture before release.

## License

MIT
