# Core13 D2D3B2B0 — actual Trivy + CycloneDX image vulnerability scan and independent admission HOLD

**2026-11-05 | Evidence from App owner-manual run #41973874199. Framework reusable security contract.**

## Actual verified owner-run facts

- [App Actions #41973874199](https://github.com/lijust/EREI-3.2/actions/runs/41973874199): completed **SUCCESS**; `workflow_dispatch`, correct **branch-specific** job `exact-fixed-image-remote-only-sbom-and-vulnerability-report`, exact SHA `11963371f13ee73b404af0a6a5f3200bec4b404d`, 2026-11-05 05:25 UTC. All scanning/SBOM/upload job steps passed. This is **success of evidence collection**, not security acceptance: `exit-code: '0'` intentionally reports vulnerabilities without failing the job.
- It scanned by Trivy `0.70.0` with `TRIVY_IMAGE_SRC=remote`; pulled vulnerability DB from `mirror.gcr.io/aquasec/trivy-db:2`. No Docker image/container START, no model/user code. Exact source-pinned image `python@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159`. Scanner identified Debian `13.7` and image environment `PYTHON_VERSION=3.12.16`.
- [Raw GitHub artifact #13390747650](https://github.com/lijust/EREI-3.2/actions/runs/41973874199/artifacts/13390747650): `trivy-vulns.json` 1,001,383 bytes SHA256 `871235bdbd8b654ea15b607a6932d41bda717b6c9450a1cd84e3acbf010ae1a7`; `trivy-sbom.cdx.json` 195,249 bytes SHA256 `1a33cbb5200552573e6a208c30bf9b81221a2c6a4282cb7dd4f92011fdfac4de`; `source-admission-hold.json` 1,924 bytes SHA256 `8de41ef01ee5b25ec36b21e3e04f613e6f874d5bb28f667d09effb270c50163e`. Hashes were independently checked by re-reading the downloaded ZIP. CycloneDX SBOM 1.6 covers **89 components** (88 library, one OS).

## Findings: package/CVE matches are not unique CVEs

| Severity | Debian OS package matches | Python package matches | Total |
|---|---:|---:|---:|
| CRITICAL | 0 | 0 | **0** |
| HIGH | 47 | 0 | **47** |
| MEDIUM | 72 | 5 | **77** |
| LOW | 62 | 1 | **63** |
| UNKNOWN | 6 | 0 | **6** |
| **Total** | **187** | **6** | **193** |

There are **10 distinct HIGH CVE IDs**, not 47 distinct HIGH vulnerabilities: 36 of the HIGH matches are four util-linux CVEs each repeated against nine related packages. The entire report contains **92 distinct CVE IDs** over 193 package matches. Among the 47 HIGH package matches: 44 `affected` with no fixed version recorded by Trivy, 2 `fixed` with available `apt/libapt-pkg7.0` `3.0.4` against installed `3.0.3`, one `fix_deferred` for `perl-base`. The `fixed` status **does not mean patched in the scanned digest**.

Distinct HIGH IDs and match counts: `CVE-2026-76642` (9); `CVE-2026-78408` (9); `CVE-2026-78409` (9); `CVE-2026-78410` (9); `CVE-2025-69720` (4); `CVE-2026-109518` (2); `CVE-2026-16742` (2); `CVE-2026-119373` (1, SQLite); `CVE-2026-54369` (1); `CVE-2026-9538` (1, Perl). Do not equate HIGH severity to verified exploitability of a specific sandbox deployment, but do not infer image safety from zero CRITICAL.

## Mandatory engineering response and reusability

1. **Do not authorize Docker START** for this currently reviewed fixed Python digest. A successful owner-run scanner with `exit-code: '0'` means reporting succeeded, **not** that a security severity gate passed. Keep the exact raw scan, CycloneDX and SHA256 evidence in GitHub for reproducibility. Do not fabricate approval.
2. Evaluate a refreshed immutable image or a minimal trusted test image, with independently checked OS/package advisories and actually applicable exploit prerequisites; treat new image digest as a **separate reviewed candidate**. Run the remote scan again on exact candidate digest, record vulnerability DB timestamp, supported architecture, SBOM provenance and diff of high CVEs/packages. Do not silently update F4C2 image reference to a mutable tag or immediately START it.
3. Independently verify image risk acceptance and route ownership. The new scan demonstrates **source-level CVE findings**, not independent L3 vulnerability attestation or release approval.
4. **Separate blockers remain:** F4C2 root test broker has `0666` filesystem socket (with kernel peer restrictions but inadequate future default permissions); actual root/private Docker broker full lifecycle is not implemented, F5 SQLite `creation_quiescence_barrier_proven=false` and `late_async_create_excluded=false`, external transport/daemon-epoch/future callbacks unresolved; old J4/J4S still have direct host Docker authority. No untrusted AI code, all model-effectiveness gates still HOLD.

**Enforced invariant:** `docker_image_current_scan_evidence_collected=true` **only for this archived scanner output**, `docker_image_digest_and_cve_accepted=false`, `docker_image_sbom_independently_attested=false`, `docker_broker_start_attach_stream_verified=false`, `docker_broker_durable_f5_intent_integrated=false`, `docker_broker_real_inflight_create_quiescence_proven=false`, `independent_l3_verification_complete=false`, `worker_isolation_certified=false`, `untrusted_code_execution_authorized=false`, `stable_ready=false`, `decision=BLOCK_AI_ACCEPTANCE`.

**Portable engineering lesson:** GitHub Actions completed SUCCESS is distinct from image policy acceptance. De-duplicate by CVE when interpreting scanner totals, but retain package-match counts for actual remediation planning. A pinned digest guarantees *identity*, not *security*. A proper gate needs authenticated source/SBOM + independent risk acceptance and separate F5 runtime quiescence.
