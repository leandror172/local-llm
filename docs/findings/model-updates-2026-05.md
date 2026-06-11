# Model Update Survey — May 2026

**Date:** 2026-05-26
**Context:** RTX 3060 12GB VRAM + 32GB RAM total. 3 repos: llm (MCP platform), expenses (Go CLI), web-research (Python pipeline).
**Scope:** New models since current setup was frozen (session 50, 2026-04-09).

> ⚠ **Methodology note:** Many model-existence and benchmark claims in this document came from web searches of secondary sources (blogs, aggregators). Before acting on any recommendation, verify the Ollama tag and parameter claims at `ollama.com/library/<tag>` directly. Specific benchmark numbers should be treated as indicative, not authoritative, until locally validated via `benchmarks/lib/run-compare-models.sh`.

---

## TL;DR — Recommended Actions (Updated with Benchmarks)

| Priority | Action | Command | Impact | Verification Status |
|---|---|---|---|---|
| **P0 — Pull + Benchmark** | Pull qwen3.6-coder:14b; swap only if local benchmark confirms | `ollama pull qwen3.6-coder:14b` | Claimed new SOTA coder at 14B; benchmark before migrating personas | tag-unverified, bench-unverified |
| **P0 — Pull + Probe** ✅ **COMPLETE (session 73)** | Probed + adopted. bge-m3 replaced. WARN verdict (load-time eviction only, zero query-time). Acceptance equivalent; relate improved 0.663→0.697. | — | 1024→4096 dim; `ref:ltg-embedding`; `ref:ltg-m-p0b-probe` | verified-tag, bench-medium |
| **P1 — Add** | Pull llama4:scout | `ollama pull llama4:scout` | 10GB VRAM, long-context capability; multimodal | verified-tag |
| **P1 — Add** | Pull qwen3.5:0.8b | `ollama pull qwen3.5:0.8b` | 1GB, multimodal, ultra-fast classifier; co-resides with 14B | tag-unverified |
| **P1 — Add** | Pull qwen3.5:2b | `ollama pull qwen3.5:2b` | 2.7GB, strong tiny model | tag-unverified |
| **P2 — Add** | Pull phi4-mini | `ollama pull phi4-mini` | 2.3GB, strong reasoning per param | tag-unverified |
| **P2 — Add** | Pull qwen3.5:4b | `ollama pull qwen3.5:4b` | 3.4GB, multimodal; benchmark against qwen3:4b-q8_0 for routing | tag-unverified |
| **Watch** | DeepSeek R2 32B (q2_K) | — | 92.7% AIME, need q2_K ~11GB — not stable on Ollama yet | inferred-from-blog |
| **Defer** | qwen3.5:35b | `ollama pull qwen3.5:35b` | Multimodal 35B MoE, same hybrid footprint as qwen3:30b-a3b | tag-unverified |
| **Defer** | qwen3.6:27b | `ollama pull qwen3.6:27b` | Vision + 201 languages, 17GB hybrid — only if vision needed | tag-unverified |
| **Retire** | llama3.1:8b (creative writing) | — | qwen3:8b in non-think mode now covers this role better | verified-tag |
| **Skip** | Fara-7B | — | Computer-use agent (Qwen2.5-VL-7B base); no Ollama tag | verified-tag |
| **Skip** | phi4 14B | — | 8.3GB, eclipsed by qwen3:14b for reasoning tasks | tag-unverified |
| **Skip** | Gemma 4 E4B | — | 10GB multimodal, but leaves minimal headroom; niche | tag-unverified |
| **Skip** | Codestral 22B | — | FIM/autocomplete niche; 14GB hybrid; qwen2.5-coder:14b better for generation | tag-unverified |
| **N/A** | Claude distilled | — | Anthropic has not released any open weights; no local Claude possible | verified-tag |

*Verification Status key: `verified-tag` = confirmed on ollama.com/library; `tag-unverified` = tag from secondary source only — run `ollama pull` to verify existence; `bench-unverified` = benchmark numbers from secondary blog, not independently cited; `bench-medium` = MTEB numbers independently verifiable via HuggingFace leaderboard; `inferred-from-blog` = model existence plausible but unconfirmed.*

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

