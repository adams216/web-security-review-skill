# OWASP Micro Prompt: Injection

Use this when you want a focused review for SQL, NoSQL, command, template, header, and log injection.

```text
Review the provided code only for injection-class vulnerabilities.

Focus on:
- SQL and NoSQL query construction
- command execution and shell invocation
- template and server-side template injection
- header injection and log injection

Trace user-controlled input to dangerous sinks across files.
Ignore unrelated best-practice findings.

For each confirmed issue include:
- severity
- CWE
- file and line
- exact exploit path
- safe fix
- short verification step
```
