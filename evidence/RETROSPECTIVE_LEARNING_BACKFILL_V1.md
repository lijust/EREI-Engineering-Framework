# Retrospective Learning Backfill V1 — Candidate Evidence

## Purpose
Provide a controlled path to reconstruct historical engineering-task learning events from durable repository evidence without pretending reconstructed history has the same quality as prospective capture.

## Core guarantees
- `capture_mode = retrospective` is mandatory.
- evidence quality is explicit: `confirmed`, `reconstructed`, or `inferred`.
- source references are mandatory.
- private reasoning, credentials, customer payloads, and large raw transcripts are forbidden.
- retrospective events are stored separately from prospective `TASK_EVENTS.jsonl`.
- retrospective events do not automatically advance prospective learning thresholds or close learning epochs.
- inferred fields cannot silently become confirmed.
- backfill is additive and fail-closed.

## Intended first validation
EREI-App-Google historical PR/CI evidence is the first target corpus. The project currently contains a dense sequence of architecture, performance, security, migration, PostgreSQL-adapter, and runtime-verification tasks with durable PR and CI evidence.

## Promotion boundary
This file records Candidate evidence only. Stable promotion requires branch CI for the backfill validator/tests and the normal Framework regression suite.
