# Adapter: OpenAI (GPT-4o / Codex)

Use this file alongside `system-prompt.md` when running the security skill with OpenAI models.

---

## Recommended models

| Model | Best for |
|-------|----------|
| `gpt-4o` | Full audits, complex codebases, structured output |
| `gpt-4o-mini` | Quick scans, PR review, cost-sensitive pipelines |
| `o3` / `o4-mini` | Deep reasoning on complex exploit chains |

---

## Model-specific notes

### GPT-4o
- Context: 128k tokens — split large repos by module
- Strong at structured JSON output (use for machine-readable reports)
- Does not support file uploads via API; embed code as text in messages

### o3 / o4-mini (reasoning models)
- Better at multi-step exploit chain analysis
- Set `reasoning_effort: "high"` for thorough threat modeling
- Slower and more expensive — use for Critical/High findings only

---

## Basic API usage

```python
from openai import OpenAI

client = OpenAI()  # uses OPENAI_API_KEY env var

with open("system-prompt.md") as f:
    system = f.read()

with open("adapters/openai.md") as f:
    adapter = f.read()

# Load your code as text
with open("src/auth/login.js") as f:
    code = f.read()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system + "\n\n" + adapter},
        {"role": "user", "content": f"Audit this file:\n\n```js\n{code}\n```"}
    ],
    max_tokens=4096,
    temperature=0   # deterministic output for security reports
)

print(response.choices[0].message.content)
```

---

## Structured output (JSON mode)

Use this when integrating the audit into a CI pipeline that parses findings programmatically:

```python
from openai import OpenAI
import json

client = OpenAI()

with open("system-prompt.md") as f:
    system = f.read()

STRUCTURED_INSTRUCTION = """
Return findings as a JSON object with this schema:
{
  "risk_level": "critical|high|medium|low",
  "finding_count": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "findings": [
    {
      "id": "SEC-001",
      "severity": "critical|high|medium|low",
      "title": "string",
      "cwe": "CWE-XXX",
      "cvss_score": 9.8,
      "cvss_vector": "CVSS:3.1/...",
      "file": "path/to/file.js",
      "line": 42,
      "description": "string",
      "attack_scenario": "string",
      "fix": "string",
      "fix_effort_hours": 1
    }
  ],
  "owasp_coverage": {
    "A01": "pass|warn|fail",
    "A02": "pass|warn|fail"
  },
  "sprint_plan": {
    "sprint_1": ["SEC-001", "SEC-002"],
    "sprint_2": ["SEC-003"],
    "backlog": ["SEC-004"]
  }
}
Return ONLY valid JSON. No markdown, no preamble.
"""

response = client.chat.completions.create(
    model="gpt-4o",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": system + "\n\n" + STRUCTURED_INSTRUCTION},
        {"role": "user", "content": f"Audit:\n\n{code}"}
    ],
    temperature=0
)

findings = json.loads(response.choices[0].message.content)
```

---

## Sending multiple files

GPT-4o does not support native file uploads via API — embed code as text:

```python
import pathlib

def build_codebase_message(src_dir: str, extensions=(".js", ".ts", ".py")) -> str:
    parts = []
    for fp in pathlib.Path(src_dir).rglob("*"):
        if fp.suffix in extensions and fp.is_file():
            try:
                content = fp.read_text(encoding="utf-8", errors="ignore")
                parts.append(f"### File: {fp}\n```\n{content}\n```")
            except Exception:
                pass
    return "\n\n".join(parts)

codebase = build_codebase_message("src/")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system + "\n\n" + adapter},
        {"role": "user", "content": f"Audit this codebase:\n\n{codebase}"}
    ],
    max_tokens=4096,
    temperature=0
)
```

**Important:** GPT-4o has a 128k token context. For large codebases, audit in chunks:
1. Send auth + middleware files first
2. Then API routes
3. Then frontend

---

## Using o3/o4-mini for deep reasoning

```python
response = client.chat.completions.create(
    model="o3",
    reasoning_effort="high",  # "low", "medium", or "high"
    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": f"Threat model this application:\n\n{codebase}"}
    ]
)
```

Use reasoning models specifically for:
- Multi-step exploit chain analysis
- Business logic vulnerability detection
- Complex auth flow review

---

## Prompt tips for GPT-4o

GPT-4o responds well to explicit output format instructions. Add these to your user message if needed:

```
Return your findings in this exact order:
1. Executive summary (3 sentences)
2. Findings table (ID | Severity | Title | File:Line | CVSS)
3. Full finding details with attack scenario and fix
4. Sprint plan table
```

Setting `temperature=0` is strongly recommended for security audits — it reduces hallucinated CVEs and invented vulnerability details.

---

## Context window strategy (128k tokens)

Rough estimates:
- 1 line of code ≈ 5–10 tokens
- Full Next.js app (50 files) ≈ 80,000–120,000 tokens (borderline)
- Split if repo exceeds ~400 files or 15k lines

Always include: `package.json`, `package-lock.json` / `requirements.txt`
Always audit first: `auth/`, `middleware/`, `routes/` or `api/`