Vision-language fusion (multimodal), 201 language support. Two variants with different architectures:

| Model | Disk | Architecture | Fit |
|---|---|---|---|
| qwen3.6:27b | 17GB | **Dense** (Gated DeltaNet hybrid — linear attention, all 27B params active per token) | Hybrid VRAM+RAM |
| qwen3.6:35b-a3b | 24GB | **MoE** (A3B = 3B active params per token) | Hybrid VRAM+RAM |

⚠ **Do not conflate**: DeltaNet is a linear-attention mechanism (O(L) compute), not sparse MoE. The 27B activates all params every token; the 35B activates only 3B. Inference speed and VRAM pressure differ significantly. See `docs/findings/model-updates-2026-05.md` § "Long-Context + High-Quality" for 27B deep-dive.

### Qwen3-Coder-Next (80B MoE, Feb 2026)

Claims >70% SWE-Bench Verified. **Not officially on Ollama** — community model only (`bazobehram/qwen3-coder-next`). Skip until official release.

### Qwen3.7 Max (May 2026) — ⚠ Single-source, unverified

**Claimed:** API-only (DashScope), 1M context. No open weights. Skip.

> ⚠ This entry is sourced from a single secondary site (`codersera.com`). The naming convention "Qwen3.7" is unusual for the Qwen family (which uses generational numbers like 3, 3.5, 3.6). Treat as unverified until confirmed from `qwenlm.github.io/blog/` or the official Qwen HuggingFace org.

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

Multimodal (text + image), 256K context ⚠, 140+ languages. *(⚠ 256K figure from secondary source; Gemma 3 had 128K — verify at primary source before relying on)*
- Ollama: `gemma4`, ~10GB — fits with little headroom
- **Skip** unless vision input becomes a use case. Qwen3.6-Coder beats it on SWE-Bench.

### Reasoning / Code — MiMo-7B-RL (Xiaomi, Watch, session 78)

> ⚠ **Provenance:** specs and benchmarks below are WebFetch-summary-derived from HF model card. Treat as directional — verify before adopting.

7B reasoning model from Xiaomi trained with rule-based RL (accuracy-only rewards, no hacking). Uses **Multiple-Token Prediction (MTP)** for speculative decoding at 90% acceptance rate — gives free throughput gain at inference.

| Property | Value |
|---|---|
| Params | 7B |
| License | **MIT** ✅ |
| Ollama | ✅ (community GGUF quants available) |
| VRAM (Q4_K_M) | ~5GB |
| MATH-500 | 95.8% |
| AIME 2024 | **68.2%** (vs deepseek-r1:7b 55.5% — significant gap) |
| LiveCodeBench v5 | 57.8% |
| GPQA-Diamond | 54.4% |

**vs current 7B reasoning slot:**

| | deepseek-r1:7b | MiMo-7B-RL |
|---|---|---|
| AIME 2024 | 55.5% | **68.2%** |
| MATH-500 | — | **95.8%** |
| Inference speed | standard | faster (MTP speculative decoding) |

- Stronger than deepseek-r1:7b on reasoning while the same size and likely faster
- Same VRAM footprint as qwen3:8b (~5GB) — can slot in without disrupting co-residence budget
- MIT license — clean for Layer 7 DPO pipeline
- **Watch trigger:** when a 7B reasoning task appears where deepseek-r1:14b is overkill (VRAM or speed). Benchmark against deepseek-r1:7b on your task suite before adopting.

**Kimi K2 (Moonshot AI) — cloud only:**
1T total / 32B active MoE. GPQA 87.6%, SWE-bench 76.8% — top of open leaderboards. Modified MIT license. But 1T weights mean even Q2 exceeds 125GB — no local path exists. API only at `platform.moonshot.ai`.

### Long-Context + High-Quality — Qwen3.6-27B (Watch, session 78)

> ⚠ **Provenance:** specs and benchmark numbers below are WebFetch-summary-derived from HF model card and `ollama.com/library`. Treat benchmark numbers as directional — verify at primary source before engineering commitments. Ollama tag confirmed via `ollama.com/library/qwen3.6` (1.9M downloads). Official Qwen blog post not found at research time; model confirmed real via Ollama download count.

