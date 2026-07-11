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
- **Session 103 [pipeline] / 104 [actual]** (2026-07-03) — **PR #66 MERGED + T-71 DONE + LTG Phase 5 design frozen.** `run-rebuild-all.sh` sequencer; P5-D1–D7 frozen. **321 tests green.** New tasks T-73/T-74.
- **Session 104 [pipeline] / 105 [actual]** (2026-07-03) — **LTG Phase 5 EXECUTED + ACCEPTED (PR #67).** `relate.py` + `relate_summary` role + CLI. Verdict bands FINAL. **377 tests green.** New agent types `impl-opus`/`impl-opus-med`.
- **Session 106** (2026-07-04) — **T-33 repo-split discovery + model-registry decision capture (PR #68).** Split-before-Phase-6 lean; S-D1–S-D7 register; T-76 deferred w/ triggers; T-77 signature extractor. Topology rule: products depend on primitives, never product↔product.
- **Session 107** (2026-07-04/05) — **T-33 SPLIT EXECUTED (PR #69).** Engine → sibling repo **`latent-topic-graph`** (filter-repo, 108-commit history; `src/ltg` package, 11 entry points; 377 tests); llm instance → **`ltg/`** (editable path-dep wrappers). SP-10 PASS + SP-11 self-index PASS. 12 engine tasks migrated (ids kept).
- **Session 108** (2026-07-06) — **Handoff-tooling bug sweep (overlay v9): T-78/T-62 DONE, T-61 partial.** 178 tests green. **NOTE (corrected sessions 110–111): the "cross-repo v9 synced" claim was wrong** — what synced was the user-level shared engine, not per-repo installs. Session 111 found three repos still running a v8-era `handoff-harvest.sh`.
- **Session 109** (2026-07-08) — **T-61 general customization seam BUILT (PR #70).** New `customizable:` installer category (`overlay-keep:<name>` regions), overlay **v10**. 221 tests green.
- **Session 110** (2026-07-08) — **T-79 DONE: overlay v10 propagated to all 4 consumer repos.** Plan correction: the `--dry-run` reset-`WARN` does NOT discriminate. Reconciled: the `merge_sections` version marker is authoritative. New task T-80. **NOTE (corrected session 111): its "`--verify` exit 0 everywhere" claim cannot have been true** — `--verify` gated on template drift and had been red on every repo since T-58.
- **Session 111** (2026-07-09) — **session-tracking v11: resume.sh becomes config, the pipeline becomes a package (PR #71, 22 commits).** T-80a + T-82 + #7 done; T-43/T-80 closed; T-81/T-83 filed. **Code ships as a package** (`src/sessiontracking/{register,handoff,resume}`, entry points `st-handoff`/`st-resume`, `uv tool install --editable`); **config ships as an overlay**. `resume.sh` is a shim; its sections are a step list in `.claude/resume.yaml`, and `region:` steps resolve through the handoff register (answers the session-83 deferral). `--verify` rebuilt: three questions per ownership + a **locator contract** — it immediately found that the starter templates never satisfied their own register (a fresh install's first handoff would have failed on four roles). Migrated + committed in all five repos; `--verify` exit 0 everywhere. **287 tests green.** Report: `docs/reports/session-111-report.md`.
- **Session 112** (2026-07-11) — **Coding-delegate grand vision authored (PR #72).** v11 acceptance PASSED first (resume.sh 7/7, `--verify` exit 0, 10/10 locators). ollama-bridge `generate_code`/`ask_ollama` → async **deliverable-run** system: submit → `run_id` → detached worker loops coder model against the Layer-4 evaluator → Claude gates each deliverable (H1); autonomy = H2 behind the V-D2 "graduation" gate. Vision FOLDER `docs/vision/coding-delegate/` (folder-local `index.md` — **root-index split starts** — + `.memories/QUICK.md`; 27 `ref:delegate-*` keys; stances S1–S21; open V-D1–V-D13; phases P1–P6). Evidence: two-agent prior-art comparison (frontier vs web-research arms), clones survey, verdict mining (10.7% coverage; ~1/3 of "improved" = compile-class). web-research field report shipped cross-repo. **Name OPEN (V-D1)** — `naming.md`, criteria C1–C7, shortlist oficina/aprendiz/apprentice/delegate.
- **Open deferred tasks:** **T-84** (coding-delegate P1 — async substrate; vision frozen at `docs/vision/coding-delegate/`), **T-83** (install-time baseline/lockfile — plan written, B-D1–B-D8 unfrozen), **T-81** (`--mode ai` cannot be previewed and does not finish — candidate first client of T-84's substrate), **T-54** (`--force-manual` override — STILL OPEN; three session-111 commits mislabel a different fix as T-54), **T-53** (preflight — now mostly a working `--verify`), **T-55** (MCP migration), **T-56** (add-task CLI), **T-60** (G/H; D adopted), **T-65**, **T-66** (validate cache-warmed fan-out), **T-70** (VM-restart store-attach gate), **T-76** (model-registry shared library — watch: coding-delegate worker config is plausibly the third consumer), **T-77** (signature/doc extractor primitive — coding-delegate P3 is its second consumer), engine tasks **T-34/T-35/T-38–T-41/T-63/T-64/T-72–T-75** migrated to `latent-topic-graph`, plus: hook-based auto-resume, Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix, Python 3.10→3.12 via uv, Layer 4 stragglers, registry hot-reload, server.py refactor, create-persona.py library, per-language error-handling conventions, M-P0a cleanup, **DeepSeek R2 32B** (watch), **T-69** (mmap revisit).
- **Next:** **Merge PR #72** (docs-only). Then **settle the coding-delegate name (V-D1** — `naming.md`, shortlist oficina/aprendiz/apprentice/delegate**)** and author the **P1 plan (T-84)** — freezes V-D4/V-D9/V-D10/V-D11 + ledger event names; first client candidate T-81. Side options: **T-83** (freeze B-D1–B-D8 with a fresh head), T-56 (add-task CLI), classifier benchmark (M-P1b/P2 — now has a product consumer: delegate failure-triage), persona hygiene (T-27/T-49). LTG Phase 6 MCP server (L-01) continues in the sibling repo.
- **Cross-repo:** `latent-topic-graph` is the **5th tracked repo** (engine sessions run there per S-D7). **All 5 repos on overlay session-tracking v11**, each committed. The handoff engine is now the **`session-tracking` Python package**, not a copied directory — `uv tool install --editable <llm>/overlays/session-tracking` once per machine; the legacy `~/.claude/tools/handoff/` copy is a dormant shim fallback. Every repo invokes `run-handoff.sh` identically (no `--registry`). Per-repo config generation = the CLAUDE.md `<!-- overlay:session-tracking vN -->` marker, which is authoritative and distinct from the package version. `--verify` exit 0 in all five. **NEW (2026-07-11): web-research holds an untracked field report** (`docs/reports/2026-07-11-field-report-llm-prior-art-run.md`, defects D1–D5 + proposed fixes) awaiting triage in that repo.
- **Environment:** Claude Code runs from WSL2 natively. Ollama serves `:11435`; the `:11434` metrics proxy is a systemd peer (`ollama-metrics-proxy.service`). Store on ext4 vhdx at `/mnt/ollama-store/models`; reboot-persistence self-heals via udev (T-68) + `ollama-store-attach.service`. Machine config lives in `~/workspaces/ollama-infra/`, NOT the repo. `.wslconfig memory=24GB` is load-bearing for 30B partial-offload. Ollama can wedge (loaded per `/api/ps` yet unresponsive) — restart clears it. `rtk git log` drops merge commits — use plain `git log` to confirm a PR landed. `st-handoff`/`st-resume` need `~/.local/bin` on PATH (it is, at login).
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
- **Layer 5 preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, 2 (accepted) quality
- **MCP server work persona split:** `my-mcp-q25c14` for tool signatures/docstrings; `my-python-q25c14` for helpers — both share qwen2.5-coder:14b (no warm_model needed when switching)
- **qwen3:8b think:false:** Must be top-level payload param, not inside `options{}` — Ollama silently ignores it there
- **num_ctx for personas:** 14B models → **32768** (probed 2026-05-30 with `OLLAMA_KV_CACHE_TYPE=q8_0`); 8B models → 32768; deepseek-coder-v2:16b → 24576. Probes now in the `latent-topic-graph` repo's `probes/`.
- **Ollama host-RAM + store location (session 98):** 30B partial-offload models read weights into **host RAM** (Ollama forces `UseMmap:false` on partial offload, any filesystem) → `.wslconfig memory=24GB` is the load-bearing fix for the `my-go-qcoder` HTTP 500 (host-RAM ENOMEM, NOT VRAM). Store on a dedicated ext4 vhdx at `/mnt/ollama-store/models`. Health: `make -C ~/workspaces ollama-store-check`. Plan: `docs/plans/ollama-store-ext4-move.md`.
- **Ollama store reboot-persistence (T-68, session 99):** self-healing. The Windows logon task ONLY attaches the vhd; recovery lives in WSL. A udev rule (matched by `ID_FS_UUID`) `SYSTEMD_WANTS` a oneshot `ollama-store-recover.service` — event-driven, survives `/dev/sdX` letter changes. Do NOT chain the in-WSL `systemctl restart` into the logon task: it races the cold WSL/systemd boot. Artifacts: `~/workspaces/ollama-infra/`.
- **Ollama store attach — VM-restart gap (session 100):** `wsl --mount` binds the vhd to a **single WSL2 VM lifetime**; any VM restart silently drops the attach. `ollama-store-attach.service` fires on every VM boot and triggers the elevated Windows task via `schtasks.exe /run`. Gate = T-70.
- **`:11434` metrics proxy coupling (session 100):** the transparent proxy (`:11434`→`:11435`, no Docker in the data path) is a systemd peer of ollama (`WantedBy`/`PartOf`/`BindsTo`), so `:11434` is up exactly when ollama is. Clients stay on the canonical `:11434`.
- **Ollama canonical-port squatter (2026-07-09):** bare `ollama` in v0.17.5 is a **TUI**; if `$OLLAMA_HOST` is unreachable it spawns a detached `ollama serve` that inherits the shell env, opens the **empty** default store, and can win the `:11434` race at boot. **A healthy system is self-defending** — with the proxy up the TUI reuses it. `ollama-store-check.sh` proves endpoint identity + cross-port count agreement. Deployed: `~/workspaces/scripts/ollama-guard.sh` (reroutes to `:11435` when the proxy is down) + `ollama-motd.sh`.
- **Machine config lives outside the repo (session 100):** all machine-specific ollama systemd/config lives in un-versioned `~/workspaces/ollama-infra/`, NOT the llm repo (portable platform code only). PR #65.
- **Multi-model comparison → DPO pairs:** `run-compare-models.sh` + `run-record-verdicts.sh` → Layer 7 pipeline
- **Session-handoff pipeline (session 83):** register-driven deterministic rewrite — reuse existing handoff `ref:` blocks (no new in-file markers), home = `session-tracking` overlay, local-model layer deferred. Load-bearing contracts (the register, the F7 schema) are Claude-authored. `ref:handoff-pipeline-design`. **B2 safety core (session 84):** F1/F3/F4 are pure functions over `(role, text)`; `Region(start,end,interior)` is the single boundary source of truth; F4 verifies by recompute-and-compare.
- **Handoff stage/promote (session 89):** `--payload` = stage (locate+apply+verify in memory, emit JSON handle); `--id` = promote (recompute from current files + idempotency check + commit + rename run dir). No `--dry-run`. MCP migration deferred (T-55).
- **Handoff topology/value-only/harvest (session 90):** `log-entry` is structured snake_case slots; the pipeline renders ALL scaffold incl. the `## <date> - Session N: <title>` heading. Latest-only `session-log.md` — rotation archives each prior entry to a slugged file; the archive dir + filenames ARE the index. `handoff-harvest.sh` seeds `what_was_done`.
- **The register is read AND write (session 111).** `resume`'s `region:` steps resolve through the same `locate()` the handoff writes with, so renaming or moving a `ref:KEY` updates both sides in one edit. Read-only roles carry `write_mode: nomodel` — the applier refuses nomodel, so they are read-only by construction, not by convention. A retired role is dead config, not harmless: `--verify` reports it `BROKEN`.
- **T-33 LTG repo split (sessions 106–107):** engine lives in the sibling `latent-topic-graph` repo; llm keeps the instance at `ltg/`. S-D1–S-D7 frozen in `docs/plans/ltg-repo-split.md`. S-D7 cadence: single-repo sessions; cross-repo touches are bounded tail-steps owned by the driving repo. Topology rule: products depend on layer-0 primitives, never on each other.

**Frozen layer decisions (Layers 1/2/3):** `.claude/archive/decisions-layers-1-3.md`
**Historical decisions (Phases 0-6, Layer 0):** `.claude/archive/phases-0-6.md`
**LTG decisions:** `latent-topic-graph` repo — `DECISIONS.md` + per-phase plans in its `docs/plans/`
<!-- /ref:active-decisions -->

---

<!-- ref:session-reading-guide -->
| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| **Coding-delegate — settle name (V-D1), then P1 plan (T-84)** | `docs/vision/coding-delegate/index.md` → `naming.md`, `phasing.md`, `architecture.md` | Vision frozen 2026-07-11 (PR #72 — merge it first). Name BEFORE P1 ships CLI entry points; shortlist oficina/aprendiz/apprentice/delegate, criteria C1–C7 (C4 = cross-language catchability). P1 plan freezes V-D4 (residency), V-D9 (retention), V-D10 (ask_ollama profile), V-D11 (orchestration-lib re-check) + ledger event names. First client candidate: T-81. 27 `ref:delegate-*` keys lookupable; folder QUICK: `docs/vision/coding-delegate/.memories/QUICK.md`. |
| **T-83 — overlay installer install-time baseline (lockfile)** | `docs/plans/overlay-install-baseline.md` (B-D1–B-D8), `overlays/lib/actions.py` `handle_manual_if_exists` | The installer records nothing about what it installed, so it cannot tell "source moved since you reconciled" from "legitimately differs" — 7 unconditional `[TODO]`s across 4 repos. Prior art is `dpkg` conffiles (BASE/OURS/THEIRS; prompt only when the last two both moved); `git merge-file` is the primitive. **B-D5 (bootstrap) is data-loss-adjacent — freeze it with a fresh head.** Half a session to freeze, one to build + propagate. Sequence **T-54 after it**; `--force-manual` likely shrinks to `--theirs`. Urgency LOW: T-82 removed the safety stakes. |
| **T-81 — `--mode ai` plan-then-apply** | `overlays/lib/planner.py` `ai_merge`, `overlays/test-merge-plan.py`, `ref:handoff-cli-surface` | `--dry-run` never calls the model, so an AI merge cannot be previewed before it rewrites `CLAUDE.md`. Two attempts on llm's 12.4 KB CLAUDE.md: 9-min timeout, then ~20 min / zero bytes (a `TIMEOUT`, not a verdict 0). **Consider making the installer the first client of T-84's async substrate instead of patching in place** — submit→review→apply is exactly the missing shape (`ref:delegate-phasing` P1). Also chunk the target — only the section neighbourhood needs to reach the model. |
| **Overlay work of any kind** | `overlays/.memories/QUICK.md` + `KNOWLEDGE.md` (system), `overlays/session-tracking/.memories/` (this overlay) | Install the package first: `uv tool install --editable overlays/session-tracking`. Suite: `make -C overlays test` (287). A new suite must be listed in `run-all-tests.sh` or it runs green testing nothing. `--verify` is now meaningful — use it, and read the per-file lines, not just the exit code. |
| **LTG — engine work (Phase 6 MCP, T-63, T-34, extraction experiments)** | Sibling repo `/mnt/i/workspaces/latent-topic-graph/` — its `CLAUDE.md`, `.claude/tasks.md`, `.memories/`, `DECISIONS.md`, phase plans | **Engine sessions run in THAT repo** (S-D7 cadence). Phase 6 MCP server is its L-01. Coding-delegate P3 will consume its retrieval tools (dependency direction: delegate→LTG, never reverse). |
| **LTG — llm instance operations (rebuild, query, relate)** | `ltg/.memories/QUICK.md`, `ltg/corpus.yaml` + `config.yaml`, `docs/plans/ltg-repo-split.md` | Wrappers in `ltg/`. Rebuild order extract → … → communities; `run-rebuild-all.sh` for derivation stages. Note: session 111 moved `ref:quick-pointers` from `index.md` to `session-context.md`, so the next anchor rebuild will show a file-origin delta for that key; session 112 added `docs/vision/coding-delegate/` (27 new keys) — expect new anchors on the next rebuild. |
| **Classifier benchmark (M-P1b/P2)** | `docs/findings/model-updates-2026-05.md` § What to Benchmark, `personas/models.yaml`, `benchmarks/lib/run-compare-models.sh` | `ref:model-selection`; models pulled: `qwen3.5:0.8b`, `qwen3.5:2b`, `phi4-mini` vs `qwen3:4b-q8_0`. **Now has a product consumer:** coding-delegate in-loop failure triage (mechanical/structural/conceptual — `ref:delegate-loop`, P6). |
| **Backfill SOLID + error-handling directives** | `docs/tasks/backfill-persona-constraints.md`, `docs/ideas/persona-error-handling-conventions.md`, `personas/registry.yaml` | grep: `git grep -L "MUST NOT modify"` modelfiles/; pair error-handling session with backfill |
| **M-P0a cleanup — retire DeepCoder personas** | `personas/registry.yaml` (filter `status: benchmark`), `ref:deepcoder-benchmark-decision` | 6 personas to rm + archive Modelfiles; `deepcoder:14b` base (9GB) optional |
<!-- /ref:session-reading-guide -->
