# Session Log

**Current Layer:** LTG Phase 1 — topic extractor spike (Claude draft track CLOSED, awaiting two-rater reconciliation)
**Current Session:** 2026-04-25 — Session 57: Score remaining 3 corpus files + capture rater notes (Claude draft 8/8 complete)
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`

---

## 2026-04-25 - Session 57: Score remaining 3 corpus files + capture rater notes (Claude draft 8/8 complete)

### Context
Resumed mid-day on `feature/ltg-rater-redesign` (session 56 had landed the new rater template + viz_sweep wiring earlier today). User asked first about the in-flight viz refactor (since-resolved by session 56), then directed three sequential scoring sessions: KNOWLEDGE.md, smart-rag-index.md, smart-rag3.md. Closed at 8/8 + captured all unwritten insights to ref blocks before session ended.

### What Was Done
- **Scored `.memories/KNOWLEDGE.md` (file 6 of 8):** 214-line, 10-section repo knowledge doc. qwen3:14b 2.85 (joint-best in spike), qwen3:8b 2.25, coder 2.30, gemma3 1.60. Confirmed insight-#4 reproduction (qwen3:8b dropped Smart RAG section 117-151 entirely; gemma3 conflated Smart RAG + LTG into one mega-topic).
- **Scored `docs/research/smart-rag-index.md` (file 7 of 8):** 64-line cross-reference index with 7 dense numbered pattern bullets. **First file in spike where qwen3:8b (2.55) outscored qwen3:14b (2.43)** — qwen3:14b had off-by-one errors on 3 of 7 pattern bullets (graph_exploitation→[23] should be [24], etc.). coder 1.83 with rule-3 violation (`cross_cutting_patterns [21,29]` structural meta-topic) and "kitchen-sink line 35" pattern. gemma3 1.35 with coverage 0.344 (below rule-2 floor).
- **Scored `docs/ideas/smart-rag3.md` (file 8 of 8):** 84-line architectural design doc. qwen3:14b 2.85 (rebound, tied with KNOWLEDGE.md for joint-best). qwen3:8b drops back to 2.30 (kitchen-sink span [10,22], three topics claiming [76,81]). coder 1.55 — **worst single-file score in the entire spike** (three structural-meta topics, all rule-3 violations). gemma3 1.40 with self-overlapping spans + crossed-overlap on [63,64].
- **Final 8-file Claude draft averages (after speed penalty):** qwen3:14b 2.44 (winner), qwen3:8b 2.27 (backup, best on cross-ref index), coder 1.76 (fails), gemma3 1.61 (fails).
- **Added 3 new numbered insights to `ref:ltg-phase1-insights`:**
  - **#6** Section-drop pattern reproduces (qwen3:8b confirmed structural, not anecdotal — KNOWLEDGE.md + persona-template.md); rubric under-penalises (dim 8 only 10% — qwen3:8b cleared 2.2 threshold despite missing 22% of file content).
  - **#7** Cross-reference index breaks qwen3:14b's lead via off-by-one on dense bullets with inline punctuation density. Off-by-one is **model-agnostic format failure** — coder hit it on smart-rag-repowise.md, qwen3:14b hits it on smart-rag-index.md.
  - **#8** Paired-file natural experiment (smart-rag-index ↔ smart-rag3, same content opposite format) shows 0.55-point swing for qwen3:8b and 0.42-point swing for qwen3:14b in opposite directions — **cleanest evidence in spike that format-sensitivity dominates content-sensitivity**.
- **Created `retrieval/spike-rater-notes.md`** with three new ref blocks (held outside `.memories/KNOWLEDGE.md` deliberately to avoid biasing user-track HTML-viz scoring):
  - `ltg-phase1-claude-rater-notes` — per-cell scoring rationale + evidence quotes for all 3 files scored this session
  - `ltg-phase1-meta-insights` — file-class taxonomy (4 roles, n=1/n=2 caveats), paired-file methodology recommendation, per-model trend observations, reconciliation priorities, mechanical post-pass guards (coverage cap >60%, containment overlap check)
  - `ltg-phase1-pending-revisions` — stale-wording cleanup queue (3 items) + three conditional drafts (A/B/C) for routing-hypothesis revision based on user-track outcome, with decision tree
- **Updated `.claude/index.md`** Phase 1 Spike Results table: refreshed counts (4/8 → 8/8), refreshed numbered findings list (#1-#3 → #1-#8), added rows for the 3 new ref keys.
- **Branch + commit:** Created `feature/ltg-phase1-scoring-and-notes` off `feature/ltg-rater-redesign`. Single commit `2330e04` adds spike-results.md edits + spike-rater-notes.md + index.md updates.

### Decisions Made
- **Hold-until-reconciliation policy:** Per-cell rationale, meta-insights, and pending revisions all live in `retrieval/spike-rater-notes.md` rather than `.memories/KNOWLEDGE.md`. Codifying findings into knowledge-tier memory before user-track scores arrive would bias the user's independent rater calibration.
- **Pre-written conditional revisions (A/B/C):** Three drafts of the routing-hypothesis revision queued in `ref:ltg-phase1-pending-revisions`, conditional on whether user track agrees on insight #8 ranking flip (Branch A: 3-arm; Branch B: 2-arm; Branch C: mixed). Decision tree included so a future session can execute mechanically.
- **New branch instead of committing to `feature/ltg-rater-redesign`:** Scoring + insights are findings, not infrastructure. Splitting them into separate PRs lets reviewers engage with the patterns without re-litigating the tooling.
- **3-arm routing story is empirically backed but n=1 on cross-ref arm:** Insight #8 is the cleanest controlled experiment in the spike; routing-hypothesis revision Branch A captures it but with explicit "n=1, fragile" caveats and gating on determinism re-run.

### Next
- **Open PR for `feature/ltg-phase1-scoring-and-notes`** (queued — final step of this session).
- **User completes HTML-viz scoring track** (in progress; manual-rubric.md.1.md/.2.md/.3/.4 backups present in working tree).
- **Two-rater reconciliation:** Diff Claude draft vs user track per cell. Apply Branch A/B/C from `ref:ltg-phase1-pending-revisions` based on outcome. Then apply stale-wording cleanup (3 items) and update `.memories/KNOWLEDGE.md` "LTG Phase 1 Extractor Spike — Findings" section to final 8/8 numbers.
- **Determinism re-run on `smart-rag-index.md` for qwen3:14b** (cheap; ~30s of compute) — does the off-by-one on the 7 pattern bullets reproduce, or was the sweep sample-unlucky? This is gating evidence for the 3-arm routing arm.
- **Prompt-iteration experiment** (deferred from session 55): topic-count floor `max(5, major_section_count)` + containment-only overlap rule. Cheap re-sweep on existing 8 files; would directly test whether qwen3:8b's whole-section-drop failure mode is fixable.
- **Then:** MoE probe (qwen3:30b-a3b, qwen3-coder:30b) folded into Phase 2 VRAM co-residence work; formal `ref:ltg-extractor` decision-replacement in `retrieval/DECISIONS.md`; routing-hypothesis revision applied per chosen branch.
- **Still open:** PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; Layer 4 stragglers; registry hot-reload; server.py refactor.

---

## 2026-04-25 - Session 56: LTG rater page redesign (Claude Design + viz_sweep wiring)

### Context
Short tooling session. Entry point: user wanted the HTML-viz scoring page URL, then pivoted to redesigning it using Claude Design (claude.ai artifact builder).

### What Was Done
- **Located viz at** `retrieval/runs/20260416-181839.html` and confirmed how to open it in Windows from WSL2.
- **Generated Claude Design brief:** Instructions + self-contained prompt covering the data schema, behavioral spec (localStorage, export, span-chip highlighting), and 8 specific improvement goals (keyboard scoring, model-comparison view, sticky progress bar with per-file coloring, better card density, resizable split, prominent metrics, dark/light toggle, error state polish).
- **Generated representative JSONL slice** (`retrieval/runs/20260416-181839-design-slice.json` — 57 KB): 4 models on `smart-rag-repowise.md` (multi-model comparison case) + 1 `qwen2.5-coder:14b` run on `build-persona.py` (code file_role variation), plus both source files. Bundled as `{tag, weights, exit_threshold, data, sources}` envelope matching the Design prompt spec.
- **User ran Claude Design** and produced `retrieval/ltg-rater.template.html` (>1600 lines).
- **Wired template into `retrieval/viz_sweep.py`:**
  - Added `TEMPLATE_PATH` constant pointing to the new file
  - Replaced inline `HTML_TEMPLATE` string literal usage in `build_html` with `TEMPLATE_PATH.read_text()`
  - Updated placeholder tokens: `__TAG__` / `__DATA_JSON__` / `__SOURCES_JSON__` → `__TAG_PLACEHOLDER__` / `__DATA_PLACEHOLDER__` / `__SOURCES_PLACEHOLDER__`
- **Diagnosed and fixed DATA envelope mismatch:** First render showed the correct tag in the header but no records/models. Root cause: template reads `DATA.data` (envelope shape from slice JSON), but renderer was injecting a bare array. Fixed `build_html` to wrap records as `{tag, weights, exit_threshold, data: [...]}`; SOURCES stays as bare map (template reads `SOURCES[path]`). Re-rendered cleanly: 32 records, 8 sources, 288 KB.

### Decisions Made
- **Template read from disk per render call** (not imported at module load) — enables iterating on the HTML in Claude Design and re-running without restarting Python.
- **Legacy `HTML_TEMPLATE` string stays in `viz_sweep.py` as dead code** for this session — safe to delete in a follow-up once the new template is confirmed on all edge cases (error rows, missing topics, etc.).
- **Envelope shape is authoritative:** `weights` and `exit_threshold` now flow from Python → template. Any future rubric changes should be made in `viz_sweep.py`, not in the template JS.

### Next
- **Score remaining 3 corpus files** (either Claude draft or user HTML-viz track): `docs/research/smart-rag-index.md`, `docs/ideas/smart-rag3.md`, `.memories/KNOWLEDGE.md`. KNOWLEDGE.md highest priority.
- **Reconcile two-rater scores:** Export `manual-rubric.md` from viz localStorage → compare with Claude's draft in `retrieval/spike-results.md`. Record divergences. Gate extractor freeze on agreement.
- **After all 8 scored:** Commit `feature/ltg-phase1-extractor-spike`, open PR.
- **Then:** prompt-iteration experiment (topic-count floor + containment-only overlap); determinism re-runs (dim 9 Jaccard); Phase 2 VRAM co-residence probe.
- **Delete `HTML_TEMPLATE` dead code** from `viz_sweep.py` once new template confirmed stable.
- **Still open:** PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; Layer 4 stragglers; registry hot-reload; server.py refactor.

---

## 2026-04-17 - Session 55: persona-template.md scored + two-rater framing + overlap-semantics insight

### Context
Resumed on `feature/ltg-phase1-extractor-spike`. Entry point was `@.claude/session-context.md resume` followed by a correction: the 4 already-scored files were scored **by Claude in session 54 (draft)**, not by the user — user's independent HTML-viz scoring is still in progress. That reframed the rest of the session around two-rater scoring and the next most diagnostic file to score.

### What Was Done
- **Relabeled `retrieval/spike-results.md` scoring table as "Claude's scores" (draft)** + added an empty "User's per-file scores" table to be exported from HTML viz localStorage. Two-rater agreement now gates the final extractor freeze.
- **Picked `personas/persona-template.md` as next file** — highest-information pick because it's the only semi-structured YAML+prose template in the corpus (other remaining files duplicate already-scored types).
- **Scored persona-template.md across all 4 models** (dims 5-8 + weighted):
  - `qwen3:14b` → **2.65** (9 topics / 9 natural sections, contiguous, zero overlap — cleanest output of any (model, file) pair in the spike)
  - `qwen3:8b` → **2.25** (best descriptions of any model on this file, but **missed Registration section 154-163 entirely**; `system_prompt_structure` bleeds into Temperature Guide)
  - `qwen2.5-coder:14b` → **2.00** (5-line Rules subsection dropped inside `system_prompt` span)
  - `gemma3:12b` → **1.35** (missed Naming Convention 140-150; `parameter_tuning` overlaps 2 other topics; boilerplate drag on dim 6)
- **Updated 5-file averages:** qwen3:14b 2.67 / qwen3:8b 2.21 / coder 2.08 / gemma3 1.71. After speed penalty: **2.42 ✅ / 2.21 ✅ / 1.83 ❌ / 1.71 ❌**. Ranking stable; qwen3:14b's cross-file consistency hardens.
- **Added two new insights to `ref:ltg-phase1-insights`:**
  - #4 **Whole-section drops under topic-budget pressure** — both sub-optimal models (qwen3:8b, gemma3:12b) produced fewer topics than the file's section count and silently omitted a section instead of merging. Dim 8 catches this.
  - #5 **Partial cross-overlap vs hierarchical containment** — revised after user pushback. Rule should be "containment OK, crossed NOT OK": allow child ⊆ parent (supports LTG multi-scale / anchor stratification per `ref:concept-latent-topic-graph`), forbid partial intersection with neither span subset. Mechanical post-hoc check: `intersection == smaller_span`.
- **Added new deferred task** (`ref:deferred-infra`): prompt iteration combining (1) topic-count floor = `max(5, major_section_count)` and (2) containment-only overlap rule. Two cheap guardrails, both grounded in persona-template.md evidence.

### Decisions Made
- **Two-rater scoring track:** Claude's scores are a draft; user's HTML-viz scores are authoritative. Divergence on specific dims = rubric calibration signal, not a tie-breaker. Gate extractor freeze on agreement.
- **Overlap semantics — containment is a feature, crossed is a bug.** User pointed out that forbidding all overlap would suppress the multi-scale retrieval pattern the LTG concept paper relies on. Revised the "no shared lines" rule to "intersection must equal smaller span". Also gives the graph a free parent→child hierarchy edge.
- **Topic-count floor is worth testing.** Under-budget extraction is a silent failure mode (whole sections vanish with no warning). A floor forces either broader topics or more of them — either is better than dropped content.

### Next
- **Score 3 remaining files:** `docs/research/smart-rag-index.md`, `docs/ideas/smart-rag3.md`, `.memories/KNOWLEDGE.md`. Either Claude continues the draft track, or user's HTML-viz scoring closes first — both paths acceptable. KNOWLEDGE.md is the highest-priority remaining (pairs with QUICK.md for memory-file size sensitivity).
- **After all 8 scored:** export manual-rubric.md from viz (user track) + compare against Claude's draft. Record divergences. Commit `feature/ltg-phase1-extractor-spike` and open PR.
- **Then:** determinism re-runs on winner (dim 9 Jaccard), MoE probe folded into Phase 2 VRAM co-residence, prompt-iteration experiment (topic-count floor + containment-only overlap).
- **Still open:** PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; Layer 4 stragglers; registry hot-reload; server.py refactor.

---

## 2026-04-16 - Session 54: Phase 1 sweep executed + HTML scorer viz + 4/8 files scored

### Context
Resumed on `feature/ltg-phase1-extractor-spike` with the extractor runner already built (session 53). Goal: run the sweep and produce a verdict for `ref:ltg-extractor`.

### What Was Done
- **Ran Phase 1 sweep:** `python3 retrieval/extract_topics.py` — 4 models × 8 files = 32/32 ok. Had to `pip3 install httpx` first. Raw results at `retrieval/runs/20260416-181839.{jsonl,summary.txt,manual-rubric.md}`.
- **Built `retrieval/viz_sweep.py`** — self-contained HTML viewer for sweep results. Features: model/file filters, live stats strip, per-card span chips that highlight source lines in a right-hand pane, duplicate-span-set auto-flag, inline rubric scorer (dims 5-8 dropdowns + notes + weighted_quality badge), localStorage persistence keyed by run_id, export-to-markdown button. Rebuilt once after a security hook flagged `innerHTML` — refactored to `createElement`/`textContent`. Help panel embedded for in-viz rubric reference.
- **Scored 4/8 files manually:** QUICK.md, smart-rag-repowise.md, plan-v2.md, build-persona.py. Raw averages: qwen3:14b=2.68, qwen3:8b=2.20, qwen2.5-coder:14b=2.10, gemma3:12b=1.80. With speed penalty (−0.25 if <15 tok/s): qwen3:14b=2.43 ✅, qwen3:8b=2.20 ✅, coder=1.85 ❌, gemma3=1.80 ❌.
- **Saved findings with ref:KEY blocks:** `retrieval/spike-results.md` (new file) — three blocks: `ltg-phase1-results` (scoring + verdict), `ltg-phase1-insights` (coder prose-vs-code split, qwen3:8b duplicate spans on plan-v2, gemma3 boilerplate), `ltg-phase1-routing-hypothesis` (specialized-model routing + MoE probe).
- **Indexed in tracking files:** `.claude/index.md` gets a new LTG Phase 1 Spike Results section with the three ref keys; `.claude/tasks.md` gets 5 new deferred items under `ref:deferred-infra` (score remaining 4 files, determinism re-runs, MoE eval, routing study, bash wrappers for retrieval tools).

### Decisions Made
- **Preliminary extractor pick:** `qwen3:14b` (not frozen — gates on remaining 4 files, determinism re-runs, MoE eval). Pick the default now to unblock Phase 2 integration.
- **Viz format: static HTML** (not CLI/Streamlit). Self-contained, no deps, works offline, persists to localStorage.
- **Scoring granularity: holistic per-record** (one dim5 score across all ~7 topics in a record), notes field for specific topic-level observations. Per-topic scoring rejected as overkill for this spike (would have been ~250 cells vs 32).
- **Speed penalty: −0.25 if <15 tok/s** (rubric left the amount undefined; this is the session 54 working value).
- **Interesting finding worth chasing later:** `qwen2.5-coder:14b` was off-by-one on prose spans but tight on code. Motivates file-type-routed extractor — captured as `ref:ltg-phase1-routing-hypothesis`.

### Next
- **Score the remaining 4 files** using the HTML viz (`retrieval/runs/20260416-181839.html`): `smart-rag-index.md`, `smart-rag3.md`, `persona-template.md`, `KNOWLEDGE.md`. User said next session they want further analysis on those files.
- **After scoring complete:** export manual-rubric.md from viz, commit the branch, open PR for `feature/ltg-phase1-extractor-spike`.
- **Still open:** determinism re-runs on winner (dim 9); MoE extractor eval (fold into Phase 2 VRAM co-residence probe); specialized-routing study (add code files to corpus).

---

