# Core13 D2D3B2B1 — immutable image candidate scan comparison / admission contract

**5 November 2026 | Framework successor to B2B0 Draft #156.**

## Baseline independently checked from uploaded owner-run

Actual owner [App Trivy #41973874199](https://github.com/lijust/EREI-3.2/actions/runs/41973874199), [raw artifact #13390747650](https://github.com/lijust/EREI-3.2/actions/runs/41973874199/artifacts/13390747650), exact source-reviewed Python 3.12.16/Debian 13.7/linux-amd64 image digest: 0 CRITICAL, **47 HIGH**, 77 MEDIUM, 63 LOW, 6 UNKNOWN package-CVE matches; **10 distinct HIGH CVE IDs**, 92 distinct IDs overall, 89 CycloneDX components. Trivy exit-code 0 produced evidence but did NOT approve this image. Original F4C2 image digest must remain unchanged pending independent risk approval. Legacy F4C2 IPC filesystem socket mode 0666, incomplete F5 async CREATE/daemon epoch and J4/J4S host Docker authority remain separately blocked.

## D2D3B2B1 reviewed implementation

App module: tools/core13_j5_04f4d2d3b2b1_immutable_image_candidate_compare.py. App adds 26 mocked-registry/CVE/SBOM offline tests, source-only PR/push CI, plus an owner-only feature-branch override of the already default-registered manual Trivy workflow name core13-j5-04f4d2d3b2b0-pinned-image-remote-trivy-manual-hold.yml. The default branch holds an unchanged explicit fail-closed registration stub, NOT a scanner or permission grant.

Exactly three Docker Official Image candidate tags with Python **3.12.16**: 3.12.16-slim-trixie, 3.12.16-slim-bookworm, 3.12.16-alpine3.24. Version stays constant to isolate the base image. Alpine musl vs glibc runtime compatibility is unproven.

Before any remote scan, the source-only resolver obtains Docker Hub's scoped anonymous pull token and retrieves only one of the three reviewed tag manifests. It verifies OCI/Docker media type, response Docker-Content-Digest equals raw SHA256, source allowlisted repository and tag, and a *single* linux/amd64 descriptor, then verifies the child image manifest fetched **by its immutable digest**. If the index/digest/architecture is ambiguous or invalid the job must fail closed. Token must never be logged or serialized into artifacts.

Trivy then scans **python@sha256:<verified linux-amd64 manifest digest>**, not the mutable tag, using remote registry mode without a Docker container start, image build, root or user/model code. Raw vulnerability JSON + CycloneDX SBOM + manifest resolution + comparison report are uploaded separately for each candidate. The comparator requires exact scan ArtifactName = pinned image, architecture amd64, runtime environment PYTHON_VERSION=3.12.16, valid schema, counts and SBOM. It records package-match severity totals, distinct HIGH CVE IDs, removed and introduced IDs, and both scan/SBOM SHA256 hashes. It CANNOT grant execution, select an image automatically or mutate F4C2.

Offline CI uses mocked manifest/index and scan reports to verify strict digest checks, wrong architecture or Python version, duplicate JSON, wrong image, invalid severity, and CVE de-duplication. Owner must manually dispatch to collect real remote candidate evidence. A green scan means only evidence generated; lower CVE count is not sufficient for image acceptance, and Alpine dependency/runtime compatibility requires separate evidence.

### Standing hard gates

Image risk approval must be independently reviewed for actual package applicability, patchability, image provenance and any necessary compatibility testing; new digest must be adopted in an explicit separate change. F4C2 broker least-privilege socket/controller separation, actual Docker lifecycle/streaming/STOP/owned cleanup, F5 durable daemon create-intent and late CREATE quiescence, independent L3 and AI acceptance remain blocked. No Docker START, privileged owner workflow or model-generated code is added in this branch.

RECORD:
- baseline_high_matches=47
- baseline_distinct_high_ids=10
- candidate_scans=OWNER_MANUAL_PENDING
- docker_image_security_approved=false
- image_compatibility_verified=false
- full_docker_lifecycle_proven=false
- durable_f5_quiescence_proven=false
- independent_l3=false
- untrusted_code_execution_authorized=false
- stable_ready=false
- decision=BLOCK_AI_ACCEPTANCE
- learning_effectiveness=NOT_ESTABLISHED

**Reusable engineering principle:** never compare two Docker Official Image floating tags as though their image bytes were immutable; record, verify and scan the architecture-specific digest. Retain per-package counts AND unique CVE IDs separately, and never treat a lower CVE count as independent authority to start a container.

## Actual source-only baseline regression evidence — 5 November 2026

App [push #41997585432](https://github.com/lijust/EREI-3.2/actions/runs/41997585432) and [PR #41997773639](https://github.com/lijust/EREI-3.2/actions/runs/41997773639), source SHA `25b0bdc66b5f04fbdf9eab6af546484094e09472`, both completed SUCCESS. **56 offline PASS/0 FAIL per run (26 new mocked registry manifest SHA/amd64/CVE+SBOM comparison +30 old B2B0 image/F5 always-HOLD).** These are code regression tests, **NOT** actual alternative image Trivy measurements. The real three-job candidate comparison reuses the already registered manual workflow filename on exact App D2D3B2B1 branch; owner must dispatch it separately and compare artifact hashes/CVE package matches and unique HIGH IDs. No newer variant is approved, no Docker container started, and F5/L3 remain false.

## Owner branch-only real registry scan completed, no image accepted — 5 Nov

[App run #42027751135](https://github.com/lijust/EREI-3.2/actions/runs/42027751135) completed 3/3 real immutable linux/amd64 Trivy+CycloneDX matrix jobs SUCCESS, with raw zipped artifacts downloaded and checked. Compared HIGH/CRITICAL package matches: baseline 47/0; Trixie slim 46/0; Bookworm slim 37/**2**; Alpine 3.24 0/0 (plus 5 MEDIUM, 1 LOW, all pip 25.0.1; SBOM 40 components). This does **not** prove musl runtime compatibility nor image approval. Baseline scan and candidates differ by approximately seven hours of vulnerability database update time. Full reusable raw SHA+unique ID triage: [owner scan independent admission report](core13-d2d3b2b1-owner-three-image-trivy-framework-admission-20261105.md). Docker START, F5 durability, L3 and AI execution remain BLOCKED.
