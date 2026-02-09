# Key Concepts: The Local LLM Ecosystem

A reference guide for foundational concepts in running LLMs locally.

---

## HuggingFace

Think of HuggingFace as the **GitHub of AI**. It's a platform (huggingface.co) where researchers and companies publish:

- **Model weights** — the actual files that make a model work (like downloading a .zip of a program)
- **Datasets** — training data used to create models
- **Papers and model cards** — documentation explaining how a model was trained and what it's good at

When Meta releases Llama, or Alibaba releases Qwen, or Mistral releases Codestral — they upload the weights to HuggingFace. It's the central distribution point. Ollama's registry is a *curated subset* of what's on HuggingFace — they take popular models, package them into an easy `ollama pull` format, and host them. But HuggingFace has far more models and variants than Ollama offers.

To get a model that isn't on Ollama's registry: go to huggingface.co, search for the model, and download the weight file directly — bypassing Ollama's registry.

---

## GGUF (GPT-Generated Unified Format)

GGUF is a **file format for model weights**, created by the [llama.cpp](https://github.com/ggerganov/llama.cpp) project.

### The problem it solves

When a research lab trains a model, they produce weights in formats like PyTorch (`.pt`) or SafeTensors (`.safetensors`). These are huge — a 7B model is ~14 GB in full precision (FP16). They're also designed for GPUs with 80 GB of VRAM in data centers.

GGUF solves the consumer hardware problem:

- It stores **quantized** weights (the Q4_K_M, Q8_0, etc.) — compressed to fit in 12 GB of VRAM
- It's optimized for **CPU+GPU inference** on consumer hardware
- It bundles everything into a **single file** — weights, tokenizer, metadata — instead of scattered files

### How it relates to Ollama

**Ollama uses GGUF internally.** When you do `ollama pull qwen3:8b`, it downloads a GGUF file and stores it in `~/.ollama/models/`. The Ollama registry is essentially a collection of pre-made GGUF files with nice tag names.

When a model isn't on Ollama's registry, you can:

1. Find the GGUF file on HuggingFace (community members often quantize popular models and upload them)
2. Download it manually
3. Import it with `ollama create my-model -f Modelfile` where the Modelfile points to the GGUF

---

## SSM Architecture (State Space Models)

Every LLM you've likely encountered — GPT, Claude, Qwen, Llama — is built on the **Transformer** architecture. SSM is a fundamentally different approach.

### The Transformer problem

Transformers use "attention" — every token looks at every other token in the context window. This is powerful (it's why they're so good), but it has a cost: processing time grows **quadratically** with context length. 1,000 tokens = 1 million attention comparisons. 10,000 tokens = 100 million. This is why long contexts are expensive.

### How SSMs differ

Instead of every token looking at every other token, SSMs process tokens **sequentially through a compressed state** — like a summary that gets updated with each new token.

Analogy: imagine reading a book and keeping a running mental summary, versus re-reading the entire book for every new sentence. The mental summary approach is SSM; the re-reading approach is Transformer attention.

### Practical impact

| Dimension | SSM | Transformer |
|-----------|-----|-------------|
| **Generation speed** | 1.5-2x faster | Baseline |
| **VRAM for long contexts** | Lower (state is fixed size) | Higher (grows with context) |
| **Long-context fidelity** | Can "forget" early details (lossy state) | Can always look back (full attention) |
| **Best for** | Code completion, autocomplete, classification | Complex reasoning, multi-file analysis |

### Key models

- **Mamba** — the most well-known SSM architecture, created by Albert Gu and Tri Dao
- **Codestral-Mamba** — Mistral's code-specialized SSM, 7B params, 1.5-2x faster than equivalent Transformers
- **Jamba** (AI21) — hybrid architecture combining Transformer + Mamba layers, aiming for best of both worlds

### Where the field is heading

There's active research into hybrid architectures that combine Transformer attention (for precision) with SSM layers (for speed). The field hasn't settled yet. For now, Transformers dominate, SSMs are a promising niche for speed-critical tasks, and hybrids are emerging.

---

## How these concepts connect

```
HuggingFace (distribution platform)
  │
  ├── Hosts model weights in various formats
  │     ├── PyTorch (.pt)         — for training/research
  │     ├── SafeTensors (.safetensors) — safer PyTorch alternative
  │     └── GGUF (.gguf)          — for local inference (consumer GPUs)
  │
  ├── Models use different architectures
  │     ├── Transformer           — Qwen, Llama, GPT, Mistral
  │     ├── SSM (Mamba)           — Codestral-Mamba
  │     └── Hybrid                — Jamba (Transformer + Mamba)
  │
  └── Ollama registry (curated subset)
        ├── Pre-packaged GGUF files with easy tags
        ├── `ollama pull model:tag` — simple download
        └── Limited selection — not every model/quant available
```

### Relevance to this project

- **Classification and routing** (Layers 0/1): speed matters more than depth — SSMs would excel here
- **Architecture reasoning** (Layers 3/8): deep context awareness needed — Transformers win
- **Model strategy** already reflects this split: small fast models for classification, larger Transformers for reasoning. SSMs would be a third axis — same quality as a Transformer of similar size, but faster, at the cost of long-context fidelity
- **When Ollama doesn't have a model you want:** search HuggingFace for the GGUF, download, and import via `ollama create`

---

*Last updated: 2026-02-08*
