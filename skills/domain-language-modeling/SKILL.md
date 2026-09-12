---
name: domain-language-modeling
description: Establish and maintain a canonical project domain vocabulary, resolve overloaded or conflicting terms, and keep specs/code/tests aligned with durable business concepts without turning the glossary into implementation documentation. Use when domain terms are ambiguous, inconsistent, or materially affect requirements, interfaces, data, or tests.
---

# Domain Language Modeling

**Status:** Stable V1

## Objective

Keep humans, agents, specs, code, tests, and durable project context aligned on the same business/domain concepts.

The goal is not more documentation. The goal is less ambiguity.

## Canonical artifact

Use a project-local glossary only when useful:

```text
.erei/DOMAIN_LANGUAGE.md
```

Create it lazily when the first material term requires durable clarification. Do not create an empty glossary during bootstrap merely for completeness.

The glossary contains **domain language**, not implementation details, file names, provider APIs, temporary task notes, or generic software vocabulary unless that vocabulary has project-specific meaning.

## Trigger when

Use when:

- one term is being used for multiple business concepts,
- multiple terms are being used for one important concept,
- accepted requirement language conflicts with code/data/test language,
- a new business concept is being introduced into the architecture or data model,
- a term materially affects authorization, ownership, lifecycle, money, identity, status, or workflow meaning,
- reviewers/agents repeatedly need to re-derive what a project-specific term means,
- a domain contradiction appears during discovery, design, implementation, or review.

## Do not trigger when

- wording is incidental and cannot change behavior,
- the term is standard implementation detail with no project-specific meaning,
- a one-off local variable name can be corrected directly,
- adding a glossary entry would create bureaucracy without reducing ambiguity.

## Required inputs

Use available:

- `.erei/PROJECT_PROFILE.md`,
- `.erei/DATA_MODEL.md`,
- `.erei/ARCHITECTURE.md`,
- accepted specs/requirements,
- relevant code/tests,
- ADRs,
- user-confirmed domain decisions,
- existing `.erei/DOMAIN_LANGUAGE.md` if present.

Durable project evidence outranks remembered assumptions.

## Procedure

### 1. Identify the ambiguous or load-bearing term

Record:

- term currently used,
- contexts where it appears,
- possible meanings,
- behavioral/data/authority consequences of choosing the wrong meaning.

### 2. Check existing durable truth

Before inventing a definition, inspect current project artifacts and code behavior.

Classify the state:

- `DEFINED_AND_CONSISTENT`,
- `DEFINED_BUT_VIOLATED`,
- `AMBIGUOUS`,
- `CONFLICTING_SOURCES`,
- `NEW_TERM`.

### 3. Sharpen overloaded language

Prefer one canonical term per material concept where practical.

Examples:

- distinguish CRM `Client` from authenticated `User`,
- distinguish business `Request` from HTTP `Request`,
- distinguish real-estate `Project` from software `Project`,
- distinguish `Developer` company from software `Developer` role when both exist in the same context.

Do not force unnatural vocabulary merely for theoretical purity. The chosen term must be usable by the domain expert and the codebase.

### 4. Stress-test with concrete scenarios

Use small scenarios that expose meaning differences.

For example:

> A broker creates a lead who has never signed into the application. Is that person a Client, a User, both, or neither?

A term is not resolved if edge cases reveal contradictory behavior.

### 5. Cross-check against code/data/tests

When the declared domain meaning disagrees with implemented behavior, surface the contradiction explicitly.

Do not silently rewrite the glossary to match code, and do not silently rename code to match a newly proposed term.

Classify whether the mismatch is:

- documentation drift,
- implementation bug,
- requirement change,
- unresolved domain decision.

Then route through the appropriate workflow.

### 6. Update the glossary immediately after resolution

For each material term record a concise structure such as:

```markdown
## Client

**Meaning:** A business-side person or organization receiving advisory/brokerage service.

**Not:** An authenticated application User unless the same real person also has an account.

**Key relationships:** May have zero or more Requests; may map to zero or one User identity depending on product flow.
```

Keep definitions implementation-neutral unless an implementation constraint is itself part of the domain contract.

### 7. Propagate canonical language proportionately

When safe and in scope, use the canonical term in new:

- specs,
- public module/interface names,
- tests,
- data-model descriptions,
- review findings.

Do not trigger broad renaming migrations automatically. Existing code rename work requires impact/risk analysis and normal approval.

### 8. Use ADRs sparingly

A glossary definition alone is not an ADR.

Create/propose an ADR only when the associated decision is all of:

- materially costly to reverse,
- non-obvious to future maintainers,
- the result of a real trade-off among alternatives.

## Required output

```text
Term/concept:
Current usage locations:
Current state:
Competing meanings:
Behavioral/data/authority consequence:
Canonical definition:
Explicit non-meaning:
Relationships/invariants:
Code/data/test contradictions:
Required propagation:
ADR required: yes | no
Open domain questions:
Glossary artifact updated: yes | no
```

## Evidence requirements

Definitions must distinguish:

- user-confirmed domain truth,
- existing project-document truth,
- observed implementation behavior,
- proposed terminology.

Do not present a proposed term as accepted truth until the underlying ambiguity is resolved by authoritative evidence or authorized decision.

## Rationalizations to reject

- "The agent can infer what Client means from context."
- "The code uses this word, therefore the domain must mean the same thing."
- "Put every technical acronym in the glossary."
- "Rename the whole codebase immediately for consistency."
- "A glossary entry needs an ADR."
- "Two conflicting definitions can coexist if everyone knows the context."

## Definition of Done

A material ambiguous concept has one evidence-backed canonical meaning, important non-meanings/relationships are explicit, contradictions are surfaced rather than hidden, the glossary is updated only when useful, and any resulting implementation/architecture change is routed through normal EREI governance.
