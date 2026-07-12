## 2026-07-11 - Session 112: Coding-delegate grand vision — async deliverable runs for local models (PR #72)

### Context

Started by verifying the session-111 handoff's acceptance (PR #71 merged, master updated), then pivoted to the user's grand-vision proposal: evolving ollama-bridge's generate_code/ask_ollama into an async coding-subagent. Full-session architectural exploration — research, stress-testing, course-corrections — ending with the vision authored as a folder.

### What Was Done

- **v11 acceptance PASSED** — first post-handoff `resume.sh` on master: 7/7 reading-guide checks; `install-overlay --verify` exit 0, `10/10 register locators resolve`.
- **Coding-delegate grand vision authored** (`docs/vision/coding-delegate/`, PR #72): 8 docs + folder-local `index.md` + `.memories/QUICK.md`; 27 `ref:delegate-*` keys; stances S1–S21 (evidence-cited); open decisions V-D1–V-D13 (leans + named triggers); phases P1–P6. Root `.claude/index.md` slimmed to a pointer — the index split starts here.
- **Two-agent prior-art comparison run** (frontier web tools vs web-research MCP, same questions) → `docs/research/coding-subagent-prior-art{,-webresearch}.md`; **clones survey** via subagent → `docs/research/coding-subagent-clones-survey.md` (claude-code patterns-only; open-multi-agent MIT).
- **Verdict-data mining** (`ollama-stats.py`/`ollama-verdicts.py`): 10.7% verdict coverage; ~1/3 of "improved" verdicts compile-class, ~1/2 of rejections typo/runtime-class — the loop's first target; one cold-start timeout hand-recorded as verdict 0 (protocol slips → mechanize).
- **web-research field report shipped cross-repo** (`~/workspaces/web-research/docs/reports/2026-07-11-field-report-llm-prior-art-run.md`): defects D1–D5 + proposed fixes + triage order (D2 first — non-discriminating auditor verdict).
- **naming.md split out** with criteria C1–C7 (C4 = cross-language catchability, from user signal) and a 13-candidate register; shortlist oficina/aprendiz/apprentice/delegate.

### Decisions Made

- **H1 = one call, one deliverable; Claude gates every deliverable** (user course-correction) — a test run precedes its implementation run; autonomy (planner model, plan runs) is H2 behind the V-D2 "graduation" gate (planner/coder small-model split has the thinnest literature — treat as hypothesis).
- **Bespoke run_id + offset-delta polling** — measured: Claude Code's MCP client is blocking-only and ignores progress notifications (#31893); MCP Tasks primitive moves to an extension in the 2026-07-28 RC; MCP sampling deprecated. Adopt Tasks *state names* only.
- **Event-sourced JSONL ledger, no KurrentDB** — the pattern without the daemon; upgrade trigger named (multi-worker/multi-machine or subscription fan-out). Queue at application level; Ollama's queue is the collision absorber.
- **No orchestration framework for the spine** (S19); **own thin loop, adapters as experiment arms** (S18 — Aider embeds via subprocess only; mini-swe-agent is the vendorable reference).
- **Judge gates every DPO chosen label** (S17) — the cheap per-iteration test signal is the most gameable; `auto_verdict` ≠ `curated_verdict`.
- **Vision-folder KNOWLEDGE.md deferred** — `decisions.md`+`evidence.md` play the role; trigger: first phase built. QUICK.md created.
- **AutoCodeRover excluded** — Sonar source-available license forbids AI ingestion/interaction.

### Next

- **Merge PR #72** (docs-only: vision folder + research + index split).
- **Settle the name (V-D1)** — `naming.md` shortlist oficina/aprendiz/apprentice/delegate — BEFORE P1 ships CLI entry points.
- **T-84 — author the coding-delegate P1 plan** (async substrate; freezes V-D4/V-D9/V-D10/V-D11 + ledger event names; first client candidate T-81).
- Side options: T-83 (freeze B-D1–B-D8), T-56, classifier benchmark (M-P1b/P2 — now has a product consumer), persona hygiene (T-27/T-49). LTG Phase 6 in the sibling repo.

### Gotchas

- **Claude Code's MCP client has no async primitives at all** — every tool call blocks, progress notifications ignored (issue #31893 closed not-planned). Poll responses must carry the narrative; nothing can push.
- **web-research defects found under load:** `search_topic` fails to hard zero on narrow queries; its auditor verdict is internally inconsistent (reports "0 results" alongside 3–5 good pages — non-discriminating signal, same class as T-54/T-80a/T-82); `query_knowledge` is substring-based and misses verbatim-matching cached content; `research_url` has no bot-wall detection and no arXiv version resolution. Field report in their repo.
- **Small-model repair decays fast** — 76–95% of gains in rounds 1–2, exponential decay after (Phi-4 14B); HumanEval-scale numbers do NOT transfer to repo-scale (~21% at 8B on SWE-bench); 14B is the floor for a coder-in-loop.
- **rtk compacts commit/push output to one line** (`ok N files changed…`) — fine, but read counts carefully; the vision commit's "3 deletions" was correct only because the whole section was new since HEAD.
