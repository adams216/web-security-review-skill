# OWASP Micro Prompt: Authentication and Authorization

Use this when you want a focused review for login, session, token, RBAC, BOLA, and IDOR issues.

```text
Review the provided code only for authentication and authorization risks.

Focus on:
- missing auth on sensitive routes
- session lifecycle and token validation
- broken object-level authorization
- role checks, tenant boundaries, and admin-only paths
- CSRF and privilege-escalation paths

Prefer realistic attack chains over checklist noise.
Ignore unrelated findings unless they directly affect authz.

For each confirmed issue include:
- severity
- CWE
- file and line
- attacker path
- impact
- concrete remediation
```
