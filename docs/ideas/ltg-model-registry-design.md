# LTG Model Registry Design — Registered Models + Role Dispatch

**Part 1 status:** IMPLEMENTED — the two-level `models:` + `roles:` shape landed in
`retrieval/config.yaml` during the extractor retrofit (sessions 77–80) and now carries
4 models / 4 roles (`embedding`, `extraction_prose`, `extraction_code`, `relate_summary`).
**Part 2 status:** DEFERRED — shared-library extraction of the registry/roles layer.
Decision + prior-art research recorded session 106 (2026-07-04). Task: **T-76**.

---

# Part 1 — Two-Level Config Shape (2026-05, IMPLEMENTED)

## Context

Phase 2 uses a flat `retrieval/config.yaml` with one role (`embedding`) and inline model
config. This is correct for Phase 2 — one role, no duplication.

When Phase 3 adds `extraction_prose` and `extraction_code` roles, two roles will point
to qwen3:14b with different `think:` flags. At that point, a two-level design (named
model configs + role references) becomes worth the added indirection.

## Proposed Design

```yaml
models:
  ollama-bge-m3-dim-1024:
    provider: ollama
    model: bge-m3
    address: http://localhost:11434
    embed_dim: 1024

  ollama-qwen3-embedding-8b-dim-4096:
    provider: ollama
    model: qwen3-embedding:8b
    address: http://localhost:11434
    embed_dim: 4096

  ollama-qwen3-14b-no-think:
    provider: ollama
    model: qwen3:14b
    address: http://localhost:11434
    options: { think: false }

  ollama-qwen3-14b-think:
    provider: ollama
    model: qwen3:14b
    address: http://localhost:11434
    options: { think: true }

  ollama-qwen36coder-14b-no-think:
    provider: ollama
    model: qwen3.6-coder:14b
    address: http://localhost:11434
    options: { think: false }

roles:
  embedding: ollama-bge-m3-dim-1024
  extraction_prose: ollama-qwen3-14b-no-think
  extraction_code: ollama-qwen36coder-14b-no-think
```

Swap `embedding` to qwen3-embedding:8b after M-P0b probe passes: change one line (`embedding:
ollama-bge-m3-dim-1024` → `embedding: ollama-qwen3-embedding-8b-dim-4096`). Nothing else.

*(Historical note: as implemented, `think:` ended up a **top-level payload key**, not inside
`options{}` — Ollama silently ignores it there. The implemented shape in `retrieval/config.yaml`
is authoritative over the sketch above.)*

## Naming Convention

Model config names use **property enumeration**: `{provider}-{model-slug}-{key-params}`.

| Name | What the parts mean |
|------|---------------------|
| `ollama-bge-m3-dim-1024` | provider + model + dim (disambiguates from a future 768-dim quantization) |
| `ollama-qwen3-14b-no-think` | provider + model + the param that differentiates it from the think=true variant |
| `ollama-qwen3-14b-think` | same model, opposite flag |
| `ollama-qwen3-embedding-8b-dim-4096` | provider + model + dim (4096 vs 1024 is material — users need to see it) |

**Rules:**
- Always prefix with provider (`ollama`, `openai`, `anthropic`) — names become ambiguous without it when cloud models are added
- Use hyphens throughout (no colons, no dots — YAML keys with special chars need quoting)
- Append only parameters that distinguish this config from other configs of the same model
- Omit default/obvious parameters (no need for `num-ctx-10240` unless you have a variant with a different context window)
- If a model only ever appears once in `models:`, a single-property suffix is enough

## What `model_client.py` Changes

`load_config()` gains a reference-resolution step:

```python
def load_config(path) -> dict:
    raw = yaml.safe_load(open(path))
    # Resolve roles to full model configs
    resolved = {}
    for role, model_name in raw["roles"].items():
        if model_name not in raw["models"]:
            raise KeyError(
                f"Role '{role}' references model '{model_name}' "
                f"which is not defined in config.yaml [models:]"
            )
        resolved[role] = raw["models"][model_name]
    return resolved  # same shape as current flat dict — rest of ModelClient unchanged
```

`embed_dim(role)` still works the same way — it reads from the resolved config, not the raw YAML.

## Note on Parallel Registry

A `models:` block here creates a second model registry alongside `personas/registry.yaml`.
This is **intentional**: the personas registry is for Ollama Modelfiles (Claude Code personas,
Modelfile syntax). This registry is for raw Python-level model parameters (provider URL,
options dict, embedding dim). Different audience, different format, different lifecycle.

