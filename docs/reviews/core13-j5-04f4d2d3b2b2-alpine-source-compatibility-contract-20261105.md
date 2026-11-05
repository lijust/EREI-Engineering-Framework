# Core13 Framework D2D3B2B2 — Alpine source-level runtime/ABI dependency acceptance contract

**5 November 2026 · Explicit evidence ceiling: actual Trivy artifact + AST of reviewed fixed scripts; no Alpine Docker execution.**

## Evidence chain

- Owner's [actual remote comparison run #42027751135](https://github.com/lijust/EREI-3.2/actions/runs/42027751135), exact immutable `python@sha256:69ebe56e2a764c399514a0a6117131cb730cc4d0e71e85c08deb9af74cbb9f41`, Python 3.12.16/linux-amd64/Alpine 3.24.3, owner [raw artifact #13413629794](https://github.com/lijust/EREI-3.2/actions/runs/42027751135/artifacts/13413629794): **0 CRITICAL/0 HIGH/5 MEDIUM/1 LOW**, all six findings in `pip 25.0.1`, CycloneDX **40 components**. Source scanner observations are not independent security/risk clearance. Debian image reference used by F4C2 remains unchanged; no Docker image was started.
- App module `tools/core13_j5_04f4d2d3b2b2_alpine_source_compatibility_audit.py` pins the SHA256 and exact byte lengths for each of the owner ZIP's 4 raw JSON entries and the Git blob IDs of four source files. It parses arbitrary ZIP/JSON *as data*, strict duplicate/path/size/hash checks; AST inspections do **not** execute inspected source.
- Four exact Git source blobs pinned: J4 lifecycle `0f655d855898bef0d02fdda36602236b76304252`, J4S streaming `42e4c879fc7a0b82c963838eb862ade8d6ac8531`, F4C2 root fixed broker `499b7f07d5d0fd9d49e61a8e75124e68b202f0b2`, D2D3B2A fixed trusted host stream `f825d2cc6fa11f876d9c6a2196cac94fbc75e9e8`.
- **The exact eight reviewed fixed Python probe snippets** are J4 normal/json, timeout/time and output/print; B2A normal/sys, timeout/time, output/sys and stderr/sys; F4C2 in-container fixed `import time; time.sleep(60)`. These use **only Python standard library `json`, `sys`, `time`** and do **not** import `pip`. J4's source-pinned Docker flags call `python -I -S -c`, B2A's host path uses `python -I -S -u -c`; J4S reuses J4 known cases. Static imports indicate **the eight fixed scripts don't require pip at runtime**; they do NOT establish all application/plugin/framework/native dependency needs.
- Trivy CycloneDX lists **`musl 1.2.6-r3`**, `musl-utils`, `sqlite-libs 3.53.4-r0`, `zlib 1.3.2-r1`, `libssl3 3.5.9-r0`, `libcrypto3`, `libffi`, BusyBox and `pip 25.0.1`, but no `glibc/libc6` or `bash` packages. This is **SBOM content only**; do not conclude that every required binary, native wheel, OS syscall or loader is present/compatible.
- All six scanner findings are `pip 25.0.1`: MEDIUM `CVE-2025-8869` (Trivy FixedVersion `25.3`), `CVE-2026-13346` (`26.2.0`), `CVE-2026-3219` (`26.1`), `CVE-2026-6357` (`26.1`), `CVE-2026-8643` (`26.1.2`); LOW `CVE-2026-1703` (`26.0`). No package is assumed exploitable in the isolated worker without an actual threat/reachability review.

## New executable verification (source-only only)

App [Actions #42037284546](https://github.com/lijust/EREI-3.2/actions/runs/42037284546) **SUCCESS**: 26 new B2B2 source/ZIP/SBOM/pip/authorization tests + 26 B2B1 OCI immutable manifest/CVE comparator regressions = **52 offline PASS/0 FAIL**. A **separate nonprivileged read-only CI job** downloaded the original exact GitHub owner artifact ID `13413629794` and verified its four file bytes/SHA256, OS/arch/Python identity, real pip/MEDIUM/LOW contents and all eight reviewed source AST snippets without running the image; compact [CI artifact #13418918176](https://github.com/lijust/EREI-3.2/actions/runs/42037284546/artifacts/13418918176) contains only a held JSON receipt. The source-only checks are reproducible while the original GitHub artifact is retained (14 days); after expiration, re-establish the raw artifact and expected hashes, **not** a synthetic acceptance claim.

## Hard distinctions / next work

**PASS only for:** authentic scan **byte identity under pinned run artifact**, source-defined fixed Python script imports and SBOM metadata present in reviewed Alpine image. **NOT PROVEN:** actual python import/entrypoint execution under Alpine musl, native ABI interoperability, pip removal or upgrade effect, package/OS CVE exploitability or full EREI dependency compatibility, real image security acceptance, privileged Docker broker isolation, F5 creation quiescence, L3 independent verifier.

Even if pip is not used by the eight exact reviewed fixed scripts, don't uninstall pip from the production image or claim the full application does not use it. A separate candidate image with pip upgraded/removed must be built, pinned, re-scanned and reviewed. Full real Alpine runtime testing may be staged only **after independently governed image risk approval and F5 transport/daemon quiescence**, with a distinct restricted controller and approved trusted fixed code. Root F4C2 currently remains the old never-started Debian image and broker source socket mode `0o666`; old J4/J4S direct host Docker CLI is not retired.

```text
owner_alpine_artifact_hash_revalidated=true
fixed_source_scripts_reviewed=8
fixed_scripts_import_only_json_sys_time=true
pip_sbom_present=25.0.1
pip_used_in_eight_fixed_scripts=false
whole_application_pip_independence_verified=false
alpine_musl_native_runtime_compatibility_verified=false
alpine_fixed_worker_container_started=false
independent_image_security_accepted=false
new_docker_image_adopted=false
f5_late_create_daemon_quiescence_verified=false
l3_independent_verified=false
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Reusable cross-country architecture rule:** inspecting *exact fixed source imports* against a *verified exact SBOM* is a useful narrowing of the compatibility test matrix, but is not a substitute for actually running inside that OS/ABI, independently reviewing the image or proving Docker/F5 authority isolation. Separate what pip source scripts **do not reference** from what the full runtime **does not require**.
