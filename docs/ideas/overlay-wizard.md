# Idea: Interactive Overlay Wizard

**Status:** Deferred — capture only, not yet planned
**Origin:** Session 40 (2026-03-11) — after completing overlay system

---

## The Gap

`install-overlay.py` works well as a batch script. But the AI merge step is still
"fire and hope" — the planner produces a JSON plan, the script applies it, and any
mistakes show up after the fact. Running it interactively *inside* an AI CLI (Claude Code,
or a future local equivalent) would allow the AI to reason step-by-step, ask clarifying
questions, and confirm before each action.

---

## The Vision

### Step 1 — Overlay wizard as a Claude Code skill

A `/install-overlay` skill (or MCP tool) that runs the installation *conversationally*
inside a Claude Code session:

- Shows the dry-run report and asks "proceed?"
- For merge_sections: presents the current CLAUDE.md, explains what it will change, and
  asks for confirmation or adjustment
- For manual_if_exists: shows both files side by side and asks the user to choose
- Handles unexpected cases through dialogue rather than [TODO] records

Claude Code *is* the AI backend — no Ollama call needed. The merge plan is produced by
the conversation itself.

### Step 2 — Generalized interactive AI CLI wizard pattern

The overlay wizard would be a specific instance of a more general pattern:
a "wizard" that runs a multi-step, stateful workflow inside an interactive AI CLI,
where each step can use the AI for reasoning and the user for confirmation.

This pattern could apply to:
- Onboarding a new repo (run multiple overlays in sequence, confirm each)
- Code migration tasks (find all usages → propose changes → confirm → apply)
- Any workflow that is "mostly deterministic but needs judgment at the edges"

### Step 3 — Portable interactive CLI

Eventually: a local interactive CLI (similar to Claude Code but running against local
models) that can host these wizards. Users who don't have a Claude subscription could
run the overlay wizard against a local Ollama backend in an interactive TUI.

This connects to the broader vision of a local AI CLI (Layer 2 research area).

---

## Key Questions to Answer

1. **Skill vs MCP tool:** A Claude Code skill is simpler (prompt expansion); an MCP tool
   gives the installer access to file system and can run the existing Python code. Which
   is the right hosting mechanism?

2. **State between turns:** The wizard needs to track which steps are done. Options:
   a. Pass state in the prompt (simple, works for short installs)
   b. Write a temp state file and resume from it
   c. Use Claude Code's built-in session context

3. **Fallback to batch mode:** The wizard should degrade gracefully if run non-interactively
   (CI, automation) — same as `--yes --mode ai` today.

4. **Relationship to `test-merge-plan.py`:** The comparison tool already runs multiple
   backends and shows plans side by side. A wizard could let the user *choose* which plan
   to apply when models disagree.

---

## Connection to Existing Work

- `overlays/install-overlay.py` — batch mode foundation
- `overlays/ai-backends.yaml` — backend config already supports `claude-code` type
- `docs/plans/overlay-system-plan.md` — Phase 3+ notes "three modes: manual, AI-assisted, unattended"
- Layer 2 research (`docs/findings/layer2-tool-comparison.md`) — prior work on interactive local AI CLIs
