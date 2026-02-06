# Closing the Gap: Local 7B Models vs Frontier Models

A practical guide to maximizing output quality from Qwen2.5-Coder-7B (and successors) on an RTX 3060 12GB, benchmarked against Claude Opus 4.6.

**Context:** See [model-comparison-hello-world.md](model-comparison-hello-world.md) for the baseline comparison that motivated this analysis.

---

## Priority Matrix: Where to Start

Ranked by impact-to-effort ratio. Start from the top.

| # | Technique | Effort | Impact | Category |
|---|-----------|--------|--------|----------|
| 1 | Upgrade to Qwen3-8B (Q5_K_M) | 5 min | High | Model Selection |
| 2 | Structured system prompts (skeleton format) | 30 min | High | System Prompts |
| 3 | One-task-per-prompt decomposition | Immediate | High | Prompt Engineering |
| 4 | Few-shot examples (1-3 per task) | 10 min/task | High | Prompt Engineering |
| 5 | Lower temperature (0.1) for code tasks | 1 min | Medium | Prompt Engineering |
| 6 | Structured output (JSON schema) | 1 hour | Medium-High | Inference-Time |
| 7 | Manual context injection ("poor man's RAG") | Immediate | High | RAG |
| 8 | Continue.dev with `@codebase` | 1-2 hours | Very High | RAG |
| 9 | Multi-model routing (RouteLLM) | Half day | Very High | Routing |
| 10 | Best-of-3 sampling for important outputs | Half day | Medium-High | Inference-Time |
| 11 | Try Qwen3-14B Q4_K_M for complex tasks | 10 min | High | Model Selection |
| 12 | Full RAG pipeline (embeddings + vector DB) | 1-2 days | Very High | RAG |
| 13 | QLoRA fine-tuning on your codebase | 2-3 days | High | Fine-Tuning |
| 14 | Self-refinement loops | 1 day | Medium | Inference-Time |

---

## 1. Prompt Engineering for Small Models

Small models don't reward clever prompts — they reward **clear contracts**.

### 1A. One Prompt, One Job

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy | High | Yes |

7B models lose coherence juggling multiple objectives. Break complex requests into chained single-purpose calls.

**Bad:** "Analyze this function for bugs, performance issues, and style problems, then suggest fixes."

**Good:** Three separate calls:
1. "List any bugs in this function. Output only bugs, one per line."
2. "List performance issues in this function. Output only issues, one per line."
3. "Given these bugs: [X] and these performance issues: [Y], suggest fixes as a numbered list."

### 1B. Context Injection (Fact Grounding)

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy | High | Yes |

7B models hallucinate more than frontier models. Counter by injecting facts as labeled blocks:

```
FACTS (use only these):
- This project uses Spring Boot 3.2 with Java 21
- The database is PostgreSQL 16
- We use Flyway for migrations

TASK: Generate a migration script to add a "status" column to the "orders" table.
```

Adding "use only these facts" or "do not fabricate information not present in the provided context" measurably reduces hallucination.

### 1C. Few-Shot Examples (1-3, Not More)

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy | High | Yes |

Include 1-3 concrete input/output examples. Even 1 shot significantly improves small model accuracy. More than 3 wastes context tokens and can distract the model.

### 1D. Chain-of-Thought (Explicit Step Forcing)

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy | Medium-High | Yes |

Give the model a numbered scaffold instead of open-ended "think step by step":

```
Solve this step by step:
Step 1: Identify the input types
Step 2: Determine the return type
Step 3: Write the function signature
Step 4: Implement the logic
Step 5: Output only the final code
```

### 1E. Lower Temperature for Code

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy | Medium | Yes |

For code generation, `temperature: 0.1` with `top_p: 0.9` produces the most consistent results on 7B models. Our current Modelfile uses 0.3 — consider lowering for pure code tasks.

```bash
# Per-request override (doesn't change the Modelfile default)
curl http://localhost:11434/api/chat -d '{
  "model": "my-coder",
  "messages": [...],
  "options": {"temperature": 0.1}
}'
```

---

## 2. System Prompt Optimization

### Key Difference: 7B vs Frontier

Frontier models handle natural language paragraphs. 7B models need **structured, concise, constraint-focused** prompts. Verbose templates that help large models actually hurt small model performance.

### 2A. The Skeleton Format

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy | Medium-High | Yes |

```
ROLE: You are a backend code generator for Java 21 and Go 1.22 projects.
CONSTRAINTS:
- MUST output only code unless explicitly asked for explanation
- MUST include error handling in every function
- MUST NOT invent library imports that were not mentioned in context
- MUST NOT add comments unless asked
FORMAT: Output code in a single fenced code block with the language identifier.
```

### 2B. Eliminate Ambiguity

Replace soft language with hard constraints:
- "Try to keep responses concise" → "Maximum 200 tokens per response"
- "You should format as JSON" → "Output valid JSON only. No text before or after the JSON."
- "Consider edge cases" → "MUST handle: null input, empty string, negative numbers"

