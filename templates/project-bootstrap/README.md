# Project Bootstrap Template Pack

This directory is the canonical V1 scaffolding used by `tools/bootstrap_project.py`.

## Generated project structure

```text
AGENTS.md
.erei/
├── framework.json
├── PROJECT_PROFILE.md
├── ARCHITECTURE.md
├── SECURITY_MODEL.md
├── DATA_MODEL.md
├── PERFORMANCE_BUDGET.md
├── PROJECT_RULES.md
└── feedback/
    ├── README.md
    └── FRAMEWORK_FEEDBACK.md
adr/
└── ADR_TEMPLATE.md
```

`FRAMEWORK_FEEDBACK.jsonl` is intentionally created only when the first evidence-backed feedback event is captured.

## Important distinction

Bootstrap **creates scaffolding**. It does not prove that the project documents are complete or correct.

For brownfield repositories, populate the generated documents only after inspecting actual code, configuration, data, deployment, tests, and authoritative project decisions.

For greenfield repositories, compose bootstrap with project discovery/new-project workflow before treating architecture/security/data sections as accepted truth.

The feedback directory is project-local learning infrastructure. It does not authorize a project agent to modify Framework Core or change the project Framework pin.

## Example

```bash
python tools/bootstrap_project.py \
  --target ../my-project \
  --project-name "My Project" \
  --project-repository "owner/my-project" \
  --project-lifecycle brownfield \
  --framework-ref <immutable-framework-commit> \
  --framework-baseline <stable-framework-baseline> \
  --overlay google-apps-script \
  --dry-run
```

After reviewing the dry run, execute without `--dry-run`.

Existing target files are fail-closed conflicts. `--force` is deliberately explicit and should not be used to bypass inspection of existing project governance.

## Stable pin rule

Candidate/Stable project baselines should use an immutable Framework commit SHA or immutable tag. A mutable branch may be used temporarily during development but is not sufficient reproducibility evidence for Stable.
