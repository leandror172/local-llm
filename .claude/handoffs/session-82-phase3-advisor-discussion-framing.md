# Advisor Framing — Phase 3 Anchor Integration: How to Run the Remaining Decisions

## The one thing to see first

Your decision table presents D2, D5, D6, D7, D1b as five parallel open items to work through in sequence. That framing will make the discussion longer and muddier than it needs to be, because **three of them are not independent — they are facets of a single architectural choice.** The integrated picture is:

- **One real now-decision:** *Do we commit to the dual-path architecture, or collapse back to the plan's physical merge?* This single choice resolves **D2, D5, and D7 together.**
- **Two confirmations:** D6 (acceptance retarget) and D1b (taxonomy granularity). Neither is a design fork; both are "confirm and move."
- **Three already-frozen:** D1, D3, D4 — agreed by user and advisor. Do **not** reopen them.

So the discussion is really: **one keystone, then two quick confirmations.**

## The keystone, stated as the question to put to the user

> *"The plan originally treated `ref:KEY` anchors as merge-targets — cleaner extracted nodes. Last session you reframed them as a parallel, authoritative retrieval surface (the ref-path), co-existing with the fuzzy span-topics path. Do we commit to that dual-path architecture in Phase 3's data model, or keep the plan's simpler physical merge?"*

