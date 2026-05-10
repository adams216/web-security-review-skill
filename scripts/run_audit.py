#!/usr/bin/env python3
"""Main CLI for the web-security-review skill."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections import Counter
from datetime import datetime, timezone
from json import JSONDecodeError
from typing import Any

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import collect_evidence


SEVERITY_ORDER = {
    "none": -1,
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

TEXT_EXTENSIONS = {
    ".cfg",
    ".conf",
    ".env",
    ".example",
    ".go",
    ".graphql",
    ".hcl",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".sh",
    ".sql",
    ".tf",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".yaml",
    ".yml",
}

ALWAYS_INCLUDE_NAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "composer.json",
    "composer.lock",
    "go.mod",
    "go.sum",
    "Gemfile",
    "Gemfile.lock",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    ".env.example",
    ".gitlab-ci.yml",
    "bitbucket-pipelines.yml",
    "azure-pipelines.yml",
}

CI_NAMES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
    "Chart.yaml",
    "Chart.yml",
}

PRIORITY_HINTS = (
    ("auth", 100),
    ("login", 90),
    ("session", 90),
    ("middleware", 90),
    ("guard", 90),
    ("api", 80),
    ("route", 80),
    ("controller", 75),
    ("model", 60),
    ("db", 60),
    ("query", 60),
    ("docker", 70),
    ("workflow", 70),
    ("iam", 65),
    ("terraform", 65),
)

STACK_REFERENCE_MAP = {
    "ai-agent-mcp": "ai-agent-security.md",
    "nextjs-react": "nextjs-react.md",
    "nodejs-express": "nodejs-express.md",
    "python-backend": "python-backend.md",
    "wordpress-php": "wordpress-php.md",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def display_path(path: pathlib.Path, root: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()


def fence_language(path: pathlib.Path) -> str:
    if path.name.startswith("Dockerfile"):
        return "dockerfile"
    mapping = {
        ".go": "go",
        ".graphql": "graphql",
        ".js": "js",
        ".json": "json",
        ".md": "markdown",
        ".php": "php",
        ".py": "python",
        ".rb": "ruby",
        ".sh": "bash",
        ".sql": "sql",
        ".tf": "hcl",
        ".toml": "toml",
        ".ts": "ts",
        ".tsx": "tsx",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return mapping.get(path.suffix.lower(), "")


def score_path(path: pathlib.Path, root: pathlib.Path) -> tuple[int, str]:
    rel = display_path(path, root).lower()
    score = 0
    for hint, value in PRIORITY_HINTS:
        if hint in rel:
            score += value
    if path.name in ALWAYS_INCLUDE_NAMES:
        score += 40
    if path.name.startswith("Dockerfile"):
        score += 30
    return (-score, rel)


def is_ai_agent_focus_file(path: pathlib.Path, root: pathlib.Path) -> bool:
    rel = display_path(path, root).lower()
    return (
        collect_evidence.is_ai_agent_file(path, root)
        or rel.startswith(".github/workflows/")
        or any(part.lower() in {"policies", "rules"} for part in path.parts)
        or any(hint in rel for hint in ("approval", "egress", "memory", "rag", "retrieval"))
    )


def select_paths(
    root: pathlib.Path,
    audit_type: str,
    target_file: pathlib.Path | None,
    max_files: int,
) -> list[pathlib.Path]:
    all_files = collect_evidence.list_repo_files(root)

    if audit_type == "single-file":
        if target_file is None:
            fail("--file is required for single-file audits")
        resolved = target_file if target_file.is_absolute() else (root / target_file)
        resolved = resolved.resolve()
        if not resolved.exists() or not resolved.is_file():
            fail(f"target file not found: {resolved}")
        return [resolved]

    selected: list[pathlib.Path] = []
    for path in sorted(all_files, key=lambda item: score_path(item, root)):
        rel = display_path(path, root)
        if audit_type == "ci-check":
            if (
                path.name in CI_NAMES
                or path.name.startswith("Dockerfile.")
                or rel.startswith(".github/workflows/")
                or rel.startswith(".circleci/")
                or any(part in {"k8s", "kubernetes", "helm"} for part in path.parts)
                or path.suffix.lower() in {".tf", ".tfvars"}
                or path.name.endswith(".tf.json")
            ):
                selected.append(path)
            continue

        if audit_type == "ai-agent":
            if (
                is_ai_agent_focus_file(path, root)
                or path.name in ALWAYS_INCLUDE_NAMES
                or path.name.startswith("Dockerfile.")
                or path.suffix.lower() in TEXT_EXTENSIONS
                and any(
                    hint in rel.lower()
                    for hint in ("agent", "prompt", "mcp", "tool", "policy", "guardrail", "llm", "model")
                )
            ):
                selected.append(path)
            continue

        if path.name in ALWAYS_INCLUDE_NAMES or path.name.startswith("Dockerfile."):
            selected.append(path)
            continue
        if path.name.endswith(".env.example") or path.name.endswith(".env.sample"):
            selected.append(path)
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            selected.append(path)

    if not selected:
        fail(f"no eligible files found under {root} for audit type '{audit_type}'")

    if audit_type == "ai-agent" and not selected:
        fallback = [path for path in sorted(all_files, key=lambda item: score_path(item, root)) if path.suffix.lower() in TEXT_EXTENSIONS]
        selected = fallback[:max_files]

    return selected[:max_files]


def build_code_blocks(paths: list[pathlib.Path], root: pathlib.Path) -> str:
    parts: list[str] = []
    for path in paths:
        content = read_text(path)
        if not content.strip():
            continue
        language = fence_language(path)
        opening = f"```{language}" if language else "```"
        parts.append(f"### File: {display_path(path, root)}\n{opening}\n{content}\n```")
    if not parts:
        fail("selected files were empty after text extraction")
    return "\n\n".join(parts)


def load_references(audit_type: str, detected_stacks: list[str], governance_profile: str) -> dict[str, str]:
    reference_names = ["core-methodology.md", "reporting-standard.md"]
    if audit_type in {"quick", "full", "single-file", "ai-agent"}:
        reference_names.append("vulnerability-catalog.md")
    if audit_type == "ai-agent":
        reference_names.append("ai-agent-security.md")
    if governance_profile == "strict":
        reference_names.append("governance-gates.md")
    for stack in detected_stacks:
        filename = STACK_REFERENCE_MAP.get(stack)
        if filename:
            reference_names.append(filename)

    loaded: dict[str, str] = {}
    for filename in reference_names:
        path = SKILL_DIR / "references" / filename
        if path.exists():
            loaded[filename] = read_text(path)
    return loaded


def load_prompt_template(audit_type: str) -> str:
    mapping = {
        "ai-agent": "ai-agent.md",
        "quick": "quick-scan.md",
        "full": "full-audit.md",
        "single-file": "single-file.md",
        "ci-check": "ci-check.md",
    }
    path = SKILL_DIR / "prompt-templates" / mapping[audit_type]
    return read_text(path)


def load_system_material(provider: str) -> tuple[str, str]:
    system_prompt = read_text(SKILL_DIR / "system-prompt.md")
    adapter_path = SKILL_DIR / "adapters" / f"{provider}.md"
    if not adapter_path.exists():
        fail(f"adapter not found for provider '{provider}'")
    adapter = read_text(adapter_path)
    return system_prompt, adapter


def schema_instruction() -> str:
    return """
