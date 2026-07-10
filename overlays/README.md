# Overlay System

An **overlay** is a self-contained package of files, config sections, and AI-agent
instructions that can be installed into any repository. The installer copies files,
creates templates, appends lines, and merges sections into shared files like CLAUDE.md.

## Install an overlay

```bash
./overlays/install-overlay.py <overlay-name> --target /path/to/repo [options]

Options:
  --mode manual|ai        How to handle merge_sections (default: manual = print TODO)
  --yes                   Auto-accept AI plan without confirmation
  --backend ID            Backend id from ai-backends.yaml, or 'auto' (default: auto)
  --model MODEL           Override model for the selected backend (+think suffix supported)
  --install-level user|project  Where the shim/skill/hooks land: user → ~/.claude/,
                          project → .claude/ per-repo (default: user). Pipeline .py
                          modules always go to ~/.claude/tools/handoff/ regardless.
  --backup / --no-backup  Backup files before overwriting (default: on)
  --dry-run               Show actions without writing anything
  --verify                Read-only drift check (see below)
  --report FILE           Write summary to file
  --report-format text|json
```

## Verify an installed overlay (--verify)

`--verify` is a **read-only** check. It never writes, backs up, or creates anything —
safe to run at any time.

It asks a **different question per kind of ownership**, because byte-equality is the
wrong question for a file the repo owns (T-82):

| Ownership | Question | Gates? |
|---|---|---|
| Overlay-owned (`files`, `user_files`) | Are the bytes what we shipped? | yes — real drift |
| `merge_sections` | Is the version marker current? | yes — behind |
| User-managed (`templates`, `manual_if_exists`) | Do the register's locators resolve? | see below |

A session log diverges from its starter template the moment a repo holds one session, and
a per-repo register diverges by design. Gating on those made `--verify` exit 1 on every
repo, always — so nobody read it. Those categories now record a non-gating `EXPECTED`.
What protects them is the **locator contract**.

```bash
# Check whether the installed session-tracking files are in sync with the overlay:
./overlays/install-overlay.py session-tracking --target /path/to/repo --verify

# With project-level shim/skill:
./overlays/install-overlay.py session-tracking --target /path/to/repo \
    --install-level project --verify
```

**Per-file labels:**

| Label | Meaning |
|-------|---------|
| `SAME` | Installed file matches overlay source (EOL-normalized) |
| `DIFF` | Overlay-owned file differs from source — **drift, gates** |
| `EXPECTED` | User-managed file differs — by design, **does not gate** |
| `CUSTOMIZED` | Sanctioned `overlay-keep` region edit — **does not gate** |
| `BROKEN` | A **write** role's locator does not resolve — the handoff will fail. **Gates** |
| `ABSENT` | A **read-only** role's block is missing — resume prints its fallback. Advisory |
| `MISSING` | Dest file absent, or merge-section marker not in dest file — **gates** |
| `SRC-MISSING` | Overlay source file not found (overlay may be corrupt) — **gates** |

**Exit codes:** `0` = nothing gating; `1` = any DIFF / BROKEN / MISSING / SRC-MISSING.

### The locator contract (`verify_locators:`)

A manifest may declare a register. `--verify` then loads it and asserts every role's
locator still resolves against its target file. Gating follows `used_by`, because the
consequence does:

- **write role, unresolvable → `BROKEN`.** The handoff *will* fail to locate its region.
- **read-only role, unresolvable → `ABSENT`.** `resume` prints its fallback. Advisory.

Checklist locators need a `task_id` from a payload, so they are checked for file
existence only.

This is the question byte-comparison cannot ask. A user-managed file may differ from its
template in every byte and still be correct — or be byte-identical and *broken*, because
a `ref:KEY` was renamed. On its first run this check found that the overlay's own starter
templates did not satisfy the register shipping beside them: a fresh install's first
handoff would have failed on four roles.

**EOL caveat:** SAME uses EOL-normalized comparison (CRLF = LF, trailing-newline
differences = SAME). This intentionally decouples verify from the installer's
byte-exact `sha256` skip — a file can be verify-SAME yet the installer would still
re-copy it (open task T-29 for proper EOL handling).

**Typical use:** run after propagating an overlay update to confirm every target repo
received the new files, and that its register still describes reality. Catches two classes
of bug: a commit claiming a file was updated when the installer never ran, and a register
that declares ownership of a region which does not exist.

## Testing the overlays

Overlay code ships with its own test suites. They are **hermetic** — each builds its
own fixtures (or monkeypatches `$HOME`) and never reads the host repo's content, so a
change anywhere in this repo can never change a test result. Run them via `make`:

```bash
make -C overlays test                    # all suites, with a PASS/FAIL summary (196 tests)
make -C overlays test-ref-indexing       # ref-lookup.sh hermetic tests   (bash,   9)
make -C overlays test-session-tracking   # handoff pipeline tests         (pytest, 174)
make -C overlays test-installer          # installer --verify tests       (pytest, 13)

# Pass pytest args to a single suite:
make -C overlays test-session-tracking ARGS='-k harvest'
```

`make` with no target prints the list. Each target delegates to a runner in
`overlays/scripts/` (which resolves the right working directory and interpreter per
suite), so the suites are equally runnable from a shell or CI:

```bash
./overlays/scripts/run-all-tests.sh      # same as `make test`; nonzero exit on any failure
./overlays/scripts/test-installer.sh -k eol
```

**Adding a suite for a new overlay:** drop a `scripts/test-<name>.sh` runner, add a
`test-<name>` target to the `Makefile`, and list it in `scripts/run-all-tests.sh`.

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
| `verdict-hooks` | PostToolUse/Stop/SubagentStop hooks (user-level, not repo-level — different installer target) |
