# Prompt Template: Governance Gate

Use this when you want a strict ship or block decision rather than an advisory report.

```text
Review the provided code and configuration as a release gate.

Your job is not only to find issues, but to decide:
- approve
- approve-with-conditions
- block

Use `block` for any confirmed Critical or High issue, committed secret, dangerous tool exposure, broken authorization on sensitive paths, or CI compromise path.

Return:
- executive summary
- findings with file and line
- release blockers
- required actions
- deferred risks
- final decision

Be conservative. If evidence is incomplete around a high-risk trust boundary, say what is missing and do not silently approve it.
```
