# EREI APP Google — Brownfield Integration Validation V1

**Status:** PASS with follow-up integration note  
**Project:** `lijust/EREI-App-Google`  
**Framework baseline:** `project-integration-bootstrap-v1`  
**Framework immutable ref:** `fd5942feb925d35a410ae945057bd6a8c4841384`

## Purpose

Record the first real brownfield application of EREI Engineering Framework Project Integration Bootstrap V1.

This evidence exists to validate whether the Framework integration model works against an already-governed project rather than only against generated fixtures.

## Existing project state discovered before write

The project already had durable governance including:

- GitHub as source-code SSOT,
- Apps Script as runtime/deployment target,
- V9.5.3 stable modularization source baseline,
- 26/26 TEST-V1 behavioral regression requirement,
- explicit security/tenant/idempotency/stale-ordering/row-version/error invariants,
- zero-behavior-change V10 modularization charter,
- explicit release and rollback process,
- project `AGENTS.md`, documentation index, and ADRs 0001–0005.

The integration therefore had to preserve existing project truth rather than replace it with Framework templates.

## Integration performed

A dedicated project branch added:

- `.erei/framework.json`,
- `.erei/PROJECT_PROFILE.md`,
- `.erei/ARCHITECTURE.md`,
- `.erei/SECURITY_MODEL.md`,
- `.erei/DATA_MODEL.md`,
- `.erei/PERFORMANCE_BUDGET.md`,
- `.erei/PROJECT_RULES.md`,
- project ADR-0006 for Framework integration,
- additive Framework bootloader instructions in the existing `AGENTS.md`.

The project enabled only the `google-apps-script` overlay. No runtime adapter was enabled because no Runtime Adapter baseline was Stable at the time.

## Safety observations

The integration:

- did not modify runtime source,
- did not push to Apps Script HEAD,
- did not create or repoint a deployment,
- did not modify V10 migration implementation,
- did not weaken project security/data/release invariants,
- did not overwrite the project's historical documentation manifest,
- used an immutable Framework commit rather than `main`.

## Review result

Project integration PR #2 contained only project governance/context integration and was merged into project `main`.

Project merge commit:

`4284fdf6c41b73120b7ce368c88340ad21b5c01b`

The long-lived `refactor/v10-modular` branch predated the Framework integration. A follow-up note was added to its PR requiring it to incorporate updated `main` before Framework-dependent work relies on the new project integration state.

## Framework lessons validated

### Confirmed useful

1. **Additive brownfield onboarding** — existing project truth can remain canonical while `.erei/` provides routed context.
2. **Immutable Framework pin** — project engineering policy is reproducible.
3. **AGENTS as bootloader** — existing project rules can be preserved while adding Framework load order.
4. **Technology overlay selection** — only relevant platform guidance needs enabling.
5. **Project-specific ADR continuity** — Framework integration can be recorded inside the project's existing ADR sequence.
6. **Separation from runtime release** — governance integration can land without changing application/runtime deployment state.

## Gaps exposed

1. **Framework upgrade workflow was missing.** Once the project is pinned, a safe standardized mechanism is required to move the pin to a newer Framework revision.
2. **Runtime adapter layer remains incomplete.** The project can declare adapters, but no Stable adapter was available yet.
3. **Long-lived project branches need an explicit policy for incorporating Framework integration changes from the default branch.** This can be handled by project Git/release workflow rather than by forcing branch mutation from Framework Core.

## Conclusion

Project Integration Bootstrap V1 passed its first brownfield validation without requiring project runtime changes or replacement of established project governance.

The highest-priority reusable follow-up is the Framework Upgrade Workflow, followed by Runtime Adapter architecture and additional brownfield validation on projects with different stacks/governance maturity.