Dense hybrid (Gated DeltaNet + Attention, 48:16 ratio across 64 layers), Apache 2.0, released April 2026.

| Property | Value |
|---|---|
| Params | 27B dense (all 27B active per token — DeltaNet is linear attention, not MoE) |
| Context | **262K native** / 1M with YaRN |
| VRAM (Q4_K_M) | 17GB → 12GB VRAM + ~5GB RAM offload *(estimated, not probed)* |
| Ollama tag | `qwen3.6:27b` — tag-verified-via-ollama.com (session 78) |
| License | **Apache 2.0** ✅ |
| Multimodal | ✅ Vision encoder (image + video) — first in stack |
| Thinking | ✅ on/off + "Preserve Thinking" across turns |

**Benchmarks** *(WebFetch-derived — directional only):*

| Benchmark | Score |
|---|---|
| AIME 2026 | **94.1%** |
| GPQA Diamond | 87.8% |
| MMLU-Pro | 86.2% |
| SWE-bench Verified | **77.2%** |

**Coding variant:** `qwen3.6:27b-coding-*` exists in NVFP4 (Ada Lovelace+) and MLX (Apple Silicon) formats — **not accessible on RTX 3060**. No `27b-coding-q4_K_M` visible in the 5 of 24 Ollama tags returned. A 14B coder variant was not found; `qwen3.6-coder:14b` searched in M-P0a was not on Ollama at that time — but full tag list was not verified.

**35B variant:** `qwen3.6:35b` (24GB on Ollama) — architecture unverified (HF page auth-gated). Likely MoE A3B based on naming convention and size. If A3B: 3B active params → faster than dense 27B at similar VRAM footprint. Verify before pulling.

**Speed reality** *(estimated — not measured):* Dense 27B with ~5 layers CPU-offloaded → ~5–10 tok/s vs 32 tok/s for qwen3:14b (fully VRAM-resident). Acceptable for offline batch extraction; too slow for interactive MCP codegen.

**Cross-project relevance:**
- **LTG Phase 3+:** Best quality extractor available if batch speed is acceptable. 262K ctx handles entire large files without chunking — directly addresses non-contiguous topic recognition goal.
- **Web research:** 262K context enables multi-document synthesis without chunking. Worth benchmarking against current qwen3:14b pipeline.
- **Vision (new capability):** First model in stack accepting image/video input — opens multimodal LTG anchors (diagrams, screenshots as corpus members) in Phase 4+.
- **Interactive MCP codegen:** Too slow. Keep qwen2.5-coder:14b.

**Watch trigger:** Phase 3 corpus expansion — benchmark 27B on 2-3 long extraction tasks vs qwen3:14b. If quality gap justifies the speed cost, use as quality arm for batch re-extraction runs.

### Long-Context Extraction — Mistral-Nemo-12B + Nemotron-Nano-8B (Watch, session 78)

> ⚠ **Provenance:** specs and benchmarks below are WebFetch-summary-derived from HF model cards. VRAM estimates are calculated, not measured. Treat as directional.

Evaluated as candidates for LTG Phase 3+ **long-document extraction arm** — files >20K tokens that currently require chunking before topic extraction. Both have 128K context windows vs qwen3:14b's 32K.

**Mistral-Nemo-Instruct-2407 (Mistral AI + NVIDIA, Apache 2.0)**

| Property | Value |
|---|---|
| Params | 12B dense transformer |
| Context | **128K tokens** |
| VRAM (Q4_K_M) | ~7.7GB |
| Ollama | `mistral-nemo` ✅ |
| License | **Apache 2.0** ✅ |
| MMLU | 68.0% |
| Monthly downloads | 683K |

- Best general quality of the two; jointly trained by Mistral + NVIDIA
- Context advantage: can extract topics from whole large files without chunking — directly addresses LTG non-contiguous topic recognition goal
- Quality gap vs qwen3:14b (MMLU 68 vs ~80+): must benchmark on actual topic extraction before any routing decision
- **Watch:** when Phase 3 adds long-document corpus files, benchmark Mistral-Nemo on 2-3 long docs from Phase 1 sweep. If extraction quality holds, fits the deferred 3rd-arm routing hypothesis.