Additionally, **LTG is likely to move to its own repository** before Phase 3+ integration.
At that point, a self-contained `config.yaml` with its own model registry is an asset —
the retrieval package is fully portable without needing to reference the parent repo's
persona registry.

## Phase 2 Interim (inline config — superseded)

Until the trigger condition was met, `config.yaml` stayed flat:

```yaml
# One role, inline config.
# Upgrade to models: + roles: two-level design when:
#   - ≥2 roles reference the same base model with different params, OR
#   - ≥3 roles total
# Design: docs/ideas/ltg-model-registry-design.md
roles:
  embedding:
    provider: ollama
    model: bge-m3
    address: http://localhost:11434
    embed_dim: 1024
```

The trigger fired at the extractor retrofit (sessions 77–80); the two-level shape is live.

---

# Part 2 — Shared Registry Library Extraction (session 106, 2026-07-04, DEFERRED)

*Recorded from the session-106 discussion of T-33 repo separation, product framing, and
prior-art research. This part exists so a future session does not re-derive or re-research
any of it. Task: **T-76** in `.claude/tasks.md`.*

## 2.1 Vision statement (verbatim intent)

> "All of this stuff I'm developing, I'd want to be configurable for any choice of model
> and access: ai-backends.yaml has some of that in place, and the format we've arrived to
> for LTG is one I find quite satisfying, allowing one to have a registry of model
> configurations, and reuse it wherever it makes sense. This does look like a library in
> itself."

The goal: every tool built in this ecosystem (LTG engine, overlay installer, future
signature extractor, web-research Dispatcher, …) should be configurable for **any choice
of model and access method** through one reusable registry format, instead of each tool
growing its own bespoke model config.

## 2.2 The three-registry observation (repo inventory, session 106)

Three look-alike registries exist in this repo today, with **zero shared code** — parallel
evolution of the same idea:

| File | Consumer | Shape / strengths |
|---|---|---|
| `retrieval/config.yaml` | LTG `ModelClient` (`load_config()` in `model_client.py`) | Named model configs + **role indirection** (`embedding:` / `extraction_prose:` / `extraction_code:` / `relate_summary:`). Encodes hard-won provider knobs: `think:` as top-level payload key (NOT `options{}`), `num_ctx: 32768`, per-role temperature (relate_summary 0.2 vs extraction 0.1), `timeout_s`, `embed_dim`. Also carries the non-model `graph:` section (τ/K/resolutions/seed). Ollama-only (`provider: ollama` is the sole implemented transport). |
| `overlays/ai-backends.yaml` | `install-overlay.py` AI-merge fallback chain | **Multi-provider** (ollama_api / cli / claude_api) + **priority fallback chain** (try backends in order, skip unavailable) + **`schema_mode` strategy per backend** (`format_param` / `prompt_injection` / `tool_use`) + **CLI-subprocess backend** (`claude -p --model haiku --output-format json` — no API key needed) + `api_key: env:VAR` indirection (never inline). |
| `personas/registry.yaml` | persona creator / MCP tools | Persona catalog (Ollama Modelfiles). Deliberately separate — different audience, format, lifecycle (see Part 1 "Note on Parallel Registry"). Stays out of scope for the library. |

**How this surfaced:** discussion of T-33 repo separation. Initial belief: `retrieval/`
depends on a model/persona registry in `overlays/`. It does not — retrieval's imports are
fully self-contained (verified session 106: all imports are stdlib/third-party/intra-package;
the real llm-repo coupling is data + convention: `corpus.yaml` paths, `anchors.py` git-grep
over the working tree, and the `store.py:44` `REPO_ROOT = Path(__file__).parent.parent`
assumption). But the *conflation was productive*: the two YAML files are the same idea at
different maturities — `ai-backends.yaml` is the more **product-mature** (multi-provider,
fallback, schema strategies) while `retrieval/config.yaml` is the more
**application-mature** (roles as a contract, provider quirk encoding, per-role tuning).

## 2.3 Prior-art research (2026-07-04 web survey)

**Conclusion: the transport layer is commodity; the registry/roles layer is not.**

Surveyed landscape:

