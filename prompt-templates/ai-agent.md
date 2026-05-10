# Prompt Template: AI Agent and MCP Security Audit

Use this to audit AI agents, prompt packs, Codex or Claude skills, MCP servers, plugins, and tool-enabled workflows.
Paste your prompt files, agent configs, MCP manifests, and tool server code.

Works with: Claude, GPT-4o, Gemini

---

## Prompt (copy from here)

```
Run a security audit focused on AI-agent and MCP risks.

Review in this order:

1. Prompt and instruction hierarchy
   - untrusted content treated as instructions
   - prompt injection paths
   - hidden prompt leakage
   - missing approval boundaries

2. Tool and MCP exposure
   - unrestricted shell, file, browser, or network tools
   - user-controlled arguments flowing into dangerous tools
   - missing validation, allowlists, or side-effect controls

3. Secrets, provider, and privacy handling
   - hardcoded keys
   - logs or prompts that reveal secrets
   - sensitive content sent to third-party providers without filtering
   - missing cost or model controls for privileged agents

4. Memory, retrieval, and data egress
   - RAG prompt injection
   - hostile web content reaching privileged prompts
   - cross-tenant memory leakage
   - exfiltration through tools or provider calls

5. Governance gate
   - decide whether this should be approved, approved with conditions, or blocked

For every finding include:
- severity
- confidence
- file and line number
- attack scenario
- evidence
- remediation
- verification step

End with a governance decision and concrete release blockers.
```

---

[Paste your AI agent files below this line]
