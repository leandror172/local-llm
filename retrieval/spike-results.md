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

### User's per-file scores

_Pending — will be exported from HTML viz localStorage once scoring complete._

| File | gemma3:12b | qwen3:14b | qwen2.5-coder:14b | qwen3:8b |
|---|---|---|---|---|
| `.memories/QUICK.md` | — | — | — | — |
| `docs/research/smart-rag-repowise.md` | — | — | — | — |
| `.claude/plan-v2.md` | — | — | — | — |
| `personas/build-persona.py` | — | — | — | — |
| `docs/research/smart-rag-index.md` | — | — | — | — |
| `docs/ideas/smart-rag3.md` | — | — | — | — |
| `personas/persona-template.md` | — | — | — | — |
| `.memories/KNOWLEDGE.md` | — | — | — | — |

### After speed penalty (−0.25 if < 15 tok/s) — final 8-file averages

| Model | raw avg | TPS | adjusted | verdict |
|---|---|---|---|---|
| qwen3:14b         | 2.69 |  9.4 | **2.44** | ✅ passes — winner overall (lead 0.17 over qwen3:8b) |
| qwen3:8b          | 2.27 | 38.4 | **2.27** | ✅ passes; 4× faster; **best on cross-reference index format** |
| qwen2.5-coder:14b | 2.01 |  6.5 | **1.76** | ❌ fails overall — code-only candidate |
| gemma3:12b        | 1.61 | 16.7 | **1.61** | ❌ fails — boilerplate + off-by-one on dense bullets + under-extraction on long prose |

**Claude draft track complete (8/8).** Final reconciliation now waits on user's HTML-viz scoring track. Per-file divergences will flag rubric calibration issues; aggregate disagreement >0.3 on any model would be a freeze blocker.

## Final verdict (Claude draft track) — pending two-rater reconciliation + determinism

**Primary candidate:** `qwen3:14b`. Raw range 2.43–2.85 across all 8 file roles (short memory, long prose, dense structured plan, Python code, semi-structured template, repo-wide knowledge doc, cross-reference index, architectural design doc). The single dip below 2.5 was on the cross-reference index format (`smart-rag-index.md`, see insight #7); rebounded sharply to 2.85 on the long-prose sibling document covering the same concepts (insight #8). 9.4 tok/s is slow but acceptable for offline indexing — LTG indexes once, queries many.

**Backup:** `qwen3:8b` if latency matters, **and primary candidate for cross-reference index files specifically**. Clears threshold at 2.27; 4× faster. Risks: (a) duplicate-span-set failure on dense structured files (plan-v2 produced two topics with byte-identical 17-span lists, finding #2); (b) **whole-section drops confirmed in 2 of 8 scored files** (Registration in persona-template.md, Smart RAG in KNOWLEDGE.md — finding #6); (c) topic-bleed and over-broad spans on long architectural prose (smart-rag3.md, multiple topics claiming the same `[76,81]` lines).

**Not recommended as general-purpose extractor:** `gemma3:12b` (boilerplate descriptions + off-by-one on dense bullets + under-extraction on long prose — only 6 topics for an 84-line architectural doc), `qwen2.5-coder:14b` (off-by-one span numbering on dense prose; emits structural meta-topics on long architectural docs — three rule-3 violations on `smart-rag3.md`; worst single-file score 1.55).

**Do not freeze yet.** Gate the final `ref:ltg-extractor` decision-replacement on:
1. **Two-rater reconciliation** — user's HTML-viz scores must agree on the ranking; per-dim divergences signal rubric calibration issues (especially dim 8 weight, see finding #6)
2. **Determinism re-runs on winner** (dim 9 Jaccard) — does qwen3:14b's `smart-rag-index.md` off-by-one reproduce, or was it sample-unlucky?
3. **MoE probe** per `ref:ltg-phase1-routing-hypothesis` — fold into Phase 2 VRAM co-residence probe
4. **Routing-hypothesis update** — cross-reference index now joins prose and code as a third file class with a different best model; the routing story is genuinely 3-armed (insight #7) and the format-sensitivity is now empirically validated by paired-file evidence (insight #8)

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

<!-- /ref:ltg-phase1-insights -->

---

<!-- ref:ltg-phase1-routing-hypothesis -->
## Open hypothesis — specialized-model routing for extractor

Phase 1 evidence suggests a single extractor model is a local optimum; file-type routing may beat any single-model choice:

- **Code files → `qwen2.5-coder:14b`** (2.48 on `build-persona.py` with tight function-aligned spans vs qwen3:14b's 2.68 with cross-function semantic topics). The tradeoff is "function enumeration" vs "cross-function clusters" — the `ref:ltg-extractor` rubric explicitly flagged this as dim `semantic-vs-syntactic` for code files. Data on this dim is still thin (one code file).
- **Prose files → `qwen3:14b`** (consistent 2.68 raw across 3 prose files of varying density).
- **MoE probe (deferred):** `qwen3:30b-a3b` (hybrid VRAM+RAM, 19 GB MoE with ~3 B active params) and `qwen3-coder:30b` when hardware-headroom permits. Hypothesis: MoE sparse activation may deliver quality closer to dense 30B-class while staying within the 12 GB + hybrid-RAM budget. The Phase 2 VRAM co-residence probe is mandatory before locking embedding anyway; folding MoE extractor eval into that probe is cheap.

**Decision gate:** do not commit to routing until (1) remaining 4 corpus files are scored, (2) MoE candidates evaluated under the same rubric, (3) determinism re-runs executed on the winner(s). Until then, pick `qwen3:14b` as single-model default to unblock Phase 2 integration; revisit when data is complete.

**Revisit triggers:**
- MoE sweep completed → re-evaluate whether routing still beats a single-model choice.
- `qwen3-coder:30b` pulled (gated on hardware-headroom probe — see `ref:deferred-infra`).
- Additional code files added to MVP corpus; current n=1 is too thin.

<!-- /ref:ltg-phase1-routing-hypothesis -->
