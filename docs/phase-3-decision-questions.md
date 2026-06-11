Saved — I'll ask before any `advisor()` call in this main thread from now on.

Now the Phase 3 discovery analysis. Your weights idea is the organizing insight here, so let me start by showing *why* it reframes everything, then run pros/cons on each decision through that lens.

---

# Phase 3 Discovery — Anchor Integration

## The reframe: your weights idea generalizes LTG's core novelty

The concept paper's distinguishing property #4 is **anchor stratification**: "mark every edge with its provenance... human-curated structure is never overwritten." As written, that's *binary* — anchors carry confidence 1.0, extracted edges carry `< 1.0`. Two classes, fixed.

Your idea — *a configurable weight per input type, fine-grainable (QUICK vs KNOWLEDGE), with `ref:KEY` weighted separately from topic spans* — is a **strict generalization** of that property: anchor-vs-extracted becomes one special case of a `source_class → weight` table. That's not a tangent; it upgrades the published concept from "binary provenance" to "configurable provenance-class weighting enabling pluggable retrieval strategies." Worth eventually folding back into the concept paper as a contribution.

`★ Insight ─────────────────────────────────────`
- There are **two distinct things people call "weight"**, and the design is cleaner if we keep them separate. **(1) Retrieval weight** — a multiplier on a node's rank when it surfaces in a query (your idea: `.memories/KNOWLEDGE` boosted, navigation refs demoted). Lives in *config*, tunable without re-indexing. **(2) Edge confidence** — how much we trust a *relationship* (anchor edge 1.0, extracted edge = similarity). Lives in the *graph*, set at build time. The plan conflates them under "confidence"; your idea is really about (1). Designing them as two fields avoids a knot later.
- **Source-class weighting moves tuning out of code and into config** — which is exactly the trajectory of the deferred two-level model registry (`docs/ideas/ltg-model-registry-design.md`) and Phase 8's per-repo `{scope_tags, permission_class}`. Your idea and those two already-planned pieces are the same shape: a config-keyed table the retrieval layer reads. Phase 3 is where that pattern is born.
- **The 8-file corpus is a gift here.** Because nothing but the 8 files / 69 topics is indexed, a schema migration costs ~3s to re-embed. So we can afford to put the *right* fields in now (`source_class`, `confidence`, `anchor_key`) rather than the *minimal* ones — the usual "don't over-build the schema" caution doesn't bite when re-indexing is free.
`─────────────────────────────────────────────────`

So the central Phase 3 question shifts from *"anchor or not?"* to *"what is the node-type taxonomy, and where do weights live?"* The three original decision points all re-resolve under that frame.

---

## Decision 1 — The confidence/weight model (the big one)

**What's being decided:** how nodes carry trust and how retrieval scoring uses it.

| Option                                                              | What it is                                                                                                                                                                                                                                           | Pros                                                                                                                                                                    | Cons                                                                                                                                                                         |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A — Binary stratification** (plan as-written)                     | Two classes: anchor (conf 1.0), extracted (conf = similarity). No retrieval-weight concept.                                                                                                                                                          | Simplest; matches plan + concept paper verbatim; ships Phase 3 fastest; minimal new fields.                                                                             | Discards your weights vision; conflates retrieval-weight with edge-confidence; can't differentiate QUICK/KNOWLEDGE/research; certain rework once weights arrive.             |
| **B — Full configurable weight table now** (your idea, fully built) | Every node tagged `source_class`; `config.yaml` maps class → retrieval weight; scoring applies it. Anchor = just one class at weight 1.0.                                                                                                            | Realizes the vision immediately; different RAG strategies by reconfig, no re-index; generalizes anchor stratification; aligns with Phase 8 + registry design.           | Tuning weights **blind** — there's no `relate()`/retrieve loop yet (Phase 5/6) to measure against; risk of inventing weight semantics we later discard; more upfront design. |
| **C — Capture taxonomy now, defer tuning** (staged path to B)       | Phase 3 adds the *fields* (`source_class`, `confidence`, `anchor_key`) and writes them; weights are **hardcoded** {anchor 1.0, extracted = sim} for now. The config-driven weight *table* lands in Phase 4/5 once there's retrieval to tune against. | Gets the expensive part (schema/provenance) in cheaply now; avoids tuning blind; Phase 3 stays shippable; trivially upgradeable to B (config read replaces a constant). | The "different strategies" payoff is deferred a phase or two; requires discipline to not let the unused field rot.                                                           |

**My lean: C.** You can't *validate* a weight of 0.7-on-QUICK-vs-1.0-on-KNOWLEDGE until there's a query returning ranked results to eyeball — that's Phase 5. But the *field* that makes weighting possible (`source_class`) is the costly-to-retrofit part, and with an 8-file corpus it's free to add now. C is "B, sequenced so you tune with evidence instead of guessing." If you'd rather see the full weighting live immediately even if the numbers are provisional, that's B — defensible given cheap re-indexing, just expect to re-tune.

**Sub-decision (independent of A/B/C): the initial `source_class` taxonomy.** Candidates from your examples: `anchor_ref`, `topic_extracted`, `memory_quick`, `memory_knowledge`, `research_prose`, `ideas_prose`, `claude_meta`. Question for you: **start coarse** (just `anchor_ref` vs `topic_extracted`, add finer classes as corpus grows) **or seed the fine-grained set now** (QUICK/KNOWLEDGE split from day one)? Coarse is less speculative; fine-grained means no migration when you want the distinction.

---

## Decision 2 — Anchor scope: which `ref:KEY` blocks become nodes

There are **138 ref keys** repo-wide, but they're not homogeneous — many are *navigation/archive* pointers (`ltg-plan-*`, `deepcoder-benchmark-*`, `mcp-*-tests`), not content. And `ref:ltg-corpus` froze the MVP corpus to a curated subset.

