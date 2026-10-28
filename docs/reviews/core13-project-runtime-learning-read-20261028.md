# Core13 P1-D — opt-in project runtime read-boundary (no provider execution)

**Purpose:** supply one actual project-local, source-activation-gated API
for project-owned task runners. Unlike the earlier synthetic-only trace
reference CLI, this API accepts a real integrated project's path and
observes a read of that project's own .erei/knowledge file. No project or
external provider is automatically run. CI remains entirely synthetic.

## Public Python integration

```python
from datetime import datetime, timezone
from tools.learning_project_runtime_bridge import ProjectKnowledgeReadSession

session = ProjectKnowledgeReadSession(
    project_root, occurrence_id, intervention_id, implementation_ref,
    capability="learning_pattern_analysis",
    now=datetime.now(timezone.utc),
)

# Integrate at the project/agent's *real data-read call site*.
knowledge_bytes = session.read("approved-knowledge.txt", expected_sha256)

# The project must pass bytes to its existing task executor, execute the
# task, independently verify terminal outcome and capture the actual
# Task Learning occurrence using its existing authorized capture workflow.
# That work is NOT performed or claimed by this integration API.

receipt = session.finalize_after_capture(
    intervention_v1, prospective_selection_v1, exact_framework_trace_ref
)
```

The constructor resolves the existing `.erei/framework.json`, candidate
adoption document, Framework `CAPABILITIES.json`, clean Framework Git
checkout and exact loaded Framework SHA using the existing authoritative
`capability_activation.resolve_activation()`. It allows only
`ACTIVE_STABLE` or `ACTIVE_CANDIDATE`, never authorizes based on the
existence of code alone. Allowed capabilities are explicitly bounded
to `learning_pattern_analysis` and `framework_effectiveness_measurement`.
An aware caller-provided clock is mandatory, but is **not sufficient by itself**
for live eligibility: at session opening its timestamp must be within five
minutes of the local UTC system clock. Every read and finalization rechecks
capability activation with a **fresh UTC clock value**, so a Candidate cannot
be kept active with an old supplied timestamp after its adoption expires.
More than five seconds of local clock rollback fails closed. The machine
clock is still **not independently authenticated time evidence**.

Read uses the prior `KnowledgeReadObserver`, which pins actual bytes to a
provided SHA-256 digest and denies traversal, symlinked trust roots, empty or
oversized files. Session re-checks activation documents, loaded SHA and
Framework cleanliness before and after the read, and at finalization.

The session refuses an occurrence already terminal before the knowledge read,
and rechecks it immediately before and after the read. Its `trace_ref` must
also equal the exact loaded Framework checkout SHA. These guards prevent a
post-hoc read from being attached to an already completed task or a different
Framework revision. They do not provide independent time-of-use attestation.

Finalization requires an already captured, unique Task Learning occurrence
with exact matching Framework revision/project repository. It then calls the
existing PR #119 complete-cohort gate and PR #120 per-task trace join.
No intervention or Task Learning files are written by this API. If a failed
task is omitted from the intervention cohort, finalization denies instead of
producing an artificially favorable effectiveness statistic. Missing
observations or terminal events do not generate fabricated successes.

## Explicit limitations

- A source-bound local read is **not** independent proof that a model or
  runner used the returned bytes meaningfully, or that an AI learned.
- Candidate adoption records are project files; local activation checks are
  not independent identity attestations, cryptographic audit or Stable.
- The caller still chooses the project root, observation time, project
  task execution code, actual terminal event, and exposure declaration.
- An authorized consumer must handle task failures and record every task,
  including exceptions/timeouts. The observer cannot ensure external runners
  cannot bypass it.
- No runtime tasks in a real user project were executed in this PR; there is
  **no independently authenticated real exposure/outcome evidence yet**.
- The session only links a read/trace to an existing local task event.
  It neither dispatches a capability nor opens a provider connection.

`observed_read_delivered_to_caller=true` means returned bytes were read
and supplied to the local caller, **not** that an external model used them.
`consumer_use_verified=false`,
`learning_exposure_independently_verified=false`,
`effectiveness=NOT_ESTABLISHED`,
`causation=NOT_ESTABLISHED` and `stable_ready=false` remain unchanged.

## QA

```text
python -m unittest evals.tests.test_learning_project_runtime_bridge -v
```

Synthetic tests cover stable candidate/expired/no adoption, branch/incorrect
Framework pins, dirty checkout, source mutation, real local read to captured
task, missing terminal occurrence, missing failed tasks and revision mismatch.
No actual project writes, Gemini calls, private data or PR98 scorer changes.

Stacked draft PR #123 → #122 → #121 → #120 → #119 → #118 → #117 → #116 → #115.
Keep out of production/Stable until independently reviewed and a selected
real project explicitly enables the instrumented read seam.
