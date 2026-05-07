<!-- ref:ltg-phase1-claude-rater-notes -->
# LTG Phase 1 — Claude Draft Rater Notes

**Purpose.** Per-file scoring rationale for the Claude draft track of the LTG Phase 1 extractor spike. Companion to `ref:ltg-phase1-results` (the score table) and `ref:ltg-phase1-insights` (the numbered findings #1–8). This document captures the reasoning behind each cell, evidence quotes, and per-file observations not abstracted into a numbered finding. **Critical input for two-rater reconciliation:** divergence on a score is more diagnostic when you can compare the rationale, not just the number.

**Held outside `.memories/KNOWLEDGE.md` deliberately** until two-rater reconciliation completes — premature codification would bias the user-track HTML-viz scoring.

## Conventions

- Scoring scale: **0–3 per dim, half-points allowed**.
- Weighted formula: `weighted = 0.35·d5 + 0.35·d6 + 0.20·d7 + 0.10·d8`.
- Dim definitions (from `retrieval/ltg-rater.template.html`):
  - d5 = name (specific & memorable)
  - d6 = description (concrete, file-specific)
  - d7 = boundary (spans fit the name)
  - d8 = coverage (file's salient content)
- Speed penalty: −0.25 if model TPS < 15 (applied to model averages, not individual cells).
- Files scored sessions 54-56 by Claude (4 of 8): QUICK.md, smart-rag-repowise.md, plan-v2.md, build-persona.py, persona-template.md.
- Files scored this session (3 of 8): KNOWLEDGE.md, smart-rag-index.md, smart-rag3.md.
- All raw model outputs in `retrieval/runs/20260416-181839.jsonl`.

## Per-file rationale (this session — files 6, 7, 8 of 8)

### `.memories/KNOWLEDGE.md` (file 6 of 8) — file role: `medium_mixed_content`

**Snapshot at sweep time.** 214 lines, **10 H2 sections**. The "LTG Phase 1 Extractor Spike — Findings" section was added in sessions 54-56 *after* the sweep ran, so models scored a 10-section, not 11-section, file. Section boundaries derived from qwen3:14b's near-perfect output (no ground-truth section table existed; qwen3:14b's 1:1 mapping is the de-facto reference here).

**Sweep-time section map:**

| # | Section | Lines |
|---|---|---|
| 1 | VRAM Budget Constraints | 5-21 |
| 2 | Model Tier Findings | 22-39 |
| 3 | Prompt Decomposition | 41-50 |
| 4 | Cross-Repo Architecture | 51-66 |
| 5 | DPO Data Collection | 67-78 |
| 6 | Local-First with Frontier Escalation | 79-89 |
| 7 | Claude Code Source + Related Repos | 90-116 |
| 8 | Smart RAG / Content-Linking Research | 117-151 |
| 9 | Latent Topic Graph — Concept + Plan | 162-203 |
| 10 | Structured Output via Grammar-Constrained Decoding | 204-213 |

(Lines 152-161 = LTG section heading + intro — natural gap.)

**`qwen3:14b` — d5=3, d6=3, d7=2.5, d8=2.5 → 2.85**
- 10 topics, exact 1:1 with sections.
- d5 = 3: distinct semantic names. "model_tier_performance" is more abstract than coder's literal "model_tier_findings"; "local_first_frontier_escalation" sharper than gemma's truncated "local_first_escalation".
- d6 = 3: active-verb descriptions ("Discusses", "Analyzes", "Explores", "Describes", "Details", "Presents", "Reviews", "Introduces") — no "This topic" boilerplate; captures the rationale of each section.
- d7 = 2.5: section-aligned spans, slight off-by-one (model_tier ends at 40 vs 39, local_first starts at 80 vs 79) and the lines 152-161 gap (LTG heading) — minor.
- d8 = 2.5: ~92% coverage per auto-rubric, all 10 sections represented as distinct topics.
- **Joint-best single-file score in spike, tied with smart-rag3.md (also 2.85).**

**`qwen3:8b` — d5=2.5, d6=2.5, d7=2, d8=1 → 2.25**
- 9 topics; **dropped Smart RAG section entirely** (lines 117-151 unscored — gap between `claude_code_integration [90,115]` and `latent_topic_graph [162,203]`).
- d5 = 2.5: good semantic names but missing one whole concept (smart_rag).
- d6 = 2.5: clean substantive descriptions, no boilerplate.
- d7 = 2: within-section fragmentation (vram split `[5,14]+[18,21]` skipping the rationale lines 15-17), claude_code ends at 115 (truncated by 1 line). Awkward but not wrong.
- d8 = 1: whole section dropped (~22% of file unscored). Confirmed reproduction of insight #4.
- **Second confirmed instance of qwen3:8b dropping a mid-file section** (first was Registration in persona-template.md). Pattern is now structural, not anecdotal.

**`qwen2.5-coder:14b` — d5=3, d6=2, d7=1.5, d8=2.5 → 2.30**
- 10 topics, section-heading-rephrased names.
- d5 = 3: distinct, semantic, no merges (literal mapping but valid for this file's structure).
- d6 = 2: terse generic descriptions ("Discussion of VRAM limitations and their impact on model architecture and performance" vs qwen3:14b's "trade-offs between model size, context length, and inference speed"). Substance acceptable, lacks specificity.
- d7 = 1.5: smart_rag span ends at 162 (overruns into LTG heading), LTG span ends at 195 (truncates LTG by ~8 lines). Same boundary-bleed pattern as smart-rag-repowise.md prose case.
- d8 = 2.5: ~93.5% coverage, all sections represented.

**`gemma3:12b` — d5=2, d6=1, d7=2, d8=1.5 → 1.60**
- 9 topics; **conflated Smart RAG + LTG into one mega-topic** `latent_topic_graph [117,189]`, truncates LTG tail (190-203 unscored).
- d5 = 2: name doesn't reflect the merged content (should be smart_rag + latent_topic_graph as separate topics).
- d6 = 1: universal "This topic discusses/details/explains/describes/outlines" prefix on every description — insight #3 reproduces.
- d7 = 2: most boundaries clean, but the latent_topic_graph 117-189 swallows two distinct sections.
- d8 = 1.5: one merge + 14-line tail unscored. **Different failure mode from qwen3:8b** — conflation, not omission.

**File-specific note.** KNOWLEDGE.md plays to qwen3:14b's strengths because it's well-structured semi-prose with clear concept-per-section format that maps directly onto a topic-extraction objective. This is empirically *the* easiest file in the corpus for qwen3:14b — the model performs best on documents that already "think in topics."

---

### `docs/research/smart-rag-index.md` (file 7 of 8) — file role: `cross_reference_index`

**Snapshot.** 64 lines, densest cross-reference doc in the corpus. Structure:

- Lines 9-19: "five philosophies" table with 7 source rows (claims 5, lists 7).
- Lines 21-29: "Cross-cutting patterns" — **7 numbered bullets, each one line, each with inline parenthetical annotations** like `1. **Hybrid = BM25 + vectors + graph** (llm-wiki v2, repowise, claude-mem) — confirms the direction…`
- Lines 31-37: refined architecture code block.
- Lines 39-43: three amendments.
- Lines 45-46: open decision point.
- Lines 48-62: existing infrastructure table.

**Pattern bullet ground truth (for reconciliation reference):**

| Line | Pattern |
|---|---|
| 22 | Hybrid (BM25 + vectors + graph) |
| 23 | Pre-compile once, query many |
| 24 | Exploit existing graph structure |
| 25 | Hierarchical scoping beats flat search |
| 26 | Filter-before-fetch via IDs/summaries |
| 27 | Supersession / contradiction tracking |
| 28 | Behavioral edges (git co-change) |

**`qwen3:8b` — d5=2.5, d6=2.5, d7=2.5, d8=3 → 2.55** (winner — first reversal in spike)
- 10 topics. **All 7 pattern bullets correctly mapped to their exact line.**
- d5 = 2.5: 9 of 10 topics excellent; one rule-3 violation on `content_linking [8-19, 20-62]` (essentially "the whole file body").
- d6 = 2.5: clean concrete descriptions, no boilerplate.
- d7 = 2.5: precise single-line spans for the patterns; content_linking spans absurdly broad.
- d8 = 3: coverage 0.859, all sections + cross-cutting topics covered.
- **First and only file where qwen3:8b outscores qwen3:14b.**

**`qwen3:14b` — d5=2.5, d6=3, d7=1.5, d8=2 → 2.43**
- 8 topics including `domain_specific_wikis` (line 46 — clever catch) and `existing_infrastructure` (48-62).
- d5 = 2.5: excellent topic identification but skips `filter_before_fetch` and `behavioral_edges`/`git_co_change` as their own topics.
- d6 = 3: clean active-verb descriptions, no boilerplate.
- d7 = 1.5: **off-by-one errors on patterns list** — `graph_exploitation [23]` should be [24]; `hierarchical_scoping [24]` should be [25]; `supersession_tracking [26]` should be [27]. 3 of 8 topics have boundary errors.
- d8 = 2: coverage 0.5; missed `filter_before_fetch` entirely.
- **First file in spike where qwen3:14b dipped below 2.5.** The bullets contain mid-line punctuation density (parens, em-dashes, bold) — qwen3:14b appears to lose count.

**`qwen2.5-coder:14b` — d5=1.5, d6=2, d7=2, d8=2 → 1.83**
- 9 topics; pattern bullets mapped 7/7 correctly. **But:**
- Structural meta-topic `cross_cutting_patterns [21,29]` is essentially "the patterns section" — rule 3 violation.
- Used **line 35 as a kitchen-sink reference** for 4 unrelated topics: `hybrid_indexing [22,23]+[34,35]`, `hierarchical_scoping [25,35]`, `filter_before_fetch [26,35]`, `supersession_tracking [27,35]`. Line 35 is the architecture line "→ retriever service (MCP tool + HTTP endpoint)" — has nothing to do with most of those topics.

**`gemma3:12b` — d5=2, d6=1, d7=1, d8=1 → 1.35**
- 7 topics; off-by-one + semantic mismatches.
- `graph_exploitation [25]` is actually hierarchical_scoping line; `hierarchical_scoping [15-16]` is actually repowise philosophy row (not hierarchical content).
- Coverage 0.344 — **well below the 60% rule-2 floor.**
- All 7 descriptions start with "This topic" prefix.
- Worst single-file score for gemma3 in the spike.

**File-specific note.** Off-by-one on the patterns list (lines 22-28) is a model-by-model variable failure — coder and qwen3:8b nail it; qwen3:14b and gemma3 miss. Compare to insight #1 (coder hit off-by-one on `smart-rag-repowise.md` Summary list). **No model is universally tight on dense bullets** — the failure is format-driven, not a model property.

---

### `docs/ideas/smart-rag3.md` (file 8 of 8) — file role: `architectural_design_doc`

**Snapshot.** 84 lines, longest and most prose-heavy reasoning narrative in the corpus. Structure:

- Lines 1-4: opening insight box.
- Line 6: intro.
- Line 8: `## The five philosophies these sources represent` (then 7 numbered subsections to ~line 30).
- Line 32: `## Patterns that cut across multiple sources` (table at 33-42).
- Line 44: `## How this refines the earlier architecture` (Amendments 1-3, ~45-65).
- Line 67: `## What I'd drop from consideration`.
- Line 73: `## The remaining decision point`.
- Line 83: separator + final question.

**Paired with `smart-rag-index.md`:** same conceptual content (the smart-RAG research synthesis), opposite format. This is the source of insight #8.

**`qwen3:14b` — d5=3, d6=3, d7=2.5, d8=2.5 → 2.85** (winner; **tied with KNOWLEDGE.md for joint-best single-file**)
- 9 well-named semantic topics including `architectural_amendments` and `domain_specific_wikis`.
- d5 = 3: comprehensive coverage of cross-cutting concepts AND specific architectural elements; no rule 3 violations.
- d6 = 3: clean active-verb descriptions, specific.
- d7 = 2.5: spans mostly precise; `supersession_tracking [11,12]+[40,41]` correctly ties Karpathy v2's mention to the patterns table row.
- d8 = 2.5: coverage 0.476 per auto, but topics well-distributed; missing the "drops" section (67-71).
- **Sharp rebound from the 2.43 dip on the sibling index file** — long-prose hypothesis confirmed.

**`qwen3:8b` — d5=2.5, d6=2.5, d7=1.5, d8=2.5 → 2.30**
- 8 topics; broader sloppier spans than on `smart-rag-index.md`.
- `pre_compiled_wiki [10,22]` is a **kitchen-sink span swallowing 4 philosophy subsections**.
- Three different topics claim `[76,81]` (decision point lines): `pre_compiled_wiki`, `hybrid_search_strategies`, `hierarchical_scoping` — only `domain_specific_wikis` really belongs.
- `filter_before_fetch [63,65]` misassigned (those lines are amendment-3 git co-change content, not filter content).
- **Drops back below qwen3:14b** — the `smart-rag-index.md` reversal does not generalize to long prose.

**`qwen2.5-coder:14b` — d5=1.5, d6=1.5, d7=1.5, d8=2 → 1.55** (**worst single-file score in the entire spike**)
- 8 topics; **three structural-section topics** (rule 3 violations):
  - `retrieval_architecture [1,4]+[6,12]+[32,42]` (~half the file)
  - `architectural_amendments [44,65]` (the entire amendments section)
  - `decision_points [73,81]` (the decision section)
- Multiple overlapping claims on `[10,12]`.
- Misses `filter_before_fetch` and `hierarchical_scoping` entirely.

**`gemma3:12b` — d5=2, d6=1, d7=1, d8=1.5 → 1.40**
- Only **6 topics for an 84-line architectural doc** — under-extracted.
- `pre_compile_wiki` has self-overlapping spans `[47,57]+[51,55]` (one is subset of the other — wasteful single-topic redundancy).
- `[63,64]` assigned to BOTH `code_signal_analysis` (correct, git co-change) AND `supersession_tracking` (wrong — supersession is in lines 60-62, not 63-64) — **crossed overlap pattern from insight #5 reproduces**.
- Universal "This topic" prefix.

**File-specific note.** This is the file that revealed insight #8 — the paired-file natural experiment with `smart-rag-index.md`. Same content, opposite format → 0.55-point swing for qwen3:8b and 0.42-point swing for qwen3:14b in opposite directions. Cleanest controlled experiment in the spike.

<!-- /ref:ltg-phase1-claude-rater-notes -->

---

<!-- ref:ltg-phase1-meta-insights -->
# LTG Phase 1 — Meta-Insights (Pre-Reconciliation)

**Purpose.** Cross-cutting observations about the spike methodology and patterns across files that are not yet abstracted into a numbered finding in `ref:ltg-phase1-insights`. Companion to `ref:ltg-phase1-claude-rater-notes`.

**Held outside `.memories/KNOWLEDGE.md` until two-rater reconciliation completes** — premature codification would bias user-track scoring.

## File-class taxonomy emerging from the corpus

The 8-file corpus revealed at least four distinct file roles with different best models:

| File role | Best model | Evidence (n) |
|---|---|---|
| Long prose narrative / design doc | `qwen3:14b` | smart-rag3.md (2.85), smart-rag-repowise.md (2.68) |
| Concept-per-section knowledge doc | `qwen3:14b` | KNOWLEDGE.md (2.85), persona-template.md (2.65) |
| Dense numbered cross-reference index | `qwen3:8b` | smart-rag-index.md (2.55) — **n=1, fragile** |
| Code (Python) | `coder` or `qwen3:14b` | build-persona.py (coder 2.48, 14b 2.68) — coder cheaper if accuracy enough |

**Caveat:** with 8 files spread across 4+ roles, every non-prose claim is n=1 or n=2. The taxonomy is suggestive, not proven. Determinism re-runs and a Phase 2 corpus expansion would tighten it.

## Methodology: paired-file design is the most diagnostic comparison

The `smart-rag-index.md` ↔ `smart-rag3.md` pair is a near-controlled experiment: same author, same concepts, opposite format. A 0.55-point swing for qwen3:8b and a 0.42-point swing for qwen3:14b in opposite directions on the same content is the cleanest evidence in the spike that **format-sensitivity dominates content-sensitivity for these models**.

**Recommendation for next-phase corpus design.** Sample by `(content_domain × format)` matrix, not by content alone. Even 2 content domains × 4 formats = 8 cells gives one per cell — enough to detect format-dependent vs content-dependent models. The current corpus has multiple cells unfilled (no second cross-reference index, no second code file, no second template).

## Per-model trend observations across the 8 files

- **`qwen3:14b`** — strongest results on documents that "already think in topics" (well-structured semi-prose with one concept per section: KNOWLEDGE.md 2.85, persona-template.md 2.65). Weakest on dense numbered bullets with inline punctuation density (smart-rag-index.md 2.43 — off-by-one on patterns list). Range: 2.43–2.85 across 8 files. Most consistent of the four models.

- **`qwen3:8b`** — consistent at ~2.20–2.55 on most files but exhibits two reproducible failure modes:
  1. **Whole-section drops** on files with ≥9 sections (persona-template.md → Registration; KNOWLEDGE.md → Smart RAG). Internal topic-budget appears capped around 7–9.
  2. **Topic-bleed and over-broad spans** on long architectural prose (smart-rag3.md: kitchen-sink `[10,22]`, three topics claiming `[76,81]`).

- **`qwen2.5-coder:14b`** — degrades on long prose (1.55 on smart-rag3.md, **worst single-file score in the spike**) due to structural-meta topic emission (three rule-3 violations on that one file). Strongest on code-structured files (build-persona.py 2.48). The "code-only candidate" framing in the verdict is empirically backed.

- **`gemma3:12b`** — bleeding. Average dropped from 1.71 (5 files) to 1.61 (8 files). Multiple compounding failures:
  - Boilerplate descriptions (insight #3, every file)
  - Under-extraction on long files (only 6 topics for 84-line smart-rag3.md)
  - Off-by-one on dense bullets (smart-rag-index.md 1.35, coverage 0.344)
  - Self-overlapping spans (smart-rag3.md `pre_compile_wiki [47,57]+[51,55]`)
  - Crossed overlaps (smart-rag3.md `[63,64]` assigned to two unrelated topics)
  - Section conflation (KNOWLEDGE.md merged Smart RAG + LTG)
  
  **Not a single fixable issue** — comprehensively weak on this rubric.

## Reconciliation priorities for the two-rater diff

Highest-leverage diffs to look at first when the user-track scoring closes:

1. **`smart-rag-index.md` ⟷ `smart-rag3.md` ranking flip** (insight #8). If user track agrees on the flip, the 3-arm routing hypothesis (`ref:ltg-phase1-routing-hypothesis`) is empirically confirmed. If user track ranks one model the same on both files, format-sensitivity is weaker than the Claude track suggests and qwen3:14b stays as universal default.

2. **Dim 8 calibration on `KNOWLEDGE.md` and `persona-template.md`** (the two files where qwen3:8b dropped a section). Does the user penalize qwen3:8b's whole-section drops more than 1 point? If yes, the rubric weighting question (dim 8 only 10% — see insight #6) should be revisited before the freeze.

3. **Dim 5 calibration on `smart-rag-index.md`**. Claude scored qwen3:8b's `content_linking [8-19, 20-62]` as a rule-3 violation (d5 = 2.5 instead of 3). Coder's `cross_cutting_patterns [21-29]` got a similar treatment (d5 = 1.5). If the user is more lenient on structural-meta topics, the gap between coder and qwen3:8b narrows; if stricter, it widens.

## Mechanical post-pass guards worth adding

Two cheap guards that would catch failure modes the rubric currently leaves to manual scoring:

1. **Coverage cap.** Reject any topic whose span set covers >60% of the file. Catches structural-meta / kitchen-sink topics like coder's `cross_cutting_patterns [21,29]` and qwen3:8b's `content_linking [8-19, 20-62]`.

2. **Containment overlap check.** For every pair of topics with span intersection, assert `intersection == smaller_span`. Permits hierarchical containment (insight #5 — desirable for LTG multi-scale design), rejects crossed overlap (boundary failure).

These complement the duplicate-span-set detector (insight #2) which only catches byte-identical lists.

## Rubric calibration concern (restated for emphasis from finding #6)

Under the current weighting (`0.10·dim8`), a whole-section drop docks the score by ~0.10–0.15 — small enough that qwen3:8b cleared the 2.2 threshold on KNOWLEDGE.md (2.25) despite missing ~22% of the file content. **This is the single most likely source of two-rater divergence** because it's a structural rubric question, not a per-cell calibration question.

Two possible adjustments (defer until after reconciliation):

- Re-weight: e.g. `0.30·d5 + 0.30·d6 + 0.20·d7 + 0.20·d8`.
- Hard penalty when `dim8 ≤ 1` (e.g. floor weighted_quality at 0.5× or apply additive penalty).

## Open questions for after Phase 1 close

- **Determinism on `smart-rag-index.md`.** Does qwen3:14b's off-by-one on the patterns list reproduce under repeated runs (same prompt, same seed)? If yes, it's a model-format property; if no, it's sample-unlucky and the cross-reference-index third arm collapses.

- **Prompt iteration.** Would the deferred experiment (topic-count floor `max(5, major_section_count)` + containment-only overlap rule, both from session 55) lift qwen3:8b across the whole-section-drop failure mode? Cheap re-sweep on existing 8 files.

- **MoE candidates.** Do `qwen3:30b-a3b` and `qwen3-coder:30b` deliver quality gains beyond the dense models worth their hybrid VRAM+RAM cost? Fold into Phase 2 VRAM co-residence probe (per `ref:ltg-phase1-routing-hypothesis`).

- **File-class generalisation.** Does the cross-reference-index → qwen3:8b routing claim hold for other files of that type? Need at least one more cross-reference index file to test (n=1 currently).

<!-- /ref:ltg-phase1-meta-insights -->

---

<!-- ref:ltg-phase1-pending-revisions -->
# LTG Phase 1 — Pending Revisions (Post-Reconciliation)

**Purpose.** Drafts and stale-content cleanup queued to apply *after* two-rater reconciliation completes. Captured in this session so a future session can execute them mechanically without re-deriving the analysis.

## Stale wording in pre-existing files (cleanup queue)

These were true at session 54 and are now stale. None affects correctness today; all should be fixed before opening the PR.

| File | Location | Stale text | Replace with |
|---|---|---|---|
| `retrieval/spike-results.md` | `ref:ltg-phase1-routing-hypothesis` block, "Decision gate" paragraph | "do not commit to routing until (1) **remaining 4 corpus files are scored**, (2) MoE candidates evaluated…, (3) determinism re-runs executed on the winner(s)" | "do not commit to routing until (1) **two-rater reconciliation closes**, (2) MoE candidates evaluated, (3) determinism re-runs executed on the winner(s)" |
| `retrieval/spike-results.md` | `ref:ltg-phase1-routing-hypothesis` block, the 2-arm bullet list | Lists only `Code files → qwen2.5-coder:14b` and `Prose files → qwen3:14b` | Add third arm `Cross-reference index files → qwen3:8b` (n=1, gated on user-track agreement on insight #8); see "Routing-hypothesis revision" below |
| `.memories/KNOWLEDGE.md` | "LTG Phase 1 Extractor Spike — Findings" section | "**Preliminary results (5/8 files scored):**" + 5-file table | "**Final results (8/8 files scored, Claude draft + reconciled with user track):**" + 8-file table; only update *after* reconciliation lands |

## Routing-hypothesis revision (conditional draft)

The current `ref:ltg-phase1-routing-hypothesis` block in `spike-results.md` describes a 2-arm split. Two replacement drafts depending on the user-track outcome:

### Branch A — user track agrees on insight #8 ranking flip (3-arm story holds)

Replace the 2-arm bullet list with:

> Phase 1 evidence supports a 3-arm specialized-model routing for the extractor:
> - **Code files → `qwen2.5-coder:14b`** (2.48 on `build-persona.py` with tight function-aligned spans). n=1; revisit when more code files added.
> - **Prose files (long narrative + concept-per-section) → `qwen3:14b`** (consistent 2.65–2.85 across 5 prose files including `KNOWLEDGE.md`, `smart-rag3.md`, `persona-template.md`, `smart-rag-repowise.md`, `plan-v2.md`).
> - **Dense numbered cross-reference index files → `qwen3:8b`** (2.55 on `smart-rag-index.md` vs qwen3:14b 2.43; off-by-one failure mode for qwen3:14b on inline-annotated bullets, see insight #7). n=1; **gated on determinism re-run** to confirm the off-by-one is a model-format property, not sample-unlucky.
> - **MoE probe (deferred):** unchanged — fold into Phase 2 VRAM co-residence work.
>
> **Single-model fallback** if routing infrastructure isn't worth the cost yet: `qwen3:14b` (loses ~0.1–0.15 quality on cross-reference index files, gains operational simplicity).

### Branch B — user track disagrees on the flip (3-arm collapses)

Replace the 2-arm bullet list with:

> Phase 1 evidence supports a 2-arm specialized-model routing for the extractor:
> - **Code files → `qwen2.5-coder:14b`** (unchanged from prior).
> - **All prose files → `qwen3:14b`** (universal default; the cross-reference-index reversal in the Claude draft track did not survive user-track scoring, suggesting it was rater-bias or rubric-edge-case rather than a model property).
> - **MoE probe (deferred):** unchanged.
>
> Insight #7 (off-by-one on dense bullets) and insight #8 (paired-file format-sensitivity) remain valid observations but do not warrant a third routing arm without reproducible cross-rater evidence.

### Branch C — user track partially agrees (mixed signal)

Keep the 2-arm split as the production routing decision (operational simplicity wins on weak evidence) but preserve the cross-reference-index hypothesis in the deferred-tasks list (`ref:deferred-infra`) for re-evaluation when (a) more cross-reference files are added to the corpus or (b) MoE candidates are eval'd. This is the most likely outcome — the spike's n=1 on this file role is genuinely thin.

## Decision tree for the future session executing this

When user-track scoring lands:

1. Compute per-cell agreement on the 4 cells `(qwen3:14b, qwen3:8b) × (smart-rag-index, smart-rag3)`. These four cells are decisive.
2. **If user track agrees** that qwen3:8b > qwen3:14b on smart-rag-index AND qwen3:14b > qwen3:8b on smart-rag3 → **Branch A** (apply 3-arm draft above).
3. **If user track disagrees on both** (no flip on either file, or flip in opposite direction) → **Branch B** (apply 2-arm draft above).
4. **Mixed** (agrees on one but not the other) → **Branch C** (no replacement; defer to next phase).
5. Apply the stale-wording cleanup table regardless of branch.
6. Then update `.memories/KNOWLEDGE.md` "LTG Phase 1 Extractor Spike — Findings" section per the cleanup table — *only after* steps 2-4 resolve.

## What's NOT pre-decided

- The `ref:ltg-extractor` decision in `retrieval/DECISIONS.md` — that's the formal extractor freeze. None of the branches above pre-commit it; they only update the *hypothesis* block. The freeze itself remains gated on determinism re-runs and MoE eval per the existing Decision Gate (4 items).
- The dim-8 rubric weighting question (insight #6) — left open. If user track penalizes whole-section drops harder than Claude did, the freeze might need to wait on a re-weighted re-score before committing to qwen3:8b as the cross-reference-index arm or as the latency backup.

<!-- /ref:ltg-phase1-pending-revisions -->
