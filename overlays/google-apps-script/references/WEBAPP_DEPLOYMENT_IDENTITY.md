# Apps Script Web App Deployment and Identity

**Source baseline:** official Apps Script Web Apps documentation, verified 2026-08-31.

## Platform choices

Apps Script web apps can execute with different effective authority depending on deployment configuration, including executing as the deploying/owner identity or as the user accessing the web app.

This is not a cosmetic deployment setting. It changes the trust/permission model.

## Engineering rules

### WD-001 — Record execute-as model in the project security model
Every production web app must explicitly document:
- who can access the deployment,
- which identity the server executes as,
- which user identity is used for application authorization,
- which Google service permissions are available,
- how tenant/user membership is resolved.

### WD-002 — Execute-as-owner does not authorize application users
If the script runs with owner/deployer authority, the backend may be able to access resources more broadly than the caller. Application-level authorization becomes even more important.

### WD-003 — Execute-as-user does not eliminate application authorization
Google identity/OAuth establishes an effective user context but does not automatically implement EREI/product roles, tenant membership, object ownership, or business permissions.

### WD-004 — Granular OAuth denial is a runtime state
When executing as accessing user, individual scopes may not be granted. Check required authorization state before relying on service access and provide explicit error/recovery behavior.

### WD-005 — Never transmit server OAuth token to browser
Official Google guidance warns that tokens obtained through `ScriptApp.getOAuthToken()` can grant access to data. Keep them server-side.

### WD-006 — Development and stable deployments are separate
The `/dev` test deployment runs the latest saved code for editors and is intended for development/testing. Do not equate testing `/dev` with production deployment verification.

### WD-007 — Production promotion needs deployment/version evidence
Record:
- deployment ID/version,
- candidate commit/version relation,
- execute-as/access configuration,
- verification result,
- rollback target.

### WD-008 — Ownership/domain movement can affect deployments
Web-app ownership/domain/shared-drive changes can require redeployment or alter operational behavior. Treat ownership/deployment authority as operational configuration, not incidental metadata.

### WD-009 — Client-visible function names are not access control
Even when a server function is not used by current UI flow, top-level callable functions must enforce their own security/business rules.

## Threat-model questions

For every Apps Script web app ask:
- Does server authority exceed caller authority?
- How is the caller identified?
- How is application role resolved?
- How is tenant resolved?
- Can a caller invoke server function directly through client API even if UI hides it?
- Which Google data/services can the execution identity access?
- What happens if OAuth scope is missing/revoked?
- What deployment config change could silently alter authority?

## Verification

Security/release verification should include:
- expected authorized role succeeds,
- unauthorized role fails server-side,
- wrong-tenant/object access fails,
- direct call bypassing UI fails when unauthorized,
- deployment identity/access settings match documented baseline,
- missing OAuth scope has controlled behavior where applicable,
- stable deployment version is the one actually verified.