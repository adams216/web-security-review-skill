# Prompt Template: CI/CD Security Check

Use this to audit your CI/CD pipeline, Dockerfile, and infrastructure config.
Paste your pipeline YAML, Dockerfile, and docker-compose files.

Works with: Claude, GPT-4o, Gemini

---

## Prompt (copy from here)

```
Audit the CI/CD and infrastructure configuration files below for security issues.

Check for:

**GitHub Actions / CI pipeline:**
- Secrets echoed or logged in steps
- `pull_request_target` trigger combined with code checkout (supply chain attack)
- Actions using floating tags (@v3) instead of pinned commit SHAs
- Long-lived credentials (AWS keys, service account JSONs) instead of OIDC
- ACTIONS_RUNNER_DEBUG or verbose logging of environment variables
- Overly broad permissions (permissions: write-all)

**Dockerfile:**
- Secrets in ENV or ARG instructions (they persist in image layers)
- Running as root user (missing USER instruction)
- No multi-stage build (build tools and dev dependencies in final image)
- Base image not pinned to digest (using :latest or floating tags)
- Sensitive files not excluded via .dockerignore

**docker-compose.yml:**
- Plaintext credentials in environment blocks
- --privileged flag or excessive capabilities
- Ports unnecessarily exposed to 0.0.0.0
- Volumes mounting sensitive host paths

**IAM / Cloud permissions:**
- Overly broad policies (Action: "*" or Resource: "*")
- Long-lived access keys instead of role-based auth
- Public S3 buckets or storage containers

For each issue:
- Severity (Critical / High / Medium / Low)
- File and line number
- What the risk is
- Fixed configuration

End with a summary table of all findings and an overall infrastructure security rating.
```

---

[Paste your Dockerfile, docker-compose.yml, and CI pipeline YAML below]
