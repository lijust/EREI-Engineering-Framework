# Core13 C0 Windows Git-blob integrity: CRLF root cause and bounded checkout fix

**8 November 2026 | CONFIRMED root cause from the owner's local log.**

The owner actually ran `python -m unittest discover -s tests/unit -p test_core13_pilot_c0_*.py -v` in a fresh Windows clone. Result **Ran 38 tests, FAILED (failures=8), exit code 1**. The Gemini injected-transport tests **16/16 passed**. The eight failures are repeated exact source hash assertions against five shared files, not eight independent runtime defects.

## Verified original-byte comparison

| Source path | Signed Git blob (LF) | Observed owner worktree Git blob (CRLF) |
|---|---|---|
| `tools/core13_pilot_b1_advisory_only.py` | `8be64b9a1a492e78b97903d95c44fcdea77099ce` | `ecbe6fe9357ffaefd5dcd520223a3e62b9d508ce` |
| `contracts/core13-pilot-b0-source-route-inventory-v1.json` | `814e7194dc5ebd95557616a68117138ee880da3e` | `4b1b6847943e5c38aee4887d1c314d37510d3835` |
| `contracts/core13-pilot-closure-v1.json` | `939a27b43f752210668f6f8c0773209422f74209` | `2f71563b7034e91257f7d641c0f8b574a2f7ae82` |
| `contracts/core13-pilot-c0-prereg-three-probes-v1.json` | `49b5c38fc3add5a015d89298ea1edeb439942130` | `d77370f7537368f9f882af7a33e23b1fb59612ea` |
| `tools/core13_pilot_c0_gemini_readonly_boundary.py` | `01ecbd606980220f459772644efc45068b963968` | `d979ef8d36b587dcb55da3130b4b497f5c8a3af9` |

Independent SHA-1 Git blob recomputation against the *actual GitHub source text* verified that replacing each `\n` with `\r\n` reproduces **all five** observed owner-local Git hashes exactly. This makes the explanation **confirmed** (not merely likely): default Windows checkout line-ending conversion changed raw bytes, whereas SHA-pinned source contracts test exact bytes. It does **not** indicate malicious source modification, model misbehavior, or broken provider HTTP logic.

## Smallest durable correction

- Added App `.gitattributes` on the C0 branch with `text eol=lf` for precisely **28** pinned source, manifest, workflow and test paths (including all 14 B0 route sources).
- Added Framework `.gitattributes` with **7** pinned mirrored JSON/document paths.
- No previously pinned `.py`, `.json` or `.yml` content was edited, no historical signoff changed, no force push, no changed expected SHA, no SHA check removed. On future Windows clones these selected files remain exact LF as in Git.
- A controlled Git clone demonstration with `core.autocrlf=true` and `.gitattributes text eol=lf` verified `i/lf w/lf` and exact matching `git hash-object`.
- **Important:** an existing Windows checkout does not necessarily rewrite CRLF files when `.gitattributes` is subsequently fetched. A **fresh differently named clone of the updated C0 branch** is the least risky validation path. Do not reset the existing checkout or change the user's global Git preferences.

## Owner-local recheck (PowerShell lowercase)

```powershell
cd "$env:userprofile\desktop"
gh repo clone lijust/erei-3.2 erei-core13-c0-lf -- --branch core13/pilot-c0-preregister-three-advisory-probes-20261108 --single-branch
cd .\erei-core13-c0-lf
git ls-files --eol tools/core13_pilot_b1_advisory_only.py
git ls-files --eol contracts/core13-pilot-c0-prereg-three-probes-v1.json
python -m unittest discover -s tests/unit -p "test_core13_pilot_c0_*.py" -v
write-output "c0_local_exit_code=$lastexitcode"
```

**Required evidence, not yet observed:** both `git ls-files --eol` outputs show `i/lf w/lf attr/text eol=lf`; test suite reports `Ran 38 tests ... OK`, exit=0. Until then, no claim of 38/38 PASS or C0 acceptance. The new GitHub-hosted Actions workflow remains blocked by the separately confirmed GitHub billing/spending limit condition. There is still no live Gemini request, no model-provider fault evidence, no independent AI effectiveness, and no C1 run.

`FORMAL_GATES=12/16`, `C0=SOURCE_EOL_CORRECTION_OWNER_RECHECK_PENDING`, `C1=NOT_STARTED`, `AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`, `stable_ready=false`.
