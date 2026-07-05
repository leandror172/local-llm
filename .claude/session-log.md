# Session Log

**Current Layer:** "Layer 5 — Expense Classifier"
**Current Session:** 2026-07-04 — Session 107: "T-33 LTG repo split EXECUTED — engine → latent-topic-graph repo, llm instance at ltg/ (S-D1–S-D7 frozen, SP-10/SP-11 acceptance PASS, PR #69)"

---
## 2026-07-04 - Session 107: "T-33 LTG repo split EXECUTED — engine → latent-topic-graph repo, llm instance at ltg/ (S-D1–S-D7 frozen, SP-10/SP-11 acceptance PASS, PR #69)"

### Context

Planned as the T-33 freeze session (per session-106 Next); the user opted to execute the split in the same session after the freeze. Master was current with PRs #67/#68 merged.

### What Was Done

- docs(ltg): T-33 split plan — S-D1–S-D7 FROZEN + SP-1–SP-14 execution plan (`docs/plans/ltg-repo-split.md`, `ref:ltg-split-frozen-decisions`)
- NEW REPO `latent-topic-graph` (`/mnt/i/workspaces/latent-topic-graph`, github.com/leandror172/latent-topic-graph private): filter-repo history extraction (108 commits, engine + LTG doc lineage), `src/ltg` package (hatchling, v0.6.0, 11 `ltg-*` entry points, shims exec them), SP-4 path-assumption kill (7 REPO_ROOT + 8 next-to-module default sites → CWD-relative instance files; tests get seeded instance-dir conftest), bootstrap (CLAUDE.md, README, overlays v4/v8 installer-verified, migrated tasks ids-kept, self-index corpus.yaml, agents + git-add guard copied), 377 tests green
- feat(ltg): SP-6 — llm LTG instance dir `ltg/` (corpus/config/index/wrappers; engine as editable uv path-dependency); `--repo-root` added to ltg-extract/ltg-embed (corpus root ≠ instance dir)
- docs(ltg): SP-7/8/9 — engine docs deleted (−3,294 lines) + pointers rewritten (index.md, session-context reading guide, root memories, tasks.md); ref sweep ran BEFORE deletion; 12 engine tasks migrated (T-34/T-35/T-38–41/T-63/T-64/T-72–75)
- SP-10 regression acceptance PASS: llm rebuild via sibling engine — 875 topics exact, all 49 anchor removals traced to moved files (diffed vs .bak, zero unexplained), relate() spot-check matches Phase 5 band; llm index now 976 nodes / 3067 edges
- SP-11 self-index acceptance PASS: new repo indexed itself (46 files → 456 nodes / 1145 edges, 74 cross-repo anchors, relate() incl. packaged-prompt summary); found+fixed 2 masked `relative_to()` decoupling bugs
- SP-14 prehistory-mining plan authored haiku-executable (new repo `docs/plans/prehistory-mining.md`: 3 full script listings, verified schemas, curation rubric) + split postmortem (`docs/plans/ltg-repo-split-postmortem.md`)
- Claude Code project memories seeded for the new repo (25 files + tailored MEMORY.md at `~/.claude/projects/-mnt-i-workspaces-latent-topic-graph/memory/`); PR #69 opened (llm split branch); docs(ltg): post-acceptance memory updates

### Decisions Made

- S-D1 (a) uv path-dependency, escalate to installed package on second machine / first external adopter; S-D2 (c) new top-level `ltg/` instance dir; S-D3 category table + filter-repo non-destructive extraction (split plan/discovery/registry doc + concept/smart-rag lineage STAY in llm, dual-cited); S-D4 overlays day one + self-index build-once AS the decoupling acceptance (name still open — `latent-topic-graph` declared temporary); S-D5 (a) Phase 6 MCP server in the new repo; S-D6 packaging flip during the split; S-D7 single-repo sessions, cross-repo = bounded tail-steps, engine tasks migrate, done-task history via prehistory.md
- Acceptance is delta-shaped, not equality-shaped: the llm index legitimately shrinks by exactly the moved ref-key set
- `config.yaml` is instance-owned (graph thresholds are corpus-probed); engine ships `config.example.yaml`
- Engine import package named `ltg` regardless of eventual repo name

### Next

- New-repo session: SP-14 prehistory mining — follow `docs/plans/prehistory-mining.md` (L-05; Steps A–D/F mechanical, Step E curation); then Phase 6 MCP server (L-01)
- Merge PR #69 (this split branch); user still to run the settings copy: `cp /mnt/i/workspaces/llm/.claude/settings.json /mnt/i/workspaces/llm/.claude/settings.local.json /mnt/i/workspaces/latent-topic-graph/.claude/` (classifier-gated, needs user hands); commit settings.json there afterwards
- New repo rename decision pending (S-D4 blank) — renaming also moves `~/.claude/projects/-mnt-i-workspaces-latent-topic-graph/`

### Gotchas

- Unit tests caught ZERO decoupling bugs; the second corpus caught 2 in minutes (`relative_to()` on mixed rel/abs paths, masked while code+corpus cohabited) — the SP-11 acceptance design was load-bearing
- ~40 engine tests silently depended on llm instance files next to the engine; fixed structurally with a seeded instance-dir conftest that now enforces the CWD invariant
- Green suite ≠ current suite: shim conversion after the test run broke 3 structural tests unnoticed for one commit
- `rm runs/2026*.jsonl` swept 4 TRACKED sweep artifacts (restored via git); globs over runs/ must exclude tracked files
- Copying `settings.json`/`settings.local.json` cross-repo is blocked by the auto-mode classifier even with in-conversation approval — `! cp` user-run is the designed path
- Full record: new repo `docs/plans/ltg-repo-split-postmortem.md` (6 lessons, plan-vs-actual per SP step)
