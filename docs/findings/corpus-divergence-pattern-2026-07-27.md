# A checker validates the corpus it can see, not the one its consumers use

**Date:** 2026-07-27 (session 131). **Status:** four measured instances across four
unrelated subsystems, three of them found in a single session. Recorded as a pattern with a
detection heuristic; **no remedy chosen** — the audit is the proposed next step.

<!-- ref:corpus-divergence-pattern -->
## The shape

A tool `T` answers a health question — *is this valid / present / covered / fresh?* — over
some set `S_T`. Its consumers act on a different set `S_C`. When `S_T ≠ S_C`, `T` reports
health and the consumers hit the gap.

**The failure is silent by construction, and that is the whole point.** `T`'s answer is not
wrong; it is *true about `S_T`* and read as true about `S_C`. Nothing inside `T`'s scope is
broken, so no error can fire. There is no bug to find — only a boundary nobody compared.

## The four instances

| # | Tool | `S_T` (what it checks) | `S_C` (what consumers use) | Observed |
|---|---|---|---|---|
| 1 | `check-ref-integrity.py` marker grammar (**T-121**) | whitespace-**tolerant** opening markers | LTG `anchors.py` requires exactly one space each side (`git grep -oE`) | **Latent** — 0 live instances across 594 tracked `*.md` in two corpora (2026-07-24). The checker would certify a marker the engine cannot see |
| 2 | `check-ref-integrity.py` file corpus (**T-124**) | filesystem glob of the **working tree** | clones, subagents and the LTG engine read **git-tracked** files | **Live** — `docs/findings/independent-derivations.md` was ref-bearing and untracked since s126; the key resolved on one machine and nowhere else |
| 3 | `.gitignore` `.claude` rules (session 131) | root-anchored `.claude/settings.json` — a slash-bearing pattern binds to its own directory | the stated rationale ("machine-specific") covers **every** `.claude/settings.json` | **Live** — `benchmarks/.claude/settings.json` escaped a rule written to exclude exactly it |
| 4 | LTG `--check` staleness (**L-1**, session 131) | `corpus-manifest.yaml`, 162 files at `e33fe88`, **zero** `docs/plans/` | the queryable index holds `docs/plans` (54 topics), `docs/vision` (50), `docs/findings` (22), `docs/patterns` (20) | **Live** — those files are returned by queries at `confidence: 1.0` while sitting outside the hash comparison, so their edits can never be reported stale |

Three of the four were found in one session, in subsystems with nothing in common beyond
living in this repo. That distribution is the argument for treating it as a class rather
than four coincidences.

## The detection heuristic

For any tool that reports health, coverage, validity or freshness, ask two questions and
compare the answers **out loud**:

1. **Over what set does this tool actually operate?** Not what it is *for* — what it enumerates.
2. **What set do the consumers of its verdict operate on?**

If the two sets are derived from *different definitions* — a glob vs `git ls-files`, a
manifest vs an index, one regex vs another — they will diverge. Not may: the definitions
have no mechanism holding them together, and drift is the default.

**Corollary on scope-narrowing:** every one of the four is a case where the checker's set is
a *subset* or a *variant* of the consumers' set. A checker whose scope is narrower than its
consumers' produces false health; the reverse (checking more than anyone consumes) produces
false alarms, which are noisy but self-announcing. **Silent-and-narrow is the dangerous
direction**, and it is the one that keeps occurring.

## Remedies, none chosen

- **(a) State the corpus in the output.** Cheapest and non-breaking: every health report
  names what it scanned ("162 files from `corpus-manifest.yaml`"). Converts a silent
  divergence into a visible one without deciding whose set is right. Does not fix anything —
  it makes the mismatch legible to a reader who thinks to look.
- **(b) Derive both sets from one definition.** Correct and expensive: the checker and the
  consumers share a corpus resolver. Blocked in the ref-integrity case by a hard constraint —
  the overlay tools must stay dependency-free copies **by design** (career-search runs the
  checker without importing `ltg`, and `ref-lookup.sh` is bash), so no shared Python package
  serves it. This is the same wall T-121/R-D2 hit.
- **(c) Parity tests.** T-121/R-D3's answer for the grammar case: assert both implementations
  accept and reject the same strings. Generalizes to sets — assert the two enumerations agree
  on a fixture corpus. The only mechanism that would have caught instance 1.

## Sibling class, deliberately kept separate

**Knowledge divergence**, where a rule established in one document is violated by a design in
another — no set is involved. Session 131's instance: P2 designs a per-run `run_id` join
whose per-iteration matching is necessarily **order-based**, while T-105 (four sessions later)
banned positional fallbacks outright — *"when identity is unknown, stay silent; a positional
fallback names the wrong call, and mislabeled is worse than missing."* Same silence, different
cause: nobody re-read the older plan against the newer principle. The heuristic above does not
catch it, and pretending it does would blunt both.

## Proposed next step

**Audit, do not fix.** Enumerate this repo's health-reporting tools and record for each the
pair (`S_T`, `S_C`). The audit is cheap, it produces a countable result, and it decides
whether remedy (a) is worth generalizing — rather than remedying four instances one at a time,
which is the ratchet shape T-119 warns about.
<!-- /ref:corpus-divergence-pattern -->
