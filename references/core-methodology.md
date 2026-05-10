# Core Methodology

Use this reference for threat modeling, evidence handling, and severity decisions.

## Threat model checklist

Capture these before reviewing findings:

- assets worth protecting
- trust boundaries
- attacker-reachable entry points
- attacker personas
- likely exploit chains

## Evidence rules

A finding is `confirmed` only if the reviewed artifact contains direct supporting
evidence, such as:

- vulnerable code
- insecure configuration
- scanner output
- committed secret material
- dependency or infrastructure evidence

A finding is `suspected` when the code suggests risk but runtime validation is still
needed, such as:

- missing server-side enforcement not visible in the current slice
- environment-dependent security headers
- cloud or WAF configuration not present in the repo

## Confidence levels

- `high`: direct evidence and clear exploit path
- `medium`: direct evidence but some deployment assumptions
- `low`: partial evidence or strong suspicion needing runtime validation

## Severity calibration

Use exploitability plus impact:

- `critical`: unauthenticated or low-friction path to data loss, auth bypass, RCE, or high-value compromise
- `high`: serious compromise that needs conditions, auth, or chaining
- `medium`: real weakness with lower exploitability or partial impact
- `low`: weak posture, hygiene issues, or limited-impact misconfiguration
- `info`: noteworthy observation or hardening opportunity

## Attack-chain thinking

Do not stop at syntax. Ask:

- can this combine with missing rate limiting, open CORS, or weak session handling?
- can a medium issue become critical with another low-friction weakness?
- does this create lateral movement, privilege escalation, or data exfiltration?

## Review order

Start here for most web codebases:

1. auth and session lifecycle
2. authorization and ownership checks
3. input validation and query construction
4. file handling and SSRF surfaces
5. secrets, config, and deployment posture
6. dependencies and supply chain

## Required output fields

For every confirmed finding, include:

- `id`
- `severity`
- `title`
- `cwe`
- `cvss_score`
- `cvss_vector`
- `confidence`
- `file`
- `start_line`
- `end_line`
- `attack_scenario`
- `impact`
- `evidence`
- `fix_summary`
- `verification`
