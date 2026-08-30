# Google Apps Script Overlay Sources

**Baseline research date:** 2026-08-31  
**Source policy:** Prefer official Google developer documentation. Numeric quotas and platform behavior must be re-checked when material because Google explicitly states quotas/limits can change.

## Official references

### Quotas and limitations
https://developers.google.com/apps-script/guides/services/quotas

Baseline observations used:
- Apps Script services have quotas/limitations and throw exceptions when exceeded.
- Quotas are per user for listed services and may change without notice.
- Script runtime: 6 minutes per execution.
- Simultaneous executions: 30 per user, 1000 per script.
- Properties read/write daily quotas vary by account type.
- Properties value size and store-size limitations exist.
- Apps Script dashboard/Cloud console can be used for execution/quota monitoring.

### Apps Script best practices
https://developers.google.com/apps-script/guides/support/best-practices

Baseline observations used:
- Minimize calls to external/Google services.
- Batch spreadsheet read/write operations.
- Read data to arrays, process in memory, write in batches.
- Libraries can add startup latency in UI-heavy scripts with repeated `google.script.run` calls.
- CacheService can reduce repeated expensive fetches.
- Large/complex Sheets workloads may require dedicated database solutions.

### HTML Service client/server communication
https://developers.google.com/apps-script/guides/html/communication

Baseline observations used:
- `google.script.run` is asynchronous.
- Calls may not execute in the order issued.
- The API allows up to 10 concurrent server-function calls from the page; excess calls wait.
- Success/failure handlers are the explicit response mechanisms.
- Only supported serializable parameter/return types can cross the boundary.
- Top-level server functions are client-visible/callable except private functions ending in underscore and other documented exclusions.

### LockService
https://developers.google.com/apps-script/reference/lock/lock-service

Baseline observations used:
- Script, user, and document lock scopes differ.
- Lock objects are not actually acquired until `tryLock()` or `waitLock()`.
- Document lock can be unavailable (`null`) outside a containing-document context such as standalone/web app execution.

### CacheService
https://developers.google.com/apps-script/reference/cache/cache-service

Baseline observations used:
- Script cache is shared across users of the script.
- User cache is scoped to current user and script.
- Document cache is document/script scoped and can be unavailable outside document context.

### PropertiesService
https://developers.google.com/apps-script/reference/properties/properties-service

Baseline observations used:
- Script properties are shared across users of the script.
- User properties are scoped to current/effective user and script.
- Document properties are only available in documented bound/add-on contexts.
- Property stores are simple key-value storage, not cross-script shared databases.

### Web Apps
https://developers.google.com/apps-script/guides/web

Baseline observations used:
- Web apps can execute as the deployer/owner or as the accessing user, with materially different permissions.
- `/dev` test deployment is for users with edit access and runs the most recently saved code.
- Production deployments use deployment configuration/versioning.
- OAuth tokens obtained server-side must not be transmitted to the client.
- Granular OAuth scopes may require programmatic authorization checks when executing as accessing user.

### Google Sheets API batch update
https://developers.google.com/workspace/sheets/api/guides/batchupdate

Baseline observations used:
- Sheets API `spreadsheets.batchUpdate` groups requests; dependent changes are applied as a batch and the documented operation is atomic with respect to request failure.
- Field masks limit updates to intended fields and help avoid accidental overwrites.

### Google Sheets API values
https://developers.google.com/workspace/sheets/api/guides/values

Baseline observations used:
- Batch get/update is recommended for multiple ranges to improve efficiency.
- Built-in SpreadsheetApp operations remain appropriate for many ordinary cases; Advanced Service/API is not automatically superior.

## License note

Google Developers documentation is generally CC BY 4.0 and code samples Apache 2.0 as stated on the referenced pages. The overlay independently summarizes engineering implications; it does not copy large documentation passages or depend on Google sample code.