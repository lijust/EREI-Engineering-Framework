# Retrospective Learning Backfill — Eval Cases

1. Reject retrospective event without source references.
2. Reject `capture_mode != retrospective` in retrospective ledger.
3. Preserve `inferred` evidence quality; never auto-promote it.
4. Keep retrospective events out of prospective threshold counts.
5. Allow repeated high-quality reconstructed evidence to seed a review candidate, not a direct Framework mutation.
6. Reject secrets, private reasoning, customer payloads, and oversized raw transcripts.
7. Re-running import is idempotent for the same source identity/fingerprint.
8. A changed historical source reference creates a new reviewed event rather than overwriting the prior event.