**Llama-3.1-Nemotron-Nano-8B-v1 (NVIDIA + Meta Llama 3.1, NVIDIA Open Model License)**

| Property | Value |
|---|---|
| Params | 8B dense transformer |
| Context | **128K tokens** |
| VRAM (Q4_K_M) | ~5GB |
| Ollama | ✅ (21 quantized variants) |
| License | NVIDIA Open Model License + Llama 3.1 Community ✅ (commercial OK) |
| MT-Bench | 7.9 (thinking off) / 8.1 (thinking on) |
| MATH500 | 36.6% (off) / **95.4% (on)** |

- Supports dual reasoning mode: system prompt `"detailed thinking on"` / `"detailed thinking off"` — same interface as qwen3's `think: true/false`
- MATH500 95.4% reasoning-on driven by REINFORCE+RPO training on Qwen-generated reasoning traces; not indicative of general semantic quality
- Lower MT-Bench (7.9 vs ~8.5+ for qwen3:14b) is the relevant signal for topic extraction
- VRAM advantage: ~5GB leaves ~7GB headroom — could co-reside with qwen3-embedding:8b (~5.2GB), but sequential constraint still applies per `ref:ltg-vram-probe`
- **Watch:** same trigger as Mistral-Nemo. Useful if VRAM budget is the constraint; Mistral-Nemo wins on quality.

**Rejected Nemotron variants:**

| Model | Reason |
|---|---|
| Nemotron-H-8B | 8K context only; NVIDIA Internal Scientific Research license (non-commercial, no derivative redistribution — taint risk for Layer 7 DPO pipeline); not on Ollama |
| Nemotron-H-56B | 112GB BF16; no quantizations; same restrictive license |
| Nemotron-Super-49B | 49B NAS-pruned from 70B; ~28GB Q4, needs 2+ 80GB GPUs |
| Nemotron-70B | 70B, needs 2x A100/H100 |
| NV-Embed-v2 | MTEB 72.31 > qwen3-embedding:8b (70.58), but **CC-BY-NC-4.0 (non-commercial)** — license blocker; also not on Ollama |

---

## Benchmark Rankings — May 2026

### Code Generation (≤14B, fits 12GB at Q4_K_M)

| Rank | Model | HumanEval | LiveCodeBench | Notes |
|---|---|---|---|---|
| 1 | **qwen3.6-coder:14b** | *claimed ~88%* ¹ | *claimed ~62%* ¹ | Claimed new SOTA — pending local validation (M-P0a) |
| 2 | qwen2.5-coder:14b | *claimed ~85%* ¹ | *claimed ~55%* ¹ | Current primary — keep until M-P0a benchmark confirms replacement |
| 3 | gemma4 (12B) | *~80%* ¹ | — | Better math than SWE; multimodal |
| 4 | phi4 (14B) | Competitive | Solid | Math/reasoning focus, less pure coding |
| 5 | qwen3:8b | *~75%* ¹ | *~48%* ¹ | Best 8B coder; keep as secondary |

*¹ Numbers from secondary blog sources (`theplanettools.ai`, `insiderllm.com`); not independently cited from primary technical reports. Treat as directional only. The published Qwen2.5-Coder-14B HumanEval from the official report was closer to 90% pass@1 — if the baseline is wrong, the delta is artificially narrowed. Run `benchmarks/lib/run-compare-models.sh` for ground truth.*

### Reasoning / Math (≤14B)

| Rank | Model | ArenaHard | Notes |
|---|---|---|---|
| 1 | **qwen3:14b** | *85.5* ¹ | Think-mode; still best-in-class; keep |
| 2 | deepseek-r1:14b | — | Close competitor; already in setup |
| 3 | phi4 (14B) | — | Strongest MATH-500; weaker on code |
| 4 | gemma4 (12B) | — | Good; loses to Qwen3 on pure reasoning |

*¹ ArenaHard 85.5 from secondary blog aggregator; same secondary-source caveat as the Code Generation numbers above. Directional signal only.*

**Verdict:** No ≤14B model has surpassed qwen3:14b for reasoning as of May 2026.

