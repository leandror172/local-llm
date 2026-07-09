"""The handoff product: a register-driven deterministic write transaction.

Claude decides *content*; the pipeline does *read + write*. No model runs here.
Safety core (`locator` via `..register`, `applier`, `verifier`) is stdlib-only.
See `ref:handoff-pipeline-map`.
"""
