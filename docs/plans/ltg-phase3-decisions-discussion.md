<!-- ref:ltg-phase3-discussion -->
# LTG Phase 3 — Anchor Integration: Full Decision Discussion

**Status:** Decisions frozen 2026-06-02, session 82.
**Frozen decisions:** `retrieval/DECISIONS.md` (`ref:ltg-phase3-decisions`)
**Discovery doc (session 81 state):** `docs/plans/ltg-phase3-anchor-discovery.md`

## Advisor outputs (session 81–82, in order)

1. `.claude/handoffs/session-81-phase3-anchor-discovery-advisor-review.md` — first advisor review after session 81 discovery; introduced the three-confidence split, node_kind vs source_class axes, D5 + D6 as undefined mechanics, `.claude/local/` safety flag.
2. `.claude/handoffs/session-82-phase3-advisor-discussion-framing.md` — framing review before session 82 discussion; reframed 5 parallel decisions into "one keystone + cascade + two confirmations"; identified D2/D5/D7 as facets of a single architectural choice.
3. `.claude/handoffs/session-82-phase3-decisions-advisor-review.md` — pre-freeze review after all decisions were discussed; flagged probe needed for D6, `node_kind=merged` orphaned, confidence-not-upgraded-on-alias rule.
4. `.claude/handoffs/session-82-phase3-probe-advisor-review.md` — post-probe-run-1 review; flagged hand-crafted descriptions ≠ D3 heuristic, asked for re-probe with mechanical extraction; also fold on non-tautological claim and precision/recall tension.
5. `.claude/handoffs/session-82-phase3-probe2-advisor-review.md` — post-probe-run-2 review; confirmed architecture ready to freeze; three items: hedge `mechanical+key` on LTG-self-referential confound, close ref-source-path verification, keep escalation heuristic out of frozen block.

---

## Session 81 — Discovery origin

Phase 3 started as a straightforward plan step: ingest `ref:KEY` blocks as anchor nodes, merge with semantically similar extracted topics, record provenance. The original plan used a physical merge model (`node_kind=merged`) and treated anchors as "cleaner extracted nodes."

During session 81, two things shifted the design:

**Empirical finding:** only 2 of 138 ref keys live inside the 8 extracted corpus files. This dissolved the noise argument behind corpus-scoped anchor ingestion (D2=B) — orphan anchors have nothing to merge with on the current corpus, so noise is not the problem B was trying to solve.

**Dual-path reframe:** the user extended the anchor concept from "merge-target" to "parallel retrieval surface." `ref:KEY` anchors form an authoritative, hand-curated graph that co-exists with the fuzzy topic-span graph rather than collapsing into it. This became the architectural keystone for all subsequent decisions.

Session 81 ended with D2/D5/D6/D7 open and D1/D3/D4 aligned. The discovery document (`docs/plans/ltg-phase3-anchor-discovery.md`) captures the full session 81 state including the empirical enumeration and dual-path framing in §2–§4.

---

## Session 82 — Decision journey

### The keystone question

The advisor's framing review (handoff #2) identified that D2, D5, and D7 were not independent — they were facets of one architectural choice: commit to dual-path or collapse back to physical merge.

Dual-path = yes because:
- Both surfaces stay independently queryable for Phase 6 routing
- Multiplicity (one topic aliasing multiple anchors) cannot be represented by physical merge
- The "configurable RAG strategies" payoff only materialises if both surfaces exist at query time
- Cost at current scale is near-zero (207 nodes, ~3s rebuild)

Once committed, the cascade followed automatically: D2 → repo-wide (a ref-path needs the full ref graph), D5 → alias-link (both rows survive), D7 → Phase 6's decision (Phase 3 = enablement only).

### D2 — Why A is affirmative, not just defensive