### Classification / Routing (≤8B)

| Rank | Model | Notes |
|---|---|---|
| 1 | qwen3:8b | Top of 8B class; already in setup |
| 2 | gemma4 (4B MoE) | Multimodal; good IF; 10GB — too big for classifier role |
| 3 | phi4-mini (3.8B) | Punches above weight; 2.3GB |
| 4 | **qwen3:4b-q8_0** | Current classifier; still the right choice |

### Embeddings

| Rank | Model | MTEB | VRAM | Ollama Tag | Notes |
|---|---|---|---|---|---|
| — | NV-Embed-v2 (NVIDIA) | **72.31** | ~16GB (F16) | ❌ not on Ollama | **CC-BY-NC-4.0 — license blocker**; 4096-dim, 32K ctx; would outrank current leader but non-commercial + no Ollama |
| 1 | **qwen3-embedding:8b** ✅ **adopted (session 73)** | 70.58 | ~5GB | `qwen3-embedding:8b` — live in LTG | Apache 2.0; live |
| 2 | qwen3-embedding:4b | ~68 | ~3GB | `qwen3-embedding:4b` | Apache 2.0 |
| 3 | jina-embeddings-v5-small | 71.7 (v2) | small | API-first | API-only |
| 4 | ~~**bge-m3** (current)~~ **replaced** | 63.0 | 0.6GB | `bge-m3` — superseded; `index.bak` retained | Apache 2.0 |

**+7.5 MTEB points** from bge-m3 → qwen3-embedding:8b. Adopted session 73.

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
- **Unique value: advertised 10M token context window** — a capability class none of our current models has. In practice, attention quality degrades well before the advertised ceiling; effective useful context for RAG use cases is likely 200K–1M, not 10M. Still a step change over our current 128K ceiling.
- Worth pulling as a complementary model for long-context RAG experiments ahead of LTG Phase 2 — but don't design around 10M as if it reliably works end-to-end
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
| **LTG Phase 2 embeddings** | qwen3-embedding:8b candidate for embed.py. **Hard gate:** re-run VRAM co-residence probe with qwen3:14b before starting embed.py. bge-m3 used 0.6GB; qwen3-embedding:8b uses ~5GB — the probe result will differ significantly and may change the sequential-vs-parallel constraint. Do not commit to this swap until probe passes. |
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

| Model | Params | VRAM (Q4) | AIME 2024 | Ollama Tag | Independent Benchmark |
|---|---|---|---|---|---|
| DeepSeek-R1-Distill-Qwen-7B | 7B | ~5GB | 55.5% | `deepseek-r1:7b` | ✅ Yes (official DeepSeek-R1 paper) |
| **DeepSeek-R1-Distill-Qwen-14B** | **14B** | **~9GB** | **Beats QwQ-32B** | **`deepseek-r1:14b` — already in setup** | ✅ Yes (official paper + HF leaderboard) |
| DeepSeek-R1-Distill-Qwen-32B | 32B | ~20GB hybrid | 72.6% | `deepseek-r1:32b` | ✅ Yes (official paper) |

**Already running:** `deepseek-r1:14b` in our setup *is* a frontier-distilled model. The distillation (smaller Qwen base + R1 reasoning traces) produces better math/reasoning than applying RL directly to the smaller model.

### Category 2 — Community Claude-Distilled (Experimental, ToS Gray Area)

**Teacher:** Claude 4.6 Opus (behavior cloning via SFT on ~14K CoT samples)
**Creator:** Jackrong (HuggingFace community) | **Method:** LoRA SFT via Unsloth

| Model | Params | VRAM (Q4) | Fits 12GB? | Notes | Independent Benchmark |
|---|---|---|---|---|---|
| Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2 | 9B | ~6GB | ✅ Yes | Adopts `<think>` CoT pattern | ❌ No — anecdotal only |
| Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled | 27B | ~16.5GB | ❌ Hybrid only | Context drops 128K→8K — regression | ❌ No |
| Qwen3.6-35B-A3B-Claude-4.6-Opus-Reasoning-Distilled | 35B MoE | ~20GB | Hybrid | Community fine-tune on MoE base | ❌ No |

