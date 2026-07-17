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
- **Session 117** (2026-07-14) — **T-89 DONE: async ergonomics + migration shape — NO facade.** Routing convention LIVE (deliverable-shaped → `submit_run` + background watch; small → sync). PostToolUse watch hook + SessionStart store-scan. Filed T-90.
- **Session 118** (2026-07-15) — **T-90 RESOLVED (hypothesis disproven).** The 14B/32K CPU-offload is Windows-desktop VRAM contention, not KV-quant drift (q8_0 + Flash Attention active). `~/workspaces/scripts/gpu-vram-windows.sh`. Sync-truncation split to T-91.
- **Session 119** (2026-07-15) — **oficina P2 plan FROZEN (T-92) — caching-first, advisor-reviewed.** `docs/plans/oficina-p2-evaluated-loop.md` (P2-D1–D13 + diagrams + 6-event promotion + acceptance + T1–T8). Advisor caught the delta-scope masking hole (subtract only out-of-scope; `.file` on `ParsedFailure`, P2-D12). T-93 filed.
- **Session 120** (2026-07-15) — **oficina P2 FIRST SLICE BUILT + ACCEPTED (T1–T8; PR #76).** The evaluated coder⇄evaluator loop for `kind: function`. New modules `parser`/`prompt`/`workspace`/`evaluator`/`loop` + intake/ledger/worker/client extensions; ~64 new tests (suite 150→223). All 6 acceptance criteria met live; cache confirmed on `prompt_eval_duration` (`ref:oficina-p2-cache-measurement`). **T-91 resolved** within. Events promoted frozen-P2; postmortem `docs/reports/session-120-report.md`.
- **Session 121** (2026-07-16) — **PR #76 REVIEWED + HARDENED.** 4-pass review (plan-conformance + 8-angle /code-review with adversarial verify + live Opus behavioral verify + /security-review; 14 subagents). **10 confirmed correctness bugs fixed w/ regression tests, suite 223→235** (`d0a90df`): false-Delivered exit-code hole, eval+wall-clock timeouts, symlink path escape, kind-scoped intake + budgets fail-loud + `num_predict`, Exhausted surfaced in result/phase/hook. **5 deferred w/ tasks T-95–T-99** (`ref:oficina-p2-review-deferred`). Security: zero findings (author-only submit assumption noted). **Executable-spec test DSL** authored + applied to 3 test files (`ref:test-executable-spec`, T-100; `9b1c5bc`). PR inline comments resolved (`0622c26` readability) + 7 threaded replies posted. T-101 filed (QUICK.md drift). Memory + `/simplify` orientation (`11fac35`).
- **Session 122** (2026-07-16) — **oficina P2 `/simplify` + T-95/T-99 RESOLVED (b) — suite 241, PR #76 pushed.** 4-angle `/simplify` (4 parallel agents) applied **13 quality fixes** (`5b35301`): `run()` decomposed, shared `errors.TriadError` (evaluation failures keep `where=` attribution on Failed), `workspace.target_relpath` single-sources the symlink guard, table-driven intake unknown-keys, `Budgets`-from-schema (`wall_clock_s` now `Optional` = "0/None disables"), context files via `server._build_context_block`. **T-99 DECIDED (b)** (`21172f0`): `auto_verdict` is LEDGER-only; P4 DPO joins ledger↔`calls.jsonl` on `run_id`; plan corrected in place; revisit join mechanics at P4. **T-95 RESOLVED (b)** (`164de8a`): one per-call transport (`worker._chat_generation` + `_cold_start_grace`) shared by single-shot + loop coder; `spec.timeout_s` reaches the loop; **Generation events single-shot-only BY DESIGN** (suite had already pinned it). 6 new tests incl. the `EvaluationError.where`-attribution pin. Memories (`b38d7c9`); branch pushed; PR #76 body gained the session-122 addendum.
- **Session 123** (2026-07-17) — **PR #76 MERGED; T-96/T-97/T-98 RESOLVED — PR #77 opened (suite 241→260), branch `feature/oficina-p2-deferrals`.** **T-96 (b)+(c):** `server._ref_lookup_script()` call-time fallback (`OFICINA_REF_LOOKUP` → `LLM_REPO_ROOT` → package-relative) + fail-loud **`RefsDropped`** worker-ledger event (frozen run-event registry untouched) — unblocks T-93 measurement. **T-97:** retention `workspace` prune class (spec→rev-parse→worktree remove+prune, mirrors teardown; repo-gone still reclaims disk, `git_pruned=False`); TTL staleness = **run-dir mtime** (empty-artifacts crashed runs were doubly invisible). **T-98:** canonical spelling = worktree-relative (producers already emit it; parser stops basenaming, evaluator stamps compile failures with `target_relpath`; consumers compare normpath'd relpaths); both confirmed collision scenarios pinned. Decision records in `ref:oficina-p2-review-deferred`; `mcp-server/Makefile` gained `make test`/`test-oficina`.
- **Open deferred tasks:** **T-100** (test-DSL promotion), **T-101** (QUICK.md revision + memory-system formalization), **T-94** (RTK porcelain pre-flight bug), **T-93** (mermaid-as-model-context — seam LIVE + T-96 fixed, measurement now unblocked), **T-86** (oficina distribution runbook — incl. `OFICINA_VALIDATE_CODE` + `OFICINA_REF_LOOKUP` + (d) hook re-wiring), **T-88** (model-call gate — G-D4/G-D5/G-D6 open), **T-85** (latent multi-`merge_sections` bugs), **T-87** (T-81 Part 2 polish), **T-83** (install-time baseline — plan written, unfrozen), **T-54** (`--force-manual`), **T-53** (preflight), **T-55** (MCP migration), **T-56** (add-task CLI), **T-60**, **T-65**, **T-66** (validate cache-warmed fan-out), **T-70** (VM-restart store-attach gate), **T-76** (model-registry shared library), **T-77** (signature/doc extractor — oficina P3's 2nd consumer), engine tasks **T-34/35/38–41/63/64/72–75** in `latent-topic-graph`, plus standing infra/model watch items.
- **Next:** **PR #77 merge decision** (3 deferral fixes + docs; lean: merge). Then **oficina P2 post-slice widening** (P2-D1: kinds/validators, escalation ladder P2-D9, tiny-model classifier P2-D4 — pairs with the M-P1b/P2 classifier benchmark), and **T-93 measurement** (now unblocked). **G-D4** gate-vs-P2 priority still open. Side options: T-83 freeze, T-56, persona hygiene (T-27/T-49). LTG Phase 6 MCP server (L-01) continues in the sibling repo.
- **Cross-repo:** `latent-topic-graph` is the **5th tracked repo** (engine sessions run there, S-D7). **All 5 repos on overlay session-tracking v11.** Handoff engine = the `session-tracking` Python package. **oficina is machine-global** (CLI + user-level MCP + shared store `~/.local/share/oficina/`); the T-89 hooks are repo-local (llm) until the D1 user-level promotion. **T-93 draft** parked at `overlays/ollama-scaffolding/drafts/diagrams-as-behavior-specs.md` (LTG's installed overlay carries it as a local divergence — merge-into-source BEFORE reinstall). web-research still holds an untracked field report awaiting triage.
- **Environment:** Claude Code runs from WSL2 natively. Ollama serves `:11435`; `:11434` metrics proxy is a systemd peer. Store on ext4 vhdx at `/mnt/ollama-store/models`; reboot-persistence self-heals. `.wslconfig memory=24GB` load-bearing for 30B partial-offload. **14B/32K partial-offload is VRAM contention, not KV drift (T-90)** — shared RTX 3060 leaves ~9 GB free. Inspect host VRAM with `~/workspaces/scripts/gpu-vram-windows.sh`. `rtk git log` drops merge commits — use plain `git log`. `st-handoff`/`st-resume`/`oficina` need `~/.local/bin` on PATH. oficina storage `~/.local/share/oficina/` (override `OFICINA_ROOT`). **P2 evaluator resolves `validate-code.py` repo-relative** — machine-global needs `OFICINA_VALIDATE_CODE`; ref-lookup already has the analogous `OFICINA_REF_LOOKUP` (T-96) — both belong in the T-86 runbook.
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
| **NEXT: PR #77 merge decision + post-slice widening** | PR #77 (3 deferral fixes + docs), `docs/plans/oficina-p2-evaluated-loop.md` (§ implementation-result report) | First slice merged (PR #76); T-95–T-99 ALL resolved. Widening per P2-D1: kinds/validators, escalation ladder (P2-D9), tiny-model classifier (P2-D4 — batch OUTSIDE the coder loop; pairs with the M-P1b/P2 classifier benchmark). |
| **oficina P2 — review deferral decision records** | `docs/findings/oficina-p2-review-deferred-2026-07-16.md` (`ref:oficina-p2-review-deferred`) | ALL FIVE resolved: T-95/T-99 (b) session 122; T-96 (b)+(c), T-97, T-98 session 123 — RESOLVED blocks in place carry the mechanism + rejected alternatives. Minor items (watch `-` run_ids, `git add -A` pycache in worktree commit) still open in the same file. |
| **T-93 — diagrams as local-model context (NOW UNBLOCKED)** | `overlays/ollama-scaffolding/drafts/diagrams-as-behavior-specs.md`, `.claude/tasks.md` T-93 | T-96 fixed the CLI-worker refs drop — either spawn surface now resolves `context.refs`; unresolved refs are fail-loud (`RefsDropped` in the worker ledger). Measure the "+diagram" verdict via a real loop delegation. Execution = merge draft into overlay **source** + reinstall (LTG carries it as a local divergence). |
| **Test authoring — executable-spec DSL (T-100)** | `docs/patterns/test-authoring-executable-spec.md` (`ref:test-executable-spec`) | 6 rules incl. the given/when triage taxonomy + pure-function collapse. Session-123 files stayed imperative per the taxonomy (structural/wiring + git-integration). Promote into code-design-conventions after next validation. |
| **oficina P2 cache measurement (criterion 5)** | `docs/findings/oficina-p2-cache-measurement-2026-07-15.md` (`ref:oficina-p2-cache-measurement`) | Measure prefix-cache reuse on `prompt_eval_duration`, NEVER `prompt_eval_count` (reports full tokens). Re-confirmed live session 121 (519 tok: 350ms warm vs 772ms cold). Reuse is non-monotonic; speed-only (P2-D6). |
| **T-86 — oficina distribution runbook** | `docs/vision/coding-delegate/.memories/KNOWLEDGE.md` (Distribution), `.claude/tasks.md` T-86 | Machine-global service, NOT overlay-distributed. Env vars now TWO: **`OFICINA_VALIDATE_CODE`** (evaluator validator path) + **`OFICINA_REF_LOOKUP`** (ref-lookup script, T-96). Plus the security boundary (author-only submit surface — `shell=True` test_cmd), (a) async-vs-sync teaching, (b) 3-step provisioning, (c) published-package trigger, (d) T-89 hook re-wiring on fresh clones. |
| **T-88 — model-call gate (when picked up)** | `docs/ideas/model-call-gate.md` | `ref:model-gate-altitude`, `ref:model-gate-decisions`. G-D1–G-D3 decided; G-D4 (priority — mild lean gate-after-P2), G-D5 (mechanism), G-D6 (substrate) open. |
| **T-81 follow-ups (T-87) / overlay AI-merge** | `docs/plans/t81-part1-merge-preview-stage-apply.md`, `docs/plans/t81-part2-merge-completion-tuning.md`, `ref:overlay-ai-merge-mode` | T-81 DONE (PR #75). T-87: `--merge-timeout` flag, fast-arm dup-detection. T-85: latent multi-`merge_sections` bugs. |
| **T-83 — overlay installer install-time baseline** | `docs/plans/overlay-install-baseline.md` (B-D1–B-D8) | Installer records nothing about what it installed. Prior art `dpkg` conffiles; `git merge-file`. **B-D5 (bootstrap) data-loss-adjacent — freeze with a fresh head.** Urgency LOW. |
| **Overlay work of any kind** | `overlays/.memories/QUICK.md` + `KNOWLEDGE.md`, `overlays/session-tracking/.memories/` | Install the package first: `uv tool install --editable overlays/session-tracking`. Suite: `make -C overlays test` (296). New suites must be listed in `run-all-tests.sh`. |
| **mcp-server test runs** | `mcp-server/Makefile` | `make -C mcp-server test` (full, 260) / `test-oficina`; `ARGS='-k x'` passes pytest filters. |
| **LTG — engine work (Phase 6 MCP, extraction)** | Sibling repo `/mnt/i/workspaces/latent-topic-graph/` | Engine sessions run in THAT repo (S-D7). Phase 6 MCP server is its L-01. oficina P3 will consume its retrieval tools (dependency oficina→LTG). |
| **LTG — llm instance operations** | `ltg/.memories/QUICK.md`, `ltg/corpus.yaml` + `config.yaml` | Wrappers in `ltg/`. Rebuild order extract → … → communities; `run-rebuild-all.sh`. Sessions 112–123 added many new docs — expect new anchors on next rebuild (index currently stale per the post-commit hook). |
| **Classifier benchmark (M-P1b/P2)** | `docs/findings/model-updates-2026-05.md` § What to Benchmark, `personas/models.yaml` | `ref:model-selection`; `qwen3.5:0.8b`/`qwen3.5:2b`/`phi4-mini` vs `qwen3:4b-q8_0`. Product consumer: oficina in-loop failure triage (P2-D4 tiny classifier / P6). |
<!-- /ref:session-reading-guide -->