### 2C. Keep It Short

Stay under 200 tokens. Move task-specific instructions to the user message — attention mechanisms in small models weight nearby tokens more heavily.

---

## 3. Model Selection

### Best Options for RTX 3060 12GB

#### 7B Class (comfortable fit, full context)

| Model | Strength | VRAM (Q4_K_M) | Speed |
|-------|----------|----------------|-------|
| Qwen2.5-Coder-7B | Current model. Solid baseline | ~4.1 GB | 40-60 t/s |
| **Qwen3-8B** | Outperforms Qwen2.5-14B on coding | ~4.5 GB | 40-55 t/s |
| Mamba-Codestral-7B | 1.5-2x faster (SSM architecture) | ~4.1 GB | 60-90 t/s |
| DeepSeek-Coder-V2-Lite (16B MoE) | MoE, only 2.4B active params | ~4 GB | 50+ t/s |

#### 14B Class (tight fit, reduced context)

| Model | Strength | VRAM (Q4_K_M) | Context Limit |
|-------|----------|----------------|---------------|
| **Qwen3-14B** | Rivals Qwen2.5-32B quality | ~7.9 GB | ~4K on 12GB |
| Qwen3-Coder-14B | Code-specialized, agentic | ~7.9 GB | ~4K on 12GB |
| DeepSeek-R1-Distill-Qwen-14B | Strong reasoning/CoT | ~7.9 GB | ~4K on 12GB |
| Phi-4 (14B) | Excellent code + reasoning | ~7.9 GB | ~4K on 12GB |

**Recommended immediate upgrade:** `ollama pull qwen3:8b` — Qwen3-8B outperforms Qwen2.5-14B on most coding benchmarks, with the same VRAM footprint as our current model.

### Quantization Tradeoffs

| Quant | VRAM (7B) | VRAM (14B) | Quality Loss | Recommendation |
|-------|-----------|------------|--------------|----------------|
| Q8_0 | 7.0 GB | 13.0 GB | <5% | Best quality. 14B does NOT fit 12GB |
| Q6_K | 5.5 GB | 10.5 GB | ~5% | Sweet spot for 7B |
| **Q5_K_M** | **4.8 GB** | 9.1 GB | 5-15% | **Best balance for 7B on our hardware** |
| Q4_K_M | 4.1 GB | 7.9 GB | 5-15% | Required for 14B to fit |
| Q3_K_M | 3.3 GB | 6.3 GB | 15-30% | Avoid for code generation |

---

## 4. Fine-Tuning (QLoRA on Consumer Hardware)

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Medium | High (for specific tasks) | Yes (7B via QLoRA) |

QLoRA loads the base model in 4-bit and trains small adapter layers. A 7B model needs ~8-10 GB VRAM — fits within 12GB.

### Recommended Tool: Unsloth

