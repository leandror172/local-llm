# LTG Model Registry Design — Registered Models + Role Dispatch

**Status:** Deferred — implement when Phase 3 adds extraction roles.
**Trigger:** ≥2 roles sharing the same base model with different parameters, OR ≥3 roles total.

---

## Context

Phase 2 uses a flat `retrieval/config.yaml` with one role (`embedding`) and inline model
config. This is correct for Phase 2 — one role, no duplication.

When Phase 3 adds `extraction_prose` and `extraction_code` roles, two roles will point
to qwen3:14b with different `think:` flags. At that point, a two-level design (named
model configs + role references) becomes worth the added indirection.

---

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

---

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

---

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

---

## Note on Parallel Registry

A `models:` block here creates a second model registry alongside `personas/registry.yaml`.
This is **intentional**: the personas registry is for Ollama Modelfiles (Claude Code personas,
Modelfile syntax). This registry is for raw Python-level model parameters (provider URL,
options dict, embedding dim). Different audience, different format, different lifecycle.

Additionally, **LTG is likely to move to its own repository** before Phase 3+ integration.
At that point, a self-contained `config.yaml` with its own model registry is an asset —
the retrieval package is fully portable without needing to reference the parent repo's
persona registry.

---

## Phase 2 Interim (inline config — current)

Until the trigger condition is met, keep `config.yaml` flat:

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

The comment in the file itself documents the upgrade path without implementing it prematurely.
