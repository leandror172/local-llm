# The ref-marker grammar has no owner — layer-0 primitive candidate

**Status:** decision record written, not planned. Registered as **T-121**.
**Surfaced:** 2026-07-24, from the latent-topic-graph side while scoping L-30
(bounding the anchor block read). Evidence is measured, not inferred.

> **Marker-syntax note (load-bearing in this repo).** This doc never writes a
> literal lowercase marker for an example key. `ingest_anchors` in the LTG engine
> harvests by `git grep` over **all tracked `*.md`** — not the corpus manifest,
> and with no fence awareness — so a doc that merely *quotes* a marker
> materializes it as an anchor node in this repo's own LTG index, and
> `check-ref-integrity`'s `find_unclosed` would report a quoted opening with no
> close as an **ERROR**. Examples below use the uppercase placeholder `KEY`,
> which matches neither tool (both require lowercase-hyphenated).

---

## The observation

The `ref:KEY` convention is the shared spine of five repos. It is **specified
only by its implementations**, and those implementations disagree.

| Implementation | Owner | Open-marker grammar |
|---|---|---|
| `overlays/ref-indexing/files/check-ref-integrity.py` | overlay (Python) | whitespace-**tolerant** (`\s*` either side) |
| `overlays/ref-indexing/files/ref-lookup.sh` | overlay (bash) | its own sed/grep forms |
| `latent-topic-graph` `src/ltg/anchors.py` | LTG engine | **exactly one space** each side (via `git grep -oE`) |
| `latent-topic-graph` `src/ltg/graph.py` | LTG engine | mention form, `(?<!/)ref:` + key charset |
| `latent-topic-graph` `probes/l27_tag_attributability.py` | LTG probe | mirrors the engine's two, by hand |

Four owners, five implementations. The overlay tools are *distributed by copy
from one source*, so they are not drift — but the overlay's grammar and the
engine's grammar are two independent definitions of the same convention, and
nothing asserts they agree.

## The concrete failure mode (measured latent, 0 live)

Write an opening marker with no spaces around the key — `<!--ref:KEY-->`:

- `check-ref-integrity` **accepts it as a valid definition** and reports the ref
  system healthy.
- The LTG engine **cannot see it at all** — no anchor node is created.

So the checker certifies a convention the engine silently does not honor. Scanned
2026-07-24 across both corpora: **0 live instances** (self 184 tracked md,
career-search 410). Latent, like most of this class.

A second divergence found the same day, internal to the engine and fixed by
L-30: openings were recognized **anywhere in a line** while closes required an
**own-line** match, so a close carrying trailing prose silently failed to close
and its block ran to EOF. Measured: **0 mid-line markers of either kind** across
594 tracked files, 178 blocks — the looseness served nobody.

## Why this is the layer-0 shape

Same pattern as **T-76** (model registry) and **T-77** (signature extractor): a
small, unglamorous grammar that two or more *products* depend on and neither
should own. Dependencies point down only; no product↔product cycle.

What the primitive would own: the key charset, the open/close marker forms, the
own-line rule, the inline-tag form, and the block-extent scan (open → close,
with the unclosed case bounded). That is roughly 30–40 lines of Python and one
paragraph of specification — the specification being the part that does not
exist today in any form.

## The hard constraint that stops a naive shared library

**The overlay tools must stay dependency-free copies.** This is by design, not
neglect:

- `career-search` runs `check-ref-integrity.py` without importing `ltg` — it is
  an LTG *consumer*, but the integrity checker must work in a repo with no
  Python dependency on the engine at all.
- `ref-lookup.sh` is bash. No Python library serves it.
- The overlay's whole distribution model is file copy (`install-overlay.py`),
  which is what makes it installable into a repo that has nothing else.

So a Python package can unify the **engine** sites and any future Python
consumer. It cannot unify the overlay tooling without either adding a dependency
the overlay explicitly avoids, or generating the tools from one source at
install time — machinery this problem does not yet justify.

<!-- ref:ref-grammar-primitive-decision -->
## Decision record

**R-D1 — Unify inside the LTG engine now, as part of L-30.** One module owning
the grammar, consumed by `anchors.py`, `graph.py` and the probe. This is
**T-72**'s already-registered item ("share the ref-key regex constant, 4th ad-hoc
copy in `graph.reference_edges`"); L-30 makes it the 5th and also changes the
grammar, so extracting at the moment of change is cheaper than a later sweep.
Takes owners from four to three. Precedent for a probe importing engine code
rather than mirroring it: `probes/l19_divisor_fit.py` imports `pass_cap` and pins
against it; the t39 probe imports its promoted primitives back.

