# Using LTG in this repo — a practical guide

**Date:** 2026-07-27 (session 131) · **Status:** FIRST DRAFT — one session of measured
use. Treat §7's observations as anecdote until they repeat.

**Source and credit:** this guide is derived from `career-search`'s
`.claude/ltg-usage-guide.md` (2026-07-21, session 97), which is the more battle-tested
document — it carries four sessions of observations. Read it too. **What transfers is
marked CARRIED; what differs is marked LLM-SPECIFIC**, and the differences are real,
because this corpus is a different shape from theirs: ~190 files, archive-heavy, and
dense with `ref:` anchor blocks, against their 60 curated claim-bearing files.

This repo also *hosts* the LTG instance (`ltg/`); the engine lives in the sibling repo
`latent-topic-graph`.

---

## 0. The 30-second version

- The MCP tools resolve `instance_dir` automatically — call them with no such argument
  (verified 2026-07-27; it resolved to `/mnt/i/workspaces/llm/ltg`).
- **Query altitude:** conceptual sentences, 8–20 words, describing a *subject area*.
  Not keywords, not quoted claim text. **CARRIED — and re-confirmed here.**
- **Ignore `query_confident` and `low_confidence`.** They track phrasing, not
  correctness. **CARRIED — and violating this cost a detour in session 131.**
- **Use results as pointers, not answers.** In this repo that mostly means: the hit
  names a `ref:KEY`; go read that key. **LLM-SPECIFIC — this is the main workflow.**
- Never refresh without GPU clearance (it competes with `ollama-bridge`).

---

<!-- ref:ltg-usage-corpus-scope -->
## 1. What LTG can see — do NOT read this off `corpus.yaml`

**Measured 2026-07-27: the live index is BROADER than the declared corpus.**
`ltg/corpus.yaml` declares `docs/research/` and `docs/ideas/` under `docs/`, and the
frozen `ltg/corpus-manifest.yaml` (162 files, `meta.commit e33fe88`) contains **zero**
`docs/plans/` and **zero** `docs/findings/` entries. Yet `run-inspect.sh --list` reports
indexed topics from all of them:

| Subtree | Topics in the live index | In `corpus.yaml`? |
|---|---|---|
| `docs/research/` | 217 | yes |
| `docs/ideas/` | 152 | yes |
| `docs/plans/` | 54 | **no** |
| `docs/vision/` | 50 | **no** |
| `docs/findings/` | 22 | **no** |
| `docs/patterns/` | 20 | **no** |

Queries return those files with `confidence: 1.0`, so this is not a rounding artifact.

**Working hypothesis (unverified):** the corpus definition was narrowed at some point and
refreshes are incremental, so files that dropped out of the definition were never pruned
from the index. Do not act on this without checking the engine's refresh semantics.

**Two practical consequences:**

1. **To learn what is actually queryable, ask the index, not the config:**
   `cd ltg && ./run-inspect.sh --list` (zero model calls).
2. **Files in the index but absent from the manifest are outside staleness tracking.**
   `--check` compares manifest hashes, so edits to those files can never be reported as
   stale. Same *family* as career-search's O-8 (a silent staleness hole) via a different
   mechanism — scope divergence rather than a mid-run edit.

**Also true here (CARRIED):** a file is invisible to LTG until it is **git-tracked**, and
the index only reflects the last refresh. Files written this session are not findable.
<!-- /ref:ltg-usage-corpus-scope -->

---

<!-- ref:ltg-usage-query-altitude -->
## 2. Query altitude (CARRIED — and independently re-measured)

`retrieve_context` matches against **extractor-written topic descriptions** (labels like
`delegate_event_model`, `failure_clarity_improvements`), not against source text. Describe
what the topic is *about*.

**Measured session 131, scoring by RESULTS rather than by the confidence flags:**

