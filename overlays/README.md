# Overlay System

An **overlay** is a self-contained package of files, config sections, and AI-agent
instructions that can be installed into any repository. The installer copies files,
creates templates, appends lines, and merges sections into shared files like CLAUDE.md.

## Install an overlay

```bash
./overlays/install-overlay.py <overlay-name> --target /path/to/repo [options]

Options:
  --mode manual|ai     How to handle merge_sections (default: manual = print TODO)
  --yes                Auto-accept AI plan without confirmation
  --backend ollama|claude|auto
  --ollama-model MODEL (default: qwen2.5-coder:14b)
  --backup / --no-backup  Backup files before overwriting (default: on)
  --dry-run            Show actions without writing anything
  --report FILE        Write summary to file
  --report-format text|json
```

## Authoring a new overlay

### 1. Create the directory structure

```
overlays/
  <your-overlay>/
    manifest.yaml       # machine-readable spec (required)
    APPLY.md            # AI-readable merge instructions (required if merge_sections used)
    README.md           # human-readable description
    files/              # files copied verbatim to target repo
    templates/          # files created only if dest is missing
    sections/           # content injected into shared files (e.g. CLAUDE.md)
    prompts/            # overlay-specific prompt overrides (optional)
```

### 2. Write manifest.yaml

```yaml
name: your-overlay
version: 1
description: >
  One-paragraph description of what this overlay provides.

# Copied verbatim. Backed up if dest differs. Make scripts executable.
files:
  script.sh: .claude/tools/script.sh
  tool.py: .claude/tools/tool.py       # .py files are executable — no .sh wrapper needed

# Created from template only if dest does not exist. Never overwrites.
templates:
  starter.md.tmpl: .claude/some-file.md

# Lines appended idempotently (grep before append).
append_lines:
  .gitignore:
    - ".claude/local/"

# Sections injected into shared files using overlay markers.
# The script wraps content with: <!-- overlay:NAME vN --> ... <!-- /overlay:NAME -->
merge_sections:
  CLAUDE.md:
    file: sections/claude-md-section.md
    merge_hint: "insert near the top, before project-specific rules"

# Files requiring manual merge if dest already exists.
# Copied from files/ if dest is missing.
manual_if_exists:
  - .githooks/pre-commit

# AI tool configurations targeted by this overlay.
agent_targets:
  claude-code:
    tools_dir: .claude/tools
    rules_file: CLAUDE.md
```

### 3. Write the section content

`sections/claude-md-section.md` is the content that gets injected into CLAUDE.md.
It should be self-contained — assume the reader has no other context.

**Do not include overlay markers in the section file.** The installer always adds
`<!-- overlay:NAME vN -->` / `<!-- /overlay:NAME -->` around the content. The markers
are never AI-generated; they are always script-generated.

### 4. Write APPLY.md

APPLY.md is read by the AI backend during `--mode ai` merges. It provides placement
rules and retrofit guidance that the JSON schema cannot express.

Required sections:
- **Goal** — what the merge is trying to achieve
- **Placement rule** — where in the target file the section belongs
- **Retrofit rule** — what to do if a simpler/older version already exists:
  - If simpler version: delete it (including heading) and insert full section
  - If verbatim match: wrap with markers instead of duplicating
- **Do not** — explicit prohibitions (don't remove unrelated content, don't add section twice)

### 5. Test the overlay

```bash
# 1. Dry run — see what would happen without touching anything
./overlays/install-overlay.py <name> --target /tmp/test-repo --dry-run

# 2. Fresh install — init a bare repo and install
git init /tmp/test-repo && echo "# Test" > /tmp/test-repo/CLAUDE.md
./overlays/install-overlay.py <name> --target /tmp/test-repo --mode ai --yes

# 3. Verify tools work
/tmp/test-repo/.claude/tools/ref-lookup.sh        # or your tool

# 4. Idempotency — run again, expect all [SKIP]
./overlays/install-overlay.py <name> --target /tmp/test-repo --mode ai --yes
```

## How the AI planner works

For `merge_sections`, `--mode ai` asks the AI for a **JSON plan** (not the full merged
file). The plan specifies `insert_after_line` and optional `delete_ranges`. The script
applies the plan deterministically and always adds markers itself.

Prompts live in `overlays/prompts/`:
- `merge-plan.txt` — prompt template (shared across all overlays)
- `merge-plan-schema.json` — JSON Schema passed to Ollama `format` param
- `merge-section.txt` — legacy full-file prompt (kept for reference)

An overlay can override the shared prompts by placing its own in `<overlay>/prompts/`.
The installer checks the overlay-specific directory first.

## Versioning and updates

When you change an overlay's content, bump `version` in `manifest.yaml`. On next
install, the installer detects `<!-- overlay:NAME vOLD -->` and replaces the section
content, incrementing the marker to `vNEW`. Deterministic — no AI needed for updates.

## Known limitation

The AI planner (14B model) reliably handles fresh installs. For retrofits (replacing an
existing manually-installed section), it may not remove the old section's heading in
one pass. The `--mode manual` default (which prints `[TODO]`) is the safe choice for
retrofits; `--mode ai` is best-effort.

## Next overlay candidates

| Overlay | What it packages |
|---------|-----------------|
| `session-tracking` | session-log.md, session-context.md, tasks.md, resume.sh, rotate-session-log.sh, session-handoff skill |
| `ollama-scaffolding` | CLAUDE.md local-model-first rules, verdict capture hooks, scaffolding template |
| `verdict-hooks` | PostToolUse/Stop/SubagentStop hooks (user-level, not repo-level — different installer target) |
