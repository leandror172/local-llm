# Session Log

**Current Layer:** LTG Phase 2 — embedding + storage (Phase 1 extractor fully frozen)
**Current Session:** 2026-05-16 — Session 60: Consolidate Ollama directives into ollama-scaffolding overlay
**Previous logs:** `.claude/archive/session-log-layer0.md`, `.claude/archive/session-log-2026-02-12-to-2026-02-20.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-23.md`, `.claude/archive/session-log-2026-02-23-to-2026-02-24.md`, `.claude/archive/session-log-2026-02-25-to-2026-02-25.md`, `.claude/archive/session-log-2026-02-26-to-2026-02-26.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-27.md`, `.claude/archive/session-log-2026-02-27-to-2026-02-28.md`, `.claude/archive/session-log-2026-03-07-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-09.md`, `.claude/archive/session-log-2026-03-09-to-2026-03-07.md`, `.claude/archive/session-log-2026-03-11-to-2026-03-11.md`, `.claude/archive/session-log-2026-03-13-to-2026-03-13.md`, `.claude/archive/session-log-2026-03-14-to-2026-03-14.md`, `.claude/archive/session-log-2026-03-15-to-2026-03-15.md`, `.claude/archive/session-log-2026-03-17-to-2026-03-17.md`, `.claude/archive/session-log-2026-03-20-to-2026-03-20.md`, `.claude/archive/session-log-2026-03-25-to-2026-03-25.md`, `.claude/archive/session-log-2026-03-26-to-2026-03-26.md`, `.claude/archive/session-log-2026-04-02-to-2026-04-02.md`, `.claude/archive/session-log-2026-04-03-to-2026-04-09.md`, `.claude/archive/session-log-2026-04-13-to-2026-04-13.md`, `.claude/archive/session-log-2026-04-14-to-2026-04-14.md`, `.claude/archive/session-log-2026-04-15-to-2026-04-15.md`, `.claude/archive/session-log-2026-04-16-to-2026-04-16.md`, `.claude/archive/session-log-2026-04-17-to-2026-04-17.md`, `.claude/archive/session-log-2026-04-25-to-2026-04-25.md`

---

## 2026-05-16 - Session 60: Consolidate Ollama directives into ollama-scaffolding overlay

### Context
Side-track from the LTG line. User observed that the expense and web-research repos carry Ollama-usage directives in their feedback memories that are absent from the `ollama-scaffolding` overlay master files. Goal: promote the selected directives into the overlay so every repo it installs into shares them. Work done on a new branch `feature/ollama-scaffolding-directives`.

### What Was Done
- **Six directives consolidated** into `ollama-scaffolding` from expense/web-research feedback memories: D1 prompt style (describe behavior, not implementation), D2 always-attempt (never skip on past `0` verdicts), D3 serialization (serial by default; 3+ parallel exceeds VRAM; different-model parallel worst), D4 retry budget (3-4 attempts before escalating), D5 caller inclusion in `context_files`, D6 few-shot-before-delete.
- **Mechanism conversion:** the retry-patterns reference doc moved from a `templates:` entry (created once, never propagates) to a `files:` entry (hash-based COPY/SKIP/overwrite — re-installs deliver updates).
- **Renamed** `local-model-retry-patterns` → `local-model-conventions` (ref key + file) to reflect the broader before/after-call scope; doc restructured into "Before you call" / "After you call". All references updated, including this repo's own `ref:` block in `session-context.md` and `CLAUDE.md`.
- **Two installer bugs fixed in `overlays/lib/actions.py`:** (1) `handle_files` forced `executable=True` — replaced with extension-based detection (`_is_executable_payload`) + explicit `_apply_mode`, because the `/mnt/i` drvfs mount reports every file as 777 so mode-preservation is unreliable; (2) `handle_merge_sections` round-tripped through `read_text`/`write_text`, silently normalizing a CRLF target to LF — added `_read_text_eol`/`_write_text_eol` to preserve line endings.
- **Propagated** to expense (`4ed7a89`) and web-research (`4bd07d5`, amended to restore CRLF after the bug was found+fixed). Both got the v1→v2 overlay marker update deterministically — no AI mode.
- **3 commits:** llm branch `feature/ollama-scaffolding-directives` — `3c0e2f4` (consolidation) + `548ca07` (line-ending fix); expense/web-research one each.

