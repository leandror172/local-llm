## 2026-07-22 - Session 126: "oficina edit mode built + accepted (T-110); M2 revised to whole-file; register refresh"

### Context

Post-/clear continuation of session 126: the pre-clear half did the stale-register refresh (commits eba4d0e..33c6f92, unhandoffed — T-108 raised there); this half ran branch cleanup + T-106 + the full edit-mode arc, ending with PR #82 open.

### What Was Done

- **T-106 fixed** — `ltg/run-refresh.sh` restored as a gitignored verbatim copy of the engine wrapper (9c1460a); full branch cleanup: 55 `-d` + 20 cherry-verified `-D` local, 66 origin branches deleted — master-only end state, in sync
- **M2 re-grounded and REVISED to whole-file-with-context** — edit-mode plan E-D1–E-D9 + T-104 amendment (code-anchored = on-file fallback, observable omission trigger) + T-89 routing-default revision (delegated codegen async-first, small edits included) (197aa56)
- **T-110 BUILT via subagent pipeline** — impl-opus T1–T5 (adfabed..c38a1ab, suite 279→297), impl-opus-med adversarial review (MERGE-READY, 10/10 invariants re-derived, F1–F6 all LOW), F1 polish + real-evaluator omission pin (08d72ad, suite 298)
- **T6 live acceptance PASSED** (7c3bd3d): R1 edit via symlink-spelled target (1 iter, sibling intact); R2 246-line module — diff 2+/2−, 24 siblings byte-intact, 25/25 green; R3 greenfield control byte-clean of edit segments; R4 uncommitted-guard Failed 1.3 s with correct triad, zero GPU
- **`.claude/tools/ollama-cache-report.py` NEW** — per-run prefix-reuse report over calls.jsonl (duration-not-count); retroactively reproduces T8's hand measurement (0.30x of cold); option B (ledger-inline) deferred in-file
- **PR #82 opened** (12 commits); memories updated in place (mcp-server QUICK, coding-delegate QUICK/KNOWLEDGE); T-110 registered shipped, T-109 counter-evidence recorded
- **Verdict harness worked all session**: 7 blocks captured normally (4 call-level incl. from inside a subagent, 3 run-level) — live counter-evidence to T-109 finding (1); finding (2) reproduced (backgrounded generate_code bypassed PostToolUse, call_id recovered by timestamp)

### Decisions Made

- **M2 (edit) = whole-file-with-context (E-D1, amends T-104):** the timeout-safety leg was sync-path-only, and span confinement forces an edit language (unit field, response validation, import merging) no founding fact needs; code-anchored stays on file as the fallback (trigger: a real edit run drops sibling code)
- **Mode = target committed at HEAD; no new spec fields (E-D2);** uncommitted target fails loud at assembly
- **T-89 routing default revised:** delegated codegen — small edits included — defaults async (`submit_run` + harness watch); sync = opportunistic fast path pending the busy-check (G-D8)
- **Cache tracking = read-side report (option A);** ledger-inline (option B) deferred with its trigger noted inside the tool file, keeping the task surface minimal

### Next

- **Review + merge PR #82** (edit mode, 12 commits)
- **Axis A Go read-side (Phase 3)** — now simpler: `locate_unit` dropped from the predicted `LanguagePack` (edit mode is language-agnostic)
- Standing: T-102 busy-check (G-D8), T-105 Phase 6 (judgeable-coverage measurement — data accumulating), T-103, T-107/T-109 (verdict-substrate checks), T-108 (persona catalog strategy)

### Gotchas

- **A `generate_code` that outlives the 120s foreground window returns via task notification and bypasses PostToolUse** — no verdict template; recover the `call_id` from calls.jsonl by timestamp (T-109 finding 2, reproduced live)
- **`pytest -q`'s short summary for a collection error is just `ERROR <file>`** — the ImportError naming the dropped symbol prints above the summary block, so omission-by-import-breakage yields thin repair feedback (recorded in the T-110 plan)
- **Edit/Write and `git add` in the same parallel tool batch race** — an index.md row nearly missed its commit; sequence file edits strictly before staging
- **Live whole-file edit drift is ADDITIVE (unrequested type annotations), not omissive** — and every T6 run converged in iteration 1 (tests-as-context), so per-run cache measurement needs multi-iteration runs (hence the report tool)
