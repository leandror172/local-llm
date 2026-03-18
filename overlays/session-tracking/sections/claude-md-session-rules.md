## Resuming Multi-Session Work

**On session start:** run `.claude/tools/resume.sh` — outputs current status, next task, recent commits in ~40 lines.
For deeper context: `ref-lookup.sh current-status` | `ref-lookup.sh active-decisions`
**Knowledge index:** `.claude/index.md` maps every topic to its file location. [ref:resume-steps]

## Workflow Rules (HARD REQUIREMENTS)

1. **DO NOT proceed to the next phase automatically** — Always wait for explicit user permission
2. **Step-by-step configuration** — Build config files incrementally, explaining each setting
