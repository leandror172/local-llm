## Local Model Usage Policy

**You MUST read `.claude/overlays/local-model-conventions.md` before calling or
evaluating any local model.** It covers what to do before a call (prompting,
when to call, serialization, context files) and after (verdict protocol 0/1/2,
the imperfect-output decision tree, cold-start grace period, retry budget).

Key rules (detail in the reference file):
- Prompt by describing behavior — signature, rules, edge cases, test cases — not
  literal code, call sequences, or embedded string values
- Try the local model for every new file or function >~5 lines, all session — a
  past `0` verdict is not a reason to skip; pass better context instead
- Serialize codegen calls — 3+ concurrent requests exceed the VRAM budget, and
  different-model parallel is worse than same-model parallel
- Evaluate every local model response with an explicit verdict
- Classify imperfect output by defect type, fix scope, and prompt cost — not line count
- First-call timeouts are `TIMEOUT_COLD_START`, not 0 (rejected) — retry immediately