Return ONLY valid JSON matching this structure:
{
  "metadata": {
    "project_name": "string",
    "audit_mode": "quick|full|single-file|ci-check|ai-agent"
  },
  "summary": {
    "overall_risk": "critical|high|medium|low|info",
    "executive_summary": "string",
    "finding_count": {
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 0,
      "info": 0
    }
  },
  "threat_model": {
    "assets": ["string"],
    "trust_boundaries": ["string"],
    "entry_points": ["string"],
    "attack_paths": ["string"]
  },
  "findings": [
    {
      "id": "SEC-001",
      "status": "confirmed|suspected",
      "severity": "critical|high|medium|low|info",
      "confidence": "high|medium|low",
      "title": "string",
      "category": "string",
      "cwe_id": "CWE-000",
      "cwe_name": "string",
      "cvss_score": 0,
      "cvss_vector": "CVSS:3.1/...",
      "file": "path/to/file",
      "start_line": 1,
      "end_line": 1,
      "attack_scenario": "string",
      "impact": "string",
      "evidence": "string",
      "fix_summary": "string",
      "verification": "string",
      "suggested_owner": "string"
    }
  ],
  "dependency_audit": [
    {
      "package": "string",
      "severity": "critical|high|medium|low|info",
      "current_version": "string",
      "fixed_version": "string",
      "cve": "string",
      "notes": "string"
    }
  ],
  "supply_chain": ["string"],
  "cryptography_assessment": ["string"],
  "security_headers": [
    {
      "header": "string",
      "status": "present|missing|partial",
      "notes": "string"
    }
  ],
  "positive_findings": ["string"],
  "governance_gate": {
    "decision": "approve|approve-with-conditions|block",
    "release_blockers": ["string"],
    "required_actions": ["string"],
    "deferred_risks": ["string"],
    "notes": "string"
  },
  "remediation_roadmap": {
    "immediate": ["string"],
    "this_sprint": ["string"],
    "backlog": ["string"]
  }
}
Requirements:
- Use empty arrays when a section has no items.
- Keep findings evidence-based.
- For quick scans, include only Critical and High findings unless there are none.
- Never invent CVEs or package versions.
""".strip()


def governance_instruction(profile: str) -> str:
    if profile == "strict":
        return """
