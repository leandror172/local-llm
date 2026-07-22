# Documentation Staleness Report
**Date:** 2026-06-09  
**Scope:** Files read in this session — `.claude/index.md`, `.memories/QUICK.md`,
`.memories/KNOWLEDGE.md`, `retrieval/.memories/QUICK.md`, `retrieval/.memories/KNOWLEDGE.md`,
`.claude/session-context.md`  
**Method:** No additional file reads performed. Report is derived purely from the
content already loaded into context.

---

## 1. `retrieval/.memories/KNOWLEDGE.md` — `ref:ltg-phase0-decisions-index` table

**Staleness:** The embedded table still lists the embedding model as:
> "bge-m3 via Ollama (1024-dim dense)" — *Key reason: Ollama-native; +3-4 MTEB vs nomic; no torch install*

This is a Phase 0 decision that was **superseded by session 73** when the embedding model was
upgraded to `qwen3-embedding:8b` (4096-dim). The same file's `ref:ltg-m-p0b-probe` section
correctly documents the upgrade, so the file is internally contradictory: two sections in
the same KNOWLEDGE.md disagree on the embedding model.

**Impact:** An agent reading `ref:ltg-phase0-decisions-index` gets wrong current state.  
**Fix needed:** Update the table row to `qwen3-embedding:8b via Ollama (4096-dim dense)`.

---

## 2. `retrieval/.memories/QUICK.md` — Status block stops at Session 81

**Staleness:** The status block ends with:
> "Session 81 (2026-06-01): Phase 3 anchor-integration DISCOVERY started (NOT frozen)."

Missing from retrieval's QUICK.md:
- **Sessions 78–80** — extractor retrofit complete: `routing.py`, `schemas.py`,
  `sweep_extractors.py`, 148 tests green, parity verified end-to-end. This is a
  **significant implementation milestone** and is absent.
- **Session 82** — Phase 3 anchor decisions **FROZEN** (all 7 decisions settled, D1–D7).
  The QUICK.md still says "D2/D5/D6/D7 OPEN" but those were closed in session 82.

**Impact:** An agent starting a Phase 3 session from retrieval/.memories/QUICK.md
believes Phase 3 decisions are unresolved and may re-litigate closed choices.  
**Fix needed:** Add session 78–80 extractor retrofit entry; update session 81 entry to
note Phase 3 is now frozen (session 82).

---

## 3. `retrieval/.memories/QUICK.md` — "What Lives Here" directory listing

**Staleness:** The directory tree shows:
```
retrieval/
  extract_topics.py
  run-vram-probe.sh
  viz_sweep.py
  ltg-rater.template.html
  spike-results.md
  prompts/extract.txt
  runs/
```

This reflects the Phase 1 spike state. It's missing every file added in Phase 2 and the
extractor retrofit:
- `config.yaml`, `model_client.py`, `embed.py`, `store.py`, `ltg_inspect.py` (Phase 2)
- `routing.py`, `schemas.py`, `sweep_extractors.py` (retrofit, sessions 78–80)
- `run-embed.sh`, `run-store.sh`, `run-inspect.sh`, `run-extract-topics.sh`,
  `run-sweep-extractors.sh`, `run-preflight.sh`, `preflight.sh` (wrappers, Phase 2+)
- `tests/` (8 test files, 148 tests)
- `probes/` (acceptance probe outputs)

**Impact:** The listing is 6+ months stale in terms of what actually exists.  
**Fix needed:** Full directory tree refresh.

---

## 4. `.memories/KNOWLEDGE.md` — Model Landscape "LTG Phase 2 implications" section

**Staleness:** The implication bullets at the bottom of the Model Landscape Update section say:
> "Start with `qwen3-embedding:8b` not `bge-m3` — already available, meaningfully better"  
> "VRAM: re-run co-residence probe with qwen3:14b"  
> "The extractor routing decision needs re-evaluation after benchmarking qwen3.6-coder:14b"  
> "Before starting LTG Phase 2, pull and validate the two P0 swaps."

