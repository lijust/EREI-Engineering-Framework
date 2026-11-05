# Core13 Framework — D2D3B2B1 owner-real Trivy comparison and governed image risk decision

**5 November 2026. Actual evidence verified, not an L3 sign-off or Docker capability grant.**

## Real reproducible source collection

Owner-run [App GitHub Actions #42027751135](https://github.com/lijust/EREI-3.2/actions/runs/42027751135) completed **SUCCESS**, `workflow_dispatch`, branch `core13/j5-04f4d2d3b2b1-pinned-candidate-image-comparison-20261105`, source SHA `93922e264ca1fe4859ca1d3eb0f4fc9543d7eae5`, 2026-11-05 12:30–12:31 UTC. Exactly three source-allowlisted image-variant jobs were SUCCESS, not the default-main fail-closed registration stub. Each completed 26 source-only tests, resolved the Docker Hub OCI index and verified **unique linux/amd64 leaf content digest**, remote-scanned that **immutable digest** with Trivy, generated a CycloneDX SBOM and uploaded raw evidence. Artifacts have been downloaded and independently re-counted/hashed from the actual raw JSON. No Docker container, root broker, candidate/model code or project writes ran.

Baseline owner-run [#41973874199](https://github.com/lijust/EREI-3.2/actions/runs/41973874199) at 2026-11-05 05:25 UTC: current source-pinned Debian 13.7 Python 3.12.16 image **0 CRITICAL / 47 HIGH / 77 MEDIUM / 63 LOW / 6 UNKNOWN per-package Trivy findings**, 10 distinct HIGH CVE identifiers, 89 SBOM components. **Seven-hour scanner-time difference is a methodological confound**: future approval-grade comparisons should re-scan this baseline using the same Trivy DB snapshot/time as candidates, not treat small differences as strictly caused by OS/image content.

## Direct actual scan results for candidate linux/amd64 leaf digests

| Candidate | Immutable image digest | Critical | High matches | Medium | Low | Unknown | Distinct High CVEs | CycloneDX components |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Existing fixed Debian 13.7 | `sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159` | 0 | **47** | 77 | 63 | 6 | 10 | 89 |
| Slim Trixie Debian 13.7 | `sha256:05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177` | 0 | **46** | 77 | 63 | 6 | 10 | 89 |
| Slim Bookworm Debian 12.15 | `sha256:0f086103b026048cc50cb5da25ec435c023c5241a83fc44daea593377abc61c4` | **2** | **37** | 122 | 106 | 6 | 12 | 107 |
| Alpine 3.24.3 | `sha256:69ebe56e2a764c399514a0a6117131cb730cc4d0e71e85c08deb9af74cbb9f41` | **0** | **0** | **5** | **1** | **0** | **0** | **40** |

Raw artifacts: [Trixie #13413838848](https://github.com/lijust/EREI-3.2/actions/runs/42027751135/artifacts/13413838848), [Bookworm #13415060670](https://github.com/lijust/EREI-3.2/actions/runs/42027751135/artifacts/13415060670), [Alpine #13413629794](https://github.com/lijust/EREI-3.2/actions/runs/42027751135/artifacts/13413629794). Raw scan JSON SHA256: Trixie `52f428aa52c6fb41ed3451ee9beac0fb9d66412d882fb1da85046fca00e6501a`, Bookworm `2b1934cf7100730bf368dc95118a3150e6de8fcdd24205fed5e048f61be3fda0`, Alpine `bc480de8fba5d0dae41e1efec0ec1ff1fa1a2a6514b4e01f31c9383c5f0b1a64`. Corresponding CycloneDX SHA256: `24e853f21fef3593d9039e25dc8ffb0091b8314665d1d3e815b089bcd70b17dd`, `65e07b4f4bd34ca5cb1dd4ce4c311a37e9759a325bea827dfefb5d9a3c39e3ac`, `2c8f6d6d9b4291165a751697b7a674fdf97ad81c5862a1e74053848b68c7e38d`.

### Relevant false shortcuts explicitly prohibited

- **Bookworm:** Fewer HIGH package matches than baseline (37 vs 47) do NOT mean lower overall severity. Its raw Trivy JSON has **two CRITICAL** results: `CVE-2025-7458` in `libsqlite3-0` installed `3.40.1-2+deb12u2` (Trivy status affected) and `CVE-2023-45853` in `zlib1g` installed `1:1.2.13.dfsg-1` (Trivy status will_not_fix). Therefore keep Bookworm out of the immediate shortlist.
- **Trixie:** 46 HIGH matches / 10 unique HIGH identifiers and same 89-component SBOM as baseline is nearly unchanged. Baseline `CVE-2026-109518` disappears but `CVE-2026-76844` appears. Scanner timing makes a one-match delta inconclusive as an image effect.
- **Alpine:** **0 CRITICAL, 0 HIGH, 5 MEDIUM, 1 LOW**, 40 components. The **six** remaining matches were against **pip version 25.0.1**, not Alpine OS packages: MEDIUM `CVE-2025-8869`, `CVE-2026-13346`, `CVE-2026-3219`, `CVE-2026-6357`, `CVE-2026-8643` and LOW `CVE-2026-1703`. Trivy records fixed-version data, including version 26.2.0 for one MEDIUM. Do not infer that one upgrade fully fixes image security or that pip is needed by the sandbox worker. Check actual dependencies/provenance, then consider new immutable image as separate PR.
- **No candidate is approved by count alone.** Alpine's musl ABI versus Debian glibc can break native components. Ubuntu nonroot host test success does NOT prove Alpine runtime compatibility, Linux privilege isolation, Docker START capability, durable F5 epoch or independent L3.
- **Do not treat a SUCCESS Trivy Action as image admission.** Prior workflows intentionally use `exit-code: '0'` to collect findings, not to enforce zero-vulnerability policy.

## Required next actions (contract, not work declared as completed)

1. **Source-only/runtime dependency inventory:** identify whether the exact Core13 fixed reviewed worker and future privileged broker rely on libc/glibc, any dynamically linked binaries, `bash`, `apt`, native Python wheels or `pip` itself at runtime. Use actual source imports and image SBOM; avoid heuristic compatibility claims.
2. **Same-DB baseline control:** fresh rescan of the current unchanged image in the same Trivy DB/scheduled job window as the specific candidate before final risk recommendation; scan `python@sha256:<digest>`, not a mutable tag.
3. **Separate candidate image review:** assess `pip` necessity, its fixed versions and any remaining risks. If a new hardened image is built, bind provenance, immutable digest, CycloneDX and Trivy; do not silently replace F4C2's existing approved-for-never-started source test image.
4. **Actual controlled runtime compatibility** only after independent image security owner signs off; candidate/musl compatibility and fixed stream test must be separately verified under least privilege. Never start Docker merely because remote scan shows 0 HIGH.
5. **Other independent hard gates**: F4C2 broker socket filesystem `0666` must be reduced, controller/root-broker OS isolation and exclusive transport proved, F5 durable intent + async late-CREATE daemon quiescence demonstrated, actual Docker STOP/REMOVE/streaming and independent L3 verified, old J4/J4S direct host Docker paths retired after parity. No user/model code authorization.

## Acceptance state

```text
three_remote_candidate_scans_completed=true
immutable_leaf_digests_verified=true
alpine_zero_high_package_matches_in_trivy_scan=true
alpine_runtime_compatibility_verified=false
independent_alpine_image_risk_accepted=false
docker_image_digest_and_cve_accepted=false
current_f4c2_image_digest_modified=false
real_root_broker_docker_start_attach_stream_verified=false
durable_f5_daemon_inflight_create_quiescence_proven=false
independent_l3_verification_complete=false
worker_isolation_certified=false
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Reusable engineering lesson:** compare OS/security baselines using exact architecture-specific OCI image SHA256 and a common vulnerability database clock, and preserve both distinct CVE IDs and repeated package matches. Smaller SBOM or zero HIGH scan is evidence for prioritizing *compatibility validation*, not a universal "safe container" conclusion.