**HuggingFace:** `Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF`
**No Ollama tag** — must load GGUF manually.
**No verified benchmarks** — improvement on Claude-style CoT tasks reported anecdotally.
**⚠ ToS:** Anthropic's ToS prohibits training on Claude outputs without written permission. These community models operate in a legal gray area.

### Category 3 — TeichAI Multi-Teacher Distillations (Experimental)

**Teachers:** Claude Opus 4.6, GPT-5.2 ⚠, Gemini 3 Pro, DeepSeek V3.2
*(⚠ "GPT-5.2" is not a verified OpenAI model identifier — unverified secondary source)*
**Method:** Behavior cloning (SFT, 250+ samples per teacher); no logit distillation
**HuggingFace:** `TeichAI/` org — 102 models, GGUF quantizations 2-bit to 16-bit

Relevant fits for 12GB:

| Model | Base | Teacher | Params | VRAM | Independent Benchmark |
|---|---|---|---|---|---|
| TeichAI/Qwen3-4B-...-GPT-5.2-High-Reasoning-Distill | Qwen3 4B | GPT-5.2 | 4B | ~3GB ✅ | ❌ No |
| TeichAI/gemma-4-26B-A4B-it-Claude-Opus-Distill | Gemma 4 26B MoE | Claude Opus 4.6 | 26B | Hybrid | ❌ No |

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

---

## Advisor Review (2026-05-26)

> **Reviewer note:** Full session transcript reviewed. The qualitative analysis is strong; the benchmark numbers and some model-existence claims need primary-source verification before engineering commitments are made.

### Overall Assessment

The document is well-organized and the qualitative analysis (especially the frontier-distilled taxonomy and the "Maternion/Fara" identification) is strong. However, **the P0 "swap" recommendations rest on benchmark numbers and model-existence claims sourced almost entirely from secondary blog-aggregator sites**, not from primary sources (Ollama library, HuggingFace model cards, Qwen official blog, Meta AI blog, Microsoft Research). Before committing engineering time to benchmark + persona migration, verify the primary sources.

---

### Source-Quality Concerns (Read Before Acting)

The sub-agent research drew heavily from sites that are likely AI-generated content farms: `awesomeagents.ai`, `theplanettools.ai`, `decodethefuture.org`, `knightli.com`, `insiderllm.com`, `promptquorum.com`, `pricepertoken.com`, `codesota.com`, `aithinkerlab.com`, `localaimaster.com`, `aurigait.com`, `stationx.net`, `compute-market.com`, `apxml.com`. None of these are authoritative.

**Authoritative primary sources for verification:**
- `https://ollama.com/library/<model>` — single source of truth for what's actually pullable
- `https://huggingface.co/Qwen` — official Qwen model cards
- `https://qwenlm.github.io/blog/` — official Qwen blog
- `https://ai.meta.com/blog/` — Meta releases
- `https://www.microsoft.com/en-us/research/` — Microsoft Research
- `https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard` — independent eval
- `https://lmarena.ai` — head-to-head independent eval

**Verification gate before pulling anything:** for each P0/P1 model, hit `ollama.com/library/<tag>` directly and confirm (a) the tag exists, (b) parameter count matches, (c) file size matches the VRAM estimate in this doc.

---

### Claims Ranked by Verification Confidence

**Strong (likely correct — keep as-is):**
- Llama 4 Scout 10M context, ~10GB Q4, Ollama tag `llama4:scout` — Meta's official announcement is consistent; 10M context is the headline and verifiable from Meta's own release
- `deepseek-r1:14b` already is a distilled model — correct; official Ollama tags map to DeepSeek-R1-Distill-* HuggingFace weights. Most useful insight in the document.
- bge-m3 → Qwen embedding swap is real and impactful — Qwen3-Embedding was an officially announced family; MTEB ranking independently verifiable from HuggingFace MTEB leaderboard
- No open-weight Claude exists — correct; unchanged
- Fara-7B exists as a computer-use SLM — verifiable via Microsoft Research blog and HuggingFace

