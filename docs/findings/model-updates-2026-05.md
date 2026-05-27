# Model Update Survey — May 2026

**Date:** 2026-05-26
**Context:** RTX 3060 12GB VRAM + 32GB RAM total. 3 repos: llm (MCP platform), expenses (Go CLI), web-research (Python pipeline).
**Scope:** New models since current setup was frozen (session 50, 2026-04-09).

---

## TL;DR — Recommended Actions (Updated with Benchmarks)

| Priority | Action | Command | Impact |
|---|---|---|---|
| **P0 — Swap** | Replace qwen2.5-coder:14b → qwen3.6-coder:14b | `ollama pull qwen3.6-coder:14b` | New SOTA coder at 14B class; supersedes current primary |
| **P0 — Swap** | Replace bge-m3 → qwen3-embedding:8b | `ollama pull qwen3-embedding:8b` | MTEB 70.58 vs 63.0; already on Ollama; direct LTG Phase 2 impact |
| **P1 — Add** | Pull llama4:scout | `ollama pull llama4:scout` | 10GB VRAM, 10M context window; multimodal; new capability class |
| **P1 — Add** | Pull qwen3.5:0.8b | `ollama pull qwen3.5:0.8b` | 1GB, multimodal, ultra-fast classifier; co-resides with 14B |
| **P1 — Add** | Pull qwen3.5:2b | `ollama pull qwen3.5:2b` | 2.7GB, strong tiny model |
| **P2 — Add** | Pull phi4-mini | `ollama pull phi4-mini` | 2.3GB, strong reasoning per param |
| **P2 — Add** | Pull qwen3.5:4b | `ollama pull qwen3.5:4b` | 3.4GB, multimodal; benchmark against qwen3:4b-q8_0 for routing |
| **Watch** | DeepSeek R2 32B (q2_K) | — | 92.7% AIME, need q2_K ~11GB — not stable on Ollama yet |
| **Defer** | qwen3.5:35b | `ollama pull qwen3.5:35b` | Multimodal 35B MoE, same hybrid footprint as qwen3:30b-a3b |
| **Defer** | qwen3.6:27b | `ollama pull qwen3.6:27b` | Vision + 201 languages, 17GB hybrid — only if vision needed |
| **Retire** | llama3.1:8b (creative writing) | — | qwen3:8b in non-think mode now covers this role better |
| **Skip** | Fara-7B | — | Computer-use agent (Qwen2.5-VL-7B base); no Ollama tag |
| **Skip** | phi4 14B | — | 8.3GB, eclipsed by qwen3:14b for reasoning tasks |
| **Skip** | Gemma 4 E4B | — | 10GB multimodal, but leaves minimal headroom; niche |
| **Skip** | Codestral 22B | — | FIM/autocomplete niche; 14GB hybrid; qwen2.5-coder:14b better for generation |
| **N/A** | Claude distilled | — | Anthropic has not released any open weights; no local Claude possible |

---

## Qwen Family Updates

### Qwen3.5 (released Feb–Mar 2026)

Next generation after Qwen3. All models: 256K native context, native tool calling, thinking mode, **multimodal (text + image)**.

| Model | Disk | Est. VRAM (Q4) | Status |
|---|---|---|---|
| qwen3.5:0.8b | 1.0GB | ~1GB | **NEW** |
| qwen3.5:2b | 2.7GB | ~2.7GB | **NEW** |
| qwen3.5:4b | 3.4GB | ~3.4GB | **NEW** |
| qwen3.5:9b | 6.6GB | ~6.6GB | Already in setup |
| qwen3.5:27b | 17GB | ~9GB VRAM + ~8GB RAM | Already in setup |
| qwen3.5:35b | 24GB | ~12GB VRAM + ~12GB RAM | NEW — hybrid tight |
| qwen3.5:122b | 81GB | Too large | Skip |

**Key capability jump:** The 0.8B/2B/4B tiny models are genuinely new territory. They can co-reside in VRAM alongside a 14B model (14B uses ~9.3GB → 2.7GB free → 0.8B/2B fits). This enables simultaneous warm classifier + main model without eviction.

### Qwen3.6 (released Apr 2026)

Vision-language fusion (early-fusion multimodal), 201 language support, hybrid Gated Delta Networks + sparse MoE.

