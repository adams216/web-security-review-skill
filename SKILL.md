---
name: web-security-review
description: >
  Perform security reviews of web applications and APIs with evidence-backed findings,
  stack-aware checks, and sprint-ready remediation. Use when auditing a React, Next.js,
  Vue, Node.js, Express, Django, FastAPI, PHP, WordPress, Docker, CI/CD, AI agent,
  MCP, prompt, plugin, or skill codebase
  for vulnerabilities, OWASP coverage, CVEs, threat modeling, secrets exposure,
  auth or authorization flaws, supply-chain risk, prompt injection, tool exposure,
  governance gates, or release readiness.
---

# Web Security Review

Use this skill to perform an application security review that engineers can act on.
Think like an AppSec engineer, not a generic code reviewer.

## Core stance

- Think in realistic attack chains, not isolated bug bingo.
- Prefer local evidence before model inference whenever tools are available.
- Separate `confirmed` findings from `suspected` findings that need runtime validation.
- Never emit a finding without evidence, file path, and remediation guidance.
- Keep the tone collaborative and delivery-focused.

## Review modes

- `quick-scan`: Critical and High issues only. Use for PRs, pre-commit checks, or fast triage.
- `full-audit`: Full threat model, static review, dependency review, infra review, crypto review, and remediation plan.
- `single-file`: Deep dive one file line by line. Best for auth, payment, upload, and route handlers.
- `ci-check`: Review Docker, CI, IAM, deployment, and platform config.
- `ai-agent`: Review prompts, MCP servers, tools, plugins, provider egress, memory, and approval boundaries.

When local execution is allowed, prefer the bundled runners:

- `scripts/audit.py`
- `scripts/audit.ps1`
- `scripts/audit.sh`
- `scripts/run-audit.sh`
- `scripts/run-audit.ps1`
- `scripts/run_audit.py`
- `scripts/collect_evidence.py`

## Default workflow

1. Determine the review mode and scope.
2. Collect local evidence first:
   - dependency scanner output
   - inventory of manifests and infra files
   - redacted secret-scan hits
   - stack detection
3. Load only the references needed for this stack and scope.
4. Model the attack surface:
   - protected assets
   - trust boundaries
   - entry points
   - likely attacker goals
5. Produce structured findings with severity, exploit path, and fix.
6. End with a sprint-ready remediation plan and positive findings.

## Required finding fields

Every confirmed finding must include:

- `id`
- `severity`
- `title`
- `file`
- `line` or line range
- `cwe`
- `cvss_score`
- `cvss_vector`
- `confidence`
- `attack_scenario`
- `impact`
- `evidence`
- `fix_summary`
- `verification`

If a finding cannot satisfy the evidence bar, mark it as `suspected` and explain what
runtime check is needed.

## Reference map

Load these references only when needed:

- `references/core-methodology.md`
  Use for threat modeling, evidence rules, confidence, severity, and exploit-chain thinking.
- `references/vulnerability-catalog.md`
  Use when enumerating vulnerability classes, CWE mappings, and stack-specific risk areas.
- `references/reporting-standard.md`
  Use when producing JSON, Markdown, or SARIF-style outputs and remediation plans.
- `references/nextjs-react.md`
  Use for Next.js, React, Auth.js, client-side rendering, and browser-side data handling.
- `references/nodejs-express.md`
  Use for Express middleware, JWT, GraphQL, file upload, and Node-specific issues.
- `references/python-backend.md`
  Use for Django, FastAPI, Pydantic validation, ORM safety, and atomic operations.
- `references/wordpress-php.md`
  Use for WordPress hardening, PHP input handling, and plugin-related risk.
- `references/ai-agent-security.md`
  Use for AI-agent, MCP, prompt, plugin, retrieval, and tool-execution review.
- `references/governance-gates.md`
  Use when the review should produce a ship, conditional-ship, or block decision.

## Reporting rules

- Group findings by severity, then by file.
- Prefer actionable, concrete language over generic advice.
- Include interim mitigations when a full remediation is large.
- Explicitly call out what the codebase does well.
- Avoid invented CVEs, package versions, or exploit claims.
- If the review is tool-assisted, distinguish `local evidence` from `model inference`.

## Large-repo strategy

For large repositories, review in slices:

1. auth and middleware
2. API handlers and server actions
3. database and data access layer
4. frontend trust-boundary crossings
5. infra and CI/CD

Merge findings at the end and deduplicate by exploit path, not by syntax pattern.

## Bundled scripts

- `scripts/audit.py`
  Friendly launcher with short commands like `setup`, `install`, `quick`, `full`, `ci`, `agent`, `validate`, and `build`, including host-aware installs for Codex and Gemini.
- `scripts/audit.ps1`
  PowerShell wrapper for the friendly launcher.
- `scripts/audit.sh`
  Bash wrapper for the friendly launcher.
- `scripts/run_audit.py`
  Main advanced CLI. Supports dry runs, evidence collection, JSON, Markdown, SARIF, fail thresholds, AI-agent mode, and strict governance gating.
- `scripts/collect_evidence.py`
  Collects local scanner output, inventory data, and redacted secret-scan evidence.
- `scripts/run-audit.sh`
  Bash wrapper for Unix-like environments.
- `scripts/run-audit.ps1`
  PowerShell wrapper for Windows environments.
- `scripts/build_skill.py`
  Builds a clean `.skill` artifact without repo-only files such as tests and workflows.
- `scripts/extract-report.py`
  Extracts the report body from raw model output.

## Output expectations

- For interactive use, return Markdown unless the caller asks for JSON.
- For automation, prefer structured JSON and render Markdown or SARIF locally.
- When a schema or exact field contract is supplied, follow it exactly.
