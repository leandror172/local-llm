# Layer 0 Findings Archive

**Archived from:** `.claude/plan-v2.md` (2026-02-11)
**Status:** Layer 0 complete (12/12 tasks)
**Index:** See `.claude/index.md` for topic-to-file map

---

## Benchmark 0.2 Findings

**Run date:** 2026-02-09 | **Models:** 4 personas × 6 prompts (3 backend, 3 visual)

Key discoveries that informed tasks 0.8–0.10:

1. **Hidden thinking tokens (→ task 0.8):** Qwen3's `<think>` blocks are stripped from `message.content` by Ollama but counted in `eval_count`. Result: 75–88% of generated tokens are invisible reasoning. Effective visible tok/s drops from ~51 to ~8 tok/s equivalent. This caused 2/3 backend prompts to time out at 120s. Fix: either disable thinking with `/no_think` for simple tasks, or budget 5–17× more time. Need a per-task strategy.

2. **Visual quality gap (→ task 0.9):** All 6 visual outputs (both models) were rated poor by frontier review. Common failures: incorrect coordinate transforms for rotation, broken collision math, variable shadowing crashes (`for (let fish of fish)`), ugly procedural shapes. Root cause: monolithic "create complete physics simulation" prompts exceed what 7–8B models handle in a single shot. Closing-the-gap technique #3 (decomposition) applies directly: break into shape drawing → physics math → animation loop → integration.

3. **Silent JS crashes (→ task 0.10a):** Qwen3's aquarium output crashed on frame 1 due to a trivial variable shadowing bug. No way to detect this without opening the file. A headless browser (Puppeteer/Playwright) smoke test catching console errors would flag obvious failures automatically.

4. **Backend code validation (→ task 0.10b):** The same class of bugs (const reassignment, undefined variables, type errors) that crash JS at runtime would be caught at compile time in Go/Java. Since `my-coder`'s primary output is backend code, a compilation + static analysis gate (`go build`, `go vet`, `javac`) provides equivalent safety for generated Go/Java snippets. Requires scaffolding: wrap snippet in compilable unit (package declaration, imports, main if needed).

**Backend quality:** Merge intervals was the only near-passing output (A- from both models). Go LRU cache had a use-after-delete bug (Qwen2.5) and an overcomplicated struct (Qwen3). Java CSV parser from Qwen3 timed out even at 300s.

**Performance comparison (backend, visible output only):**
| Model | Avg tok/s | Avg tokens | Thinking overhead |
|-------|-----------|------------|-------------------|
| Qwen2.5-Coder-7B | 66 tok/s | 500–800 | None |
| Qwen3-8B | 51 tok/s (raw) | 3000–9400 | 75–88% hidden |

---

## Task 0.8 Findings: Thinking Mode Strategy

**Run date:** 2026-02-09 | **Tool:** `benchmarks/lib/ollama-probe.py`

**Key discovery: `/no_think` in message content does NOT disable thinking.** Only the API-level `think: false` parameter works. `/no_think` is a soft hint the model can (and does) ignore — it still produced 247-1856 chars of hidden reasoning.

**Overhead measurements (my-coder-q3, same prompt, think vs no-think):**
| Prompt complexity | think:true tokens | think:false tokens | Speedup | Thinking % |
|-------------------|-------------------|--------------------|---------|-----------:|
| Simple (add two ints) | 1,152 | 425 | 3.2x | 67% |
| Medium (merge intervals) | 6,867 | 1,201 | 6.0x | 77% |
| Complex (LRU cache) | 12,206 | 2,006 | 6.9x | 84% |

**Default strategy — `think: false` unless reasoning-critical:**
| Task type | Mode | Rationale |
|-----------|------|-----------|
| Simple code gen | `think: false` | 3x faster, near-identical output |
| Medium algorithms | `think: false` | 6x faster, adequate first-pass quality |
| Complex architecture | `think: true` | Correctness-critical; thinking helps plan structure |
| Classification / routing | `think: false` | Speed matters, reasoning overkill |
| Creative / visual | `think: false` | Thinking didn't improve quality in benchmarks |
| Retry after failure | `think: true` | Escalate with reasoning if first attempt has bugs |

