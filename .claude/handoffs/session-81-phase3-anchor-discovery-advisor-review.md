# Advisor Review — Phase 3 Anchor Integration Decisions

*Session 81 (2026-06-01). Advisor called on the Phase 3 discovery analysis. Written to file verbatim, not acted upon, to permit session rewind (context-duplication workaround).*

---

Calling me to write to a file — so this needs to stand alone as a design review the user reads after a rewind. I'll engage the Phase 3 decisions directly. Overall the analysis is strong; the retrieval-weight vs edge-confidence split is a real insight. Two things matter most: a pushback on Decision 2, and two mechanics the analysis didn't surface.

---

# Advisor Review — Phase 3 Anchor Integration Decisions

## Verdict up front
The discovery is solid and the "weights generalize anchor stratification" reframe is correct and worth keeping. I agree with your leans on D1, D3, D4. **I push back on D2** — your lean toward corpus-scoping conflicts with the plan's explicit wording and its stated acceptance criterion. And there are **two core mechanics the analysis hasn't defined yet** that will block implementation if frozen as-is.

## Clarification that tightens the whole design: there are THREE "confidence/weight" concepts, not two
Your split (retrieval weight in config vs edge confidence in graph) is right but incomplete — and the missing third is what `confidence` will actually mean in Phase 3:

1. **Retrieval weight** — config, keyed by `source_class`, a ranking multiplier. Tunable without re-index. *Tuning belongs in Phase 5 (needs a query loop); field now.* ✅ your point.
2. **Node provenance confidence** — "how much do I trust this node *exists* as stated." Anchor node = 1.0 (human-declared); extracted node = a default. **This is what Phase 3 writes**, because Phase 3 produces nodes, not edges.
3. **Edge confidence** — anchor edge 1.0, extracted edge = similarity. **This is Phase 4** (no edges exist until graph assembly).