### Decisions Made
- **`files:` over markers for the overlay doc** — it is 100% overlay-owned with zero per-repo customization, so the template "user-managed" contract bought nothing; `files:` propagates on re-install with no version bump. A standalone marked-file mechanism was considered and deferred.
- **Renamed the ref key** — the doc outgrew "retry patterns" once pre-call directives were added; `local-model-conventions` covers calling + verdict + retry.
- **chmod by extension, not filesystem mode** — drvfs makes the executable bit meaningless; extension is the only reliable signal without a git dependency.
- **Amended the web-research commit** (user-approved) rather than a follow-up commit — it was unpushed and the EOL-normalization noise would otherwise complicate merges with in-progress work in that repo.

### Next
- Resume the LTG Phase 2 line — VRAM co-residence probe (qwen3:14b + bge-m3 ≈ 12 GB). This session did not touch LTG.
- New deferred items added to `ref:deferred-infra`: AI-merge-path CRLF preservation; ollama-scaffolding overlay review-for-improvements.
- Open PR for `feature/ollama-scaffolding-directives`.

### Notable
- **WSL drvfs gotcha:** Windows drives mounted in WSL (`/mnt/*`, 9p/drvfs) report every file as `-rwxrwxrwx` and ignore `chmod`. Any tool that copies files off such a mount and trusts `os.access` or mode-preservation will mis-set permissions. `git ls-files -s` still shows the correct mode (git stores it).
- The deterministic v1→v2 marker replace in `handle_merge_sections` is mode-independent — AI mode is only used for *first* insertion when no marker exists. "Don't use AI mode" was satisfied automatically for both target repos.

---

## 2026-05-04 - Session 59: Determinism re-run + MoE eval → Phase 1 extractor frozen

### Context
Resumed on `feature/ltg-phase1-reconciliation-session-58`. PR was already open. Two freeze gates remained: determinism re-run on `smart-rag-index.md` × qwen3:14b, and MoE extractor eval (qwen3:30b-a3b, qwen3-coder:30b). Both completed this session, closing all three gates and allowing the formal `ref:ltg-extractor` decision-replacement.

### What Was Done
- **Determinism re-run** (5 runs, `smart-rag-index.md` × `qwen3:14b`): All 5 runs scored 1–3/7 on the 7 cross-cutting-pattern bullets (original was 4/7). Branch C confirmed — off-by-one is a model property, not sampling luck. Three deterministic failure modes: B2 semantic conflation (absorbed into `wiki_precompilation` at line 12 every run), B6 −1 shift (claims 26 every run), B5 structural absorption (dropped in 4/5 runs). Jaccard median 0.600 — no stability bonus. Committed to `retrieval/runs/20260504-153903.jsonl` + filled `determinism-ground-truth.md` analysis template.
- **MoE eval (qwen3:30b-a3b)**: Unusable. TTFT > 9 minutes even for trivial prompts (direct probe: 150 tokens in 6.5s at 23 tok/s generation, but prefill latency ~9 min). Root cause: Ollama MoE hybrid RAM offload loads all attention layers during prefill at RAM bus speeds. Architecture limitation, not a config fix. `extract_topics.py` timeout bumped 240 → 600s for future probes.
- **MoE eval (qwen3-coder:30b)**: 8/8 files completed at 6.7–14.8 tok/s. Scored by Opus subagent (methodology-consistent with sessions 54-57). Prose avg: 2.36 pre-penalty / **2.06 adjusted** (fails ≥2.2 — speed penalty universal). Key failure: span-anchoring weakness on long/loose files (plan-v2.md: 5.7% coverage). Bright spots: persona-template.md 3.00, build-persona.py 2.80 (semantic clusters not enumeration). Does not displace qwen3:14b.
- **Formal `ref:ltg-extractor` freeze**: Replaced placeholder "how we will decide" entry in `retrieval/DECISIONS.md` with frozen `winner_model` entry — 2-arm routing (qwen3:14b prose, qwen2.5-coder:14b code), frozen params, deferred items list, gate evidence.
- **New ref blocks** added to `retrieval/spike-rater-notes.md`: `ref:ltg-phase1-determinism-smart-rag-index`, `ref:ltg-phase1-moe-eval`. Decision gate items 2 and 3 struck through in `ref:ltg-phase1-routing-hypothesis` in `retrieval/spike-results.md`.
- **2 commits** on `feature/ltg-phase1-reconciliation-session-58`: `9aca7c7` (determinism) + `84f3647` (MoE eval + extractor freeze).

