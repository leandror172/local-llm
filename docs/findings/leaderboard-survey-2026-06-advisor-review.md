# Advisor Review — Model & Leaderboard Survey (session 78)

**Scope reviewed:** the findings (model deep-dives + leaderboard data), the research methodology section, and the saved artifacts (`model-updates-2026-05.md` additions, `leaderboard-survey-2026-06.md`, `tasks.md` entries, `index.md` pointer).

## Verdict

Two tiers of trust in this work, and they're not labeled as such in the saved files:

- **Hard data (trust):** the 4,576-model parquet table and everything derived from it; the methodology writeup; the license analysis; the Kimi-K2 cloud-only conclusion.
- **WebFetch-summary data (do not yet trust as reference):** every Qwen3.6-27B / MiMo-7B / Nemotron / Mistral-Nemo benchmark number and architecture claim. These came from a small model summarizing a page, not from primary sources — yet the saved docs present them in clean tables with the same authority as the parquet data.

One issue below is potentially load-bearing (it can void an entire section). The rest are calibration fixes.

## 1. CRITICAL — Qwen3.6's existence is not actually established, and signals you collected point against it

You wrote ~100 lines across two files treating Qwen3.6-27B as real, plus a task. But three signals in your own transcript cut against that, and they were underweighted:

- The `huggingface.co/Qwen` **org-page fetch explicitly listed Qwen3 and Qwen3.5 only — "No Qwen3.6 series models visible."** An org's own page omitting its flagship release is the strongest disconfirming signal available.
- The 4,576-model leaderboard parquet contained **zero** real Qwen3 / 3.5 / 3.6 entries (only one junk `bbhqwen3` fine-tune). You explained this via staleness — plausible for the leaderboard alone, but it compounds with the org-page omission.
- The pre-existing `model-updates` doc itself flags Qwen3.x naming skepticism (the Qwen3.7 note).

Counter-evidence is real but weaker: the direct-URL WebFetch "succeeded" with detailed specs, and the Ollama size (27B × Q4 ≈ 17GB) is arithmetically correct. But a WebFetch "success" does **not** confirm a page exists — the summarizer confabulates plausible structure on thin/redirected pages (it did exactly that for livebench/scale/arena in this same session, returning official-looking content where there was none).

I can't resolve existence from here. **This is the tie-breaker constraint:** if Qwen3.6 doesn't exist as described, the entire Qwen3.6-27B section, the M-watch task, and a chunk of the leaderboard doc are fiction. Make this the #1 verification before the docs are trusted. The definitive cheap check is the user running `ollama pull qwen3.6:27b` (or checking `qwenlm.github.io/blog`). Two minutes resolves ~100 lines.

## 2. "verified, session 78" overclaims the source

The doc labels `qwen3.6:27b` Ollama tag as "✅ (verified, session 78)." It was **WebFetch-summarized from `ollama.com/library/qwen3.6`, not pulled.** Your own project convention (CLAUDE.md, the May doc's verification taxonomy) reserves "verified" for `ollama.com/library` confirmed or `ollama pull`. Relabel to `tag-unverified` / `inferred-from-WebFetch` to match the existing taxonomy. Same applies to MiMo's "Ollama ✅" and Nemotron-Nano's.

## 3. Internal contradiction — Qwen3.6-27B "dense" vs "sparse MoE"

Within `model-updates-2026-05.md`: your new section calls it **"27B dense"** and builds the speed analysis on "dense → activates all 27B params → 3-7 tok/s." But the pre-existing Qwen3.6 subsection (lines ~54-63) describes Qwen3.6 as **"hybrid Gated Delta Networks + sparse MoE"** and references **`qwen3.6:35b-a3b`** (A3B = MoE, 3B active). If the 27B is MoE, your speed/VRAM analysis is wrong in the favorable direction (MoE would be faster, not 3-7 tok/s). Reconcile dense-vs-MoE — it changes the practical verdict.

## 4. "qwen3.6-coder:14b never existed" is an overreach

The Ollama fetch that grounds this **explicitly said only 5 of 24 tags were shown** ("24 models total… only 5 specific variants detailed in the visible table"). Concluding "Qwen3.6 skipped 14B entirely / the tag never existed" from a partial list is unsupported. Soften to "not present in the visible tags; 14B not found." Keep the prior-session search as corroboration, but don't state non-existence as fact.

## 5. All new-model benchmark tables need the May doc's caveat

The May survey carries an explicit "benchmark numbers are indicative, verify before engineering commitments" methodology note. The session-78 additions (Qwen3.6 AIME 94.1%, SWE-bench 77.2%; MiMo MATH 95.8%; Nemotron MT-Bench) drop that hedge and read as authoritative. Add a one-line provenance caveat to each WebFetch-derived block, or a doc-level note: "session-78 model specs are WebFetch-summary-derived; verify at primary source before acting." The **parquet leaderboard table is the explicit exception** — call it out as the one hard-data section so a future reader knows what to trust.

## 6. Speed/VRAM estimates are presented as table values

"~5-10 tok/s," "3-7 tok/s," "12GB VRAM + ~5GB RAM offload" appear in tables without an "estimated, unmeasured" marker. These will drive a future "is it worth it" decision. Mark them estimates. (The Ollama *download sizes* — 17GB, 24GB — are real data and fine as-is.)

## What is solid — do NOT re-litigate in the rewound session

- **Parquet-download methodology** (`datasets-server.huggingface.co/parquet` → pyarrow) is correct, reusable, and the writeup is genuinely valuable. The "walls hit" sequence will save real time next round.
- **License reasoning** (CC-BY-NC-4.0 and NVIDIA-Internal-Research taint the Layer-7 DPO pipeline; TII license is permissive-but-non-standard) is sound.
- **Kimi K2 = cloud-only** (1T total params, ~125GB at Q2) is correct and well-argued.
- **Leaderboard-staleness finding** (2025-26 models absent because developers moved to AIME/SWE-bench) is correct and is the most useful single takeaway in the survey.
- **File split + index pointer** follows project convention.

## Concrete verification checklist for the rewound session

1. `ollama pull qwen3.6:27b` (or check `qwenlm.github.io/blog`) — **gate everything Qwen3.6 on this.** If it fails, delete/flag the Qwen3.6-27B section, its task, and the leaderboard-doc references.
2. Resolve dense-vs-MoE for Qwen3.6-27B; fix the speed analysis to match.
3. Relabel all "verified, session 78" → match the May doc's verification taxonomy.
4. Soften "qwen3.6-coder:14b never existed" → "not found in visible tags."
5. Add WebFetch-provenance caveat to session-78 benchmark blocks; explicitly mark the parquet table as the hard-data exception.
6. Mark tok/s and VRAM-offload figures as estimates.

Net: the methodology and hard-data portions are publishable as-is; the model deep-dives need a provenance pass and one existence check before they're reference-grade.
