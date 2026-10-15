# Candidate Capability Adoption Workflow V1

**Status:** Candidate V1

## Core invariant

**Capability presence is not capability activation.**

A capability with `status: candidate` in `CAPABILITIES.json` is dormant for a project unless deterministic activation evidence passes. Stable capabilities do not require Candidate adoption records.

## Project-owned record

Candidate trials are recorded in:

```text
.erei/CANDIDATE_CAPABILITIES.json
```

Absence of this file, or an empty `adoptions` array, means all Candidate capabilities are dormant.

Each adoption binds the exact Framework commit, exact capability/version, approval time, mandatory expiry, approving role, risk, purpose, and durable evidence.

Maximum Candidate trial window: **30 days**. Renewal requires a new reviewed adoption record.

## Risk

Default: **L2**. Raise to **L3** when the Candidate affects architecture, security/data boundaries, release authority, identity/authorization, destructive mutation, or Framework governance.

## Procedure

1. Confirm the project is pinned by exact immutable commit SHA.
2. Confirm the loaded Framework checkout is **clean** (including untracked files) and is that exact project pin.
3. Read `CAPABILITIES.json`; freeze the Candidate name/version.
4. Define purpose, expected effect, success metrics, rollback/removal path, and trial cohort.
5. Obtain approval appropriate to the risk.
6. Add exactly one adoption entry for the capability.
7. Run `python tools/capability_activation.py --target <project> --capability <name>`.
8. Run required project regression/security/data gates.
9. Invoke the Candidate only when resolution returns `ACTIVE_CANDIDATE`.
10. Expiry, removal, ref drift, or version drift returns the Candidate to dormant/blocked state.

## Fail-closed conditions

Do not activate when the project pin is not an exact commit, the loaded checkout is dirty or differs from the project pin, the adoption is missing/invalid, no matching adoption exists, the version differs, approval is future-dated, adoption is expired, trial exceeds 30 days, duplicate adoptions exist, or evidence is missing.

## Upgrade boundary

Moving a project pin to a commit that contains Candidate assets **does not activate them**. Existing Candidate adoptions must be revalidated against the new exact ref/version.

## Promotion boundary

Project Candidate adoption does not promote the Framework capability, change registry status, authorize other projects, move Stable, or move project pins automatically.