### Decisions Made
- **Determinism Branch C applied**: containment/post-pass guard at retrieval time for `qwen3:14b` on dense single-line bullet lists — not a routing change. The deferred 3rd-arm hypothesis (qwen3:8b for cross-ref-index files) is unaffected.
- **qwen3:30b-a3b permanently deferred**: Ollama MoE offload makes it unusable on this hardware. Not a config problem — would require Ollama internals change or dedicated MoE inference path.
- **qwen3-coder:30b not adopted**: Fails adjusted threshold. Better than qwen2.5-coder:14b on code (2.80 vs 2.48) but not enough to justify 3× resource cost at MVP stage.
- **ref:ltg-extractor frozen**: qwen3:14b (prose), qwen2.5-coder:14b (code). Phase 1 is complete.

### Next
- **Phase 2 entry point: VRAM co-residence probe** — qwen3:14b + bge-m3 ≈ 12 GB on 12 GB card. Must confirm they can run simultaneously before embedding is locked. This is Phase 2's first concrete task.
- **Prompt-iteration experiment** (still deferred from sessions 55/57): topic-count floor `max(5, major_section_count)` + containment-only overlap rule. Cheap re-sweep on existing 8 files; tests whether qwen3:8b's whole-section-drop failure is prompt-fixable.
- **Still-open PRs**: session 57 PR (`feature/ltg-phase1-scoring-and-notes`); `feature/gemma3-benchmark`; `feature/ltg-phase1-reconciliation-session-58` (current, already open).
- **Phase 2 work**: LanceDB integration, bge-m3 embedding, graph construction (networkx + leidenalg), `relate(a,b)` acceptance test.

### Notable
- The original 4/7 determinism score was a *favorable* draw — the re-run landed 1–3/7, worse than the original. Single-run spike studies may overestimate model stability.
- qwen3-coder:30b's span-anchoring failure (keyword pointer vs section range) is qualitatively different from qwen3:8b's section-drop — content recognition is correct but the model can't extend a concept to the paragraphs that develop it.
- Pre-committed decision trees (determinism + two-rater reconciliation) paid off again — both branches applied mechanically without post-hoc negotiation.

---

## 2026-04-30 - Session 58: LTG Phase 1 two-rater reconciliation closes Phase 1 (Branch C)

