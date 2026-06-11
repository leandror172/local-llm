**Verdict: the architecture is right and ready to freeze today.** The probe re-run did exactly its job — it caught the mechanical heuristic failing on `plan-ltg`, which is precisely what needed catching before D3 froze. Two wording fixes and one quick verification, then write the block. Do **not** run more probe variants; six methods is past the point of new information.

## 1. The key-name finding is real but its magnitude is confounded — hedge D3 the way you already hedged D6

Every positive merge in the probe is an **LTG anchor matching an LTG topic**, where the key name (`…latent-topic-graph`, `ltg-…`) contains the exact distinctive tokens of the target. That is the single most favorable possible case for key-name inclusion. It is also the *same* "favorable-sample" assumption that `ref:thinking-mode` violated (untestable) and that hand-crafted descriptions violated (mechanical failed for plan). You caught both. You correctly hedged D6 ("abstract-to-abstract; broad validation at 2.5"). **"mechanical+key is the validated default" is the structurally identical claim and has not received the same hedge.**

Freeze it as: include the key name, **hyphenated** (key_words strictly worse — that finding is solid), as provisional — *validated on LTG-self-referential anchors; key-name weighting and the threshold both recheck at Phase 2.5.* And name the untested risk: the probe only measured **recall on true merges, never false-merge precision**. For a generically-named anchor (`ref:git-safety`, `ref:patterns-index`) the key tokens are common words that could pull toward unrelated topics — key-name inclusion may *cost* precision on the anchor class the probe never sampled.

## 2. Close the ref-source-path item before wording the integrity check

You agreed to this twice but haven't verified it. `anchors.py` needs, for every key, its **source file** — for the anchor row's `file_path` *and* the `.claude/local/` filter. `ref-lookup.sh --list` exists (resume cited 138 keys). Confirm it emits file paths, not just key names. If it doesn't, ingestion is a repo grep for `<!-- ref:KEY -->`, a different code path you'd rather know now than discover mid-`anchors.py`. One command — run it before freezing the "every ref key in tracked, non-sensitive files" sentence, so the integrity check is implementable as written.

## 3. Keep the escalation heuristic out of the frozen block as anything more than a fallback

Two things: (a) `parse_first_prose_line` already skips italic metadata, so `*Created`/`*Draft` never reach output — the only leak was `**Status:**` (bold) — so your "detect these prefixes" list is mostly redundant with code you have; (b) more importantly, with key-name inclusion as default, `plan-ltg` already merges with **no escalation**. So escalation is a fallback for poor merge quality, not a status-line detector. Freeze it as "escalate to an LLM one-liner if a key's merges are weak" and leave detection mechanics to `anchors.py`. Don't over-specify implementation in a decisions doc.

## Green — freeze as-is
Dual-path=yes; D2=A; D5 alias-link, M:N `alias_of` JSON list, confidence 0.7 node-provenance (not upgraded on alias); `node_kind` drops `merged`; D7→Phase 6; D1b config-projection, denormalized `source_class`; anchor "structural authority ≠ human-declared" reframe + deferred `human_reviewed`; unit-normalization confirmed; threshold 0.85/L2 0.547 provisional, recheck at 2.5. D1/D4 untouched; D3 with the hedge in #1.

## Does it block?
**No.** Nothing here blocks the freeze or the architecture. #1 and #3 are wording; #2 is a one-command check to run before you finalize the integrity-check sentence. Write the block today — the LTG-self-referential confound caps what any further probing can teach you, so the honest move is freeze-with-hedge, not more measurement.
