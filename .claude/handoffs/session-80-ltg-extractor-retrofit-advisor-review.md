# LTG Extractor Retrofit — Session Review & Next-Session Handoff

**Branch:** `feature/ltg-extractor-retrofit`
**Reviewed:** end of session.80-ltg-extractor-retrofit-impl-2
**Test state:** 147 passing. **Parity check:** passed for the production path (extract_topics → embed).

---

## 1. What was completed and is durable

| Task | Commit | Verification |
|------|--------|--------------|
| 5 — `sweep_extractors.py` (benchmark sweeper) | `8fdfe0a` | Unit tests only (13). **Never run live against Ollama.** |
| 6 — `extract_topics.py` 2-arm production runner | `321d1a5` | Unit tests (11) + **live parity run confirmed**. |
| 7 — bash wrappers + `.claude/index.md` | `6ba7e25` | Wrappers created, chmod +x, registered. Not executed via wrapper. |
| 8 — parity check (no commit, by design) | — | **Passed**: prose→qwen3:14b, code→qwen2.5-coder:14b, 16 topics, 0 failures, dim=4096. |

Tasks 1–4 were completed in the prior session. Test count progressed 123 → 136 (Task 5) → 147 (Task 6).

The production pipeline contract (§1 of the plan) is **empirically verified**: `route(path)` → role → `config[role]["model"]` → written to `row["model"]` by the runner → matched by `embed.py`'s `winning_extractor(filepath, cfg)`. Three code paths agree on the same model string for both a prose and a code file.

---

## 2. Findings & caveats (ordered by importance)

### A. `sweep_extractors.py` has never been run live — verification gap (HIGH)
The parity check exercised `extract_topics.py` + `embed.py` only. The sweep's `run_single`/`run_sweep` were validated **only with mocked `client.call`**. The refactor is mechanically parallel to the (verified) production runner, and the payload shape is equivalent to the old `call_ollama` (same `format`, same top-level `think`, same `/api/chat` URL), so risk is low — but it is untested code now sitting on the branch. Mocks cannot catch: a model in `DEFAULT_MODELS` not being pulled, or `gemma3:12b` handling `format=` differently.
**This is the single biggest open item.** It is a dev/benchmark tool, not the production path, so it is a "should-verify," not a correctness blocker.

### B. Stale `bge-m3` references in `embed.py` — operationally misleading (HIGH)
`config.yaml` now resolves the `embedding` role to **`qwen3-embedding:8b` (embed_dim 4096)**, but `embed.py` still says otherwise:
- Docstring (`embed.py:3–7`): "embeds topic descriptions … via bge-m3" — **stale**.
- Sequential-constraint comment (`embed.py:13–17`): claims "bge-m3 (~700MB VRAM) + qwen3:14b (~9GB VRAM) co-fit." An 8B embedding model is **far larger than 700MB** (~5GB class). The co-residence premise is likely **no longer true** (8B-embed + 14B-extractor would exceed the 12GB ceiling). The parity check only survived because embed runs *after* extraction (sequential policy), so only the embedding model was resident.
**Action:** update both comments; re-check / re-run `run-vram-probe.sh` with `qwen3-embedding:8b` substituted for `bge-m3`. The `[ref:ltg-vram-probe]` conclusions in `CLAUDE.md` may also need revisiting.

### C. Benchmark vs production `num_ctx` mismatch (MEDIUM)
`sweep_extractors.py:57–60` keeps `OLLAMA_OPTIONS = {num_ctx: 16384, temperature: 0.1}`, but production `config.yaml` extractors use `num_ctx: 32768`. The sweep therefore evaluates candidate models under **half the production context window**. If sweep results are used to choose/qualify models, they won't reflect production behavior. This was inherited unchanged from the original spike (so it's pre-existing, not introduced here), but it's now a latent inconsistency worth a deliberate decision: align to 32768, or document why the benchmark intentionally differs.

### D. Winning-row agreement depends on Ollama echoing the exact config model tag (MEDIUM — document as invariant)
`embed.select_winning_row` matches `row["model"] == cfg[route]["model"]`. `row["model"]` is `ChatResult.model`, sourced from `resp.json().get("model", model_config["model"])` — i.e., whatever **Ollama echoes back**. It currently matches the config tags exactly for `qwen3:14b` and `qwen2.5-coder:14b` (confirmed). If a future model's Ollama-echoed tag ever differs from its `config.yaml` tag (e.g., a `:latest` vs pinned-digest discrepancy), the winning-row match **fails silently** (row dropped with "no winning row"). Document this invariant near `winning_extractor` and/or add a guard test.