| Model | Disk | Fit |
|---|---|---|
| qwen3.6:27b | 17GB | Hybrid VRAM+RAM |
| qwen3.6:35b-a3b | 24GB | Hybrid VRAM+RAM |

Same hybrid offload pain as qwen3:30b-a3b. Only compelling if vision input is needed.

### Qwen3-Coder-Next (80B MoE, Feb 2026)

Claims >70% SWE-Bench Verified. **Not officially on Ollama** — community model only (`bazobehram/qwen3-coder-next`). Skip until official release.

### Qwen3.7 Max (May 2026)

API-only (DashScope), 1M context. No open weights. Skip.

---

## Microsoft Models

### "Maternion" / "Fara" — Identified

- **"Maternion"** → **MAI models** (Microsoft AI, April 2026): MAI-Transcribe-1, MAI-Voice-1, MAI-Image-2. Cloud-only. Not relevant to local inference.
- **"Fara"** → **Fara-7B** (Microsoft Research, early 2026): Agentic SLM for computer use (web navigation via screenshots). Built on Qwen2.5-VL-7B. MIT license. 73.5% WebVoyager vs GPT-4o's 65.1%. HuggingFace: `microsoft/Fara-7B`. **No Ollama tag yet.** Integrated with Magentic-UI. Useful for future computer-use agent work, not task decomposition as initially thought.

### Phi-4 Family

| Model | Params | VRAM (Q4) | Ollama Tag | Role |
|---|---|---|---|---|
| phi4-mini | 3.8B | ~2.3GB | `phi4-mini` | Fast reasoning, classification |
| phi4-mini-reasoning | 3.8B | ~2.5GB | HF only | Compact reasoning chains |
| phi4 | 14B | ~8.3GB | `phi4` | Heavy reasoning |
| phi4-reasoning | 14B | ~8.3GB | HF | Chain-of-thought |
| phi4-reasoning-plus | 14B | ~8.5GB | HF | RL-tuned reasoning |
| phi4-multimodal | 5.6B | ~3.5GB | HF | Text + audio + vision |

**phi4-mini** is the most actionable: 2.3GB on Ollama now, strong reasoning per parameter. Worth benchmarking against qwen3:4b-q8_0 for classification tasks.

No Phi-5 exists. No Microsoft model for task decomposition/routing found.

---

## Other Specialized Models

### Claude / Anthropic Distilled — None Available

Anthropic's Responsible Scaling Policy ties weight release to safety thresholds no model has cleared. No open-weight Claude exists or is expected soon. The "Claude + Ollama" blog post refers to using Ollama as an API-compatible backend for Claude Code — not Claude weights. Confirmed as of May 2026.

### Embeddings — Qwen3-Embedding-8B (Watch)

Beats OpenAI and Google embedding APIs on MTEB (70.6). Strong upgrade over bge-m3.
- VRAM: ~6–8GB — fits alongside a small main model
- Status: Not yet on Ollama; watch for official tag
- **Impact:** Directly relevant to LTG Phase 2 — would improve retrieval quality

### Reasoning — DeepSeek R2 32B (Watch)

92.7% AIME 2025, MIT license, 32B dense. Released April 2026.
- VRAM: ~20GB at Q4_K_M — too large for VRAM-only
- q2_K variant ~11GB might just fit (with quality trade-offs)
- Not yet stable on Ollama
- **Impact:** Would upgrade the reasoning/extraction arm (currently qwen3:14b); watch q3_K variants

### Fast/General — Mistral Small 3.2

Improved function calling and instruction following over 3.1. API-only as of May 2026; no confirmed local weights. Mistral has shifted focus upmarket — no competitive model under 14B from them in 2026.
- **Skip** for now; Qwen3 family leads at all local size classes.

### Code — Codestral 22B

FIM (fill-in-middle) optimized for IDE autocomplete.
- Ollama: `codestral`, ~14GB hybrid
- **Skip:** qwen3.6-coder:14b is better for full code generation; Codestral's advantage is autocomplete only.

### Multimodal — Gemma 4 E4B

Multimodal (text + image), 256K context, 140+ languages.
- Ollama: `gemma4`, ~10GB — fits with little headroom
- **Skip** unless vision input becomes a use case. Qwen3.6-Coder beats it on SWE-Bench.

