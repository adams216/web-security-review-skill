# Prompt Template: Full Engineering Audit

Use this prompt for a complete pre-launch security audit.
Paste your code below the divider line, or reference the files you've shared.

Works with: Claude, GPT-4o, Gemini

---

## Prompt (copy from here)

```
Run a full engineering-grade security audit on the codebase provided.

Follow all 8 phases in order:

**Phase 1 — Threat Modeling**
Map the attack surface: list protected assets, draw trust boundaries, enumerate all entry points, and complete a STRIDE assessment for each major component.

**Phase 2 — Static Code Analysis**
Scan in priority order (auth first, then API routes, then database layer, then file handling, then crypto, then config, then client-side, then infra). For every finding record: file path, line number, CWE ID, CVSS v3.1 score, and attack scenario. Check for all vulnerability classes from Critical down to Low.

**Phase 3 — Dependency Audit**
Identify the package manager. List all vulnerable dependencies with: package name, installed vs. fixed version, CVE ID, CVSS score, vulnerability type, and fix effort. Also flag supply chain risks (unmaintained packages, suspicious postinstall scripts, missing lockfile).

**Phase 4 — CI/CD & Infrastructure**
Review Dockerfile, docker-compose, and CI pipeline files. Check for: secrets in ENV/ARG, non-root user, multi-stage builds, pinned action versions, OIDC vs long-lived credentials.

**Phase 5 — Cryptography Audit**
Check all hashing, encryption, and random number generation. Flag any use of MD5/SHA1 for passwords, Math.random() for tokens, ECB mode, or hardcoded IV/salt.

**Phase 6 — CVSS Scoring**
Score every finding using CVSS v3.1 base metrics. Include the full vector string.

**Phase 7 — Security Report**
Produce a complete SECURITY_REPORT.md with:
- Executive summary and overall risk rating
- Findings table (ID, severity, CWE, CVSS, file:line, fix effort hours)
- Full detail per finding: attack scenario, impact, vulnerable code, fixed code, why it works
- OWASP Top 10 (2021) coverage table
- Dependency audit results table
- Cryptography assessment
- Remediation roadmap mapped to sprints
- Security headers checklist
- Positive findings (what was done well)

**Phase 8 — Inline Fixes**
For every finding, provide a fix block:
- File and line number
- One-sentence attack vector
- Vulnerable code (labeled VULNERABLE)
- Fixed code (labeled FIXED)
- Bullet list of what changed and why
- How to verify the fix (curl command, unit test, or manual step)

Start with Phase 1 and proceed through all phases. If the codebase is large, announce your scope before each phase and ask if I want to continue.
```

---

[Paste your code or file tree below this line]
