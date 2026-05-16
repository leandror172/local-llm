# Verdict Numeric Migration — Session Report

**Date:** 2026-05-16  
**Branch:** `verdict-numeric-migration` across 4 repos  
**Scope:** Replace `ACCEPTED`/`IMPROVED`/`REJECTED` string verdicts with integers `0`/`1`/`2` everywhere they appear as protocol tokens

---

## Work Done

### Phase 1 — Capture hooks
The load-bearing pair: `ollama-post-tool.py` (template prompt) and `verdict-capture.py` (regex + record constructor). These had to change together because they are a matched producer/consumer pair — the template instructs Claude what to write, the regex parses what Claude wrote.

**Changes:**
- Template: `ACCEPTED | IMPROVED | REJECTED` → `0 | 1 | 2 ← 0=rejected 1=improved 2=accepted`
- Regex capture group: `(ACCEPTED|IMPROVED|REJECTED)` → `([012])`
- Record constructor: `verdict.upper()` → `int(verdict)`
- Docstring example updated

**Verification:** 4/4 steps passed — regex unit test (PASS), end-to-end fixture with isolated `$HOME` (PASS), negative check proving old format cleanly rejected (PASS), syntax gate (PASS).

### Phase 2 — Data migration
`calls.jsonl` (225 lines, 40 verdict records) and `compare-runs.jsonl` (2 lines, 4 verdict fields). Migration scripts written to `/tmp/vmig/` for single-authorization reuse. Both scripts idempotent.

**Pre-migration distribution:** `IMPROVED: 28, REJECTED: 7, ACCEPTED: 5`  
**Post-migration:** `{1: 28, 0: 7, 2: 5}` — distribution identical, type changed  
**Verification:** 5/5 checks — count parity, distribution parity, type check (all int), JSON validity, idempotency, non-verdict byte-diff (PASS on all).

### Phase 3 — Analysis tools
`ollama-stats.py` and `ollama-verdicts.py`: iteration order `['ACCEPTED','IMPROVED','REJECTED']` → `[2, 1, 0]`, label maps added for display, CLI filter updated to accept digit strings and cast to int, `find_patterns` filter `== 'REJECTED'` → `== 0`.

