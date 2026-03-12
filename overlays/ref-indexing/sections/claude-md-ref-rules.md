## Reference Indexing Convention

Rules in this file may include `[ref:KEY]` tags pointing to detailed reference material
stored as `<!-- ref:KEY -->` blocks in `*.md` files.

**To look up a ref:** `.claude/tools/ref-lookup.sh KEY` — prints that section.
Run with no args to list all known keys.
**To check integrity:** `.claude/tools/check-ref-integrity.py` — finds broken `[ref:KEY]`
tags and malformed blocks across the repo.

### Two-Tier Notation

| Tier | Notation | When to Use | How to Resolve |
|------|----------|-------------|----------------|
| **Active reference** | `[ref:KEY]` | Agent needs this content during work | `ref-lookup.sh KEY` |
| **Navigation pointer** | `§ "Heading"` | Background reading, archive, rationale | Open the file, find the heading |

Use `ref:KEY` for content agents need at runtime. Use `§ "Heading"` for background or
archive navigation. Do not use `ref:KEY` for content that is only occasionally needed.

### Hard Requirements When Modifying Files

1. **New ref blocks** — wrap with `<!-- ref:KEY -->` / `<!-- /ref:KEY -->`; one concept
   per block; never wrap an entire file in one block
2. **New `[ref:KEY]` tag in CLAUDE.md** — add a corresponding block somewhere in `*.md`
3. **New scripts/tools** — add to `.claude/index.md` under the scripts/tools table
4. **New files of any kind** — add to `.claude/index.md` under the appropriate table

The full indexing convention (examples, block format, § pointer usage) is documented in
`.claude/index.md` under the "Indexing Conventions" section.
