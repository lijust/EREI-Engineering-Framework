# Core13 P1-A — project-pinned capability activation source preview

**Status: OFFLINE SOURCE-BOUND PILOT — NOT PRODUCTION DISPATCH.**
This PR depends on draft PR #117 (and, transitively, #116/#115). It changes
neither the frozen PR98 scorer nor the original Gemini provider responses.

## Integration

```text
project .erei/framework.json + .erei/CANDIDATE_CAPABILITIES.json
             + Framework CAPABILITIES.json
             + clean loaded Framework git revision
                          |
          existing capability_activation.resolve_activation()
                          |
        typed AI action → learning_proposal_runtime.evaluate_proposal()
                          |
               in-memory preview ONLY
```

`tools.learning_proposal_activation_source.evaluate_activation_from_project(
proposal, project_root, capability, now=<aware UTC-comparable datetime>)`

- Does not accept model-provided registry, adoption document, project pin,
  `trusted_context`, loaded Framework SHA, or output state.
- Loads sources from the project's existing manifest/adoption paths and
  the Framework's existing registry, checks Framework checkout cleanliness
  and exact loaded ref, and delegates the policy decision to the unchanged
  existing activation resolver.
- Requires an explicit timezone-aware observation clock for deterministic
  trial expiry; does not use Gemini's suggested time.
- Seeds a **simulation** with resolver-derived status and an empty executions
  list. That execution history is a test projection, **not** project truth.
- Checks the local source-file digests and loaded Framework revision after
  the preview to reject observed mid-read source changes. These are *local*
  consistency checks, not signatures or independently verified provenance.
- Candidate without adoption stays dormant; branch-pinned activation is
  blocked; wrong capability/version/mode/reason is denied. Stable need
  not have a candidate adoption record.
- Never invokes a real capability, writes files, registers adoption,
  changes a project manifest, closes a review or records a model PASS.

## Safety boundary

The local project path, capability name, and replay clock are supplied by
the trusted application caller, not established or independently attested
by this adapter. A malicious local actor capable of replacing complete
self-consistent files or changing records after preview remains outside the
pilot's threat model. This result MUST NOT authorize external execution.
Use the production `capability_activation.require_active()` gate at the
actual dispatch boundary with identity/permissions/approval controls.

## Synthetic test matrix

- Source-bound stable allow with unchanged source files.
- Candidate without adoption deny and block; exact bounded candidate
  adoption allow in isolated synthetic fixture.
- Mutable project pin blocks activation.
- Wrong capability/version, forged context and invalid manifest deny.
- Dirty Framework checkout denies before policy evaluation.
- Observed concurrent registry change denies the preview.
- Missing project identity or timezone-aware clock denies.

```text
python -m unittest evals.tests.test_learning_proposal_activation_source -v
```

Exit is **source-only** after CI and independent review. This is not
cryptographic authentication, real execution verification, learning
effectiveness evidence, independent acceptance or Stable readiness.

Remaining P1-B: bind review findings / Development Output intervention
identity to prospective task occurrences and measure actual learning
exposure, recurrence and baseline, not hypothetical model-success rates.