[Unsloth](https://github.com/unslothai/unsloth) — 2.5x faster than HuggingFace, 70% less VRAM, direct GGUF export for Ollama.

### Workflow

```
1. Start with an instruct model (e.g., Qwen3-8B-Instruct)
2. Prepare dataset in ChatML/ShareGPT format
3. Fine-tune with Unsloth QLoRA
4. Export to GGUF
5. Import into Ollama with a custom Modelfile
```

### Best Datasets for Code

| Type | Source | Impact |
|------|--------|--------|
| **Your own codebase** | Function-docstring pairs from Java/Go projects | High |
| Code instructions | HuggingFace: `CodeAlpaca-20k` | Medium |
| Bug fix pairs | Git history: buggy commit → fix commit | High |
| Code reviews | PR history | Medium |

**Key insight:** 500-2000 high-quality examples from your own codebase outperform 100K generic examples. Quality > quantity.

---

## 5. RAG (Retrieval Augmented Generation)

### 5A. Manual Context Injection (Start Here)

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy | High | Yes |

Before investing in infrastructure, manually inject relevant code:

```
Here is the existing interface:
[paste interface]

Here is the existing service:
[paste service]

TASK: Add a method to cancel an order. Follow the existing patterns exactly.
```

Retrieval accuracy boosts code generation accuracy by ~37%.

### 5B. Continue.dev with @codebase

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Medium | Very High | Yes |

[Continue.dev](https://docs.continue.dev/guides/custom-code-rag) — VS Code / JetBrains extension with built-in `@codebase` context that indexes your project. Supports Ollama as backend.

### 5C. Full RAG Pipeline

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Medium-Hard | Very High | Yes |

- **Embedding model:** `nomic-embed-text` via Ollama (~275MB VRAM)
- **Vector store:** Qdrant (Docker) or ChromaDB (in-process)
- **Chunking:** AST-aware (split by function/class, not line count)
- **Framework:** LangChain or LlamaIndex (both support Ollama)

---

## 6. Multi-Model Routing

### 6A. RouteLLM (Local + Cloud Hybrid)

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Medium | Very High | Yes |

[RouteLLM](https://github.com/lm-sys/RouteLLM) routes simple queries to local Ollama, complex ones to a cloud API. Drop-in OpenAI client replacement.

```python
from routellm.controller import Controller

client = Controller(
    routers=["mf"],
    strong_model="claude-3-5-sonnet",     # frontier (paid)
    weak_model="ollama_chat/qwen3:8b",    # local (free)
)
```

Default threshold achieves ~50% local routing while maintaining ~95% of frontier quality. Up to 85% API cost reduction.

### 6B. Cascade Pattern (Try Local First)

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy-Medium | High | Yes |

1. Send every query to local model first
2. Score the response (syntax check, format validation, confidence heuristic)
3. If score is low, re-send to cloud API

Simpler than RouteLLM, no pre-trained router needed.

---

## 7. Inference-Time Techniques

### 7A. Structured Output (JSON Schema)

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy | Medium-High | Yes |

Ollama supports grammar-based constrained decoding — invalid tokens are masked during sampling:

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "my-coder",
  "messages": [{"role": "user", "content": "Analyze this function for bugs"}],
  "format": {
    "type": "object",
    "properties": {
      "bugs": {"type": "array", "items": {"type": "string"}},
      "severity": {"type": "string", "enum": ["low", "medium", "high"]},
      "fix_suggestion": {"type": "string"}
    },
    "required": ["bugs", "severity", "fix_suggestion"]
  }
}'
```

### 7B. Best-of-N Sampling

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Easy-Medium | Medium-High | Yes |

Generate 3-5 candidates with `temperature: 0.6`, select the best via:
- Does it parse/compile?
- Does it pass type checking?
- Do test cases pass?

At 64 tok/s, 3 candidates for a 200-token function takes ~10-15 seconds.

### 7C. Self-Refinement Loop

| Difficulty | Impact | RTX 3060 |
|------------|--------|----------|
| Medium | Medium | Yes |

```
Pass 1: Generate code
Pass 2: "Review this code for bugs and issues: [code from pass 1]"
Pass 3: "Fix these issues in the code: [issues from pass 2]"
```

Target the repair prompt narrowly — "fix these specific issues" not "improve the code."

---

## The Honest Assessment

**Where 7B models will NOT match frontier quality** (even with all techniques):
- Complex multi-file refactoring
- Architectural reasoning across large codebases
- Novel algorithm design
- Ambiguous natural language understanding

**Where 7B models CAN approach frontier quality:**
- Single-function code generation with clear specs
- Code completion within known patterns
- Boilerplate generation (CRUD, tests, DTOs)
- Formatting and transformation tasks
- Simple bug identification in short functions
- Generating code that follows provided examples

**The pragmatic answer:** Multi-model routing (#6). Use local for the 60-70% of tasks it handles well, route the rest to a frontier API. Speed + privacy + low cost for routine work, frontier quality on demand.

---

## Going Deeper

To explore any technique in detail:
1. Pick a technique from the priority matrix
2. Create a new Modelfile variant to test it (e.g., `modelfiles/structured-coder.Modelfile` with skeleton-format system prompt)
3. Run the same prompt through both variants and compare
4. Document results in `docs/` using the format from [model-comparison-hello-world.md](model-comparison-hello-world.md)

Suggested first experiments:
- **Experiment 1:** Swap Qwen2.5-Coder-7B for Qwen3-8B Q5_K_M. Re-run the hello world comparison.
- **Experiment 2:** Rewrite the system prompt in skeleton format. Compare output quality.
- **Experiment 3:** Add a 1-shot example to the prompt. Compare with zero-shot.

---

## Sources

- [Practical Prompt Engineering for Smaller LLMs](https://web.dev/articles/practical-prompt-engineering)
- [Getting High-Quality Output from 7B Models](https://dev.to/superorange0707/getting-high-quality-output-from-7b-models-a-production-grade-prompting-playbook-21hi)
- [Optimizing LLMs: Prompt Engineering Techniques (MDPI)](https://www.mdpi.com/2076-3417/15/3/1430)
- [AI Quantization Guide (Local AI Zone)](https://local-ai-zone.github.io/guides/what-is-ai-quantization-q4-k-m-q8-gguf-guide-2025.html)
- [Qwen3 Technical Report (arXiv)](https://arxiv.org/pdf/2505.09388)
- [Unsloth GitHub](https://github.com/unslothai/unsloth)
- [Fine-Tuning on RTX GPUs (NVIDIA Blog)](https://blogs.nvidia.com/blog/rtx-ai-garage-fine-tuning-unsloth-dgx-spark/)
- [RAG for Large-Scale Codebases (Qodo)](https://www.qodo.ai/blog/rag-for-large-scale-code-repos/)
- [Continue.dev Custom Code RAG](https://docs.continue.dev/guides/custom-code-rag)
- [RouteLLM (GitHub)](https://github.com/lm-sys/RouteLLM)
- [Structured Outputs (Ollama Docs)](https://docs.ollama.com/capabilities/structured-outputs)
- [Scalable Best-of-N Selection (arXiv)](https://arxiv.org/html/2502.18581v1)
