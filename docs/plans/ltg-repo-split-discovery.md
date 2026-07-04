# LTG Repo Split (T-33) — Discovery + Open Decision Register

**Status:** SUPERSEDED — S-D1–S-D7 FROZEN session 107 (2026-07-04) in
`docs/plans/ltg-repo-split.md` (`ref:ltg-split-frozen-decisions`). This doc remains the
discovery record (drivers, dependency map, register rationale). Created session 106.
**Task:** T-33 (`.claude/tasks.md`). Plan-gate note: `ref:ltg-plan-phase-6`.
**Next step:** one fresh session = freeze S-D1–S-D7 + author `docs/plans/ltg-repo-split.md`
(the session-104 shape: freeze + plan in one sitting, execute in the following session(s)).
**Sequencing:** after PR #67 (Phase 5) merges; before Phase 6 (the MCP tool is designed once,
in its final home — the master plan itself says "if separated, implement Phase 6 in the new repo").

Companion record: `docs/ideas/ltg-model-registry-design.md` Part 2
(`ref:model-registry-library-decision`) — dependency topology, product tiers, T-76 registry
deferral, prior-art survey. This doc carries the split-specific half of the same session-106
discussion; that doc carries the registry/product half. Read both before the freeze session.

---

## Established in session 106 (not up for re-litigation without new evidence)

### The lean: SPLIT, before Phase 6

Two independent drivers align:

1. **Workflow decoupling (the primary, user-confirmed driver).** The constraint, as
   stated (session 106): **the blocking is mutual** — "there are things I want to develop
   in the other parts of the repo, and that stops LTG, and vice-versa." Concrete example:
   the deep session-tracking-overlay change/fix arc (sessions ~88–93) serialized the repo
   and stalled LTG for weeks; equally, LTG phase work blocks overlay/tooling development.
   This is a constraint-driven argument, stronger than the master plan's
   schema-stability one.
2. **Deliverable framing.** LTG + overlays are to be usable by other people/companies
   ("viable in the use sense, not the sell one"). Phase 6's MCP tool is LTG's first
   public-facing API — building it in the old home and moving later means designing it twice.

