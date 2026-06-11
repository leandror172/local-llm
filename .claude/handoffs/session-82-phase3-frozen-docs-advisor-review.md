# Advisor Review — Phase 3 Frozen Docs (DECISIONS.md + Discussion File)

*Session 82 (2026-06-02). Advisor called on `ref:ltg-phase3-decisions` block in `retrieval/DECISIONS.md` and `docs/plans/ltg-phase3-decisions-discussion.md`. Written to file immediately.*

---

**Advisor review — Phase 3 frozen docs (DECISIONS.md `ref:ltg-phase3-decisions` + discussion file).** The architecture is sound and none of the decisions need reopening. The discussion file is accurate and complete — advisor-file references check out, the journey is faithfully captured, no changes needed there. But the **frozen block has one implementation-blocking omission and two concrete factual errors** that should be fixed before this is treated as final/buildable. All are mechanical fixes; none touch a decision.

## 1. Blocker — anchor rows have no field-population spec (add this)

The block adds 4 new fields but the Phase 2 schema (`ref:ltg-phase2-schema`) has ~16 existing ones. An anchor row must populate **all** of them, and the block is silent on how. This is the exact "implementer will stall" class you elevated to a Phase 3 *decision* for `node_kind=merged`, the 0.7 default, and scalar-vs-list `alias_of`. Leaving anchor-row semantics implicit is inconsistent with that standard. Specify, in one short table or paragraph:

- **`id`** — Phase 2 uses `"{file_path}:{topic_slug}"`. Anchors need a convention. `anchor_key` is already globally unique, so either `id = anchor_key` or `id = "{file_path}:{anchor_key}"`. This is **load-bearing for the integrity check** — "every ref key appears as ≥1 anchor node" is checked by querying anchor identity, so pick the queryable key now.
- **`spans`** — anchors *do* have a location (the ref-block line range; your ingestion grep already returns the start line). D3 says "keep raw body as retrieval payload," but **no field stores raw body** — and it doesn't need one if anchors store their ref-block line range in `spans` (raw body re-derived from `file_path`+`spans`, exactly as topics do). So: `spans` is NOT null for anchors. State that — it's what satisfies D3's retrieval-payload clause.
- **`embed_model` / `embed_dim` / `embed_mode`** — same as topics (`qwen3-embedding:8b` / `4096` / `description`).
- **`extractor_model` / `extraction_run_id` / `extraction_timestamp` / `file_role`** — null/empty for anchors (not extracted). Say so explicitly.
- **`vector`** — each anchor carries the 4096-dim embedding of its `mechanical+key` description. (Implied, but make it explicit since it's an inherited field.)

## 2. Fix — D6 concept-anchor distances cite the wrong method

The block's D6 says `ref:concept-ltg` merges at **0.978 / 0.965 "via mechanical+key."** Those are the **`mechanical`** numbers (0.9775 / 0.9645). The chosen `mechanical+key` default gives **0.972 / 0.970**, and the rank order flips. Correct text:

> `ref:concept-ltg` ↔ `.memories/QUICK.md::ltg_implementation` (cosine **0.972**) + `.memories/KNOWLEDGE.md::latent_topic_graph` (**0.970**) — both via `mechanical+key`.

(The plan-ltg cited 0.898/0.861 are correct — those *are* the mechanical+key numbers. Only concept is mislabeled.) Doesn't change the verdict — concept clears handily either way — but a frozen acceptance record should cite the method it's actually freezing.

## 3. Fix — the ingestion grep pattern is non-functional as written

D2 states the command literally as `grep -rn "<!-- ref:KEY -->" . --include="*.md"`. With `KEY` as literal text this matches **nothing**, and substituting one key defeats enumeration. Replace with a prefix/regex match, e.g.:

```
grep -rnoE '<!-- ref:[a-z0-9-]+ -->' . --include='*.md'
```

(matches opening markers only — `<!-- /ref:` closers are correctly excluded). An implementer copy-pasting the current text gets zero rows.

## 4. Verify before trusting the integrity-check wording (open half of prior item)

The prior review (#5, item 2) asked you to close the ref-source-path question before wording the integrity check. You confirmed `--list` lacks paths and switched to grep — good — but never confirmed the **grep's key set matches what `ref-lookup.sh --list` reports (~138).** The integrity check now *defines* its universe as the grep output; if grep misses keys that `--list` finds (e.g., a ref block in a non-`*.md` file, or an edge-case marker), the universe is wrong. One command:

```
diff <(ref-lookup.sh --list | sort) \
     <(grep -rhoE '<!-- ref:[a-z0-9-]+ -->' . --include='*.md' | sed -E 's/<!-- ref:(.*) -->/\1/' | sort -u)
```

If it diverges, the D2 integrity-check sentence needs adjusting (or the grep needs widening beyond `*.md`). This is a verify-then-maybe-edit, not a definite change — flagging because it's the unclosed half of an item you already accepted.

## 5. Minor — node_kind enum

The block freezes `node_kind ∈ {extracted, anchor}`. The Phase 2 schema explicitly anticipated `community` (Phase 4). Add a parenthetical — "`{extracted, anchor}` for Phase 3; `community` added Phase 4" — so the 2-value enum isn't read as permanently closed.

## Does it block?

**Substance: no** — every decision stands, and #1's anchor-row semantics are forced by the architecture you already chose (they just need writing down). **Buildability/accuracy: yes** — fix #1 (or `anchors.py` stalls), #2 and #3 (factual errors in a frozen record), run #4's check, fold #5. After that the block is complete, internally consistent, and buildable — still no `anchors.py`.
