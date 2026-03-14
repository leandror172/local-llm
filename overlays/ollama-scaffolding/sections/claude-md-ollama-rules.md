## Local Model Verdict & Retry Policy

**You MUST read `.claude/overlays/local-model-retry-patterns.md` before evaluating
any local model output.** It defines the verdict protocol (ACCEPTED/IMPROVED/REJECTED),
the decision tree for handling imperfect output, and the cold-start grace period.

Key rules (detail in the reference file):
- Evaluate every local model response with an explicit verdict
- Classify imperfect output by defect type, fix scope, and prompt cost — not line count
- First-call timeouts are `TIMEOUT_COLD_START`, not REJECTED — retry immediately
