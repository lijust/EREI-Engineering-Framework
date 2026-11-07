# Core13 Pilot-A2 — second manual root FAIL, exact kernel cause, R2/2 bounded remediation

**Date:** 2026-11-07. **Package:** A, no additional F5B1 stage. **Status:** A2 BLOCKED pending one owner-manual final review run; no new remedial cycle permitted automatically.

## Evidence from the owner's second manual run

Owner-dispatched [Actions #42386762635](https://github.com/lijust/EREI-3.2/actions/runs/42386762635) followed the recorded [G3 owner approval](https://github.com/lijust/EREI-3.2/issues/307#issuecomment-6708853149).

| Job | ID | Result |
|---|---|---|
| Nonroot tests | `128445685369` | 105/105 PASS |
| Actual owner-manual root fixture | `128445731294` | **FAIL (exit 2)** |

The privileged decoded log establishes **exactly**:
```text
A2_OWNER_MANUAL_BLOCKED_STAGE=PROXY_VERIFIER_GET
A2_OWNER_MANUAL_BLOCKED_CODE=A2_FD_OR_OVERSIZE_PACKET_DENIED
```
This localizes the failure to Root Proxy's `recvmsg` validation, **not** to a proven Docker backend GET failure. There is **no evidence of a completed real secondary Docker GET through the protected proxy** or full cleanup acceptance from this failed run.

## Root cause and narrowly scoped R2/2 correction

The previous implementation compared `flags == 0` after:
```python
raw, ancillary, flags, _ = conn.recvmsg(
    MAX_PACKET + 1, socket.CMSG_SPACE(4 * 4), socket.MSG_CMSG_CLOEXEC
)
```

On Linux, a perfectly valid `AF_UNIX/SOCK_SEQPACKET` receipt may report **`MSG_CMSG_CLOEXEC` (0x40000000)** in returned flags, even when there are **zero ancillary descriptors** and no truncated payload. A separate real Linux `socketpair(SOCK_SEQPACKET)` check reproduced this exact returned value; the latest GitHub CI now contains a genuine kernel-level regression that asserts it. `flags == 0` incorrectly rejected all such benign requests.

**Fix:** Accept **only** the known harmless `MSG_CMSG_CLOEXEC` and `MSG_EOR` flag bits, and still reject *any* other flags (including `MSG_TRUNC` and `MSG_CTRUNC`). Continue rejecting **every ancillary control message**, closing any `SCM_RIGHTS` FDs before failure, enforcing exact peer PID/UID/GID, payload size bounds, and GET-only path allowlist. The fix does not broaden Docker API methods, source authority, or root dispatch permissions.

- Fixed A2 source Git blob: `3fe19020b46fcffb6b49ab9885cd3d3e00c74a39`.
- CI regression for true Linux `MSG_CMSG_CLOEXEC`, genuine truncation denial and a **three-request live Unix proxy** using **FAKE Docker backend** (one POST denied + two GET allowed). No Docker daemon involved in CI.
- [CI #42387019699](https://github.com/lijust/EREI-3.2/actions/runs/42387019699) — nonroot job `128446443573` **SUCCESS**: 28 A2 + 29 A1 + 30 A0 + 21 Governance = **108/108 PASS**; owner-manual Root job SKIPPED by design.
- The review and CI still do **not** prove real Docker behavior. Root HMAC custody is not independent of Root; `INDEPENDENT_TERMINAL_SETTLEMENT` and `LATE_CREATE_QUIESCENCE` remain NOT_ESTABLISHED.

## Hard-stop / gate disposition

**Package A remediation budget is now R2/2.** R1 exposed the swallowed privileged error code; R2 fixes the root cause localized by the second manual run and adds real-kernel regression coverage.

One final **explicit owner-manual dispatch** may check the reviewed R2 candidate. No automatic dispatch or reusing previous source SHA. If it succeeds, review its decoded logs, cleanup, peer boundaries and real daemon GET evidence and then decide A2/A3 scoped closure. If it fails, **stop remediation, close Package A evaluation as CLOSED_NO_GO or CLOSED_BLOCKED**, and record reason. A third code correction or new F5B1 letter is not allowed without a separately approved change request (not implied by a request to continue).

**Current official status:** G0–G3 + A0 + A1 = **6/16 evidence-backed gates**; A2 BLOCKED; A3/B/C NOT_STARTED. `AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`, `stable_ready=false`.
