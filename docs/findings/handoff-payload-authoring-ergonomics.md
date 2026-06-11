# Handoff payload authoring — the "I wrote a generator script" retro

**Date:** 2026-06-06 (session 87) · **Context:** running the new session-handoff pipeline
to finalize the session. Captured at the user's request after they asked *"why did you write
a Python file?"* — a retro on a process choice, with the design questions it exposes.

---

## What happened

To build each F7 handoff payload this session (the dog-food, the temp-branch fold, and the real
finalize) I wrote a small Python generator (`build_*payload*.py`, scratch, now deleted). Each one:
fetched the `replace`-mode interiors via `ref-lookup.sh`, stripped the markers, spliced my two
authored edits into the ~45-line `current-status` block (and one `reading-guide` row) by
`str.startswith` anchors, asserted the anchors were found, and wrote `.claude/local/handoff-pending.md`.

The skill's prescribed flow is simpler: **decide content → author the payload file directly → one
`run-handoff.sh` call.** I substituted a code generator for the "author the payload file" step.

## Why I did it (reasoning in the moment)

- `current-status` is `replace` mode, so the payload must carry the **entire** new interior even
  though I was changing only 2 of ~45 lines.
- I wanted the unchanged 43 lines reproduced **byte-exact**, so a stray typo couldn't silently alter
  an unrelated bullet (which `replace` would then commit).
- The script made the splice **deterministic and assertable** (it fails loudly if an anchor moves).

## What I was trying to avoid

- Hand-retyping a large block from memory and corrupting a line I wasn't supposed to touch.
- The perceived token cost of restating the whole block.

## Why it was the wrong call

- **A `Write` would have done it.** `ref-lookup`'s output is already in my context; the by-the-book
  path is to paste that output into a `Write` of the payload and edit the two lines inline. That is
  equally byte-exact (I'm copying the same bytes) without a program.
- **It made the dog-food less faithful.** The point of running the handoff was to exercise the
  *workflow the skill documents*. A future session (or any agent following `SKILL.md`) will not write
  a generator. I validated the **engine** but not the **authoring UX** as written.
- **Opacity / reviewability.** A script hides what the payload will contain until `--dry-run`; a
  written payload file is directly inspectable before running anything.
- **Scratch + fragility.** It left throwaway files, and `startswith`-anchored splicing is brittle —
  it silently mis-splices if an anchor line's text drifts (the asserts caught it here, but that's
  luck-adjacent, not robustness).
- **The token justification was weak.** Writing ~80 lines of generator + running it is not obviously
  cheaper than pasting the block into a `Write`. The real benefit was correctness, not tokens — and
  correctness was available the cheap way too.

## The legitimate kernel (the real friction)

The instinct wasn't baseless. `current-status` is a **growing chronological list with a mutable
footer** (session bullets + a `**Next:**` line + a few summary lines). Because it's one `replace`
region, *every* handoff must restate the whole, ever-growing block to change a couple of lines. That
friction is real and will only grow. The generator was a poor-man's workaround for it.

This is also a **determinism-vs-authorship** tension: the pipeline's premise is "Claude decides the
content," but the unchanged 43 lines aren't being *decided* — they're being *carried over*. A
`replace` block therefore has two zones — **authored deltas** and **carried-over bulk** — and the
workflow doesn't currently distinguish them.

## Should there be a tool? (options, least → most invasive)

1. **Nothing new — paste `ref-lookup` output into `Write`.** The intended path. Zero new surface.
   Correct answer for *today*. Worth stating explicitly in `SKILL.md` so no one re-derives the
   generator hack.
2. **`run-handoff.sh --dump <role>`** — print a single role's current interior (markers stripped),
   ready to edit. `ref-lookup <key>` already nearly does this for `ref_block` roles; a `--dump` that
   keys off the *register* would also cover `structural`/`field` roles and guarantee the exact bytes
   the applier will swap. Small, in-spirit affordance.
3. **Restructure `current-status` so the list isn't `replace`.** Split the chronological bullets
   (make them `prepend`, like `log-entry` — append a bullet, never restate) from the mutable footer
   (`**Next:**` as its own `field`/small `replace` region). This **removes the restate-the-whole-block
   need at the source** and is the highest-leverage fix. Cost: register + block-structure change,
   and `prepend` lists grow unboundedly without a separate trim step.
4. **A blessed payload-builder / partial-replace ("patch") mode.** Generalize what I ad-hoc'd: let a
   `replace` payload carry only a diff/patch against the current interior. This is the most powerful
   and the most dangerous — it reintroduces "a program assembles the payload," partially defeating the
   "one payload, one call, fully inspectable" simplicity, and needs its own verification. Probably a
   no, or only as a deferred idea.

**Recommendation:** (1) now (document the paste-and-edit path in `SKILL.md`); seriously consider (3)
as the structural fix; treat (2) as a nice-to-have; avoid (4).

## Angles worth recording (some not raised in the ask)

- **The generator is a hand-rolled mini-"Placer."** The deferred local-model enhancement
  (`ref:handoff-placer-enhancement`) exists precisely to expand *terse intent* into *full prose* so
  the author doesn't restate bulk. My script was a deterministic stand-in for it — evidence the
  ergonomic need the Placer targets is **already real in Scope A**, not just a future nicety.
- **Eating-your-own-dog-food integrity.** When the validation run deviates from the documented
  workflow, it under-tests the part most likely to bite real users (the human authoring step). The
  engine being green is necessary but not sufficient.
- **Auditability of the transform.** The `input.md` recovery artifact preserves the payload's final
  *bytes*, but the *transformation* (the generator) was scratch and is gone. For a one-off that's
  fine (git diff + input.md fully audit the result); for anything batched it would matter.
- **Habit risk / slippery slope.** If "write a script to write the payload" becomes normal, the
  pipeline's headline simplicity ("decide content → one file → one call") quietly erodes into
  "write a program that writes the file." Guard the simplicity.
- **When a generator *is* right.** Batch/programmatic cases — e.g. migrating many repos' registers,
  or a scripted backfill across N sessions — justify code. A single interactive handoff does not.
- **Transparency to the user as a first-class cost.** Beyond correctness, the written-payload path
  lets the user see and edit exactly what will be committed *before* a dry-run. Process opacity has a
  real review cost, separate from whether the output was correct.

## Bottom line

The output was correct (`verify: ok`, scoped, checkoffs landed), but the *method* was over-engineered
and off-pattern. For replace-mode blocks: **paste the `ref-lookup` interior into a `Write` and edit
inline — no generator.** The durable fix is structural (option 3): stop making a growing list a
`replace` region so handoffs never restate it. Everything else here is a note, not a build order.
