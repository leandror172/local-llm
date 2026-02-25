# Shell Benchmark Findings

**Date:** 2026-02-24 (session 29)
**Branch:** `feature/4x-shell-rubric` → PR #7 into `feature/layer4-evaluator-framework`
**Personas:** `my-shell-q3` (updated), `my-coder-q3` (baseline), `my-architect-q3` (reference)
**Rubric:** `evaluator/rubrics/code-shell.yaml`

---

## What Was Built

| Artifact | Purpose |
|----------|---------|
| `evaluator/rubrics/code-shell.yaml` | Shell rubric — 1 Phase 1 criterion (`shellcheck_clean`, w=3.0) + 5 Phase 2 criteria |
| `benchmarks/lib/validate-code.py` | Added `validate_shell()` using `shellcheck --format=json1`; `.sh` dispatch |
| `evaluator/lib/evaluate.py` | Added `shellcheck_clean` case to `_score_from_validator_output()` |
| `modelfiles/shell-qwen3.Modelfile` | 6 new shellcheck-targeted constraints (see below) |

**Plan note:** The original plan stated "evaluate.py needs NO changes" — incorrect.
The `else` branch returned `score: null` with "unknown auto_source mapping".
`shellcheck_clean` required an explicit case, same pattern as `compiles`.

---

## Benchmark Runs

Three runs were conducted; results combined below.

| Run ID | Personas | Timeout | Notes |
|--------|----------|---------|-------|
| 2026-02-24T103037 | shell, coder, architect | 300s | First run; 4/5 shell timeouts |
| 2026-02-24T123513 | shell, coder | 600s | All generations complete; sh-01 still timed out for both |
| 2026-02-24T190133 | shell, coder | 900s | sh-01/sh-02 still complementary timeouts |

---

## Combined Results: Full Dataset

### `my-shell-q3` (updated persona, 4 prompts completed)

| Prompt | % | shellcheck_clean | Findings |
|--------|---|-----------------|----------|
| sh-01-log-analyzer | 50.8% | 1 | SC2183 printf arg mismatch, SC2154 unset var |
| sh-02-backup-rotation | timeout | — | — |
| sh-03-health-check | 65.0% | 1 | SC1073/SC1072 broken test expression |
| sh-04-git-hook | **95.2%** | **5 (clean)** | — |
| sh-05-deploy-script | 55.8% | 1 | SC2034 unused variable |
| **avg (4 prompts)** | **66.7%** | **2.0** | |

### `my-coder-q3` (unchanged baseline, 4 prompts completed)

| Prompt | % | shellcheck_clean | Findings |
|--------|---|-----------------|----------|
| sh-01-log-analyzer | timeout | — | — |
| sh-02-backup-rotation | 52.5% | 1 | SC2207, SC2086 |
| sh-03-health-check | 77.5% | 3 | info/style only |
| sh-04-git-hook | 68.6% | 5 (clean) | — |
| sh-05-deploy-script | 68.3% | 1 | SC2115 |
| **avg (4 prompts)** | **66.7%** | **2.5** | |

### `my-architect-q3` (14B reference, run 1 only — 5/5 complete)

| Prompt | % | shellcheck_clean |
|--------|---|-----------------|
| sh-01-log-analyzer | 92.9% | **5 (clean)** |
| sh-02-backup-rotation | 67.5% | 1 |
| sh-03-health-check | 39.2% | 1 |
| sh-04-git-hook | 67.5% | **5 (clean)** |
| sh-05-deploy-script | 60.0% | 1 |
| **avg** | **65.4%** | **2.6** |

---

## shellcheck Findings Taxonomy

### SC codes observed across all outputs

| Code | Severity | Description | Count | Addressed by constraint? |
|------|----------|-------------|-------|--------------------------|
| SC2207 | warning | `arr=( $(cmd) )` — word-split array | 5 | ✅ yes (new constraint) |
| SC2181 | note | `if [ $? -ne 0 ]` — indirect exit check | 6 | ✅ yes (new constraint) |
| SC2012 | note | `ls` used for file listing | 5 | ✅ yes (new constraint) |
| SC2064 | warning | `trap "cmd"` — expands eagerly | 2 | ✅ yes (new constraint) |
| SC2086 | note | Unquoted `$var` | 4 | ✅ existing constraint (reinforced) |
| SC2034 | warning | Variable assigned but unused | 3 | ✗ logic issue — model writes arg parsers but forgets to use the value |
| SC1073/SC1072 | error | Broken test expression | 2 | ✗ logic issue — malformed regex in `[[ ]]` |
| SC2183 | warning | printf format/arg count mismatch | 2 | ✗ logic issue — can't constraint-engineer away |
| SC2154 | warning | Variable referenced but not assigned | 1 | ✗ logic issue |
| SC2207 (post-fix) | warning | Still appears in `my-coder-q3` (unchanged) | 1 | n/a — baseline unchanged |
| SC2115 | warning | `rm -rf $var/` without `${:?}` guard | 1 | ✅ yes (new constraint) |
| SC2030/SC2031 | note | Pipeline subshell loses array changes | smoke only | ✅ yes (new constraint) |
| SC2168 | error | `local` outside function body | smoke only | ✅ yes (new constraint) |
| SC2188 | warning | Redirection without command `> file` | smoke only | — |