**R-D2 — Do NOT extract a cross-repo library yet.** One Python consumer
(the engine) plus two dependency-free tools is not a library; it is one owner and
two copies that must be *checked*, not merged. Extracting now would either break
the overlay's zero-dependency property or add generation machinery for a problem
with zero live instances.

**R-D3 — Add a parity test instead.** Assert that the overlay tooling's grammar
and the engine's grammar accept and reject the same strings. This targets the
actual risk (silent disagreement) at a fraction of the cost, and it is the only
mechanism that would have caught the whitespace divergence. Open question: where
it lives, since it must see both repos — candidates are an llm-repo test that
reads the LTG checkout, or a shared fixture file of accept/reject cases that both
sides test against independently (preferred: no cross-repo path coupling).

**R-D4 — A real primitive earns itself on a second Python importer.** Same
trigger discipline as T-76's "third internal consumer of the shape". Plausible
candidates: T-77's signature extractor if it grows markdown-adjacent parsing, a
second engine that ingests the convention, or any external adopter of the
ref-indexing convention.

**R-D5 — The specification is the deliverable, not the code.** The convention has
five implementations and zero written grammar. Even without extracting a library,
`overlays/ref-indexing/README.md` should state the grammar normatively — charset,
marker forms, own-line rule, inline-tag form — so the next implementation has
something to conform *to*. This is cheap and independent of R-D1–R-D4.

**R-D5 inputs collected so far** (write these into the spec when it is drafted;
both were measured 2026-07-25, not assumed):

1. **Case is significant, and uppercase is the sanctioned escape.** Keys are
   lowercase — `[a-z0-9-]+`. A key written with an uppercase FIRST character is
   invisible to every implementation in the chain: the engine's mention,
   inline-tag and block-marker forms all miss it, `ref-lookup.sh` greps
   `[a-z0-9-]*`, and `check-ref-integrity.py` compiles `[a-z0-9-]+`. This is the
   one behaviour all five implementations have always agreed on, and it is the
   sanctioned way to write an illustrative or example key. **Caveat: the
   uppercase must start at the first character** — `ref:patterns-INDEX` still
   matches the stem `patterns-` and yields a truncated-key fragment. Rationale
   and populations: [ref:ref-citation-convention].
2. **The charset silently excludes keys people actually write.** A real block
   `<!-- ref:ltg-phase2.5-corpus -->` existed in latent-topic-graph and was
   invisible to the engine and to the checker, while `ref-lookup.sh` resolved it
   on DIRECT lookup but omitted it from listings — partial visibility, which
   hides itself. Its citations parsed as the stub key `ltg-phase2` and read as
   dangling. Resolved there by RENAMING the key (commit `fce689b`), not by
   widening the charset — but the spec must state the charset restriction
   explicitly, because nothing currently warns an author that a `.` silently
   deletes their block. Note this is a different failure class from the
   divergences above: every tool agreed, and all were uniformly wrong.
<!-- /ref:ref-grammar-primitive-decision -->

## Triggers

Fire the library extraction on **any one**:

- A second Python consumer of the grammar outside the LTG engine.
- The parity test (R-D3) fails, or proves too awkward to maintain, indicating the
  copies are drifting faster than checking can track.
- A live instance of any cross-tool divergence appears — one real
  checker-accepts-engine-ignores marker turns this from latent to a bug.
- An external adopter of the ref-indexing convention.

## Discipline until then

- Any change to marker recognition on either side gets mirrored on the other in
  the same session, and the parity fixture updated.
- No gratuitous grammar divergence — if the overlay tolerates something the
  engine does not, that is a defect in one of them, not a feature of either.
- New implementations of the grammar are a smell: check R-D4's trigger before
  writing a sixth.

## Relations

- **T-72** (latent-topic-graph) — the engine-side unification; R-D1 is its scope.
- **T-76** — the layer-0 precedent, and the trigger discipline this borrows.
- **T-77** — layer-0 sibling; if it grows markdown parsing it becomes R-D4's
  second importer.
- **T-60 / T-86** — overlay and oficina distribution models; the same
  "who owns this and how does it reach consumers" question in different clothes.

## Provenance

Everything above was measured on 2026-07-24 while scoping latent-topic-graph's
L-30. The instrument that produced the counts is
`latent-topic-graph/probes/l27_tag_attributability.py`; the corpus-level record
is `latent-topic-graph/probes/l27-tag-attributability.md`.
