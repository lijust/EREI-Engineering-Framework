# EREI Eval Adapter Protocol V1

## Goal

Allow the same EREI eval suite to execute against different coding-agent/model runtimes without changing the canonical case definition.

The transport is deliberately minimal: one JSON request on stdin, one JSON response on stdout.

## Request

```json
{
  "protocol_version": "1.0",
  "suite_id": "impact-analysis-v1",
  "case_id": "T-001",
  "artifact": "skills/impact-analysis",
  "input": {
    "prompt": "..."
  },
  "context": {},
  "tags": ["trigger", "security"]
}
```

### Required request fields

- `protocol_version`
- `suite_id`
- `case_id`
- `artifact`
- `input`

`context` and `tags` are optional convenience fields populated by the runner.

## Response

Minimum valid response:

```json
{
  "output": "agent-visible result"
}
```

Recommended normalized response:

```json
{
  "output": "...",
  "metadata": {
    "risk": "L3",
    "selected_workflow": "security-critical-change"
  },
  "trace": [
    {"type": "tool", "name": "impact-analysis"},
    {"type": "tool", "name": "threat-model"}
  ]
}
```

## Rules

1. Adapter writes protocol JSON only to stdout.
2. Diagnostic logs should go to stderr.
3. Non-zero process exit means adapter execution failure, not an eval assertion failure.
4. `output` is required.
5. `metadata` must be a JSON object when present.
6. `trace` must be an array when present.
7. Tool steps should use:

```json
{"type": "tool", "name": "tool-or-skill-name"}
```

8. Adapters may include additional fields; Core ignores unknown response fields.
9. Secrets/API keys are runtime configuration and must never be embedded in eval cases.
10. Adapter behavior must not alter the expected semantics of the target framework artifact merely to satisfy a test.

## Why CLI instead of a Python interface?

A CLI/JSON boundary is language-neutral. An adapter may be implemented in Python, JavaScript, Go, shell, or another runtime and can wrap external tools such as Promptfoo or Inspect AI.

## Future protocol evolution

Breaking changes require a new `protocol_version`. Core should prefer additive response fields when possible.