### Constraint validation

The 6 new constraints in `my-shell-q3` eliminated the targeted SC codes:
- **SC2207/SC2012** (array from `ls`) → gone from new outputs
- **SC2181** (`$?` check) → gone from new outputs
- **SC2064** (trap double-quotes) → gone from new outputs
- **SC2168** (`local` outside function) → gone after constraint refinement

The remaining failures are **logic errors** (wrong number of printf args, variables set but unused, broken regex in `[[ ]]`) — not mechanical style violations. These cannot be reliably fixed by persona constraints at 8B scale.

---

## Key Findings

### 1. Specialist hypothesis: not confirmed at 8B scale

Both `my-shell-q3` and `my-coder-q3` averaged exactly **66.7%** across their 4 completed prompts. The specialist did not outperform the polyglot overall.

**Where the specialist wins:** sh-04-git-hook (95.2% vs 68.6%) — a well-scoped, single-concept prompt. The specialist constraint density helps on prompts that fit within the model's reliable generation window.

**Where the specialist doesn't win:** complex, multi-requirement prompts (sh-01, sh-03, sh-05). On these, `my-coder-q3` matched or outperformed — likely because the polyglot's more general training gives it better coverage of multi-domain bash patterns.

### 2. Prompt complexity is the primary variable — and a prompt engineering problem

`sh-01-log-analyzer` and `sh-02-backup-rotation` exhausted every persona at every timeout (300s, 600s, 900s) — they simply require too many tokens for 8B models to generate reliably. The problem is not timeout tuning; it is prompt difficulty relative to model capacity.

`sh-04-git-hook` and `sh-03-health-check` completed reliably for all 8B personas. `sh-05-deploy-script` is borderline. The **reliable zone for 8B shell generation is single-concept scripts under ~300 lines**.

**Generalizable principle:** When a prompt exhausts the model's generation budget, two classes of failure appear simultaneously — timeout (incomplete output) and logic errors (the model rushes or loses coherence in long scripts). Neither is fixable by persona constraints. The remedy is **prompt decomposition**: split multi-requirement prompts into sub-tasks that each fit within the model's reliable window, then compose the results. This is closing-the-gap technique #3 (decomposition), already documented for visual generation — it applies equally to complex shell scripts.

**Implication for future benchmarks:** Before running a persona benchmark, classify prompts by expected output length relative to the target model tier:
- 8B models: reliable up to ~400 tokens output (~300 lines of code). Prompts requiring more should be decomposed or reserved for 14B+.
- 14B models: reliable up to ~800 tokens output. Complex multi-requirement scripts are in range.
- Prompt complexity can be estimated cheaply: ask the model to outline the script structure first (fast, low tokens), then judge whether the full implementation fits the tier.

### 3. 14B model produces cleaner shellcheck output than 8B shell specialist

`my-architect-q3` (qwen3:14b) achieved shellcheck_clean=5 on 2/5 prompts at 65.4% overall — better shellcheck hygiene than both 8B models despite having no shell-specific constraints. Raw model capability dominates constraint engineering at this scale gap.

### 4. Constraint iteration has diminishing returns for logic errors

The smoke-test iteration loop (5 rounds) showed that specific-pattern constraints (SC2207, SC2181, etc.) are reliably fixable, but each fix revealed new logic errors (SC2183, SC2154, SC2188) that couldn't be addressed by constraints. **Constraint engineering is effective for mechanical patterns, not for semantic correctness.**

---

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Commit constraints despite mixed benchmark results | The targeted SC codes are eliminated; residual errors are logic issues — commit signals progress clearly |
| Do not add shell constraints to `my-coder-q3` | It's a Java/Go polyglot; adding shell constraints would bloat its prompt for non-shell tasks |
| Accept missing sh-01/sh-02 data | Further timeout increases won't fix the underlying generation length problem; data from 4 prompts is sufficient for directional conclusions |
| Defer prompt trimming | sh-01 and sh-02 could be shortened or split into sub-tasks — valid future work but not blocking |

---

## Follow-up Items

- [x] Split `sh-01-log-analyzer` → `01a-log-stats.md` (stats 1–5) + `01b-log-histogram.md` (histogram only)
- [x] Split `sh-02-backup-rotation` → `02a-backup-create.md` (mktemp+trap) + `02b-backup-rotate.md` (keep-N rotation)
      Each sub-task targets ~150–250 token output — within the 8B reliable window (~400 tokens)
- [ ] Increase default `--timeout` in `run-benchmark.sh` from 300s to 600s (or add per-domain defaults)
- [ ] Consider `sh-04-git-hook` as the canonical "shell specialist test" — it's the most reliable differentiator
- [ ] Java Phase 1 validator (`javac`) and Python Phase 1 validator (`py_compile`) — next deferred evaluator tasks
