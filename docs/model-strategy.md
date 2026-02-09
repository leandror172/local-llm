# Model Strategy: Multi-Model Inventory for RTX 3060 12GB

**Last updated:** 2026-02-07

---

## Hardware Constraints

- **VRAM:** 12,288 MiB (12 GB)
- **Model loading:** One model active in VRAM at a time (Ollama swaps on demand)
- **Swap time:** Cold load ~40s, warm reload (within keep_alive window) <100ms
- **Embedding model:** Can coexist alongside main model (~275 MB)
- **Keep alive:** 30 minutes default (configurable per model)

## VRAM Budget

| Model Size | Quantization | VRAM (weights) | VRAM (with 16K ctx) | VRAM (with 4K ctx) | Fits? |
|-----------|-------------|---------------|--------------------|--------------------|-------|
| 3-4B | Q5_K_M | ~2.5 GB | ~3.5 GB | ~3.0 GB | Comfortable |
| 7-8B | Q5_K_M | ~4.8 GB | ~6.3 GB | ~5.3 GB | Comfortable |
| 7-8B | Q6_K | ~5.5 GB | ~7.0 GB | ~6.0 GB | Good |
| 7-8B | Q8_0 | ~7.0 GB | ~8.5 GB | ~7.5 GB | Tight |
| 14B | Q4_K_M | ~7.9 GB | ~10+ GB | ~8.9 GB | 4K ctx only |
| 14B | Q5_K_M | ~9.1 GB | Doesn't fit | ~10.1 GB | Marginal |

**Strategy:** Use Q5_K_M for 7-8B models (best quality-to-VRAM ratio). Use Q4_K_M for 14B models (only option that fits). Use higher quants (Q6_K, Q8_0) for small models (3-4B) where VRAM is abundant.

---

## Model Inventory

### Tier 1: Daily Drivers (pull immediately in Layer 0)

| Role | Model | Quant | VRAM | Context | Why this model |
|------|-------|-------|------|---------|---------------|
| **Coding** | Qwen3-8B | Q4_K_M | ~5.2 GB | 16K | Outperforms Qwen2.5-14B on coding benchmarks. Direct upgrade from current Qwen2.5-Coder-7B |
| **Heavy reasoning** | Qwen3-14B | Q4_K_M | ~9.3 GB | 4K | Architecture decisions, complex analysis. Short context is fine for reasoning tasks |
| **Classification / routing** | Qwen3-4B | Q8_0 | ~4.4 GB | 4K | Fast, cheap. Good enough for "is this a coding question or a general question?" |

> **Note (2026-02-08):** Ollama's library doesn't offer Q5_K_M for Qwen3. Available quantizations are Q4_K_M, Q8_0, and FP16. Q4_K_M is the practical choice for 8B (comfortable VRAM with 16K ctx). For Q5_K_M, you'd need to import a GGUF from HuggingFace manually — marginal benefit doesn't justify the complexity.

### Tier 2: Specialized (pull when building specific layers)

| Role | Model | Ollama tag | Quant | Size | When needed | Notes |
|------|-------|-----------|-------|------|-------------|-------|
| **General / writing** | Llama-3.1-8B-Instruct | `llama3.1:8b-instruct-q5_K_M` | Q5_K_M | 5.7 GB | Layer 3 (personas) | Broader training than code-focused models. Better for career coaching, general writing |
| **Embeddings (RAG)** | nomic-embed-text | `nomic-embed-text` | native | 274 MB | Layer 7 (memory) | Runs alongside main model. Required for vector search |
| **Translation (PT-BR)** | Needs research | TBD | TBD | TBD | Layer 3/8 | Quality critical. May need frontier for nuanced PT-BR. Research during Layer 3 |

### Tier 3: Experimental (test when exploring)

| Role | Model | Ollama tag | Quant | Size | Notes |
|------|-------|-----------|-------|------|-------|
| **Reasoning specialist** | DeepSeek-R1-Distill-Qwen-14B | `deepseek-r1:14b` | Q4_K_M | 9.0 GB | Chain-of-thought reasoning. Good for evaluator role |
| **Alternative coder** | DeepSeek-Coder-V2 (MoE) | `deepseek-coder-v2:16b` | default | 8.9 GB | 16B total params, 2.4B active per token. MoE stores all experts — VRAM ~8.9 GB, not ~4 GB as originally estimated |
| **Fast code** | Mamba-Codestral-7B | *not on Ollama* | — | — | SSM architecture, 1.5-2x faster. Would need HuggingFace GGUF import |