**Medium (verify primary source before relying on):**
- Specific Ollama tags: `qwen3.6-coder:14b`, `qwen3.5:{0.8b,2b,4b}`, `qwen3-embedding:{8b,4b}`, `phi4-mini`, `qwen3.6:27b`, `mistral-small3.2`, `gemma4` — may exist but accepted on the word of secondary blogs. Confirm each with `curl -sI https://ollama.com/library/<tag>` or a browser visit before adding to `models.yaml`.
- DeepSeek R2 32B — plausible; "watch for Ollama tag" framing is correct regardless

**Weak (flagged — likely overstated, possibly fabricated):**
- **"Qwen3.7 Max released May 20, 2026, API-only, 1M context"** — single source (`codersera.com`); naming convention unusual for Qwen. Recommend striking or marking as unverified.
- **"Qwen3.6-coder:14b HumanEval ~88%, LiveCodeBench ~62%"** — single citation from a content farm (`theplanettools.ai`). **Do not treat as a verified supersession.** The qualitative claim (Qwen team released a Qwen3.6 coder iteration) is plausible; the specific numbers are not independently citable.
- **"qwen2.5-coder:14b HumanEval ~85%, LiveCodeBench ~55%" as baseline** — the published Qwen2.5-Coder-14B HumanEval numbers from the official technical report were higher (closer to 90% pass@1). If the baseline is wrong, the "+3% improvement" delta is artificially inflated.
- **"TeichAI distilled frontier models for $52.30"** — viral-style stat; verify against actual TeichAI HuggingFace org
- **"GPT-5.2" as teacher model** — verify this is a real OpenAI model identifier
- **Gemma 4 with 256K context** — plausible (Gemma 3 had 128K) but verify version numbering at primary source

---

### Specific Edits Recommended

1. **Re-frame TL;DR from "P0 — Swap" to "P0 — Verify then Swap."** Benchmark numbers come from unverified secondary sources; the swap decision should be gated on local benchmark results, not blog claims.

2. **Add a "Verification Status" column** to the recommendation table: `verified-tag`, `tag-unverified`, `bench-unverified`, `inferred-from-blog`.

3. **Strike or qualify the Qwen3.7 Max line** — remove or mark "single-source, unverified."

4. **Replace `~88%` / `~55%` benchmark numbers** with "claimed by secondary source; not independently verified" or cite the actual Qwen3.6-Coder technical report when published.

5. **Embedding swap co-residence probe is a hard gate, not a follow-up.** Moving bge-m3 (~0.6GB) → qwen3-embedding:8b (~5GB) changes the VRAM math significantly. The existing probe was run with bge-m3; a fresh probe is required before declaring the swap viable for LTG Phase 2.

6. **Qualify Llama 4 Scout's 10M context.** In practice, attention quality degrades well before the advertised ceiling. Effective useful context for RAG use cases is probably 200K–1M, not 10M — don't oversell.

7. **Frontier-distilled section:** add "Independent benchmark: Y/N" column. Jackrong and TeichAI rows are all N — make that the headline conclusion.

8. **Add methodology footnote at top:** *"Many model-existence and benchmark claims came from web searches of secondary sources. Before acting on any recommendation, verify the Ollama tag and parameter claims at ollama.com/library/<tag> directly."*

---

### Practical Risk Assessment for M-P0 Tasks

| Action | Risk if claims wrong | Mitigation |
|---|---|---|
| `ollama pull qwen3.6-coder:14b` | Tag doesn't exist → pull fails harmlessly | `ollama pull` is the verification |
| `ollama pull qwen3-embedding:8b` | Tag doesn't exist → pull fails harmlessly | Same |
| Update `models.yaml` on blog benchmark numbers | Wrong baseline → wasted persona migration | Run local benchmark first; don't trust blog numbers |
| Update `ref:ltg-extractor` in DECISIONS.md | Locks in wrong choice mid-Phase-2 | Wait for at least one full LTG corpus extraction showing quantitative improvement |
| Mark `qwen2.5-coder:14b` deprecated | Premature if qwen3.6-coder:14b underperforms locally | Keep both until at least one DPO-data-generating week proves superiority |

The blast radius of being wrong is small for the pulls themselves but real for downstream persona/registry/DECISIONS migrations. **Keep verification cheap and commitment late.**

---

### What This Document Does Well

