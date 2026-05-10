# Web Security Review Skill

An engineering-grade security audit skill for web applications. It works with Claude,
OpenAI models, and Google Gemini, and it is designed to catch the security issues
that general coding prompts often miss.

## What it does

Given a web application codebase, this package performs:

1. Threat modeling with trust boundaries, entry points, and STRIDE coverage
2. Static code analysis mapped to OWASP Top 10, CWE IDs, and CVSS v3.1
3. Dependency and supply-chain review
4. CI/CD and infrastructure review
5. Cryptography review
6. Formal report generation in `SECURITY_REPORT.md`
7. Inline fixes with attack context and verification steps

## Supported stacks

| Layer | Supported |
|-------|-----------|
| Frontend | React, Next.js, Vue, plain HTML/JS |
| Backend | Node.js/Express, Python (Django, FastAPI), PHP, Go |
| CMS | WordPress |
| Infrastructure | Docker, GitHub Actions, GitLab CI, IAM policies |
| Databases | PostgreSQL, MySQL, MongoDB, Redis |

## Repository structure

```text
web-security-review/
|-- README.md
|-- system-prompt.md
|-- SKILL.md
|-- adapters/
|   |-- claude.md
|   |-- openai.md
|   `-- gemini.md
|-- prompt-templates/
|   |-- quick-scan.md
|   |-- full-audit.md
|   |-- single-file.md
|   `-- ci-check.md
|-- references/
|   |-- nextjs-react.md
|   |-- nodejs-express.md
|   |-- python-backend.md
|   `-- wordpress-php.md
`-- scripts/
    |-- run-audit.sh
    `-- extract-report.py
```

## Prompt templates

- `prompt-templates/quick-scan.md` for fast PR reviews or pre-commit checks
- `prompt-templates/full-audit.md` for a full pre-launch audit
- `prompt-templates/single-file.md` for one-file deep dives
- `prompt-templates/ci-check.md` for Docker, CI, and infrastructure files

## CLI runner

`scripts/run-audit.sh` bundles the relevant files, picks a template, calls the
selected provider, and writes the result to `SECURITY_REPORT.md`.

Examples:

```bash
./scripts/run-audit.sh --model claude --dir ./my-project --type quick
./scripts/run-audit.sh --model openai --dir ./my-project --type full
./scripts/run-audit.sh --model openai --dir ./my-project --type single-file --file src/auth/login.ts
./scripts/run-audit.sh --model gemini --dir ./my-project --type ci-check
```

Supported audit types:

- `quick`
- `full`
- `single-file` (requires `--file`)
- `ci-check`

Provider defaults:

- Claude: `claude-sonnet-4-5` for quick, single-file, and CI checks; `claude-opus-4-5` for full audits
- OpenAI: `gpt-4o-mini` for quick; `gpt-4o` for full, single-file, and CI checks
- Gemini: `gemini-2.0-flash` for quick; `gemini-2.5-pro` for full; `gemini-2.5-flash` for single-file and CI checks

Override the default model with `--model-name <provider-model-id>`.

Windows note:

- `run-audit.sh` is a Bash script. Use Git Bash, WSL, or another POSIX shell on Windows.
- `scripts/extract-report.py` runs fine from PowerShell with `python`.

## Extracting a clean report

If a provider returns extra text before the final markdown report, use:

```bash
python scripts/extract-report.py raw-output.txt --output SECURITY_REPORT.md
```

The runner already normalizes common fenced-output cases, but this script is useful
when you want to clean saved raw output manually.

## Quick start by model

### Claude

Option A:

- Install `web-security-review.skill` directly in your Claude environment

Option B:

- Copy `system-prompt.md` into the system prompt
- Use one of the prompt templates from `prompt-templates/`

Option C:

```python
import anthropic

with open("system-prompt.md") as f:
    system = f.read()

with open("adapters/claude.md") as f:
    adapter = f.read()

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=8096,
    system=system + "\n\n" + adapter,
    messages=[{"role": "user", "content": YOUR_CODE_OR_PROMPT}],
)
```

### OpenAI

Option A:

- Open [OpenAI Playground](https://platform.openai.com/playground)
- Use Chat mode
- Paste `system-prompt.md` into the system field
- Use one of:
  - `prompt-templates/quick-scan.md`
  - `prompt-templates/full-audit.md`
  - `prompt-templates/single-file.md`
  - `prompt-templates/ci-check.md`

Option B:

```python
from openai import OpenAI

with open("system-prompt.md") as f:
    system = f.read()

with open("adapters/openai.md") as f:
    adapter = f.read()

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system + "\n\n" + adapter},
        {"role": "user", "content": YOUR_CODE_OR_PROMPT},
    ],
)
```

### Gemini

Option A:

- Open [Google AI Studio](https://aistudio.google.com)
- Paste `system-prompt.md` into the system instructions field
- Use one of the templates from `prompt-templates/`

Option B:

```python
import google.generativeai as genai

with open("system-prompt.md") as f:
    system = f.read()

with open("adapters/gemini.md") as f:
    adapter = f.read()

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system + "\n\n" + adapter,
)
response = model.generate_content(YOUR_CODE_OR_PROMPT)
```

## Context window tips

| Model | Context limit | Strategy for large codebases |
|-------|--------------|------------------------------|
| Claude Opus/Sonnet | 200k tokens | Send core modules first, then infra |
| GPT-4o | 128k tokens | Split by module and use `single-file` when needed |
| Gemini 2.x | 1M to 2M tokens | Most repos fit without chunking |

For codebases that exceed the context window, audit in this order:

1. Auth and middleware
2. API routes and controllers
3. Database layer
4. Frontend input handling
5. Infrastructure files

## Contributing

Good next contributions include:

- new reference files for more stacks
- more CI examples
- stronger machine-readable output modes
- better repo chunking for very large projects

## License

MIT. Use freely; attribution is appreciated.
