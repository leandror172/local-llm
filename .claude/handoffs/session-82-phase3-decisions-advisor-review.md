# Advisor Review — Phase 3 Decisions, Pre-Freeze

*Session 82 (2026-06-02). Advisor called on the full Phase 3 decision discussion. Written to file for session rewind / re-feed.*

---

**Advisor review — Phase 3 decisions, pre-freeze.** The direction is sound. Dual-path = yes is well-founded, D2=A is now affirmatively (not just defensively) justified, and the D5/D7/D1b mechanics hang together. You're close to a clean freeze. Three things to resolve **before or inside** the frozen block — one is decision-changing, two will block `anchors.py` if left implicit.

## 1. D6's "real test" is an unverified prediction — verify it's satisfiable, or hedge it honestly (decision-changing)

You retargeted D6 away from `ref:thinking-mode` *precisely because it isn't satisfiable on the current corpus*. The new "real test" — orphan anchors (`ref:concept-latent-topic-graph`, `ref:plan-latent-topic-graph`, `ref:ltg-corpus`) merging cross-file with in-corpus topics — is asserted as "almost certainly" close. That is the **same confident-but-unchecked assumption** that the 2/138 enumeration just demolished for thinking-mode. Don't freeze an acceptance clause on it without applying the lesson you just learned.

It's cheap to check now and it's feasibility, not `anchors.py`: embed 2–3 candidate orphan anchors as descriptions (D3 register: heading + first line), compute cosine/L2 against the 69 stored topic vectors, look at where they land.

The reason this is decision-relevant, not hygiene: **the satisfiability is entangled with the threshold.** The two in-corpus self-summary refs are near-identical to their file's topics — they clear *any* threshold. The cross-file LTG anchors are *semantically related but not near-identical* — they may land at cosine ~0.70–0.80. If you set the threshold conservatively (0.85/L2 0.547) to suppress noise, the cross-file merges **don't fire**, and Phase 3's near-term acceptance collapses back to the tautological self-summaries you already conceded prove little. The probe tells you whether a single threshold can catch the real merges without flooding noise — which you cannot know from the distance formula alone.

So: **either** the frozen D6 cites actual probed distances ("ref:X ↔ topic Y at cosine Z, clears threshold") — recommended, a few minutes — **or** it states explicitly that the cross-file merge is a *predicted, unverified* expectation and Phase 3's only asserted near-term acceptance is the integrity check + the tautological sanity merges, with the real mechanism validated at Phase 2.5. Don't freeze it worded as a confident "real test" with neither. (Bonus: the probe doubles as a D3 register-match check.)

## 2. `node_kind = merged` is orphaned by the alias-link decision (blocks implementation)

The schema enum is `node_kind ∈ {extracted, anchor, merged}`. "merged" was the *physical-merge* value — a topic that absorbed an anchor. Under alias-link, both rows survive and the topic row keeps `node_kind = extracted` with a non-null `alias_of`. So **when is `node_kind` ever `merged`?** As written, never. An implementer will stall on this. Pick one and state it in the frozen block:
- (a) Drop `merged` from the enum — alias state is signaled by `alias_of != null`. Cleanest. **Lean.**
- (b) Repurpose `merged` as a denormalized "has ≥1 alias" flag (redundant with `alias_of`, but convenient for `ltg_inspect` filtering).

Either is fine; leaving it ambiguous is not.

## 3. Aliasing must NOT upgrade `confidence` — say so (prevents a misread)

The plan's wording "merged nodes preserve both the anchor confidence and the extracted context" invites an implementer to set `topic.confidence = 1.0` on alias. Under alias-link that's wrong: the pair satisfies the acceptance — **1.0 lives on the anchor row** (and later the alias edge); the topic row keeps its extracted default (0.7) unchanged. State explicitly: *aliasing does not modify `topic.confidence`; provenance confidence reflects how the node came to exist, and an aliased topic is still LLM-extracted.*

## Second-tier (fold into the frozen block, no debate needed)

- **Integrity-check universe.** D2=A + the `.claude/local/` safety filter means the check is "every ref key in **tracked, non-sensitive** files appears as an anchor," not literally "every ref key in the repo." Reconcile the two or the integrity check fails on deliberately-excluded keys. Also confirm the ref walker/`ref-lookup` exposes each ref's **source-file path** — you need it for both the safety filter and the anchor's own `file_path`.
- **Threshold is a procedure, not the number 0.547.** Freeze it as "derive from observed 8-file anchor↔topic distance distribution; 0.547 is only the cosine-0.85 sanity anchor; provisional, recalibrate at Phase 2.5." And **confirm qwen3-embedding:8b vectors are unit-normalized** (or normalize before storing) — the cosine↔L2 identity holds only for normalized vectors, and this is the exact L2-vs-cosine trap from `ref:ltg-phase2-findings #2`.

## Frozen block should contain
Keystone (dual-path=yes) → D2=A, D5=alias-link, D7=Phase-6-deferred · schema fields (`source_class` denormalized string; `confidence` float = 0.7 extracted default, **explicitly node-provenance #2, not edge/retrieval weight, not upgraded on alias**; `anchor_key` nullable; `alias_of` JSON list, nullable, **Phase-4 will relocate to edge table**) · `node_kind` fate (drop or redefine — item #2) · threshold procedure + normalization confirm · safety filter + integrity-check universe · D6 acceptance (sanity merges + cross-file clause **verified or honestly hedged** per #1) · D1/D3/D4 untouched.

**Scope:** all of the above freezes as decisions. The §1 probe is a feasibility check (like the 2/138 enumeration), not `anchors.py` — don't let it slide into writing the implementation.

**Net:** the architecture is right and ready to freeze. Resolve #1 (verify or hedge D6), #2 (node_kind fate), #3 (no confidence upgrade) and the block is complete and buildable.
