# OWASP Micro Prompt: SSRF and Data Egress

Use this when you want a focused review for SSRF, open fetchers, webhook abuse, and unsafe outbound calls.

```text
Review the provided code only for SSRF and outbound data-egress risks.

Focus on:
- user-controlled URLs or hosts
- internal metadata service reachability
- unsafe webhook, crawler, or fetch endpoints
- server-side browser or HTTP client misuse
- outbound calls that can exfiltrate sensitive data

Trace attacker input into network destinations.
Call out missing allowlists, DNS pinning, or protocol restrictions.

For each confirmed issue include:
- severity
- CWE
- file and line
- reachable target and attack path
- impact
- remediation guidance
```