| Query | Outcome |
|---|---|
| `the event vocabulary and freeze ladder for run ledger events, and how public run state is folded from them` | **Bullseye** — ranks 1/2/4/5 were `ref:delegate-ledger`, `ref:delegate-event-model`, `ref:delegate-p2-events`, `ref:delegate-run-spec`. `query_confident: false`, all items `low_confidence: true` |
| `how should a failed run explain which stage failed, whose fault it was, and what exactly broke` | Adjacent-but-not-target: returned the *handoff pipeline's* failure-clarity work, which is genuinely where "where/whose/what" originated (`ref:delegate-first-principles` #7) but is not the oficina answer |

**A caution against the rule I first inferred.** In session 131 I concluded the opposite —
that short proper-noun queries (`oficina edit mode whole-file-with-context`) beat conceptual
sentences — because that query was the only one returning `query_confident: true`. Scoring
by results instead of by the flag reverses it: the 18-word conceptual query above produced
the single best result set of the session while reporting every negative signal. **Short
proper-noun queries do work in this corpus** (they match anchor-derived topic names), but
they are not better, and preferring them is an artifact of trusting §3's flags.
<!-- /ref:ltg-usage-query-altitude -->

---

<!-- ref:ltg-usage-pointer-loop -->
## 3. The pointer loop — the main workflow here (LLM-SPECIFIC)

**LTG is most useful as a guide to what to read, not as a source of answers.** In this
corpus that is unusually literal: because the repo is dense with `ref:` anchor blocks, a
large share of hits come back with the *marker line itself* as the excerpt — a single-line
span whose entire content is the opening marker. There is no answer in that excerpt to
ingest. The hit is an instruction: **read that key.**

Career-search's guide says "read the top ~6 *files*". That is right for their corpus and
coarse for ours — here `ref-lookup.sh KEY` is a better read unit than the file. Measured
example: session 131's rank-1 hit pointed at the ledger block in `architecture.md` —
~16 lines via the key, against a 196-line file. Roughly 12× less context, strictly more
targeted.

**The loop:**

1. `retrieve_context` with a §2-shaped query.
2. **Collect the `ref:KEY` names** from marker-shaped hits (topic name and excerpt both
   give it away).
3. `.claude/tools/ref-lookup.sh KEY` for each — that is the actual read.
4. **Non-marker hits: read the `spans` range**, then widen if the passage does not stand
   alone.
5. **Widen to the whole file when the question is phase- or file-level.**

**Step 5 is not optional, and here is the case that proves it.** The
`ref:delegate-event-model` block runs lines 20–70 of `event-model.md`. A parked watch-item
reading *"Revisit at P4 (delivery-report format)"* — a live trigger on the plan being
written that session — sits at line ~193, **outside every block**. Block-scoped reading
would have missed it. Out-of-block material is invisible to the anchor graph, and parked
decisions are exactly the kind of thing that lives there.

**Never conclude from an excerpt.** Career-search's O-4 gives the mechanical reason:
excerpts are read live from disk at *stored* spans, so after edits the text and the offsets
can silently disagree. Use spans to locate; verify by content.
<!-- /ref:ltg-usage-pointer-loop -->

---

<!-- ref:ltg-usage-output-reading -->
## 4. Interpreting output (CARRIED, with a 5th confirmation)

- **Ignore `query_confident`.** Career-search measured it unstable across refreshes and
  correlated with query *polarity* (O-7, O-11 — four confirmations). Session 131 is the
  fifth: the session's best result set carried `query_confident: false` and
  `low_confidence: true` on every item.
- **Most items carry `low_confidence: true` and scores band 0.55–0.85. That is normal.**
  Rank order is the signal.
- **Do not treat rank 1 as the answer.** Read several. Session 131's decisive find
  (`event-model.md`, which settled three open plan decisions) arrived at **rank 3** of a
  `find_related` call.
- **`find_related` verdicts** (`strong`/`moderate`/`weak`) come from edge structure;
  `moderate` is common even for genuinely close files.
<!-- /ref:ltg-usage-output-reading -->

---

## 5. Which tool answers which question

| Question | Tool |
|---|---|
| "Which files discuss THIS SUBJECT?" | `retrieve_context`, §2-shaped query |
| "Which files echo THIS FILE's claims / what should I have read before deciding?" | `find_related` (zero model calls) |
| "How exactly do these two files relate?" | `relate_files` — leave `with_summary=False`; `True` is the only call that invokes the local model |