The argument against B was initially defensive ("orphan anchors don't cause noise"). The discussion in session 82 sharpened it to affirmative: cross-file semantic merges between orphan anchors and in-corpus topics *are* the mechanism working as designed. A corpus-scoped anchor set would only ever produce tautological within-file merges — the ref-path is an authoritative whole-repo artifact and scoping it defeats its purpose.

Additional sharpening: the 8 corpus files have likely changed since Phase 2 extraction, and several of the 136 orphan anchors (`ref:concept-ltg`, `ref:plan-ltg`, `ref:ltg-corpus`) are semantically relevant to the extracted content — tested in the probe.

### Anchor authority — structural, not human-declared

The confidence = 1.0 for anchors was initially framed as "human-declared, certain." The user challenged this: most anchors in the repo were added by Claude Sonnet/Opus sessions, not by a human directly. Future anchors could come from local models. What anchors actually have is **structural authority** — they follow an explicit `<!-- ref:KEY -->` convention, they appear in committed files, they tend to be PR-reviewed (though not guaranteed), and they encode the author's (or LLM's) deliberate intent about what constitutes a named concept.

This is different from extracted topics, which are latent — not structurally marked, possibly hallucinated, possibly over-split.

So `confidence = 1.0` for anchors is better read as "maximum structural authority available in this system," not "human-declared certainty." A future `human_reviewed` boolean could split this distinction if it becomes load-bearing. Not added to Phase 3.

**Naming taxonomy as a second graph.** The user also noted that key naming conventions encode relationships that embeddings may not recover: `ref:concept-X` / `ref:plan-X` are explicitly paired by design; `ref:ltg-*` forms a domain cluster; `ref:ltg-corpus` is a sub-topic of `ltg-*` by construction. This is an orthogonal axis to embedding similarity — structural/lexical, declared rather than inferred. The `anchor_key` field stores the key name, enabling future key-prefix parsing for sub-taxonomy or weighting. Not in Phase 3 scope.

### Three-concepts split on "confidence"

