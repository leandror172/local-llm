## 2026-07-14 - Session 117: 2026-07-14 — Session 117: T-89 async ergonomics built (watch hook, session-start scan, origin annotation) + migration shape decided

### Context

Started from resume + a next-steps discussion; the user's challenge "isn't using ollama for coding a client in itself?" unwound a mis-framing of oficina's founding purpose, led to reading the full oficina corpus, produced the migration-shape decision record (T-89 filed), and then built T-89 in the same session.

### What Was Done

- docs(oficina): async-ergonomics decision record — migration shape + V-D12 fired (T-89) (`docs/plans/oficina-async-ergonomics.md`, `ref:oficina-async-migration-shape` + `ref:oficina-async-ergonomics-scope`)
- feat(oficina): T-89 BUILT same session — PostToolUse watch hook (`.claude/hooks/oficina-watch-hook.py`) + SessionStart store-scan (`.claude/hooks/oficina-runs-scan.py`, `surfaced` markers, origin-annotated) + `submitted_from` in `RunSubmitted` (`service.submit`); 11 hook tests (`.claude/hooks/tests/run-tests.sh`) + mcp-server 150 green
- Item (b) VERIFIED live, no build: the `Delivered` payload carries the result (answer/target) into the backgrounded watcher's harness notification
- chore(tasks): T-90 filed (KV-quant/offload anomaly) + T-86(d) hook re-wiring runbook line
- Non-commit: hook wiring added to gitignored `.claude/settings.json` (machine-local); routing-convention memory written (`project_oficina_async_routing.md`); both scripts generated via `submit_run` itself — the dogfooding caught a real relative-path bug (cwd drift) no test would have found

### Decisions Made

- **Migration shape: NO sync facade, NO cutover.** Sync directness IS the v1 interactive-priority mechanism (sync bypasses the run FIFO; the gate's rule 2 presumes sync survives). Routing is a per-call convention, effective immediately: deliverable-shaped/long/parallelizable → `submit_run` + background watch; small-and-waiting-anyway → sync. Timeout-redirect hint rejected (model-mediated recovery, pays twice).
- **D1** hook config repo-level first (user-level promotion is a T-86 runbook line); **D2** scan is global + origin-annotated, never filtered (option 3 repo-filter = presentation-only change later, data recorded from day one); **D3** refs parity deferred to P2; marker = per-run `surfaced` flag file (cancel-flag pattern).
- **V-D12 FIRED** via design discussion, not felt usage friction (guessed-trigger corollary again) — updated in place in `decisions.md`.

### Next

- **Verify both hooks fire on next session start** (settings.json doesn't hot-reload — this next session IS the first live firing; the scan should stay silent since today's 5 runs are marked).
- **T-86** distribution runbook — now includes (d): re-adding the two hook entries on fresh clones/machines (settings.json is gitignored).
- **oficina P2 / first-client** + the **G-D4** gate-vs-P2 priority decision (unchanged from session 116).
- **T-90** when convenient: KV-quant anomaly (q25c14 loaded 15.2GB total / 8.8GB VRAM → partial offload → sync timeouts); then recheck the sync-truncation asymmetry.

### Gotchas

- `.claude/settings.json` is **gitignored** — hook wiring is machine-local; fresh clones need the two entries re-added (T-86(d)).
- `my-python-q25c14` loaded with a 15.2GB/8.8GB total/VRAM split — the f16-KV signature at 32K ctx; `OLLAMA_KV_CACHE_TYPE=q8_0` may not be active (T-90).
- Sync `generate_code` truncated twice mid-code (EOS at eval 490/755) where `submit_run` runs produced complete files every time — unexplained asymmetry, recorded in the T-89 build record.
- The session-start scan surfaced and MARKED today's 5 runs — a silent scan next session is correct behavior, not a failure.
