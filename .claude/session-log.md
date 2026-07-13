# Session Log

**Current Layer:** "Layer 5 — Expense Classifier (side-track: oficina P1 merged + installed; T-81 AI-merge stage/apply DONE without oficina; T-86 distribution decision next)"
**Current Session:** 2026-07-12 — Session 115: "2026-07-12 — Session 115: oficina installed + T-81 AI-merge stage/apply (no oficina), PR #75"

---
## 2026-07-12 - Session 115: "2026-07-12 — Session 115: oficina installed + T-81 AI-merge stage/apply (no oficina), PR #75"

### Context

Continued from session 114 (oficina P1 built). User merged PR #73/#74 to master, then directed: install the `oficina` CLI and build T-81 as its first client — session ran autonomously after the design was settled.

### What Was Done

- Installed the `oficina` CLI machine-wide (`uv tool install --editable ./mcp-server` → `~/.local/bin/oficina`) and live-smoked the async substrate end-to-end (submit→status→result; a `pong` run); confirmed the 4 MCP tools (`submit_run`/`run_status`/`run_result`/`cancel_run`) are live in-session and the CLI shares the machine-global store.
- Built **T-81** (`install-overlay --mode ai` preview) in two parts via two Opus subagents (serial for the 12 GB VRAM ceiling), each verified by re-deriving the invariant rather than trusting green tests — PR #75, two commits.
- Part 1 (preview): stage→apply split — `--stage` / `--apply-plan` / `--plan-file`, `--dry-run` stays pure; staleness guard (sha256 pre-image, aborts STALE before any write); 13 hermetic tests, the two safety tests mutation-verified.
- Part 2 (completion): `fit_num_ctx` sizes num_ctx to the INPUT prompt (fixed the `num_ctx=4096 if fmt` overflow RC1; deleted the output-sized defect-marker comment); empirical arm pick flipped qwen3:14b to `think:false` (5.1× faster, better placement); config-driven read + wall-clock timeouts; findings doc.
- Verified independently: full overlay suite 296 green (re-ran myself); live end-to-end on the shipped code (dry-run purity, stage leaves target byte-identical, apply + backup + markers, STALE re-apply exit 1).
- Captured the overlay-vs-oficina distribution discussion in coding-delegate KNOWLEDGE.md (Distribution + T-81-outcome sections), QUICK.md, README, index.md; filed T-85/T-86/T-87; wrote a new memory (num_ctx sizes to input).

### Decisions Made

- T-81 built WITHOUT oficina (user + analysis): install-overlay is a one-shot CLI with nothing to do while the GPU works, so async buys it nothing; its defects were solved by a client-side stage/apply + a num_ctx/think fix. Lesson: oficina's real first client must be an AGENT that can parallelize, not a batch CLI.
- D1: two explicit verbs (`--stage`/`--apply-plan`) with `--dry-run` kept pure — rejected overloading `--dry-run` to be the stage (would fire a GPU call + write a file as a side effect of a full-sequence preview; advisor + special-case-comment smell).
- Subagent contract: they OWN code/tests/their own new files and PROPOSE all shared-file/memory/README edits in their report (parent applies) — matches the "output = suggestions" instruction and avoids write-conflicts.

### Next

- **T-86** — decide the oficina distribution model + a new-machine provisioning runbook (discuss next session); whether `ollama-scaffolding` should gain async-vs-sync guidance (likely P2-era).
- A genuine **agent-driven first client** for oficina, or start **P2** (evaluated deliverable loop) with its own frozen plan.
- Merge PR #75.

### Gotchas

- oficina is a **machine-global service** (CLI + user-level MCP tools in `~/.claude.json` + shared store `~/.local/share/oficina/`) — NOT overlay-distributed. Installing an overlay does not enable oficina; new-machine enablement = 3 steps (uv-tool install `mcp-server` + user-level MCP registration + Ollama).
- The `num_ctx=4096 if fmt` constant was defended by an output-sized comment — a defect marker: it sized context to the tiny JSON output, truncating the ~15 KB full-file merge input.
- Handoff header fields (`**Current Layer:**`/`**Current Session:**`) live in `.claude/session-log.md`.
