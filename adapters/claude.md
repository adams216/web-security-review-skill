# Adapter: Claude (Anthropic)

Use this file alongside `system-prompt.md` when running the security skill with Claude.

---

## Recommended models

| Model | Best for |
|-------|----------|
| `claude-opus-4-5` | Full audits, complex codebases, threat modeling |
| `claude-sonnet-4-5` | Fast scans, PR reviews, single-file audits |

---

## Claude-specific capabilities to use

### Extended thinking (Opus)
For complex threat modeling or tracing multi-step attack chains, enable extended thinking.
This allows Claude to reason through exploit paths before presenting findings.

```python
import anthropic

client = anthropic.Anthropic()

with open("system-prompt.md") as f:
    system = f.read()

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 8000},
    system=system,
    messages=[{"role": "user", "content": audit_prompt}]
)

# Extract thinking and response separately
for block in response.content:
    if block.type == "thinking":
        print("=== THREAT MODELING REASONING ===")
        print(block.thinking)
    elif block.type == "text":
        print("=== SECURITY REPORT ===")
        print(block.text)
```

### File inputs (PDFs, images of architecture diagrams)
Claude can directly read uploaded files. Pass source files as base64:

```python
import base64

with open("src/auth/login.js", "rb") as f:
    file_data = base64.standard_b64encode(f.read()).decode("utf-8")

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=8096,
    system=system,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "text/plain",
                    "data": file_data
                },
                "title": "auth/login.js"
            },
            {"type": "text", "text": "Run a full security audit on this file."}
        ]
    }]
)
```

### Sending multiple files
Pass an array of document blocks — Claude handles up to 200k tokens of context:

```python
import os, base64, pathlib

def load_file(path):
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

files = list(pathlib.Path("src/").rglob("*.js")) + \
        list(pathlib.Path("src/").rglob("*.ts"))

content = []
for fp in files[:30]:  # stay within context budget
    content.append({
        "type": "document",
        "source": {"type": "base64", "media_type": "text/plain", "data": load_file(fp)},
        "title": str(fp)
    })

content.append({"type": "text", "text": "Run a full security audit on all files above."})

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=8096,
    system=system,
    messages=[{"role": "user", "content": content}]
)
```

---

## Claude Skills install (native)

If you're using Claude Skills (Claude.ai or enterprise deployment), install the `.skill`
file directly — no system prompt needed. The SKILL.md is loaded automatically when
security-related tasks are detected.

Install path: Settings → Skills → Upload `.skill` file

---

## Prompt tips for Claude

Claude follows multi-phase instructions well. You can say:
- "Run only Phase 1 and Phase 2 — skip the report for now"
- "Focus on the auth module only, then ask me before continuing"
- "Give me the CVSS scores in a table before explaining each finding"

Claude will respect phased instructions and ask for confirmation before proceeding
to the next module on large codebases.

---

## Context window strategy (200k tokens)

Rough token estimates:
- 1 line of code ≈ 5–10 tokens
- 1,000 line file ≈ 7,000–10,000 tokens
- Full Next.js app (50 files) ≈ 80,000–120,000 tokens

For large repos, use this order:
1. `auth/` + `middleware/` + `lib/` — always first
2. `api/` or `routes/` — second
3. `components/` — third
4. `Dockerfile`, CI config — last

Pass `package.json` and `package-lock.json` always (needed for dep audit).
