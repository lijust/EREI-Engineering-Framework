# Google Sheets Data Access

**Source baseline:** official Apps Script best practices and Google Sheets API batch/value guides, verified 2026-08-31.

## Core principle

Treat Sheets access as remote/service I/O. Minimize round trips and preserve data invariants explicitly.

## Engineering rules

### SD-001 — Batch reads and writes
Prefer:
1. read required ranges in one/few calls,
2. process in JavaScript arrays/maps,
3. write results in one/few batched calls.

Avoid per-cell `getValue()`/`setValue()` loops and alternating reads/writes.

### SD-002 — Read only required scope when scale matters
A full-sheet `getDataRange().getValues()` may be reasonable for small data but becomes a hidden scaling cost. Define required columns/rows/index strategy for frequently called paths.

### SD-003 — Build in-memory indexes for repeated lookups within one execution
For repeated ID/key matching, construct maps/sets once rather than repeatedly scanning rows or invoking Sheet services.

### SD-004 — Preserve immutable identifiers
Use stable IDs/keys rather than row positions as domain identity. Row numbers may change after sorting/insertion/deletion.

### SD-005 — Separate schema from UI position assumptions
Centralize sheet/tab/column schema metadata. Avoid scattering magic column numbers/names through business logic.

### SD-006 — Writes need explicit overwrite policy
Before mutating existing data define:
- overwrite allowed/forbidden,
- blank-only behavior,
- optimistic precondition/version behavior,
- expected current value when material,
- audit/evidence requirements.

### SD-007 — Concurrency-sensitive writes require a protocol
Use appropriate lock/precondition/re-read strategy for shared mutable records. Batched access improves performance but does not by itself prevent lost updates.

### SD-008 — Critical writes may require read-back
For high-value enrichment, migration, configuration, or state transitions, verify persisted values after write when the workflow requires evidence.

### SD-009 — Use field/range precision to reduce accidental overwrite
When using Sheets API update operations, target only intended ranges/fields. Field masks on applicable `batchUpdate` operations help limit updates to intended properties.

### SD-010 — Understand batch semantics
Google Sheets API `spreadsheets.batchUpdate` groups requests and documents atomic behavior for request application: if a request in the batch is invalid, the batch is not applied. This does not mean all multi-call application workflows are transactional.

### SD-011 — Built-in vs Advanced Service is an engineering choice
Do not assume the Advanced Sheets API is always faster/better. Use built-in `SpreadsheetApp` for ordinary range operations when appropriate; use batch APIs where their semantics/efficiency/features provide measurable benefit.

### SD-012 — Separate operational database concerns from spreadsheet presentation
As relational complexity, concurrent writes, query patterns, dataset size, or transactional requirements grow, evaluate dedicated storage rather than turning a spreadsheet into an increasingly fragile database.

## Recommended repository abstraction

For non-trivial Apps Script applications, isolate domain logic from raw Spreadsheet calls:

```text
UI / API
   ↓
Service / Use Case
   ↓
Domain logic
   ↓
Repository interface
   ↓
Google Sheets adapter
```

This allows testing and future migration without rewriting business rules.

## Performance diagnostics

Measure:
- number of Spreadsheet service calls per request,
- rows/cells read,
- rows/cells written,
- serialization payload size,
- filtering/calculation time in memory,
- lock wait time,
- total Apps Script duration,
- client-server duration.

## Verification scenarios
- blank-only write does not overwrite populated cell,
- row reorder does not change entity identity,
- concurrent edits do not silently lose updates,
- batch failure does not leave assumed partial state where atomic API semantics apply,
- read-back matches intended critical writes,
- search path meets performance budget at realistic dataset size.