The split is career-search's O-2. Session 131 is a clean instance of the second: `find_related`
on a plan's *predecessor* (`docs/plans/oficina-p2-evaluated-loop.md`) ranked an unread vision
doc third, and that doc pre-decided three open decisions in the plan being written.

---

## 6. What NOT to do

| Don't | Why |
|---|---|
| Read corpus scope off `corpus.yaml` | It understates the live index — §1 |
| Gate anything on `query_confident` / `low_confidence` | Five measurements say they track phrasing, not correctness — §4 |
| Conclude from an excerpt | Excerpts are live text at stored spans; they can misalign — §3 |
| Stop at the anchor block | Out-of-block material (parked watch-items, addenda) is invisible to the graph — §3 step 5 |
| Query with single keywords or quoted claim text | Career-search measured both to miss — §2 |
| Expect a file written this session to be findable | Index reflects the last refresh; corpus is git-tracked-only — §1 |
| Write a bare `ref:` HTML-comment marker in prose | `check-ref-integrity` counts it as a real definition → false duplicate/unclosed errors. Fence examples in code blocks (this repo hit it live while filing T-124) |
| Refresh while the GPU is busy | Competes with `ollama-bridge`; ask first |

---

## 7. Observations log (session 131, 2026-07-27)

One session is an anecdote. **Do not amend §1–§6 from a single row** — career-search's own
protocol, adopted here for the same reason.

| # | Observation | Implication (NOT yet acted on) |
|---|---|---|
| L-1 | **Live index contains 4 `docs/` subtrees the corpus config and frozen manifest do not** (`plans` 54 topics, `vision` 50, `findings` 22, `patterns` 20). Verified via `run-inspect.sh --list` against `corpus-manifest.yaml` at `e33fe88`. | Scope is unreadable from config (§1). Second-order: those files sit outside `--check`'s hash comparison, so their edits can never be reported stale. **Candidate task** — needs the engine's refresh/prune semantics checked before filing a claim about cause. |
| L-2 | The single best result set of the session reported `query_confident: false` with every item `low_confidence: true`. | 5th independent confirmation of career-search §4. The rule is now well-evidenced across two corpora. |
| L-3 | **Ranks 1/2/4/5 of that query were all bare `ref:KEY` marker excerpts** — no prose content at all. | The pointer loop (§3) is not a stylistic preference here; for anchor-dense corpora it is frequently the *only* usable mode. |
| L-4 | Reading only the anchor block would have missed a parked watch-item ~120 lines outside it, which was a live trigger on the work in hand. | §3 step 5. Anchors index what someone chose to anchor; decisions get parked in prose. |
| L-5 | `find_related` on a plan's predecessor surfaced the vision doc that pre-decided three of that plan's open decisions. Cost: zero model calls. | Strongest single result of the session, and the cheapest call. Supports promoting "run `find_related` on the predecessor before opening a new plan" to a rule — **after 2 more confirmations**. |
| L-6 | `focus` (`history` / `current` / `balanced`) is undocumented in career-search's guide and untested here — one query used `current`, confounding session 131's first framing comparison. | Open question, and likely to matter more here than there: this corpus is archive-heavy (97 of 162 manifest files are `archive`), so source-group reweighting has more to bite on. Design a clean test before drawing any rule. |

---

## 8. Where to read more

| Doc | What it holds |
|---|---|
| `~/workspaces/career-search/.claude/ltg-usage-guide.md` | **The battle-tested original** — four sessions of observations, refresh discipline, anchor mechanics |
| `docs/research/latent-topic-graph.md` | The concept and its smart-RAG lineage ([ref:concept-latent-topic-graph]) |
| `docs/plans/ltg-repo-split.md` | Engine/instance split ([ref:ltg-split-frozen-decisions]) — engine work happens in the sibling repo |
| `ltg/corpus.yaml` | Declared corpus **intent** — see §1 before trusting it as scope |
