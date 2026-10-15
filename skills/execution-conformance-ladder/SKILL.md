---
name: execution-conformance-ladder
description: Determine the minimum evidence ladder required before promoting static, generic-runtime, exact execution-environment, managed-provider, exact-target-runtime, or convergence claims. Use when shell/runtime/provider semantics can change behavior or when earlier proof has been contradicted by a later environment.
---

# Execution Conformance Ladder

**Status:** Candidate V1

## Objective

Prevent evidence from a weaker execution layer from silently satisfying a stronger runtime claim.

## Ladder

Use only the rungs relevant to the claim:

1. **SOURCE_STATIC** — syntax, source contracts, schemas, deterministic static analysis.
2. **GENERIC_RUNTIME** — behavior on a representative engine/runtime not bound to the deployment environment.
3. **EXACT_EXECUTION_ENVIRONMENT** — exact OS/shell/runtime family and material version/toolchain semantics.
4. **MANAGED_PROVIDER** — provider-managed roles, identity, lifecycle, limits and service behavior.
5. **EXACT_TARGET_RUNTIME** — the exact target resource/deployment/runtime identity where the claim matters.
6. **CONVERGENCE** — repeated/read-back observations when provider state or asynchronous behavior can remain ambiguous after one execution.

A higher rung is not automatically required for every task. The required rung follows from the engineering claim and risk.

## Trigger when

- source/static or generic tests passed but exact environment later disagreed;
- shell/process stdout, stderr, exit status, quoting, path or encoding semantics affect control flow;
- managed provider behavior differs from a generic engine;
- release evidence is being promoted from local proof to provider/production claims;
- runtime identity, deployment identity, role semantics, quotas or eventual consistency matter;
- Task Learning shows a verification escape attributable to environment/provider mismatch.

## Do not trigger when

- a local/cosmetic change has no environment-sensitive behavior;
- the current evidence rung already exactly matches the claim;
- the user is asking only for source analysis with no runtime claim.

## Procedure

1. State the exact claim being accepted.
2. Identify the strongest evidence currently available.
3. Identify environment/provider semantics that could falsify the claim.
4. Select the minimum required rung.
5. For exact execution environment, bind at minimum the material OS/shell/runtime/tool versions and native process stream/exit-code behavior when relevant.
6. For managed provider/exact target, bind identity/resource/version/deployment evidence.
7. Keep weaker-rung evidence as useful support, but never relabel it as stronger proof.
8. If a stronger rung cannot be exercised, mark the item deferred/blocked rather than inventing equivalence.
9. Record convergence requirements only when one observation cannot resolve provider state reliably.

## Required output

```text
Claim:
Current evidence rung:
Required evidence rung:
Why stronger proof is or is not required:
Environment/provider semantics at risk:
Exact identities/versions to bind:
Required test/read-back:
Deferred/blocked evidence:
Acceptance decision:
```

## Rationalizations to reject

- "It passed on PowerShell 7, so Windows PowerShell 5.1 is equivalent."
- "The generic database engine supports it, so the managed provider does too."
- "The API shape is the same, so runtime semantics are the same."
- "Static proof is enough because the runtime step is inconvenient."
- "One successful provider observation always proves convergence."

## Definition of Done

The accepted claim is bound to the weakest sufficient—but not weaker—evidence rung, material environment/provider semantics are explicit, missing stronger evidence remains visible, and no runtime authority is implied by analysis alone.
