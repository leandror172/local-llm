# APPLY instructions for ref-indexing overlay

This file is read by the AI merge backend when the installer needs to merge
overlay content into existing files. It explains intent and constraints.

---

## Merging `sections/claude-md-ref-rules.md` into `CLAUDE.md`

**Goal:** Insert the ref-indexing convention section into the target repo's CLAUDE.md,
wrapped in overlay markers, without disrupting existing content.

**Placement rule:** Near the top of the file — ideally after any top-level heading and
before project-specific rules. If a "## Documentation" or "## Reference" section already
exists, place it immediately before or merge into it.

**Marker format to use:**
```
<!-- overlay:ref-indexing v1 -->
[content of sections/claude-md-ref-rules.md here]
<!-- /overlay:ref-indexing -->
```

**Retrofit rule:** If the target CLAUDE.md already contains `[ref:KEY]` usage or
`ref-lookup.sh` mentions without overlay markers, that content was manually installed.
Two cases:
- If the existing content is a *simpler or partial version* of the section (e.g., a
  "Reference Lookup Convention" with just the lookup command and no two-tier table or
  hard requirements), **remove it** and insert the full overlay section in its place.
- If the existing content is substantially the same as the overlay section, wrap it
  with the overlay markers instead of duplicating it.
Report what you removed or wrapped so the human can verify.

**Do not:**
- Remove or reorder any existing CLAUDE.md content
- Modify content outside the overlay markers
- Add the section twice
