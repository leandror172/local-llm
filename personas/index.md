# Personas — Folder Index

**Authoritative map for the persona system.** The root `.claude/index.md` keeps a pointer
here and nothing more (index split — same pattern as `docs/vision/coding-delegate/index.md`).

**Source of truth is `registry.yaml`.** Every count in this file is a snapshot; re-derive
rather than quoting. As of 2026-07-21: **59 personas — 51 active, 6 benchmark, 2 inactive —
across 14 distinct base models**, with 59 matching Modelfiles in `../modelfiles/`.

---

## Files

### Data (source of truth)
| File | Purpose |
|------|---------|
| `registry.yaml` | Persona inventory — name, modelfile, base_model, role, temperature, num_ctx, tier, status. **The** authority. |
| `models.yaml` | Base-model definitions (contexts, temps, domains). 19 entries defined; 14 referenced by a registry persona. |
| `../modelfiles/*.Modelfile` | The Ollama Modelfiles themselves — 1:1 with registry entries. Sibling folder, persona-owned. |

### Documentation
| File | Purpose | Ref key |
|------|---------|---------|
| `personas-reference.md` | Catalog by category with modelfile + base model | `ref:personas` ⚠️ **incomplete — see below** |
| `persona-template.md` | Spec for creating a new persona: fields, defaults, skeleton, model selection, checklist | — |
| `ideas.md` | Candidates not yet built | — |
| `BUILD-PERSONA.md` / `DETECT-PERSONA.md` | Tool-specific docs for the build/detect CLIs | — |

### Tools
| Script | Wrapper | Purpose |
|--------|---------|---------|
| `create-persona.py` | `run-create-persona.sh` | Interactive 8-step flow or `--non-interactive` flags; accepts raw float temps [0.0, 2.0] (T-19) |
| `detect-persona.py` | `run-detect-persona.sh` | Deterministic codebase analyzer → persona recommendation. Three-signal scoring: extensions 50% / imports 30% / config files 20%. **No LLM calls.** |
| `build-persona.py` | `run-build-persona.sh` | LLM-assisted conversational persona designer (`my-persona-designer-q3`) |
| `models.py` | — | Shared helpers (`parse_temperature_input`, registry/model loading) |

### Tests
| File | Purpose |
|------|---------|
| `run-tests.sh` | Entry point — `python3 -m pytest`; **21 tests** across unit + integration |
| `pyproject.toml` | `[tool.pytest.ini_options]` testpaths + pythonpath |
| `tests/test_temperature.py` | Unit tests for `parse_temperature_input` |
| `tests/test_collect_flags.py` | Integration: argparse + `collect_from_flags` end-to-end |

### Memory
`.memories/QUICK.md` (working) · `.memories/KNOWLEDGE.md` (MODEL_MATRIX rationale,
constraint-reliability findings, detection algorithm, tier design)

---

## ⚠️ Open: `ref:personas` catalog is incomplete (T-108, decision deferred)

**State as of 2026-07-21:** `personas-reference.md` lists **34 of 59** personas, while
advertising itself as the "full catalog". `CLAUDE.md`'s model-selection rule points at
`[ref:personas]`, so this is the catalog an agent consults to choose a model.

**Why it matters — the omissions are the ones actually in use.** Measured against
`~/.local/share/ollama-bridge/calls.jsonl`: **286 of 566 logged calls (51%) used a persona
the catalog does not list**, including the 2nd and 3rd most-used overall
(`my-go-qcoder` 100 calls, `my-python-q25c14` 91 calls). Two of the missing entries —
`my-python-q25c14` and `my-mcp-q25c14` — are *named as recommended* in
`ref:active-decisions` while being invisible in the catalog that recommendation points at.

**Root cause — subset staleness, which is why it went unnoticed.** `create-persona.py`
writes `registry.yaml`; **nothing writes `personas-reference.md`**. Every persona created
since roughly session 50 exists in the machine-readable source and is absent from the
human/agent-readable one. The two files never *disagree* on any individual row — the
reference is a strict subset — so there is no contradiction to trip over, only an absence.
Contrast with the count drift fixed in session 126, which was detectable by comparison.

**Missing entries (25):** `my-api-docs-q3`, `my-classifier-q35`, `my-classifier-qcoder`,
`my-go-deepcoder`, `my-go-deepcoder-vanilla`, `my-go-g3-12b`, `my-go-g3-27b`,
`my-go-q3-14b`, `my-go-q35`, `my-go-q35-27b`, `my-go-qcoder`, `my-mcp-deepcoder`,
`my-mcp-deepcoder-vanilla`, `my-mcp-q25c14`, `my-python-deepcoder`,
`my-python-deepcoder-vanilla`, `my-python-dsc16`, `my-python-dsr14`, `my-python-g3-12b`,
`my-python-g3-27b`, `my-python-q25c14`, `my-python-q3-14b`, `my-python-q3-30a3b`,
`my-python-q35`, `my-python-q3c30`.

### Candidate strategies — not yet decided

| # | Strategy | Gains | Costs |
|---|----------|-------|-------|
| **a** | **Generate `personas-reference.md` from `registry.yaml`** via a `run-render-catalog.sh`; make it a build artifact | Cannot drift again — one source of truth. Fixes the class, not the instance | Flattens the hand-curated category structure ("Specialized Coding", "Code Review", "Architecture", "Cloud Consulting"…) unless categories move *into* `registry.yaml` as a field |
| **b** | **Hand-add the 25 missing rows** | Preserves curation exactly; cheapest right now | Decays again on the very next `create-persona.py` run — treats the instance, not the cause |
| **c** | **Hybrid** — keep curated sections, append a generated "All personas (complete)" table below them | Curation survives *and* the promise of completeness is machine-kept | Two representations of the same set in one file; needs a rule for which wins |
| **d** | **Retire `personas-reference.md`** — move `ref:personas` onto a `query_personas`/`--list` CLI view over `registry.yaml` | No prose catalog to rot; the MCP tool `query_personas` already reads the registry live | `ref:KEY` lookups are file-based today, so `ref:personas` would become a pointer-to-a-command rather than content |

**Prerequisite for (a) and (c):** `registry.yaml` has no `category` field — categories exist
only as headings in the prose. Adding one is a small schema change that
`create-persona.py` would need to prompt for.

**Also decide:** whether the catalog should list *all* 59 or only `status: active` (51).
Some omissions may be deliberate — the `*-vanilla` pairs and the 6 `benchmark`-status
entries are plausibly not meant for routine selection. Do not assume all 25 are oversights.

**Do not fix this piecemeal.** Option (b) alone reproduces the same gap within weeks.
