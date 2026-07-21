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
- **Session 118** (2026-07-15) — **T-90 RESOLVED.** 14B/32K CPU-offload is Windows-desktop VRAM contention, not KV-quant drift (q8_0 + Flash Attention active). `~/workspaces/scripts/gpu-vram-windows.sh`.
- **Session 119** (2026-07-15) — **oficina P2 plan FROZEN (T-92).** Advisor caught the delta-scope masking hole (P2-D12).
- **Session 120** (2026-07-15) — **P2 FIRST SLICE BUILT + ACCEPTED (PR #76).** `kind:function` loop; suite 150→223; cache on `prompt_eval_duration`.
- **Session 121** (2026-07-16) — **PR #76 REVIEWED + HARDENED.** 10 correctness fixes (suite→235); 5 deferred T-95–T-99; executable-spec DSL (T-100).
- **Session 122** (2026-07-16) — **P2 `/simplify` + T-95/T-99 (b)** (suite 241). Shared per-call transport; `auto_verdict` ledger-only.
- **Session 123** (2026-07-17) — **PR #76 MERGED; T-96/T-97/T-98 RESOLVED (PR #77, suite 260).** refs fallback + `RefsDropped`; retention worktree prune; worktree-relative path scoping.
- **Session 124** (2026-07-18) — **Founding problem recovered (T-102) + Go-widening Phase 1 + write-model M2 decided (T-104); PR #79.** (1) T-102: multi-session GPU contention is the *founding* problem, dropped in the T-21→T-88 supersession; T-89 scope-limited; gate gains G-D7 (wait tolerance) + G-D8 (busy-check MVP). (2) T-92 Axis A Phase 1 shipped: `deliverable.language` + inference + kind-scoped rejects (suite 279); R1/R3/R4 settled by a worktree `go build` experiment. (3) T-104: `loop.py:263` overwrites whole files → `kind:function` is file-granular; loop reimplements what it should compose; **M2 (edit) = code-anchored** (benchmark 108 gens — null on correctness, cost win). Filed T-103 (timeout config).
- **Open deferred tasks:** **T-102** (multi-session contention — M-D4/M-D5 open, gate busy-check G-D8), **T-103** (timeout config mismatch), **T-104** (write-model — M2 decided, edit-kind BUILD open), **T-100** (test-DSL promotion), **T-101** (QUICK.md revision), **T-93** (mermaid-as-context — measurement unblocked), **T-86** (oficina distribution runbook — `OFICINA_VALIDATE_CODE`/`_REF_LOOKUP`), **T-88** (model-call gate — G-D4/5/6 + new G-D7/G-D8), **T-94** (RTK porcelain), **T-85/T-87/T-83/T-54/T-53/T-55/T-56/T-60/T-65/T-66/T-70/T-76/T-77**, engine tasks **T-34/35/38–41/63/64/72–75** in `latent-topic-graph`, plus standing infra/model watch items.
- **Next:** **Build the edit kinds on M2** (`LanguagePack.locate_unit` + loop composes `patch_file` + C0 target-present flip). Then **Axis A Go read-side** (Phase 3: `_parse_gotest`, compile-in-worktree, flat category rule — the honest oficina dogfood target). **PR #79 review/merge.** Standing: T-102 busy-check (G-D8), T-103, T-93 measurement, T-86, **G-D4** gate-vs-widening priority (M-D3 removed its unmet-trigger support).
- **Cross-repo:** `latent-topic-graph` is the 5th tracked repo (S-D7). All 5 on session-tracking v11. **oficina is machine-global**; T-89 hooks repo-local (llm) until user-level promotion. Session 124 branch `docs/t102-multi-session-contention` (PR #79). T-93 draft parked at `overlays/ollama-scaffolding/drafts/`. web-research still holds an untracked field report.
- **Environment:** Claude Code runs from WSL2 natively. Ollama serves `:11435`; `:11434` metrics proxy is a systemd peer. Store on ext4 vhdx at `/mnt/ollama-store/models`; reboot-persistence self-heals. `.wslconfig memory=24GB` load-bearing. 14B/32K partial-offload is VRAM contention (T-90) — ~9 GB free of the shared RTX 3060. `rtk git log` drops merge commits — use plain `git log`. `st-handoff`/`st-resume`/`oficina` need `~/.local/bin` on PATH. oficina storage `~/.local/share/oficina/` (`OFICINA_ROOT`). **T-103: declared `OLLAMA_TIMEOUT=120` (`config.py:33`) is NOT operative — effective sync ceiling is ~600s (`.bashrc` 120000 vs `.claude.json` 600000 disagree); a large-context 14B delegation can still exceed 120s → split+shrink.** P2 evaluator needs `OFICINA_VALIDATE_CODE` on a machine-global install.
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
- **oficina composes the ollama-bridge tools; it does not reimplement them (session 124, T-104).** `loop.py:263`'s bespoke `write_text` silently dropped `patch_file`, which already exists → `kind:function` became file-granular. Sibling of T-95 (loop reimplemented the transport) and the T-102 busy-check (a scheduler proposed where a busy-check existed). Each time the re-authored local version is the cruder one. Corollary for the write model: **M2 (edit) = code-anchored** (`LanguagePack.locate_unit` computes `old_string` from disk → feeds `patch_file`; 100% apply, no model reproduction fragility); named-unit kinds are code-anchorable, arbitrary patch is not. M1 (greenfield) = compose `output_file`.
- **The founding problem is multi-session GPU contention (session 124, T-102).** N concurrent Claude sessions contend for one GPU; a sync call that waits its turn exhausts its own transport deadline. Dropped in the T-21→T-88 supersession (clients reframed sessions→products). **T-89 is scope-limited, not reopened** — it answered interactive-vs-*batch*; "sync bypasses the FIFO" is a priority mechanism only with one interactive caller. The gate needs a **wait-tolerance axis (G-D7)** distinct from admission policy, and its MVP is **T-21's busy-check (G-D8)**, not the full scheduler. A trigger a person can satisfy by hand (manual serialization) is not a trigger.
- **Code ships as a package; config ships as an overlay (session 111, R-D9).** An overlay installer that copies `.py` files is a hand-rolled package manager. `session-tracking` is a real Python package; the overlay installs only per-repo config and docs. Corollary: **a deferral whose trigger is guessed will fire on a different trigger** (and: a deferral that gets *generalized* may become unbuildable and take its problem statement with it — T-21→T-88).
- **Three version facts, never conflate (session 111):** installed package `--version` (machine-global); `registry.yaml: version:` (per-file schema contract, exit 2); the CLAUDE.md `<!-- overlay:session-tracking vN -->` marker (per-repo config generation).
- **A signal that fires unconditionally carries zero bits (session 111).** Corollary for `--verify`: byte-equality is the wrong question for a file the repo owns — the **locator contract** is (every register role resolves; write roles gate, read-only advise). Corollary for warnings: spend silence only on proof of safety.
- **Config over code-patching seams (session 111).** Wanting an `overlay-keep:` region is a symptom of a missing config field. A comment defending why *this* case is special is usually the artifact of an accident, not its justification.
- **Two scheduling altitudes (session 116, G-D1):** products schedule *runs* (oficina); a layer-0 **gate** schedules *calls*. LTG/expense/benchmark workloads are gate clients, and oficina's worker becomes one too. Client-owns-plan / gate-owns-admission. `ref:model-gate-altitude`.
- **Async routing convention (session 117, T-89):** deliverable-shaped / long / parallelizable local-model work → `submit_run` + background watch; small-and-waiting-anyway → sync tools. **No facade, no cutover — sync directness IS the v1 interactive-priority mechanism** (for ONE caller — see T-102 for the multi-session limit). `ref:oficina-async-migration-shape`.
- **Layer 5 preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, 2 (accepted) quality
- **MCP server work persona split:** `my-mcp-q25c14` for tool signatures/docstrings; `my-python-q25c14` for helpers — both share qwen2.5-coder:14b (no warm_model needed when switching)
- **qwen3:8b think:false:** Must be top-level payload param, not inside `options{}` — Ollama silently ignores it there
- **num_ctx for personas:** 14B models → **32768** (probed 2026-05-30 with `OLLAMA_KV_CACHE_TYPE=q8_0`); 8B → 32768; deepseek-coder-v2:16b → 24576. Probes in the `latent-topic-graph` repo's `probes/`. q8_0 verified active (T-90).
<!-- /ref:active-decisions -->

---

<!-- ref:session-reading-guide -->
| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| **NEXT: build edit kinds on M2 (code-anchored)** | `docs/findings/oficina-write-model-benchmark-2026-07-18.md` (`ref:oficina-write-model-report`), `ref:oficina-function-kind-write-model` | M2 = code-anchored DECIDED (cost/timeout-safety, not correctness). Build: `LanguagePack.locate_unit` (Python ast — the benchmark's `locate_function` is a seed; Go `go/parser`); loop **composes `patch_file`** for edit kinds (retire bespoke `write_text`); C0 baseline flips to target-present. Principle: compose, don't reimplement. |
| **Axis A Go read-side (Phase 3 — oficina dogfood)** | `docs/plans/oficina-p2-go-widening.md`, `docs/plans/oficina-language-widening-notes.md` (`ref:oficina-language-widening`) | R1/R3/R4 settled. Measured Go output shapes in the notes doc: compile `./f.go:L:C: msg` self-attributes; test via `go test -json` Package field; flat category rule. Duplicate Go beside Python FIRST, extract `LanguagePack` only after (Phase 4 never before Phase 3). `_parse_gotest` is a clean loop-dogfood deliverable. |
| **T-102 multi-session contention (founding problem)** | `docs/ideas/multi-session-contention.md` (`ref:multi-session-contention`, `-failure-mode`, `-transport-requirement`, `-busy-check`) | The founding problem, recovered. T-89 scope-limited not reopened. Gate needs wait-tolerance (G-D7); MVP = T-21 busy-check (G-D8), not the scheduler. Measurement is a lower bound (bridge-only log; user manually serializes). |
| **Phase 1 language plumbing (shipped)** | `mcp-server/src/ollama_mcp/oficina/intake.py`, `test_intake.py` | `deliverable.language` (declared/inferred), `resolve_language`, `unsupported_language`/`language_not_supported` rules. Stays in intake until the loop is a real 2nd consumer (then extract to `language.py`). Suite 279. |
| **oficina P2 — review deferral records** | `docs/findings/oficina-p2-review-deferred-2026-07-16.md` (`ref:oficina-p2-review-deferred`) | T-95–T-99 all resolved. Minor items (watch `-` run_ids, `git add -A` pycache) still open there. |
| **T-93 — diagrams as model context (unblocked)** | `overlays/ollama-scaffolding/drafts/diagrams-as-behavior-specs.md` | T-96 fixed the refs drop. Measure the "+diagram" verdict via a real loop delegation. Merge draft into overlay source + reinstall. |
| **T-86 — oficina distribution runbook** | coding-delegate `KNOWLEDGE.md` (Distribution), `.claude/tasks.md` T-86 | Machine-global. Env vars: `OFICINA_VALIDATE_CODE` + `OFICINA_REF_LOOKUP`. Author-only submit boundary. |
| **T-88 gate (when picked up)** | `docs/ideas/model-call-gate.md` | G-D1–G-D3 decided; G-D4/G-D5/G-D6 open; **new G-D7** (wait tolerance ≠ admission) + **G-D8** (busy-check MVP) from T-102. |
| **mcp-server / benchmark test runs** | `mcp-server/Makefile`; `benchmarks/lib/run-write-model-bench.sh` | `make -C mcp-server test` (279). Write-model bench: `--per-bucket`/`--arms`/`--runs`/`--limit`; `test_writemodel_apply.py` (19, model-free). |
| **LTG — engine / instance** | Sibling `/mnt/i/workspaces/latent-topic-graph/`; `ltg/.memories/QUICK.md` | Engine sessions run there (S-D7). llm instance index stale (post-commit hook) — sessions 112–124 added docs. |
<!-- /ref:session-reading-guide -->
