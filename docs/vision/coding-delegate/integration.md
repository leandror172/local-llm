# Integration: how this touches the existing estate

<!-- ref:delegate-conventions-mapping -->
## The conventions doc, mechanized (the design's core justification)

`ref:local-model-conventions` (`.claude/overlays/local-model-conventions.md`, shipped by the
`ollama-scaffolding` overlay) is today a manual protocol. This system turns each rule into a
component:

| Convention (manual today) | Becomes (component) |
|---|---|
| "Describe behavior, not implementation" prompt style | Prompt compiler template (P3) |
| CONSTRAINTS block (single responsibility, ≤15-line bodies, naming) | Structural checks in the loop gate (P2) + prompt compiler (P3) |
| Tests-first, tests as context | S3 ordering: test deliverable → review → implementation run |
| Callers included in context (0-verdict prevention) | Intake/fetcher rule (P3) |
| Serialize calls / VRAM ceiling | Worker FIFO + phase batching (`ref:delegate-gpu-policy`) |
| Retry budget 3–4 attempts before escalating | Iteration + fresh-start budgets (S11) |
| Tier 1 → tier 2 model escalation | Mechanized escalation ladder (P2) |
| Stubs-then-Ollama retry pattern | Fresh start with stub re-anchoring (S11) |
| Cold-start grace (TIMEOUT ≠ verdict 0) | Worker warm-up handling — the recorded protocol violation becomes impossible |
| Verdict 0/1/2 on every call | `auto_verdict` per iteration + `curated_verdict` from Claude's review (S17) |
| `refs` / `context_files` / `output_file` / `patch_file` | Reused as-is — the fetchers and write path already exist in `mcp-server/` |
<!-- /ref:delegate-conventions-mapping -->

<!-- ref:delegate-estate-map -->
## Estate map

**Consumes (exists today):**
- `mcp-server/` ollama-bridge: async httpx client, persona/language routing, `refs`+
  `refs_root`, `context_files`, `output_file`/`output_only`, `patch_file`, `warm_model`
  in-flight guards, `calls.jsonl` logging (gains `run_id` + `auto_verdict` fields).
- `evaluator/`: Phase 1 validators (go build+vet, shellcheck, Python compile(), javac, JSON
  schema) + Phase 2 LLM-judge rubrics (7 rubrics; one criterion per call). The loop's gate.
- `benchmarks/lib/decomposed-run.py`: the `steps:` mechanism's ancestor.
- Personas + `personas/registry.yaml`: coder/judge/triage roles; same-base switching
  (`my-*-q25c14` family) for zero-swap judge.
- Git worktrees convention (`ref:git-worktrees`); git-safety protocol for any destructive op.
- Layer-0 findings: `format` structured output (`ref:structured-output`), think-mode policy
  (`ref:thinking-mode`), 3-stage decomposition.

**Feeds / advances (planned estate):**
- **T-81** (installer `--mode ai` preview + timeout): P1's first client candidate — solved
  structurally rather than fixed in place.
- **T-77** (signature/doc extractor primitive): this system is its *second consumer*
  (compact API surface into prompts) — strengthens T-77's case; do not block on it.
- **T-76** (model-registry shared library): the worker's model/role/escalation config is
  plausibly the *third internal consumer* of the registry shape — may fire T-76's trigger.
  Watch for it at P1/P2 plan time.
- **T-55** (handoff MCP migration): shares the submit-inline + handle pattern; whichever
  ships first informs the other.
- **T-21** (Ollama coordination layer): the named horizon for real priority/preemption
  (V-D13); do not build early.
- **T-14** (hook-based auto-resume): adjacent mechanism for V-D12 monitor injection.
- **M-P1b/P2** (tiny-model classifier benchmark: qwen3.5:0.8b/2b, phi4-mini vs qwen3:4b-q8_0):
  gains a product consumer — in-loop failure triage (P6).
- **Layer 7 (7.6–7.9)**: SFT/DPO dataset builders get per-iteration labeled data; the
  "500+ entries ≈ 1 year" estimate collapses to weeks (`ref:delegate-evidence-dpo`).
- **plan-v2 positioning:** this vision *references, does not rewrite*, plan-v2 (user decision
  2026-07-11). It realizes: Layer 9.3 (self-refinement jobs) as the loop; Layer 8's
  coordination shape with the correction that *Claude* is the coordinator (not a local
  architect persona); Layer 7.10 (context pre-processor) as the P3 assembly stage; routing
  Pattern B (frontier delegates down) fully realized; closing-the-gap #10 (best-of-N) and
  #14 (self-refinement/cascade) as loop policies.
- **LTG (sibling repo `latent-topic-graph`)**: Phase 6 MCP retrieval tools become P3
  fetchers; dependency direction is delegate→LTG (products depend on primitives; never
  product↔product — topology rule, `ref:model-registry-library-decision`).

**Constraints inherited (from CLAUDE.md / findings):**
- 12GB VRAM; one 14B resident; ~15s warm load from the ext4 store; 32K ctx personas
  (`ref:model-selection`); q8_0 KV cache; Ollama on `:11435` with `:11434` metrics proxy;
  Ollama wedge failure mode (loaded-but-unresponsive → restart); host-RAM budget for 30B
  partial offload (`.wslconfig memory=24GB`); bash-wrapper whitelist convention for all new
  entry points; `.claude/local/` for anything sensitive.
<!-- /ref:delegate-estate-map -->

<!-- ref:delegate-cross-repo -->
## Cross-repo threads opened by this session

- **web-research**: field report delivered to
  `~/workspaces/web-research/docs/reports/2026-07-11-field-report-llm-prior-art-run.md`
  (5 defects D1–D5 + proposed fixes + triage order; D2 = the auditor's non-discriminating
  verdict, same defect class as session 111's installer findings). The two-agent comparison
  method (frontier arm vs web-research arm, identical questions, operational appendix) is
  reusable for future web-research regression checks — the full appendix lives in
  `docs/research/coding-subagent-prior-art-webresearch.md`.
- **latent-topic-graph**: no action now; P3 will consume its Phase 6 MCP tools when both
  exist. Engine sessions continue there per S-D7 cadence.
- **Clones** (`~/workspaces/clones/`): survey verdicts final — claude-code (patterns only,
  proprietary), open-multi-agent (MIT, LoopDetector + tool-calling stance), others
  irrelevant. Navigation aid: `claude-code-sourcemap/`. Full citations:
  `docs/research/coding-subagent-clones-survey.md`.
<!-- /ref:delegate-cross-repo -->
