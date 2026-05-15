# Deferred Infrastructure — Completed Items

Items from `ref:deferred-infra` in `tasks.md` that have been completed. Extracted to keep the active backlog lean.

---

- **ref-integrity checker** (COMPLETE, session 39, branch `feature/ref-integrity-checker`). `check-ref-integrity.py`: 4 checks (dangling refs, unclosed blocks, duplicate defs, orphaned blocks). Fence-aware (skips ``` blocks), excludes `.git/`/`node_modules/`/`.venv/`, supports `--root` for cross-repo. `check-ref-integrity.sh`: thin bash wrapper. `.githooks/pre-commit`: gates on staged `*.md` files. Install: `git config core.hooksPath .githooks`. LLM repo exits clean; expense repo revealed 1 dangling ref + 3 duplicate block defs.

- **ref_lookup cross-repo support** (COMPLETE, session 39). `ref-lookup.sh` now accepts `--root /abs/path` to override `PROJECT_ROOT`; MCP `ref_lookup` tool adds optional `path: str` param that passes `--root` to the script. Validated: cross-repo lookup of expense repo refs works, `--list` enumerates that repo's keys, bad path returns clear error.

- **ollama-bridge: context_files input for generate_code / ask_ollama** (COMPLETE, session 39, branch `feature/context-files-param`). `ContextFile` Pydantic model (`path`, `start_line`, `end_line`); `_build_context_block()` reads files server-side and prepends as `<context>` fenced blocks. Added to both `generate_code` and `ask_ollama`. Absolute paths enforced; errors returned as strings. FastMCP generates proper nested JSON schema from the Pydantic model.

- **ollama-bridge: log prompt/completion token counts + frontier savings estimate** (COMPLETE, session 38, PR #10). `prompt_eval_count`, `prompt_chars`, `response_chars`, and `claude_tokens_est` ((prompt+system+response chars)/4) now logged in every `calls.jsonl` entry. Verdict instruction in CLAUDE.md + scaffolding-template.md updated: ACCEPTED/IMPROVED verdicts include a rough mental chars/4 estimate — no file reads, no code execution.

- **ollama-bridge: PostToolUse hook for structured verdict capture** (COMPLETE, session 39, PR pending). `PostToolUse` hook injects `[VERDICT prompt_hash=N]` template via `hookSpecificOutput.additionalContext`; `Stop`/`SubagentStop` hooks scan the correct transcript (main vs `agent_transcript_path`) and append `{type:"verdict", prompt_hash, verdict, reason, est_claude_tokens}` to `calls.jsonl`. Hooks promoted to `~/.claude/settings.json` (user-level) so they fire in all Claude Code sessions, not just this repo.

- **Claude Code user-config backup/tracking** (COMPLETE, session 41). Private repo `leandror172/dotfiles` at `~/workspaces/dotfiles/`. `backup.sh` (OS-aware, WSL2+Linux) + `install.sh` (restore, top-of-file variables for machine-specific paths). `SessionStart` hook in `~/.claude/settings.json` auto-runs backup. Covers: `claude-code/` (user-level `~/.claude/`), `claude-projects/llm/` (memory only), `claude-desktop/` (Windows AppData). First commit pushed.

- **Refine IMPROVED verdict workflow for Ollama code generation** (COMPLETE, session 42). Policy authored in `docs/scaffolding-template.md` § "Handling Imperfect Output: Decision Tree". Replaced "3 lines" threshold with 3-dimension heuristic (defect type / fix scope / prompt cost). Stubs-then-Ollama codified as named retry pattern. Runtime ref block: `ref:local-model-retry-patterns`. Propagated to expense repo via `ollama-scaffolding` overlay (PR #8 in expense repo). Also: `warm_model` MCP tool built (in-flight tracking + safe eviction), cold-start grace period policy added.

- **MCP `create_persona` / `copy_persona` tools** (COMPLETE, session 45, PR #21). `create_persona` accepts name/role/constraints/base_model/temperature; `copy_persona` parses source Modelfile via regex. User-level `create-persona` skill (3 patterns). Added to `ollama-scaffolding` overlay. Also: timeout param added to `ask_ollama`/`generate_code` for 30B+ models; context sizes audited and upgraded (8B: 8K→32K, 35 Modelfiles updated); DeepSeek models added to `models.yaml`; model config extracted from Python to YAML.

- **MCP `warm_model` tool (Option 1 — bundled)** (COMPLETE, session 43, PR #15). In-flight tracking (mark_inflight/mark_complete/is_busy) wraps chat() in try/finally. list_running() wraps /api/ps. unload_model() wraps keep_alive:0. warm_model orchestrates: check loaded → validate model exists → check busy → evict → warm with trivial prompt. Bug fixed: validate before evict (was "evict then 404" on bad model names). **Caveat:** in-flight check is single-session only — each Claude Code session has its own MCP server process. Cross-session protection needs Option 2 (file-based coordination layer).

- **LTG Phase 1 — score remaining 4 corpus files** (COMPLETE — Claude draft session 57; user HTML-viz track session 58; two-rater reconciliation session 58, Branch C). Final 8/8 adjusted: qwen3:14b ✅ winner (2.44 / 2.61 Claude/User), qwen3:8b ✅ backup (2.27 / 2.63), coder ❌ (1.76 / 2.16 — borderline under user), gemma ❌ (1.61 / 1.82). Both rater tracks identical ranking + verdicts. User scoring at `retrieval/runs/manual-rubric.md` + `retrieval/runs/ltg-rater-20260416-181839-20260430-215756Z.json`. Production routing decision: `ref:ltg-phase1-routing-hypothesis`.

- **LTG Phase 1 — determinism re-runs on winner** (COMPLETE, session 59). Branch C confirmed as model property. Containment/post-pass guard added for qwen3:14b on dense single-line bullet lists.

- **LTG Phase 1 — MoE model extractor eval** (COMPLETE, session 59). qwen3:30b-a3b: TTFT > 9 min, unusable. qwen3-coder:30b: fails adjusted threshold (2.06). Neither advances. See `ref:ltg-extractor` in `retrieval/DECISIONS.md` for the frozen extractor decision.
