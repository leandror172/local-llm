<!-- ref:ltg-phase1-results -->
# LTG Phase 1 — Extractor Spike Results

**Context:** Topic extractor A/B decision is at `ref:ltg-extractor`. Rubric and exit criteria frozen session 52 (2026-04-14). Sweep executed session 54 (2026-04-16).

**Status:** Claude draft track **complete** — 8 of 8 corpus files scored. User's independent scoring via HTML viz in progress. Two-rater agreement now gates final freeze. Four models × all 8 files run mechanically (32/32 ok).

## Sweep configuration (as executed)

| Axis | Value |
|---|---|
| Models | `gemma3:12b`, `qwen3:14b`, `qwen2.5-coder:14b`, `qwen3:8b` (`think: false`) |
| Files | 8 corpus files (7 prose + 1 code) |
| Runs per combo | 1 (determinism re-runs deferred) |
| Options | `num_ctx=8192`, `temperature=0.1`, `format=json_schema` |
| Raw JSONL | `retrieval/runs/20260416-181839.jsonl` |
| Viewer | `retrieval/runs/20260416-181839.html` (self-contained) |
| Scorer | `retrieval/viz_sweep.py` → generates viewer with inline rubric + localStorage persistence |

## Mechanical dimensions (all 32 runs, auto-computed)

| Model | avg topics | avg coverage | avg non-contiguity | avg tok/s |
|---|---|---|---|---|
| gemma3:12b        | 6.6 |  60% | 71% | 16.7 |
| qwen3:14b         | 8.8 |  64% | 68% |  9.4 |
| qwen2.5-coder:14b | 8.5 |  75% | 27% |  6.5 |
| qwen3:8b          | 7.5 |  60% | 76% | 38.4 |

- `qwen2.5-coder:14b` has the highest span coverage but the lowest non-contiguity rate — it treats sections as topics, losing cross-cutting concepts.
- `qwen3:8b` has the opposite pattern: highest non-contiguity, moderate coverage — hunts for fragmented mentions but misses chunks.
- `qwen3:14b` balances both.

## Manual scoring (weighted_quality = 0.35·d5 + 0.35·d6 + 0.20·d7 + 0.10·d8)

**Raters:** Two parallel scoring tracks — **Claude** (table below, session 54 draft) and **User** (HTML viz, in progress). Final verdict requires agreement; divergence on specific dims is signal that those rubric definitions need tightening before extractor freeze.

### Claude's per-file scores (before speed penalty)

| File | gemma3:12b | qwen3:14b | qwen2.5-coder:14b | qwen3:8b |
|---|---|---|---|---|
| `.memories/QUICK.md` | 1.68 | **2.68 ✅** | 2.00 | 2.08 |
| `docs/research/smart-rag-repowise.md` | 1.83 | **2.68 ✅** | 1.80 | **2.35 ✅** |
| `.claude/plan-v2.md` | 1.68 | **2.68 ✅** | 2.10 | 1.93 |
| `personas/build-persona.py` | 2.00 | **2.68 ✅** | **2.48 ✅** | **2.45 ✅** |
| `personas/persona-template.md` | 1.35 | **2.65 ✅** | 2.00 | **2.25 ✅** |
| `.memories/KNOWLEDGE.md` | 1.60 | **2.85 ✅** | **2.30 ✅** | **2.25 ✅** |
| `docs/research/smart-rag-index.md` | 1.35 | **2.43 ✅** | 1.83 | **2.55 ✅** |
| `docs/ideas/smart-rag3.md` | 1.40 | **2.85 ✅** | 1.55 | **2.30 ✅** |
| **average (8 files)** | **1.61** | **2.69** | **2.01** | **2.27** |

Exit threshold is `≥ 2.2`. ✅ = passes threshold.

### User's per-file scores (HTML-viz track, complete — session 58)

