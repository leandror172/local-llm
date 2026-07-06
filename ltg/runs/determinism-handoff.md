# Determinism Re-Run — Session Handoff

**Created:** 2026-04-27 (mid-session, GPU was busy so Step 2 deferred)
**Branch:** `feature/ltg-phase1-scoring-and-notes` (PR already open)
**Read this file first.** Then load further context only as triggers below say.

---

## What this task is

Re-run `qwen3:14b` 5× on `docs/research/smart-rag-index.md` to test whether the off-by-one drift on the 7 cross-cutting-pattern bullets (lines 22-28) reproduces. Result branches the routing hypothesis 3 ways. Originally observed 4/7 accuracy in the Phase 1 sweep (`retrieval/runs/20260416-181839.jsonl`); question is "model property" vs "sampling luck."

## Where you are in the 5-step plan

- [x] **Step 1 — Pre-flight.** Ground truth, original-sweep observation, pre-committed decision rule, and analysis template written to `retrieval/runs/determinism-ground-truth.md`. **Read this file** — it has everything needed to interpret the runs.
- [ ] **Step 2 — Execute the runs.** Single command:
  ```
  python3 retrieval/extract_topics.py \
      --model qwen3:14b \
      --file docs/research/smart-rag-index.md \
      --runs 5
  ```
  Produces `retrieval/runs/<new-tag>.jsonl` (5 records) + `<new-tag>-summary.txt` + `<new-tag>-manual-rubric.md`. ~3 min on free GPU. Same params as original sweep (`temperature=0.1`, `think=False`, `num_ctx=8192`) — the runner enforces them.
- [ ] **Step 3 — Analysis.** Read 5 records, fill in the analysis template at the bottom of `determinism-ground-truth.md`. Match bullets by content (not by topic-name string) — see ground-truth file for why.
- [ ] **Step 4 — Decision + write-up.** Apply the pre-committed rule → pick Branch A / B / C. Append a new ref block to `retrieval/spike-rater-notes.md` (suggest `ref:ltg-phase1-determinism-smart-rag-index`). If Branch B or C wins, also revise `ref:ltg-phase1-routing-hypothesis` per the conditional drafts in `ref:ltg-phase1-pending-revisions`.
- [ ] **Step 5 — Commit.** Fold into existing PR for `feature/ltg-phase1-scoring-and-notes`. Suggested message: `docs(ltg-phase1): determinism re-run on smart-rag-index.md (qwen3:14b, 5 runs)`.

## Note for the evaluating Claude

If you'll be doing **subjective evaluation of model output** (e.g. judging topic-name quality, description boilerplate, boundary-vs-bleed calls — like sessions 54-57 did with the rubric scoring), **consider spawning an Opus subagent** for that evaluation pass. The Phase 1 spike-results scoring was Opus-graded; using a weaker model for the same task introduces a methodology break in the two-rater reconciliation chain. For *this* determinism task specifically, the analysis is mechanical (line-number matching against the ground-truth table) so this note is more relevant for the prompt-iteration experiment that comes after, but flagging now so it's not forgotten.

---

## Triggers — load context only when needed

These are the only files/refs you should need. Each line: **trigger condition → what to read**. Do not preload; the point is to keep context lean.

### Always-load (small, immediately needed)

- `retrieval/runs/determinism-ground-truth.md` — ground truth + decision rule + analysis template. **~120 lines, read on session start.**

### Load when you start Step 2

- `retrieval/extract_topics.py` — only if the runner errors or you suspect param drift. The runner's CORPUS / MODEL_EXTRA_PARAMS / OLLAMA_OPTIONS sections lock the sweep params. Otherwise no read needed.

### Load when you start Step 3 (analysis)

- The new run JSONL `retrieval/runs/<new-tag>.jsonl` produced by Step 2.
- For each of the 5 records, read only `parsed_topics` — the rest is metadata.

### Load when you start Step 4 (write-up)

- `.claude/tools/ref-lookup.sh ltg-phase1-routing-hypothesis` — current hypothesis text; you'll be appending or revising depending on branch.
- `.claude/tools/ref-lookup.sh ltg-phase1-pending-revisions` — has the pre-drafted Branch A/B/C revision text. **Use these drafts; don't rewrite from scratch.**
- `.claude/tools/ref-lookup.sh ltg-phase1-insights` — finding #7 is the original observation; cite when adding the new ref block.
- `retrieval/spike-rater-notes.md` — append the new ref block here. Read only the file's existing ref-block boundaries (search for `<!-- ref:ltg-phase1-` markers) so the append matches the existing structure.

### Load only if context is unclear

- `.claude/tools/ref-lookup.sh ltg-phase1-claude-rater-notes` — per-cell scoring rationale from session 57. The smart-rag-index.md row gives full context on why qwen3:8b's 7/7 there is interesting.
- `.claude/tools/ref-lookup.sh ltg-extractor` — Phase 0 decision frame for the extractor choice; useful if Branch C requires a formal decision-replacement.
- `docs/plans/2026-04-13-latent-topic-graph-implementation.md` — only if you've forgotten what Phase 1 / Phase 2 are. The plan ref keys `ltg-plan-phase-1` and `ltg-plan-phase-2` cover the same content with `ref-lookup.sh`.
- `.claude/session-log.md` (tail) — only if you need full session 54-57 history beyond what the refs above contain.

### Do NOT preload (would blow up context)

- `retrieval/runs/20260416-181839.jsonl` — the original sweep. 32 records, 288 KB rendered. The relevant single observation is already extracted into `determinism-ground-truth.md`. Never read this whole file in this session.
- `retrieval/runs/20260416-181839.html` — even larger. The viz is for human scoring.
- `retrieval/spike-results.md` — full Phase 1 results; the relevant findings are already in the refs above.
- `retrieval/ltg-rater.template.html` — 1600-line UI template, irrelevant to this task.
- `docs/research/smart-rag-index.md` — already read in pre-flight; ground truth captured. Re-read only if you doubt the line numbers in the ground-truth table.

---

## Quick orientation if the user asks "where are we"

1. LTG Phase 1 extractor spike completed (8/8 files scored by Claude in sessions 54-57).
2. User is doing parallel HTML-viz scoring for two-rater reconciliation; that gates final extractor freeze.
3. This task is **gating evidence** for the routing hypothesis (`ref:ltg-phase1-routing-hypothesis`) — specifically the third arm question raised by finding #7 (`ref:ltg-phase1-insights`). Cheap to run, high-leverage.
4. Phase 2 (embedding + storage) is blocked on extractor freeze, which is blocked on (a) two-rater reconciliation and (b) this determinism check + the deferred prompt-iteration experiment.

## Constraints to remember

- **GPU-shared with the user** — check before launching `extract_topics.py`. If unsure, ask.
- **Never read the original sweep JSONL/HTML wholesale** — see do-not-preload list. The cost is ~10-50K tokens for a single observation already extracted.
- **Pre-committed decision rule is binding** — see `determinism-ground-truth.md`. Do not edit the threshold table after seeing results.
- **Match topics by content, not by name string** — qwen3:14b and qwen3:8b produced different names for the same bullets in the original sweep.
- **Cozempic context-window bug** — `cozempic` reports 1.00M ceiling but actual is 200K. Multiply reported % by 5×.
