# Modelfile Reference: coding-assistant

Configuration rationale for `modelfiles/coding-assistant.Modelfile`, which defines the `my-coder` custom model.

## Settings Overview

| Setting | Value | Purpose |
|---------|-------|---------|
| `FROM` | qwen2.5-coder:7b | Base model weights (4.7GB, Q4_K_M quantization) |
| `num_ctx` | 16384 | 16K context window — fits full source files with room for response. Costs ~1-2GB extra VRAM over default 2048. |
| `temperature` | 0.3 | Low randomness for precise code generation. High enough to suggest alternatives, low enough for correct syntax. |
| `top_p` | 0.9 | Nucleus sampling — prunes the bottom 10% of unlikely tokens entirely. Works with temperature as a two-stage funnel. |
| `repeat_penalty` | 1.1 | Gentle repetition penalty. Prevents degenerate loops without breaking natural code patterns like repeated keywords. |
| `stop` | `<\|im_end\|>`, `<\|endoftext\|>` | Qwen2.5's native ChatML end-of-turn markers. Ensures clean response termination. |
| `SYSTEM` | Java/Go backend expert | Persona: SOLID principles, idiomatic code, production-ready, explains reasoning, markdown code blocks. |

## Design Decisions

**Why 16K context and not 32K or higher?**
With 12GB VRAM and ~4.9GB used by model weights, 16K is the sweet spot. Each doubling of context window adds ~0.5-1GB VRAM at 7B scale. 16K fits a full Java class or Go file comfortably. Going to 32K would work but leaves less headroom.

**Why temperature 0.3 and not 0.0?**
Zero temperature is fully deterministic — it always picks the single most likely token. While appealing for code, it can get stuck in local optima (e.g., always generating the same boilerplate pattern when a different approach fits better). 0.3 adds just enough variation to explore alternatives.

**Why both temperature and top-p?**
They operate at different stages. Temperature reshapes the probability curve (applied to logits before softmax). Top-p prunes the tail (applied to probabilities after softmax). See [sampling-parameters.md](sampling-parameters.md) for a visual explanation.

**Why a short system prompt?**
7B parameter models follow short, direct instructions more reliably than long, nuanced ones. Six concise lines perform better than a page of detailed rules. Larger models (14B+) can handle more complex system prompts.

## Creating Additional Personas

The same base model can serve multiple roles. Create a new Modelfile with a different system prompt and register it:

```bash
ollama create my-frontend  -f modelfiles/frontend-dev.Modelfile
ollama create my-architect  -f modelfiles/architect.Modelfile
```

All personas share the same base weights on disk — only the configuration layer differs.
