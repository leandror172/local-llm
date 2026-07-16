# Session Context for Future Agents

**Purpose:** User preferences and working context across Claude Code sessions.

---

<!-- ref:user-prefs -->
## User Preferences

### Interaction Style
- **Output style:** Explanatory (educational insights with task completion)
- **Pacing:** Interactive — pause after each phase for user input
- **Explanations:** Explain the "why" for each step, like a practical tutorial

### Configuration Files
- **Build incrementally:** Never dump full config files at once
- **Explain each setting:** Add a setting, explain what it does, then add the next
- **Ask before proceeding:** Give user options before making non-obvious choices

### Persona Naming
- Pattern: `my-<role>` (my-coder, my-creative-coder)
- Qwen3 variants get `-q3` suffix (my-coder-q3, my-creative-coder-q3)
<!-- /ref:user-prefs -->

---

## File Management

### Sensitive Data
- **Location:** `.claude/local/` (gitignored)
- **Rule:** System specs, paths, or personal info → write to `local/`

### Log Rotation
- **Tool:** `.claude/tools/rotate-session-log.sh` — run at session end via session-handoff skill
- **Policy:** Keep 3 most recent sessions in `session-log.md`; archive the rest
- **Archive:** `.claude/archive/session-log-YYYY-MM-DD-to-YYYY-MM-DD.md`

### Context Optimization
- **System-prompt files** (CLAUDE.md, MEMORY.md): Keep lean — rules + current state only; history in archives
- **Session files** (tasks.md, this file): Only active layer + pointers to archives
- **Knowledge index:** `.claude/index.md` maps every topic to its file location
- **Archives:** `.claude/archive/` — full historical data, read on demand

---

