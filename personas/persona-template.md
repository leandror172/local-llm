# Persona Template Specification

**Version:** 1.0
**Created:** 2026-02-17
**Purpose:** Canonical reference for creating Ollama Modelfile personas.

---

## Overview

A persona is a lightweight Ollama model configuration (Modelfile) that pairs a base model with role-specific parameters and a system prompt. All personas share the same base weights on disk — only the configuration layer differs (~few KB each).

### Two Persona Tiers

| Tier | Description | Has SYSTEM prompt | Has full params | Example |
|------|-------------|:-:|:-:|---------|
| **Full** | Standalone persona used via API or MCP | Yes | Yes | my-coder-q3, my-classifier-q3 |
| **Bare** | Wrapper for external tools that inject their own prompt | No | Minimal | my-aider, my-opencode |

---

## Modelfile Structure

### Required Fields

Every persona Modelfile **must** include:

```
FROM <base-model>
PARAMETER num_ctx <context-size>
PARAMETER temperature <value>
```

### Standard Fields (Full Personas)

Full personas include all of these. Bare personas omit what the host tool controls.

```
FROM <base-model>

PARAMETER num_ctx 16384
PARAMETER temperature <0.1 | 0.3 | 0.7>
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

SYSTEM """<system-prompt>"""
```

### Field Reference

| Field | Required | Default | Notes |
|-------|:--------:|---------|-------|
| `FROM` | Yes | — | Base model tag from Ollama. See Model Selection below |
| `num_ctx` | Yes | 16384 | Context window in tokens. Only reduce for 14B models (use 4096) |
| `temperature` | Yes | 0.3 | See Temperature Guide below |
| `top_p` | Full | 0.9 | Nucleus sampling cutoff. No reason to change from 0.9 |
| `repeat_penalty` | Full | 1.1 | Prevents loops without breaking natural patterns |
| `stop` (pair) | Full | Both ChatML tokens | `<\|im_end\|>` + `<\|endoftext\|>`. Omit only for bare personas |
| `SYSTEM` | Full | — | Must use skeleton format (see below) |

---

## System Prompt Skeleton

All full personas use the **ROLE / CONSTRAINTS / FORMAT** skeleton:

```
SYSTEM """ROLE: <one-line role description>.
CONSTRAINTS:
- MUST <positive requirement>
- MUST <positive requirement>
- MUST NOT <negative requirement>
- MUST NOT <negative requirement>
FORMAT: <output format description>."""
```

### Rules

1. **ROLE** — Single sentence. States what the persona IS, not what it does
2. **CONSTRAINTS** — 5-8 items using MUST / MUST NOT (never "should" or "try to")
3. **FORMAT** — Single sentence describing expected output structure
4. **Total length** — Target ~80-120 tokens. 7-8B models follow short prompts more reliably
5. **Each constraint targets a real failure** — Don't add rules speculatively; add them when you observe the model breaking that behavior

### Constraint Patterns

| Pattern | When to use | Example |
|---------|-------------|---------|
| `MUST output X` | Define the primary deliverable | "MUST output complete, compilable code" |
| `MUST use X` | Enforce a specific standard | "MUST use standard library only" |
| `MUST include X` | Require an often-skipped element | "MUST include error handling" |
| `MUST NOT add X` | Suppress a common bad behavior | "MUST NOT add explanatory text unless asked" |
| `MUST NOT invent X` | Prevent hallucination | "MUST NOT invent import paths" |
| `MUST maintain X` | Preserve input properties | "MUST maintain original formatting" |

---

## Temperature Guide

| Value | Use when | Personas |
|-------|----------|----------|
| **0.1** | Same input must produce same output | classifier, codegen, tool-integrated (aider, opencode) |
| **0.3** | Accuracy matters but mild variation helps | coder, creative-coder, summarizer, translator |
| **0.7** | Creativity and diversity wanted | writer, brainstormer (future) |

**Rule of thumb:** If the persona's output gets evaluated for correctness → 0.1. If it gets evaluated for quality → 0.3. If it gets evaluated for creativity → 0.7.

---

## Model Selection Guide

Choose the base model based on the persona's role:

| Role Type | Recommended Base | Ollama Tag | VRAM | Context | Why |
|-----------|-----------------|------------|------|---------|-----|
| **Code generation** | Qwen3-8B | `qwen3:8b` | ~5.2 GB | 16K | Best coding quality at 7-8B |
| **Code generation (Qwen2.5)** | Qwen2.5-Coder-7B | `qwen2.5-coder:7b` | ~4.7 GB | 16K | Legacy; use for Qwen2.5-specific personas |
| **Heavy reasoning** | Qwen3-14B | `qwen3:14b` | ~9.3 GB | 4K | Deeper reasoning, limited context |
| **Fast classification** | Qwen3-4B | `qwen3:4b-q8_0` | ~4.4 GB | 4K | Speed > depth |
| **General writing** | Llama-3.1-8B | `llama3.1:8b-instruct-q5_K_M` | ~5.7 GB | 16K | Broader training than code models |
| **Translation (PT-BR)** | Qwen3-8B | `qwen3:8b` | ~5.2 GB | 16K | Strong multilingual; research ongoing |

### Decision Flow

```
Is the task code-related?
  ├─ Yes → Qwen3-8B (or Qwen2.5-Coder for legacy)
  └─ No
      ├─ Needs deep reasoning / architecture? → Qwen3-14B (4K ctx)
      ├─ Needs speed / routing / classification? → Qwen3-4B
      ├─ General writing / docs / coaching? → Llama-3.1-8B
      └─ Multilingual / translation? → Qwen3-8B
```

---

## Naming Convention

```
my-<role>           → Qwen2.5-based persona   (e.g., my-coder)
my-<role>-q3        → Qwen3-based persona      (e.g., my-coder-q3)
my-<tool>           → Bare persona for a tool   (e.g., my-aider, my-opencode)
```

Modelfile naming: `<role>-<base>.Modelfile`
- `coding-assistant-qwen3.Modelfile` → registered as `my-coder-q3`
- `classifier-qwen3.Modelfile` → registered as `my-classifier-q3`

---

## Registration

After creating a Modelfile, register it with Ollama:

```bash
ollama create my-<name> -f modelfiles/<filename>.Modelfile
```

This creates a lightweight manifest (~few KB) pointing to the shared base model weights. No disk duplication.

---

## Bare Persona Guidelines

For personas wrapped by external tools (Aider, OpenCode, etc.):

1. **No SYSTEM prompt** — the tool injects its own
2. **Minimal parameters** — only `FROM`, `num_ctx`, `temperature`
3. **Stop tokens** — omit or set only what the tool doesn't handle
4. **Comment the rationale** — explain WHY each omission is intentional

---

## Checklist: Creating a New Persona

- [ ] Choose base model using the Decision Flow
- [ ] Set temperature using the Temperature Guide
- [ ] Write SYSTEM prompt using the skeleton (ROLE / CONSTRAINTS / FORMAT)
- [ ] Keep constraints to 5-8 items, each targeting an observed failure
- [ ] Keep total SYSTEM prompt under ~120 tokens
- [ ] Add inline comments explaining non-obvious parameter choices
- [ ] Register with `ollama create my-<name> -f modelfiles/<file>.Modelfile`
- [ ] Test with a representative prompt to verify behavior
- [ ] Add to persona registry (`personas/registry.yaml`)
