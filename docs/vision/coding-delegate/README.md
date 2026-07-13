# Coding-Delegate — Grand Vision (working name)

**Status:** Vision v1 authored 2026-07-11 (stress-tested, course-corrected, research-backed).
**P1 (async substrate) BUILT + MERGED to master** (2026-07-12; `docs/plans/oficina-p1-async-substrate.md`,
149 tests, live acceptance 6/6). **`oficina` CLI installed machine-wide** + 4 MCP tools live.
Each remaining phase gets its own `docs/plans/` doc before execution (P2 next). Current state:
`.memories/QUICK.md`; implementation invariants + distribution model: `.memories/KNOWLEDGE.md`.
**Name:** **`oficina`** (DECIDED, V-D1 2026-07-11 — `naming.md`). The `coding-delegate` folder
label survives; ref keys are location-agnostic.

**Note:** oficina is a **machine-global service** (CLI + user-level MCP tools + shared store),
NOT a per-repo overlay — you don't `install-overlay` it; new-machine enablement is 3 steps
(uv-tool install `mcp-server` + user-level MCP registration + Ollama). See KNOWLEDGE.md
"Distribution" + task T-86.

## Elevator

Evolve ollama-bridge's `generate_code` (and `ask_ollama`) from a synchronous prompt-in/text-out
call into an **async deliverable runner**: Claude submits a bounded deliverable spec (one test
file, one function, one class), gets a `run_id` back instantly, and keeps working; a detached
worker loops a local coder model against the Layer-4 evaluator until mechanical defects are
gone or budgets exhaust; Claude reviews each delivered result against plan and quality. Every
iteration is logged with an automatic verdict — the DPO flywheel becomes a byproduct. End
state (user's words): *"given a detailed enough plan, a Claude session using it will mostly be
the coordinator and verifier."*

## Navigation

The authoritative map lives in **`index.md`** (this folder): files by recontextualization
intent, the full 26-key `ref:delegate-*` inventory, supporting research artifacts, and memory
files. Cold-start reading order: `vision.md` → `phasing.md` → `architecture.md`; pull
`evidence.md` sections on demand via `ref-lookup.sh`. Current project state:
`.memories/QUICK.md`.

## Provenance (how this knowledge was produced, 2026-07-11 session)

- User's vision statement + one course correction (near-term = **one call, one deliverable**;
  autonomy is horizon 2) + answers to 7 scoping questions — all folded into `vision.md`/`decisions.md`.
- **Two-agent prior-art comparison run** (frontier web tools vs the local web-research MCP,
  same questions): `docs/research/coding-subagent-prior-art.md` and
  `docs/research/coding-subagent-prior-art-webresearch.md`. Side product: a field report on
  web-research's defects shipped cross-repo to
  `~/workspaces/web-research/docs/reports/2026-07-11-field-report-llm-prior-art-run.md`.
- **Clones survey** (patterns from `~/workspaces/clones/`, incl. the proprietary claude-code
  source — patterns only, never code): `docs/research/coding-subagent-clones-survey.md`.
- **Verdict-data mining** of `~/.local/share/ollama-bridge/calls.jsonl` via
  `.claude/tools/ollama-stats.py` + `ollama-verdicts.py` (457 calls, 49 verdicts) —
  distilled in `evidence.md`.
