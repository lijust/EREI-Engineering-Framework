---
name: exclusive-claim-analysis
description: Analyze one-time, singleton, lease, lock, migration, deployment, recovery, or authority-claim designs to distinguish attempt identity from real mutual exclusion and verify atomic acquisition, ownership/fencing, recovery and release semantics.
---

# Exclusive Claim Analysis

**Status:** Candidate V1

## Objective

Prevent designs from confusing a unique attempt identifier with exclusive authority.

## Core rule

**Uniqueness of attempts is not mutual exclusion.**

Two actors can each create a different random UUID/ref/file and both believe they won. Exclusive authority requires all competitors to contend on the same canonical claim or on an equivalent atomic serialization primitive.

## Trigger when

- an operation must execute at most once or have only one active owner;
- a workflow uses random refs/UUIDs/files/markers as a "lock";
- migrations, project creation, deployment, recovery, payment/usage commit, leader election, or destructive maintenance need singleton authority;
- a lease/lock exists and stale-owner behavior matters;
- Task Learning shows a concurrency/race verification escape.

## Procedure

### 1. Separate identities

Identify independently:

- **attempt identity** — journal/audit identity for one actor's attempt;
- **claim identity** — canonical resource/key all competitors contend on;
- **owner identity** — actor/session/principal admitted by the claim;
- **resource identity** — exact object/deployment/database/project being protected.

Do not collapse these into one random identifier.

### 2. Prove atomic acquisition

Require one operation whose success/failure serializes competitors, such as:

- compare-and-set / conditional create on one canonical key,
- database uniqueness/transactional lock,
- provider-supported lease/lock,
- Git ref creation/update on one stable claim ref with conflict semantics,
- another mechanism with equivalent atomicity.

"Check then create" is not atomic unless the underlying primitive guarantees it.

### 3. Bind downstream authority

No mutation may proceed merely because an attempt record exists.

Bind authority to the successfully acquired claim and, where stale ownership is possible, use an ownership token/generation/fencing value that old owners cannot reuse.

### 4. Define lifecycle

Specify:

- acquisition,
- renewal if leased,
- expiry if applicable,
- success closeout,
- failure closeout,
- crash recovery,
- stale-owner handling,
- safe retry,
- audit/journal preservation.

### 5. Test adversarially

At minimum reason/test:

- two concurrent contenders,
- winner crash after claim but before mutation,
- stale loser resumes,
- retry after ambiguous result,
- release/reacquire,
- claim state mismatch/tamper,
- resource identity mismatch.

## Required output

```text
Protected singleton operation:
Attempt identity:
Canonical claim identity:
Atomic acquisition primitive:
Owner/fencing identity:
Protected resource binding:
Concurrent-contender result:
Crash/recovery semantics:
Release/expiry semantics:
Adversarial checks:
Decision:
```

## Rationalizations to reject

- "UUIDs never collide, so only one actor can proceed."
- "Each actor creates its own unique ref, so that is a lock."
- "We check whether a marker exists before creating ours."
- "The first actor should usually finish before the second starts."
- "Audit identity proves authority."

## Definition of Done

Every contender races on one real exclusion primitive, downstream authority is bound to the admitted claim, stale/recovery semantics are explicit, and attempt journaling remains separate from mutual exclusion.
