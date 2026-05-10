# OWASP Micro Prompt: XSS and Template Injection

Use this when you want a focused review for reflected, stored, DOM-based XSS, and unsafe rendering.

```text
Review the provided code only for XSS and template-injection risks.

Focus on:
- unsafe HTML rendering
- dangerouslySetInnerHTML and innerHTML usage
- unescaped template output
- markdown or rich-text rendering paths
- client-side trust-boundary crossings

Trace attacker-controlled content from input to rendered output.
Ignore unrelated findings.

For each confirmed issue include:
- severity
- CWE
- file and line
- exploit path
- impact
- concrete fix
```