<!-- ref:current-status -->
- **Session 112** (2026-07-11) — **Coding-delegate grand vision authored (PR #72).** ollama-bridge `generate_code`/`ask_ollama` → async **deliverable-run** system (H1 = Claude gates each deliverable; H2 behind the V-D2 graduation gate). Vision folder `docs/vision/coding-delegate/` (28 `ref:delegate-*` keys; S1–S21; V-D1–V-D13; P1–P6).
- **Session 113** (2026-07-11) — **oficina: V-D1 DECIDED + P1 plan FROZEN (PR #73).** Name = **oficina**. P1 plan `docs/plans/oficina-p1-async-substrate.md` (P1-D1–D11; single-writer ledger + cancel flag; machine-global store; lazy-daemon worker). Event model `event-model.md`.
- **Session 114** (2026-07-12) — **oficina P1 BUILT + ACCEPTED (T-84 DONE; PR #74).** T1–T10 via one Opus subagent; 149 mcp-server tests green. Full substrate (11 modules + `service.py` + 4 MCP tools + `oficina` CLI + `watch-run.sh` + retention). Live acceptance 6/6. Review caught append-onto-torn-tail → repair-on-append in `Ledger._append`.
- **Session 115** (2026-07-12) — **oficina installed + T-81 AI-merge stage/apply BUILT (no oficina; PR #75).** PR #73/#74 merged. `oficina` CLI installed machine-wide + live-smoked. **T-81 built in two parts via two Opus subagents** (serial, VRAM; each re-derivation-verified): Part 1 stage→apply split (`--stage`/`--apply-plan`, `--dry-run` pure; sha256 staleness guard; 13 tests mutation-verified); Part 2 `fit_num_ctx` (fixed the 4096 input-overflow) + `think:false` (5.1× faster) + config timeouts. **296 overlay tests green**; live end-to-end confirmed independently. **Decided T-81 needed NO oficina** — a one-shot CLI gains nothing from async; oficina's real first client must be an agent that parallelizes. Distribution model documented (oficina = machine-global service, not an overlay). Filed T-85/T-86/T-87 + a new memory.
- **Session 116** (2026-07-13) — **Model-call gate decision recorded (T-88): oficina is NOT the gate.** PR #75 merged at session start. Settled the two-altitude split — oficina schedules *runs* (product), a future gate schedules *calls* (layer-0 primitive); LTG refresh / expense probes / benchmarks are **gate** clients, and oficina's worker becomes one behind its injectable `GenerateFn` seam. Decision record `docs/ideas/model-call-gate.md` (G-D1–G-D3 decided; G-D4 priority vs P2 / G-D5 mechanism / G-D6 substrate-reuse open; two constraint families, v1 = local Ollama; subsumes T-21's scope). Also committed `my-go-q3-14b` (Go persona on qwen3:14b).
- **Session 117** (2026-07-14) — **T-89 DONE: async ergonomics built + migration shape decided — NO facade (sync directness IS v1 interactive priority).** Routing convention LIVE (deliverable-shaped → `submit_run` + background watch; small → sync; memory + `ref:oficina-async-migration-shape`). Built same session: PostToolUse watch hook + SessionStart store-scan (`surfaced` markers, origin-annotated per D2-option-2) + `submitted_from` in `RunSubmitted`; 11 hook tests + mcp-server 150 green; item (b) verified live (Delivered payload carries the result into the notification); V-D12 FIRED. Scripts local-model-generated via `submit_run` itself (dogfooding caught a relative-path bug). Hook wiring is in gitignored settings.json → T-86(d). Filed T-90 (KV-quant/offload anomaly).
- **Session 118** (2026-07-15) — **T-89 hooks verified live + T-90 RESOLVED (hypothesis disproven).** Both T-89 hooks wired + firing (hermetic 11/11; SessionStart scan correctly silent on already-marked runs). T-90's "KV-quant drift" is **wrong**: KV `q8_0` + Flash Attention are ACTIVE (KV cache 3.26 GB, not f16's 6.5); the 14B/32K CPU-offload is **Windows-desktop VRAM contention** — the RTX 3060 shares VRAM with the desktop, leaving ~9 GB free not 12. No fix needed; CLAUDE.md's 32K fact corrected. New machine-local `~/workspaces/scripts/gpu-vram-windows.sh`. Finding `ref:kv-quant-vram-contention`; commit `1622b9f`. Sync-truncation asymmetry split to **T-91**.
- **Session 119** (2026-07-15) — **oficina P2 plan FROZEN (T-92) — caching-first evaluated-loop design, advisor-reviewed + committed.** Whiteboarded the coder⇄evaluator loop and wrote `docs/plans/oficina-p2-evaluated-loop.md`: **P2-D1–D13** + run spec + individually-anchored state/loop Mermaid diagrams + 6-event promotion (draft-P2→frozen, incl. `AssemblyDone`) + acceptance + T1–T8 build steps. **Caching drove the design:** Ollama has implicit prefix reuse only → monotonic stable-prefix layout (P2-D2) in one swappable `SEGMENTS` tuple + ordering-guard test (P2-D3); rule-based in-loop classifier is cache-load-bearing (P2-D4); per-run reused worktree serves toolchain caches + S16 delta-scope (P2-D5). First slice = `function`-against-tests, Python, 3-iter, no escalation (P2-D1). **Advisor caught a blocking hole:** blanket delta-scope baseline-subtraction would mask an absent/misnamed target → silent success on broken code; fixed to subtract only out-of-scope failures + `.file` on `ParsedFailure` (P2-D12). Diagrams split into own ref anchors (`ref:delegate-p2-state-diagram`/`-loop-diagram`) → injectable via `context.refs` → **T-93** filed (draft authored cross-session by LTG session 18 with measured evidence). Commits `c24281c`, `eee21ca`.
- **Open deferred tasks:** New: **T-92** (oficina P2 evaluated-loop plan FROZEN — build next at T1), **T-93** (Mermaid diagrams as local-model context — draft-ready via LTG session 18, execution = merge draft into overlay source + reinstall). Still open: **T-91** (sync `generate_code` EOS'd mid-code — NOT offload; **now a P2 prereq**, num_predict floor/cap), **T-88** (model-call gate — G-D4/G-D5/G-D6 open; subsumes T-21), **T-85** (latent multi-`merge_sections` bugs), **T-86** (oficina distribution runbook — incl. (d) hook re-wiring on fresh clones), **T-87** (T-81 Part 2 polish), **T-83** (install-time baseline — plan written, unfrozen), **T-54** (`--force-manual`), **T-53** (preflight), **T-55** (MCP migration), **T-56** (add-task CLI), **T-60** (G/H; D adopted), **T-65**, **T-66** (validate cache-warmed fan-out), **T-70** (VM-restart store-attach gate), **T-76** (model-registry shared library), **T-77** (signature/doc extractor — oficina P3's 2nd consumer), engine tasks **T-34/35/38–41/63/64/72–75** in `latent-topic-graph`, plus the standing infra/model watch items.
- **Next:** **oficina P2 build (T-92)** — start at **T1** (`parse_validator_output`, three readers depend on it), then T2–T8; **T-91 is a prerequisite** (num_predict on the loop generator). **G-D4** gate-vs-P2 priority still open (T-90 showed *contention* not *thrash* → mild lean gate-after-P2). Side options: T-86 distribution runbook, T-83 freeze, T-56, classifier benchmark (M-P1b/P2), persona hygiene (T-27/T-49). LTG Phase 6 MCP server (L-01) continues in the sibling repo.
- **Cross-repo:** `latent-topic-graph` is the **5th tracked repo** (engine sessions run there, S-D7). **All 5 repos on overlay session-tracking v11.** Handoff engine = the `session-tracking` Python package (`uv tool install --editable <llm>/overlays/session-tracking` once per machine). **oficina joins the machine-global tools** (CLI + user-level MCP + shared store `~/.local/share/oficina/`) — reachable from every repo, NOT overlay-distributed; the T-89 hooks however are repo-local (llm) until the D1 user-level promotion. **T-93 draft authored cross-session by an LTG session** (parked `overlays/ollama-scaffolding/drafts/diagrams-as-behavior-specs.md`; LTG's installed overlay carries the section as a local divergence — merge-into-source-BEFORE-reinstall to avoid clobber). web-research still holds an untracked field report awaiting triage there.
- **Environment:** Claude Code runs from WSL2 natively. Ollama serves `:11435`; `:11434` metrics proxy is a systemd peer. Store on ext4 vhdx at `/mnt/ollama-store/models`; reboot-persistence self-heals (udev T-68 + `ollama-store-attach.service`). `.wslconfig memory=24GB` load-bearing for 30B partial-offload. Ollama can wedge (loaded per `/api/ps` yet unresponsive) — restart clears it. **14B/32K partial-offload is VRAM contention, not KV drift (T-90 resolved session 118)** — KV `q8_0` + Flash Attention are active; the shared RTX 3060 leaves only ~9 GB free (Windows desktop holds ~3 GB). Inspect host VRAM with `~/workspaces/scripts/gpu-vram-windows.sh`; reclaim via NVIDIA overlay off (~1 GB) or route 32K work to `submit_run`. `rtk git log` drops merge commits — use plain `git log`. `st-handoff`/`st-resume`/`oficina` need `~/.local/bin` on PATH (it is, at login). oficina storage `~/.local/share/oficina/` (override `OFICINA_ROOT`).
<!-- /ref:current-status -->

---

<!-- ref:local-model-conventions -->
## Local Model Conventions

When Ollama output is imperfect, classify by **defect type × fix scope × prompt cost**:

Verdict scale: 2 = accepted · 1 = improved · 0 = rejected

- **Mechanical** (syntax, typo, wrong import) → 1 (improved), inline always
- **Structural, 1–2 isolated sites** → inline (1 or 0 based on effort)
- **Structural, 3+ sites or interdependent** → 0 (rejected) + stubs-then-Ollama if interface definable; scratch if not
- **Conceptual** (correct syntax, wrong behavior) → 0 (rejected), write from scratch
- **Prompt cost tiebreaker:** if explaining > fixing → inline regardless of scope

Stubs-then-Ollama: write stub signatures, call Ollama with stubs in `context_files`. First call = 0 (rejected) triple; second call gets its own verdict (often 2 (accepted)). Both are clean DPO signal.

Cold-start timeouts → `TIMEOUT_COLD_START`, not 0 (rejected). No DPO triple recorded. Retry immediately. Use `warm_model` MCP tool to eliminate cold starts.

**Prompt anti-patterns (confirmed session 71):**
- Do NOT send code stubs to Ollama — describe behavior, not implementation. Stubs = you wrote the code and the model transcribed it.
- Do delegate test-writing to Ollama when tests contain non-trivial logic - you may pass test names.
- Large prompts (>2000 chars + 3 large context files) time out on 14B even when model is warm. Split into helper-first + main()-second calls.

**LanceDB API gotcha (session 71):** `LanceTable` has no `.column()` method. Use `.to_arrow().column("field_name").to_pylist()` to read a column. `table.count_rows()` is available directly.

**httpx async slip (session 71):** qwen2.5-coder generates `async def`/`await httpx.post()` even in sync contexts. Fix: explicitly write "use `httpx.post(url, json=payload, timeout=120.0)` — NOT async, NOT httpx.Client" in the prompt.

Full decision tree: `docs/scaffolding-template.md` § "Handling Imperfect Output: Decision Tree"
<!-- /ref:local-model-conventions -->

<!-- ref:resume-steps -->
## Quick Resume

Run `.claude/tools/resume.sh` for a compact session-start summary (replaces reading multiple files).

Or manually:
1. `ref-lookup.sh current-status` — current layer, next task, branch state
2. Tail of `.claude/session-log.md` — "Next" pointer from most recent session
3. `git log --oneline -3` — recent commits
4. `.claude/index.md` — find any specific file/topic on demand
<!-- /ref:resume-steps -->

---

<!-- ref:quick-pointers -->
## Quick Pointers (Active Work)

| What | Where |
|------|-------|
| Current layer tasks & progress | `.claude/tasks.md` |
| Active execution plan | `.claude/plan-v2.md` |
| Session log (current) | `.claude/session-log.md` |
| Agent preferences & resume checklist | `.claude/session-context.md` |
| Project rules & constraints | `CLAUDE.md` (repo root) |
| Cross-session memory | `~/.claude/projects/.../memory/MEMORY.md` |
<!-- /ref:quick-pointers -->

---

<!-- ref:active-decisions -->
### Cross-cutting principles
- **Routing patterns:** (A) local-first escalate, (B) frontier delegates via MCP, (C) chat routes both → `docs/vision-and-intent.md`
- **Licensing (STRONG):** Always check + honor external project licenses; attribute in `docs/ATTRIBUTIONS.md`
- **Code ships as a package; config ships as an overlay (session 111, R-D9).** An overlay installer that copies `.py` files is a hand-rolled package manager. `session-tracking` is now a real Python package (`uv tool install --editable`, entry points `st-handoff`/`st-resume`); the overlay installs only per-repo config and docs. Publish-escalation trigger, adopted verbatim from the LTG split: flip to a published package only when working from a machine without the checkout, or on a first external adopter. Corollary: **a deferral whose trigger is guessed will fire on a different trigger** — option D was deferred "until H becomes concrete" and was actually forced by a second consumer needing a shared primitive.
- **Three version facts, never conflate (session 111):** the installed package `--version` is **machine-global**; `registry.yaml: version:` is a **per-file schema contract** (enforced, exit 2); the CLAUDE.md `<!-- overlay:session-tracking vN -->` marker is the **per-repo config generation**. One installer run used to write both code and config, which is why sessions 108/110 conflated them.
- **A signal that fires unconditionally carries zero bits (session 111).** `manual_if_exists` flagged identical files; `customizable:` warned on benign resets; `--verify` gated on template drift and was red on every repo from the day it shipped. Each hid the others. Corollary for `--verify`: **byte-equality is the wrong question for a file the repo owns** — what must hold is the **locator contract** (every register role resolves; write roles gate, read-only advise). Corollary for warnings: **spend silence only on proof of safety.**
- **Config over code-patching seams (session 111).** Wanting an `overlay-keep:` region is a symptom of a missing config field. `resume.sh`'s sections became `.claude/resume.yaml`; `customizable:` survives as a general escape hatch with zero call-sites. A comment defending why *this* case is special is usually the artifact of an accident, not its justification.
- **Two scheduling altitudes (session 116, G-D1):** products schedule *runs* (oficina); a layer-0 **gate** schedules *calls*. Products never route model calls through other products — LTG/expense/benchmark workloads are gate clients, and oficina's worker becomes one too. Client-owns-plan / gate-owns-admission (batches + affinity hints + priority class in; placement + interleave out). `ref:model-gate-altitude`.
- **Async routing convention (session 117, T-89):** deliverable-shaped / long / parallelizable local-model work → `submit_run` + background watch (the PostToolUse hook injects the instruction); small-and-waiting-anyway → sync tools. **No facade, no cutover — sync directness IS the v1 interactive-priority mechanism** (sync bypasses the run FIFO). `refs`-dependent calls stay sync until P2 closes T-89(d). `ref:oficina-async-migration-shape`.
- **Layer 5 preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, 2 (accepted) quality
- **MCP server work persona split:** `my-mcp-q25c14` for tool signatures/docstrings; `my-python-q25c14` for helpers — both share qwen2.5-coder:14b (no warm_model needed when switching)
- **qwen3:8b think:false:** Must be top-level payload param, not inside `options{}` — Ollama silently ignores it there
- **num_ctx for personas:** 14B models → **32768** (probed 2026-05-30 with `OLLAMA_KV_CACHE_TYPE=q8_0`); 8B models → 32768; deepseek-coder-v2:16b → 24576. Probes now in the `latent-topic-graph` repo's `probes/`. **T-90 (session 117): the q8_0 setting may have drifted — verify before trusting these ceilings.**
<!-- /ref:active-decisions -->

---

<!-- ref:session-reading-guide -->
| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| **oficina P2 — evaluated loop (T-92, FROZEN — build next)** | `docs/plans/oficina-p2-evaluated-loop.md` (`ref:delegate-p2-goal`/`-decisions`/`-state-diagram`/`-loop-diagram`/`-events`/`-acceptance`), then `docs/vision/coding-delegate/.memories/KNOWLEDGE.md` + `phasing.md` (P2) | Plan FROZEN session 119, advisor-reviewed. **Build starts at T1** (`parse_validator_output → ParsedFailure{stage, file, error_key, raw}` — three readers depend on it), then T2–T8. First slice = `function`-against-tests, Python, 3-iter, no escalation (P2-D1). Loop is a new `GenerateFn` filling P1's worker seam. **T-91 is a prerequisite** (P2-D10 needs num_predict floor/cap). Reachable states: queued→working(intake→assembling→looping→packaging)→completed\|failed\|cancelled (`input_required` unreachable until P4). Post-impl: promote diagrams/events to FINAL in the vision folder, then report result in the plan (documentation-lifecycle rule). |
| **T-93 — diagrams as local-model context (draft-ready)** | `overlays/ollama-scaffolding/drafts/diagrams-as-behavior-specs.md` (parked draft), `.claude/tasks.md` T-93 | Section authored cross-session by an LTG session with measured evidence (qwen3:14b extracts sub-topics from inside mermaid blocks). Execution = merge draft into the overlay **source** (`overlays/ollama-scaffolding/files/local-model-conventions.md`), THEN reinstall to consumers (LTG carries it as a local divergence — merge-before-reinstall avoids clobber). Enabled by the P2 diagram anchors + the `refs` param. |
| **T-91 — sync-truncation asymmetry (now a P2 prereq)** | `.claude/tasks.md` T-91, `docs/plans/oficina-async-ergonomics.md` build record, `mcp-server/src/ollama_mcp/` | Sync `generate_code` hit EOS mid-file twice (eval 490/755) where `submit_run` completes. Ruled out (T-90): NOT offload. Action: diff request options sync tool sends vs oficina worker's `_default_generate`; check for a `num_predict` cap. **Blocks P2 build step T6** (P2-D10 needs num_predict floored/capped). |
| **T-86 — oficina distribution runbook** | `docs/vision/coding-delegate/.memories/KNOWLEDGE.md` (Distribution + T-81-outcome sections), `.claude/tasks.md` T-86 | oficina is a **machine-global service** (CLI `~/.local/bin/oficina`, user-level MCP tools, shared store), NOT overlay-distributed. Decide: (a) `ollama-scaffolding` async-vs-sync teaching; (b) 3-step provisioning runbook; (c) published-package trigger; **(d) re-adding the two T-89 hook entries on fresh clones (settings.json gitignored) + the D1 user-level promotion seam.** |
| **T-88 — model-call gate (when picked up)** | `docs/ideas/model-call-gate.md`, then `docs/ideas/ollama-coordination-layer.md` (mechanism seed) | `ref:model-gate-altitude`, `ref:model-gate-decisions`. G-D1–G-D3 decided; open G-D4 (priority — mild lean gate-after-P2), G-D5 (mechanism — dir-contract vs broker vs semaphore; watch PR #9392/#11159), G-D6 (substrate extraction only when gate is real). Triggers: observed thrash · LTG `on_commit: refresh` automatic · explicit gate-first call. |
| **T-81 follow-ups (T-87) / overlay AI-merge** | `docs/plans/t81-part1-merge-preview-stage-apply.md`, `docs/plans/t81-part2-merge-completion-tuning.md`, `docs/findings/overlay-merge-latency-2026-07-12.md`, `ref:overlay-ai-merge-mode` | T-81 DONE (PR #75 merged). Stage/apply seam in `overlays/lib/planner.py`; num_ctx fit + `think:false` in `backends.py`. T-87: `--merge-timeout` CLI flag, fast-arm dup-detection. T-85: latent multi-`merge_sections` bugs. |
| **T-83 — overlay installer install-time baseline (lockfile)** | `docs/plans/overlay-install-baseline.md` (B-D1–B-D8), `overlays/lib/actions.py` `handle_manual_if_exists` | Installer records nothing about what it installed → can't tell "source moved" from "legitimately differs" — 7 unconditional `[TODO]`s. Prior art `dpkg` conffiles (BASE/OURS/THEIRS); `git merge-file`. **B-D5 (bootstrap) data-loss-adjacent — freeze with a fresh head.** Sequence T-54 after. Urgency LOW. |
| **Overlay work of any kind** | `overlays/.memories/QUICK.md` + `KNOWLEDGE.md` (system), `overlays/session-tracking/.memories/` | Install the package first: `uv tool install --editable overlays/session-tracking`. Suite: `make -C overlays test` (296). A new suite must be listed in `run-all-tests.sh`/`test-installer.sh` or it runs green testing nothing. `--verify` is meaningful — read the per-file lines. |
| **LTG — engine work (Phase 6 MCP, extraction)** | Sibling repo `/mnt/i/workspaces/latent-topic-graph/` — its `CLAUDE.md`, `.claude/tasks.md`, `.memories/`, `DECISIONS.md` | Engine sessions run in THAT repo (S-D7). Phase 6 MCP server is its L-01. oficina P3 will consume its retrieval tools (dependency direction oficina→LTG, never reverse). |
| **LTG — llm instance operations (rebuild, query, relate)** | `ltg/.memories/QUICK.md`, `ltg/corpus.yaml` + `config.yaml` | Wrappers in `ltg/`. Rebuild order extract → … → communities; `run-rebuild-all.sh`. Sessions 112–119 added coding-delegate + T-81 + gate + async-ergonomics + VRAM-finding + P2-plan docs — expect new anchors on the next rebuild. |
| **Classifier benchmark (M-P1b/P2)** | `docs/findings/model-updates-2026-05.md` § What to Benchmark, `personas/models.yaml`, `benchmarks/lib/run-compare-models.sh` | `ref:model-selection`; models pulled: `qwen3.5:0.8b`, `qwen3.5:2b`, `phi4-mini` vs `qwen3:4b-q8_0`. Product consumer: oficina in-loop failure triage (P6). |
<!-- /ref:session-reading-guide -->
