# Ref citation convention — brackets are the citation form

**Status:** decided 2026-07-25 (latent-topic-graph session 27); rollout unstarted.
**Companion to T-121.** That task owns the *grammar* — what a marker is. This one
owns what a *citation* is, and getting every repo to write one.

<!-- ref:ref-citation-convention -->
## The rule

A citation is written **`[ref:KEY]`**. A bare `ref:KEY` in running prose is **not**
a citation — it is a mention of the key as subject matter, and no tool should treat
it as a pointer.

**This is enforcement, not a new rule.** The two-tier notation table already says
active references use the bracketed form; it has said so since the overlay shipped.
What is new is that practice diverged and nobody measured it until now:

| latent-topic-graph, 184 tracked `*.md` | count |
|---|---:|
| bare `ref:KEY` mentions | **658** |
| bracketed `[ref:KEY]` citations | **7** |

Roughly 1% adherence. The convention was correct and inert; nothing ever depended
on it, so nothing corrected it.
<!-- /ref:ref-citation-convention -->

## Why it stops being inert

The LTG engine's **L-27** turns inline tags into `references` graph edges. The
engine decided **brackets only** — bare mentions outside anchor blocks emit nothing.
That makes the bracket the difference between a citation that becomes structure and
one that does not, in every repo LTG indexes.

The alternative (emit on bare mentions too) was rejected on five grounds, kept here
because the rollout will meet people who ask:

1. **The failure modes are asymmetric.** Forget to bracket → no edge, and the
   engine's diagnostic lists the site. Forget to *avoid* a bare mention under a
   bare-emitting rule → a false edge appears silently in the asserted layer, whose
   defining property is that it contains no inferred edges.
2. **Population ratio.** On the engine corpus the gate measured **193 bare vs 2
   bracketed** sites. Emitting on bare taxes the ~99% who mention a key incidentally
   to serve the ~1% who cite it.
3. **It would falsify documentation.** Docs whose *subject matter* is keys — index
   files, convention guides, a JSON example showing a stored `alias_of` value —
   contain lowercase keys that are neither citations nor mistakes. Any scheme that
   forces them to change makes the document wrong about the thing it documents.
4. **The reversibility window is closing.** Nothing traverses a `references` edge
   today, so over-emission is currently harmless — but LTG's **L-31** is the task
   that ends that. Widening later is additive; narrowing later deletes edges
   consumers may be traversing.
5. **Consumers are unauditable.** The engine cannot detect whether any convention
   was adopted. A repo that never heard of the rule must still be safe by default.

## Companion rule — illustrative keys are uppercase

A key written with an **uppercase first character** is invisible to every
implementation in the chain. Verified empirically 2026-07-25 against the engine's
`markers.py` (mention, inline-tag and block-marker forms all miss) *and* both
dependency-free overlay tools (`ref-lookup.sh` greps `[a-z0-9-]*`,
`check-ref-integrity.py` compiles `[a-z0-9-]+`). This is not a new affordance — it
falls out of the charset — but it has never been written down.

Use it for illustrative, example and placeholder keys.

**Caveat: the uppercase must start at the first character.** `ref:patterns-INDEX`
still matches the stem `patterns-` and lands in the engine's `fragment` class, so a
half-applied convention manufactures fragments instead of silence.

career-search already applied this on the **definition** side (their session 99:
illustration block markers uppercased, because `ref-lookup.sh` was indexing them as
real blocks and shadowing the real key). This extends the same move to mentions.

## Open question — cross-repo citations

Measured on the engine corpus: **93 dangling sites, of which 51 resolve in this
repo (llm) and 42 resolve nowhere.** Bracketing a key that lives in *another* repo
would make `check-ref-integrity` flag a broken tag, since it validates that every
bracketed tag resolves locally.

Three options, none chosen:
- **(a)** leave cross-repo citations bare — honest, but indistinguishable from an
  incidental mention;
- **(b)** uppercase them — silences tooling, but they *are* citations;
- **(c)** a repo-qualified form (e.g. `[ref:llm/KEY]`) — correct, but it is a
  grammar change and therefore T-121's decision, not this one's.

**Decide before the rollout reaches a repo that cites across.** The engine repo
cites llm keys today, so this blocks its own cleanup at the margin.

## What has to change in the overlay

1. **`overlays/ref-indexing/README.md`** — state the citation form normatively.
   This extends R-D5, which already says the specification is the deliverable.
2. **`overlays/ref-indexing/sections/claude-md-ref-rules.md`** — the two-tier table
   already names the bracketed form; add the explicit negative ("a bare mention is
   not a citation") and the uppercase rule.
3. **`overlays/ref-indexing/files/check-ref-integrity.py`** — add the enforcement
   rule that does not exist today: flag a **bare mention of a known key, outside all
   block bodies**, as "should be `[ref:KEY]`". Without a checker the convention
   diverges again, exactly as it already did.
   **Hard constraint (T-121):** the overlay tools stay dependency-free copies — the
   checker must not import `ltg`. career-search runs it without the engine.

## Rollout

Per-repo, in this order — each repo's cleanup is independent once the overlay lands:

| repo | state |
|---|---|
| latent-topic-graph | measured: 494 candidate sites in 64 living files; cleanup in progress 2026-07-25 |
| llm | unmeasured — run the inventory before estimating |
| career-search | LTG consumer, two-tier convention already in use; smallest job (11 sites at last gate) |
| others running the overlay | unmeasured |

**Cost to price in every repo running LTG:** a bracket edit changes file bytes, so
every edited file re-extracts on the next refresh. In the engine repo that is ~60%
of the corpus — a near-full rebuild with corresponding topic churn, not a cosmetic
diff.

**Scope exclusion:** leave frozen records alone — session archives and completed
probe records are history. Rewriting them to satisfy a new convention edits
evidence, which cuts against the keep-corrections-visible ethic.

## Evidence

- Gate + populations: latent-topic-graph `probes/l27-tag-attributability.md`
- Grammar owner: latent-topic-graph `src/ltg/markers.py`
- Grammar ownership decision record: `docs/ideas/ref-grammar-primitive.md` (T-121,
  R-D1–R-D5)
