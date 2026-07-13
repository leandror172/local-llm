## 2026-07-12 - Session 114: oficina P1 BUILT — T1–T10, live acceptance 6/6, PR #74

### Context

Fresh session reading the frozen P1 plan cold (the plan-completeness test by design). Build delegated to one Opus subagent across two dispatches, with main-session review between and after.

### What Was Done

- feat(oficina): P1 async substrate T1-T5 — ledger, ids+store, intake, fifo, workerproc (T-84) — commit `26cd5a6`; 68 tests
- feat(oficina): P1 T6-T10 — worker, MCP tools, CLI, retention; live acceptance 6/6 (T-84 DONE) — commit `2049519`; 149 tests total
- docs(oficina): README — async-run tools, timeout demotion note, project structure
- docs(mcp-server): README — backfill 6 undocumented tools (pre-existing drift)
- Review fix-loop between the halves: re-derivation caught append-onto-torn-tail silently corrupting the ledger (test was green while encoding the bug) → repair-on-append moved INTO `Ledger._append` (rejected the subagent's defer-to-T6 proposal)
- Live acceptance 6/6 incl. #2 detach/reattach replayed from the main session (`OFICINA_ROOT=... oficina status <id>`) and #6 calls.jsonl `run_id` continuity
- Folder KNOWLEDGE.md created (`docs/vision/coding-delegate/.memories/KNOWLEDGE.md`) — implementation invariants + P2 parking; both QUICKs updated in place; mcp-server memories updated
- PR #74 opened, stacked on `feature/oficina-p1-plan` (PR #73 still unmerged) — retarget to master after #73 merges

### Decisions Made

- Repair-on-append lives in the ledger, not in T6 worker-resume: requiring future writers to remember tail-repair is special-case knowledge far from the artifact; single-writer discipline makes truncation race-free
- One deliberate `client.py` seam accepted (additive `dict.get()`-safe `run_id` in calls.jsonl): the only faithful way to meet acceptance #6 without re-implementing the DPO log schema; revert path documented in mcp-server KNOWLEDGE.md
- Delivery report lives in the `Delivered` event payload (ledger, `ledger: forever`) — what keeps `run_result` answerable after retention prunes artifacts
- No warm_model this session (GPU shared with other processes); lenient timeouts — a timeout is never a 0 verdict

### Next

- User merges PR #73, then retarget PR #74 to master and merge
- Restart the MCP bridge (or start a fresh session) to expose the 4 new tools (`submit_run`/`run_status`/`run_result`/`cancel_run`)
- T-81 as oficina's first client (submit→review→apply for `install-overlay --mode ai`), or T-83 freeze (B-D1–B-D8, fresh head)

### Gotchas

- P1 `in_place` runs never populate `artifacts/`, so retention is an observable no-op on real runs until P2 worktrees or deliverable-copying — parked in the folder KNOWLEDGE.md with the other P2 gaps (refs unsupported in worker default generate; Failed triad keys `where/whose/what` vs intake `stage/fault/detail`; `_default_generate` reuses server.py privates)
- The plan-completeness experiment worked: two cold reads produced 14 explicit gap reports, zero silent improvisations; the biggest defect was caught by review re-derivation, not by the builder — evidence for keeping the H1 gate