**One-line rule:** Default `think: false`, escalate to `think: true` for complex reasoning or retries.

**Implementation notes:**
- `think` is an API parameter, not a Modelfile setting — callers (MCP server, scripts) must set it
- Two calls with `think: false` is still faster than one call with `think: true` on complex prompts
- Qwen2.5-Coder has no thinking mode — this strategy only applies to Qwen3 models

---

## Task 0.5 Findings: Qwen3-14B Performance

**Run date:** 2026-02-09 | **Tool:** `benchmarks/lib/ollama-probe.py`

**VRAM:** 10.4 GB / 12 GB with 14B loaded — context limited to ~4K tokens.

**14B vs 8B on complex prompt (LRU cache):**
| Model | Mode | Tokens | Wall time | tok/s | Content chars |
|-------|------|--------|-----------|-------|---------------|
| Qwen3-8B | think:false | 2,006 | 36s | 56 | 6,807 |
| Qwen3-8B | think:true | 12,206 | 252s | 49 | 8,003 |
| Qwen3-14B | think:false | 1,726 | 54s | 32 | 5,614 |
| Qwen3-14B | think:true | 7,616 | 257s | 30 | 5,252 |

**Key findings:**
- 14B is more concise (14% fewer tokens, tighter code)
- 14B reasons more efficiently (26K vs 43K chars of thinking — 40% less)
- Speed: 32 tok/s (1.7x slower than 8B) — manageable for single-question use
- VRAM constraint: ~4K context max, unsuitable for multi-file or long conversations

