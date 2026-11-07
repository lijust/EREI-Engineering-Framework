# Core13 PILOT-A — A2 real secondary Docker GET-only evidence & A3 closure review packet

**7 November 2026 | Evidence captured; A3 owner post-run sign-off PENDING.**
**Scope:** fixed Core13 PILOT-CLOSE v1, Package A only. This is **not** Stable acceptance or model code execution authorization.

## Verified actual GitHub run

The owner `lijust` previously recorded [G3 owner approval, comment #6708853149](https://github.com/lijust/EREI-3.2/issues/307#issuecomment-6708853149), then explicitly dispatched [owner-manual workflow #42418179869](https://github.com/lijust/EREI-3.2/actions/runs/42418179869), using the already reviewed GET-only inputs.

| Job / control | Actual result |
|---|---|
| `nonroot-source-and-offline-deny`, Job `128540689948` | **SUCCESS**; 28 A2 + 29 A1 + 30 A0 + 21 governance = **108/108 PASS** |
| `owner-manual-real-secondary-dockerd-getonly`, Job `128540730256` | **SUCCESS**; reviewed owner-manual root test actually executed |
| Owner root job final decoded log | `CORE13_PILOT_A2_REAL_SECONDARY_GET_ONLY_OWNER_SCOPED_PASS_NOT_TERMINAL` |
| Unexpected failed steps | **None reported** |
| Source file Git blob reviewed in workflow | `3fe19020b46fcffb6b49ab9885cd3d3e00c74a39` (`tools/core13_pilot_a2_owner_real_dockerd_getonly_hold.py`) |
| A2 review PR | [EREI-3.2 #314](https://github.com/lijust/EREI-3.2/pull/314) |
| Framework companion | [Framework #174](https://github.com/lijust/EREI-Engineering-Framework/pull/174) |

The owner-run workflow first checked that the local source matched the exact reviewed Git blob and that transitive dependencies matched their reviewed Git blobs before sudo. The root process then passed its own fixed GET-only assertions, returned its scoped result, and the nonroot postcondition checker validated the result. **The raw root-owned HMAC secret/receipt was not uploaded as a public artifact**; job evidence comprises the source-bound observations and success/failure predicates in the workflow logs. GitHub artifacts list was empty; do not claim a separate archival independent attestation.

## A2 scoped positive witnesses confirmed by the successful job assertions

The root script, under the reviewed source SHA, checks all of the following before producing a positive result:

1. Private disposable secondary `dockerd` created under a newly generated /run root, with private socket `0600`, root-owned source/Socket and private daemon PID/host boot-id/start-ticks binding. The secondary driver/root and initial inventory are checked.
2. Distinct real nonroot `runner` Controller, `nobody` Worker, and `daemon` Verifier identities; controller/worker denied key, proxy, daemon socket and receipt access.
3. Root-owned Unix proxy validates `SO_PEERCRED` exact verifier PID/UID/GID. Verifier attempts one `POST /containers/create`, which must return `DENIED` **without being sent to Docker**, then executes **two allowed real secondary-daemon** `GET /containers/json?all=1` reads via the proxy. Source directly checks the backend returns the genuine empty inventory `[]`.
4. Root script also checks initial and final secondary inventories (four enumerated GETs total, excluding helper health/info reads), daemon identity stability, host-default Docker data-root and host container IDs before vs after.
5. Local nonce/HMAC receipt binds the verifier UID and the real daemon process identity; the private receipt is reread and checked by Root. **This HMAC is NOT independently secured against Root**.
6. Exact private scratch-root removal asserted **after** root subprocess completes by `assert not os.path.lexists('/run/'+temporary_root_name)` in the owner job. No source-authorized image pull, CREATE/START/DELETE or model-generated code was executed. No claims about global host-wide Docker exclusivity follow from these checks.

These are **scoped source-and-log-backed assertions**, not an additional independent out-of-band test of the root host, nor general proof for other Docker transports, accounts, daemons or restarts.

## Negative witnesses / historical defects

- Pre-review A0/A1 nonroot tests: strict GET allowlist, wrong expected peer identity, rejected POST/START/DELETE, foreign CID/query, timeout, oversized packet, `SCM_RIGHTS`, symlink/permissions; successful CI Job `128540689948` confirms regressions at the reviewed run.
- Earlier owner test [#42385635445](https://github.com/lijust/EREI-3.2/actions/runs/42385635445) failed without diagnostic; diagnostic R1 changed only fail-closed reason reporting.
- Second owner test [#42386762635](https://github.com/lijust/EREI-3.2/actions/runs/42386762635) failed with `PROXY_VERIFIER_GET / A2_FD_OR_OVERSIZE_PACKET_DENIED`. R2 fixed a too-strict Linux `recvmsg` returned-flags check, preserving denial of truncation/unknown flags/ancillary FDs; final successful owner run #42418179869 verifies the tested correction.
- Package A root-cause remediation budget consumed **2/2**. **No third automatic remediation or new F5B1-letter** is permitted.

## Exact A2 and A3 closure decision

**A2 technical acceptance:** `A2_REAL_SECONDARY_GET_SCOPED_VERIFIED` from the successful reviewed owner-manual job. No further runtime engineering work needed for the narrowly scoped GET-only objective.

**A2 formal GATE_PASS:** **PENDING** explicit owner **post-run** review decision in [Package A issue #308](https://github.com/lijust/EREI-3.2/issues/308), per v1 contract. The earlier dispatch is authorization to run, not post-run signoff. Until owner decision, do not set `A2.state=GATE_PASS`.

**A3 evidence-packet review:** all required positive/negative witnesses, source/run/job, host-baseline and cleanup claims, risk boundaries, rollback/failed-run history and stop budget have been assembled in this document. `A3_GATED_PASS` and `A=CLOSED_PASS` also require a **post-run owner approval**, not an automatic GitHub SUCCESS result. One scoped review comment can explicitly approve **A2, A3 and Package A** together after inspecting these cited sources/logs; it must NOT approve Stable/AI execution. **B must remain NOT_STARTED until Package A is formally closed.**

### Scope limitations not waived

```text
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
PILOT_DECISION=UNDECIDED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_ESTABLISHED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
EXTERNALLY_INDEPENDENT_ROOT_KEY_CUSTODY=NOT_ESTABLISHED
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
```

This is an **A2 scoped read-only secondary Docker verifier success**, not a production or autonomous-execution certificate. The A3 review is the finite final task for Package A. No repeat of A2 is needed based solely on the results above.