| Option                                                                     | What it is                                                                                                                             | Pros                                                                                   | Cons                                                                                                                                                                                                          |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A — All 138, repo-wide** (plan's literal wording)                        | Every `<!-- ref:KEY -->` block becomes an anchor.                                                                                      | Complete; integrity check trivially holds; nothing missed.                             | Injects low-value navigation/archive refs as nodes; pulls in keys whose source files are *outside* the frozen corpus (benchmarks, personas) — contradicts `ref:ltg-corpus`; graph noise.                      |
| **B — Corpus-scoped only**                                                 | Only ref blocks whose source file is in `docs/research/`, `docs/ideas/`, `.claude/`, `.memories/`.                                     | Consistent with the frozen corpus; matches what Phase 2 already extracted; less noise. | "Integrity check" redefines to *every corpus ref key* not *every repo ref key*; boundary calls needed (does `docs/patterns/` join?).                                                                          |
| **C — Include all, but weight by ref-class** (uses Decision 1's machinery) | All refs become nodes; navigation/archive refs get a *low* `source_class` weight; content refs get a high one. Data decides relevance. | Realizes weights idea; nothing excluded but noise suppressed; reversible by reconfig.  | Requires classifying refs (content vs navigation) — heuristic (block length, presence of `§` markers, file location) or a manual tag; more work; only meaningful once weighting (B/C from Decision 1) exists. |

**My lean: B for the boundary, with C's class-tag attached.** Stay inside the frozen corpus for the MVP (don't relitigate `ref:ltg-corpus`), but tag each anchor with a ref-class so that *when* the corpus widens (Phase 2.5), navigation refs are down-weighted rather than re-litigated. Note the index's own convention already distinguishes "active reference" (`ref:KEY`) from "navigation pointer" (`§`) — that existing taxonomy is a ready-made classifier seed.

---

## Decision 3 — Anchor-block granularity

Ref blocks vary wildly: `ref:bash-wrappers` is ~70 lines of multi-table content; `ref:test-key` is a stub. One 4096-dim vector for a big heterogeneous block dilutes the signal.

| Option                                                             | What it is                                                                                                                                                                 | Pros                                                                                                                                                                                    | Cons                                                                                                                                                         |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **A — One node per block, embed raw body** (plan default)          | The ref:KEY *is* the node; embed its full text.                                                                                                                            | Simple; 1:1 key↔node; clean provenance; trivial integrity check.                                                                                                                        | Large blocks embed poorly (signal dilution); the merge-with-topic threshold misbehaves on big blocks.                                                        |
| **B — Sub-segment large blocks**                                   | Blocks over N tokens split into multiple anchor nodes sharing the key.                                                                                                     | Better embedding fidelity; finer merge granularity.                                                                                                                                     | Breaks 1:1 key↔node; reintroduces the **chunking** decision Phase 1 deliberately avoided; blurs "anchor = one human-declared unit"; complex integrity check. |
| **C — One node per block, embed a *description*** (mirror Phase 2) | Keep 1:1 key↔node, but embed a short summary/heading-line of the block (parallel to topics embedding `description`, not raw spans); raw body stays as retrievable payload. | Consistent with the *validated* Phase 2 `embed_mode=description`; sidesteps dilution without chunking; preserves anchor identity; summary is a cheap local-model pass over ~138 blocks. | Needs a description per block (one-line LLM summary, or heading + first line as a zero-cost heuristic); summary quality affects merge accuracy.              |

**My lean: C.** It reuses the pattern Phase 2 already proved (embed the coherent description, keep the body as payload), keeps each anchor identity-stable, and avoids dragging chunking into Phase 3. The cheapest viable "description" is *heading + first sentence*; the better one is a one-line `qwen3:14b` summary — both fit your local-first convention.

---

## The threshold mechanics (carry-over, not a new decision but must be settled)

Two threads converge in Phase 3's merge step:
1. **L2-vs-cosine:** LanceDB returns **L2 distance**, not cosine. The plan's "merge above 0.85 cosine" → for unit-normalized 4096-dim vectors, `L2 = sqrt(2·(1−0.85)) ≈ 0.548`. The merge code must convert or it'll silently use the wrong cutoff (the exact trap from `ref:ltg-phase2-findings` #2).
2. **4096-dim recalibration:** session 73 explicitly deferred N-criteria threshold recalibration to Phase 3 (noise now lands at 0.84–0.98 L2 vs the old `>1.0`). The anchor-merge threshold should be set from the *observed* score distribution on the 8-file corpus, not the paper's 0.85 guess.

These aren't A/B/C choices — they're "do it correctly," but I flag them because they're easy to get silently wrong.

---

## What I'd want from you to close Phase 3 discovery

1. **Decision 1:** A, B, or **C** (my lean) for the confidence/weight model — and the taxonomy granularity sub-call (coarse vs fine-grained from day one).
2. **Decision 2:** anchor scope — A, **B+tag** (my lean), or C.
3. **Decision 3:** granularity — A, B, or **C** (my lean); and if C, *heuristic* description (heading+first line) vs *LLM* one-liner.
4. **Schema:** confirm we extend the LanceDB schema now (`source_class`, `confidence`, `anchor_key`) given the cheap-migration window — or stay minimal.

Once you've called these, I'll crystallize them into a Phase 3 design doc (a `DECISIONS.md` addendum + an updated `ref:ltg-plan-phase-3` note) — still **no implementation**, just the frozen decisions, exactly as Phase 0 was done.

One process note honoring your new rule: this analysis is the kind of design fork where the advisor's second opinion is usually high-value. **Want me to call the advisor on these Phase 3 decisions before you commit to them?** (I'll hold unless you say yes.)