- **LiteLLM** — the incumbent. Unified OpenAI-style interface to 140+ providers (Ollama
  included). Its proxy config is literally a YAML model registry: `model_list` of named
  configs, router settings with **fallback chains**, load balancing, cost tracking,
  caching, observability. Both a Python SDK and a proxy server. Heavyweight dependency,
  fast-moving, known for frequent breaking changes.
  https://a2a-mcp.org/blog/what-is-litellm ·
  https://codeyaan.com/blog/programming-languages/litellm-unified-python-sdk-for-100-llm-providers-2503
- **any-llm (Mozilla AI)** — the lean version: unified interface, switch providers via a
  single config parameter, minimal footprint.
  https://blog.mozilla.ai/introducing-any-llm-a-unified-api-to-access-any-llm-provider/
- **AbstractCore** — "write once, run everywhere"; explicitly **local-first** (run local
  models end-to-end or switch to cloud with identical code), prompt caching,
  OpenAI-compatible gateway. https://github.com/lpalbou/AbstractCore
- **PyALM** — abstraction layer for different LLMs. https://github.com/finnschwall/PyALM
- **LLM Master** — unified interface for multiple LLM + multimedia providers.
  https://github.com/Habatakurikei/llmmaster

## 2.4 Gap analysis — our shape vs. existing libraries

| Feature | Where we have it | Covered by existing libs? |
|---|---|---|
| Provider transport (per-provider HTTP quirks) | `ModelClient._chat()`, Ollama-only | ✅ **Commodity.** LiteLLM/any-llm do this ×140 providers. Do NOT rebuild. |
| Named model registry in YAML | `config.yaml` `models:` | ✅ LiteLLM proxy `model_list` is this exactly |
| Fallback priority chain | `ai-backends.yaml` `priority:` | ✅ LiteLLM Router fallbacks |
| **Role indirection** (semantic roles as an *application contract*: "this app needs an embedding arm, a prose arm, a summary arm — wire them here") | `config.yaml` `roles:` | ❌ Model *aliases* exist everywhere; app-level **role** semantics are first-class nowhere |
| **`schema_mode` strategy** per backend (`format_param` / `prompt_injection` / `tool_use`) | `ai-backends.yaml` | ⚠️ Libs normalize structured output per provider, but explicit per-backend strategy *selection* is unusual |
| **CLI-subprocess backend** (Claude Code CLI as a model backend, no API key) | `ai-backends.yaml` `type: cli` | ❌ Nobody does this. Genuinely bespoke. |
| Hard-won provider knob placement (`think:` top-level not in `options{}`; `num_ctx`; `format` param reliability) | Both files + `ref:thinking-mode` / `ref:structured-output` | ⚠️ Passthrough exists; whether quirks survive the abstraction is exactly where generic wrappers leak |
| `api_key: env:VAR` indirection | `ai-backends.yaml` | ✅ Common pattern |

## 2.5 The two-layer conclusion

The satisfying design is a **two-layer cake, and only the bottom layer is commodity**:

```
┌──────────────────────────────────────────────────────┐
│  Registry / roles layer (~200 lines, app-shaped)      │  ← unowned in the market;
│  named configs · roles contract · fallback policy ·   │    THIS is the library
│  schema_mode strategy · validation · env-key refs     │
├──────────────────────────────────────────────────────┤
│  Transport layer (talk to a provider correctly)       │  ← commodity; PLUGGABLE:
│  delegate: LiteLLM / any-llm for hosted providers     │    delegate, don't build
│  keep: own httpx path for Ollama (quirks encoded)     │
└──────────────────────────────────────────────────────┘
```

- Building transport = re-implementing LiteLLM badly. Delegate it.
- The top layer is thin, app-shaped, and **unowned** — that is the library-worthy 20%.
- Keep our own httpx Ollama path as one pluggable transport: the `think:`-placement /
  `format`-param / `num_ctx` knowledge is already encoded and battle-tested there, and
  local-first is the primary deployment.
- The eventual library's candidate scope = union of the two files' strengths:
  named model configs + roles contract + priority fallback + `schema_mode` strategies +
  CLI-subprocess backend + `env:` key indirection + validation (unknown role → named
  error, as `load_config()` does today).

## 2.6 Dependency topology — registry as a layer-0 primitive

From the same session's product-topology discussion (see T-33 amendment in `tasks.md`):

```
            ┌─────────────┐        ┌──────────────┐
            │  LTG engine │        │   overlays   │      ← products
            └──────┬──────┘        └──────┬───────┘
                   │        ┌─────────────┤
                   ▼        ▼             ▼
     ┌────────────────┐ ┌──────────────┐ ┌─────────────────┐
     │ model registry │ │ ref-key      │ │ sig extractor   │   ← primitives
     │ (this library) │ │ grammar     │ │ (tree-sitter)   │
     └────────────────┘ └──────────────┘ └─────────────────┘
```

