# Overlay: ref-indexing (v1)

Installs the ref block documentation system into any repository.

## What it provides

- **`[ref:KEY]` convention** — tag rules in CLAUDE.md to point at detailed blocks in `*.md` files
- **`ref-lookup.sh`** — CLI tool to print any ref block by key; also lists all known keys
- **`check-ref-integrity.sh`** — detects broken `[ref:KEY]` tags and malformed blocks; can run as a pre-commit hook
- **Starter `index.md`** — `.claude/index.md` template with the two-tier indexing convention pre-filled
- **CLAUDE.md section** — ref-indexing rules injected into the target repo's Claude Code instructions

## Install

```bash
python3 overlays/install-overlay.py ref-indexing --target /path/to/repo
```

Options:
- `--dry-run` — show what would be done without doing it
- `--mode ai` — use AI backend for CLAUDE.md merge (Ollama → claude -p fallback)
- `--mode manual` — print TODO list instead of merging (default)

## What gets installed

| Action | File | Condition |
|--------|------|-----------|
| COPY | `.claude/tools/ref-lookup.sh` | Always (backup if exists and differs) |
| COPY | `.claude/tools/check-ref-integrity.py` | Always |
| COPY | `.claude/tools/check-ref-integrity.sh` | Always |
| CREATE | `.claude/index.md` | Only if missing |
| APPEND | `.gitignore` | `.claude/local/` line if missing |
| MERGE | `CLAUDE.md` | Injects ref-indexing section with overlay markers |
| TODO | `.githooks/pre-commit` | Manual merge required if file exists |

## After install

1. Run `ref-lookup.sh` with no args to verify it finds ref blocks in the repo
2. Run `check-ref-integrity.sh` to see baseline integrity status
3. If `.githooks/pre-commit` already exists, manually add the integrity check call
4. Enable the pre-commit hook: `git config core.hooksPath .githooks`