**Model selection rule:**
| Scenario | Model |
|----------|-------|
| Quick code gen, boilerplate | 8B think:false |
| Medium algorithms | 8B think:false |
| Complex architecture | 14B think:false |
| Multi-file / long context | 8B (14B can't fit) |
| Retry after 8B failure | 14B think:true |
| Classification / routing | 8B or 4B |

---

## Task 0.7 Findings: Structured Output (JSON Schema)

**Run date:** 2026-02-10 | **Tool:** `benchmarks/lib/ollama-probe.py` + `benchmarks/lib/run-structured-tests.sh`

**Test matrix:** 5 prompts × 2 models × 2 variants (format=on vs format=off) = 20 API calls.
Prompts map to real use cases: expense classification (L5), bug analysis (L4), model routing (L1), function metadata (L3), number describe (baseline).

**Headline: grammar-constrained decoding works flawlessly.**

| | format=on (constrained) | format=off (instructed) |
|--|------------------------|------------------------|
| Valid JSON | **10/10 (100%)** | **0/10 (0%)** |
| Schema-compliant | 10/10 | N/A |
| Enum adherence | 10/10 | N/A |

**Without `format`, coding personas never produce JSON.** In 8/10 free-form runs, both models wrote code (Java classes, Go functions) instead of answering the analytical question. The `format` parameter doesn't just format output — it shifts the model from code-generation mode to analysis/classification mode.

**Speed impact:**
| Model | format=on tok/s | format=off tok/s | Per-token overhead |
|-------|----------------|-----------------|-------------------|
| Qwen3-8B | 56.7 | 57.1 | ~0% (negligible) |
| Qwen2.5-Coder-7B | 63.4 | 65.4 | ~3% |

Per-token speed is unaffected. Qwen2.5 shows a wall-time startup overhead (5-7s on some runs, likely grammar compilation) that Qwen3 does not exhibit.

**Implementation rules for downstream layers:**
1. Always use `format` for structured tasks — it is not optional for coding personas
2. No speed penalty — safe to use in hot paths (MCP server responses, classification)
3. Enum enforcement is reliable — define allowed values in schema, model cannot violate them
4. Combine with `think: false` for fastest structured responses

---

## Task 0.9 Findings: Prompt Decomposition for Visual Tasks

**Run date:** 2026-02-10 | **Tool:** `benchmarks/lib/decomposed-run.py` + `benchmarks/lib/run-decomposed.sh`

**Approach:** Incremental build — each stage produces a complete runnable HTML file, adding one feature. Previous stage's output becomes context for the next. Tested two variants: v1 (prose instructions) and v2 (explicit math formulas with step-by-step algorithms).

**Results summary (decomposed grade vs monolithic grade):**

| Prompt | Model | Monolithic | Decomposed | Change |
|--------|-------|-----------|------------|--------|
| Bouncing Ball v2 | Qwen3-8B | C+ | D | ↓ (const crash, sign errors) |
| Bouncing Ball v2 | Qwen2.5-7B | D+ | C- | ↑ (follows 7-step structure) |
| Heptagon | Qwen3-8B | C+ | B+ | ↑↑ (edge-normal works, balls work) |
| Heptagon | Qwen2.5-7B | D | C | ↑ (algorithm correct, const crash) |
| Aquarium | Qwen3-8B | C+ | C | ~ (fish=ellipse, scope bugs) |
| Aquarium | Qwen2.5-7B | D+ | C- | ↑ (fish+tail+eye, bubbles spawn) |

**What decomposition consistently fixes:**
1. Feature completeness — missing elements (heptagon drawing, bubble spawning, ball numbers) now appear
2. Persistent state — pebbles, light rays no longer re-randomized per frame
3. Shape quality — fish upgraded from triangles to ellipse bodies with fins and eyes
4. Algorithm structure — explicit formulas get followed as a sequence

**What decomposition doesn't fix:**
1. `const` vs `let` — systematic pattern: models default to `const` for formula variables, crash when prompt shows mutation (`/=`). Appears in 4/6 formula-heavy runs
2. Coordinate-space confusion — bouncing ball collision response still wrong in both v1 and v2
3. Variable scoping — shadowing, undefined references in complex multi-stage outputs

**Key insight: decomposition reduces bug severity.** Monolithic bugs were fundamental design errors (wrong algorithm, missing features). Decomposed bugs are implementation/transcription errors (const vs let, sign errors, scope). The latter are detectable by runtime validation — strongly motivating task 0.10.

**Practical rules for prompt decomposition:**
1. 3 stages is the sweet spot for 7-8B models (more stages = more context growth)
2. Explicit formulas help with algorithm structure but use `let` in examples, never show `/=` on declared variables
3. Each stage prompt should say "modify the file above" to prevent rewrites from scratch
4. `--start N --inject file.html` allows retrying individual stages without rerunning the whole pipeline
5. Runtime validation catches the #1 remaining bug pattern (const crash) instantly

---

## Layer 0 Task Completion Summary

All 12 tasks completed 2026-02-11:

| ID | Task | Key Result |
|----|------|-----------|
| 0.1a | Pull Tier 1 models | qwen3:8b, qwen3:14b, qwen3:4b-q8_0 (4m 50s) |
| 0.1b | Create Qwen3 personas | my-coder-q3, my-creative-coder, my-creative-coder-q3 |
| 0.2 | Benchmark Qwen3 vs Qwen2.5 | 4×6 matrix; hidden thinking tokens discovered |
| 0.3 | Rewrite system prompts | ROLE/CONSTRAINTS/FORMAT skeleton for all 4 Modelfiles |
| 0.4 | Few-shot example library | 6 examples, `--examples` flag, 47% token reduction verified |
| 0.5 | Test Qwen3-14B | 32 tok/s, concise, ~4K context limit |
| 0.6 | Pull Tier 2+3 models | llama3.1, nomic-embed, deepseek-r1, deepseek-coder-v2 |
| 0.7 | Structured output testing | 100% JSON compliance with `format`, 0% without |
| 0.8 | Thinking mode management | `think: false` default; API param, not `/no_think` |
| 0.9 | Prompt decomposition | 3-stage pipeline; fixes features, not const bugs |
| 0.10a | Frontend runtime validation | Puppeteer headless; 22/30 pass, catches const/shadow |
| 0.10b | Backend runtime validation | Go build+vet gate; 5 fixtures tested |