The advisor (handoff #1) identified that a single word "confidence" smears three distinct concepts:

1. **Node provenance confidence** — "how much do I trust this node exists as stated." Anchor = 1.0, extracted = 0.7. **This is what Phase 3 writes.**
2. **Retrieval weight** — config-keyed by `source_class`; ranking multiplier. Phase 5 tunes this. Phase 3 lands the `source_class` field as a placeholder.
3. **Edge confidence** — anchor edge 1.0, extracted edge = similarity score. **Phase 4**, no edges exist until graph assembly.

Keeping these explicit prevents the `confidence` field from being misread as edge semantics in Phase 4 or retrieval semantics in Phase 5.

### Why aliasing does not upgrade `confidence`

Under the original physical-merge model, setting `confidence = 1.0` on a merged topic was correct — the node was being *reclassified* from LLM-extracted to anchor-authority. Under alias-link the topic row is not reclassified. It is still LLM-extracted. The fact that it is semantically close to an anchor doesn't change how it came to exist — the extraction might have wrong span boundaries, might be slightly over-split, might be the LLM's paraphrase rather than the author's intent. None of that uncertainty changes because an anchor agrees on the topic. The 1.0 lives on the anchor row. The topic row keeps 0.7.

### `node_kind = merged` is orphaned

The advisor (handoff #3) flagged that under alias-link, `node_kind = merged` never gets written — a topic row keeps `node_kind = extracted` and signals alias state via `alias_of != null`. Two options:
- (a) Drop `merged` from the enum — single source of truth, clean Phase 4 migration, filtering via `alias_of IS NOT NULL`.
- (b) Repurpose as "has ≥1 alias" — minor filtering convenience, but two sources of truth that can diverge on partial writes, and Phase 4 creates a cleanup burden.

Option (a) chosen. Enum is now `{extracted, anchor}`.

### The 0.7 default

0.7 is a chosen placeholder — not empirically derived. It encodes "LLM-extracted, reliable but uncertain." Nothing consumes it until Phase 4/5, so precision doesn't matter yet. What matters: below 1.0 (distinguishes extraction from structural authority), consistent across all extracted nodes (Phase 4 edge scoring won't see heterogeneous priors), documented as node-provenance not edge-weight.

---

## Probe methodology and results (session 82)

### Why the probe was needed

After the D6 retarget (from untestable `ref:thinking-mode` to cross-file orphan merges), the advisor (handoff #3) noted that the "real test" claim was the same class of confident-but-unchecked assumption that the 2/138 enumeration had just demolished. The satisfiability of D6 was also entangled with the threshold: if orphan LTG anchors land at cosine 0.72–0.80, the threshold at 0.85 cuts them out and Phase 3 acceptance collapses back to the tautological self-summaries.

The probe also doubled as a D3 register-match check: embedded as descriptions (D3 rule) and queried against the 69 stored topic vectors (themselves embedded as descriptions in Phase 2). Register mismatch (anchor raw-body vs topic description) would produce meaningless similarity scores.

### First probe run — hand-crafted descriptions

Hand-written descriptions were used initially. Results: `ref:concept-ltg` 2 merges (0.964, 0.905), `ref:plan-ltg` 2 merges (0.928, 0.908), `ref:ltg-corpus` 0 merges (closest 0.816). Unit normalization confirmed (norm 0.999999).

The advisor (handoff #4) flagged that hand-crafted descriptions silently applied human judgment about what was meaningful. For `ref:concept-ltg` the description used the abstract sentence; for `ref:plan-ltg` it used a clean implementation-focused sentence. Neither was "heading + first line" — the D3 heuristic had not actually been tested.

### Second probe run — six methods

Six description methods tested: `handcrafted`, `mechanical` (heading + first prose line, no key), `mechanical+key` (key name + heading + first prose line), `key_only` (key name only, hyphenated), `key_words` (key name only, spaces), `full_content` (first 400 chars of body).

Key findings:

**Hyphenated key name beats space-normalized consistently.** `key_only` (hyphenated) outperforms `key_words` (spaces) across all anchors. qwen3-embedding:8b treats hyphenated identifiers as meaningful compound units — do not space-normalize key names.

**`mechanical` alone fails for plan-type anchors.** The first real prose line of `ref:plan-ltg` is `**Status:** Ready for execution…` — an operational line, not a conceptual description. Mechanical gives top cosine 0.822, 0 merges. Key-name inclusion rescues it: `mechanical+key` gives 0.898/0.861, 2 merges.

**`mechanical+key` is the best all-around method.** Only method besides handcrafted achieving 2 merges on both concept and plan anchors. Key name compensates when body is bad; body adds context when it's rich.

**`key_only` is a documented fast fallback.** Gets 2 merges on concept-type anchors (0.948, 0.869), 1 on plan-type (0.923, misses #2 at 0.834). Useful for batch/no-LLM mode.

**`ref:ltg-corpus` is a genuine orphan regardless of method** (0.619–0.816). Corpus-scope decisions don't appear in extracted content by construction.

**M:N validated empirically:** both `ref:concept-ltg` and `ref:plan-ltg` alias the same two topics (`latent_topic_graph` + `ltg_implementation`). A scalar `alias_of` would have silently dropped one anchor. JSON list is correct.

**Unit normalization reconfirmed** across all methods (norm 0.999999–1.000000). The cosine↔L2 formula `L2 = sqrt(2*(1-cosine))` is valid.

### The LTG-self-referential confound (advisor handoff #5)

All positive merges in the probe were LTG anchors matching LTG topics — the key tokens `latent-topic-graph` and `ltg-` appear directly in the target topics. This is the single most favorable possible case for key-name inclusion. The probe measured recall on true merges; it never tested false-merge precision on generically-named anchors (`ref:git-safety`, `ref:patterns-index`) where the key tokens are common words that could pull toward unrelated topics.

This is the same sample-bias the probe was designed to catch for other claims. Frozen accordingly: `mechanical+key` is provisional, validated on LTG-self-referential anchors, recheck at Phase 2.5.

### Precision/recall tension at 0.85

The threshold at cosine 0.85 / L2 0.547 produces a clean gap for the LTG anchors (0.90+ vs 0.84 and below). But `graph_exploitation` at cosine 0.836 is arguably a real semantic relation being excluded — graphs and LTG are genuinely related. The threshold buys precision at the cost of applied-mention recall. This is named honestly in the frozen block: provisional, recalibrate at Phase 2.5.

### Abstract-to-abstract vs abstract-to-applied-mention

The fired merges (concept/plan anchor ↔ `.memories/` summaries) are abstract-to-abstract — both the anchor and the topic describe the LTG concept at a high level. The harder, more valuable case — an abstract anchor linking to an incidental applied mention in a different domain file — did not fire (closest was `graph_exploitation` at 0.836). This is the Phase 2.5 story: corpus expansion to non-LTG files is where the cross-pollination payoff lives.

---

## D3 escalation — merge-quality-based, not status-line detector

The initial escalation framing was: detect operational first-prose-lines (lines starting with `**Status:**`, `*Created`, etc.) and escalate those anchors to an LLM one-liner.

The advisor (handoff #5) pointed out: (a) `parse_first_prose_line` already skips italic metadata, so most of the list is redundant with existing code; (b) more importantly, with key-name inclusion `plan-ltg` already merges at 0.898/0.861 without escalation — no LLM needed. Escalation is therefore a fallback for **weak merge quality**, not a status-line detector.

Frozen as: "escalate to an LLM one-liner if a key's top merge scores are weak." Detection mechanics belong in `anchors.py`. The naming-taxonomy prefix is a free signal for which anchors are likely candidates (plan-* opens with status; concept-* opens with abstract).

---

## Ingestion path — grep, not ref-lookup

`ref-lookup.sh --list` emits key names only — no file paths (verified session 82). `anchors.py` needs source file paths for both the anchor row's `file_path` field and the `.claude/local/` safety filter. Ingestion must use a direct repo grep:

```bash
grep -rn "<!-- ref:KEY -->" . --include="*.md"
```

Output format: `file:line:marker` — gives file path and line number in one pass. This is also what `ref-lookup.sh` does internally (per its comment header). Filter `.claude/local/` and gitignored paths on this output.

A deferred task exists to add a `--paths` (or similar) flag to `ref-lookup.sh` to expose source paths directly. See tasks.md.

---

## D7 framing — Phase 3 = enablement, Phase 6 = decision

D7 (path-selection binding time: query-time vs build-time) was raised by the user in session 81 as genuinely open. The advisor reframed it: it is not a Phase 3 decision. Phase 3's obligation is to not foreclose — store both surfaces and keep them linked via `alias_of`. D2=A + D5=alias-link already deliver this.

Phase 6 (`retrieve_context`) is the natural consumer and the correct place to decide: span-only / ref-only / both per query, or per input-class routing via `config.yaml`. Lean for Phase 6: query-time (one index serves all strategies, blend is config-driven). This is the payoff the weight-table was meant to unlock.

---

## Open items deferred to Phase 2.5

- **Threshold recalibration:** current 0.85/0.547 is from a 3-anchor LTG-self-referential probe. Recalibrate from the full distribution after Phase 2.5 corpus expansion.
- **Key-name weighting precision check:** false-merge precision on generic anchors (`ref:git-safety`, `ref:patterns-index`). May need a precision penalty or lower weight for key-name contribution.
- **Broad merge validation:** non-LTG corpus, non-summary topics, abstract-to-applied-mention merges.
- **Stale corpus:** if 8-file re-extraction runs before Phase 2.5, re-run anchor linking against fresh topics.
- **`human_reviewed` boolean:** if the structural-authority vs human-reviewed distinction becomes load-bearing.

<!-- /ref:ltg-phase3-discussion -->