All four bullets are now stale:
- The embedding upgrade was done (session 73). bge-m3 is gone.
- The VRAM probe for qwen3-embedding:8b was completed (session 73, WARN verdict, sequential constraint unchanged).
- M-P0a (qwen3.6-coder:14b) was closed with **NO SWAP** in session 74 — the tag is a phantom (doesn't exist on Ollama); qwen2.5-coder:14b remains primary coder.
- LTG Phase 2 is **complete** (session 72), well past the "before starting" gate.

**Impact:** These bullets read as forward-looking action items but every one is resolved.
An agent could incorrectly conclude there is pending probe/benchmark work before Phase 2.  
**Fix needed:** Convert to past-tense findings or remove the implication block entirely
and replace with a "Resolved" note pointing to `ref:ltg-m-p0b-probe` + `ref:ltg-phase2-findings`.

---

## 5. `.memories/QUICK.md` (root) — "Open deferred tasks" — qwen3.6-coder:14b note

**Staleness:** The open deferred tasks list contains:
> "Qwen3-Coder-Next feasibility (superseded — qwen3.6-coder:14b is the near-term upgrade; 80B MoE still deferred)"

This note was written before M-P0a was resolved. Session 74 confirmed that `qwen3.6-coder:14b`
is a **phantom tag** (does not exist on Ollama) and the benchmark closed with NO SWAP —
`qwen2.5-coder:14b` remains the primary coder. The deferred task was closed, not superseded
by a viable alternative.

**Impact:** Low — the root QUICK.md session entries (lines 14, 18, etc.) correctly document
M-P0a's closure. But the deferred-tasks list contradicts them.  
**Fix needed:** Change wording to "(closed session 74 — NO SWAP; qwen3.6-coder:14b phantom tag on Ollama; qwen2.5-coder:14b confirmed primary)".

---

## 6. Portfolio docs — Persona count (28 vs 50)

**Staleness:** The portfolio documents (`docs/portfolio/portfolio.md`,
`docs/portfolio/engineer-profile.md`) were last substantively updated April 2026 and
state "28 active personas." The registry (`personas/registry.yaml`) currently contains
**50 active personas** across 12 base models — a 79% increase since the docs were written.

**Impact:** High if sharing with recruiters or adding to a portfolio site. A 28-persona
claim is verifiably wrong against the live registry.  
**Fix needed:** Update the persona count and the list of covered base models in both files.

---

## 7. `retrieval/.memories/KNOWLEDGE.md` — `ref:ltg-vram-probe` section (minor)

**Staleness:** The section title is:
> "VRAM Co-Residence: qwen3:14b + bge-m3 (2026-05-20, session 61)"

The section content correctly documents the bge-m3 probe and notes the sequential
constraint. The new probe (`ref:ltg-m-p0b-probe`) is a separate section directly below
it, documenting the qwen3-embedding:8b upgrade. The two sections coexist correctly.

However, the `ref:ltg-vram-probe` section still refers to bge-m3 as the model being
probed, while the "Fallback" note says "drop to `mxbai-embed-large`." Since bge-m3 was
itself the fallback from qwen3-embedding:8b, the fallback chain note is now slightly
misleading: bge-m3 is the intermediate, not the primary.

**Impact:** Very low — historical record is accurate as of session 61; the upgrade is
documented separately. Not urgent.

---

## 8. `.claude/index.md` — `ref:bash-wrappers` table (minor gap)

**Staleness:** The bash-wrappers table in `.claude/index.md` correctly lists most Phase 2
run scripts. It notes `run-handoff.sh` lives in `overlays/session-tracking/files/handoff/`.
One small gap: `retrieval/run-sweep-extractors.sh` (added sessions 78–80, extractor retrofit)
is in the table, but `retrieval/sweep_extractors.py` is not listed in the Python libs
section below it.

**Impact:** Minimal — the wrapper is documented; the underlying library omission is cosmetic.

---

## Summary Table

| File | Issue | Severity |
|------|-------|----------|
| `retrieval/.memories/KNOWLEDGE.md` | Phase 0 embedding model still shows bge-m3 (internal contradiction) | **High** |
| `retrieval/.memories/QUICK.md` | Status block missing sessions 78–82; Phase 3 shown as open when frozen | **High** |
| `retrieval/.memories/QUICK.md` | "What Lives Here" directory listing is Phase-1-era only | **High** |
| `.memories/KNOWLEDGE.md` | LTG Phase 2 implications still framed as future action items (all resolved) | **Medium** |
| `.memories/QUICK.md` | Deferred task note says qwen3.6-coder:14b is near-term upgrade (phantom tag, NO SWAP) | **Low** |
| `docs/portfolio/portfolio.md` + `engineer-profile.md` | Persona count 28 vs actual 50 | **High** (if sharing externally) |
| `retrieval/.memories/KNOWLEDGE.md` | bge-m3 fallback chain note slightly misleading post-upgrade | **Very Low** |
| `.claude/index.md` | `sweep_extractors.py` missing from Python libs section | **Very Low** |