**Rule: dependencies point downward only — products depend on primitives, never on each
other.** This resolves the "registry could be a public dependency LTG uses — and vice
versa?" question: no vice versa, ever (product↔product cycles are how shared codebases
rot). The registry becomes a primitive *both* the overlay installer and the LTG engine
consume; neither product imports the other. Sibling primitives identified the same session:

- **ref-key grammar** — T-72(1) already notes a 4th ad-hoc copy of the regex inside this
  repo; the within-repo extraction is overdue and upgrades to a public seam under product
  framing.
- **signature/doc extractor** (T-77) — mechanical code-node source for LTG + context
  feeder for the ollama-scaffolding overlay. Completes the extraction-source quadrant:
  prose/LLM = topics · md/mechanical = ref anchors · code/LLM = coder-arm topics ·
  **code/mechanical = signatures+doc-comments**. Python + tree-sitter (not bash/ctags):
  needs structured JSON out with per-language doc-comment attachment, and serves two
  products plus external machines.

## 2.7 Relation to the product-tier framing

Also from session 106 — maturity tiers for LTG as a deliverable ("viable in the use
sense, not the sell one"):

| Tier | Meaning | Requires |
|---|---|---|
| 1. Internal substrate | This machine, all repos, via MCP | Phase 6 only (MCP registration is machine-global). Formal plan success definition met here. |
| 2. Multi-corpus tool | Per-repo indexes, permission scoping | Phase 8 (the T-33 repo split pulls ~half of it forward: `REPO_ROOT` / corpus parameterization). Phase 9 federation optional. |
| 3. Adoptable product | Someone else's machine/corpus | Mostly **non-phase work**: provider abstraction (THIS document), packaging/install, docs, schema versioning, license, graceful degradation when llm-repo conventions are absent (no ref keys → anchors source is a no-op, not an error). Phase 7 reranker = optional quality knob at every tier. |

**Provider abstraction is the single biggest tier-3 gap and is invisible in the phase
plan** (it was a non-issue on a one-machine substrate). An external adopter's first
touchpoint is this config file — they have an OpenAI/Claude key, not an RTX 3060.

<!-- ref:model-registry-library-decision -->
## 2.8 Decision (session 106, 2026-07-04): DEFER extraction — with discipline rules now

**Decision:** Do NOT extract the registry/roles layer into a shared library yet. It is
explicitly **not a requirement for the T-33 repo split**, and coupling the two would push
the split past its ~1.5–2-session scope for no near-term consumer.

**Why deferral is cheap (and stays cheap):**
1. The eventual build is small — a thin layer + transport delegation (Part 2.5), not a
   platform. No compounding lock-in accrues while waiting.
2. Both existing implementations are already contained: `load_config()` lives in one
   module (`retrieval/model_client.py`); backends resolution lives in `overlays/lib`.
   Nothing is spreading; extraction stays mechanical whenever it happens.
3. The requirements that would shape the design haven't arrived. The first non-Ollama
   provider need or first external adopter will answer questions no design session can
   (does `schema_mode` belong in the registry or the transport? does the CLI backend
   survive at all?).

**Re-evaluation triggers (any one fires T-76):**
- First need for a **non-Ollama provider** in LTG (e.g., a Claude-API quality arm).
- First **external adopter** of LTG or the overlays (tier 3 becomes real).
- A **third internal consumer** of the registry shape (most plausible: web-research
  Dispatcher — see T-51 local-routing audit).

**Discipline rules in force from now (cost ≈ 0):**
1. Through the T-33 split, `load_config()` + the config schema stay in **one module** of
   the engine — config parsing must not spread across modules.
2. No gratuitous divergence between `retrieval/config.yaml` and `overlays/ai-backends.yaml`
   shapes — when either evolves, check the other's vocabulary first (they merge under T-76).
3. When T-76 fires, design **multi-provider from day one** (that's where ai-backends'
   fallback-chain + `schema_mode` shape merges with config.yaml's roles shape) — doing it
   single-provider means doing it twice.
4. Transport is delegated (LiteLLM or any-llm for hosted; own httpx for Ollama), never
   rebuilt. Re-verify the library landscape at trigger time — this corner moves fast;
   the 2.3 survey is a snapshot of 2026-07.
<!-- /ref:model-registry-library-decision -->

