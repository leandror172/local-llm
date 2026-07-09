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
- **Session 96 [pipeline] / 97 [actual]** (2026-06-30) — **Session-97 batch LANDED to master.** #56 + #57 merged; T-19/T-26/T-30/T-42/T-58/T-59 done. Overlay test runner (196 tests). Git-add bulk-stage guard.
- **Session 97 [pipeline] / 98 [actual]** (2026-06-30) — **`my-go-qcoder` HTTP 500 = host-RAM ENOMEM fixed (`.wslconfig memory=24GB`) + Ollama store moved to ext4** (cold load 33s→15.6s). Plan: `docs/plans/ollama-store-ext4-move.md`.
- **Session 98 [pipeline] / 99 [actual]** (2026-07-01) — **T-68 CLOSED: ext4 store reboot-persistence self-heals** (udev rule + attach-only logon task; real reboot cold PASS). 162 GB reclaimed. Artifacts: `~/workspaces/ollama-infra/`.
- **Session 99 [pipeline] / 100 [actual]** (2026-07-01) — **Career chatbot Groq free-tier fix.** Three budget caps; retrieval heading-vocabulary contract discovered; worst-case ~11.9K vs 12K TPM. 68 tests green. Deployed.
- **Session 100 [pipeline] / 101 [actual]** (2026-07-02) — **Ollama outage fixed + systemd coupling gaps closed + machine config moved out of the repo (PR #65).** `ollama-store-attach.service` fires on every VM boot; `:11434` proxy now a systemd peer. Gate = T-70.
- **Session 101 [pipeline] / 102 [actual]** (2026-07-02) — **LTG Phase 4 design locked + plan authored.** P4-D1–D7 frozen. Phase 4 = zero model calls.
- **Session 102 [pipeline] / 103 [actual]** (2026-07-02) — **LTG Phase 4 EXECUTED (T1–T7, PR #66) + anchors-rebuild idempotency fix.** τ=0.70/K=10 frozen; 3367 edges; Leiden 207/214. All acceptance PASS. **304 tests green.**
- **Session 103 [pipeline] / 104 [actual]** (2026-07-03) — **PR #66 MERGED + T-71 DONE + LTG Phase 5 design frozen.** `run-rebuild-all.sh` sequencer; P5-D1–D7 frozen. **321 tests green.** New tasks T-73/T-74.
- **Session 104 [pipeline] / 105 [actual]** (2026-07-03) — **LTG Phase 5 EXECUTED + ACCEPTED (PR #67).** `relate.py` + `relate_summary` role + CLI. Verdict bands FINAL. **377 tests green.** New agent types `impl-opus`/`impl-opus-med`.
- **Session 106** (2026-07-04) — **T-33 repo-split discovery + model-registry decision capture (PR #68).** Split-before-Phase-6 lean; S-D1–S-D7 register; T-76 deferred w/ triggers; T-77 signature extractor. Topology rule: products depend on primitives, never product↔product.
- **Session 107** (2026-07-04/05) — **T-33 SPLIT EXECUTED (PR #69).** S-D1–S-D7 frozen + split done in one session: engine → sibling repo **`latent-topic-graph`** (github.com/leandror172/latent-topic-graph, private; filter-repo 108-commit history; `src/ltg` package, 11 entry points, CWD-relative instance resolution; 377 tests; overlays + memories + agents seeded); llm instance → **`ltg/`** (editable path-dep wrappers). **SP-10 PASS** (875 topics exact, 49 anchor removals all traced; llm index now 976 nodes / 3067 edges) + **SP-11 self-index PASS** (456 nodes / 1145 edges; 2 masked `relative_to()` bugs found+fixed). 12 engine tasks migrated (ids kept). SP-14 prehistory-mining plan authored haiku-executable (new repo `docs/plans/prehistory-mining.md`); postmortem `docs/plans/ltg-repo-split-postmortem.md`. Claude project memories seeded for the new repo.
- **Session 108** (2026-07-06) — **Handoff-tooling bug sweep (overlay v9): T-78/T-62 DONE, T-61 partial.** T-78 wrapped-bullet parser continuation-join (`payload.py`) + 4 tests; T-62 `run-handoff.sh` shim honors `--registry` + prefers a co-located engine (home repo runs source; verified end-to-end by this session's own handoff); T-61 `resume.sh` §2b backported (source ⊇ installed) — general customization-seam half still open. 178 tests green. **NOTE (corrected session 110): the "cross-repo v9 synced + merged" claim was wrong** — what synced was the user-level shared engine at `~/.claude/tools/handoff/`, not per-repo overlay installs; the consumer CLAUDE.md markers were still at v6/v6/v8.
- **Session 109** (2026-07-08) — **T-61 general customization seam BUILT (PR #70).** New `customizable:` installer category — overlay owns a file EXCEPT named `overlay-keep:<name>` regions (repo-owned, seed-once); `resume.sh` moved `files:`→`customizable:`, overlay **v10**. Markers are plain comments not `ref:KEY` (both ref-lookup + `anchors.py` are `*.md`-only → a `.sh` marker is LTG-inert). `_extract_regions`/`_splice_regions` + `handle_customizable` + `verify_overlay` ext in `lib/actions.py`. 21 tests, installer suite 13→34, live acceptance PASS. session-tracking `.memories/` split out of `overlays/.memories/`. **221 tests green.** Follow-up: T-79 v10 propagation.
- **Session 110** (2026-07-08) — **T-79 DONE: overlay v10 propagated to all 4 consumer repos** (expenses/code, web-research, career-search, latent-topic-graph; each committed on master). `--verify` exit 0 everywhere — 3× `SAME`, career-search `CUSTOMIZED`; CLAUDE.md at v10 in all four; idempotent on re-install. career-search's "What to read first" §2b variant **preserved** (hand-wrapped in `overlay-keep` markers before install; verified in the committed blob and in live `resume.sh` output). **Plan correction (`ref:overlay-v10-warn-tripwire`): the `--dry-run` reset-`WARN` does NOT discriminate** — no repo had markers, so decision-3 fired on all four with byte-identical output for the benign reset and the destructive one; the step-1 §2b diff is the only real discriminator. **Three repo classes, not two** — `latent-topic-graph` had no §2b block at all (seeded fresh, +18 lines). Reconciled: the `merge_sections` version marker is **authoritative** (rewritten every install), so session 108's "v9 synced" note overclaimed. New task **T-80**.
- **Open deferred tasks:** **T-34/T-35/T-38–T-41/T-63/T-64/T-72/T-73/T-74/T-75 MIGRATED to the `latent-topic-graph` repo (ids kept)**, ~~T-33~~ (split executed session 107; SP-14 = new repo's L-05), **T-55** (MCP migration deferred), **T-56** (add-task CLI tool), **T-60** (overlay distribution G/H evaluation), ~~T-61~~ (DONE session 109), **T-65** (provenance cheap-half DONE; weighting → new repo's Phase 6 retrieval surface), **T-66** (validate cache-warmed fan-out), **T-70** (VM-restart store-attach gate), **T-76** (model-registry shared library — deferred w/ triggers), **T-77** (signature/doc extractor primitive), ~~T-79~~ (**DONE session 110** — v10 in all 4 repos), **T-80** (make the `customizable:` reset warning discriminate + move `# 2b.` comment inside the keep-region → v11 re-propagate), hook-based auto-resume, Qwen3-Coder-Next feasibility, expense-reporter runtime.Caller fix, **Python 3.10→3.12 via uv** (retrieval slice DONE; benchmarks/scripts/.claude tools pending), Layer 4 stragglers, registry hot-reload, server.py refactor, file-based coordination layer, create-persona.py library, `add_model` MCP tool, prompt-iteration experiment, delete legacy `HTML_TEMPLATE`, per-language error-handling + logging conventions, M-P0a cleanup (retire DeepCoder personas), **DeepSeek R2 32B** (watch), **Fara-7B** (watch), **T-69** (mmap revisit — re-check on Ollama releases; test = load `my-go-qcoder`, `journalctl -u ollama | grep UseMmap`)
- **Next:** **T-80** — make the `customizable:` reset warning discriminate (`WARN-CLOBBER` only when the installed interior differs from the overlay default) + move the `# 2b.` section comment inside the keep-region; (b) changes the region interior → bump **v11** and re-propagate, so sequence both into one release. LTG Phase 6 MCP server (L-01) continues in the sibling `latent-topic-graph` repo. Side options: T-56 (add-task CLI), classifier benchmark (M-P1b/P2), persona hygiene (T-27/T-49).
- **Cross-repo:** `latent-topic-graph` is the **5th tracked repo** (engine sessions run there per S-D7). **All 5 repos now on overlay session-tracking v10** (llm + expenses + web-research + career-search + latent-topic-graph; propagated session 110). career-search is the only repo with a sanctioned keep-region customization (`--verify` → `CUSTOMIZED`, non-gating). The handoff **engine** is a single shared user-level copy at `~/.claude/tools/handoff/` — syncing it is NOT a per-repo install; check each repo's CLAUDE.md `<!-- overlay:session-tracking vN -->` marker for real per-repo state. MVP spike in web-research; expense MCP work in expenses repo. Overlay test runner (`make -C overlays test`) now **221 tests** in master.
- **Environment:** Claude Code runs from WSL2 natively (direct Linux commands). Ollama serves `:11435`; the `:11434` metrics proxy is a systemd peer of ollama (`ollama-metrics-proxy.service`). Store on dedicated ext4 vhdx at `/mnt/ollama-store/models`; reboot-persistence self-heals via udev (T-68) + `ollama-store-attach.service` (session 100). Machine-specific ollama config lives in `~/workspaces/ollama-infra/`, NOT the repo. WSL `.wslconfig memory=24GB` is load-bearing for 30B partial-offload. Ollama can wedge (model loaded per `/api/ps` yet unresponsive) — restart clears it. `rtk git log` drops merge commits — use plain `git log` to confirm a PR landed.
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

<!-- ref:active-decisions -->

### Cross-cutting principles
- **Routing patterns:** (A) local-first escalate, (B) frontier delegates via MCP, (C) chat routes both → `docs/vision-and-intent.md`
- **Licensing (STRONG):** Always check + honor external project licenses; attribute in `docs/ATTRIBUTIONS.md`
- **Layer 5 preferred codegen model:** `my-go-q25c14` (qwen2.5-coder:14b) — ~25-32s, 2 (accepted) quality
- **MCP server work persona split:** `my-mcp-q25c14` for tool signatures/docstrings; `my-python-q25c14` for helpers — both share qwen2.5-coder:14b (no warm_model needed when switching)
- **qwen3:8b think:false:** Must be top-level payload param, not inside `options{}` — Ollama silently ignores it there
- **num_ctx for personas:** 14B models → **32768** (probed 2026-05-30 with `OLLAMA_KV_CACHE_TYPE=q8_0` — all pass); 8B models → 32768; deepseek-coder-v2:16b → 24576 (32K tight at 574 MiB). See `retrieval/probes/ctx-probe-2026-05-30.md` (now in the `latent-topic-graph` repo's `probes/`).
- **Ollama host-RAM + store location (session 98):** 30B partial-offload models read weights into **host RAM** (Ollama forces `UseMmap:false` on partial offload, any filesystem) → `.wslconfig memory=24GB` is the load-bearing fix for the `my-go-qcoder` HTTP 500 (host-RAM ENOMEM, NOT VRAM). Store on a dedicated ext4 vhdx at `/mnt/ollama-store/models` (faster loads + clean store, not a RAM fix). Health: `make -C ~/workspaces ollama-store-check` (systemd+API, namespace-robust). Plan: `docs/plans/ollama-store-ext4-move.md`.
- **Ollama store reboot-persistence (T-68, session 99):** self-healing. The Windows logon task (`WSL-Ollama-ext4-store`, `-AtLogOn`) ONLY attaches the vhd (`wsl --mount --vhd … --bare`); recovery lives in WSL, not Windows-side timing. A udev rule (`99-ollama-store.rules`, matched by `ID_FS_UUID`) `SYSTEMD_WANTS` a oneshot `ollama-store-recover.service` (`reset-failed` + `start ollama` → pulls mount → pulls now-present device) — event-driven, survives `/dev/sdX` letter changes (proven sde→sdd). Do NOT chain the in-WSL `systemctl restart` into the logon task: it races the cold WSL/systemd boot (`LastTaskResult=1`). Artifacts + verified runbook: `~/workspaces/ollama-infra/` (machine-local; moved out of the llm repo 2026-07-02 — the repo carries no machine config).
- **Ollama store attach — VM-restart gap (T-68 follow-up, session 100):** `wsl --mount` binds the vhd to a **single WSL2 VM lifetime**; any VM restart (idle timeout, `wsl --shutdown`, Docker bouncing WSL) silently drops the bare-disk attach and nothing re-attaches — `LastTaskResult=0` is misleading (the attach succeeds then evaporates). The logon task covers cold boot but not mid-session restarts. Fix: `ollama-store-attach.service` (oneshot, `WantedBy=multi-user.target`, `Before=` the mount) fires on **every** VM boot and triggers the elevated Windows attach task via `schtasks.exe /run` (interop; no UAC needed to trigger an already-elevated task). The udev→recover chain completes it. Machine-local at `~/workspaces/ollama-infra/`. Gate = T-70.
- **`:11434` metrics proxy coupling (session 100):** the Session-76 transparent proxy (native Go binary, `:11434`→`:11435`, **no Docker in the data path** — only Grafana/Prometheus `make stack` is Docker) is now a systemd peer of ollama: `ollama-metrics-proxy.service` with `WantedBy=ollama.service` + `PartOf` + `BindsTo`, so `:11434` is up exactly when ollama is. Clients (expenses, MCP bridge, benchmarks) stay on the canonical `:11434`; no per-repo port changes. Install/unit: `~/workspaces/ollama-infra/`.
- **Machine config lives outside the repo (session 100):** all machine-specific ollama systemd/config (ports, `/usr/local/bin`, WSL/UNC paths) lives in un-versioned `~/workspaces/ollama-infra/`, NOT the llm repo (portable platform code only). Boundary established by `~/workspaces/scripts/`; PR #65. Only live pointers repoint on a move; historical session logs keep old paths as history.
- **Multi-model comparison → DPO pairs:** `run-compare-models.sh` + `run-record-verdicts.sh` → Layer 7 pipeline
- **Session-handoff pipeline (session 83):** register-driven deterministic rewrite of the session-handoff flow — reuse existing handoff `ref:` blocks (no new in-file markers), home = `session-tracking` overlay, local-model layer deferred to enhancement. Load-bearing contracts (the register, the F7 schema) are Claude-authored, not local-model. See `ref:handoff-pipeline-design`. **B2 safety core (session 84):** F1/F3/F4 are pure functions over `(role, text)`; the `Region(start,end,interior)` is the single boundary source of truth; F4 verifies by recompute-and-compare (re-derive expected text byte-exact), not hash-outside.
- **Handoff stage/promote redesign (session 89):** `--payload` = stage (rename-on-ingest via `shutil.move` + locate+apply+verify in memory + emit JSON handle); `--id` = promote (recompute from current files + idempotency git-log check + apply + commit + rename dir suffix). `--dry-run` flag dropped. Run dir status suffix (`-pending`/`-success`/`-failed`) replaces "writes nothing" invariant. JSON stdout. MCP migration deferred (T-55). Plan: `~/.claude/plans/handoff-redesign-rename-on-ingest.md`.
- **Handoff topology/value-only/harvest (session 90):** D1 = value-only **2-full** (`log-entry` is structured snake_case slots — `context`/`what_was_done`/`decisions`/`next`/`gotchas`; the pipeline renders ALL scaffold incl. the `## <date> - Session N: <title>` heading). D2 = **clean break** (manifest v5→v6, all repos migrate in lockstep, no dual-accept). Latest-only `session-log.md` — rotation archives each prior entry to a slugged `session-log-<date>-s<N>-<slug>.md`; the `Previous logs:` line is dropped (archive dir + filenames are the index). `handoff-harvest.sh` seeds `what_was_done`. Target registries left untouched (`manual_if_exists`) — the orphaned `header-previous-logs` role is inert (pipeline only walks payload→register). Plan: `docs/plans/session-handoff-topology-valueonly-harvest.md`.
- **T-33 LTG repo split (sessions 106–107):** engine lives in the sibling `latent-topic-graph` repo; llm keeps the instance at `ltg/` (corpus/config/index/wrappers; editable uv path-dependency). S-D1–S-D7 frozen in `docs/plans/ltg-repo-split.md` (`ref:ltg-split-frozen-decisions`); postmortem in the new repo. S-D7 cadence: single-repo sessions; cross-repo touches are bounded tail-steps owned by the driving repo. Topology rule: products (LTG engine, overlays) depend on layer-0 primitives, never on each other.

**Frozen layer decisions (Layers 1/2/3):** `.claude/archive/decisions-layers-1-3.md`
**Historical decisions (Phases 0-6, Layer 0):** `.claude/archive/phases-0-6.md`
**LTG decisions:** `latent-topic-graph` repo — `DECISIONS.md` + per-phase plans in its `docs/plans/` (moved T-33 split, session 107)
<!-- /ref:active-decisions -->

---

<!-- ref:session-reading-guide -->
| Task | Read first | Ref keys / notes |
|------|-----------|-----------------|
| **T-80 — make the `customizable:` reset warning discriminate (+ move `# 2b.` comment inside the region)** | `docs/plans/overlay-v10-propagation.md` (`ref:overlay-v10-warn-tripwire`), `overlays/lib/actions.py` `handle_customizable`, `docs/plans/overlay-customizable-regions.md` | Decision-3 emits the same `WARN … reset to overlay default` whether the reset is a no-op or a silent clobber. Compare installed interior vs `src_regions[name]`; emit `WARN-CLOBBER` only when they differ. Fixture: career-search pre-v10 (customized, unmarked) vs expenses (default, unmarked) must produce DIFFERENT dry-run output. (b) moves the section comment into the region → interior change → bump **v11** + re-propagate; ship (a)+(b) together. Suite: `make -C overlays test-installer`. |
| **LTG — engine work (Phase 6 MCP, T-63, T-34, extraction experiments)** | Sibling repo `/mnt/i/workspaces/latent-topic-graph/` — its `CLAUDE.md`, `.claude/tasks.md` (migrated task ids kept), `.memories/`, `DECISIONS.md`, phase plans in its `docs/plans/` | **Engine sessions run in THAT repo** (S-D7 cadence: single-repo sessions; llm touched only for instance rebuilds as engine-session tail-steps). Phase 6 MCP server is its L-01. |
| **LTG — llm instance operations (rebuild, query, relate)** | `ltg/.memories/QUICK.md`, `ltg/corpus.yaml` + `config.yaml`, `docs/plans/ltg-repo-split.md` (`ref:ltg-split-frozen-decisions`) | Wrappers in `ltg/` (cd-in + engine entry points via editable path-dep). Rebuild order extract → … → communities; `run-rebuild-all.sh` for derivation stages. First post-split rebuild: anchor delta must equal the moved ref-key set (SP-10). |
| **Overlay propagation to consumer repos (any version)** | `docs/plans/overlay-v10-propagation.md` — the "as executed" procedure + watch-outs | **Never trust the `--dry-run` reset-`WARN` as a safety gate** (`ref:overlay-v10-warn-tripwire`); diff the keep-region against the overlay default per repo first. Diff the FULL `.bak`, not just the region. Run the installed script (exit 0) — installer output does not prove it works. Per-repo state = the CLAUDE.md `<!-- overlay:session-tracking vN -->` marker, which is authoritative. |
| **Classifier benchmark (M-P1b/P2)** | `docs/findings/model-updates-2026-05.md` § What to Benchmark, `personas/models.yaml`, `benchmarks/lib/run-compare-models.sh` | `ref:model-selection`; models pulled: `qwen3.5:0.8b`, `qwen3.5:2b`, `phi4-mini` vs `qwen3:4b-q8_0` |
| **Backfill SOLID + error-handling directives** | `docs/tasks/backfill-persona-constraints.md`, `docs/ideas/persona-error-handling-conventions.md`, `personas/registry.yaml` | grep: `git grep -L "MUST NOT modify"` modelfiles/; pair error-handling session with backfill |
| **M-P0a cleanup — retire DeepCoder personas** | `personas/registry.yaml` (filter `status: benchmark`), `ref:deepcoder-benchmark-decision` | 6 personas to rm + archive Modelfiles; `deepcoder:14b` base (9GB) optional |
| **Handoff pipeline + overlay installer — COMPLETE (overlay v10, all 5 repos)** | `ref:handoff-pipeline-design`, `overlays/session-tracking/files/registry.yaml`, `overlays/.memories/KNOWLEDGE.md` (system) + `overlays/session-tracking/.memories/` (handoff history) | B1-B4 + stage/promote + all fixes through session-108 v9 bug sweep + session-109 `customizable:` category (T-61) + session-110 propagation (T-79). Engine shared user-level at `~/.claude/tools/handoff/` — one copy, not per-repo. Home-repo run via shim `--registry`. Installer categories: files/templates/merge_sections/append_lines/manual_if_exists/**customizable**. |
<!-- /ref:session-reading-guide -->
