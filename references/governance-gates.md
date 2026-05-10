# Governance Gates

Use this reference when the review is meant to influence merge, release, or deployment decisions.

## Decision options

- `approve`: no meaningful blocker remains
- `approve-with-conditions`: merge or rollout can proceed only if listed follow-up actions are owned and scheduled
- `block`: release or merge should stop until blockers are resolved

## Always-block conditions

Use `block` when any confirmed finding shows:

- unauthenticated or low-friction compromise of a sensitive system
- arbitrary command execution or unrestricted tool execution
- committed secrets or long-lived credentials in repo-controlled files
- broken authentication or authorization on sensitive paths
- clear tenant-boundary failure or high-confidence data exfiltration path
- CI or deployment compromise path through untrusted pull requests or overbroad credentials
- AI agent or MCP workflow where untrusted content can drive privileged tools

## Conditional approval

Use `approve-with-conditions` when:

- only Medium, Low, or Info findings remain
- runtime verification is still needed but the current evidence does not show active compromise
- remediation is required before broad rollout but not before a limited internal test

## Required gate output

Populate:

- `decision`
- `release_blockers`
- `required_actions`
- `deferred_risks`
- `notes`

Keep blockers concrete and merge-ready. Prefer:

- owner-ready fix statements
- verification steps
- explicit rollout constraints

## High-risk areas to call out explicitly

- auth and authorization
- secrets and credential lifecycle
- shell, browser, filesystem, and network tool execution
- CI/CD identity and third-party action trust
- provider egress and data retention
- multi-tenant data boundaries
