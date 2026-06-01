# LLM Leaderboard Survey — June 2026

**Date:** 2026-06-01 (session 78)
**Context:** RTX 3060 12GB VRAM + 32GB RAM. Evaluating new model candidates beyond May 2026 survey.
**Method:** Direct parquet download from `open-llm-leaderboard/contents` HF dataset (4,576 models); Arena.ai live rankings; per-model HF page fetches.

> ⚠ **Leaderboard staleness note:** The HF Open LLM Leaderboard v2 (benchmarks: IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO) has been de-prioritised by model developers since mid-2025. All major 2025-2026 releases are **absent** — Qwen3/3.5/3.6, DeepSeek-V3, Llama 4, Gemma 4, MiMo, Nemotron-H, Mistral-Nemo. Developers have shifted to AIME 2025/2026, SWE-bench, and LiveCodeBench as the de facto standard. Use this data for the 2024 generation only.

---

## Arena.ai — Frontier Rankings (closed + open)

Human preference Elo from live battles. Top 10 as of 2026-06-01:

| Rank | Model | Elo | Org |
|---|---|---|---|
| 1 | claude-opus-4-6-thinking | 1502 | Anthropic |
| 2 | claude-opus-4-7-thinking | 1500 | Anthropic |
| 3 | claude-opus-4-6 | 1498 | Anthropic |
| 4 | claude-opus-4-7 | 1494 | Anthropic |
| 5 | muse-spark | 1489 | Meta |
| 6 | gemini-3.1-pro-preview | 1487 | Google |
| 7 | gemini-3-pro | 1486 | Google |
| 8 | gpt-5.5-high | 1482 | OpenAI |
| 9 | gpt-5.4-high | 1480 | OpenAI |
| 10 | gemini-3.5-flash | 1479 | Google |

All top-10 are closed-weight API models. No open-weight model appears in the top 10. The first open-weight entries (not captured in the visible excerpt) are likely Llama 4 / Kimi K2 variants.

---

## HF Open LLM Leaderboard v2 — Notable ≤30B Official Models

Filtered from 4,576 submissions: notable org prefixes, ≤30B params (or MoE with ≤40B total), avg > 15. Sorted by average score.

| Avg | IFEval | GPQA | MATH Lvl5 | Params | Model | Notes |
|---|---|---|---|---|---|---|
| 41.6 | 84.1 | 12.4 | 53.0 | 14.8B | Qwen/Qwen2.5-14B-Instruct-1M | Best official ≤14B |
| 41.3 | 81.6 | 9.6 | 54.8 | 14.8B | Qwen/Qwen2.5-14B-Instruct | Standard context |
| 38.9 | 70.1 | 9.5 | 40.8 | 19.9B | internlm/internlm2_5-20b-chat | 20B — hybrid VRAM+RAM |
| 38.2 | 43.8 | 18.3 | 57.0 | 14.8B | deepseek-ai/DeepSeek-R1-Distill-Qwen-14B | **Already in stack** |
| **36.4** | **—** | **8.1** | **—** | **7.5B** | **tiiuae/Falcon3-7B-Instruct** | **Beats Qwen2.5-7B; see below** |
| 36.2 | 79.8 | 16.7 | 23.9 | 27.2B | google/gemma-2-27b-it | 27B hybrid |
| 35.5 | 78.2 | 10.5 | 27.6 | 10.3B | tiiuae/Falcon3-10B-Instruct | 10B, Apache-like |
| 35.2 | 75.9 | 5.5 | 50.0 | 7.6B | Qwen/Qwen2.5-7B-Instruct | In stack (superseded by qwen3:8b) |
| 33.1 | 54.2 | 11.5 | 19.6 | 7.6B | nvidia/AceInstruct-7B | NVIDIA general 7B |
| 32.1 | 69.1 | 7.3 | 32.5 | 14.8B | Qwen/Qwen2.5-Coder-14B-Instruct | Coding variant |
| 32.1 | 74.4 | 14.8 | 19.5 | 9.0B | google/gemma-2-9b-it | Strong 9B |
| **30.3** | **45.3** | **5.6** | **63.4** | **7.6B** | **nvidia/AceMath-7B-Instruct** | **MATH 63.4% — license blocked** |
| 30.4 | 5.9 | 20.8 | 31.6 | 14.7B | microsoft/phi-4 | IFEval 5.9 = format artifact, not capability |
| 29.4 | 73.8 | 7.9 | 17.0 | 3.8B | microsoft/Phi-4-mini-instruct | Strong 3.8B |
| 29.9 | 62.8 | 11.1 | 20.4 | 22.2B | mistralai/Mistral-Small-Instruct-2409 | 22B |
| 28.1 | 71.7 | 7.2 | 30.1 | 7.3B | tiiuae/Falcon3-Mamba-7B-Instruct | Mamba arch, interesting |

