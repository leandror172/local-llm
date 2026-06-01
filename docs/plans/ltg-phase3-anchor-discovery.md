# LTG Phase 3 — Anchor Integration: Discovery & Decisions

**Status:** Discovery / decisions IN PROGRESS. **No implementation written.** This document is the resume point for the next session continuing Phase 3.
**Session:** 81 (2026-06-01).
**Branch:** `feature/ltg-phase3-anchors` (stacked on `feature/ltg-extractor-retrofit`; rebase onto `master` after the retrofit PR merges).
**Mode:** discovery + decisions only — freeze decisions, then write `anchors.py` in a later session.

> **RESUME POINT (read first):** No decision below is final. The user had not yet fully read/analysed the §4 empirical enumeration ("only 2 of 138 ref keys live in the 8 files") or the §3 dual-path framing when the session ended. **Next session continues the discussion from §4 onward** — do NOT treat D2/D5/D6 as decided, and do NOT write the frozen `ref:ltg-phase3-decisions` block until the user works through the empirical finding and confirms. D1/D3/D4 are aligned across user+advisor but were stated before the dual-path reframe, so re-confirm them too.

---

## 0. How to resume — required reading (in order)

Read these before continuing the Phase 3 discussion:

1. **This document** — the full discovery state, decision register, and open questions.
2. **Advisor review of these decisions:** `.claude/handoffs/session-81-phase3-anchor-discovery-advisor-review.md` — pushes back on D2, adds the three-confidence clarification and two undefined mechanics (D5, D6).
3. **Phase 3 plan section:** `ref:ltg-plan-phase-3` (`.claude/tools/ref-lookup.sh ltg-plan-phase-3`) — goal, steps, acceptance, deliverables.
4. **Concept / vision:** `ref:concept-latent-topic-graph` (`docs/research/latent-topic-graph.md`) — esp. property #4 (anchor stratification) and the "anchors are first-class nodes" line that grounds the dual-path framing.
5. **Frozen Phase 0 decisions:** `retrieval/DECISIONS.md` — esp. `ref:ltg-corpus` (corpus scope), `ref:ltg-embedding` (qwen3-embedding:8b, 4096-dim), `ref:ltg-storage-layout`, and `ref:ltg-phase2-schema` (the 16-field row — what we're extending).
6. **Phase 2 findings:** `ref:ltg-phase2-findings` (`retrieval/.memories/KNOWLEDGE.md`) — L2-vs-cosine gotcha, R2 borderline, the forward-compat fields.
7. **Retrofit close-out handoff:** `.claude/handoffs/session-80-ltg-extractor-retrofit-advisor-review.md` — what the retrofit delivered (config.yaml two-level shape + `ModelClient.extract_*` that Phase 3 builds on).
8. **Code surfaces Phase 3 touches/extends:** `retrieval/store.py` (schema + write path), `retrieval/model_client.py` (embedding + `embed_texts`/`embed_dim`), `retrieval/embed.py` (winning-row + `embed_mode=description` pattern), `retrieval/config.yaml` (two-level models/roles), `retrieval/ltg_inspect.py` (acceptance/inspection CLI).
9. **Full LTG plan (context):** `ref:plan-latent-topic-graph` (`docs/plans/2026-04-13-latent-topic-graph-implementation.md`) — Phases 0–9, esp. Phase 4 (graph/communities, which consumes Phase 3 output) and Phase 6 (MCP `retrieve_context` — the dual-path consumer).

---

## 1. Where Phase 3 sits

**Goal (plan):** ingest the existing `ref:KEY` graph as **anchor nodes** and merge with extracted topics where appropriate. Record provenance. Write an integrity check (every ref key → ≥1 anchor node).

**Feeds:** Phase 4 (graph assembly + Leiden communities — anchor edges get confidence 1.0, extracted edges = similarity) and Phase 6 (MCP `retrieve_context` — the first cross-repo consumer; the natural home of the dual-path retrieval).

**Prereqs (all clear):** retrofit done (config single-source-of-truth ✓ session 80), embedding upgraded (qwen3-embedding:8b, 4096-dim ✓ session 73), 14B num_ctx re-probe ✓ session 76, Phase 2 index built (8 files, 69 topics ✓ session 72).

**Cheap-migration window:** only the 8 spike files / 69 topics are indexed. Re-embed is ~3s. So Phase 3 can add the *right* schema fields now rather than the minimal ones — the usual "don't over-build the schema" caution doesn't bite when re-indexing is free.

---

## 2. Central reframe — weights generalize anchor stratification

The user's idea: a **configurable weight per input/content type**, fine-grainable (e.g. `.memories/QUICK` vs `.memories/KNOWLEDGE`), with `ref:KEY` weighted separately from topic spans — so all "types" of inputs are configurable, enabling different RAG strategies by reconfiguration.

This is a **strict generalization** of the concept paper's anchor stratification (property #4): anchor-vs-extracted (binary, fixed 1.0/<1.0) becomes one special case of a `source_class → weight` table. It upgrades the published concept from "binary provenance" to "configurable provenance-class weighting enabling pluggable retrieval strategies." Worth folding back into the concept paper as a contribution once validated.

### 2a. THREE distinct "confidence/weight" concepts (do not smear)

The single word "confidence" hides three different things; keeping them separate prevents a knot later:

1. **Retrieval weight** — config-keyed by `source_class`; a ranking multiplier. Tunable WITHOUT re-index. *Tuning belongs in Phase 5 (needs a query loop to measure against); the FIELD lands now.*
2. **Node provenance confidence** — "how much do I trust this node *exists* as stated." Anchor node = 1.0 (human-declared); extracted node = a default. **This is what Phase 3 actually writes** (Phase 3 produces nodes, not edges).
3. **Edge confidence** — anchor edge 1.0, extracted edge = similarity. **This is Phase 4** (no edges exist until graph assembly).

In Phase 3, `confidence` means **node provenance (#2)**. State this explicitly in the frozen doc so the field isn't misread as edge semantics later.

### 2b. `node_kind` and `source_class` are DIFFERENT axes — keep both

- `node_kind ∈ {extracted, anchor, merged}` = **provenance / origin** (already in the schema).
- `source_class ∈ {anchor_ref, memory_quick, memory_knowledge, research_prose, …}` = **content-type for weighting** (new).
- A node is e.g. `node_kind=extracted, source_class=memory_quick`. They coincide only on the anchor row. Collapsing them would force a choice between tracking origin and tracking weight-class.

### 2c. Taxonomy granularity dissolves into a config projection

`source_class` for an extracted node is a **deterministic function of `file_path`** (already stored): `.memories/QUICK.md → memory_quick`, `docs/research/* → research_prose`, etc. So the taxonomy is not a property of the data — it is a **config-defined mapping over `(file_path, node_kind)`**. Consequences:

- **Never freeze granularity.** Start coarse (`anchor_ref` vs `topic_extracted`); add the QUICK/KNOWLEDGE split the day you wire weighting — a config edit + ~3s re-tag, not a migration.
- The class mapping and the weight table both live in `config.yaml` — which *is* the "configurable RAG strategies" vision, landing where the deferred two-level registry (`docs/ideas/ltg-model-registry-design.md`) was already heading.
- Phase 3 only needs to store enough to *derive* class: `file_path` (already there) + `anchor_key` (new). A denormalized `source_class` column is optional convenience for filtering, with the config mapping as source of truth.

**Answer to "coarse or fine?":** start coarse, but model `source_class` as a config projection of `(file_path, node_kind)`. Fine-grained whenever wanted, for free — strictly better than either fixed endpoint.

---

## 3. NEW framing (session 81, late) — ref-keys as a parallel retrieval PATH

The user's extension: the 8 files (and most documents) likely *should* carry ref anchors; this makes `ref:KEY` a **secondary retrieval path**, not just a merge-target. Given an input, the RAG could follow the **topic-spans path**, the **ref-keys path**, or a **combination** — and the input-class separation feeds the routing.

### 3a. Two co-existing retrieval surfaces

- **Topic-spans path** — fuzzy / discovered. Embedding ANN over LLM-extracted topic nodes. Finds latent cross-document connections. Recall-oriented.
- **Ref-keys path** — precise / authoritative. Over the hand-curated `ref:KEY` + `index.md` graph. Both *semantic* (embed the ref block description) and *lexical* (ref keys have names; `index.md` encodes structure). Authority-oriented.

This is grounded in the concept paper's own words: "Anchors are first-class nodes with the same retrieval properties as extracted topics, but their provenance and confidence differ." The dual-path reading emphasizes the *first-class parallel surface* over the *merge*.

### 3b. Combination strategies the weight table now expresses

These ARE the "different RAG strategies":
- **Union + rerank** by `similarity × class_weight` across both surfaces.
- **Anchor-first expansion** — hit authoritative refs, expand to topics aliased to them.
- **Topic-first with anchor-boost** — discovered topics, trust-boosted when curated.
- **Class-routed** — query/input class selects the blend. "What did we *decide* about X" → ref-path (decisions are anchored); "what *relates* to X" → topic-path (discovery).

So the weight machinery generalizes to three levels: per-content-class weight (within-path ranking), per-path weight (topic vs ref blend), per-query-class routing (which strategy). All config-driven.

### 3c. Data-model implication — link, do NOT physically merge

If both paths must stay intact as retrieval surfaces, a "merge" must **not** collapse a topic into its anchor. Instead: **keep both rows; connect them with a high-confidence `alias`/`same_as` edge** (or an `alias_of` field on the topic row referencing the anchor). The plan's acceptance ("merged nodes preserve both anchor confidence and extracted context") is still satisfied — as a *linked pair*, not a fused row.

Benefits: (a) both retrieval paths remain whole; (b) **multiplicity resolves cleanly** — one topic may alias several anchors (multiple edges), which physical merge cannot represent; (c) provenance stays crisp (anchor row keeps `node_kind=anchor, confidence=1.0`; topic row keeps its spans and `alias_of`).

### 3d. Co-evolution (forward idea, not Phase 3 scope)

High-salience recurring topics could be **suggested as new `ref:KEY` anchors** — the curated and discovered graphs feed each other over time. Connects to concept-paper property #5 (derived structure rebalances; salience promotion). Note for a later phase / concept-paper revision; do not build in Phase 3.

---

## 4. Empirical ground truth (enumeration, session 81)

**The 8 extracted corpus files:**
```
.claude/plan-v2.md
.memories/KNOWLEDGE.md
.memories/QUICK.md
docs/ideas/smart-rag3.md
docs/research/smart-rag-index.md
docs/research/smart-rag-repowise.md
personas/build-persona.py
personas/persona-template.md
```

**ref:KEY blocks that physically live INSIDE those 8 files (only two):**
- `ref:smart-rag-research` → `docs/research/smart-rag-index.md`
- `ref:rag-repowise` → `docs/research/smart-rag-repowise.md`

**Interpretation:**
- Merge/alias happens by **embedding similarity**, not file co-location — an anchor can link to a topic from a *different* file. But the corpus is narrow (smart-rag cluster + a few `.claude`/`.memories`/`personas` files), so only **smart-rag-themed anchors** find a partner. Every unrelated anchor (thinking-mode, bash-wrappers, mcp-*) is an **orphan** on this corpus regardless of scoping.
- **This dissolves the noise argument behind D2=B**: orphan anchors don't pollute merges; they sit in the table satisfying the integrity check. The thing B tried to prevent doesn't occur.
- **The plan's headline acceptance example is untestable now**: `ref:thinking-mode` merging with a thinking-mode topic — thinking-mode isn't in the 8 files. Use the two in-corpus refs as acceptance examples instead (D6).
- Node-count under repo-wide ingestion (A): ~138 anchors + 69 topics ≈ **207 nodes** — trivially cheap.

---

## 5. Decision register

| # | Decision | User pick | Advisor | Post-empirical / post-dual-path lean | Status |
|---|----------|-----------|---------|--------------------------------------|--------|
| **D1** | Confidence/weight model | C | C | **C** | ✅ agreed |
| **D1b** | Taxonomy granularity | (asked) | coarse | **coarse, as config projection of `(file_path, node_kind)`** | proposed (likely non-decision) |
| **D2** | Anchor scope | B | A | **A + class-tag** (empirical + dual-path moved it) | ⚠️ OPEN — user to confirm |
| **D3** | Anchor granularity | C-heuristic | C-heuristic | **C-heuristic** (ref-path quality = new escalation trigger) | ✅ agreed |
| **D4** | Schema extension now | yes | yes | **yes** | ✅ agreed |
| **D5** | Merge representation + multiplicity | — | (raised) | **alias-link (keep both rows), many-topics:one-anchor** | ⚠️ OPEN |
| **D6** | Acceptance example | — | (raised) | **retarget to 2 in-corpus refs; broad validation at Phase 2.5** | ⚠️ OPEN |

### D1 — Confidence/weight model
- **A — binary stratification** (plan as-written): anchor 1.0, extracted = similarity. Pros: simplest, matches plan verbatim, ships fastest. Cons: discards weights vision; conflates retrieval-weight with edge-confidence; can't differentiate QUICK/KNOWLEDGE; certain rework.
- **B — full configurable weight table now**: every node tagged `source_class`; config maps class→weight; scoring applies it. Pros: realizes vision immediately; strategies by reconfig; aligns with Phase 8 + registry. Cons: tuning BLIND (no retrieval loop until Phase 5); risk of inventing weight semantics later discarded; more upfront design.
- **C — capture taxonomy now, defer tuning** (chosen): add fields (`source_class`, `confidence`, `anchor_key`), hardcode {anchor 1.0, extracted default}; config weight-table lands Phase 5. Pros: cheap costly-to-retrofit part now; tune with evidence; shippable; trivially upgradeable. Cons: payoff deferred a phase; discipline to not let field rot.

### D1b — Taxonomy granularity
See §2c. Proposed resolution: **config projection** makes this a non-decision — store `file_path` + `anchor_key`, derive class via a config mapping, start coarse, refine free. *Confirm acceptance of this framing.*

### D2 — Anchor scope (OPEN)
| | B (corpus-scoped) | A (repo-wide + class-tag) |
|---|---|---|
| Plan fidelity | redefines frozen acceptance ("**all** ref keys") | matches plan step 1 + acceptance verbatim |
| Axis logic | conflates anchor-scope with corpus-scope | anchor-scope ≠ corpus-scope (concept: ingest curated graph wholesale) |
| Noise | excludes infra refs to avoid noise | empirical: orphans cause no merge noise; class-tag + low weight handles it |
| Relevant-ref risk | may drop out-of-directory smart-rag/LTG refs that SHOULD link | keeps them |
| Dual-path | weakens the ref-path (a secondary surface wants completeness) | ref-path stays whole/authoritative |
| Future cost | re-ingest at Phase 2.5 | none |
| Safety | smaller surface | MUST filter `.claude/local/` + gitignored/sensitive paths explicitly |

**Recommendation:** **A + class-tag** (down-weight `navigation`/`infra` refs, don't exclude). User's B instinct (keep infra out) is better served by weighting than exclusion. **User to make the final call.**

### D3 — Anchor granularity
- **A — one node/block, embed raw body**: simple, 1:1 key↔node; but large heterogeneous blocks (e.g. `ref:bash-wrappers` ~70 lines) embed poorly → merge threshold misbehaves.
- **B — sub-segment large blocks**: better fidelity; but reintroduces chunking (Phase 1 avoided it), breaks 1:1 identity, complex integrity check.
- **C — one node/block, embed a DESCRIPTION** (chosen, heuristic): mirror Phase 2's validated `embed_mode=description`. **Register-matching is the real reason** — extracted topics were embedded as descriptions, so anchor↔topic similarity is only meaningful if the anchor is in the same register; raw-body-vs-description compares unlike things. Keep raw body as retrieval payload. **Heuristic first** (heading + first line — ref blocks are already "one concept per block," so the heading is usually a good description). Escalate to an LLM one-liner only if merge/ref-path quality is poor — don't add an LLM pass on spec.

### D4 — Schema extension now (agreed: yes)
Add (cheap at 8 files): `source_class` (string; or derive — see D1b), `confidence` (float; node provenance, see §2a), `anchor_key` (string, nullable; the ref:KEY for anchor/merged rows), and (per §3c) an `alias_of` reference (string, nullable; topic→anchor link) if the alias-link model (D5) is adopted. Nail field semantics per the three-concepts note.

### D5 — Merge representation + multiplicity (OPEN)
- **Representation:** mutate the extracted topic row (attach `anchor_key`/`alias_of`, `node_kind=merged`) — cleanest — vs a third linking row. Dual-path framing (§3c) favors **alias-link: keep both rows, connect by edge/`alias_of`** so both retrieval surfaces stay intact.
- **Anchor row survival:** under alias-link the standalone anchor row **survives** (it's a ref-path node). Integrity check satisfied either way if the row carries `anchor_key`.
- **Multiplicity:** one anchor near N topics → link all above threshold (**many topics : one anchor**, matches "alias the topic to the anchor"). One topic near M anchors → alias-link permits multiple edges (physical merge cannot). **Decide explicitly.**
- **Recommendation:** alias-link, many-topics:one-anchor, topic may alias multiple anchors. **User to confirm.**

### D6 — Acceptance example (OPEN)
Plan's `ref:thinking-mode` example is untestable on the current corpus. **Retarget to the two in-corpus refs:**
- `ref:smart-rag-research` ↔ the `smart-rag-index.md` topics (it is literally that file's own summary block — a guaranteed link).
- `ref:rag-repowise` ↔ the `smart-rag-repowise.md` topics.
Note that broad merge/alias validation only fully fires after **Phase 2.5** corpus expansion — same "provisional, recheck at 2.5" stance taken for `num_ctx`. **User to confirm.**

---

## 6. Threshold mechanics (carry-over — "do it correctly," not A/B/C)

1. **L2-vs-cosine:** LanceDB returns **L2 distance**, not cosine. Plan's "merge above 0.85 cosine" → for unit-normalized 4096-dim vectors, `L2 = sqrt(2·(1−0.85)) ≈ 0.547`. The merge code MUST convert or it silently uses the wrong cutoff (the exact trap from `ref:ltg-phase2-findings` #2).
2. **4096-dim recalibration:** session 73 deferred N-criteria threshold recalibration to Phase 3 (noise now lands at 0.84–0.98 L2 vs the old `>1.0`). Set the alias/merge threshold from the **observed 8-file score distribution**, not the paper's 0.85 guess.
3. **Provisionality:** a threshold tuned on 69 topics won't generalize — **mark provisional, recalibrate at Phase 2.5** (consistent with the num_ctx recheck trigger).

---

## 7. Safety / scope discipline

- **`.claude/local/` filter (D2=A safety):** with repo-wide anchor ingestion, verify NO ref block sources from `.claude/local/` or other gitignored/sensitive paths (chatbot-safe scope convention). Quick filter — do it.
- **Discovery-only mode:** everything here is freezable as decisions WITHOUT writing `anchors.py`. Resist letting D1's weight-table or D3's LLM-summary creep into Phase 3 — both deferrable, deferring is correct.

---

## 8. Open questions for the next session

1. **D2 final call** — hold B, or move to A + class-tag (recommended)? Dual-path framing pushes hard toward A.
2. **D5 final call** — confirm alias-link (keep both rows) + many-topics:one-anchor + topic-may-alias-multiple-anchors.
3. **D6 final call** — confirm retargeting acceptance to the 2 in-corpus refs + Phase-2.5 deferral for broad validation.
4. **D1b** — confirm the config-projection framing (likely a non-decision).
5. **Dual-path data model** — confirm the alias-link model is what Phase 3 builds (vs the plan's physical merge). This is the single biggest design choice the new framing introduces; it determines the schema (`alias_of` vs `node_kind=merged` row mutation) and the Phase 6 retrieval surface.
6. **Then:** write the frozen decisions into `retrieval/DECISIONS.md` (new `ref:ltg-phase3-decisions` block) + update `ref:ltg-plan-phase-3` notes — still no implementation. After that, a separate session writes `anchors.py` TDD.

---

## 9. Appendix A — full prior analysis output (verbatim, session 81)

> The empirical check is decisive — and it reshapes the D2 debate. Here's what's actually in the index:
>
> **Only 2 of the 138 ref keys live inside the 8 extracted files:**
> - `ref:smart-rag-research` → in `docs/research/smart-rag-index.md` ✅ extracted
> - `ref:rag-repowise` → in `docs/research/smart-rag-repowise.md` ✅ extracted
>
> **Insight:**
> - **Merge is by embedding similarity, not file co-location** — so an anchor can merge with a topic from a *different* file if they're semantically close. But the corpus is narrow (the smart-rag cluster + a few `.claude`/`.memories`/`personas` files), so only **smart-rag-themed anchors** will find a merge partner. Every other anchor (thinking-mode, bash-wrappers, mcp-*) is an **orphan** on this corpus regardless of whether we scope by directory or repo.
> - This **dissolves the noise argument behind your D2=B.** Orphan anchors don't pollute merges — they just sit in the table satisfying the integrity check. The thing B was trying to prevent (noise) doesn't actually happen, because unrelated anchors have nothing to merge with.
> - It also exposes a **hidden cost of B**: corpus-scoping by directory would still *exclude* the infra refs — but more importantly, the smart-rag cluster's *most relevant* anchors (`ref:rag-llm-wiki`, `ref:concept-latent-topic-graph`, `ref:plan-latent-topic-graph`) live in files that *weren't* in the 8 extracted. They'd merge beautifully with the extracted smart-rag topics — and a too-aggressive scoping risks dropping them.
>
> **Your explicit question: taxonomy granularity (D1 sub-decision).**
> The naïve framing: define `source_class` as just `{anchor_ref, topic_extracted}` (coarse) or `{anchor_ref, memory_quick, memory_knowledge, research_prose, …}` (fine) now? Advisor leans coarse; user leans fine (QUICK/KNOWLEDGE vision).
> But `source_class` for an extracted node is a deterministic function of its `file_path` (already stored). So the taxonomy is a **config-defined mapping over file_path** (plus `node_kind` for anchors). Therefore: never freeze granularity (start coarse, add splits via config edit + ~3s re-tag); class mapping + weight table both live in config.yaml (= the configurable-RAG-strategies vision); Phase 3 only stores enough to derive class (file_path + anchor_key). Answer: start coarse, model `source_class` as a config projection of `(file_path, node_kind)`.
> Advisor's reinforcing point: `node_kind` and `source_class` are different axes — keep both. `node_kind ∈ {extracted, anchor, merged}` = provenance; `source_class ∈ {memory_quick, research_prose, …}` = content-type for weighting; coincide only on the anchor row.
>
> **The D2 conflict — surfaced, not silently resolved.** User said B; advisor argues A (all refs repo-wide, class-tagged).
> Comparison: plan fidelity (B redefines frozen acceptance / A matches verbatim); axis logic (B conflates anchor-scope with corpus-scope / A treats them as distinct — concept paper ingests curated graph wholesale); noise (B excludes to avoid noise / A: empirical shows orphans cause no noise, class-tag handles it); relevant-ref risk (B may drop out-of-directory smart-rag refs that should merge / A keeps them); future cost (B re-ingests at 2.5 / A none); safety (A must filter `.claude/local/`).
> Honest read after empirical check: lean A. B's core benefit (noise reduction) is largely illusory; its costs (redefining frozen criterion, dropping relevant anchors, re-ingestion) are real. The genuine infra-clutter concern is better handled by your own weights idea (tag `navigation`/`infra`, down-weight). But it's the user's call; B defensible with `.claude/local/` filter if keeping indexed surface small matters.
>
> **Two NEW decisions the advisor surfaced (must settle before freezing).**
> D5 — how is a "merged" node represented + multiplicity: mutate the extracted row (attach `anchor_key`, `confidence=1.0`, `node_kind=merged`) — cleanest — vs a third linking row; does the standalone anchor row survive or get consumed; multiplicity 1:1 vs many:1 (plan's "mark the topic as aliased to the anchor" hints many topics : one anchor).
> D6 — is the acceptance test satisfiable on the current corpus: plan's `ref:thinking-mode` example not testable now; use two clean in-corpus merges instead (`ref:smart-rag-research` ↔ smart-rag-index topics; `ref:rag-repowise` ↔ smart-rag-repowise topics); note broad validation only fires after Phase 2.5.
>
> **Where the decisions stand:** D1=C ✅, D1b=coarse-as-config-projection, D2=user-B vs my-now-A (user's call), D3=C-heuristic ✅, D4=extension ✅, D5=mutate-row + 1:1-vs-many:1, D6=retarget to 2 in-corpus merges. D1/D3/D4 settled and agree. Open: D2, D1b, D5, D6.

---

## 10. Appendix B — advisor review

Full text: `.claude/handoffs/session-81-phase3-anchor-discovery-advisor-review.md`. Summary: agrees C / C-heuristic / extension; pushes back on D2 (argues A); adds the three-confidence clarification (§2a), node_kind-vs-source_class axes (§2b), and the two undefined mechanics now tracked as D5 + D6; flags threshold provisionality (§6) and `.claude/local/` safety (§7). Advisor's "if you change one thing": flip D2 to A (class-tagged) and add D5 + D6 before writing the design doc.
