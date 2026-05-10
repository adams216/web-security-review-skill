# Prompt Template: Quick Scan

Use this for fast PR reviews or pre-commit checks.
Returns only Critical and High findings — skips report generation.
Typical response time: 30–90 seconds.

Works with: Claude, GPT-4o, Gemini

---

## Prompt (copy from here)

```
Run a fast security scan on the code below. Focus only on Critical and High severity issues.

For each finding return:
- Severity (Critical / High)
- CWE ID
- CVSS v3.1 score
- File and line number
- One-sentence attack scenario
- The vulnerable code snippet
- The fixed code snippet

Skip: Medium/Low findings, dependency audit, infrastructure review, full report.
Stop after listing all Critical and High findings and give me a 2-sentence summary of overall risk.

If no Critical or High issues are found, say so clearly and list any Medium findings briefly.
```

---

[Paste your code below this line]
