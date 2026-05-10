# OWASP Micro Prompt: Secrets and Supply Chain

Use this when you want a focused review for credential exposure, dependency risk, and CI secrets handling.

```text
Review the provided code and config only for secrets exposure and supply-chain risk.

Focus on:
- hardcoded keys, passwords, and tokens
- secrets in CI, Docker, env examples, or logs
- risky dependency versions and missing lockfiles
- third-party actions, install scripts, and plugin trust
- long-lived credentials where short-lived identity should be used

Separate confirmed secret exposure from weaker hygiene issues.
Ignore unrelated application bugs.

For each confirmed issue include:
- severity
- file and line
- what is exposed or trusted unsafely
- likely blast radius
- concrete fix and verification step
```
