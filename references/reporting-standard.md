# Reporting Standard

Use this reference when generating structured output, Markdown reports, or SARIF.

## Canonical result model

The preferred internal model is:

- `metadata`
- `summary`
- `threat_model`
- `findings`
- `dependency_audit`
- `supply_chain`
- `cryptography_assessment`
- `security_headers`
- `positive_findings`
- `best_actions`
- `remediation_roadmap`

## Required finding fields

Each finding should include:

- `id`
- `severity`
- `title`
- `cwe_id`
- `cwe_name`
- `cvss_score`
- `cvss_vector`
- `confidence`
- `status`
- `category`
- `file`
- `start_line`
- `end_line`
- `attack_scenario`
- `impact`
- `evidence`
- `fix_summary`
- `verification`
- `suggested_owner`

## Markdown report sections

Render reports in this order:

1. Executive summary
2. Best actions
3. Governance decision, when requested
4. Threat model summary
5. Findings by severity
6. Dependency and supply-chain review
7. Cryptography assessment
8. Security headers
9. Positive findings
10. Remediation roadmap

## Best actions section

Every Markdown report should include `## Best Actions` near the top.

Each action should include:

- priority
- action
- why it matters
- files or systems affected
- suggested owner
- verification step

Keep the list focused on the highest-leverage work. Prefer 3 to 7 actions.

## SARIF mapping

Map severities like this:

- `critical` -> `error`
- `high` -> `error`
- `medium` -> `warning`
- `low` -> `note`
- `info` -> `note`

Use the finding `id` as the SARIF `ruleId`.

## Fail-threshold logic

For CI gating, compare the highest finding severity against the configured threshold:

- `critical`
- `high`
- `medium`
- `low`
- `info`
- `none`

Fail the process when any confirmed finding meets or exceeds the threshold.