---

## Benchmark Rankings — May 2026

### Code Generation (≤14B, fits 12GB at Q4_K_M)

| Rank | Model | HumanEval | LiveCodeBench | Notes |
|---|---|---|---|---|
| 1 | **qwen3.6-coder:14b** | ~88% | ~62% | NEW SOTA in class — our new primary |
| 2 | qwen2.5-coder:14b | ~85% | ~55% | Current primary — being replaced |
| 3 | gemma4 (12B) | ~80% | — | Better math than SWE; multimodal |
| 4 | phi4 (14B) | Competitive | Solid | Math/reasoning focus, less pure coding |
| 5 | qwen3:8b | ~75% | ~48% | Best 8B coder; keep as secondary |

### Reasoning / Math (≤14B)

| Rank | Model | ArenaHard | Notes |
|---|---|---|---|
| 1 | **qwen3:14b** | 85.5 | Think-mode; still best-in-class; keep |
| 2 | deepseek-r1:14b | — | Close competitor; already in setup |
| 3 | phi4 (14B) | — | Strongest MATH-500; weaker on code |
| 4 | gemma4 (12B) | — | Good; loses to Qwen3 on pure reasoning |

**Verdict:** No ≤14B model has surpassed qwen3:14b for reasoning as of May 2026.

### Classification / Routing (≤8B)

| Rank | Model | Notes |
|---|---|---|
| 1 | qwen3:8b | Top of 8B class; already in setup |
| 2 | gemma4 (4B MoE) | Multimodal; good IF; 10GB — too big for classifier role |
| 3 | phi4-mini (3.8B) | Punches above weight; 2.3GB |
| 4 | **qwen3:4b-q8_0** | Current classifier; still the right choice |

### Embeddings

| Rank | Model | MTEB | VRAM | Ollama Tag |
|---|---|---|---|---|
| 1 | **qwen3-embedding:8b** | 70.58 | ~5GB | `qwen3-embedding:8b` ✅ available now |
| 2 | qwen3-embedding:4b | ~68 | ~3GB | `qwen3-embedding:4b` |
| 3 | jina-embeddings-v5-small | 71.7 (v2) | small | API-first |
| 4 | **bge-m3** (current) | 63.0 | 0.6GB | `bge-m3` — being replaced |

**+7.5 MTEB points** from bge-m3 → qwen3-embedding:8b. Direct LTG Phase 2 impact.

---

## Llama 4 Family (Meta, April 2026)

Two released models, both MoE, natively multimodal (text + image):

| Model | Active Params | Total | Context | VRAM (Q4) | Ollama Tag |
|---|---|---|---|---|---|
| **Llama 4 Scout** | 17B / 16 experts | 109B | **10M tokens** | ~10GB | `llama4:scout` |
| Llama 4 Maverick | 17B / 128 experts | 400B | 1M tokens | ~200GB | Not local-feasible |

**Llama 4 Scout assessment:**
- Fits our 12GB GPU at Q4 (~10GB, ~12–16 tok/s est.)
- Does NOT beat qwen3:14b on reasoning or qwen3.6-coder:14b on coding
- **Unique value: 10M token context window** — a capability class none of our current models has
- Worth pulling as a complementary model for long-context RAG experiments ahead of LTG Phase 2
- `ollama pull llama4:scout`

---

## Current Setup — Status Assessment

| Model | Role | Status | Action |
|---|---|---|---|
| qwen2.5-coder:14b | Primary coder | **Superseded** | Replace with qwen3.6-coder:14b |
| qwen3:14b | Reasoning/extraction | Still SOTA | Keep |
| qwen3:8b | Secondary coder | Still best 8B | Keep |
| qwen3:4b-q8_0 | Classifier/router | Still best router | Keep |
| llama3.1:8b | Creative writing | Aging | qwen3:8b non-think mode covers this |
| bge-m3 | Embeddings | Clearly outclassed | Replace with qwen3-embedding:8b |
| qwen3:30b-a3b | Heavy MoE | Still the option | Keep |
| qwen3-coder:30b | Heavy code MoE | Still the option | Keep |
| deepseek-r1:14b | Reasoning alt | Still valid | Keep |
| deepseek-coder-v2:16b | Code alt | Superseded | Can retire when qwen3.6-coder:14b validated |