Source: `retrieval/runs/manual-rubric.md` + `retrieval/runs/ltg-rater-20260416-181839-20260430-215756Z.json` (32/32 cells scored, with 648 per-topic scores `{n, d, b}` in 29/32 cells; per-topic JSON usage deferred to Phase 2 — see `ref:deferred-infra`).

| File | gemma3:12b | qwen3:14b | qwen2.5-coder:14b | qwen3:8b |
|---|---|---|---|---|
| `.memories/QUICK.md` | 0.75 | **2.80 ✅** | 1.75 | **2.70 ✅** |
| `docs/research/smart-rag-repowise.md` | **2.20 ✅** | **2.70 ✅** | **2.25 ✅** | **2.50 ✅** |
| `.claude/plan-v2.md` | 1.35 | **2.70 ✅** | **2.35 ✅** | 1.90 |
| `personas/build-persona.py` | 1.65 | **2.90 ✅** | **2.90 ✅** | **2.60 ✅** |
| `personas/persona-template.md` | **2.20 ✅** | **3.00 ✅** | **2.55 ✅** | **2.90 ✅** |
| `.memories/KNOWLEDGE.md` | **2.20 ✅** | **3.00 ✅** | **2.65 ✅** | **2.90 ✅** |
| `docs/research/smart-rag-index.md` | 2.00 | **2.80 ✅** | **2.45 ✅** | **2.65 ✅** |
| `docs/ideas/smart-rag3.md` | **2.20 ✅** | **3.00 ✅** | **2.35 ✅** | **2.90 ✅** |
| **average (8 files)** | **1.82** | **2.86** | **2.41** | **2.63** |

### Two-rater reconciliation (session 58, 2026-04-30) — Branch C

**Outcome.** Both rater tracks produce **identical 4-model ranking** and identical pass/fail verdicts after speed penalty (`qwen3:14b ✅ > qwen3:8b ✅ > qwen2.5-coder:14b ❌ > gemma3:12b ❌`). User track is systematically more lenient (per-model Δ_avg: gemma +0.21, qwen3:14b +0.18, coder +0.40, qwen3:8b +0.36) but the relative ordering and gating decisions hold under both raters.

**Decisive cells** (the four that gate Branch A/B/C from `ref:ltg-phase1-pending-revisions`):

| Cell | Claude | User | Cross-rater agreement |
|---|---|---|---|
| `smart-rag-index.md` × qwen3:14b | 2.43 | 2.80 | — |
| `smart-rag-index.md` × qwen3:8b  | **2.55** | 2.65 | ✗ Claude says qwen3:8b wins by +0.12; User says qwen3:14b wins by +0.15 — flip does NOT survive |
| `smart-rag3.md` × qwen3:14b | **2.85** | **3.00** | ✓ both agree |
| `smart-rag3.md` × qwen3:8b  | 2.30 | 2.90 | ✓ both agree (qwen3:14b wins) |

**Resolution: Branch C (mixed).** Both raters agree on `smart-rag3` (qwen3:14b wins) but disagree on `smart-rag-index` (the qwen3:8b lead does not survive). Per the pre-registered decision tree: **keep 2-arm routing as the production decision; preserve the cross-reference-index 3rd-arm hypothesis as a deferred item** for re-evaluation when (a) determinism re-runs supply more evidence, (b) more cross-reference files are added to the corpus, or (c) MoE candidates are evaluated. The spike's n=1 on this file role is genuinely thin. See `ref:ltg-phase1-routing-hypothesis` for the revised production routing.

**Largest single-cell disagreement: `.memories/QUICK.md` × `gemma3:12b` (Δ=−0.93).** Claude scored 1.68; user scored 0.75 with d5=0 and the explicit note _"Tends to infer wrong ideas (memory_architecture name/description from aggregated pieces that seem very tangent to that idea), strange decisions on spans (12-14 + 16-23, missing `llm/` root folder of structure)"_. This is the **only** cell of 32 where the user track is harsher than Claude, and it concerns a model already verdict-failing — so it sharpens gemma's `❌` rather than weakening it. The concrete failure mode it reveals is *semantic hallucination on dense memory files*: gemma3:12b inferred a topic identity from peripheral content rather than from the topic's own span, a behaviour the per-file weighted scalar in Claude's draft underweighted.

