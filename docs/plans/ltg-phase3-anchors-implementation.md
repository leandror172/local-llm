# LTG Phase 3 — `anchors.py` Implementation Plan

**Status:** Ready to execute (TDD). Decisions frozen session 82 (`ref:ltg-phase3-decisions`).
**Branch:** `feature/ltg-phase3-anchors` (already merged to master — work continues on a fresh branch off master).
**Authored:** session 94 (2026-06-20). Grounded against live repo + recovered field-population table.

> This plan is the buildable spine. The *why* lives in `ref:ltg-phase3-decisions` (frozen
> decisions) and `ref:ltg-phase3-discussion` (reasoning). Read those first; this file is the *how*.

---

## 0. What Phase 3 delivers

Ingest every `<!-- ref:KEY -->` marker in tracked `*.md`, create one **anchor node** per unique key,
embed its `mechanical+key` description, link it to semantically-near topic rows via `alias_of`, and
rebuild the LanceDB `topics` table with both surfaces present. Anchors are a **parallel retrieval
surface** (dual-path), not merge-targets — both anchor rows and topic rows survive.

**Grounded facts (verified session 94):**
- **143 unique ref keys** in tracked `*.md` (`git grep -hoE '<!-- ref:[a-z0-9-]+ -->'`). Count is
  derived at runtime — never hard-coded.
- On-disk index: **69 topic rows, qwen3-embedding:8b, 4096-dim** → topic vectors are reused, not re-embedded.
- `.claude/local/` is gitignored → `git grep` (tracked-only) gives the D2 safety filter for free.
- Only **2 of 143** keys live inside the 8 extracted corpus files (`smart-rag-research` in
  `smart-rag-index.md`-adjacent, `rag-repowise` in `smart-rag-repowise.md`). The other ~141 are
  legitimate orphans — most correctly never merge.

---

## 1. Decisions locked (recap — see frozen block for rationale)

| # | Decision | Locked value |
|---|----------|--------------|
| D2 | Scope | Repo-wide, tracked `*.md` via `git grep` |
| D3 | Description | `f"{bare_key}: {heading} — {first_prose_line}"` — hyphenated key, **no space-normalization** |
| D5 | Merge representation | alias-link, M:N; `alias_of` = JSON list of anchor keys on the **topic** row; both rows survive |
| D1 | `confidence` | node-provenance only: anchor `1.0`, extracted `0.7`; **not** modified by aliasing |
| D7 | Path routing | deferred to Phase 6; Phase 3 only stores both surfaces |

**Session-94 decisions (this discussion):**
- **Escalation** → **diagnostic-only**. No LLM/conditional logic in Phase 3. Emit a near-miss report; decide escalation in Phase 3.5 from real data.
- **Methods** → `--method` CLI flag (`mechanical+key` default, `key_only`, `mechanical`). Per-method integration tests in separate files; shared unit tests consolidated.
- **Staleness** → reuse stored topic vectors; **preserve** topic provenance fields on rebuild; **warn** if any source file mtime > its row's `extraction_timestamp`. Do not re-extract (deferred to Phase 2.5 per D6 #4).
- **Threshold/config** → hardcode `COSINE_THRESHOLD = 0.85` as a named constant with a `# TODO Phase 5: move to config.yaml` note.

---

## 2. The write path — full rebuild (overwrite-only store)

`store.py` is **overwrite-only** (`db.create_table(..., mode="overwrite")`, line 99) — there is no
incremental column-add or row-update. Phase 3 is therefore a **full table rebuild**, which fits the
existing single-ingest-path design (`ref:ltg-storage-layout`) and reuses store.py's auto-backup.

```
1. ingest_anchors(repo_root)         # git grep → [(file, line, bare_key)], dedup by key
2. read 69 topic rows from index     # vectors INCLUDED — no re-embed
3. for each anchor: build description (method) → embed → 4096-d vector
4. match_anchors(anchors, topics)    # exact in-memory cosine ≥ 0.85
5. set alias_of (JSON list) on matched topic rows
6. backfill new fields on topic rows: source_class="topic_extracted", confidence=0.7, anchor_key=null
7. build anchor rows (field table §4)
8. build_schema_v3(embed_dim) → 22 fields (+source_class,confidence,anchor_key,alias_of)
9. write topics + anchors together via store path (mode="overwrite", auto-backup)
10. integrity check + staleness warning + diagnostic report
```

