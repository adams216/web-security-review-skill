# Adapter: Google Gemini

Use this file alongside `system-prompt.md` when running the security skill with Gemini.

---

## Recommended models

| Model | Context | Best for |
|-------|---------|----------|
| `gemini-2.5-pro` | 2M tokens | Full monorepo audits, large codebases |
| `gemini-2.0-flash` | 1M tokens | Fast scans, CI pipelines, cost-sensitive |
| `gemini-2.5-flash` | 1M tokens | Balanced speed/quality for most audits |

Gemini's massive context window is its primary advantage — you can often pass an
entire repository in a single request without chunking.

---

## Basic API usage

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")  # or set GOOGLE_API_KEY env var

with open("system-prompt.md") as f:
    system = f.read()

with open("adapters/gemini.md") as f:
    adapter = f.read()

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system + "\n\n" + adapter
)

with open("src/auth/login.js") as f:
    code = f.read()

response = model.generate_content(
    f"Run a full security audit on this file:\n\n```js\n{code}\n```"
)

print(response.text)
```

---

## Sending an entire repository

Gemini's 1M–2M token context means most full projects fit in one request.

```python
import pathlib
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")

with open("system-prompt.md") as f:
    system = f.read()

def load_repo(root: str, extensions=(".js", ".ts", ".py", ".php", ".go", ".env.example")) -> str:
    skip_dirs = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", "vendor"}
    parts = []
    for fp in pathlib.Path(root).rglob("*"):
        if any(d in fp.parts for d in skip_dirs):
            continue
        if fp.suffix in extensions and fp.is_file():
            try:
                content = fp.read_text(encoding="utf-8", errors="ignore")
                parts.append(f"### {fp}\n```\n{content}\n```")
            except Exception:
                pass
    return "\n\n".join(parts)

codebase = load_repo("./my-project")

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=system
)

response = model.generate_content(
    f"Run a full engineering-grade security audit on this codebase.\n\n{codebase}"
)

print(response.text)
```

---

## File upload API (for binary files or very large repos)

For files over ~500k tokens, use Gemini's File API to upload first:

```python
import google.generativeai as genai
import pathlib, zipfile, tempfile, os

genai.configure(api_key="YOUR_GEMINI_API_KEY")

# Zip the repo first
with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in pathlib.Path("./my-project").rglob("*"):
            if fp.is_file() and "node_modules" not in str(fp):
                zf.write(fp, fp.relative_to("./my-project"))
    zip_path = tmp.name

# Upload to Gemini File API
uploaded = genai.upload_file(zip_path, mime_type="application/zip")
print(f"Uploaded: {uploaded.name}")

# Use in generation
model = genai.GenerativeModel("gemini-2.5-pro")
response = model.generate_content([
    uploaded,
    "Run a full security audit on this repository."
])

print(response.text)
os.unlink(zip_path)
```

---

## Structured JSON output

```python
import google.generativeai as genai
import json

genai.configure(api_key="YOUR_GEMINI_API_KEY")

STRUCTURED_INSTRUCTION = """
Return findings as a JSON object only. No markdown, no preamble. Schema:
{
  "risk_level": "critical|high|medium|low",
  "finding_count": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "findings": [
    {
      "id": "SEC-001",
      "severity": "critical",
      "title": "SQL Injection in login endpoint",
      "cwe": "CWE-89",
      "cvss_score": 9.8,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
      "file": "src/auth/login.js",
      "line": 42,
      "attack_scenario": "string",
      "fix_summary": "string",
      "fix_effort_hours": 1
    }
  ],
  "sprint_plan": {
    "sprint_1_critical": ["SEC-001"],
    "sprint_2_high": [],
    "backlog_medium_low": []
  }
}
"""

with open("system-prompt.md") as f:
    system = f.read()

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system + "\n\n" + STRUCTURED_INSTRUCTION,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        temperature=0
    )
)

response = model.generate_content(f"Audit:\n\n{code}")
findings = json.loads(response.text)
```

---

## Gemini-specific prompt tips

**Use explicit section markers.** Gemini performs better when you ask for clearly delineated sections:
```
Produce the audit in these sections, each starting with "## SECTION NAME":
## THREAT MODEL
## FINDINGS
## DEPENDENCY AUDIT
## REMEDIATION ROADMAP
```

**Temperature.** Set `temperature=0` for security reports to prevent hallucinated CVEs.

**Safety settings.** Gemini's default safety filters may block security-related content (exploit descriptions, vulnerability details). If responses are being blocked or truncated, configure safety settings:

```python
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
)
```

**Note:** `BLOCK_NONE` for dangerous content is appropriate for security tooling where the
content describes vulnerabilities in the user's own code. Use responsibly.

---

## Context window strategy

Gemini's large context is a major advantage. Still, for best results:

- Always put `package.json` / `requirements.txt` early in the prompt (dependency audit)
- Put auth and API route files before frontend components
- Skip `node_modules/`, `dist/`, `build/`, `.next/`, `__pycache__/`
- `.env.example` is useful; never pass actual `.env` files with real secrets to any API

Rough estimates:
- 1 line of code ≈ 5–10 tokens
- Medium Next.js app (100 files, 10k lines) ≈ 100,000 tokens
- Large monorepo (500 files, 80k lines) ≈ 800,000 tokens (fits in gemini-2.5-pro)
