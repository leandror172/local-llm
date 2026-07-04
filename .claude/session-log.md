# Session Log

**Current Layer:** Layer 5 — Expense Classifier
**Current Session:** 2026-07-04 — Session 106: T-33 repo-split discovery + model-registry decision capture (T-76/T-77, S-D1–S-D7)

---
## 2026-07-04 - Session 106: T-33 repo-split discovery + model-registry decision capture (T-76/T-77, S-D1–S-D7)

### Context

Discussion session while PR #67 (Phase 5) sat under user review — started from tasks.md + resume.sh + a full read of the LTG master plan, aimed at "what's next" and grew into the T-33 split + product-framing decision capture.

### What Was Done

- docs(ltg): session-106 decision capture — model-registry library (T-76 deferred), T-33 split lean, T-77 signature extractor (`ltg-model-registry-design.md` restructured: Part 1 IMPLEMENTED, Part 2 = full session record)
- docs(ltg): T-33 repo-split discovery doc — established facts + open decision register S-D1–S-D7 (`docs/plans/ltg-repo-split-discovery.md`, `ref:ltg-split-decisions`)
- docs(ltg): split-discovery audit round — S-D7 substance (mutual blocking), LTG-overlay end-state, GPL licensing, portfolio driver
- Prior-art web survey (LiteLLM / any-llm / AbstractCore / PyALM / LLM Master): transport layer is commodity; registry+roles layer is the unowned library-worthy 20%
- Verified retrieval/ dependency map firsthand: all imports self-contained; real coupling = corpus.yaml paths + anchors git-grep convention + `store.py:44` REPO_ROOT landmine
- New branch `feature/model-registry-decision` (stacked on `feature/ltg-phase5-relate` for tasks.md consistency; rebase onto master after #67 merges)
- New feedback memory: never cat/grep a file you intend to Edit (Edit gates on Read → full file enters context twice)

### Decisions Made

- T-33 lean: **split before Phase 6** — drivers: mutual-blocking workflow decoupling (primary, user-confirmed; session-tracking arc ~88–93 as example), deliverable framing, portfolio evidence (smaller; reorders tier-3 → cheap-and-early visibility polish). S-D1–S-D7 to freeze in a fresh session post-#67-merge (session-104 freeze+plan shape), execute after
- T-76: model-registry shared-library extraction DEFERRED with triggers (first non-Ollama provider in LTG / first external adopter / third internal consumer); discipline rules in force (load_config stays one module; no config.yaml↔ai-backends.yaml shape divergence; multi-provider from day one when fired; delegate transport, never rebuild)
- T-77: signature/doc extractor = layer-0 primitive, Python + tree-sitter (not bash/ctags); completes the extraction-source quadrant (code/mechanical) and dual-serves ollama-scaffolding overlay + LTG
- Dependency topology rule: products (LTG engine, overlays) depend on layer-0 primitives (registry, ref-key grammar, sig extractor), never product↔product — resolves the "registry as public dep, vice versa?" question with no cycles
- Product-tier framing validated: tier 1 = Phase 6 / tier 2 = Phase 8 / tier 3 = non-phase work (provider abstraction = biggest gap)

### Next

- Merge PR #67; then fresh session: freeze S-D1–S-D7 + author `docs/plans/ltg-repo-split.md` (read `ltg-repo-split-discovery.md` + registry doc Part 2 first); rebase `feature/model-registry-decision` onto master
- Then execute the split (1.5–2 sessions); Phase 6 lands in the new repo

### Gotchas

- leidenalg is GPL-3 / python-igraph GPL-2 — irrelevant internally, but constrains tier-3 distribution license; caveat added to T-72(3) (igraph-direct deepens GPL)
- Never cat/grep a file you intend to Edit — Edit/Write gate on the Read tool, so the content enters context twice; decide edit-vs-read-only before reading (feedback memory saved)
- Capture audit caught 2 dropped pieces of user *intent* (LTG-overlay case, S-D7 substance) despite all *resolutions* being recorded — a closing "did we capture reasoning, not just conclusions?" pass is worth it on discovery/freeze sessions
