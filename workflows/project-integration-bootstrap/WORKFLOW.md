# Project Integration Bootstrap Workflow

**Status:** Stable V1 — governed by ADR-0002

## Mission
Integrate an existing or new software repository with the pinned EREI Engineering Framework without overwriting project truth, inventing architecture, or coupling the project to one agent runtime.

## Trigger
Use when:
- a project first adopts EREI Engineering Framework,
- an existing project needs formal `.erei/` project context,
- a project integration is being repaired or upgraded,
- a Framework pin/overlay declaration must be established.

Do not use as a substitute for `new-project` product discovery or `brownfield-onboarding`; compose them as appropriate.

## Primary roles
- Chief Engineer — owns routing/risk/gates.
- System Architect — reviews project boundary and integration fit.
- Security Engineer — required when existing auth/tenant/security assumptions are discovered or changed.
- Data Engineer — required when source-of-truth/data ownership is uncertain or materially changed.
- QA Engineer — verifies integration artifacts and non-overwrite behavior.

## Inputs
Minimum:
- target project repository,
- project lifecycle state (greenfield/brownfield/unknown),
- current Framework stable baseline,
- exact Framework ref candidate,
- available project code/docs/configuration,
- known runtime/technology stack where evidenced.

## Procedure

### 1. Inspect before writing
Check for existing:
- `AGENTS.md`,
- `.erei/`,
- architecture/security/data docs,
- ADR directories,
- project-specific agent instructions,
- Framework integration manifests.

Do not assume an empty bootstrap target.

### 2. Determine lifecycle path
- **Greenfield:** compose with `new-project` workflow to establish project facts.
- **Brownfield:** compose with `brownfield-onboarding` and `project-standard-discovery` before converting observed conventions into durable rules.
- **Unknown:** inspect first; do not guess.

### 3. Select Framework pin
Read the Framework stable baseline and choose an exact ref.

For Candidate/Stable project integration:
- prefer immutable commit SHA or immutable tag,
- reject a mutable branch-only pin as reproducibility evidence.

A development experiment may track a branch temporarily if explicitly labeled non-stable.

### 4. Select overlays from evidence
Enable only overlays supported by the project stack and task reality.

Examples:
- Apps Script/Google Sheets project → `google-apps-script`.
- Plain Python service → do not load Apps Script overlay.

Do not enable overlays merely because they exist.

### 5. Run bootstrap dry-run
Use `tools/bootstrap_project.py --dry-run` or equivalent adapter behavior.

Review:
- planned files,
- conflicts,
- framework ref/baseline,
- selected overlays,
- target path.

### 6. Resolve conflicts fail-closed
If project files already exist:
- do not overwrite silently,
- inspect and merge conceptually,
- preserve project truth,
- require explicit replacement only when intentional and safe.

`--force` is not a conflict-resolution strategy by itself.

### 7. Create integration skeleton
Canonical V1 target:

```text
AGENTS.md
.erei/
├── framework.json
├── PROJECT_PROFILE.md
├── ARCHITECTURE.md
├── SECURITY_MODEL.md
├── DATA_MODEL.md
├── PERFORMANCE_BUDGET.md
├── PROJECT_RULES.md
└── feedback/
    ├── README.md
    └── FRAMEWORK_FEEDBACK.md
adr/
└── ADR_TEMPLATE.md
```

`FRAMEWORK_FEEDBACK.jsonl` is created on first feedback capture rather than as an empty machine ledger.

### 8. Replace placeholders with evidence
The generated templates are scaffolding, not completed project truth.

Populate project documents from:
- existing code/config,
- deployment/runtime evidence,
- user-confirmed decisions,
- authoritative project docs,
- accepted ADRs.

Mark unknowns explicitly.

### 9. Validate project-local boundaries
Confirm:
- project facts stay in project repo,
- Framework Core is referenced rather than copied by default,
- project rules do not silently weaken the pinned Constitution,
- auth/tenant/data boundaries are represented where relevant,
- performance budgets are project-specific and measurable where possible,
- project feedback is stored locally and cannot silently mutate Framework Core or the Framework pin.

### 10. Verify integration
Minimum deterministic checks:
- `.erei/framework.json` parses and satisfies schema,
- all manifest-referenced paths exist,
- Framework repository/baseline/ref are populated,
- stable integration does not rely only on mutable branch ref,
- no unintended pre-existing file was overwritten,
- `AGENTS.md` points to project and Framework truth rather than duplicating it,
- enabled overlays match evidenced stack,
- `.erei/feedback/README.md` and `.erei/feedback/FRAMEWORK_FEEDBACK.md` exist for new V1 feedback-aware integrations.

### 11. Brownfield convergence
For existing codebases, compare generated context against inspected reality.

Do not call integration complete while project docs contradict actual code/runtime without recording that drift.

### 12. Produce integration report
Required output:
- project/repository,
- lifecycle path,
- Framework baseline/ref,
- overlays,
- files created/updated/preserved,
- conflicts encountered,
- evidence sources,
- unknowns,
- risk level,
- next onboarding/discovery actions.

## Risk routing

### L0/L1
Documentation-only correction inside an already integrated project with no boundary change.

### L2
Normal first-time integration using the accepted contract without changing project architecture/security/data boundaries.

### L3
Required if integration establishes or changes:
- auth/tenant boundary,
- source-of-truth architecture,
- cross-project Framework contract,
- mutable-vs-immutable release policy,
- project architecture not already approved.

### L4
Destructive replacement of established project governance or production-critical integration with material irreversible risk.

## Stop conditions
Stop/escalate when:
- Framework ref cannot be resolved,
- target project identity is ambiguous,
- overwrite conflicts are unresolved,
- existing instructions conflict materially with Constitution,
- security/data ownership cannot be established for a requested structural change,
- generated project facts would require invention.

## Definition of Done
- Integration manifest valid.
- Framework pin reproducible for stable state.
- Project context files exist and are evidence-backed or explicitly marked unknown.
- Feedback scaffolding exists for new feedback-aware integrations.
- Existing project truth preserved.
- Applicable overlays selected proportionally.
- Required brownfield/new-project workflow completed or queued.
- No unresolved blocking conflict.
- Verification evidence recorded.