`★` Why this is *simpler*, not harder: because the store is overwrite-only and the corpus is tiny
(~212 rows, ~3s rebuild), "update a topic's `alias_of`" and "add ~143 anchor rows" collapse into the
**same single operation**. A mutable store would have forced `add_columns` + `merge_insert`.

---

## 3. Matching mechanism — exact in-memory cosine, NOT LanceDB ANN

- 143 anchors × 69 topics = ~9.9k dot products — trivially free.
- Vectors are **unit-normalized** (qwen3-embedding:8b; probe norm 0.999999–1.0), so cosine = dot product.
- **Exact** matters for M:N alias correctness — ANN is approximate and could drop a valid alias.
- Sidesteps the "query before or after rebuild?" ordering question entirely (matching happens in
  memory between read and write).

```python
COSINE_THRESHOLD = 0.85   # TODO Phase 5: move to config.yaml; provisional, LTG-self-referential probe only
# L2 equivalent for reference: sqrt(2*(1-0.85)) = 0.5477 (valid only for unit-normalized vectors)
```

---

## 4. Anchor row field population (authoritative — from `retrieval/DECISIONS.md`)

| Field | Anchor value | Nullable? |
|---|---|---|
| `id` | `anchor_key` (`"ref:KEY"`) — globally unique, used by integrity check | no |
| `file_path` | source file from grep (`file:line` → `file`) | no |
| `topic_name` | snake-case of bare key (`concept_latent_topic_graph`) | no |
| `description` | the `mechanical+key` string (the embedded text) | no |
| `spans` | `"[[start_line, start_line]]"` (single-line point from grep) | no |
| `vector` | 4096-d embedding of description | no |
| `embed_model` | `"qwen3-embedding:8b"` | no |
| `embed_dim` | `4096` | no |
| `embed_mode` | `"description"` | no |
| `embedding_timestamp` | ISO-8601 UTC at ingestion | no |
| `extractor_model` | `""` (not extracted) | no → **empty string** |
| `extraction_run_id` | `""` | no → **empty string** |
| `extraction_timestamp` | `""` | no → **empty string** |
| `file_role` | `"anchor"` | no |
| `node_kind` | `"anchor"` | no |
| `scope_tags` | `"[]"` | no → **empty JSON array string** |
| `segment_id` | `null` | yes |
| `segment_range` | `null` | yes |
| `source_class` | `"anchor_ref"` | (new) |
| `confidence` | `1.0` | (new) |
| `anchor_key` | `"ref:KEY"` | (new, nullable) |
| `alias_of` | `null` (anchors don't alias anchors) | (new, nullable) |

**Nullable resolution** (advisor catch): every non-nullable provenance field that an anchor lacks gets
the empty string `""` / `"[]"` — PyArrow accepts those in non-nullable columns. Only `segment_id`,
`segment_range`, `anchor_key`, `alias_of` are genuinely null. New fields `source_class`/`confidence`
are non-nullable and always set for **all** rows (topics get `"topic_extracted"`/`0.7`).

---

## 5. Module surface (`retrieval/anchors.py`)

Following `ref:patterns-code-named-methods` — named intent-methods, private dispatch.

```python
# ingestion
def ingest_anchors(repo_root: Path) -> list[Anchor]        # git grep, dedup by key, parse heading+prose
def parse_first_prose_line(body: str) -> str               # skip blank/italic-meta/##/---/HTML-comment

# description (D3) — method-parameterized private, named public wrappers
def describe_mechanical_key(anchor) -> str                 # default: key + heading + prose
def describe_key_only(anchor) -> str                       # fast fallback
def describe_mechanical(anchor) -> str                     # body-only (validates failure on plan-type)

# matching
def match_anchors(anchors, topic_rows, threshold=COSINE_THRESHOLD) -> dict[topic_id, list[anchor_key]]

# row construction
def build_anchor_rows(anchors, vectors) -> list[dict]      # field table §4
def apply_aliases(topic_rows, matches) -> list[dict]       # set alias_of + backfill new fields

# orchestration
def rebuild_index(repo_root, index_path, method="mechanical+key") -> RebuildReport

# diagnostics
def staleness_warnings(topic_rows, repo_root) -> list[str] # mtime > extraction_timestamp
def nearmiss_report(anchors, topic_rows) -> list[dict]     # see §7
```

Bash wrapper: `retrieval/run-anchors.sh` (parallel to `run-embed.sh`/`run-store.sh`), whitelist-safe;
add to `ref:bash-wrappers` + `.claude/index.md`.

---

## 6. Test layout (TDD — separate files per use case)

**Fixture strategy (advisor catch):** the embedding model is ~4s/call under a hard sequential
constraint — unrunnable in a red/green loop. So **all logic tests use fixed/mocked vectors**; exactly
**one** real-model acceptance test is marked `@pytest.mark.slow`.

```
retrieval/tests/
  conftest.py                         # fixtures: tmp repo w/ ref blocks, fixed topic vectors, fake embedder
  test_anchors_unit.py                # parse key, prose-skip rules, description format, snake_case, cosine math
  test_anchors_match.py               # threshold, M:N both directions, orphan no-match (mocked vectors)
  test_anchors_rows.py                # field population §4, nullable handling, alias backfill, schema_v3
  test_anchors_integrity.py           # every grepped key → ≥1 anchor row; safety filter; staleness warn
  test_anchors_method_mechanical_key.py  # integration, mocked embedder, default method
  test_anchors_method_key_only.py        # integration, key-only path
  test_anchors_method_mechanical.py      # integration, body-only — asserts plan-type anchor FAILS to merge
  test_anchors_acceptance_slow.py     # @pytest.mark.slow: real qwen3-embedding; concept-ltg↔.memories ~0.97
```

Unit tests use explicit cases (no parametrization); per-method integration files may parametrize over
anchors against the shared fixed-vector corpus.

---

## 7. Diagnostic (escalation deferred — diagnostic-only)

**Reframed per advisor:** a binary "top match < 0.80" flag would light up ~141 of 143 keys (legit
orphans) — pure noise on the current corpus. Instead emit a **near-miss report**: anchors whose top
match sits in the *interesting band* `[0.80, 0.85)` (just below threshold — e.g. `graph_exploitation`
at 0.836), plus the score distribution. That is the signal Phase 3.5/2.5 actually needs.

Output: `retrieval/probes/anchor-nearmiss-<ts>.md` — `{anchor_key, top_topic, top_cosine, band}`.
Plan note: **inert until Phase 2.5 corpus expansion** — say so in the report header so nobody mistakes
an empty report for "nothing to escalate."

---

## 8. Acceptance (D6 — same corpus, Phase 2.5 revalidates)

1. **Sanity:** the 2 corpus-resident keys merge with topics from their own files (tautological; exercises pipeline).
2. **Real (probe-verified):** `ref:concept-ltg` ↔ `.memories/QUICK.md::ltg_implementation` (~0.972) +
   `KNOWLEDGE.md::latent_topic_graph` (~0.970); `ref:plan-ltg` ↔ same two (~0.898/0.861). **M:N** —
   both anchors alias the same two topics → `alias_of` JSON list correct.
3. **Orphan:** `ref:ltg-corpus` no-merge (correct).

---

## 9. Honest limitations (carried to Phase 2.5)

- All probe merges are **LTG-self-referential** (key tokens appear in targets — most favorable case).
  False-merge precision on generic anchors (`ref:git-safety`) is **untested**.
- Threshold `0.85` is provisional from a 3-anchor probe — recalibrate from full distribution at Phase 2.5.
- Topic rows may be **stale** vs current files — Phase 3 links against the snapshot; re-extraction
  before Phase 2.5 → re-run linking (D6 #4). Provenance fields preserved + mtime warning make this visible.

---

## 10. Out of scope (explicit)

Phase 4: edges/graph/communities (`alias_of` is a proto-edge it will relocate). Phase 5: retrieval-weight
tuning (`source_class` is a placeholder field). Phase 6: dual-path routing. Escalation LLM pass (Phase 3.5).
Threshold recalibration + generic-anchor precision (Phase 2.5).