### Phase 4 — Benchmark scripts
`compare-models.py`, `record-verdicts.py`, `run-compare-models.sh`. Three `verdict_map` occurrences across two files (per plan's Note C). Interactive prompts updated from `[A]/[I]/[R]` → `[2]/[1]/[0]`. Error fallback `"REJECTED"` → `0`. Non-interactive path verified programmatically; invalid input rejection verified.

**Out-of-scope discovery:** `benchmarks/.memories/QUICK.md` and `KNOWLEDGE.md` — updated with user approval.

### Phase 5 — llm-repo documentation (6 files)
`CLAUDE.md`, `docs/scaffolding-template.md`, `overlays/ollama-scaffolding/templates/local-model-retry-patterns.md.tmpl`, `overlays/ollama-scaffolding/sections/claude-md-ollama-rules.md`, `.claude/session-context.md` (decision tree + model quality descriptor at line 111). 14 individual edits. Canonical legend line placed in each doc.

### Phase 6 — Three downstream repos
`expenses`, `web-research`, `career-search`. Pre-step diff gate confirmed all three overlay files byte-identical — enabling a clean `cp` sync. `web-research/CLAUDE.md` had 4 hits including model-quality descriptors (`ACCEPTED with context files, IMPROVED without` → `2 (accepted)/1 (improved)`). All three repos branched, edited, committed with only verdict files staged — `web-research`'s 5 in-progress uncommitted files left untouched.

### Phase 7 — Cross-session memory
`feedback_ollama_retry_protocol.md` (frontmatter description + 4 body hits), `feedback_ollama_workflow.md` (2 hits), `MEMORY.md` index line. First-use parenthetical label applied (`0 (rejected)`), subsequent uses bare `0`.

### Phase 8 — Index + extended cleanup
Plan file indexed in `.claude/index.md`. Global leftover scan surfaced 7 additional active-file hits not in the original plan: `OLLAMA-ANALYSIS-README.md`, `.memories/KNOWLEDGE.md` (root), `.memories/QUICK.md`, `evaluator/.memories/KNOWLEDGE.md`, `README.md` (3 hits), `client.py` code comment — all updated with user approval.

---

## Results

| Metric | Value |
|---|---|
| Repos touched | 4 (`llm`, `expenses`, `web-research`, `career-search`) |
| Files changed (llm) | 24 |
| Net diff (llm) | +216 / −119 lines |
| Commits (llm) | 7 |
| Commits (downstream) | 3 (one per repo) |
| Data records migrated | 40 verdict records in `calls.jsonl` + 4 in `compare-runs.jsonl` |
| Distribution preserved | 5/28/7 → `{2:5, 1:28, 0:7}` ✓ |
| Canonical legend occurrences | 11 — all byte-identical |
| Leftover scan result | Zero hits in active files |
| Interactive path | Flagged for manual user verification (Claude cannot test `input()`) |

---

## Insights

**The fixture test `$HOME` trick.** `CALLS_LOG` in both hooks is `Path.home() / ...` — a hardcoded module constant. There is no env-var override. The only clean isolation strategy is `HOME=$(mktemp -d)` so Python's `Path.home()` resolves to a throwaway directory, leaving the real log untouched. This pattern generalises to any Python tool that hardcodes a path relative to `$HOME`.

**Three `verdict_map` locations (Note C was right).** The plan flagged this explicitly, and it was the right call. `compare-models.py` had one occurrence (inside `collect_verdict`), `record-verdicts.py` had two (in `apply_verdicts_noninteractive` and `collect_verdict`). Missing either of the two in `record-verdicts.py` would have left a silent mixed-type window in the non-interactive path.

**`re.IGNORECASE` stays.** The compiled regex retains `re.IGNORECASE` even though digits are case-insensitive. Removing it would shrink the diff by one word but make the change larger than required. Minimal-diff discipline is a real constraint, not just a preference — in a migration touching 24 files, every gratuitous change is noise that makes review harder.

**The `cp` strategy for overlays works cleanly because the template has no `{{ }}` vars.** The `local-model-retry-patterns.md.tmpl` is named `.tmpl` but contains no template variables — it renders identically to its source. This means `cp .tmpl overlay.md` is lossless and drift-free. If vars were ever added, the copy strategy would need to become a render step.

**Memory file `description:` is the retrieval hook, not the body.** The frontmatter `description:` in memory files is what future sessions read when scanning `MEMORY.md` to decide relevance. If the description still said "After a REJECTED Ollama verdict…" but the body used integers, sessions loading the memory would see conflicting signals. Updating both is not optional.

---

## Observations

**Scope creep was real and legitimate.** The plan covered 8 phases. The actual migration required extending into `benchmarks/.memories/`, `README.md`, `.memories/` (root and evaluator), `OLLAMA-ANALYSIS-README.md`, and `client.py` — none of which were in the plan. These were surfaced rather than unilaterally edited, and the user approved each. The plan's "stop and ask" rule functioned correctly.

**`web-research` had 5 uncommitted files that needed to be left in place.** Creating the feature branch carried those changes along (correct Git semantics), but staging only the verdict-migration files and committing separately preserved the in-progress state without stashing or losing work. This is the right pattern for feature branches on top of dirty working trees.

**The `compare-runs.jsonl` was gitignored.** It's a data file, like `calls.jsonl`. This means Phase 2.3's migration was a filesystem-only operation with no commit. Both files now live outside git tracking — the backup files (`*.bak-verdict-migration-20260516`) serve as the recovery point until manually removed.

**`docs/portfolio/`, `docs/research/`, `docs/ideas/`, and `.claude/plan-v2.md` still use string verdicts.** These are intentionally not migrated — they're historical prose or background context, not runtime-read protocol files. They were excluded from the leftover scan by design. A future decision to update them (e.g., when the portfolio is next revised) can reference the migration plan for the canonical mapping.

**The `2 > 1 > 0` ordering aligns with DPO training-signal strength.** This was a deliberate decision captured in Note H of the plan. The ordering means `accepted > improved > rejected` numerically, which maps cleanly onto DPO preference pair labelling: `chosen = 2`, `rejected = 0`. Phrases like "the strongest training signal is verdict 2" now read naturally without requiring a legend to decode.

---

## Remaining Items

- **Manual verification needed:** Interactive `input()` paths in `compare-models.py` and `record-verdicts.py` — run `run-compare-models.sh` in a real terminal to confirm `(0/1/2)` prompt appears and accepts a digit keystroke.
- **Backups to remove (when confident):** `~/.local/share/ollama-bridge/calls.jsonl.bak-verdict-migration-20260516`
- **Not migrated (intentional):** `docs/portfolio/`, `docs/research/`, `docs/ideas/`, `.claude/plan-v2.md` — historical/background prose.