Plus a **third, smaller driver (session 106):** portfolio evidence. The deliverable
framing is partly career/portfolio-motivated — presentable tools alongside the
engineer-profile/career track. Explicitly smaller ("still a bit far from the presentation
point"), so it does NOT add engineering scope; what it does is reorder tier-3 priorities:
**cheap-and-early visibility polish (README, quickstart, demo transcript) is worth doing
well before any tier-3 engineering** (provider abstraction etc.), which stays deferred.

Counterweights, acknowledged and accepted: ~1.5–2 sessions of split mechanics; a second
repo's ongoing tracking overhead (session-handoff, PR flow, "which repo does this belong
to"); and the fact that `git subtree split` preserves history *whenever* run — the split
cost barely rises with delay, so urgency was never the argument. The drivers are.

### Verified dependency map (session 106 code inspection)

- **Code: already an island.** Every import in `retrieval/*.py` is stdlib, third-party,
  or intra-package. Own `pyproject.toml` + `uv.lock` + test suite (377 green at Phase 5).
  Nothing outside the directory imports it yet — Phase 6 would be the first consumer.
- **The real coupling is data + convention, not code:**
  - `corpus.yaml` / `corpus-manifest.yaml` — the corpus IS the llm repo (paths like
    `docs/research/`, `.claude/archive/`).
  - `anchors.py` → `git grep` for `ref:KEY` markers over the working tree. Already
    parameterized (`repo_root` arg); degrades to zero anchors on a repo without the
    convention — that degradation must become graceful-by-design (no ref keys → anchors
    source is a no-op, not an error).
  - **`store.py:44`** — `REPO_ROOT = Path(__file__).parent.parent`: the one hard landmine.
    Assumes `retrieval/` sits *inside* the corpus repo. Breaks the moment code and corpus
    live apart. Killing this assumption is non-negotiable split scope.
  - `index/` (LanceDB) — derived artifact of *this repo's* content; belongs with the
    corpus, not the code.
  - Ollama `:11434` + `config.yaml` roles — machine-level, moves freely.
- **`retrieval/` conflates three things** that the split (or Phase 8) must tease apart:
  portable **engine** (the `.py` files) · per-repo **corpus config** (`corpus.yaml`) ·
  per-repo **derived data** (`index/`). The split and the parameterization are separable
  decisions the master plan happens to bundle; the split forces the parameterization
  (~half of Phase 8 pulled forward).

### Scope lean

- **Moves:** engine code, tests, `pyproject.toml`/`uv.lock`, prompts (see S-D3 for the
  arguables).
- **Stays:** `corpus.yaml`, `corpus-manifest.yaml`, `index/` (+ backups) — the llm repo's
  instance data (residency: S-D2).
- **Rides along:** `REPO_ROOT`/corpus parameterization; **pluggable-source design stance**
  (engine never imports source-specific code; every source — topic extractor, anchors,
  future T-77 signature extractor — is a program emitting schema-conformant rows with a
  distinct `source_class`; the store schema + docs ARE the plugin interface, no plugin
  API built).
- **Explicitly OUT:** T-76 model-registry library extraction (deferred with triggers —
  see companion doc); building a formal plugin API; provider abstraction; packaging for
  external adopters (tier-3 backlog items, recorded not built).
- **Estimate:** 1.5–2 sessions (up from the master plan's ~1: the original number covered
  subtree-split + path parameterization only, not the source-discipline pass).

### Product/topology context (details in companion doc)

- Tiers: 1 = internal substrate (Phase 6 alone reaches it; formal success definition met) ·
  2 = multi-corpus tool (Phase 8; split pulls half forward) · 3 = adoptable product
  (mostly non-phase work; provider abstraction is the biggest gap).
- Topology rule: **products (LTG engine, overlays) depend on layer-0 primitives (model
  registry, ref-key grammar, signature extractor) — never on each other.** No
  product↔product cycles, ever.
- Bash→py: the `run-*.sh` wrappers are 3-line uv shims; conversion to `[project.scripts]`
  entry points is a *consequence* of the split's packaging flip (S-D6), not an input.
  Phase 6 consumers import `relate()` directly and never touch the CLI.
- ollama-bridge is already machine-global: cross-repo *consumption* never required
  cross-repo *code residence* — which is why workflow decoupling, not architecture, is
  the honest primary driver.
- **Future LTG overlay (user-raised, session 106: "there may be a case for an LTG overlay").**
  The eventual per-repo distribution shape: an overlay carries the **scaffolding** —
  `corpus.yaml` template, MCP registration, `.memories/` integration, rebuild
  conventions — while the **engine arrives as a package dependency, never via overlay**.
  This is the session-handoff B+C lesson applied verbatim (engine central, config
  per-repo; wholesale-file overwrite and stale-engine propagation were the failure modes
  paid for in T-61 / session 91). Feeds S-D1 and S-D4; not split scope — recorded so the
  freeze session designs S-D1 with this end-state in view.
- **Licensing (tier-3 constraint, surfaced session 106).** `leidenalg` is **GPL-3** and
  `python-igraph` **GPL-2** — the Phase 4 community stack. Internal use: unaffected.
  Distribution as an adoptable product (tier 3): constrains the license choice — either
  copyleft the product, or make `communities.py` an optional/swappable component.
  T-72(3) (drop networkx, build igraph directly) goes *deeper* into GPL — fine
  internally; caveat recorded on that task. CLAUDE.md's licensing hard rule applies the
  moment tier 3 becomes real; decide the product license then, not now.

---

<!-- ref:ltg-split-decisions -->
## Open decision register (S-D1–S-D7) — freeze before authoring the plan

- **S-D1 — Engine consumption path.** How does the llm repo (and later repos) use the
  engine post-split? Options: (a) uv path-dependency on a sibling checkout; (b) installed
  package (uv tool / pip editable); (c) user-level shared install à la handoff engine
  (`~/.claude/tools/handoff/` B+C model — precedent exists and worked, but handoff is a
  CLI; the LTG engine is a *library* imported by MCP code, so a Python-dependency path is
  more natural). Shapes S-D5 and S-D6 downstream.
- **S-D2 — Corpus config + index residency in the llm repo.** `corpus.yaml`,
  `corpus-manifest.yaml`, `index/` stay — but where? A stub `retrieval/` dir; a
  `.claude/retrieval/` instance dir; or a new top-level (e.g. `ltg-instance/`)? Interacts
  with rebuild tooling paths (`run-rebuild-all.sh`) and with `.claude/index.md` entries.
- **S-D3 — What moves vs. stays, item by item.** The arguables: `DECISIONS.md` (carries
  `ref:` blocks consumed by llm-repo `ref-lookup.sh` AND ingested as anchors into the LTG
  index itself — moving it silently breaks those keys and changes the corpus);
  `probes/` (acceptance reports reference llm-repo files); `retrieval/.memories/`
  (QUICK/KNOWLEDGE — engine knowledge vs instance knowledge is genuinely mixed);
  `prompts/` (engine-owned, likely moves); `spike-*.md` (historical, likely stays/archives).
  The `DECISIONS.md` ref-coupling is the subtle one nobody will rediscover cheaply.
- **S-D4 — New repo bootstrap.** Name; session-tracking/handoff overlay install (it becomes
  the 5th tracked repo); its own `.memories/`; PR/branch conventions; CLAUDE.md; whether
  it gets its own LTG corpus (self-indexing) from day one or later; whether per-repo
  consumer scaffolding is eventually delivered as an **LTG overlay** (see Established §
  "Future LTG overlay" — end-state to design toward, not split scope).
- **S-D5 — Phase 6 MCP placement.** (a) New `retrieval-mcp` server in the new repo — the
  master plan's lean ("first external-facing deliverable"); (b) tools added to
  ollama-bridge (llm repo) importing the engine — reuses existing machine-global
  registration but couples the products the topology rule says to keep apart. Note
  ollama-bridge would then *depend on* the engine (product→product) — S-D5 decided
  against (b) would keep the rule intact; deciding for (b) needs an explicit exception
  rationale.
- **S-D6 — Packaging flip timing.** Flip `package = false` → packaged layout +
  `[project.scripts]` entry points during the split (restructuring is forced anyway;
  lean = yes), or keep the 3-line bash shims one more round? Interacts with the
  llm repo's `[ref:bash-wrappers]` convention — wrappers stay for the *instance* rebuild
  tooling regardless.
- **S-D7 — Multi-repo session cadence.** How new-repo work interleaves with llm-repo work,
  given the now-stated constraint (see driver 1: **mutual blocking** — other-repo-part work
  stops LTG and vice-versa; session-tracking-overlay arc as the proven example). The split
  succeeds only if both directions unblock: LTG sessions run wholly in the new repo (llm
  repo touched only for instance rebuilds), AND llm-repo tooling/overlay work proceeds
  without parking LTG. Decide the cadence pattern + where handoffs write; the plan should
  encode it explicitly.
<!-- /ref:ltg-split-decisions -->

---

## Inputs for the freeze session (read first)

1. This doc + companion `docs/ideas/ltg-model-registry-design.md` Part 2.
2. T-33 entry in `.claude/tasks.md` (session-106 amendment — condensed form of the above).
3. `ref:ltg-plan-phase-6` (the gate note in the master plan).
4. `retrieval/store.py:44` + `corpus.yaml` + `anchors.py` `ingest_anchors()` (the coupling,
   firsthand).
5. Precedents: handoff-engine B+C distribution (`docs/findings/overlay-distribution-options.md`),
   T-18 uv migration slice (session 96), `git subtree split` mechanics.
