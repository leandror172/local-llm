# Session Log

**Current Layer:** LTG retrieval substrate — Phase 4 (graph + communities) next
**Current Session:** 2026-07-02 — Session 100: Ollama outage fix — VM-restart store-attach gap + durable :11434 metrics proxy + machine-config consolidated out of the repo

---
## 2026-07-02 - Session 100: Ollama outage fix — VM-restart store-attach gap + durable :11434 metrics proxy + machine-config consolidated out of the repo

### Context

Side-track: the expenses repo reported the local Ollama down. A store/attach outage that cascaded into closing a second systemd-coupling gap and a machine-config cleanup out of the repo.

### What Was Done

- Diagnosed the outage: `wsl --mount` binds the ext4 store vhd to a **single WSL2 VM lifetime**. The logon-only attach task succeeds (`LastTaskResult=0`) then the attach *evaporates* on any mid-session VM restart (idle timeout / `wsl --shutdown` / Docker), so the udev self-heal never receives its device-add trigger. No fallback store since the 162 GB reclaim → ollama loud-fails.
- Recovered service live via `schtasks.exe /run` interop against the elevated task (device back in 1 s → udev → recover → mount → ollama; 81 models / 178 blobs on `:11435`).
- Authored + user-installed `ollama-store-attach.service` — a oneshot that fires on **every** VM boot and triggers the elevated Windows attach task via interop (`schtasks /run` needs no UAC to trigger an already-elevated task), `Before=` the mount; udev→recover completes it. Closes the VM-restart gap the logon-only task missed.
- Fixed `:11434`: the Session-76 transparent metrics proxy (native Go binary, **no Docker in the data path** — only Grafana/Prometheus `make stack` is Docker) was only ever hand-started. Authored + installed `ollama-metrics-proxy.service` coupled to ollama (`WantedBy=ollama.service` + `PartOf` + `BindsTo`); `:11434` now up whenever ollama is. Coupling gate passed (the install's `restart ollama` brought the proxy up automatically).
- Consolidated ALL machine-specific ollama config out of the llm repo to un-versioned `~/workspaces/ollama-infra/` (6 tracked files `git rm`'d + 3 new artifacts + docs); live pointers repointed, historical session-log entries left as history. Committed on `chore/consolidate-ollama-machine-config`, pushed, **PR #65**.

### Decisions Made

- `wsl --mount` is per-VM-lifetime → the store attach must fire on **every VM boot**, not just at Windows logon (the original T-68 blind spot). The trigger event is WSL's own systemd boot, driven from inside WSL via `schtasks /run` of the already-elevated attach task.
- `:11434` stays the canonical client port (Session-76 design) → clients (expenses) do NOT repoint to `:11435`; reliability comes from coupling the proxy to ollama's lifecycle instead.
- Machine-specific config (ports, `/usr/local/bin`, WSL/UNC paths) lives in `~/workspaces/ollama-infra/`, NOT the versioned repo. Only live pointers repoint; historical session logs keep old `scripts/ollama-ext4/` paths as accurate history.

### Next

- Run the **T-70** gate: `wsl.exe --shutdown` + reopen the terminal, then `make -C ~/workspaces ollama-store-check` must PASS cold with zero manual attach (proves the attach service closes the mid-session VM-restart gap).
- Merge/close PR #65.
- Resume top priority: LTG Phase 4 — graph + communities.

### Gotchas

- `LastTaskResult=0` on the logon task is misleading — the attach genuinely succeeds, then evaporates on the next VM restart. Success ≠ persistence for `wsl --mount`.
- A dead `:11434` with a healthy `:11435` means the **proxy** is down, not ollama (ollama serves `:11435`; `:11434` is the transparent metrics proxy).
- `git rm` refuses a file with uncommitted modifications (RUNBOOK had the Step-8 edit) — needs `-f` once the working copy is safely duplicated at the destination.
