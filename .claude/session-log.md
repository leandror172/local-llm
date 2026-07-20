# Session Log

**Current Layer:** "Layer 5+ — oficina (P2 widening: Go Axis A + write-model M2)"
**Current Session:** 2026-07-20 — Session 124: "founding problem recovered (T-102) + Go-widening Phase 1 + write-model M2 decided (T-104) — PR #79"

---
## 2026-07-20 - Session 124: "founding problem recovered (T-102) + Go-widening Phase 1 + write-model M2 decided (T-104) — PR #79"

### Context

Started from a review of oficina's capabilities and the user's question about whether all local codegen goes through the async path. That unwound into recovering oficina's *founding* problem (multi-session GPU contention), then into starting the P2 kind/language widening, where reading the loop surfaced a write-model design flaw. One branch `docs/t102-multi-session-contention`, PR #79.

### What Was Done

- **T-102 — founding problem recovered:** multi-session GPU contention (N concurrent Claude sessions; sync times out under contention) was named session 42, downgraded 43, then dropped in the T-21→T-88 supersession (clients reframed sessions→products). New record `docs/ideas/multi-session-contention.md`; captured the failure mode + measurement caveats + busy-check MVP; amended every contradiction found (elevator prose, `Exhausted`/`Delivered`, `validate-code.py` docstring) as annotations; advisor-reviewed (two overstated claims corrected before commit).
- **T-92 Axis A (Go widening) groundwork:** R1/R3/R4 settled (R3 `go build ./...` in a git worktree confirmed by throwaway experiment); 5-phase build plan; language-widening design notes (what-varies table, value-object-pack-over-ABC, two warnings).
- **T-92 Axis A Phase 1 SHIPPED (tested):** `intake.py` gains `deliverable.language` (declared, else inferred from ext) + two kind-scoped rejection rules mirroring the acceptance pair. mcp-server suite **279 green, zero existing tests touched**.
- **T-104 write-model finding + decision:** `loop.py:263` overwrites the whole target file → `kind:function` is file-granular; root cause = the loop reimplements what it should compose (dropped `patch_file`). Built + ran a **pre-registered 3-arm benchmark** (108 gens, `benchmarks/lib/writemodel_*`). **M2 (edit) DECIDED = code-anchored**; full report `docs/findings/oficina-write-model-benchmark-2026-07-18.md`.
- **PR #79 opened** (9 commits, 25 files). Filed T-103 (timeout config mismatch, found while measuring).

### Decisions Made

- **Founding problem is multi-session contention (T-102).** T-89 is **scope-limited, not reopened** (it answered interactive-vs-*batch*; interactive-vs-*interactive* was never posed). The gate (T-88) gains a wait-tolerance axis (**G-D7**) and its MVP is T-21's busy-check, not the scheduler (**G-D8**). Triggers were unfalsifiable (user manually serializes; `calls.jsonl` only sees the bridge).
- **R1 = declared `deliverable.language`, infer-from-ext as default** (revisit when a non-author submits specs). **R3 = in-worktree `go build ./...`**. **R4 = compile self-attributes; test stage uses `go test -json`** via the Package field. Go category rule is flat.
- **M2 (edit) = code-anchored** (`LanguagePack.locate_unit` → `patch_file`), decided on **cost/timeout-safety** (size-invariant 25 tok vs whole-file 40→134→310 — whole-file on large files is what blew the 120s ceiling twice this session), **NOT correctness** (benchmark null — uniform-filler corpus was whole-file's best case; regression trap never sprang). Re-run declined: the open axis isn't load-bearing. M1 (greenfield) = compose `output_file`.
- **Principle: oficina composes the ollama-bridge tools, it does not reimplement them.** Sibling of T-95 (transport) and the T-102 busy-check — the re-authored local version is always the cruder one.

### Next

- **Build the edit kinds on M2** — `LanguagePack.locate_unit` (Python ast — the benchmark's `locate_function` is a seed; Go `go/parser`); loop composes `patch_file` for edit kinds; C0 baseline flips to target-present.
- **Axis A Go read-side (Phase 3)** — `_parse_gotest`, compile-in-worktree, flat category rule; the honest oficina loop dogfood target (substantial + Python).
- **PR #79 review/merge.** Standing: T-102 gate busy-check (G-D8), T-103 timeout config, T-93 measurement (unblocked), T-86 distribution.

### Gotchas

- **Delegating a large-context edit to the 14B timed out at 120s TWICE** (cold, then a real >120s generation on ~650-line context). That's T-103 (declared `OLLAMA_TIMEOUT=120` vs the effective ~600s ceiling; `.bashrc` vs `.claude.json` disagree). The retry-protocol fix worked: **split + shrink** (write trivial parts directly, tiny inline example). Async can't rescue it (T-104: kinds overwrite existing files).
- **Do not read the benchmark's green table as "whole-file is safe."** It's a coverage null — the corpus's uniform `op_k` filler is whole-file's *best case* and never sprang the regression trap. Only the cost axis discriminated.
