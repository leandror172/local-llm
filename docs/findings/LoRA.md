This file is not directly about the project: it is an output about something that I learned about, and questioned Claude.

 About RAG with embeddings: that technique is (or sounds like) exactly what I've been thinking that "there must be a way to inject 'extra training' into the existing model, with a way that is cheaper
  than inputing a textual description (including the SYSTEM prompt in personas), so that we can better 'parameterize' a model/persona with more detail of 
 the behavior we want, while using up less
  context/tokens; in fact, since the models themselves work through vectors/matrixes multiplications and whatnot, injecting this directly into the model - or an extra layer incorporated into the model
  on-demand, seems to be the way, and something that should theoretically be possible... so an 8B model could, over time, be 'trained' to get better at what we want to do, by improving and injecting this
   layer, and have it be the customization and learning layer... and extra layers could be added to different processing (and even reused when upgrading to another model)". And it just occurred to me,
  that is this could truly be an extra "layer", it could process a result from a model (before output), when perhaps not "all" of the "model" needs to be loaded into memory, when applying this (or a
  different) extra layer. But this is starting to sound like how AirLLM might work (and also not the most important point).
  So, could this be used to enhance the local models we've been testing, improving their benchmark (and real use) results, in the way that I was thinking? And/or how limited this would be?

● You've independently arrived at several real, named techniques. Let me map your intuitions to what exists.

  ---
  What You're Describing is Real, and Has Multiple Names

  ★ Insight ─────────────────────────────────────
  Your core intuition — "inject learned behavior directly as matrices, cheaper than text prompts, detachable, reusable" — is essentially the definition of LoRA (Low-Rank Adaptation). You reinvented it from
  first principles, which means you understood the problem correctly.
  ─────────────────────────────────────────────────

  The Problem LoRA Solves

  A 7B parameter model is a collection of weight matrices — large 2D arrays of floating point numbers, totaling ~14GB at full precision. Full fine-tuning means adjusting all 7 billion of those numbers for your
   task. Requires 100GB+ of compute memory. Impractical on a 12GB GPU.

  LoRA's insight: for any weight matrix W (shape d×d), you don't need to change the whole thing. You can approximate the change you want as the product of two thin matrices A and B:

  New behavior = W + ΔW
              = W + (A × B)

  Where:
    W:  4096 × 4096 = 16.7 million parameters (frozen)
    A:  4096 × 8    =    32,768 parameters     (trained)
    B:  8    × 4096 =    32,768 parameters     (trained)
    rank r=8 → 256x fewer parameters to train

  The pair (A, B) is the LoRA adapter — a small file (10–200MB) that captures the learned behavioral change. The base model is frozen. You only train the adapters.

  This is exactly your "extra layer incorporated on-demand" — the adapter is loaded alongside the base model, and its output is added to the base model's output at each layer it's applied to.

  ---
  QLoRA: Feasible on Your RTX 3060

  QLoRA (Quantized LoRA) takes this further: load the base model in 4-bit quantization (fitting a 7B model in ~4GB VRAM), train LoRA adapters in float16. The base model's weights never change; only the small
  adapters are trained in full precision.

  For a 7-8B model on 12GB VRAM:
  - Base model: ~4-5GB (4-bit quantized)
  - LoRA adapters: ~100-500MB in memory during training
  - Training overhead: ~2-4GB
  - Total: fits in 12GB with room to spare
  - Training time on your expense dataset (~700 examples): roughly 5–20 minutes

  ---
  The "Reusable Across Model Upgrades" Question

  This is where the picture gets more complicated. Your intuition that an adapter "could be reused when upgrading to another model" is partially correct, but with constraints:

  ┌───────────────────────────────────────────────────────────┬───────────────────────┬────────────────────────────────────────────────────────────────┐
  │                         Scenario                          │        Works?         │                              Why                               │
  ├───────────────────────────────────────────────────────────┼───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ Qwen2.5-7B adapter → same Qwen2.5-7B, larger quantization │ ✅ Yes                │ Identical architecture                                         │
  ├───────────────────────────────────────────────────────────┼───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ Qwen2.5-7B adapter → Qwen2.5-14B                          │ ⚠️ Partial            │ Same family, different dimensions — needs re-projection        │
  ├───────────────────────────────────────────────────────────┼───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ Qwen2.5-7B adapter → Qwen3-8B                             │ ❌ No direct transfer │ Different architecture, weight shapes don't align              │
  ├───────────────────────────────────────────────────────────┼───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ Conceptual knowledge → new fine-tune                      │ ✅ Via data           │ Re-train adapter on same correction log against new base model │
  └───────────────────────────────────────────────────────────┴───────────────────────┴────────────────────────────────────────────────────────────────┘

  The correction log (your behavioral training data) is the real reusable asset — not the adapter file itself. If you upgrade from Qwen2.5-7B to a better model, you re-run QLoRA training on the same data
  against the new model. The adapter is the product of (base model × training data), and only the training data transfers cleanly.

  ---
  On AirLLM and Layer-by-Layer Inference

  Your intuition that "not all of the model needs to be in memory when applying the extra layer" maps to two different real things:

  AirLLM / layer offloading: Transformer models are made of N sequential layers (Qwen3-8B has 32 layers). AirLLM loads one layer at a time from disk to GPU, runs it, streams the activation forward, then
  offloads that layer. This allows running 70B models on 8GB VRAM. Very slow (10–100x slower than full-VRAM inference), but works. Ollama does a simpler version of this with its GPU layer count parameter.

  What this means for LoRA: LoRA adapters are applied per-layer. In theory you could apply an adapter only to layers 20–32 (the "reasoning" layers) and skip the early embedding layers. In practice, most
  frameworks merge the LoRA into the base weights at load time or apply it uniformly during inference. The selective-layer idea is valid architecturally but not yet a mainstream feature in Ollama/llama.cpp.
  ---
  The Fundamental Constraint

  ★ Insight ─────────────────────────────────────
  Fine-tuning adjusts how a model expresses its existing capabilities. It cannot add reasoning capacity that wasn't there. A 7-8B model's hard limits — output budget, multi-step reasoning depth, long-context
  coherence — are set by parameter count and pre-training compute. QLoRA won't change those ceilings.
  ─────────────────────────────────────────────────

  Your Layer 4 benchmark findings already identified the root causes precisely:

  ┌───────────────────────────────────────────┬─────────────────────────────────────────┬──────────────────────────────────────────────┐
  │                  Finding                  │               Root cause                │                Fine-tunable?                 │
  ├───────────────────────────────────────────┼─────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ ~400 token reliable output budget         │ Attention coherence over long sequences │ ❌ No — architectural limit                  │
  ├───────────────────────────────────────────┼─────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Logic errors (wrong arg count, bad regex) │ Reasoning capacity                      │ ❌ Barely — only for seen patterns           │
  ├───────────────────────────────────────────┼─────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Mechanical errors (quoting, array syntax) │ Pattern reinforcement                   │ ✅ Yes — this is what fine-tuning excels at  │
  ├───────────────────────────────────────────┼─────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Prompt decomposition helps                │ Output budget constraint                │ ✅ Indirectly — smaller tasks fit the window │
  ├───────────────────────────────────────────┼─────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ MUST constraints fix style but not logic  │ Same as above                           │ ✅/❌ Split                                  │
  └───────────────────────────────────────────┴─────────────────────────────────────────┴──────────────────────────────────────────────┘

  ---
  What Fine-Tuning Actually Buys You on Coding Tasks

  Real wins (~5–20% improvement in affected areas):

  1. Baking in persona constraints
  Right now, your constraint headers ("MUST use set -euo pipefail", "NEVER use ${array[@]}") cost 300–500 tokens per prompt. If you fine-tune on (prompt + constraints, correct output) pairs, that behavior
  becomes default without the tokens. Smaller context → more room for actual task, faster inference, fewer places for the model to "forget" a constraint mid-generation.

  2. Fixing mechanical patterns specific to your stack
  If Qwen3-8B consistently mis-formats Go error wrapping, or always gets excelize cell reference syntax wrong — fine-tuning on corrected examples of those patterns will fix them. Not because the model now
  "understands" better, but because those patterns are now reinforced in the weight distribution.

  3. Instruction format alignment
  Making the model reliably respond in specific structured formats you've designed (edit blocks, plan → code splits, specific JSON schemas) without needing to re-explain the format each time.

  Not real wins (won't help):

  Multi-file architectural reasoning — understanding how a new feature interacts with existing code across 5 files requires holding a large working set in attention. 8B model, hard limit.

  Novel complex logic — the shell benchmark failures (wrong printf arg count, malformed regex) where the model "almost" got it right but made a reasoning error — fine-tuning on the correct output for those
  specific prompts would help only if you then test on nearly identical prompts. It won't generalize to new complex prompts.

  Long generation quality — generating a complete 300-line bash script without errors. The ~400 token reliable window is a property of how the model was trained at scale. QLoRA won't push it to 800.

  ---
  The Data Problem for Your Use Case

  Your Layer 4 benchmarks generated exactly the right shape of data:
  input:  benchmark prompt (e.g., sh-01-log-analyzer)
  wrong:  model's actual output (the failing generation)
  right:  the correct solution (ground truth)

  That (input, right_answer) pair is a fine-tuning example. But:

  - Layer 4 produced maybe 20–40 benchmark prompts across shell, Python, Java
  - Meaningful fine-tuning on coding tasks needs hundreds to thousands of (prompt, correct) pairs
  - Generalizable improvement needs diverse examples, not just your specific benchmark tasks

  What you have is enough to fix the specific patterns that failed in your specific benchmarks. It's not enough to broadly improve the model on new coding tasks it hasn't seen.

  ---
  Where It Actually Gets Interesting

  The "bake in the persona" use case is the most practical near-term win:

  You've spent significant effort in Layer 3 engineering persona constraints that reliably improve output quality. Those constraints work through the context window — they're text taking up tokens every single
   call. A fine-tuned adapter that makes those behaviors default for the model would mean:

  Before fine-tune:
    [500 token MUST/NEVER constraint block]
    [actual task prompt]
    → model follows constraints ~85% of the time

  After fine-tune on (task, correct_constrained_output) pairs:
    [actual task prompt only]
    → model follows constraints ~85% of the time
    + 500 tokens freed for actual task
    + faster inference

  The quality ceiling doesn't move much. The efficiency improves meaningfully.

  ---
  Honest Assessment for Frontier-Gap Tasks

  For the tasks you mentioned — OpenCode/Claude Code equivalent, hiring helper — the gap you're experiencing is not primarily about fine-tuning opportunities:

  Coding assistant (OpenCode-style):
  The frontier model advantage here is mostly: understanding large codebases, multi-file reasoning, architectural judgment. These require holding large context coherently. Fine-tuning won't change that. The
  practical path is what Layer 4 already showed: decompose tasks into 8B-sized units, use 14B for complex reasoning, escalate to frontier for architectural decisions.

  Hiring helper:
  CV analysis + question generation is document understanding + structured output. This is actually closer to the 8B capability boundary than coding — it's shorter documents, more formulaic reasoning.
  Fine-tuning on examples of good CV analyses would help consistency here more than for coding. This is a better QLoRA candidate than making it a better general coder.

  ---
  The Realistic Roadmap

  ┌─────────────────┬───────────────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────────┐
  │      Phase      │                                   What                                    │                             Expected gain                             │
  ├─────────────────┼───────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
  │ Now (Layer 5-6) │ Prompt engineering, decomposition, persona constraints                    │ Already captured in Layer 4                                           │
  ├─────────────────┼───────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
  │ Layer 7         │ Fine-tune on correction logs (expense + any task with collected feedback) │ Fix mechanical patterns, bake in personas, ~5-15% on affected tasks   │
  ├─────────────────┼───────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
  │ Later           │ Larger base models as they improve (Qwen4, etc.)                          │ The real quality leap — new model generations, not fine-tuning        │
  ├─────────────────┼───────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
  │ Much later      │ QLoRA on collected benchmark failures                                     │ Only if you've accumulated hundreds of (prompt, correct_output) pairs │
  └─────────────────┴───────────────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────┘

  ★ Insight ─────────────────────────────────────
  The most powerful lever you have right now isn't fine-tuning — it's the cascade pattern: try local model first, detect low confidence or failure, escalate to 14B or frontier. You get local model speed/cost
  for the 70–80% of tasks that fit the 8B window, and frontier quality on the 20–30% that genuinely need it. Fine-tuning makes the 70% slightly better. The cascade makes the whole system reliable.
  ─────────────────────────────────────────────────