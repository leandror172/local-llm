## Resuming Multi-Session Work

**On session start:** run `.claude/tools/resume.sh` — outputs current status, last session's Next, the pre-session reading guide, key files, active decisions, and recent commits in ~80-100 lines.
**What it prints is config, not code.** Edit `.claude/resume.yaml` to reorder, retitle, filter, or add sections. A `region:` step names a role in the handoff register, so renaming a `ref:KEY` updates both what resume reads and what the handoff writes, in one edit. Use a `run:` step for anything the overlay does not model.
For deeper context: `ref-lookup.sh current-status` | `ref-lookup.sh active-decisions` | `ref-lookup.sh quick-pointers` | `ref-lookup.sh user-prefs`
**Knowledge index:** `.claude/index.md` maps every topic to its file location. [ref:resume-steps]

## Workflow Rules (HARD REQUIREMENTS)

1. **DO NOT proceed to the next phase automatically** — Always wait for explicit user permission
2. **Step-by-step configuration** — Build config files incrementally, explaining each setting
