# AI Agent and MCP Security

Use this reference for AI agents, MCP servers, prompt packs, plugins, and tool-using workflows.

## Review priorities

1. Prompt and instruction hierarchy
2. Tool exposure and execution boundaries
3. Secrets and credential handling
4. Data egress and provider trust boundaries
5. Memory, retrieval, and prompt-injection resistance
6. Multi-agent role separation and approval flow

## Prompt and instruction risks

Check for:

- system prompts that tell the model to ignore approval or safety boundaries
- prompt files that prioritize user content over system or policy rules
- instructions that reveal hidden prompts, secrets, or chain-of-thought-like internals
- untrusted document ingestion with no prompt-injection boundary
- missing distinction between trusted repo instructions and untrusted retrieved content

Evidence patterns:

- `ignore previous instructions`
- `always comply`
- `reveal system prompt`
- `run tools automatically`
- prompt templates with no trust-boundary guidance

## MCP and tool exposure

Check for:

- shell, filesystem, browser, or network tools exposed without clear approval boundaries
- tool wrappers that pass user-controlled input into `shell=True`, `exec`, or equivalent
- server tools that allow arbitrary file read, file write, process launch, or network egress
- MCP servers with broad capabilities but no argument validation or allowlist
- plugin manifests or tool registries that quietly expand permissions

Blocker-class issues:

- arbitrary shell execution from prompt-controlled input
- unrestricted file exfiltration tools
- tools that can reach production systems without explicit approval

## Secrets and provider configuration

Check for:

- hardcoded LLM provider keys or service credentials
- agent prompts that print environment variables or log secrets
- long-lived cloud credentials in MCP config or CI files
- missing cost controls, quota controls, or model allowlists for privileged agents

## Data flow and privacy

Check for:

- sensitive repo content sent to third-party providers with no filtering
- prompts that instruct the model to forward full documents, logs, or credentials
- memory or transcript storage with no redaction boundary
- cross-tenant context mixing in agent memory or retrieval layers

## Retrieval and prompt injection

Check for:

- RAG pipelines that trust retrieved documents as instructions
- browser or web-fetch tools that can import hostile instructions into privileged context
- markdown or HTML rendering paths that convert untrusted content into executable tool requests
- absence of clear "data, not instructions" handling for external content

## Governance expectations

When the review is acting as a gate, call out:

- whether powerful tools are separated from low-trust user input
- whether secrets can leak through prompts, logs, or provider calls
- whether approval boundaries are explicit and enforceable
- whether prompt injection can trigger side effects
- whether deployment should be blocked pending guardrails
