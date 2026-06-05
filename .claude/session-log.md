# Session Log

**Current Layer:** Tooling side-track — Session-handoff pipeline (B2 safety core done; B3 next). LTG Phase 3 still pending (`anchors.py` TDD).
**Current Session:** 2026-06-04 — Session 84: Session-handoff pipeline — B2 safety core (F1/F3/F4)
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`, `.claude/archive/session-log-2026-04-30-to-2026-04-30.md`, `.claude/archive/session-log-2026-05-04-to-2026-05-04.md`, `.claude/archive/session-log-2026-05-16-to-2026-05-16.md`, `.claude/archive/session-log-2026-05-20-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-22-to-2026-05-22.md`, `.claude/archive/session-log-2026-05-25-to-2026-05-25.md`, `.claude/archive/session-log-2026-05-26-to-2026-05-26.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`, `.claude/archive/session-log-2026-05-27-to-2026-05-27.md`, `.claude/archive/session-log-2026-05-28-to-2026-05-28.md`, `.claude/archive/session-log-2026-05-29-to-2026-05-29.md`, `.claude/archive/session-log-2026-05-29-to-2026-05-29.md`, `.claude/archive/session-log-2026-05-30-to-2026-05-30.md`

---

## 2026-06-04 - Session 84: Session-handoff pipeline — B2 safety core (F1/F3/F4)

### Context
Resumed from session 83 (design + register frozen, B1.1 done). Goal: build the deterministic safety core of the register-driven session-handoff pipeline (Scope A, NO local model). Session hit its limit at close → wrote an emergency one-file handoff (`.claude/handoff-session-84.md`) instead of the normal multi-file flow.

### What Was Done
- **B1.2:** added stable `(T-NN)` task IDs to `.claude/tasks.md` (52 open tasks, awk pass; convention noted in the build section). Commit `a1f985d`. Also refreshed the stale root `.memories/QUICK.md` (was stuck at session 74).
- **B2.1 F1 Locator** (`e6d4615`): `locator.py` + 15 contract tests. Pure stdlib; `Region(kind, mode, start, end, interior)` with `text[start:end]==interior`; `locate(role, text, *, task_id=None)` dispatching four kinds (`ref_block`, `field`, `structural`, `checklist`); non-unique/missing → `LocatorError`. Local model verdict 1 (4 mechanical regex/offset off-by-ones fixed via `patch_file`).
- **B2.2 F3 Applier** (`71979e6`): `applier.py` + 8 tests. `apply(text, region, content)` dispatching on `region.mode` (replace/prepend/append/checkoff); never touches bytes outside the region. Local model verdict 2 (as-is).
- **B2.3 F4 Verifier** (`f0c4822`): `verifier.py` + 8 tests — the trust boundary. `verify(original, modified, edits)`: overlap guard + independent recompute-and-compare (re-derive expected text right-to-left, byte-exact) + ref-marker multiset invariant. Does NOT call apply — independent check. Local model verdict 2 (as-is).
- All code in `overlays/session-tracking/files/handoff/` (installs to `.claude/tools/handoff/` via the overlay `files:` mechanism). **31 tests green** (15+8+8).

### Decisions Made
- **F1/F3/F4 are pure functions** over `(role dict / Region, text str)` — no file I/O, no YAML, stdlib only. The caller parses `registry.yaml`. Lets the contract tests construct inputs inline.
- **The `Region` is the single source of boundary truth** — F3 and F4 both consume F1's `start/end/interior`, which is why F3/F4 were near-trivial (only F1 needed fixes).
- **F4 = recompute-and-compare**, not literal "hash outside the regions" — strictly stronger, and handles undelimited structural insertions. Independence preserved by NOT calling apply().
- **Local-model process (reaffirmed):** delegate impl to `my-python-q25c14`; you MAY delegate test bodies too (pass fn names + functional language) when the model isn't timing out; on timeout, wait-then-retry rather than escalate. Two feedback memories saved (`feedback_delegate_test_writing`, `feedback_ollama_timeout_cache_retry`).

### Next
- Two tracks. **(LTG)** write `retrieval/anchors.py` TDD (`ref:ltg-phase3-decisions`; rebase `feature/ltg-phase3-anchors` onto master first). **(pipeline)** resume at **B3.1 F5 mechanics** (header-field bumps + session-N derivation + `rotate-session-log.sh`), then B3.2 F6 Orchestrator (stage→apply→verify→commit-or-rollback), B3.3 per-run logging, then B4 SKILL.md rewrite.
- F6 note: F4 must verify the COMBINED result of F3 payload edits + F5 header bumps — pass F5's field changes to F4 as `(field-region, new-value)` edits.

---

## 2026-06-04 - Session 83: Session-handoff pipeline — design + register (B1.1)

### Context
Resumed from an **emergency one-file handoff** (`​.claude/handoff-session-83.md`) — the prior session hit its limit mid-work. Goal: design (and start building) a replacement for the token-heavy `session-handoff` skill. The current skill makes Claude *decide → read every tracking file → write each section via many Edits*; the new design keeps *decide* with Claude and collapses *read+write* into one deterministic, register-driven pipeline call.

### What Was Done
- Designed **Scope A** and wrote two committed design docs: `docs/plans/session-handoff-pipeline-design.md` (`ref:handoff-pipeline-design`, the active plan) + `docs/plans/session-handoff-placer-enhancement.md` (`ref:handoff-placer-enhancement`, the deferred local-model layer). Indexed both (2 rows in `.claude/index.md`).
- Created branch `feature/session-handoff-pipeline` (stacked on `feature/ltg-phase3-anchors`; rebase onto master before any PR).
- **B1.1 done:** authored `overlays/session-tracking/registry.yaml` — 10 roles, all locators verified against the real files (4/4 ref keys, 3/3 header fields, `---` at line 7, `deferred-infra` block present). Tried the local model (`qwen2.5-coder:14b`) first → it produced valid YAML with **hallucinated ref-key names + wrong files/locators** → **verdict 0 (rejected)**, rewrote by hand. Lesson: load-bearing contracts = Claude authors; the hallucinated-locator failure is exactly what F1/F4 sandbox at runtime.
- This session resume (session 83): committed the four design/register files (`b18aba9`) and folded the handoff back into the tracking files.

### Decisions Made
- **Scope A = deterministic spine, NO local model.** The register supplies edit locations; Claude authors each block → every op reduces to replace / prepend / append / checkoff / nomodel.
- **The model became an enhancement, not a prerequisite** (expands *terse intent → prose*; saves authoring tokens). Fully deferred to the enhancement doc.
- **Localization reuses EXISTING handoff `ref:` blocks** via a shared per-repo register — **no new in-file markers** (rejected: would pollute the LTG corpus that ingests `.claude/`+`.memories/`). Register shared by `resume.sh` (read) + the pipeline (write) so they can't drift.
- **The register doubles as the handoff-owned-vs-content boundary** — every other ref key is content/LTG anchor the pipeline MUST NOT touch. Basis for a future portable-handoff overlay.
- **Task IDs in-file** (the lone new in-file element) → deterministic checkoff by id.
- **Home = the `session-tracking` overlay** (build here, propagate via overlay install).
- **F4 Verifier = the trust boundary:** hashes everything outside register-defined regions → corruption can't be committed; rollback is free (`git checkout` on verify-fail). This is what lets an untrusted model run later.

### Next
- Two tracks. **(LTG)** write `retrieval/anchors.py` TDD (`ref:ltg-phase3-decisions` = full spec; rebase onto master first). **(pipeline)** continue at **B1.2** (add task IDs to tasks.md), then B2 deterministic core (F1 Locator / F3 Applier / F4 Verifier, TDD).
- Full plan: B1 register+IDs → B2 safety core → B3 orchestrator+logging → B4 SKILL.md rewrite. See `ref:handoff-pipeline-design`.

---

## 2026-06-02 - Session 82: LTG Phase 3 anchor decisions frozen

### Context
Resumed from session 81 where Phase 3 discovery was in progress (D2/D5/D6/D7 open). Entry: read all Phase 3 docs, advisor framing handoff, and session-81 advisor review.

### What Was Done
- Worked through all Phase 3 anchor integration decisions in depth (D1b, D2, D3, D5, D6, D7) with five advisor passes
- Ran 2-pass anchor similarity probe (`retrieval/probes/anchor-similarity-probe-2026-06-02.py`) — 6 description methods against 69 stored topic vectors; key findings: mechanical+key validated, hyphenated > space-normalized, M:N multiplicity observed in data, `ref:ltg-corpus` honest orphan
- **All decisions frozen** in `retrieval/DECISIONS.md` (`ref:ltg-phase3-decisions`)
- Created `docs/plans/ltg-phase3-decisions-discussion.md` (`ref:ltg-phase3-discussion`) — full journey, all 5 advisor reviews, all angles
- Applied 5 corrections via subagent: anchor row field-population spec, D6 distance numbers (mechanical+key), grep pattern fix (literal KEY → regex), `node_kind` enum Phase 4 annotation, integrity-check universe
- Updated `tasks.md`: Phase 3 task updated to DECISIONS FROZEN; deferred task added for `ref-lookup.sh --paths` flag
- Committed 14 files; PR pending

### Decisions Made
- **Dual-path = yes** (keystone): `ref:KEY` anchors as a parallel retrieval surface, not merge-targets
- **D2 = A (repo-wide):** ingestion via `grep -rnoE '<!-- ref:[a-z0-9-]+ -->' . --include='*.md'`; `ref-lookup.sh --list` lacks file paths (verified)
- **D5 = alias-link, M:N:** both rows survive; `alias_of` JSON list; `node_kind` drops `merged`; `confidence` 0.7 not upgraded on alias; M:N validated in probe data
- **D3 = mechanical+key default:** key (hyphenated) + heading + first prose line; provisional on LTG-self-referential anchors; escalation = weak merge quality
- **D6 verified (with hedge):** cross-file merges at cosine 0.97/0.90 (mechanical+key); abstract-to-abstract class; Phase 2.5 for applied mentions
- **D7 → Phase 6:** Phase 3 = enablement only
- **D1b = config projection:** `source_class` denormalized, coarse start, separate axis from `node_kind`
- **Anchor confidence = structural authority:** not human-declared; `human_reviewed` deferred
- **Threshold provisional:** 0.85 cosine / L2 0.547; recalibrate Phase 2.5

### Next
- **Rebase `feature/ltg-phase3-anchors` onto master** after retrofit PR merges
- **Write `retrieval/anchors.py` TDD** — read `ref:ltg-phase3-decisions` as the full spec (ingestion grep, anchor row population, description method, alias-link, acceptance all specified)

---

## 2026-06-01 - Session 81: Retrofit close-out + LTG Phase 3 anchor discovery

### Context
Resumed post-session-80 to open the retrofit PR and start LTG Phase 3. Entry point: read all Phase 3 prep docs (concept paper, full plan, DECISIONS) + the session-80 advisor review.

### What Was Done
- **Retrofit close-out (sonnet sub-agent):** cleared the advisor punch-list. Live-ran the sweep once (`status=ok`, non-zero tokens — Gap A closed); fixed stale `bge-m3` refs in `embed.py` + documented Invariant D (Gap B/D); added `test_config_yaml_contract` regression test. **148 tests** (was 147), independently re-verified. Commits `1572b39`, `2dc49b2`. Retrofit PR was already open; pushed.
- **num_ctx three-way finding:** frozen spec + sweep = 16384 (validated point); production `config.yaml` drifted to 32768 (session 75/76 ctx upgrades). **Decision (c):** keep both deliberately; RECHECK before Phase 2.5. Recorded in `sweep_extractors.py`, `DECISIONS.md`, `tasks.md`. Commit `d17f446`.
- **Workflows guide:** wrote `.claude/workflows-feature-guide.md` (+ index entry) — dynamic workflows = script-orchestrated subagents at scale, NOT a session tracker; when-to-use; repo candidates (Phase 3 design, persona backfill, model surveys). Commit `ce885df`.
- **LTG Phase 3 DISCOVERY (not frozen):** new branch `feature/ltg-phase3-anchors`. Full discovery doc `docs/plans/ltg-phase3-anchor-discovery.md`. Reframes: (1) configurable per-class **weights** generalize anchor stratification; (2) three-confidence concepts (retrieval weight / node provenance / edge confidence); (3) `node_kind` vs `source_class` as separate axes, taxonomy as a config projection of `(file_path, node_kind)`; (4) **dual-path RAG** — `ref:KEY` anchors as a *parallel* retrieval surface (span-topics / ref-keys / both), pushing merge toward an **alias-link** model; (5) empirical enumeration: only 2 of 138 ref keys live in the 8 extracted files (orphans carry no merge-noise). Advisor reviewed (D2 pushback to A + surfaced D5/D6). Commits `76cdc4a`, `6638320`.

### Decisions Made
- **num_ctx (c):** keep benchmark 16384 / production 32768 divergent; recheck at Phase 2.5.
- **Advisor permission rule:** ask before `advisor()` in the main session (context-dup bug); subagents may call freely. Saved to memory.
- **Phase 3 settled:** D1=C (capture fields, defer weight tuning), D3=C-heuristic (embed description not raw block), D4=yes (extend schema while re-index is ~3s).
- **Phase 3 OPEN (next session):** D2 (anchor scope — user leans B, advisor+empirical lean A), D5 (merge representation/multiplicity — lean alias-link, many-topics:one-anchor), D6 (acceptance retarget to 2 in-corpus refs), D7 (path-selection binding time — query vs build, lean query). Nothing frozen — user had not finished analysing §4 empirical finding.

### Next
- **Resume LTG Phase 3 discussion from `docs/plans/ltg-phase3-anchor-discovery.md` §4 onward.** Work through the empirical enumeration, confirm/decide D2/D5/D6/D7 (+ re-confirm D1/D3/D4 under the dual-path reframe), then freeze into a `ref:ltg-phase3-decisions` block in `DECISIONS.md`. Only then write `anchors.py` (TDD) in a later session.
- Retrofit PR (`feature/ltg-extractor-retrofit` → master) open; Phase 3 branch stacked on it — rebase onto master after retrofit merges.

---

## 2026-06-01 - Session 80: LTG extractor retrofit — full implementation

### Context
Continuation of sessions 78/79 (prior compact). Picked up from Task 5 with Tasks 1–4 already committed on `feature/ltg-extractor-retrofit`. All 8 tasks executed this session.

### What Was Done
- **Task 5 — `sweep_extractors.py`:** `cp extract_topics.py sweep_extractors.py`; removed `FORMAT_SCHEMA` + `call_ollama`; added `_build_benchmark_config(model)` helper (injects `think:false` for qwen3 variants only); `run_single` gains `client` param; `run_sweep` creates one `ModelClient` and threads it. 13 new tests. Commit `8fdfe0a`.
- **Task 6 — `extract_topics.py` rewrite:** Full rewrite as 2-arm production runner (~160 lines vs 440). `route_file()` delegates to `routing.route()`; `run_file()` dispatches to `client.extract_prose/extract_code` based on extension; JSONL contract (run_id, timestamp, model, file, file_role, status, parsed_topics). 11 new tests. Commit `321d1a5`.
- **Task 7 — Bash wrappers:** `run-extract-topics.sh` + `run-sweep-extractors.sh` (4-line pattern matching `run-embed.sh`). Both registered in `.claude/index.md` `bash-wrappers` table. Commit `6ba7e25`.
- **Task 8 — Parity check (no commit):** Ran `extract_topics.py` on `docs/research/smart-rag-repowise.md` (prose) + `personas/build-persona.py` (code). Then `embed.py` on output. Result: 2 files, 16 topics, 0 failed. `extractor_model` field confirmed `qwen3:14b` for prose, `qwen2.5-coder:14b` for code. No "WARNING: no winning row". Pipeline contract verified end-to-end.
- **Total tests:** 147 green (was 123 entering this session).
- **Ollama timeouts:** `my-python-q25c14` timed out 4× on full-file generation prompts for `sweep_extractors.py`. Resolved by writing implementation directly (user granted permission). Root cause: large context payload, not cold-start. Fix: use targeted slices in future, not full files as context.

### Decisions Made
- **`_build_benchmark_config` injects `think` key only for qwen3 variants** — checks `MODEL_EXTRA_PARAMS` dict; omits key entirely for gemma3/coder (correct Ollama behavior per `ref:thinking-mode`).
- **`run_single` takes `client` as parameter** (dependency injection) — `run_sweep` creates one client, threads it down. Makes testing clean without network calls.
- **`extract_topics.py` drops rubric/sweep entirely** — clean separation: production runner vs benchmark are now distinct tools.
- **`record["model"]` comes from `ChatResult.model`** (what Ollama actually used), not from the role name — survives future model renames in config.

### Gotchas Discovered
- `generate_code` with full-file context (350+ lines) reliably times out on `my-python-q25c14`. Use targeted `start_line`/`end_line` slices per context_files entry, or skip `output_file` and write surgically via Edit.
- `rel_path` passed to `run_single` must be `str`, not `PosixPath` — f-string `{path:<45}` format spec rejects Path objects with `TypeError`.

### Next
- **Open PR** for `feature/ltg-extractor-retrofit` → `master`. All 8 tasks complete, 147 tests green, parity verified.
- **After merge: LTG Phase 3 — anchor integration** (`retrieval/anchors.py`). Read `ref:ltg-plan-phase-3` + `retrieval/DECISIONS.md` first.
- **Deferred cleanup:** `embed_texts(role=)` → named wrapper; `embed_batch_with_retry` → ModelClient unification (both out-of-scope for this retrofit; tracked in tasks.md).

---

## 2026-05-30 - Session 77: LTG extractor retrofit — design complete

### Context
All PRs merged, master current. Entire session focused on design for the `extract_topics.py` → `model_client.py` retrofit (prereq for LTG Phase 3). Two advisor reviews. No implementation started — context hit 62% and a full plan was written for a fresh session.

### What Was Done
- **Extensive file reading:** `extract_topics.py`, `model_client.py`, `embed.py`, `config.yaml`, all test files, `ltg-model-registry-design.md`, `extract.txt` prompt, Phase 3 plan, `run-embed.sh`.
- **4 design Q&A settled:** ChatResult shape (`NamedTuple(content, model, prompt_tokens, eval_count)`), config YAML layout (YAML `options:` sub-dict + `think` as top-level sibling), role names (`extraction_prose`/`extraction_code`), schema location (`retrieval/schemas.py`).
- **Fork decision (two advisor passes):** Path B (production 2-arm runner) + `sweep_extractors.py` (benchmark). `extract_topics.py` keeps canonical name; `sweep_extractors.py` is the new file. Named methods (`extract_prose`/`extract_code`) for production; generic `call(prompt, model_config, schema)` for benchmark (dynamic-roles exception per pattern doc).
- **§1 pipeline contract identified:** `embed.py`'s `winning_extractor` + `select_winning_row` must agree with production runner's model name output. Fix: `routing.py` as single source of truth for `CODE_EXTENSIONS` + `route(path)→role`; `embed.py` imports from it.
- **`docs/patterns/code-design-conventions.md` written:** Language-agnostic pattern for named semantic methods (code as documentation). Python + Go examples. `ref:patterns-code-named-methods`. Added to `technology-conventions.md` index + `index.md`.
- **`feedback_code_as_documentation.md` saved to memory.**
- **`retrieval/tests/test_routing.py` written (TDD):** 14 tests for `routing.py`, confirmed red (ModuleNotFoundError). Committed on branch.
- **`docs/plans/ltg-extractor-retrofit.md` written:** Complete implementation guide — mandatory reading list, all settled decisions, per-task TDD guidance, local model call patterns (model: `my-python-q25c14`, timeout: 600), parity check criteria, out-of-scope items.
- **Branch `feature/ltg-extractor-retrofit` created.** 2 commits.
- **8-task list created** (session task tracker) covering routing.py → schemas.py → model_client.py → config.yaml → sweep_extractors.py → extract_topics.py → bash wrappers → parity check.

### Decisions Made
- **Fork B + sweep_extractors.py:** `extract_topics.py` → 2-arm production runner; benchmark sweep preserved in `sweep_extractors.py`.
- **ModelClient surface:** `extract_prose()`, `extract_code()` (named, production); `call(prompt, model_config, schema, timeout)` (generic, benchmark); `_chat()` private, owns all Ollama quirks.
- **`_chat` takes resolved config dict** (not role string) — named methods resolve role→dict; `call()` passes dict directly. Shared HTTP core.
- **ChatResult:** `NamedTuple(content, model, prompt_tokens, eval_count)`. Caller keeps wall-clock for tok/s.
- **config.yaml two-level:** `models:` + `roles:` with `options:` sub-dict for `num_ctx`/`temperature`; `think: false` as top-level sibling key (NOT inside `options{}`); `timeout_s` per model.
- **`schemas.py`:** `TOPIC_FORMAT_SCHEMA` moves to `retrieval/schemas.py` (leaf module). Imported by `model_client.py` + `sweep_extractors.py`.
- **Timeout:** config `timeout_s` default + caller override. 14B extractors: 600s. Never inherit `embed_texts`'s 120s.
- **Error handling:** `_chat`/`call` raise; caller classifies status taxonomy.
- **Code as documentation:** named methods over role strings — stored in memory + pattern doc.

### Next
- **Start implementation from `docs/plans/ltg-extractor-retrofit.md`** on branch `feature/ltg-extractor-retrofit`.
- **Read mandatory list first** (plan file § "Mandatory reading") — especially `.claude/overlays/local-model-conventions.md`.
- **Task 1 is ready:** `retrieval/tests/test_routing.py` exists (14 tests, confirmed red). Call `my-python-q25c14` with `timeout=600` to generate `routing.py`.

---