GOVERNANCE PROFILE: strict
- Treat this audit as a release gate, not an advisory report.
- Populate `governance_gate` with a final decision.
- Use `block` when there is any confirmed Critical or High finding, any committed secret, dangerous tool or shell exposure without guardrails, missing auth or authorization on sensitive surfaces, or untrusted data can reach a powerful tool, provider, or external system.
- Use `approve-with-conditions` when only Medium or Low findings remain but follow-up work is still required before broad rollout.
- Put merge-blocking remediation in `release_blockers` and mandatory next steps in `required_actions`.
""".strip()
    return """
GOVERNANCE PROFILE: standard
- Populate `governance_gate` with a practical decision for engineering teams.
- Use `approve-with-conditions` when non-blocking follow-up work is still needed.
""".strip()


def build_request_bundle(
    root: pathlib.Path,
    provider: str,
    model_name: str,
    audit_type: str,
    governance_profile: str,
    output_format: str,
    selected_paths: list[pathlib.Path],
    evidence: dict[str, Any],
    references: dict[str, str],
    user_message: str,
    system_prompt: str,
) -> dict[str, Any]:
    return {
        "generated_at": now_utc(),
        "provider": provider,
        "model_name": model_name,
        "audit_type": audit_type,
        "governance_profile": governance_profile,
        "output_format": output_format,
        "root": str(root),
        "selected_files": [display_path(path, root) for path in selected_paths],
        "detected_stacks": evidence.get("stacks", []),
        "references_loaded": list(references.keys()),
        "inventory": evidence.get("inventory", {}),
        "evidence": evidence,
        "system_prompt_characters": len(system_prompt),
        "user_prompt_characters": len(user_message),
        "prompt_preview": user_message[:3000],
    }


def json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def parse_json_response(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    stripped = text.strip()
    if not stripped:
        fail("model returned an empty response")

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except JSONDecodeError:
        pass

    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(stripped[index:])
        except JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    fail("could not parse JSON from the model response")
    raise AssertionError("unreachable")


def normalize_severity(value: Any) -> str:
    if not value:
        return "info"
    text = str(value).strip().lower()
    return text if text in SEVERITY_ORDER else "info"


def highest_confirmed_severity(findings: list[dict[str, Any]]) -> str:
    highest = "info"
    for finding in findings:
        if finding.get("status") == "suspected":
            continue
        severity = normalize_severity(finding.get("severity"))
        if SEVERITY_ORDER[severity] > SEVERITY_ORDER[highest]:
            highest = severity
    return highest


def default_governance_gate(findings: list[dict[str, Any]], governance_profile: str) -> dict[str, Any]:
    highest = highest_confirmed_severity(findings)
    if highest in {"critical", "high"}:
        decision = "block"
    elif highest in {"medium", "low"}:
        decision = "approve-with-conditions"
    else:
        decision = "approve"

    if governance_profile == "strict" and highest == "medium":
        decision = "approve-with-conditions"

    return {
        "decision": decision,
        "release_blockers": [],
        "required_actions": [],
        "deferred_risks": [],
        "notes": "",
    }


def normalize_result(
    raw: dict[str, Any],
    root: pathlib.Path,
    audit_type: str,
    provider: str,
    model_name: str,
    governance_profile: str,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for index, finding in enumerate(raw.get("findings") or [], start=1):
        if not isinstance(finding, dict):
            continue
        severity = normalize_severity(finding.get("severity"))
        start_line = finding.get("start_line") or finding.get("line") or 0
        end_line = finding.get("end_line") or start_line or 0
        normalized = {
            "id": finding.get("id") or f"SEC-{index:03d}",
            "status": str(finding.get("status") or "confirmed").lower(),
            "severity": severity,
            "confidence": str(finding.get("confidence") or "medium").lower(),
            "title": finding.get("title") or "Untitled finding",
            "category": finding.get("category") or "",
            "cwe_id": finding.get("cwe_id") or finding.get("cwe") or "",
            "cwe_name": finding.get("cwe_name") or "",
            "cvss_score": finding.get("cvss_score") or 0,
            "cvss_vector": finding.get("cvss_vector") or "",
            "file": finding.get("file") or "",
            "start_line": int(start_line) if str(start_line).isdigit() else 0,
            "end_line": int(end_line) if str(end_line).isdigit() else 0,
            "attack_scenario": finding.get("attack_scenario") or "",
            "impact": finding.get("impact") or "",
            "evidence": finding.get("evidence") or "",
            "fix_summary": finding.get("fix_summary") or finding.get("fix") or "",
            "verification": finding.get("verification") or "",
            "suggested_owner": finding.get("suggested_owner") or "",
        }
        findings.append(normalized)

    counts = Counter(normalize_severity(item["severity"]) for item in findings if item.get("status") != "suspected")
    summary = raw.get("summary") if isinstance(raw.get("summary"), dict) else {}
    overall_risk = normalize_severity(summary.get("overall_risk")) or highest_confirmed_severity(findings)
    if overall_risk == "info":
        overall_risk = highest_confirmed_severity(findings)

    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    governance_gate = raw.get("governance_gate") if isinstance(raw.get("governance_gate"), dict) else {}
    default_gate = default_governance_gate(findings, governance_profile)
    result = {
        "metadata": {
            "project_name": metadata.get("project_name") or root.name,
            "audit_mode": metadata.get("audit_mode") or audit_type,
            "provider": provider,
            "model_name": model_name,
            "governance_profile": governance_profile,
            "generated_at": now_utc(),
        },
        "summary": {
            "overall_risk": overall_risk,
            "executive_summary": summary.get("executive_summary") or "",
            "finding_count": {
                "critical": counts.get("critical", 0),
                "high": counts.get("high", 0),
                "medium": counts.get("medium", 0),
                "low": counts.get("low", 0),
                "info": counts.get("info", 0),
            },
        },
        "threat_model": raw.get("threat_model") if isinstance(raw.get("threat_model"), dict) else {
            "assets": [],
            "trust_boundaries": [],
            "entry_points": [],
            "attack_paths": [],
        },
        "findings": findings,
        "dependency_audit": raw.get("dependency_audit") if isinstance(raw.get("dependency_audit"), list) else [],
        "supply_chain": raw.get("supply_chain") if isinstance(raw.get("supply_chain"), list) else [],
        "cryptography_assessment": raw.get("cryptography_assessment")
        if isinstance(raw.get("cryptography_assessment"), list)
        else [],
        "security_headers": raw.get("security_headers") if isinstance(raw.get("security_headers"), list) else [],
        "positive_findings": raw.get("positive_findings") if isinstance(raw.get("positive_findings"), list) else [],
        "governance_gate": {
            "decision": str(governance_gate.get("decision") or default_gate["decision"]).lower(),
            "release_blockers": governance_gate.get("release_blockers")
            if isinstance(governance_gate.get("release_blockers"), list)
            else default_gate["release_blockers"],
            "required_actions": governance_gate.get("required_actions")
            if isinstance(governance_gate.get("required_actions"), list)
            else default_gate["required_actions"],
            "deferred_risks": governance_gate.get("deferred_risks")
            if isinstance(governance_gate.get("deferred_risks"), list)
            else default_gate["deferred_risks"],
            "notes": governance_gate.get("notes") or default_gate["notes"],
        },
        "remediation_roadmap": raw.get("remediation_roadmap") if isinstance(raw.get("remediation_roadmap"), dict) else {
            "immediate": [],
            "this_sprint": [],
            "backlog": [],
        },
    }
    return result


def render_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    metadata = result["metadata"]
    threat_model = result["threat_model"]
    findings = result["findings"]

    lines = [
        "# Security Audit Report",
        "",
        f"**Project:** {metadata['project_name']}",
        f"**Generated:** {metadata['generated_at']}",
        f"**Mode:** {metadata['audit_mode']}",
        f"**Provider:** {metadata['provider']} ({metadata['model_name']})",
        f"**Governance:** {metadata.get('governance_profile', 'standard')}",
        "",
        "## Executive Summary",
        summary.get("executive_summary") or "No executive summary provided.",
        "",
        "| Severity | Count |",
        "|---|---:|",
        f"| Critical | {summary['finding_count']['critical']} |",
        f"| High | {summary['finding_count']['high']} |",
        f"| Medium | {summary['finding_count']['medium']} |",
        f"| Low | {summary['finding_count']['low']} |",
        f"| Info | {summary['finding_count']['info']} |",
        "",
        f"**Overall Risk:** {summary['overall_risk'].title()}",
        f"**Gate Decision:** {result.get('governance_gate', {}).get('decision', 'approve-with-conditions').replace('-', ' ').title()}",
        "",
        "## Threat Model",
        "",
        "**Assets**",
    ]

    for item in threat_model.get("assets", []):
        lines.append(f"- {item}")
    if not threat_model.get("assets"):
        lines.append("- None provided")

    lines.extend(["", "**Trust Boundaries**"])
    for item in threat_model.get("trust_boundaries", []):
        lines.append(f"- {item}")
    if not threat_model.get("trust_boundaries"):
        lines.append("- None provided")

    lines.extend(["", "**Entry Points**"])
    for item in threat_model.get("entry_points", []):
        lines.append(f"- {item}")
    if not threat_model.get("entry_points"):
        lines.append("- None provided")

    lines.extend(["", "**Likely Attack Paths**"])
    for item in threat_model.get("attack_paths", []):
        lines.append(f"- {item}")
    if not threat_model.get("attack_paths"):
        lines.append("- None provided")

    lines.extend(["", "## Findings"])
    if not findings:
        lines.extend(["", "No confirmed findings were returned."])

    for finding in findings:
        lines.extend(
            [
                "",
                f"### {finding['id']} [{finding['severity'].upper()}] {finding['title']}",
                "",
                f"- Status: {finding['status']}",
                f"- Confidence: {finding['confidence']}",
                f"- CWE: {finding['cwe_id']} {finding['cwe_name']}".rstrip(),
                f"- CVSS: {finding['cvss_score']} {finding['cvss_vector']}".rstrip(),
                f"- Location: {finding['file']}:{finding['start_line']}",
                f"- Suggested owner: {finding['suggested_owner'] or 'Unassigned'}",
                "",
                f"**Attack Scenario**: {finding['attack_scenario'] or 'Not provided.'}",
                "",
                f"**Impact**: {finding['impact'] or 'Not provided.'}",
                "",
                f"**Evidence**: {finding['evidence'] or 'Not provided.'}",
                "",
                f"**Fix Summary**: {finding['fix_summary'] or 'Not provided.'}",
                "",
                f"**Verification**: {finding['verification'] or 'Not provided.'}",
            ]
        )

    lines.extend(["", "## Dependency Audit"])
    dependencies = result.get("dependency_audit", [])
    if dependencies:
        lines.extend(["", "| Package | Severity | Current | Fixed | CVE | Notes |", "|---|---|---|---|---|---|"])
        for item in dependencies:
            lines.append(
                "| {package} | {severity} | {current_version} | {fixed_version} | {cve} | {notes} |".format(
                    package=item.get("package", ""),
                    severity=item.get("severity", ""),
                    current_version=item.get("current_version", ""),
                    fixed_version=item.get("fixed_version", ""),
                    cve=item.get("cve", ""),
                    notes=item.get("notes", ""),
                )
            )
    else:
        lines.extend(["", "No dependency findings were returned."])

    lines.extend(["", "## Supply Chain"])
    if result.get("supply_chain"):
        lines.extend(f"- {item}" for item in result["supply_chain"])
    else:
        lines.append("- No supply-chain notes provided.")

    lines.extend(["", "## Cryptography Assessment"])
    if result.get("cryptography_assessment"):
        lines.extend(f"- {item}" for item in result["cryptography_assessment"])
    else:
        lines.append("- No cryptography notes provided.")

    lines.extend(["", "## Security Headers"])
    headers = result.get("security_headers", [])
    if headers:
        lines.extend(["", "| Header | Status | Notes |", "|---|---|---|"])
        for item in headers:
            lines.append(
                f"| {item.get('header', '')} | {item.get('status', '')} | {item.get('notes', '')} |"
            )
    else:
        lines.append("- No security header assessment provided.")

    lines.extend(["", "## Positive Findings"])
    if result.get("positive_findings"):
        lines.extend(f"- {item}" for item in result["positive_findings"])
    else:
        lines.append("- No positive findings provided.")

    governance_gate = result.get("governance_gate", {})
    lines.extend(["", "## Governance Gate", "", f"**Decision:** {governance_gate.get('decision', 'approve-with-conditions').replace('-', ' ').title()}"])
    if governance_gate.get("notes"):
        lines.extend(["", governance_gate["notes"]])

    lines.extend(["", "**Release Blockers**"])
    for item in governance_gate.get("release_blockers", []):
        lines.append(f"- {item}")
    if not governance_gate.get("release_blockers"):
        lines.append("- None")

    lines.extend(["", "**Required Actions**"])
    for item in governance_gate.get("required_actions", []):
        lines.append(f"- {item}")
    if not governance_gate.get("required_actions"):
        lines.append("- None")

    lines.extend(["", "**Deferred Risks**"])
    for item in governance_gate.get("deferred_risks", []):
        lines.append(f"- {item}")
    if not governance_gate.get("deferred_risks"):
        lines.append("- None")

    roadmap = result.get("remediation_roadmap", {})
    lines.extend(["", "## Remediation Roadmap", "", "**Immediate**"])
    for item in roadmap.get("immediate", []):
        lines.append(f"- {item}")
    if not roadmap.get("immediate"):
        lines.append("- None")

    lines.extend(["", "**This Sprint**"])
    for item in roadmap.get("this_sprint", []):
        lines.append(f"- {item}")
    if not roadmap.get("this_sprint"):
        lines.append("- None")

    lines.extend(["", "**Backlog**"])
    for item in roadmap.get("backlog", []):
        lines.append(f"- {item}")
    if not roadmap.get("backlog"):
        lines.append("- None")

    return "\n".join(lines) + "\n"


def render_sarif(result: dict[str, Any], root: pathlib.Path) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    seen_rules: set[str] = set()

    for finding in result["findings"]:
        if finding["status"] == "suspected":
            continue
        rule_id = finding["id"]
        if rule_id not in seen_rules:
            rules.append(
                {
                    "id": rule_id,
                    "name": finding["title"],
                    "shortDescription": {"text": finding["title"]},
                    "fullDescription": {"text": finding["evidence"] or finding["attack_scenario"] or finding["title"]},
                    "properties": {
                        "severity": finding["severity"],
                        "cwe_id": finding["cwe_id"],
                        "cvss_score": finding["cvss_score"],
                        "confidence": finding["confidence"],
                    },
                }
            )
            seen_rules.add(rule_id)

        level = "note"
        if finding["severity"] in {"critical", "high"}:
            level = "error"
        elif finding["severity"] == "medium":
            level = "warning"

        artifact_uri = finding["file"] or "."
        location: dict[str, Any] = {"artifactLocation": {"uri": artifact_uri}}
        if finding["start_line"]:
            location["region"] = {
                "startLine": finding["start_line"],
                "endLine": finding["end_line"] or finding["start_line"],
            }

        results.append(
            {
                "ruleId": rule_id,
                "level": level,
                "message": {"text": finding["fix_summary"] or finding["title"]},
                "locations": [{"physicalLocation": location}],
                "properties": {
                    "severity": finding["severity"],
                    "confidence": finding["confidence"],
                    "attack_scenario": finding["attack_scenario"],
                    "impact": finding["impact"],
                    "verification": finding["verification"],
                },
            }
        )

    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "web-security-review",
                        "version": "0.3.1",
                        "informationUri": "https://github.com/adams216/web-security-review-skill",
                        "rules": rules,
                    }
                },
                "originalUriBaseIds": {
                    "%SRCROOT%": {"uri": root.as_uri() + "/"},
                },
                "results": results,
            }
        ],
    }


def maybe_fail_threshold(result: dict[str, Any], threshold: str, governance_profile: str) -> int:
    decision = str(result.get("governance_gate", {}).get("decision") or "").lower()
    if governance_profile == "strict" and decision == "block":
        print("Strict governance gate blocked the review result.", file=sys.stderr)
        return 2

    threshold = normalize_severity(threshold) if threshold != "none" else "none"
    if threshold == "none":
        return 0
    highest = highest_confirmed_severity(result["findings"])
    if SEVERITY_ORDER[highest] >= SEVERITY_ORDER[threshold]:
        print(
            f"Fail threshold reached: highest confirmed severity is {highest}, threshold is {threshold}.",
            file=sys.stderr,
        )
        return 2
    return 0


def call_model(provider: str, model_name: str, system_prompt: str, user_message: str) -> str:
    if provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            fail("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI
        except ImportError:
            fail("openai package is not installed")
        client = OpenAI()
        response = client.chat.completions.create(
            model=model_name,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""

    if provider == "claude":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            fail("ANTHROPIC_API_KEY is not set")
        try:
            import anthropic
        except ImportError:
            fail("anthropic package is not installed")
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model_name,
            max_tokens=12000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "\n\n".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()

    if provider == "gemini":
        if not os.environ.get("GOOGLE_API_KEY"):
            fail("GOOGLE_API_KEY is not set")
        try:
            import google.generativeai as genai
        except ImportError:
            fail("google-generativeai package is not installed")
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        response = model.generate_content(user_message)
        return response.text

    fail(f"unsupported provider: {provider}")
    raise AssertionError("unreachable")


def write_output(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a web security audit.")
    parser.add_argument("--model", required=True, choices=["claude", "openai", "gemini"], help="Model provider")
    parser.add_argument("--model-name", help="Override the provider-specific model name")
    parser.add_argument("--dir", required=True, help="Repository or project directory")
    parser.add_argument("--type", default="quick", choices=["quick", "full", "single-file", "ci-check", "ai-agent"], help="Audit mode")
    parser.add_argument("--file", help="Target file for single-file mode")
    parser.add_argument("--output", default="SECURITY_REPORT.md", help="Output path")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json", "sarif"], help="Output format")
    parser.add_argument("--fail-on", default="none", choices=["none", "low", "medium", "high", "critical"], help="Exit non-zero if findings meet or exceed this severity")
    parser.add_argument("--governance-profile", default="standard", choices=["standard", "strict"], help="Set the review stance to advisory or release-gate mode")
    parser.add_argument("--max-files", type=int, default=200, help="Maximum number of files to include in the model context")
    parser.add_argument("--dry-run", action="store_true", help="Build the request bundle and skip the model call")
    parser.add_argument("--evidence-out", help="Optional path to write the collected evidence JSON")
    parser.add_argument("--scanner-timeout", type=int, default=20, help="Timeout in seconds per external scanner command")
    return parser.parse_args()


def default_model_name(provider: str, audit_type: str) -> str:
    defaults = {
        "claude": {
            "ai-agent": "claude-opus-4-5",
            "quick": "claude-sonnet-4-5",
            "full": "claude-opus-4-5",
            "single-file": "claude-sonnet-4-5",
            "ci-check": "claude-sonnet-4-5",
        },
        "openai": {
            "ai-agent": "gpt-4o",
            "quick": "gpt-4o-mini",
            "full": "gpt-4o",
            "single-file": "gpt-4o",
            "ci-check": "gpt-4o",
        },
        "gemini": {
            "ai-agent": "gemini-2.5-pro",
            "quick": "gemini-2.0-flash",
            "full": "gemini-2.5-pro",
            "single-file": "gemini-2.5-flash",
            "ci-check": "gemini-2.5-flash",
        },
    }
    return defaults[provider][audit_type]


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.dir).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        fail(f"directory not found: {root}")

    target_file = pathlib.Path(args.file).expanduser() if args.file else None
    provider = args.model
    model_name = args.model_name or default_model_name(provider, args.type)

    system_prompt, adapter = load_system_material(provider)
    evidence = collect_evidence.collect_evidence(
        root=root,
        audit_type=args.type,
        target_file=(root / target_file).resolve() if target_file and not target_file.is_absolute() else target_file,
        timeout=args.scanner_timeout,
    )

    if args.evidence_out:
        evidence_path = pathlib.Path(args.evidence_out).expanduser()
        if not evidence_path.is_absolute():
            evidence_path = root / evidence_path
        write_output(evidence_path, json_dumps(evidence) + "\n")

    selected_paths = select_paths(root, args.type, target_file, args.max_files)
    references = load_references(args.type, evidence.get("stacks", []), args.governance_profile)
    code_blocks = build_code_blocks(selected_paths, root)
    template = load_prompt_template(args.type)

    evidence_block = json_dumps(
        {
            "inventory": evidence.get("inventory", {}),
            "stacks": evidence.get("stacks", []),
            "scanners": evidence.get("scanners", []),
            "secret_scan": evidence.get("secret_scan", {}),
        }
    )

    reference_block = "\n\n".join(
        f"## Reference: {name}\n\n{text}" for name, text in references.items()
    )

    user_message = "\n\n".join(
        [
            template.strip(),
            schema_instruction(),
            governance_instruction(args.governance_profile),
            "LOCAL EVIDENCE:\n```json\n" + evidence_block + "\n```",
            "SUPPORTING REFERENCES:\n" + reference_block,
            "CODEBASE:\n" + code_blocks,
        ]
    )
    full_system_prompt = system_prompt + "\n\n" + adapter

    output_path = pathlib.Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = root / output_path

    if args.dry_run:
        bundle = build_request_bundle(
            root=root,
            provider=provider,
            model_name=model_name,
            audit_type=args.type,
            governance_profile=args.governance_profile,
            output_format=args.format,
            selected_paths=selected_paths,
            evidence=evidence,
            references=references,
            user_message=user_message,
            system_prompt=full_system_prompt,
        )
        write_output(output_path, json_dumps(bundle) + "\n")
        print(f"Dry-run bundle saved to: {output_path}")
        return 0

    raw_response = call_model(provider, model_name, full_system_prompt, user_message)
    parsed = parse_json_response(raw_response)
    normalized = normalize_result(parsed, root, args.type, provider, model_name, args.governance_profile)

    if args.format == "json":
        write_output(output_path, json_dumps(normalized) + "\n")
    elif args.format == "sarif":
        sarif = render_sarif(normalized, root)
        write_output(output_path, json_dumps(sarif) + "\n")
    else:
        write_output(output_path, render_markdown(normalized))

    print(f"Saved report to: {output_path}")
    return maybe_fail_threshold(normalized, args.fail_on, args.governance_profile)


if __name__ == "__main__":
    raise SystemExit(main())
