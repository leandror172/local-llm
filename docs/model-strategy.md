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
| **Coding** | Qwen3-8B | Q5_K_M | ~6.3 GB | 16K | Outperforms Qwen2.5-14B on coding benchmarks. Direct upgrade from current Qwen2.5-Coder-7B |
| **Heavy reasoning** | Qwen3-14B | Q4_K_M | ~8.9 GB | 4K | Architecture decisions, complex analysis. Short context is fine for reasoning tasks |
| **Classification / routing** | Qwen3-4B or Phi-4-mini | Q8_0 | ~3 GB | 4K | Fast, cheap. Good enough for "is this a coding question or a general question?" |

### Tier 2: Specialized (pull when building specific layers)

| Role | Model | Quant | VRAM | When needed | Notes |
|------|-------|-------|------|-------------|-------|
| **General / writing** | Llama-3.1-8B-Instruct | Q5_K_M | ~6.3 GB | Layer 3 (personas) | Broader training than code-focused models. Better for career coaching, general writing |
| **Embeddings (RAG)** | nomic-embed-text | native | ~275 MB | Layer 7 (memory) | Runs alongside main model. Required for vector search |
| **Translation (PT-BR)** | Needs research | TBD | TBD | Layer 3/8 | Quality critical. May need frontier for nuanced PT-BR. Research during Layer 3 |

### Tier 3: Experimental (test when exploring)

| Role | Model | Quant | VRAM | Notes |
|------|-------|-------|------|-------|
| **Alternative coder** | DeepSeek-Coder-V2-Lite (MoE) | Q4_K_M | ~4 GB | 16B total, 2.4B active. Fast, good quality |
| **Reasoning specialist** | DeepSeek-R1-Distill-Qwen-14B | Q4_K_M | ~8.9 GB | Chain-of-thought reasoning. Good for evaluator role |
| **Fast code** | Mamba-Codestral-7B | Q5_K_M | ~4.8 GB | SSM architecture, 1.5-2x faster than transformer. Good for autocomplete |

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

| Model | On-disk size | Cumulative |
|-------|-------------|------------|
| Qwen2.5-Coder-7B (existing) | 4.7 GB | 4.7 GB |
| Qwen3-8B Q5_K_M | ~5.5 GB | 10.2 GB |
| Qwen3-14B Q4_K_M | ~8.5 GB | 18.7 GB |
| Qwen3-4B Q8_0 | ~4.0 GB | 22.7 GB |
| Llama-3.1-8B Q5_K_M | ~5.5 GB | 28.2 GB |
| nomic-embed-text | ~275 MB | 28.5 GB |
| DeepSeek-R1-Distill-14B Q4_K_M | ~8.5 GB | 37.0 GB |

**Available:** I: drive has 562 GB free. Disk is not a constraint.

---

## Upgrade Path

### Immediate (Layer 0)
```bash
ollama pull qwen3:8b        # ~5.5 GB download
ollama pull qwen3:14b       # ~8.5 GB download
ollama pull qwen3:4b        # ~4.0 GB download (or phi4-mini when available)
```

### When building Layer 7 (Memory)
```bash
ollama pull nomic-embed-text
```

### When building Layer 3 (Personas)
```bash
ollama pull llama3.1:8b
# Research and pull best PT-BR translation model
```

---

## Quantization Decision Guide

When choosing quantization for a new model:

1. **Is it a 14B+ model?** → Q4_K_M (only option that fits 12GB)
2. **Is it a 7-8B model and you need max context (16K)?** → Q5_K_M
3. **Is it a 7-8B model and 8K context is enough?** → Q6_K (better quality)
4. **Is it a 3-4B model?** → Q8_0 (why not? It fits easily)
5. **Is speed critical (autocomplete, classification)?** → Smaller model + higher quant > larger model + lower quant