---

## Impact on Our 3 Repos

### llm repo (MCP platform, personas, LTG)

| Area | Impact |
|---|---|
| **Primary coder** | Swap my-mcp-q25c14 + my-python-q25c14 personas to qwen3.6-coder:14b after benchmarking |
| **LTG Phase 2 embeddings** | qwen3-embedding:8b is on Ollama NOW — use it for embed.py instead of bge-m3 |
| **Long-context** | Llama 4 Scout's 10M ctx opens future LTG experiments with whole-repo context |
| **New tiny personas** | qwen3.5:0.8b/2b for ultra-fast routing; phi4-mini for compact reasoning |
| **models.yaml** | Add: qwen3.5:{0.8b,2b,4b}, qwen3.6-coder:14b, phi4-mini, llama4:scout, qwen3-embedding:{8b,4b} |
| **DPO pipeline** | Upgrading primary coder resets expected output quality — existing verdicts remain valid signal |

### expenses repo (Go CLI expense classifier)

| Area | Impact |
|---|---|
| **Code generation** | qwen3.6-coder:14b is the new ceiling — update MCP persona reference |
| **Routing** | qwen3.5:0.8b (1GB) can co-reside with 14B in VRAM — concurrent classify + generate |

### web-research repo (Python pipeline, DDD agents)

| Area | Impact |
|---|---|
| **Embeddings** | qwen3-embedding:8b is a direct, high-impact swap for the RAG pipeline (+7.5 MTEB) |
| **Long-context agents** | Llama 4 Scout's 10M ctx relevant for future multi-document synthesis tasks |
| **Agent routing** | qwen3.5:0.8b viable as dispatch/routing model |

---

## What to Benchmark Next Session

Run via `benchmarks/lib/run-compare-models.sh`:

1. **Coder swap:** qwen2.5-coder:14b vs qwen3.6-coder:14b — same Go/Python prompts from existing benchmark suite
2. **Embedding swap:** bge-m3 vs qwen3-embedding:8b — MTEB subset + LTG corpus recall test
3. **Tiny classifier:** qwen3:4b-q8_0 vs qwen3.5:4b vs phi4-mini — expense category extraction prompt
4. **Long-context:** llama4:scout on a >100K token prompt (whole retrieval corpus) to validate the 10M claim locally

---

## Frontier-Distilled Open Models

> **Concept:** Open-weight models trained using a large proprietary model (Claude Opus, GPT-4/5, Gemini) as teacher — either via logit distillation or behavior cloning (SFT on teacher outputs). The student model inherits reasoning patterns at a fraction of the VRAM cost.

### Category 1 — Official, Production-Grade (DeepSeek-R1 Distilled)

**Teacher:** DeepSeek-R1's own frontier reasoning (~800K verified CoT traces)
**License:** MIT | **Status:** Benchmarked, validated, on Ollama

| Model | Params | VRAM (Q4) | AIME 2024 | Ollama Tag |
|---|---|---|---|---|
| DeepSeek-R1-Distill-Qwen-7B | 7B | ~5GB | 55.5% | `deepseek-r1:7b` |
| **DeepSeek-R1-Distill-Qwen-14B** | **14B** | **~9GB** | **Beats QwQ-32B** | **`deepseek-r1:14b` — already in setup** |
| DeepSeek-R1-Distill-Qwen-32B | 32B | ~20GB hybrid | 72.6% | `deepseek-r1:32b` |

**Already running:** `deepseek-r1:14b` in our setup *is* a frontier-distilled model. The distillation (smaller Qwen base + R1 reasoning traces) produces better math/reasoning than applying RL directly to the smaller model.

### Category 2 — Community Claude-Distilled (Experimental, ToS Gray Area)

**Teacher:** Claude 4.6 Opus (behavior cloning via SFT on ~14K CoT samples)
**Creator:** Jackrong (HuggingFace community) | **Method:** LoRA SFT via Unsloth

| Model | Params | VRAM (Q4) | Fits 12GB? | Notes |
|---|---|---|---|---|
| Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2 | 9B | ~6GB | ✅ Yes | Adopts `<think>` CoT pattern |
| Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled | 27B | ~16.5GB | ❌ Hybrid only | Context drops 128K→8K — regression |
| Qwen3.6-35B-A3B-Claude-4.6-Opus-Reasoning-Distilled | 35B MoE | ~20GB | Hybrid | Community fine-tune on MoE base |