### Context
Resumed mid-day on `feature/ltg-phase1-scoring-and-notes` (session 57's branch). User signaled "Manual viz is done; ltg-rater-...-215756Z.json also has individual scores for (almost) each topic" — i.e., the user-track HTML-viz scoring complete, with richer per-topic data than the original rater. This was the queued reconciliation step from session 57's "Next" pointer. User explicitly directed: commit on a new branch, then session-handoff, then PR.

### What Was Done
- **Reconciled user track (manual-rubric.md, 32/32 cells) with Claude draft.** Per-cell delta analysis: **identical 4-model ranking and identical pass/fail verdicts** under both raters. User track systematically more lenient (per-model Δ_avg: gemma +0.21, qwen3:14b +0.18, coder +0.40, qwen3:8b +0.36) but the relative ordering and gating decisions hold.
- **Applied Branch C** from `ref:ltg-phase1-pending-revisions` per the pre-registered decision tree. Cross-rater agreement: agree on `smart-rag3.md` (qwen3:14b wins, both raters); disagree on `smart-rag-index.md` (Claude: qwen3:8b > qwen3:14b by +0.12; User: qwen3:14b > qwen3:8b by +0.15). Mixed → Branch C: keep 2-arm production routing (qwen2.5-coder:14b for code, qwen3:14b for prose); cross-ref-index 3rd-arm hypothesis preserved as deferred Phase 2 item.
- **Final 8/8 adjusted scores (Claude / User):** qwen3:14b 2.44 / 2.61 ✅ winner; qwen3:8b 2.27 / 2.63 ✅ backup; qwen2.5-coder:14b 1.76 / 2.16 ❌ (borderline under user, 0.04 below threshold — corpus expansion could plausibly flip); gemma3:12b 1.61 / 1.82 ❌.
- **Edited `retrieval/spike-results.md`** (5 surgical edits): filled user scores table (32 cells, was placeholder); added Two-rater reconciliation section with decisive cells + Branch C resolution + largest single-cell disagreement note (QUICK.md × gemma3 Δ=−0.93) + dim-8 reweight question; softened pre-reconciliation routing claims in Claude draft block; added insight #9 to `ref:ltg-phase1-insights` (rubric fit-for-purpose for binary decisions; ~0.2–0.4 calibration drift for continuous reuse); rewrote `ref:ltg-phase1-routing-hypothesis` block per Branch C with explicit 2-arm production + 3 deferred Phase 2 items.
- **Updated `.memories/KNOWLEDGE.md`** "LTG Phase 1 Extractor Spike — Findings" section: replaced preliminary 5/8 table with final 8/8 reconciled (Claude + User columns), added production-routing summary + rater-calibration takeaway for Layer 7 / DPO scoring.
- **Updated `.claude/tasks.md`:** marked "score remaining 4 corpus files" complete; added 2 new deferred items in `ref:deferred-infra` — (a) cross-reference-index 3rd-arm routing hypothesis (defer-to-Phase-2 with re-eval triggers), (b) per-topic JSON (648 scores) as Phase 2 input.
- **Updated `.memories/QUICK.md` (root) + `retrieval/.memories/QUICK.md`:** refreshed status blocks from "session 56, 5/8 in progress, preliminary winner" to "session 58, reconciliation closed, 2-arm production, freeze pending determinism + MoE". Confirmed other per-folder QUICK.md / KNOWLEDGE.md files (evaluator, mcp-server, overlays, personas, benchmarks) do not reference Phase 1 content — left untouched.
- **Branch + commits:** Created `feature/ltg-phase1-reconciliation-session-58` off `feature/ltg-phase1-scoring-and-notes` (session 57's branch — not master, because the reconciliation depends on session 57's `ref:ltg-phase1-pending-revisions`). Two commits: `c3fdcdd` (reconciliation core: spike-results.md + KNOWLEDGE.md + tasks.md + tracked manual-rubric.md + tracked latest JSON export) and `34cfaa8` (chore: QUICK.md memory updates).

### Decisions Made
- **Branch C selected mechanically** per the pre-registered decision tree from session 57 (`ref:ltg-phase1-pending-revisions`). Rationale: agree on `smart-rag3` flip but disagree on `smart-rag-index` flip → Branch C (mixed). The pre-registration prevented post-hoc rationalization of which branch fits the data.
- **3rd-arm hypothesis preserved as deferred, not killed.** Re-eval triggers documented: (a) determinism re-run on smart-rag-index × qwen3:14b confirms/refutes off-by-one, (b) more cross-reference-index files added to corpus (n=1 → n≥3), (c) MoE candidates evaluated. Determinism re-run is cheapest (~30s) and answers the deferred question directly.
- **Dim-8 reweight question (insight #6) NOT load-bearing for ranking** — both rater tracks produce identical pass/fail; deferred to Phase 2 as a refinement that would matter only if the rubric is later repurposed for continuous DPO scoring.
- **Per-topic JSON (648 scores in 29/32 cells) deferred to Phase 2** — could supply per-topic boundary evidence to disambiguate the 3rd arm without corpus expansion. Out of scope for Phase 1 binary freeze.
- **Branch off current session 57 branch, not master** — reconciliation depends on the `ref:ltg-phase1-pending-revisions` block introduced in session 57; branching off master would create a base where the decision tree doesn't exist.
- **Tracked the user-track source files** (`retrieval/runs/manual-rubric.md` + `…215756Z.json`) alongside the doc edits because spike-results.md cites them. Other intermediate exports + manual-rubric backups left untracked.

### Next
- **Push `feature/ltg-phase1-reconciliation-session-58`** + open PR (final step of this session).
- **Determinism re-run on `smart-rag-index.md` × qwen3:14b** — now the cheapest gating evidence remaining (~30s of compute). If the off-by-one on the 7 pattern bullets reproduces under 2 more sweeps, that's the missing Phase 1 evidence for the deferred 3rd arm. Apply stability bonus (+0.5 if Jaccard ≥ 0.85, +0.25 if ≥ 0.80) to weighted_quality before the formal freeze decision.
- **Prompt-iteration experiment** (still deferred from sessions 55/57): topic-count floor `max(5, major_section_count)` + containment-only overlap rule. Cheap re-sweep on existing 8 files; would directly test whether qwen3:8b's whole-section-drop failure mode is fixable in-prompt.
- **Phase 2 VRAM co-residence probe** (qwen3:14b + bge-m3 ≈ 12 GB on 12 GB card) folded with **MoE extractor eval** (qwen3:30b-a3b, qwen3-coder:30b) per `ref:ltg-phase1-routing-hypothesis`.
- **Formal `ref:ltg-extractor` decision-replacement** in `retrieval/DECISIONS.md` once determinism + MoE evidence lands. Branch C does NOT pre-commit the freeze; only the routing hypothesis.
- **Still open:** session 57 PR for `feature/ltg-phase1-scoring-and-notes`; PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; Layer 4 stragglers; registry hot-reload; server.py refactor.

### Notable
- **Largest single-cell disagreement: `.memories/QUICK.md` × `gemma3:12b` (Δ=−0.93).** The only cell of 32 where the user track is harsher than Claude. User scored d5=0 with explicit note about semantic hallucination ("infers wrong ideas, strange decisions on spans"). Sharpens gemma's `❌` rather than weakening it — the failure mode is *semantic hallucination on dense memory files*, which Claude's per-file scalar underweighted.
- **Coder borderline:** under user track, qwen2.5-coder:14b finishes at 2.16 adjusted (0.04 below threshold) vs Claude 1.76 (0.44 below). Same verdict but margin is small enough that 2-3 more code files in the corpus could flip it.
- **Methodological insight for Layer 7:** rubric is fit-for-purpose for binary decisions; absolute scores diverge by ~0.2–0.4 weighted-quality points across raters. Continuous reuse (DPO scoring) would need inter-rater calibration.
- **Pre-registered decision tree paid off.** Session 57 wrote down what each user-track outcome would mean before seeing the user's scores. Branch C applied mechanically rather than getting argued into Branch A on weak grounds. Worth carrying forward to determinism + MoE eval (pre-register what each outcome means).

---

## 2026-04-25 - Session 57: Score remaining 3 corpus files + capture rater notes (Claude draft 8/8 complete)

### Context
Resumed mid-day on `feature/ltg-rater-redesign` (session 56 had landed the new rater template + viz_sweep wiring earlier today). User asked first about the in-flight viz refactor (since-resolved by session 56), then directed three sequential scoring sessions: KNOWLEDGE.md, smart-rag-index.md, smart-rag3.md. Closed at 8/8 + captured all unwritten insights to ref blocks before session ended.

### What Was Done
- **Scored `.memories/KNOWLEDGE.md` (file 6 of 8):** 214-line, 10-section repo knowledge doc. qwen3:14b 2.85 (joint-best in spike), qwen3:8b 2.25, coder 2.30, gemma3 1.60. Confirmed insight-#4 reproduction (qwen3:8b dropped Smart RAG section 117-151 entirely; gemma3 conflated Smart RAG + LTG into one mega-topic).
- **Scored `docs/research/smart-rag-index.md` (file 7 of 8):** 64-line cross-reference index with 7 dense numbered pattern bullets. **First file in spike where qwen3:8b (2.55) outscored qwen3:14b (2.43)** — qwen3:14b had off-by-one errors on 3 of 7 pattern bullets (graph_exploitation→[23] should be [24], etc.). coder 1.83 with rule-3 violation (`cross_cutting_patterns [21,29]` structural meta-topic) and "kitchen-sink line 35" pattern. gemma3 1.35 with coverage 0.344 (below rule-2 floor).
- **Scored `docs/ideas/smart-rag3.md` (file 8 of 8):** 84-line architectural design doc. qwen3:14b 2.85 (rebound, tied with KNOWLEDGE.md for joint-best). qwen3:8b drops back to 2.30 (kitchen-sink span [10,22], three topics claiming [76,81]). coder 1.55 — **worst single-file score in the entire spike** (three structural-meta topics, all rule-3 violations). gemma3 1.40 with self-overlapping spans + crossed-overlap on [63,64].
- **Final 8-file Claude draft averages (after speed penalty):** qwen3:14b 2.44 (winner), qwen3:8b 2.27 (backup, best on cross-ref index), coder 1.76 (fails), gemma3 1.61 (fails).
- **Added 3 new numbered insights to `ref:ltg-phase1-insights`:**
  - **#6** Section-drop pattern reproduces (qwen3:8b confirmed structural, not anecdotal — KNOWLEDGE.md + persona-template.md); rubric under-penalises (dim 8 only 10% — qwen3:8b cleared 2.2 threshold despite missing 22% of file content).
  - **#7** Cross-reference index breaks qwen3:14b's lead via off-by-one on dense bullets with inline punctuation density. Off-by-one is **model-agnostic format failure** — coder hit it on smart-rag-repowise.md, qwen3:14b hits it on smart-rag-index.md.
  - **#8** Paired-file natural experiment (smart-rag-index ↔ smart-rag3, same content opposite format) shows 0.55-point swing for qwen3:8b and 0.42-point swing for qwen3:14b in opposite directions — **cleanest evidence in spike that format-sensitivity dominates content-sensitivity**.
- **Created `retrieval/spike-rater-notes.md`** with three new ref blocks (held outside `.memories/KNOWLEDGE.md` deliberately to avoid biasing user-track HTML-viz scoring):
  - `ltg-phase1-claude-rater-notes` — per-cell scoring rationale + evidence quotes for all 3 files scored this session
  - `ltg-phase1-meta-insights` — file-class taxonomy (4 roles, n=1/n=2 caveats), paired-file methodology recommendation, per-model trend observations, reconciliation priorities, mechanical post-pass guards (coverage cap >60%, containment overlap check)
  - `ltg-phase1-pending-revisions` — stale-wording cleanup queue (3 items) + three conditional drafts (A/B/C) for routing-hypothesis revision based on user-track outcome, with decision tree
- **Updated `.claude/index.md`** Phase 1 Spike Results table: refreshed counts (4/8 → 8/8), refreshed numbered findings list (#1-#3 → #1-#8), added rows for the 3 new ref keys.
- **Branch + commit:** Created `feature/ltg-phase1-scoring-and-notes` off `feature/ltg-rater-redesign`. Single commit `2330e04` adds spike-results.md edits + spike-rater-notes.md + index.md updates.

### Decisions Made
- **Hold-until-reconciliation policy:** Per-cell rationale, meta-insights, and pending revisions all live in `retrieval/spike-rater-notes.md` rather than `.memories/KNOWLEDGE.md`. Codifying findings into knowledge-tier memory before user-track scores arrive would bias the user's independent rater calibration.
- **Pre-written conditional revisions (A/B/C):** Three drafts of the routing-hypothesis revision queued in `ref:ltg-phase1-pending-revisions`, conditional on whether user track agrees on insight #8 ranking flip (Branch A: 3-arm; Branch B: 2-arm; Branch C: mixed). Decision tree included so a future session can execute mechanically.
- **New branch instead of committing to `feature/ltg-rater-redesign`:** Scoring + insights are findings, not infrastructure. Splitting them into separate PRs lets reviewers engage with the patterns without re-litigating the tooling.
- **3-arm routing story is empirically backed but n=1 on cross-ref arm:** Insight #8 is the cleanest controlled experiment in the spike; routing-hypothesis revision Branch A captures it but with explicit "n=1, fragile" caveats and gating on determinism re-run.

### Next
- **Open PR for `feature/ltg-phase1-scoring-and-notes`** (queued — final step of this session).
- **User completes HTML-viz scoring track** (in progress; manual-rubric.md.1.md/.2.md/.3/.4 backups present in working tree).
- **Two-rater reconciliation:** Diff Claude draft vs user track per cell. Apply Branch A/B/C from `ref:ltg-phase1-pending-revisions` based on outcome. Then apply stale-wording cleanup (3 items) and update `.memories/KNOWLEDGE.md` "LTG Phase 1 Extractor Spike — Findings" section to final 8/8 numbers.
- **Determinism re-run on `smart-rag-index.md` for qwen3:14b** (cheap; ~30s of compute) — does the off-by-one on the 7 pattern bullets reproduce, or was the sweep sample-unlucky? This is gating evidence for the 3-arm routing arm.
- **Prompt-iteration experiment** (deferred from session 55): topic-count floor `max(5, major_section_count)` + containment-only overlap rule. Cheap re-sweep on existing 8 files; would directly test whether qwen3:8b's whole-section-drop failure mode is fixable.
- **Then:** MoE probe (qwen3:30b-a3b, qwen3-coder:30b) folded into Phase 2 VRAM co-residence work; formal `ref:ltg-extractor` decision-replacement in `retrieval/DECISIONS.md`; routing-hypothesis revision applied per chosen branch.
- **Still open:** PR for `feature/gemma3-benchmark`; Phase 3 chatbot convergence with LTG; Layer 4 stragglers; registry hot-reload; server.py refactor.

---

