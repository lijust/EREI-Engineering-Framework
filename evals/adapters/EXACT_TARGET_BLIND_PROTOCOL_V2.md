# Exact-Target Blind Adapter Request Protocol V2

**Scope:** `evals/exact_target_run.py` only (external behavioral runtime); independent model-boundary evidence, not the V2 Stable run-manifest schema.

The generic reference-contract harness still supports the separately documented **V1 request protocol** at `evals/adapters/PROTOCOL.md`. **V2 is an intentionally incompatible transport version** because it replaces canonical suite/case identifiers with randomized opaque one-use identifiers and removes case tags.

```json
{
  "protocol_version": "2.0",
  "suite_id": "blind-suite-0123456789abcdef",
  "case_id": "blind-case-fedcba9876543210",
  "artifact": "skills/impact-analysis",
  "input": {"prompt": "..."},
  "context": {}
}
```

The six fields above are exact. Opaque identifiers are unpredictable and generated per invocation, not derived from known case identities. Scorer criteria, case tags, canonical suite/case IDs and case score results stay strictly on the harness side.

A V1 adapter must **not** be treated as a V2-compatible model runtime. V2 adapters must explicitly validate `protocol_version == "2.0"`. The Copilot adapter rejects V1 and unknown protocol versions.

This upgrade does **not** affect the schema version of run evidence; the current digest-only run manifest is V1 and still **does not satisfy Stable V2 reconstructibility and provenance requirements**. Never infer Stable eligibility from passing V2 transport tests.

No live Copilot token use, external CLI execution, RC freeze or Stable promotion is authorized by this protocol.

For the 13 Core cases, `input.response_contract` declares
`erei-action-simulation-v1`. The request may expose operation interfaces and
scenario facts, but never private expected state or `reference_actions`. The
typed response is a proposed in-memory simulation, not a tool trajectory. See
[`../BEHAVIORAL_SIMULATION.md`](../BEHAVIORAL_SIMULATION.md). Transport tests and
synthetic fixtures do not constitute independent model evidence.
