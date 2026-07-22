# llm/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents and chatbot. Keep under 30 lines.*

## Status

Layers 0-4 complete (of 10-layer plan). Infrastructure fully operational.
Layer 5+ active: expense classifier, chatbot Phases 1+2 (cross-repo context + LLM routing).
Session 59 (2026-05-04): LTG Phase 1 **fully closed**. All 3 freeze gates cleared.
**ref:ltg-extractor frozen**: qwen3:14b prose, qwen2.5-coder:14b code. ✅ Confirmed — session 74 benchmark closed M-P0a with NO SWAP.
Session 76 (2026-05-30): **14B num_ctx re-probe complete.** All models upgraded 16K→32K with q8_0 KV (dsc16→24K). 11 personas rebuilt. `scripts/run-ctx-probe.sh` added. LTG repo-separation gate note placed at Phase 6. Pre-session reading guide added to resume.sh.
Session 72 (2026-05-28): **LTG Phase 2 complete.** 69 topics, 8 files, 7/8 acceptance pass.
Session 73 (2026-05-28): **M-P0b complete.** Embedding upgraded bge-m3 (1024-dim) → **qwen3-embedding:8b (4096-dim)**. WARN verdict (load-time eviction only). `embed.py`/`store.py` config-driven.
Session 74 (2026-05-29): **M-P0a closed — NO SWAP.** `qwen3.6-coder:14b` phantom tag. Benchmarked DeepCoder-14B: 5/6 timeout at 500s, no think-suppression, intrinsic R1-distill overhead. `qwen2.5-coder:14b` remains primary coder. Side finding: `my-mcp-q25c14` uses wrong FastMCP API (P1 fix pending). Report: `ref:deepcoder-benchmark-decision`. **Next: fix mcp-q25c14 persona OR LTG Phase 3.**
Sessions 63-65 (2026-05-22): MCP Plans 1+2+3 complete — `refs`/`refs_root`, `output_file`/`output_only`,
`patch_file` tool. 29 green tests total. PRs #37 (Plans 1+2) and #38 (Plan 3) open, pending merge.
Session 68 (2026-05-26): Model survey complete. Key findings:
- **qwen3.6-coder:14b** — M-P0a closed NO SWAP (session 74); phantom tag on Ollama; `qwen2.5-coder:14b` confirmed primary coder
- **qwen3-embedding:8b** — ✅ adopted (session 73, M-P0b complete). Replaced bge-m3; MTEB 63.0→70.58; 1024→4096 dim.
- **llama4:scout** — new long-context capability (~200K–1M effective for RAG, advertised 10M); multimodal, fits 12GB (~10GB Q4)
- qwen3:14b still SOTA reasoning ≤14B; qwen3:4b-q8_0 still best classifier
- Full survey + advisor review: `docs/findings/model-updates-2026-05.md`
Sessions 75-82 (2026-05-29→06-02): infra (Ollama store→I:\, `q8_0` KV cache, tiny models pulled); **all 14B → 32K ctx**; **LTG extractor retrofit complete** (routing.py/schemas.py/ModelClient, 148 tests); **LTG Phase 3 anchor decisions FROZEN** (dual-path + alias-link; next = `anchors.py` TDD).
Session 83 (2026-06-04): **Session-handoff pipeline** side-track — Scope A design frozen (register-driven deterministic, no local model); `registry.yaml` + `(T-NN)` task IDs done.
Session 84 (2026-06-04): handoff pipeline **B2 safety core** — F1/F3/F4, 31 tests.
Session 85 (2026-06-05): handoff pipeline **B3 milestone complete** — F5 Mechanics / F6 Orchestrator+git adapter / per-run logging in `overlays/session-tracking/files/handoff/`, 53 tests green. Scope A spine functionally complete; next = B4 (F7 schema + SKILL rewrite).
Sessions 86–87 (2026-06-05/06): handoff pipeline **B4 complete — Scope A fully done, dog-food-validated.** F7 payload schema + `handoff.py`/`registry_io.py` entrypoint + `run-handoff.sh`; manifest install layout (register via `manual_if_exists` = Option C, propagate-with-flag); `SKILL.md` rewritten (decide content → one payload → one `run-handoff.sh` call). Clone dog-food found+fixed a real append/replace **newline-glue bug** F4 was blind to (`_normalize_block` at the `_collect_edits` seam); **77 tests green.**
Session 86 (2026-06-09): **flexible task ID checkoff** — checkbox-first locator (enumerates `- [ ]` lines, filters by word-boundary ID within first 40 chars); ID validation broadened `^T-\d+$` → `^[A-Za-z\d][A-Za-z\d.\-]*$`. Validated against tasks.md formats across 3 repos. **88 tests green.** Overlay bumped to v3. Synced to expenses, career-search, web-research. Distribution options analysis (9 options A–I) at `ref:overlay-distribution-options`.
Session 111 (2026-07-09): **session-tracking v11 — code ships as a package, config ships as an overlay.**
`overlays/session-tracking` is now a Python package (`src/sessiontracking/{register,handoff,resume}`,
entry points `st-handoff` / `st-resume`, `uv tool install --editable`). `register/` = `registry_io` +
`locator`, a primitive both products import; neither imports the other. `resume.sh` is a thin shim and
its sections are a step list in `.claude/resume.yaml`; `region:` steps name a **register role**, so read
and write share one `locate()`. `--verify` was permanently red since T-58 and now asks a different
question per ownership, plus a **locator contract** that found the starter templates never satisfied
their own register. Installed + committed in all five repos; `--verify` exit 0 everywhere.
Plan: `docs/plans/resume-config-steps.md`. Report: `docs/reports/session-111-report.md`.
*(Resolved 2026-07-11: PR #71 merged; post-handoff `resume.sh` + `--verify` acceptance passed — 7/7 checks, exit 0, 10/10 locators.)*
Session 112 (2026-07-11): **Coding-delegate grand vision authored** (name pending, V-D1): ollama-bridge
`generate_code`/`ask_ollama` → **async deliverable-run system** — submit → `run_id` → detached worker
loops coder model against the Layer-4 evaluator → Claude gates each deliverable (H1); autonomy = H2
behind the V-D2 "graduation" gate. Vision FOLDER `docs/vision/coding-delegate/` with its own `index.md`
(root index slimmed to a pointer — index split starts) + `.memories/QUICK.md`; 27 `ref:delegate-*` keys;
stances S1–S21, open V-D1–13; phases P1–P6 (**next: P1 plan** — async substrate; first client T-81).
Evidence: 2-agent prior-art comparison + clones survey (`docs/research/coding-subagent-*`), verdict
mining (10.7% coverage; ~1/3 of "improved" = compile-class). web-research field report shipped cross-repo.
Session 98 (2026-06-30): **`my-go-qcoder` HTTP 500 = host-RAM ENOMEM, NOT VRAM.** 30B partial-offload reads ~10–15 GiB of weights into RAM > old WSL2 15.5 GiB. **Fix = WSL `.wslconfig` memory=24GB (load-bearing).** T-67 ext4 store move EXECUTED (`/mnt/ollama-store/models`, ext4 vhdx on I:) but did NOT free RAM — Ollama keeps mmap off for partially-offloaded models on any fs; payoff was cold load 33s→15.6s + clean store. Health: `make -C ~/workspaces ollama-store-check`. See KNOWLEDGE.md "Host-RAM budget". **T-68 DONE (session, 2026-07-01):** reboot-persistence self-heals (udev `SYSTEMD_WANTS` recover service + attach-only logon task — device matched by UUID, survived a real reboot cold PASS incl. sde→sdd letter change); old 162 GB on I: reclaimed (394 GB free).

Session 125 (2026-07-21): **Verdict harness repaired (T-105). Coverage 9.6% → 18.7% (106/566).** *(One measurement, three published numbers — reconcile before citing: **9.6%** = 54/562 at investigation start · **10.2%** = 58/566 in the archived pre-backfill snapshot · **18.7%** = 106/566 post-repair. **48** prose verdicts were recovered; the findings doc's "49 recoverable" counts one whose subagent transcript had already been collected.)* Every durable doc taught an inline phrase (`2 — ~300 est. …`) while the capture regex accepted only a `[VERDICT …]` block **taught nowhere durable**; the harness worked, it was never fed (live probe captured cleanly). **Judgeable set NARROWED — supersedes "0/1/2 on every local model output" above:** `generate_code` + `ask_ollama` per-call; **oficina per-RUN** via `run_result` (it bypasses the MCP tools via the `GenerateFn` seam); NOT summarize/translate/classify_text. **`call_id` replaces `prompt_hash` as verdict identity** — `prompt_hash` is a content address and collided (1 hash = 24 calls / 8 models), so a sweep could record exactly one verdict. The hook now injects **only on a confirmed response-content match, with no positional fallback** — a stale id mislabels, which is worse than a miss. **81.4% of calls carry no judgment at all**: format was the minority of the gap; gate deferred pending measurement. Findings `docs/findings/verdict-coverage-collapse-2026-07-21.md`, plan `docs/plans/verdict-capture-repair.md`.

## Repo Structure

```
llm/
  mcp-server/    # MCP bridge server (Python/FastMCP) — Claude Code ↔ Ollama
  personas/      # 59 model configs (51 active) across 14 base models
  evaluator/     # Two-phase evaluation framework (automated + LLM-as-judge)
  benchmarks/    # Multi-language code validation suite
  overlays/      # Portable scaffolding packages for cross-repo consistency
  modelfiles/    # Ollama Modelfile definitions
  ltg/           # LTG *instance* (corpus.yaml, config.yaml, index/, wrappers) — the ENGINE moved to sibling repo latent-topic-graph (T-33 split, session 107)
  docs/          # Research, patterns, portfolio, findings
```

## Key Rules

- **12GB VRAM budget** shapes every architecture decision (RTX 3060)
- **Bash wrappers over direct python3** — `./script.sh` form, whitelist-safe
- **ref-indexing convention** — `<!-- ref:KEY -->` blocks for runtime lookups; `ref-lookup.sh --paths` emits `KEY<TAB>relpath` map (`.claude/local/` excluded)
- **Local-first, frontier escalation** — try local models first, Claude for judgment
- **Verdict protocol** — 0/1/2 on every **judgeable** call: `generate_code`/`ask_ollama` per-call, oficina per-RUN via `run_result`. NOT summarize/translate/classify_text (narrowed T-105, session 125). Measured coverage **18.7%** (106/566), not 100%

## Deeper Memory -> KNOWLEDGE.md

- **VRAM Budget Constraints** — model tier limits, context window ceilings
- **Prompt Decomposition** — empirically validated 3-stage sweet spot
- **Cross-Repo Architecture** — 3 repos, one hardware platform, MCP integration layer
- **DPO Data Collection** — passive training data from verdict-labeled inference logs
- **Smart RAG Research** — content-linking retrieval cluster (7 sources, 5 philosophies); hub at `ref:smart-rag-research`. Converges chatbot Phase 3 + Layer 7 RAG into one substrate.
- **Latent Topic Graph (LTG)** — topic-level retrieval substrate; concept `ref:concept-latent-topic-graph` (concept + smart-rag lineage stay in this repo). **Engine split to sibling repo `latent-topic-graph` (T-33, session 107)** — Phases 0–5 complete there; **Phase 6 MCP server BUILT there and registered globally** (`mcp__ltg__retrieve_context`/`find_related`/`relate_files` → `latent-topic-graph/run-server.sh`). This repo keeps the instance at `ltg/` (**1,357 nodes / 190 files / 3,779 edges**, queried 2026-07-21). Split record: `docs/plans/ltg-repo-split.md` (`ref:ltg-split-frozen-decisions`). Engine plans/decisions/probes + their ref keys → sibling repo.
