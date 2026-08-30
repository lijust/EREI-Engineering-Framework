# Impact Analysis Evals

**Status:** Draft V1

These cases test trigger selection, proportionality, boundary detection, and risk routing.

## Trigger cases

### T-001 — Should trigger: auth flow
**Prompt:** Change login so users can sign in with Google and access only their company data.

Expected:
- Trigger impact-analysis.
- Identify authentication, authorization, tenant isolation, backend, data/session, frontend, QA/release implications.
- Provisional risk at least L3.
- Recommend security review/threat model.

### T-002 — Should trigger: cross-layer search
**Prompt:** Make search instant by caching results in the browser and backend.

Expected:
- Trigger impact-analysis.
- Identify frontend state, backend cache behavior, stale data, authorization scope, performance, observability.
- Do not assume cache is safe across users/tenants.
- Likely L2, higher if shared tenant/user cache boundaries change.

### T-003 — Should trigger: schema change
**Prompt:** Split customer name into first_name and last_name across the existing application.

Expected:
- Trigger impact-analysis.
- Identify schema/data migration, backend contracts, frontend forms, exports/reports, compatibility and rollback.
- L2 or L3 depending migration/production state.

### T-004 — Should trigger: apparently small concurrency fix
**Prompt:** Replace the request sequence counter with Date.now() so stale searches stop failing after refresh.

Expected:
- Trigger at least lightweight impact analysis because request ordering/state semantics change.
- Identify frontend state, backend stale-request validation, collision/ordering assumptions, tests.
- Avoid classifying purely by diff size.

## Should-not-trigger full analysis

### N-001 — Cosmetic copy
**Prompt:** Change the button text from Search to Find Projects.

Expected:
- No full impact-analysis if confirmed presentation-only.
- L0 local verification.

### N-002 — Isolated CSS
**Prompt:** Increase modal border radius from 8px to 12px.

Expected:
- No full impact-analysis.
- L0.

## Behavior cases

### B-001 — Frontend security rationalization
Input scenario:
A role proposes hiding the Admin button for brokers and says this enforces permission.

Expected:
- Identify frontend as untrusted.
- Require server-side authorization.
- Raise security implication and reject the rationalization.

### B-002 — Tenant cache
Input scenario:
A shared backend cache key is based only on search parameters, not tenant/user scope.

Expected:
- Identify possible cross-tenant leakage.
- Raise to L3/security-critical until scope isolation is proven.
- Recommend Security role + security-review.

### B-003 — Over-routing check
Input scenario:
A local non-functional CSS adjustment with known isolation.

Expected:
- Do not recommend Backend, Security, Data, Performance, Architect, and Release roles unnecessarily.
- Prefer minimal path.

### B-004 — Unknown brownfield assumption
Input scenario:
The request modifies an existing payment calculation but current persistence and rounding behavior have not been inspected.

Expected:
- Mark current behavior unknown.
- Route to discovery/inspection before material implementation.
- Do not invent the existing rule.

## Regression eval policy

Any real project incident traced to a missed impact class should create a new permanent case here or in a machine-readable eval harness once implemented.