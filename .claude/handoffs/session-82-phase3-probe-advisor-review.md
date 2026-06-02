# Advisor Review — Phase 3, Post-Probe

*Session 82 (2026-06-02). Advisor called after anchor-similarity probe results. Written to file for session rewind / re-feed.*

---

**Advisor review — Phase 3, post-probe. The architecture is right and ready to freeze. The probe was the correct call and it paid off — but it quietly reintroduced the exact assumption-class we've now caught twice, one level down. One cheap re-check before you can honestly call D6 "verified"; two folds; the rest freezes.**

## 1. The probe validated curated descriptions, not the D3 heuristic it was supposed to test (small blocker on the "verified" wording)

Look at what you actually embedded. `ANCHOR_DESCRIPTIONS` are hand-written strings — for `ref:concept-latent-topic-graph` you wrote a clean one-sentence gloss; for `ref:ltg-corpus` you *inlined the directory bullets* into the description. That is **not** "heading + first line" extracted mechanically, which is what D3 freezes and what `anchors.py` will actually do.

Why this matters, concretely:
- "First line" is **underspecified**. `ref:concept-latent-topic-graph` leads with an italic metadata note (`*Draft concept note. Model-agnostic…*`), then `## Abstract`, *then* the sentence you used. A literal "first line after heading" rule grabs the metadata line — garbage register. You silently resolved that ambiguity with human judgment. `anchors.py` can't.
- So two things are unverified, not one: (a) D6's positive result is conditional on description quality you supplied by hand; (b) **D3's own "heuristic suffices, escalate to LLM only if poor" claim was never actually tested** — the heuristic didn't run.
- The margins say this isn't hypothetical. `ref:ltg-corpus` top hit is 0.8157 (0.06 under the line) and `concept` rank-3 is 0.8357 — both description-sensitive near-misses. A worse mechanical description can flip the abstract merges from "clears" to "doesn't."

Fix is cheap and it's still feasibility, not `anchors.py`: **define the extraction rule precisely** (e.g., heading + first non-empty, non-metadata, non-sub-heading prose line) and **re-run the same probe with mechanically-extracted strings.** If the strong merges hold (0.90+), D6 is *genuinely* verified and D3's heuristic is validated in one shot. If they degrade, you've learned — before freezing "heuristic first" — that the LLM-one-liner escalation fires on day one. Either outcome is worth the few minutes. Until then, freeze D6 as "verified for curated descriptions; mechanical-heuristic check pending," not a flat "measured result."

## 2. Fold: temper two claims in the frozen block

- **"Non-tautological cross-file merge."** Both fired merges are `concept/plan` anchor ↔ `.memories/` *summary-of-the-same-concept*. That's genuinely cross-file (it does prove the cross-file path works — good), but it's still abstract-to-abstract. The harder, higher-value case — an abstract anchor linking to an *incidental applied mention* — did **not** fire: `graph_exploitation` (0.836), `hybrid_retrieval` (0.734) all sit below 0.85. So the probe shows the ref-path aliases at the summary level but the cross-pollination payoff awaits Phase 2.5. Say that; don't let "non-tautological at all" stand.
- **"Threshold well-calibrated, clear gap."** True for the 0.90+ merges. But the noise floor for these anchors is 0.81–0.84, a ~0.05 margin — and `graph_exploitation` at 0.836 is arguably a *real* semantic relation being excluded, not "noise." Name the precision/recall tension honestly: 0.85 buys precision at the cost of the applied-mention recall, and it's provisional pending 2.5 recalibration (consistent with your `num_ctx` stance).

## 3. Fold: integrity-check universe + ref-source-path (from my prior review — make sure it lands)

Two enumerable-now items that block `anchors.py` if left implicit: (a) confirm `ref-lookup`/`index.md` actually exposes each ref's **source file path** — you need it both for the anchor row's own `file_path` and for the `.claude/local/` filter; (b) word the integrity check as "every ref key in **tracked, non-sensitive** files," or it fails on deliberately-excluded keys. Don't let these drop out of the freeze.

## Green — freeze as-is, do not reopen

Dual-path = yes; D2 = A; D5 = alias-link, M:N `alias_of` JSON list (probe-validated — both anchors aliased the same two topics, a scalar would have lost one); `confidence` = 0.7 extracted default as node-provenance placeholder, not upgraded on alias; `node_kind` drops `merged` (option a); the anchor "structural authority ≠ human-declared" reframe and deferred `human_reviewed`; D7 → Phase 6; D1b config-projection with denormalized `source_class`; unit-normalization confirmed (0.999999). D1/D3*/D4 untouched (*D3's heuristic pending the §1 re-probe).

## Does it block?

Only §1 blocks, and only the **"verified" status of D6 and D3's heuristic** — not the architecture. Re-run the probe with mechanical descriptions (cheap), or freeze-with-caveat and let the heuristic check happen when `anchors.py` is written. §2 and §3 are wording/enumeration folds. After that the block is complete and buildable — still no `anchors.py`.

One question worth putting back to the user when you draft the block: do they want the mechanical re-probe now (clean "verified"), or freeze-with-caveat and let the heuristic check happen when `anchors.py` is written? That's their call, not mine.