**Dual-path = yes (my lean — it's well-founded and cheap now):**
- *Buys:* a parallel authoritative surface (precise/lexical ref-path alongside the recall-oriented topic-path); clean multiplicity (one topic can alias several anchors — physical merge cannot represent this); both surfaces stay independently queryable for Phase 6 routing; and it's a real contribution back to the concept paper (generalizes property-#4 anchor stratification into configurable provenance-class weighting).
- *Costs:* you must maintain both surfaces always; the schema grows an `alias_of` link; Phase 6 carries routing logic. **At current scale these costs are near-zero** (207 nodes, ~3s rebuild). The cost is mostly *future retrieval-layer complexity, deferred to Phase 6* — not a Phase 3 burden.

**Dual-path = no (collapse to plan):** physically merge topic into anchor (row-mutation, `node_kind=merged`). Simpler retrieval, smaller schema. But it destroys the standalone anchor as an independent node, forecloses the ref-path, and throws away the vision the user got excited about.

## The cascade — keystone resolves three decisions

| Keystone | D2 (scope) | D5 (merge rep.) | D7 (binding) |
|---|---|---|---|
| **Dual-path = yes** | **A** (repo-wide) — forced; a ref-path needs the whole ref graph | **alias-link** — forced; both rows must survive | **enable now, decide in Phase 6** |
| **Dual-path = no** | **A** anyway (plan fidelity + integrity check) | **row-mutation** | n/a — single materialized path |

Commit to dual-path once, and D2/D5/D7 fall out of it.

## D2 — near-forced, regardless of the keystone

A is robust under both branches:
- The plan says "all `<!-- ref:KEY -->` blocks **across the repo**" and the acceptance says "**All** ref keys are represented as anchor nodes," with an explicit integrity check. B overrides a *frozen acceptance criterion.*
- The empirical finding (2/138 in-corpus) **dissolves the noise argument**: orphan anchors have nothing to merge with.
- The user's noise concern is **answered by the class-tag** — down-weight `navigation`/`infra`, don't exclude. Exclusion risks dropping the most relevant smart-rag anchors (`ref:rag-llm-wiki`, `ref:concept-latent-topic-graph`, `ref:plan-latent-topic-graph`) that live in non-extracted files but would merge beautifully.

**Obligates:** a `.claude/local/` + gitignored-path filter — repo-wide ingestion must not pull sensitive sources. Quick, but mandatory.

## D5 — implementation teeth

If dual-path, alias-link is forced. But mechanics need nailing:

1. **Multiplicity is M:N.** "Many topics : one anchor" *and* "one topic may alias multiple anchors." A scalar `alias_of` is insufficient — store as a **JSON-encoded list of anchor keys** (consistent with `spans` and `scope_tags` in `ref:ltg-phase2-schema`).
2. **The alias link is conceptually a Phase 4 edge produced early.** A `same_as`/`alias` edge at confidence ~1.0 *is* an edge, and edges are Phase 4 territory. Options: (a) store denormalized on the topic row as `alias_of` JSON (cheap, migrate to edge table in Phase 4), or (b) introduce a minimal edge representation now. **Lean (a)** — flag that Phase 4 will relocate it, so no downstream code should hard-depend on the topic-row location.
3. **Pick the extracted-node confidence default.** Every doc says anchor=1.0, extracted="a default" — no number chosen. Per the three-concepts split this is **node-provenance confidence (#2)** — "how much I trust this node exists as stated" — NOT edge confidence (#3). Pick a fixed value (e.g., 0.7) and **document explicitly in the frozen block that it is provenance, not edge-weight or similarity.** The exact number doesn't matter yet (nothing consumes it until Phase 4/5), but leaving it undefined means the field rots.

## D7 — reframe as Phase 6's decision

The binding-time *choice* belongs to Phase 6 (the `retrieve_context` consumer). Phase 3's only obligation is *enablement*: store both surfaces and keep them linked so query-time routing remains possible later. D2=A + D5=alias-link already deliver that enablement.

*Phase 3 = don't foreclose. Phase 6 = decide the routing logic.*

Lean remains query-time (strictly more expressive, near-zero cost given 3s rebuilds, and it's the payoff that putting weights/routing in `config.yaml` was meant to unlock).

## D6 — confirm, but with eyes open

Retargeting the acceptance from `ref:thinking-mode` (untestable) to the two in-corpus refs is correct. But be honest: both in-corpus refs (`ref:smart-rag-research`, `ref:rag-repowise`) are **self-summary blocks of their own files** — they will embed near topics from that same file almost tautologically. The retargeted test largely checks "does a file's summary embed near that file's topics" — which exercises the **embedding pipeline more than the anchor-merge mechanism.**

That's fine for "Phase 3 ships," but the core merge claim isn't validated until Phase 2.5. Don't dress it up. Retarget + defer is right.

## D1b — non-decision, confirm and move

Config projection is correct: store `file_path` + `anchor_key`, derive `source_class` via a config mapping over `(file_path, node_kind)`, start coarse, refine free. Keep `node_kind` and `source_class` as separate axes.

Sub-question: store a denormalized `source_class` column or derive purely? **Lean: store it** (cheap, helps `ltg_inspect` filtering) with config as source of truth.

## What the frozen block must contain

1. Keystone outcome (dual-path yes/no) and the resulting D2/D5/D7 settlement.
2. Exact schema fields: `source_class` (string, denormalized), `confidence` (float — chosen extracted default, explicit "node-provenance #2, not edge-weight" note), `anchor_key` (string, nullable), `alias_of` (JSON list of anchor keys, nullable).
3. Threshold mechanics: cosine→L2 conversion (0.85 → ~0.547 for unit-normalized 4096-dim), threshold set from observed 8-file distribution, marked **provisional, recalibrate at Phase 2.5**.
4. Safety: `.claude/local/` + gitignored-path filter.
5. Acceptance: retargeted to 2 in-corpus refs, explicit note that broad validation fires at Phase 2.5 and near-term test is thin.
6. D7 explicitly deferred to Phase 6 (Phase 3 = enablement only).
7. Register-mismatch diagnostic note under D3: if the two in-corpus acceptance merges come back weak, check register-mismatch (heading-only vs LLM-summary register gap) before touching the threshold.

## Integration with surrounding phases

- **Phase 4:** alias links Phase 3 creates *are* proto-edges (anchor edges = confidence 1.0). "Edge produced early" framing reinforces D5's denormalized-now-migrate-later approach.
- **Phase 5:** where `source_class` weights get tuned. Phase 3 lands the field; Phase 5 sets values.
- **Phase 6:** dual-path consumer and the true home of D7 routing.
- **Concept paper:** weight-generalization and dual-path are genuine contributions. Capture once validated — do **not** scope-creep into Phase 3.
- **Consistency check:** alias-link as JSON string fits `ref:ltg-storage-layout` convention (JSON-encoded, not nested types). No frozen decision conflicts.
- **Watch-item (not a reopening of D3):** if acceptance merges come back weak, check register-mismatch first, before touching the threshold.

## How to run the discussion

- **Open with the keystone, not the table.** One real architectural decision; three items fall out; two are confirmations.
- **Present options as plain text, not AskUserQuestion** — environment has a rendering bug.
- **Pause after the keystone** for the user's call before moving to D6/D1b.
- **Do not reopen D1/D3/D4.**
- **End by drafting the frozen block for approval — still no `anchors.py`.**

*Net: one genuine decision (dual-path commit) + a short cascade + two confirmations.*