---

## Model-to-Persona Mapping

| Persona | Base Model | Rationale |
|---------|-----------|-----------|
| my-coder | Qwen3-8B | Code-optimized, fast, full context |
| my-architect | Qwen3-14B | Needs deeper reasoning, OK with 4K context |
| my-reviewer | Qwen3-8B | Code review is a coding task |
| my-classifier | Qwen3-4B / Phi-4-mini | Speed matters more than depth |
| my-writer | Llama-3.1-8B | Broader training for non-code text |
| my-translator | TBD (research needed) | May need different model for PT↔EN quality |
| my-evaluator | Qwen3-14B (local) or Claude (frontier) | Needs strongest available reasoning |

**Key insight:** The persona creator (Layer 3) should recommend base models based on the role being created, not default everything to the same model. A "meta-model" that understands the strengths of each base model.

---

## Disk Space Budget

Models stored at `~/.ollama/models/` in WSL2.

| Model | Ollama tag | On-disk size | Cumulative |
|-------|-----------|-------------|------------|
| Qwen2.5-Coder-7B (existing) | `qwen2.5-coder:7b` | 4.7 GB | 4.7 GB |
| Qwen3-8B Q4_K_M | `qwen3:8b` | 5.2 GB | 9.9 GB |
| Qwen3-14B Q4_K_M | `qwen3:14b` | 9.3 GB | 19.2 GB |
| Qwen3-4B Q8_0 | `qwen3:4b-q8_0` | 4.4 GB | 23.6 GB |
| Llama-3.1-8B Q5_K_M | `llama3.1:8b-instruct-q5_K_M` | 5.7 GB | 29.3 GB |
| nomic-embed-text | `nomic-embed-text` | 274 MB | 29.6 GB |
| DeepSeek-R1-Distill-14B Q4_K_M | `deepseek-r1:14b` | 9.0 GB | 38.6 GB |
| DeepSeek-Coder-V2 16B MoE | `deepseek-coder-v2:16b` | 8.9 GB | 47.5 GB |

**Available:** I: drive has 562 GB free. Disk is not a constraint.

---

## Upgrade Path

### All tiers (automated)
```bash
# Downloads all 7 models (~43.8 GB) in priority order.
# Tier 1 finishes first so Layer 0 work can begin immediately.
./scripts/pull-layer0-models.sh
```

### Manual (individual pulls)
```bash
# Tier 1 — Daily Drivers
ollama pull qwen3:8b                        # Q4_K_M, ~5.2 GB
ollama pull qwen3:14b                       # Q4_K_M, ~9.3 GB
ollama pull qwen3:4b-q8_0                  # Q8_0,   ~4.4 GB

# Tier 2 — Specialized
ollama pull llama3.1:8b-instruct-q5_K_M    # Q5_K_M, ~5.7 GB
ollama pull nomic-embed-text                # native,  ~274 MB

# Tier 3 — Experimental
ollama pull deepseek-r1:14b                 # Q4_K_M, ~9.0 GB
ollama pull deepseek-coder-v2:16b           # MoE,    ~8.9 GB
```

---

## Quantization Decision Guide

When choosing quantization for a new model:

1. **Is it a 14B+ model?** → Q4_K_M (only option that fits 12GB)
2. **Is it a 7-8B model?** → Q4_K_M (default on Ollama) or Q5_K_M if available. Check `ollama.com/library/<model>/tags` for exact options
3. **Is it a 7-8B model and 8K context is enough?** → Q6_K (better quality, if available)
4. **Is it a 3-4B model?** → Q8_0 (why not? It fits easily)
5. **Is speed critical (autocomplete, classification)?** → Smaller model + higher quant > larger model + lower quant

> **Note:** Not all quantizations are available for every model on Ollama. Qwen3 only offers Q4_K_M, Q8_0, and FP16. Llama 3.1 offers the full range including Q5_K_M. Always check the model's tags page before assuming a quant exists.
