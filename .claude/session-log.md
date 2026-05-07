# Session Log

**Current Layer:** LTG Phase 1 — topic extractor spike CLOSED via two-rater reconciliation (Branch C); final freeze pending determinism re-run + MoE eval
**Current Session:** 2026-04-30 — Session 58: LTG Phase 1 two-rater reconciliation closes Phase 1 (Branch C)
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`

---

## 2026-04-30 - Session 58: LTG Phase 1 two-rater reconciliation closes Phase 1 (Branch C)

### Context
Resumed mid-day on `feature/ltg-phase1-scoring-and-notes` (session 57's branch). User signaled "Manual viz is done; ltg-rater-...-215756Z.json also has individual scores for (almost) each topic" — i.e., the user-track HTML-viz scoring complete, with richer per-topic data than the original rater. This was the queued reconciliation step from session 57's "Next" pointer. User explicitly directed: commit on a new branch, then session-handoff, then PR.

### What Was Done
- **Reconciled user track (manual-rubric.md, 32/32 cells) with Claude draft.** Per-cell delta analysis: **identical 4-model ranking and identical pass/fail verdicts** under both raters. User track systematically more lenient (per-model Δ_avg: gemma +0.21, qwen3:14b +0.18, coder +0.40, qwen3:8b +0.36) but the relative ordering and gating decisions hold.
- **Applied Branch C** from `ref:ltg-phase1-pending-revisions` per the pre-registered decision tree. Cross-rater agreement: agree on `smart-rag3.md` (qwen3:14b wins, both raters); disagree on `smart-rag-index.md` (Claude: qwen3:8b > qwen3:14b by +0.12; User: qwen3:14b > qwen3:8b by +0.15). Mixed → Branch C: keep 2-arm production routing (qwen2.5-coder:14b for code, qwen3:14b for prose); cross-ref-index 3rd-arm hypothesis preserved as deferred Phase 2 item.
- **Final 8/8 adjusted scores (Claude / User):** qwen3:14b 2.44 / 2.61 ✅ winner; qwen3:8b 2.27 / 2.63 ✅ backup; qwen2.5-coder:14b 1.76 / 2.16 ❌ (borderline under user, 0.04 below threshold — corpus expansion could plausibly flip); gemma3:12b 1.61 / 1.82 ❌.
- **Edited `retrieval/spike-results.md`** (5 surgical edits): filled user scores table (32 cells, was placeholder); added Two-rater reconciliation section with decisive cells + Branch C resolution + largest single-cell disagreement note (QUICK.md × gemma3 Δ=−0.93) + dim-8 reweight question; softened pre-reconciliation routing claims in Claude draft block; added insight #9 to `ref:ltg-phase1-insights` (rubric fit-for-purpose for binary decisions; ~0.2–0.4 calibration drift for continuous reuse); rewrote `ref:ltg-phase1-routing-hypothesis` block per Branch C with explicit 2-arm production + 3 deferred Phase 2 items.
- **Updated `.memories/KNOWLEDGE.md`** "LTG Phase 1 Extractor Spike — Findings" section: replaced preliminary 5/8 table with final 8/8 reconciled (Claude + User columns), added production-routing summary + rater-calibration takeaway for Layer 7 / DPO scoring.
- **Updated `.claude/tasks.md`:** marked "score remaining 4 corpus files" complete; added 2 new deferred items in `ref:deferred-infra` — (a) cross-reference-index 3rd-arm routing hypothesis (defer-to-Phase-2 with re-eval triggers), (b) per-topic JSON (648 scores) as Phase 2 input.
- **Updated `.memories/QUICK.md` (root) + `retrieval/.memories/QUICK.md`:** refreshed status blocks from "session 56, 5/8 in progress, preliminary winner" to "session 58, reconciliation closed, 2-arm production, freeze pending determinism + MoE". Confirmed other per-folder QUICK.md / KNOWLEDGE.md files (evaluator, mcp-server, overlays, personas, benchmarks) do not reference Phase 1 content — left untouched.
- **Branch + commits:** Created `feature/ltg-phase1-reconciliation-session-58` off `feature/ltg-phase1-scoring-and-notes` (session 57's branch — not master, because the reconciliation depends on session 57's `ref:ltg-phase1-pending-revisions`). Two commits: `c3fdcdd` (reconciliation core: spike-results.md + KNOWLEDGE.md + tasks.md + tracked manual-rubric.md + tracked latest JSON export) and `34cfaa8` (chore: QUICK.md memory updates).

### Decisions Made
- **Branch C selected mechanically** per the pre-registered decision tree from session 57 (`ref:ltg-phase1-pending-revisions`). Rationale: agree on `smart-rag3` flip but disagree on `smart-rag-index` flip → Branch C (mixed). The pre-registration prevented post-hoc rationalization of which branch fits the data.
- **3rd-arm hypothesis preserved as deferred, not killed.** Re-eval triggers documented: (a) determinism re-run on smart-rag-index × qwen3:14b confirms/refutes off-by-one, (b) more cross-reference-index files added to corpus (n=1 → n≥3), (c) MoE candidates evaluated. Determinism re-run is cheapest (~30s) and answers the deferred question directly.
- **Dim-8 reweight question (insight #6) NOT load-bearing for ranking** — both rater tracks produce identical pass/fail; deferred to Phase 2 as a refinement that would matter only if the rubric is later repurposed for continuous DPO scoring.
- **Per-topic JSON (648 scores in 29/32 cells) deferred to Phase 2** — could supply per-topic boundary evidence to disambiguate the 3rd arm without corpus expansion. Out of scope for Phase 1 binary freeze.
- **Branch off current session 57 branch, not master** — reconciliation depends on the `ref:ltg-phase1-pending-revisions` block introduced in session 57; branching off master would create a base where the decision tree doesn't exist.
- **Tracked the user-track source files** (`retrieval/runs/manual-rubric.md` + `…215756Z.json`) alongside the doc edits because spike-results.md cites them. Other intermediate exports + manual-rubric backups left untracked.

### Next
- **Push `feature/ltg-phase1-reconciliation-session-58`** + open PR (final step of this session).
- **Determinism re-run on `smart-rag-index.md` × qwen3:14b** — now the cheapest gating evidence remaining (~30s of compute). If the off-by-one on the 7 pattern bullets reproduces under 2 more sweeps, that's the missing Phase 1 evidence for the deferred 3rd arm. Apply stability bonus (+0.5 if Jaccard ≥ 0.85, +0.25 if ≥ 0.80) to weighted_quality before the formal freeze decision.
- **Prompt-iteration experiment** (still deferred from sessions 55/57): topic-count floor `max(5, major_section_count)` + containment-only overlap rule. Cheap re-sweep on existing 8 files; would directly test whether qwen3:8b's whole-section-drop failure mode is fixable in-prompt.
- **Phase 2 VRAM co-residence probe** (qwen3:14b + bge-m3 ≈ 12 GB on 12 GB card) folded with **MoE extractor eval** (qwen3:30b-a3b, qwen3-coder:30b) per `ref:ltg-phase1-routing-hypothesis`.
- **Formal `ref:ltg-extractor` decision-replacement** in `retrieval/DECISIONS.md` once determinism + MoE evidence lands. Branch C does NOT pre-commit the freeze; only the routing hypothesis.
- **Still open:** session 57 PR for `feature/ltg-phase1-scoring-and-notes`; PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; Layer 4 stragglers; registry hot-reload; server.py refactor.

### Notable
- **Largest single-cell disagreement: `.memories/QUICK.md` × `gemma3:12b` (Δ=−0.93).** The only cell of 32 where the user track is harsher than Claude. User scored d5=0 with explicit note about semantic hallucination ("infers wrong ideas, strange decisions on spans"). Sharpens gemma's `❌` rather than weakening it — the failure mode is *semantic hallucination on dense memory files*, which Claude's per-file scalar underweighted.
- **Coder borderline:** under user track, qwen2.5-coder:14b finishes at 2.16 adjusted (0.04 below threshold) vs Claude 1.76 (0.44 below). Same verdict but margin is small enough that 2-3 more code files in the corpus could flip it.
- **Methodological insight for Layer 7:** rubric is fit-for-purpose for binary decisions; absolute scores diverge by ~0.2–0.4 weighted-quality points across raters. Continuous reuse (DPO scoring) would need inter-rater calibration.
- **Pre-registered decision tree paid off.** Session 57 wrote down what each user-track outcome would mean before seeing the user's scores. Branch C applied mechanically rather than getting argued into Branch A on weak grounds. Worth carrying forward to determinism + MoE eval (pre-register what each outcome means).

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

