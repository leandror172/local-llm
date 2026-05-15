# Layer 0 Runtime Reference

Runtime ref blocks for Layer 0 findings. These are cited directly from `CLAUDE.md` via `[ref:KEY]` tags
and looked up by agents via `.claude/tools/ref-lookup.sh`.

Full benchmark data and test methodology → `.claude/archive/layer-0-findings.md`

---

<!-- ref:model-selection -->
### Model Selection Rules
Detailed benchmarks and selection rules → `.claude/archive/layer-0-findings.md`

| Scenario | Model | Notes |
|----------|-------|-------|
| Quick code gen, boilerplate | 8B think:false | my-go-q3, my-python-q3 etc. |
| Medium algorithms | 8B think:false | |
| Complex architecture | 14B think:false | my-architect-q3 (qwen3:14b) |
| Multi-file / long context | 8B (14B can't fit ~4K ctx) | |
| Retry after 8B failure | 14B think:true | |
| Classification / routing | 8B or 4B | my-classifier-q3 |
| Code gen (DPO comparison A) | qwen2.5-coder:14b | my-go-q25c14 — code-specialized, full VRAM |
| Code gen (DPO comparison B) | qwen3:8b-q8_0 | my-go-q3-q8 — same model, higher quant |
| Code gen (quality ceiling) | qwen3:30b-a3b | my-go-q3-30b — hybrid, ~10-20 tok/s |
| Code gen (speed tier) | gemma3:12b | my-go-g3-12b — 3-4× faster than 14B (~32 tok/s), IMPROVED quality (both prompts); good for iterative tasks |

**Future candidates (not yet pulled):**
- `qwen3.5:35b-a3b` (24GB) — released 2026-02-24, architecture update. Revisit in ~4 weeks.
- `qwen3-coder:30b` (19GB) — code-specialized MoE. Pull after qwen3:30b-a3b is validated.
- `gemma3:12b` (~7-8GB Q4) — fits fully in VRAM; **QAT variant** available (`gemma-3-12b-it-qat`) = Quantization-Aware Training, Q4 quality closer to Q8. Multimodal (image+text). Priority benchmark against `my-go-q25c14` on coding tasks. Ollama tag: `gemma3:12b`.
- `gemma3:27b` (~14-16GB Q4) — needs ~4-6GB RAM spillover; dense architecture offloads better than MoE (expect ~20-25 tok/s vs 10-20 for 30B-A3B). QAT variant also available. Only worthwhile if 12B falls short on reasoning. Ollama tag: `gemma3:27b`.
- `gemma4:31b` (~19GB+) — released 2026-04-02, multimodal. Not on Ollama yet as of 2026-04-09. Revisit in ~2 weeks.
<!-- /ref:model-selection -->

<!-- ref:thinking-mode -->
### Thinking Mode Strategy
Full measurements → `.claude/archive/layer-0-findings.md` § "Task 0.8 Findings"

- **`/no_think` does NOT work** — only API parameter `think: false` disables thinking
- Default: `think: false` for all tasks
- Escalate to `think: true` for: complex architecture, retry after failure
- Overhead: 67-84% of Qwen3 tokens are hidden thinking (3-7x slower)
- `think` is an API param, not a Modelfile setting — callers must set it
<!-- /ref:thinking-mode -->

<!-- ref:structured-output -->
### Structured Output (JSON Schema)
Full test results → `.claude/archive/layer-0-findings.md` § "Task 0.7 Findings"

- Always use `format` param — 100% valid JSON with it, 0% without it
- No speed penalty (~0-3% overhead)
- Enum enforcement is reliable — model cannot violate schema constraints
- Without `format`, coding personas write code instead of answering analytical questions
- Combine with `think: false` for fastest structured responses
<!-- /ref:structured-output -->

---

## Other Layer 0 Findings

| Topic | File | Key Takeaway |
|-------|------|-------------|
| Qwen3 vs Qwen2.5 benchmarks | `.claude/archive/layer-0-findings.md` | 4 personas × 6 prompts; hidden thinking tokens discovery |
| 14B performance profile | `.claude/archive/layer-0-findings.md` | 32 tok/s, ~4K context, best for complex single-Q |
| Prompt decomposition results | `.claude/archive/layer-0-findings.md` | 3-stage sweet spot, reduces bug severity not count |
| Few-shot example library | `benchmarks/examples/` | 6 examples (3 backend, 3 visual), `--examples` flag |