**HuggingFace:** `Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF`
**No Ollama tag** — must load GGUF manually.
**No verified benchmarks** — improvement on Claude-style CoT tasks reported anecdotally.
**⚠ ToS:** Anthropic's ToS prohibits training on Claude outputs without written permission. These community models operate in a legal gray area.

### Category 3 — TeichAI Multi-Teacher Distillations (Experimental)

**Teachers:** Claude Opus 4.6, GPT-5.2, Gemini 3 Pro, DeepSeek V3.2
**Method:** Behavior cloning (SFT, 250+ samples per teacher); no logit distillation
**HuggingFace:** `TeichAI/` org — 102 models, GGUF quantizations 2-bit to 16-bit

Relevant fits for 12GB:

| Model | Base | Teacher | Params | VRAM |
|---|---|---|---|---|
| TeichAI/Qwen3-4B-...-GPT-5.2-High-Reasoning-Distill | Qwen3 4B | GPT-5.2 | 4B | ~3GB ✅ |
| TeichAI/gemma-4-26B-A4B-it-Claude-Opus-Distill | Gemma 4 26B MoE | Claude Opus 4.6 | 26B | Hybrid |

**No Ollama support** — GGUF only, manual load via `ollama create` from GGUF.
Same ToS caution applies for Claude-teacher models.

### Frontier-Distilled Recommendation Summary

| Priority | Model | What it gives you |
|---|---|---|
| **Already have** | `deepseek-r1:14b` | Best validated distilled reasoning in 12GB VRAM — keep using it |
| **Watch** | Jackrong Qwen3.5-9B-Claude-distilled | Claude CoT reasoning style at 6GB VRAM — interesting if benchmarks emerge |
| **Skip (legal)** | TeichAI Claude-teacher models | Gray area + no benchmarks + no Ollama; not worth the risk |
| **Skip (size)** | Any 27B+ Claude-distilled | Context regression + hybrid needed; no advantage over deepseek-r1:14b |

---

## Appendix: Sources

- Qwen3.5 on Ollama: https://ollama.com/library/qwen3.5
- Qwen3.6 blog: https://qwen.ai/blog?id=qwen3.6
- Qwen3.6-Coder beats Gemma 4: https://theplanettools.ai/blog/qwen-3-6-alibaba-beats-google-gemma-4-coding-benchmarks-2026
- qwen3-embedding on Ollama: https://ollama.com/library/qwen3-embedding
- Qwen3 Technical Report: https://arxiv.org/html/2505.09388v1
- Llama 4 Scout hardware guide: https://www.compute-market.com/blog/llama-4-local-hardware-guide-2026
- llama4 on Ollama: https://ollama.com/library/llama4
- Meta Llama 4 blog: https://ai.meta.com/blog/llama-4-multimodal-intelligence/
- Open LLM Leaderboard 2026: https://www.vellum.ai/open-llm-leaderboard
- Best local coding models 2026: https://insiderllm.com/guides/best-local-coding-models-2026/
- Best embedding models 2026: https://www.stackai.com/insights/best-embedding-models-for-rag-in-2026-a-comparison-guide
- Fara-7B: https://www.microsoft.com/en-us/research/blog/fara-7b-an-efficient-agentic-model-for-computer-use/
- Phi-4 family: https://azure.microsoft.com/en-us/blog/empowering-innovation-the-next-generation-of-the-phi-family/
- phi4-mini on Ollama: https://ollama.com/library/phi4-mini
- DeepSeek R2: https://decodethefuture.org/en/deepseek-r2-explained/
- Gemma 4 VRAM guide: https://knightli.com/en/2026/05/01/gemma-4-local-vram-quantization-table/
- Claude Opus distilled into Qwen3.5-27B: https://awesomeagents.ai/news/qwen-27b-claude-opus-reasoning-distilled/
- TeichAI frontier distillations: https://huggingface.co/TeichAI
- DeepSeek-R1-Distill-Qwen-14B: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B
- DeepSeek R1 technical paper: https://arxiv.org/html/2501.12948v1
