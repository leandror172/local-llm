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
Wrap the existing content block with the markers (do not duplicate it). Report what
you wrapped so the human can verify.

**Do not:**
- Remove or reorder any existing CLAUDE.md content
- Modify content outside the overlay markers
- Add the section twice