The single word "confidence" smears 2 and 3. In Phase 3, `confidence` is node provenance (#2). Don't let it pre-empt the Phase 4 edge semantics. Worth stating explicitly in the frozen doc so the field isn't misread later.

## Decision-by-decision

**D1 (confidence/weight model) — agree: C.** Capture `source_class` now, hardcode {anchor 1.0, extracted default}, defer the config weight-table to Phase 5. You can't tune weights without a retrieval loop to measure against; the field is the costly-to-retrofit part and it's free at 8 files. Two refinements:
- **`node_kind` vs `source_class` are different axes — keep both, don't collapse.** `node_kind ∈ {extracted, anchor, merged}` = provenance/origin. `source_class ∈ {anchor_ref, memory_quick, memory_knowledge, research_prose, …}` = content-type-for-weighting. A node is `node_kind=extracted, source_class=memory_quick`. They overlap only on the anchor row; keep them separate for clarity.
- **Taxonomy: start coarse** (`anchor_ref` vs `topic_extracted`), add the QUICK/KNOWLEDGE split when you actually wire weighting. Seeding fine classes now is speculative and you can't validate them yet.

**D2 (anchor scope) — reconsider; I'd take A (all refs repo-wide), not B.** This is my main pushback:
- The plan is explicit: step 1 says "all `<!-- ref:KEY -->` blocks **across the repo**," and the acceptance says "**All** ref keys are represented as anchor nodes." Your B (corpus-scoped) **redefines a frozen acceptance criterion**, which needs a stronger justification than noise.
- **Anchor scope ≠ corpus scope — they're different axes.** `ref:ltg-corpus` governs which files get *topic-extracted*. Anchor ingestion is overlaying the *hand-curated graph*, which the concept paper says to ingest **wholesale** (property #4). The plan author already saw this tension and chose repo-wide for anchors while keeping the corpus a subset. B overrides a considered decision.
- Your actual concern (navigation/archive refs are noise) is **already solved by the class-tag you're building** — down-weight `navigation` refs, don't exclude them. Exclusion forces re-ingestion later.
- **Orphan anchors are a feature, not a bug.** Refs whose source files aren't extracted simply don't merge yet; they still satisfy the integrity check, enrich the Phase 4 anchor subgraph (refs cross-reference each other), and start merging for free at Phase 2.5. 138 anchors + 69 topics = ~207 nodes; trivially cheap.
- One safety check this raises: with repo-wide ingestion, **verify no ref block sources from `.claude/local/`** or other gitignored/sensitive paths (you have a chatbot-safe scope convention). Quick filter, but do it.

**D3 (granularity) — agree: C, with a sharper reason.** Embed a description, not the raw block. The motivation isn't just "avoid dilution" — it's **register-matching**: extracted topics were embedded as descriptions, so to compare anchor↔topic similarity meaningfully for the merge, the anchor must be in the same register. Raw-body-vs-description comparison is comparing unlike things. Keep raw body as retrieval payload. **Heuristic first** (heading + first line) — ref blocks are already curated "one concept per block," so the heading is usually a good description. Escalate to an LLM one-liner only if merge quality is poor. Don't add an LLM pass on spec.

**D4 (schema now) — agree: yes.** Add `source_class`, `confidence`, `anchor_key` while re-index is ~3s. Just nail the field semantics per the three-concepts note above.

## Two mechanics your analysis hasn't defined — these will block implementation
**(1) How is a "merged" node physically represented, and what's the merge multiplicity?** The acceptance says "merged nodes preserve both anchor confidence and extracted context," but flat LanceDB rows force a concrete choice:
- Is a merge **mutating the extracted topic row** (attach `anchor_key`, `confidence=1.0`, `node_kind=merged`) — cleanest — or creating a third row linked to two?
- Does the standalone anchor row survive a merge, or is it consumed? (Integrity check is satisfied either way if the merged row carries `anchor_key`.)
- **Multiplicity:** one anchor near 3 topics — merge all 3, or best-only? One topic near 2 anchors — which wins? The plan says "mark the topic as aliased to the anchor," implying topic→anchor, possibly many topics→one anchor. Decide 1:1 vs many:1 explicitly. This is a Phase 3 decision, not an implementation detail.

**(2) Is the acceptance test even satisfiable on the current 8-file corpus?** The plan's example — "'thinking mode handling' merges with `ref:thinking-mode`" — looks **untestable now**: `ref:thinking-mode` lives in a layer-0 findings doc that is almost certainly *not* in the 8 smart-rag-cluster files, so no thinking-mode topic was extracted to merge with it. **Action before freezing D2/D3:** enumerate which ref keys' source files actually overlap the 8 extracted files (`ref-lookup.sh` gives each ref's location) — those are the *only* refs that can produce a merge. If the overlap is thin, either pick in-corpus merge examples for the acceptance test, or note merges validate properly only after Phase 2.5. This is the difference between "Phase 3 passes" and "Phase 3 looks done but the headline acceptance never fired."

Note these two reinforce each other and D2: repo-wide anchors (A) + a known small merge-overlap set is the honest picture — most anchors are orphans now, a handful merge, all satisfy integrity.

## Smaller flags
- **Threshold provisionality.** Set the merge cutoff from the observed 8-file score distribution (converting cosine→L2: 0.85 → ~0.547, as you noted), but **mark it provisional and recalibrate at Phase 2.5** — same trigger you just used for `num_ctx`. A threshold tuned on 69 topics won't generalize; be consistent about saying so.
- **Scope discipline.** You're in discovery/decisions-only mode. Everything above is freezable as decisions without writing `anchors.py`. Resist letting D1's weight-table or D3's LLM-summary creep into Phase 3 — both are deferrable, and deferring is the right call.

## If you change one thing
Flip D2 to A (all refs, class-tagged), and add the two undefined mechanics (merge representation/multiplicity + acceptance-overlap enumeration) to the decisions list before writing the Phase 3 design doc. The rest of your leans can freeze as-is.
