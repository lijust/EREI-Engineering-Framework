# ADR-0006 — Explicit Candidate Capability Activation

**Status:** Accepted for Candidate evaluation; Stable promotion requires normal release/architecture governance  
**Date:** 2026-10-15  
**Risk:** L3 — Cross-project governance and activation boundary

## Context

Stable and Development-line Candidate capabilities can coexist in one immutable Framework commit. A project may pin such a commit to evaluate one Candidate or consume another change. Without a separate activation boundary, pin movement could silently authorize every Candidate asset present in that commit.

This is incompatible with the intended release split between **Task Learning V2 Core** and **Learning Operations V1**.

## Decision

1. Candidate presence is dormant by default.
2. Candidate activation is project-local through `.erei/CANDIDATE_CAPABILITIES.json`.
3. Candidate activation requires an exact 40-character commit pin and a loaded Framework checkout matching that pin.
4. Adoption binds exact capability/version, evidence, risk, approval and expiry.
5. Candidate trials may not exceed 30 days.
6. Stable registry capabilities do not require Candidate adoption.
7. Routers must resolve Candidate activation before use.
8. Framework pin movement alone never activates Candidate capabilities.
9. Stale/expired/ref-mismatched/version-mismatched adoptions fail closed.

## Consequences

This creates explicit project authority, bounded experiments, reproducible release-scope separation, and rollback by removal/expiry. It adds one project-local record and one deterministic activation check.

## Rejected alternatives

- **All capabilities in the pinned commit are active:** rejected because presence would become authority.
- **Put temporary adoption state inside framework.json:** rejected because it couples stable integration identity to trial churn.
- **Use chat memory as approval:** rejected because activation evidence must be durable and project-owned.

## Promotion boundary

This ADR authorizes Candidate implementation/evaluation only. It does not change the Stable Framework release or any project pin.