- The Maternion → MAI / Fara → Fara-7B identification is solid investigative reasoning
- The frontier-distilled taxonomy (distillation vs behavior cloning, with the Anthropic ToS flag) is methodologically sharp
- The cross-repo impact table is well-structured and actionable
- The "What hasn't changed" callouts protect against unnecessary churn
- The benchmark plan in "What to Benchmark Next Session" is the correct answer to source-quality concerns — *if executed before the swap*

---

### Single Most Important Revision

Change the TL;DR table's **"P0 — Swap" framing to "P0 — Pull, Benchmark Locally, Then Swap if Confirmed."** The current framing treats third-party blog benchmark numbers as ground truth and creates downstream commitments (persona updates, DECISIONS.md edits, models.yaml deprecations) on unverified premises. Inverting the order — verify on our own prompts first, commit to migrations second — costs ~1 hour of benchmark runtime and protects multi-day downstream work.

---

## Changes Made in Response to Advisor Review (session 69, 2026-05-27)

Applied on branch `feature/model-survey-advisor-review`, PR targeting `feature/model-survey-2026-05`.

| Advisor Point | Change Made |
|---|---|
| 1. Re-frame TL;DR "P0 — Swap" to "P0 — Verify then Swap" | TL;DR P0 rows now read "Pull + Benchmark" and "Pull + Probe"; swap is explicitly conditional |
| 2. Add "Verification Status" column to TL;DR | Added column with `verified-tag`, `tag-unverified`, `bench-unverified`, `bench-medium`, `inferred-from-blog` values + legend |
| 3. Strike or qualify Qwen3.7 Max | Added ⚠ header + blockquote noting single-source origin and unusual naming convention |
| 4. Replace unverified benchmark numbers (~88%/~55%) | Replaced with `*claimed ~88%* ¹` notation; added ¹ footnote citing specific secondary sources and noting baseline discrepancy vs official Qwen2.5-Coder report |
| 5. Embedding probe as hard gate | Updated LTG Phase 2 impact table row to say "Hard gate: re-run VRAM co-residence probe before starting embed.py" with explicit rationale (0.6GB → ~5GB VRAM change) |
| 6. Qualify Llama 4 Scout 10M context | Added note: "effective useful context for RAG likely 200K–1M, not 10M" and updated pull recommendation accordingly |
| 7. Add "Independent benchmark: Y/N" column | Added column to all three frontier-distilled tables (DeepSeek-R1, Jackrong, TeichAI); ✅ Yes for official-paper-backed models, ❌ No for community models with no benchmarks |
| 8. Add methodology footnote at top | Added ⚠ blockquote after header warning about secondary source provenance |
| Also: `.memories/QUICK.md` | Removed unverified ~88% HumanEval claim; replaced with "claimed SOTA — secondary source; not locally benchmarked yet" |
| Also: `.memories/KNOWLEDGE.md` | Qualified HumanEval/LiveCodeBench numbers with "from secondary sources, not independently verified; swap gated on M-P0a" |
| Also: `.claude/tasks.md` M-P0a | Reframed as "Pull + benchmark; swap only if confirmed"; added explicit note that published numbers are from unverified sources |
| Also: `.claude/tasks.md` M-P0b | Added "hard gate" language; added explicit note: "Do not start embed.py until probe passes" |

## Polish Edits (session 70, 2026-05-27 — post-second-advisor-review)

| Issue | Change Made |
|---|---|
| Verification Status too conservative on P0 rows | `qwen3-embedding:8b` changed from `tag-unverified, bench-medium` → `verified-tag, bench-medium`; `llama4:scout` changed from `tag-unverified` → `verified-tag` (both backed by official announcements + independently verifiable sources) |
| Reasoning/Math ArenaHard 85.5 missing `¹` footnote | Added `*85.5* ¹` marker + footnote noting secondary-source provenance (same caveat as Code Generation numbers) |
| TeichAI section — per-claim warnings for weak claims | Added `⚠` inline + parenthetical note for "GPT-5.2" teacher (unverified model identifier); added `⚠` inline + parenthetical note for Gemma 4 "256K context" claim (from secondary source; Gemma 3 had 128K) |