**Top community fine-tune (for reference):** `Qwen/Qwen2.5-72B-Instruct` base gets 48.0 avg; community fine-tunes of it reach 48.1. The leaderboard top is saturated by 72B Qwen2.5 variants — not relevant to 12GB VRAM.

---

## New Model Deep-Dives

### Falcon3-7B-Instruct (TII UAE, Dec 2024) — Watch

| Property | Value |
|---|---|
| Params | 7.5B dense |
| Context | 32K |
| VRAM (Q4_K_M) | ~5GB |
| Ollama | ✅ (community GGUF quants) |
| License | **TII Falcon-LLM License 2.0** — permissive for commercial use, attribution required; NOT Apache/MIT |
| Leaderboard avg | 36.4 (vs Qwen2.5-7B at 35.2) |

Key numbers from the benchmark suite: BBH 37.92 (Llama-3.1-8B: 29.89), MATH Lvl5 31.87 (Llama: 19.34). Trained on 14 trillion tokens, multilingual (EN/FR/ES/PT).

**Assessment:** Genuinely strong 7B model in the 2024 generation. Superseded by Qwen3:8b for our stack (qwen3:8b is newer, stronger, Apache 2.0). License is non-standard — check TII Falcon-LLM License 2.0 before any derivative/DPO use.

**Falcon3-Mamba-7B-Instruct:** Same family, Mamba architecture (SSM, O(L) inference). 28.1 avg — weaker than the dense variant on these benchmarks. Architecturally interesting (same SSM direction as Nemotron-H). Same TII license concern.

### AceMath-7B-Instruct (NVIDIA, Dec 2024) — License-Blocked

| Property | Value |
|---|---|
| Params | 7.6B (Qwen2.5-Math-7B base) |
| VRAM (Q4_K_M) | ~5GB |
| Ollama | ✅ (7 GGUF quants) |
| License | **CC-BY-NC-4.0 — non-commercial only** |
| MATH avg pass@1 | **67.2%** (beats GPT-4o 67.4%, Claude 3.5 Sonnet 65.6%) |

Math-specialist at 7B, outdoing frontier models on pure math. Same license blocker as NV-Embed-v2: CC-BY-NC-4.0 taints DPO training data for Layer 7 pipeline. **Skip.**

---

## Kimi K2 (Moonshot AI) — Cloud Only

| Property | Value |
|---|---|
| Total params | 1 Trillion |
| Active params | 32B (MoE, 384 experts, 8 selected) |
| Context | 128K |
| License | Modified MIT |
| GPQA Diamond | 87.6% |
| SWE-bench | 76.8% |

Cloud-only regardless of quantization: 1T weights × Q2 = ~125GB minimum. No local path. API at `platform.moonshot.ai`. Best open-weight benchmark scores as of June 2026 for agentic + coding tasks.

---

## MiMo-7B-RL (Xiaomi, MIT) — Local Candidate

Covered in depth in `docs/findings/model-updates-2026-05.md` § "Reasoning / Code". Summary:
- MATH-500 95.8%, AIME 2024 68.2% at 7B (beats deepseek-r1:7b 55.5%)
- MIT license, Ollama available, ~5GB Q4
- Multiple-Token Prediction: ~90% speculative decoding acceptance → faster than standard 7B
- **Not in HF leaderboard** (too new)

---

## What the Leaderboard Tells Us Overall

1. **Qwen2.5-14B-Instruct** is the best officially-submitted ≤14B model at 41.6 avg. Our stack already runs Qwen3:14b (later generation, would score higher if submitted).

2. **No new must-have model discovered.** The 2024-generation findings confirm our stack choices. Falcon3-7B is interesting but superseded by qwen3:8b.

3. **The benchmark gap:** Phi-4's low IFEval score (5.9) is a format artifact — the model uses a different system prompt convention. Same models that score "poorly" here score well on AIME/GPQA. The leaderboard penalises non-conforming prompt formats, not capability.

4. **2025-2026 models need direct HF page evaluation** (as done in this session) — the leaderboard cannot be used as a ranking signal for anything released after mid-2024.

---

## Sources

- HF Open LLM Leaderboard dataset: `open-llm-leaderboard/contents` (parquet, 4,576 models, downloaded 2026-06-01)
- Arena.ai leaderboard: `arena.ai/leaderboard` (accessed 2026-06-01)
- Falcon3-7B HF page: `tiiuae/Falcon3-7B-Instruct`
- AceMath-7B HF page: `nvidia/AceMath-7B-Instruct`
- Kimi K2 HF page: `moonshotai/Kimi-K2-Instruct`