### E. `sweep` couples to `config.yaml` it doesn't use (LOW — design smell)
`run_sweep` does `client = ModelClient(load_config(CONFIG_PATH))`, but the sweep drives everything through `client.call(prompt, model_config, …)` with `model_config` from `_build_benchmark_config`. The resolved config is never read. The sweep only needs the `.call()` method; it could be `ModelClient({})`. Current form means the sweep crashes at startup if `config.yaml` is missing/invalid, for no functional reason. Harmless but worth simplifying if touched.

### F. `route_file` is a thin pass-through (LOW)
`extract_topics.route_file(path)` just returns `route(path)`. It exists as a local test seam (GROUP 2 tests patch `extract_topics.route`). Harmless; leave unless simplifying.

### G. Housekeeping (LOW)
- **Orphan tasks:** the task list carries completed duplicates `#9–#12` (created at session start before discovering `#1–#8` already existed). Cosmetic clutter; clean up.
- **`session-log.md`** was modified at session start and not updated; run the `session-handoff` skill to record this session.
- **`expense-reporter/`** remained untracked throughout — not part of this work, leave as-is.

---

## 3. Concrete steps for the next session

**Before merging the branch:**
1. **Live-run the sweep once** to close gap (A):
   `python3 retrieval/sweep_extractors.py --model qwen3:14b --file docs/research/smart-rag-repowise.md`
   (single model × single file keeps it fast). Confirm: a `runs/<tag>.jsonl` + `-summary.txt` + `-manual-rubric.md` are written, `status=ok`, rubric token counts populated (non-zero `prompt_tokens`/`output_tokens`). `warm_model` first.
2. **Fix stale comments** (B): update `embed.py` docstring (`:3–7`) and the VRAM comment (`:13–17`) to reference `qwen3-embedding:8b` and the corrected co-residence reality. Re-run `run-vram-probe.sh` if you want the co-fit claim to be authoritative.
3. **Decide `num_ctx` for the sweep** (C): either bump `sweep_extractors.py` `OLLAMA_OPTIONS["num_ctx"]` to 32768 to match production, or add a one-line comment stating the benchmark deliberately uses 16384.

**Optional hardening:**
4. Add a regression test pinning the real `config.yaml`: `load_config(CONFIG_PATH)["embedding"]["embed_dim"] == 4096` and that `extraction_prose`/`extraction_code` resolve to the expected tags. This guards the winning-row invariant (D) and the embed-dim contract.
5. Document invariant (D) in a comment by `winning_extractor` in `embed.py`.

**Housekeeping:**
6. Run the `session-handoff` skill (updates `session-log.md`, resume state).
7. Delete orphan tasks `#9–#12`.
8. No PR has been created yet. If a PR is wanted, create it from `feature/ltg-extractor-retrofit` → `master` summarizing Tasks 1–8. **Confirm with the user before pushing/creating the PR** — pushing is a shared-state action and was not authorized in this session.

---

## 4. Invariants future work must preserve (do not regress)

- `_chat` uses **module-level `httpx.post`**, not `httpx.Client` — tests mock `patch("httpx.post", …)`.
- `think` is a **top-level** payload key, injected only when present in the model config (`qwen2.5-coder` has none).
- `load_config` requires the **two-level shape** (`models:` + `roles:`); no flat fallback.
- `config.yaml` is the **single source of truth** for production model names — `embed.py` derives them via `cfg[route(path)]["model"]`; do not reintroduce hardcoded `CODE_EXTRACTOR`/`PROSE_EXTRACTOR` constants.
- Production runner writes **one JSONL row per file** with contract fields `run_id, timestamp, model, file, file_role, status, parsed_topics`; `model` is the model-name string, never the role name.
- The sweep's record/rubric output schema is unchanged from the original spike — downstream summary/manual-rubric tooling depends on it.

---

## 5. Verdict

The retrofit is **functionally complete, tests green, and the production path is live-verified.** No correctness bug was found in the committed code. The branch is close to mergeable. The only substantive open risk is that **`sweep_extractors.py` is untested live** (step 1); the rest are doc-accuracy and housekeeping items (steps 2–8). Address step 1 and the stale-comment fix (step 2) before merge; the embedding-model VRAM premise (B) is the most likely thing to bite someone operationally if left undocumented.