**Coder borderline note.** Under the user track, `qwen2.5-coder:14b` finishes at 2.16 adjusted (raw 2.41, −0.25 speed penalty) — only 0.04 below the 2.2 threshold, vs Claude draft's 1.76 adjusted (0.44 below). Verdict still resolves to `❌`, but the margin is small enough that adding 2-3 more code files to the corpus could plausibly flip it. Tracked as the "specialized-extractor routing study" deferred item.

**Dim-8 reweight question (insight #6).** User-track weighted scores ran systematically higher on whole-section-drop files (`KNOWLEDGE.md` × qwen3:8b: +0.65; `persona-template.md` × qwen3:8b: +0.65) — but the per-dim breakdown of the Claude draft is not available, so a d8-specific calibration claim cannot be made from per-file scalars alone. What can be said: **dim-8 reweighting is not load-bearing for the ranking** (the binary freeze decision survives both rater tracks unchanged). Left as a Phase 2 deferred refinement — could matter if the rubric is later repurposed as a continuous quality metric (e.g., for DPO scoring at Layer 7); for the binary freeze it is fit-for-purpose.

### After speed penalty (−0.25 if < 15 tok/s) — final 8-file averages

| Model | raw avg | TPS | adjusted | verdict |
|---|---|---|---|---|
| qwen3:14b         | 2.69 |  9.4 | **2.44** | ✅ passes — winner overall (lead 0.17 over qwen3:8b) |
| qwen3:8b          | 2.27 | 38.4 | **2.27** | ✅ passes; 4× faster; **best on cross-reference index format in Claude draft** (user track inverted this — see Two-rater reconciliation above) |
| qwen2.5-coder:14b | 2.01 |  6.5 | **1.76** | ❌ fails overall — code-only candidate |
| gemma3:12b        | 1.61 | 16.7 | **1.61** | ❌ fails — boilerplate + off-by-one on dense bullets + under-extraction on long prose |

**Claude draft track complete (8/8).** Final reconciliation now waits on user's HTML-viz scoring track. Per-file divergences will flag rubric calibration issues; aggregate disagreement >0.3 on any model would be a freeze blocker.

## Final verdict (Claude draft track) — pending two-rater reconciliation + determinism

**Primary candidate:** `qwen3:14b`. Raw range 2.43–2.85 across all 8 file roles (short memory, long prose, dense structured plan, Python code, semi-structured template, repo-wide knowledge doc, cross-reference index, architectural design doc). The single dip below 2.5 was on the cross-reference index format (`smart-rag-index.md`, see insight #7); rebounded sharply to 2.85 on the long-prose sibling document covering the same concepts (insight #8). 9.4 tok/s is slow but acceptable for offline indexing — LTG indexes once, queries many.

**Backup:** `qwen3:8b` if latency matters, **and primary candidate for cross-reference index files specifically**. Clears threshold at 2.27; 4× faster. Risks: (a) duplicate-span-set failure on dense structured files (plan-v2 produced two topics with byte-identical 17-span lists, finding #2); (b) **whole-section drops confirmed in 2 of 8 scored files** (Registration in persona-template.md, Smart RAG in KNOWLEDGE.md — finding #6); (c) topic-bleed and over-broad spans on long architectural prose (smart-rag3.md, multiple topics claiming the same `[76,81]` lines).

**Not recommended as general-purpose extractor:** `gemma3:12b` (boilerplate descriptions + off-by-one on dense bullets + under-extraction on long prose — only 6 topics for an 84-line architectural doc), `qwen2.5-coder:14b` (off-by-one span numbering on dense prose; emits structural meta-topics on long architectural docs — three rule-3 violations on `smart-rag3.md`; worst single-file score 1.55).

**Do not freeze yet.** Gate the final `ref:ltg-extractor` decision-replacement on:
1. ~~**Two-rater reconciliation**~~ — **complete (session 58, Branch C)**: identical ranking and verdicts under both raters; user-track leniency does not flip pass/fail on any model; cross-ref-index 3rd-arm deferred (see Two-rater reconciliation above and `ref:ltg-phase1-routing-hypothesis`).
2. **Determinism re-runs on winner** (dim 9 Jaccard) — does qwen3:14b's `smart-rag-index.md` off-by-one reproduce, or was it sample-unlucky? Now the cheapest gating evidence remaining (~30s of compute); if reproducible, supplies the missing Phase 1 evidence for the deferred 3rd arm.
3. **MoE probe** per `ref:ltg-phase1-routing-hypothesis` — fold into Phase 2 VRAM co-residence probe.
4. ~~**Routing-hypothesis update**~~ — **complete (session 58)**: 2-arm production routing; cross-ref-index 3rd arm deferred to Phase 2 pending more file-class samples or MoE eval (Branch C, see `ref:ltg-phase1-routing-hypothesis`).

<!-- /ref:ltg-phase1-results -->

---

<!-- ref:ltg-phase1-insights -->
## Notable model-behavior findings

### 1. `qwen2.5-coder:14b` has a striking prose-vs-code split

On `docs/research/smart-rag-repowise.md` (54-line research doc), the model produced topics with **off-by-one span numbering** in the dense Summary list:

| Topic name (model output) | Span claimed | Actual content at that span |
|---|---|---|
| `graph_intelligence` | 12–13 | line 12 = graph ✓, line 13 = git (off by one) |
| `git_intelligence` | 14–14 | documentation (off by one) |
| `documentation` | 15–15 | decisions (off by one) |
| `decision_intelligence` | 16–16 | blank line |
| `local_storage` | 17–17 | storage ✓ (aligns again) |

On `personas/build-persona.py` (478-line Python file), the same model produced the tightest function-aligned boundaries of all four models — **2.48 weighted quality, passing threshold**. Its section-tight span style (which hurt on prose) matches Python's function-block structure perfectly.

**Hypothesis:** code-specialized models excel on code-file structure (function boundaries) but drift on prose enumeration. Motivates `ref:ltg-phase1-routing-hypothesis`.

### 2. `qwen3:8b` produces duplicate span sets on dense structured files

On `.claude/plan-v2.md` (442-line dense multi-layer plan), `qwen3:8b` output two topics with **byte-identical 17-span lists**:

- `model_deployment` → `[11-17, 20-34, 40-44, 47-51, 70-74, 92-96, 119-123, 130-134, 164-168, 193-197, 225-229, 243-247, 272-276, 332-336, 361-365, 389-393, 418-422]`
- `evaluation_and_refinement` → **same list, byte-for-byte**

The viz auto-flags this as `⚠ duplicate span set`. Dim 8 collapses. Likely cause: when topic count was ambiguous, the model listed layer headers rather than extracting semantic topics, then re-used the same layer-header list for a second topic theme.

### 3. `gemma3:12b` descriptions lead with boilerplate

Every topic description begins with `"This topic covers…"` / `"This topic describes…"` / `"This topic focuses on…"`. Dim 6 consistently scores ≤ 2 because of this prefix pollution. Material concern: extracted `description` feeds `bge-m3` embeddings downstream — the model will learn that the first ~30 chars of every topic description are noise. Either a dedicated prompt iteration or a different model is needed.

### 4. Whole-section misses under topic-budget pressure (persona-template.md)

On `personas/persona-template.md` (188-line semi-structured reference with 9 natural sections), two models dropped a full section:

| Model | Topics | Section dropped |
|---|---|---|
| `qwen3:8b` | 7 | **Registration (lines 154-163)** — not in any topic |
| `gemma3:12b` | 8 | **Naming Convention (lines 140-150)** — not in any topic |

Both models produced fewer topics than the file's natural section count. `qwen3:8b` compensated with cross-section spans on system_prompt (bleeding into Temperature Guide 101-104), further confusing boundaries. `qwen3:14b` was the only model to produce 9 topics matching the 9 natural sections, with zero overlap and contiguous spans (dim 4 non-contiguity = 0.0 on this file).

**Hypothesis:** When a model's internal topic budget is below the file's section count, it silently omits a section rather than merging. This is a dim 8 failure that the rubric's mutual-coverage check catches — a useful signal for the file-type routing question in `ref:ltg-phase1-routing-hypothesis`.

### 5. Partial cross-overlap vs hierarchical containment (persona-template.md)

On the same file, `qwen3:8b` produced `system_prompt_structure [66-78, 79-88, 89-104]` and `temperature_guidelines [101-110]` — they share lines 101-104. Neither span is a subset of the other; they are "crossed". Lines 101-104 are Temperature content, not a sub-aspect of System Prompt — this is incidental bleed, not intentional nesting.

Important distinction for LTG:

- **Hierarchical containment** (child ⊆ parent) is desirable and aligns with the multi-scale / anchor-stratification design in `ref:concept-latent-topic-graph`. A coarse parent topic and a precise child topic sharing lines serves different queries at different granularities; a no-overlap rule would suppress that.
- **Partial cross-overlap** (neither span ⊆ the other) is a real boundary failure — it signals the extractor couldn't decide where one topic ends and another begins. This is what dim 7 should catch, not mere overlap.

Useful prompt guardrail, therefore, is not "topics must not share lines" but **"if two topics share lines, one span must fully contain the other"** — permits hierarchy, rejects bleed. Mechanical check: for every pair of topics with span intersection, assert `intersection == smaller_span`. The viz's duplicate-span-set detector (finding #2) only catches byte-identical lists; a containment check would complement it.

### 6. Section-drop pattern reproduces — and the rubric under-penalises it

`.memories/KNOWLEDGE.md` (214-line, 10-section repo knowledge doc at sweep time) confirmed two failure modes from finding #4 in a different setting:

| Model | Topics | Failure mode | Section affected |
|---|---|---|---|
| `qwen3:8b`  | 9 | **whole-section drop** | Smart RAG (lines 117-151) — gap between `claude_code_integration` [90,115] and `latent_topic_graph` [162,203] |
| `gemma3:12b` | 9 | **adjacent-section conflation** | Smart RAG + LTG fused into one mega-topic `latent_topic_graph` [117,189], plus LTG tail (190-203) truncated |
| `qwen3:14b` | 10 | none | 1:1 topic-to-section, weighted_quality 2.85 (highest single-file score in the spike) |
| `qwen2.5-coder:14b` | 10 | **boundary bleed** | smart_rag span ends at 162 (eats LTG heading), LTG span ends at 195 (truncates tail by ~8 lines) — same off-by-one pattern as `smart-rag-repowise.md` |

**Whole-section drops are now a confirmed `qwen3:8b` pattern, not a hypothesis.** Two of six scored files show it (persona-template.md Registration, KNOWLEDGE.md Smart RAG). Both dropped sections sit mid-file, not at the head or tail. Both files have ≥9 natural sections. The model appears to have an internal topic-budget ceiling around 7–9 and silently omits when the file exceeds it.

**Rubric calibration concern.** Under the current weighting (`0.10·dim8`), a whole-section drop docks the score by ~0.10–0.15 — small enough that `qwen3:8b` still clears the 2.2 threshold on KNOWLEDGE.md (2.25) despite missing 22% of the file's content. If the user-track scores penalise this more aggressively on dim 8, that's a calibration signal worth surfacing during reconciliation: either re-weight (e.g. 0.30·d5 + 0.30·d6 + 0.20·d7 + 0.20·d8) or add a hard penalty when `dim8 ≤ 1`. Defer the call until the two-rater comparison shows whether this matters in practice.

### 7. Cross-reference index breaks qwen3:14b's lead — and it's an off-by-one problem

`docs/research/smart-rag-index.md` (64-line cross-reference doc, the densest pattern list in the corpus — 7 numbered bullets at lines 22-28, each one line) is the first and only file where `qwen3:8b` outscores `qwen3:14b`:

| Model | weighted | Pattern-bullet mapping accuracy |
|---|---|---|
| `qwen3:8b`         | **2.55** | 7/7 bullets mapped to their exact line — clean |
| `qwen3:14b`        | 2.43 | 4/7 — `graph_exploitation→[23]` should be 24; `hierarchical→[24]` should be 25; `supersession→[26]` should be 27 |
| `qwen2.5-coder:14b` | 1.83 | 7/7 mapped correctly, **but** added structural meta-topic `cross_cutting_patterns [21,29]` (rule 3 violation) and used line 35 as a kitchen-sink reference for 4 unrelated topics |
| `gemma3:12b`       | 1.35 | 3/7 bullets, plus mismapped repowise philosophy row (line 15-16) to `hierarchical_scoping`. Coverage 0.344, well below rule-2 floor |

The pattern bullets each contain inline parenthetical annotations: `1. **Hybrid = BM25 + vectors + graph** (llm-wiki v2, repowise, claude-mem) — confirms the direction…`. `qwen3:14b` and `gemma3:12b` lose count on punctuation-dense bullets; `qwen3:8b` and `qwen2.5-coder:14b` do not.

**Compare to finding #1:** `qwen2.5-coder:14b` had off-by-one on a similarly dense numbered list in `smart-rag-repowise.md`. **Off-by-one in dense numbered bullets is a model-agnostic failure mode — *which* models hit it varies by file.** There is no single "tight on bullets" model.

**Two structural-meta topics emerged (rule 3 violations):**

- `qwen2.5-coder:14b` → `cross_cutting_patterns [21-29]` (essentially "the patterns section")
- `qwen3:8b`         → `content_linking [8-19, 20-62]` (essentially "the whole file body")

Both violate prompt rule 3 ("topics must be semantic, not structural"). A cheap mechanical post-pass would reject any topic whose span set covers >60% of the file — complements the duplicate-span-set detector (#2) which only catches byte-identical lists.

**Implication for `ref:ltg-phase1-routing-hypothesis`:** Cross-reference index joins prose and code as a **third file class with a different best model** — `qwen3:8b` on this type, not the `qwen3:14b`/`coder` split. The routing story grows a third arm. Single-model default is now genuinely lossy on at least one corpus type.

### 8. Paired-file natural experiment confirms format-sensitivity dominates content

`docs/research/smart-rag-index.md` (cross-reference index, 64 lines, dense numbered bullets + tables) and `docs/ideas/smart-rag3.md` (architectural design doc, 84 lines, long prose) cover **the same conceptual content** — the smart-RAG research synthesis. They are the index and the long-form sibling of one investigation. This pair is the closest to a controlled experiment the corpus offers: same author, same concepts, opposite format.

| File | Format | qwen3:14b | qwen3:8b | Winner |
|---|---|---|---|---|
| `smart-rag-index.md` | dense numbered bullets, tables | 2.43 | **2.55** | qwen3:8b (+0.12) |
| `smart-rag3.md`      | long prose narrative           | **2.85** | 2.30 | qwen3:14b (+0.55) |

A **0.55-point swing for qwen3:8b** and a **0.42-point swing for qwen3:14b** in opposite directions, on the same content. Format dominates content for these two models on this material.

| File | Format | coder | gemma3 |
|---|---|---|---|
| `smart-rag-index.md` | dense bullets    | 1.83 | 1.35 |
| `smart-rag3.md`      | long prose       | 1.55 | 1.40 |

Both lower-tier models also vary by format, but neither is strong enough on either format to compete. Notably, `coder` got *worse* on long prose (structural meta-topic emission — three rule-3 violations on `smart-rag3.md`).

**Methodology takeaway:** paired-file design is far more diagnostic than any single-file score because it isolates format-sensitivity from content-difficulty. Future spikes (e.g. determinism re-runs, MoE probe, prompt-iteration) should look for or construct similar pairs where possible. For the current spike, this is **the cleanest evidence that the routing hypothesis (`ref:ltg-phase1-routing-hypothesis`) is empirically grounded**, not a small-sample artifact.

**Implication for the freeze:** if user-track scoring agrees on the smart-rag-index/smart-rag3 ranking flip, route by format; if it disagrees, the third routing arm collapses and qwen3:14b becomes single-model default. This single paired comparison is the highest-leverage reconciliation point in the two-rater diff.

### 9. Two-rater reconciliation (session 58) — ranking robust, calibration is rater-dependent

After the user's HTML-viz scoring track completed (32/32 cells in `retrieval/runs/manual-rubric.md` + per-topic detail in `retrieval/runs/ltg-rater-20260416-181839-20260430-215756Z.json`), the two rater tracks produced **identical 4-model ranking and identical pass/fail verdicts** but with systematic absolute-score divergence:

| Model | Claude raw avg | User raw avg | Δ_avg | Verdict (both) |
|---|---|---|---|---|
| qwen3:14b         | 2.69 | 2.86 | +0.17 | ✅ |
| qwen3:8b          | 2.27 | 2.63 | +0.36 | ✅ |
| qwen2.5-coder:14b | 2.01 | 2.41 | +0.40 | ❌ (borderline under user, 0.04 below threshold) |
| gemma3:12b        | 1.61 | 1.82 | +0.21 | ❌ |

**The decisive flip from finding #8 did not survive.** On `smart-rag-index.md`, Claude scored qwen3:8b > qwen3:14b by +0.12 (motivating the 3-arm routing hypothesis). The user track reverses the order — qwen3:14b > qwen3:8b by +0.15. On `smart-rag3.md` both raters agree (qwen3:14b wins by +0.55 / +0.10). Per the pre-registered decision tree (`ref:ltg-phase1-pending-revisions` Branch C), this is mixed → keep 2-arm routing, defer 3rd arm to Phase 2.

**The single counter-direction divergence is structurally informative.** Of 20 cells with |Δ| ≥ 0.30, **19 are user-higher**; the lone exception, `.memories/QUICK.md` × `gemma3:12b` (Δ=−0.93, user d5=0 with note "infers wrong ideas, strange decisions on spans"), concerns a model already verdict-failing. This sharpens the `gemma3:12b ❌` rather than weakening it: gemma's failure mode on dense memory files is *semantic hallucination* (inferring topic identity from peripheral content), which the per-file scalar in Claude's draft underweighted. Two raters caught what one would not have.

**Methodological takeaway for Layer 7 / DPO scoring.** The rubric is fit-for-purpose for **binary** decisions (which model passes the gate, which model wins a head-to-head) but absolute scores are calibration-sensitive across raters by ~0.2–0.4 weighted-quality points. If the same rubric is later reused as a continuous quality metric (e.g., for DPO preference pairs at Layer 7), expect to need either inter-rater calibration or per-rater normalization before treating raw weighted_quality as a global signal.

**Spike's net contribution to extractor freeze:** identical binary verdicts across raters → the freeze on `qwen3:14b` (prose) + `qwen2.5-coder:14b` (code) is robust to rater calibration. The remaining gates are determinism re-run + MoE eval, neither of which depends on rater calibration.

<!-- /ref:ltg-phase1-insights -->

---

<!-- ref:ltg-phase1-routing-hypothesis -->
## Production routing decision — 2-arm specialized extractor (Branch C, session 58)

Two-rater reconciliation closed at session 58 with **mixed evidence on the cross-reference-index 3rd arm** (Branch C, see `ref:ltg-phase1-pending-revisions`). The user track did not reproduce Claude's `qwen3:8b > qwen3:14b` flip on `smart-rag-index.md` — qwen3:14b instead won under user scoring. With n=1 on cross-reference-index files and inconsistent cross-rater evidence, the 3rd arm is preserved as a hypothesis but not adopted as production routing.

**Production routing (Phase 1 freeze candidate, gated on determinism + MoE):**

- **Code files → `qwen2.5-coder:14b`** (2.48 Claude / 2.90 User on `personas/build-persona.py`, tight function-aligned spans). n=1; revisit when more code files added — under the user track, this model finishes 0.04 below threshold rather than 0.44, so a corpus expansion could plausibly flip the verdict.
- **Prose files → `qwen3:14b`** (universal prose winner on every one of 7 prose files in both rater tracks: Claude 2.43–2.85 raw, User 2.70–3.00 raw; ranking agreement is bit-identical on prose).
- **Single-model fallback** if routing infrastructure isn't worth the cost yet: `qwen3:14b` (loses ~0.10–0.15 quality on cross-reference-index files in the Claude draft, gains operational simplicity; the user-track loss is inverted, so the worst-case under either rater is ~0.15 — small).

**Deferred to Phase 2 (was 3rd arm in pre-reconciliation hypothesis):**

- **Cross-reference-index files (n=1) → `qwen3:8b` candidate.** Claude draft saw a 0.12 weighted-quality lead on `smart-rag-index.md`; user track reversed it. Re-evaluate when (a) the determinism re-run on `smart-rag-index.md` × qwen3:14b confirms or refutes the off-by-one failure mode (insight #7), (b) more cross-reference-index files are added to the corpus, or (c) MoE candidates are evaluated under the same rubric.
- **MoE probe:** `qwen3:30b-a3b` (hybrid VRAM+RAM, 19 GB MoE with ~3 B active params) and `qwen3-coder:30b` when hardware-headroom permits. Hypothesis: MoE sparse activation may deliver quality closer to dense 30B-class while staying within the 12 GB + hybrid-RAM budget. The Phase 2 VRAM co-residence probe is mandatory before locking embedding anyway; folding MoE extractor eval into that probe is cheap.
- **Per-topic JSON evidence (648 scores in 29/32 cells):** Could supply per-topic boundary evidence to disambiguate the deferred 3rd arm without a corpus-expansion sweep. Tracked in `ref:deferred-infra`.

**Decision gate** for the formal `ref:ltg-extractor` decision-replacement (do not commit until):
1. ~~Two-rater reconciliation~~ — **complete (session 58, Branch C)**.
2. **Determinism re-runs on winner** under the same rubric (Jaccard ≥ 0.85 → +0.5 stability bonus; ≥ 0.80 → +0.25). Cheapest remaining evidence; ~30s of compute on `smart-rag-index.md` × qwen3:14b also answers the deferred 3rd-arm question directly.
3. **MoE candidates evaluated** — fold into Phase 2 VRAM co-residence probe.

**Revisit triggers:**
- MoE sweep completed → re-evaluate whether routing still beats a single-model choice.
- `qwen3-coder:30b` pulled (gated on hardware-headroom probe — see `ref:deferred-infra`).
- Additional code files added to MVP corpus (current n=1 is too thin; coder 0.04-below-threshold under user track makes a corpus-expansion flip plausible).
- Additional cross-reference-index files added (n=1 → n≥3 would resolve the deferred 3rd arm).

<!-- /ref:ltg-phase1-routing-hypothesis -->
