# Prompt Template: Single File Deep Dive

Use this when you want a line-by-line review of one specific file.
Best for: auth modules, payment handlers, file upload endpoints, API route files.

Works with: Claude, GPT-4o, Gemini

---

## Prompt (copy from here)

```
Perform a deep security review of the single file below. Go line by line through every function and code block.

For this file, I want:

1. **Function-by-function analysis** — for each function or route handler, describe:
   - What it does
   - What security assumptions it makes
   - Whether those assumptions hold
   - Any vulnerabilities found (with CWE and CVSS)

2. **Input validation audit** — list every place external input enters this file. For each:
   - Is it validated? (type, length, format, range)
   - Is it sanitized before use in queries/commands/HTML?
   - Is it safe?

3. **Auth/authz check** — does this file check authentication? Authorization? Are the checks correct and complete?

4. **Secrets & config** — any hardcoded values, environment variables, or config that could be a security issue?

5. **Inline fixes** — for every issue found, provide before/after code with explanation.

6. **Overall verdict** — one paragraph on the security quality of this file and the top 3 things to fix.
```

---

[Paste your file below this line, with the filename as a comment on the first line]
