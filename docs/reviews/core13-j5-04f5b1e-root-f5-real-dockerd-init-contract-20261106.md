# Core13 F5B1E — root-owned F5 WAL initialized against live private secondary dockerd

**6 November 2026 | companion acceptance contract, stacked on Framework F5B1D #165.**

F5B1D [manual Actions #42069248000](https://github.com/lijust/EREI-3.2/actions/runs/42069248000) demonstrated actual kernel POSIX boundary for root/controller/worker. F5B1E stages a **separate** owner-manual experiment: an actual root-owned SQLite WAL initialization with verified local secondary Docker daemon, while sending **zero CREATE/START** requests.

### Requirements to pass this limited gate

- Genuinely privileged OS root process on explicitly owner-dispatched, disposable Linux GitHub Actions runner only, source-fixed reviewed exact branch, no sudo on automatic push/PR.
- New root-owned `/run` namespace, `0710` with controller group, root-owned ledger `0700`, database and journal `0600`. No mutable runner-owned ledger path accepted by F5.
- Actual secondary rootful `dockerd` with known fixed command/Unix socket/data-root/exec-root/pidfile, `vfs` and no bridge/iptables. Separate from host dockerd, which must remain responsive and unchanged. Private daemon socket `0600`; direct read-only `/info` and `/containers/json?all=1` must show exact path, zero containers and kernel peer UID/PID/GID.
- Persist the kernel boot ID + daemon PID/start ticks + inode local epoch through F5 `initialize()` as root. Re-open database to check integrity/FKs, exactly one generation, zero intents, source-fixed epoch/boot; root owner and file modes confirmed. Distinct controller and worker UID/GID must both be unable to read the actual DB or root-owned Docker socket.
- Stop only exact owned secondary daemon; verify private API endpoint closes, root ledger is disposed, and host baseline remains reachable.
- No Docker CREATE/START/image pull; no untrusted code; no L3 promotion.

Even a genuine successful manual run would prove only `REAL_ROOT_F5_INITIALIZE_LOCAL_SCOPED_PASS`, not independent generation fencing, crash replay, actual exclusive Docker broker, terminal settlement, late-CREATE quiescence, J4/J4S lifecycle migration or safety for AI execution. All these remain explicit HOLD gates.

```text
REAL_ROOT_F5_INITIALIZE=NOT_EXECUTED
REAL_PRIVATE_DOCKERD_OS_IDENTITY=NOT_EXECUTED
REAL_DOCKER_CREATE=NOT_EXECUTED
BROKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
LATE_ASYNC_CREATE_QUIESCENCE=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

## Observed owner-manual run — 6 November 2026

[App Actions #42198897241](https://github.com/lijust/EREI-3.2/actions/runs/42198897241) completed SUCCESS for both nonroot (139 scoped regression PASS) and owner-manual jobs. The manual job verified actual secondary dockerd and root-owned F5 SQLite WAL initial generation, persisted OS-derived local epoch, controller/worker denial on DB and private socket, empty private inventory, shutdown of private endpoint and unchanged host Docker baseline. Log marker `F5B1E_REAL_ROOT_SECONDARY_DOCKERD_F5_SQLITE_INIT_ZERO_CREATE_LOCAL_PASS_BUT_AI_BLOCKED`. The evidence is local-scoped and contains no Docker CREATE/START. Broker exclusivity, independent durable terminal settlement, late-CREATE quiescence, J4/J4S migration, L3 and AI acceptance remain NOT_ESTABLISHED.
