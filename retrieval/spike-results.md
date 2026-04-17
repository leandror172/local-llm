<!-- ref:ltg-phase1-results -->
# LTG Phase 1 — Extractor Spike Results

**Context:** Topic extractor A/B decision is at `ref:ltg-extractor`. Rubric and exit criteria frozen session 52 (2026-04-14). Sweep executed session 54 (2026-04-16).

**Status:** Partial — 5 of 8 corpus files scored by Claude (draft). User's independent scoring via HTML viz in progress. Two-rater agreement gates final freeze. Four models × all 8 files run mechanically (32/32 ok).

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
| **average (5 files)** | **1.71** | **2.67** | **2.08** | **2.21** |

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

### After speed penalty (−0.25 if < 15 tok/s)

| Model | raw avg | TPS | adjusted | verdict |
|---|---|---|---|---|
| qwen3:14b         | 2.67 |  9.4 | **2.42** | ✅ passes — clear winner |
| qwen3:8b          | 2.21 | 38.4 | **2.21** | ✅ passes barely; 4× faster |
| qwen2.5-coder:14b | 2.08 |  6.5 | **1.83** | ❌ fails overall — code-only candidate |
| gemma3:12b        | 1.71 | 16.7 | **1.71** | ❌ fails — boilerplate descriptions drag dim 6 |

**Remaining unscored files (3/8):** `docs/research/smart-rag-index.md`, `docs/ideas/smart-rag3.md`, `.memories/KNOWLEDGE.md`. Preliminary ranking unlikely to shift given consistency of qwen3:14b across all 5 file types already scored (short memory, long prose, dense structured plan, Python code, semi-structured template).

## Preliminary verdict (pending 4/8 scoring + determinism)

**Primary candidate:** `qwen3:14b`. Consistent 2.65–2.68 raw across all 5 file types scored so far (short memory, long prose, dense structured plan, Python code, semi-structured template). 9.4 tok/s is slow but acceptable for offline indexing — LTG indexes once, queries many.

**Backup:** `qwen3:8b` if latency matters. Barely clears threshold at 2.20; 4× faster. Risk: duplicate-span-set failure on dense structured files (plan-v2 produced two topics with byte-identical 17-span lists).

**Not recommended as general-purpose extractor:** `gemma3:12b` (boilerplate descriptions), `qwen2.5-coder:14b` (off-by-one span numbering on prose — see `ref:ltg-phase1-insights`).

**Do not freeze yet.** Gate the final `ref:ltg-extractor` decision-replacement on: (1) remaining 4 files scored, (2) determinism re-runs on the winner (dim 9), (3) MoE probe per `ref:ltg-phase1-routing-hypothesis`.

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
