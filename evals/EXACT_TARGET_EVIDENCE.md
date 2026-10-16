# Exact-target runtime evidence — Reconstructible V2 candidate

The published 75 reference-contract cases (including one harness-only case) do **not** constitute independent-model evidence. The blind exact-target request transport uses protocol V2 with unique opaque IDs. Scorer expectations and canonical case identities remain harness-only.

## Three-file governed evidence package

1. `exact-target-run.json` — exact target revision, adapter identity, runtime identity evidence, and a **retained normalized response** for every executed behavioral case; schema V2.
2. `execution-evidence.json` — V2 scored case rows with exact refs to the manifest.
3. `runtime-identity.json` — provenance of exact release carrier, target/tree, model, CLI package/version/hash, Actions run/attempt, destinations and SHA-256 of first two files.

`tools/exact_target_evidence.py` reconstructs and re-scores responses against the published behavioral cases, validates digests and rejects stale identities or mismatched outcomes. `tools/import_exact_target_evidence.py` checks the package in a temporary non-Git staging area before reserving and writing the three original files. Git history binding then requires their **first add in one direct first-parent commit** above the carrier and forbids later mutation.

Only exact frozen scope `releases/VNEXT_RELEASE_SCOPE.json` (currently Task Learning V2 Core plus Candidate Activation governance, 13 behavioral cases) belongs in the Stable release gate. Separate general-eval coverage remains 74 external behavioral cases; do not assume that reference-oracle 75/75 PASS is model behavior.

**Release note:** this is source-only engineering until manual, explicit runtime authorization, credential and package identity binding, genuine independent execution, verified enforcement and target-bound Architecture/Security approvals exist. A passing unit test alone is not Stable evidence.
