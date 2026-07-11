# Naming (V-D1 — open)

Split from `vision.md` on 2026-07-11 when the discussion outgrew a section. This file is the
single home for the naming decision: criteria, candidate register, signals, and eventually the
decision record.

<!-- ref:delegate-naming -->
## Status, criteria, current leans

**Status:** DECIDED 2026-07-11 — **oficina** (see Decision record below). The folder and the
`delegate-*` ref keys keep the `coding-delegate` working label (they name the *transaction*
and outlive the brand — the "rename once or never" option resolved to *never*); the brand
carries the package, CLI, and narrative from P1 on.

**What carries the name:** folder + docs (cheap), Python package + CLI (expensive after P1 —
the `st-*` precedent), portfolio story (tier-3 framing). NOT the MCP tools — those stay
generic verbs (`submit_run`) inside ollama-bridge, outside Claude's tool-calling hot path.

**CLI shape note (relaxes prefix pressure):** `st-handoff`/`st-resume` are prefixed because
they are two separate tools. This system is ONE tool with verbs — the likelier shape is a
single entry point with subcommands (`<name> submit|status|result|cancel|answer`), which
makes even longer names ergonomic. Prefix brevity (C3) matters less than it first appeared.

**Criteria:**
- **C1 — Identity fit.** Does it name what makes this different? The loop mechanics exist in
  Aider/mini-swe-agent; the distinctive thing is the supervised flywheel (master reviews →
  corrections become training data → autonomy is earned) and the deterministic harness.
- **C2 — Collisions / greppability.** Ecosystem (searchable) and in-repo (unique token).
- **C3 — CLI ergonomics.** ASCII only (no diacritics), no shell/tool collisions, short-ish.
- **C4 — Cross-language catchability** *(added 2026-07-11 from user signal)*: a PT-BR name
  must be readable/sayable by English speakers even if opaque — "*some* names may work, like
  'oficina' — an English speaker can still catch/say that, even if they don't know the
  meaning." This filters PT candidates: accent-free + phonetically transparent pass
  (oficina, aprendiz, obra); accented ones fail C3/C4 outright (ateliê, fábrica, ofício).
- **C5 — Estate culture.** All infra names are descriptive-functional (ollama-bridge,
  session-tracking, ref-indexing, ltg); personas are the one anthropomorphic corner. A
  story-name would be the estate's first — justified only if the relationship IS the identity.
- **C6 — Horizon longevity.** Survives H2 autonomy? (Or is renaming-at-graduation a feature?)
- **C7 — Portfolio story.** Outward-facing narrative quality ("I built an apprenticeship
  system for local models" / "a repair-shop harness for local models").

**Naming subjects — the framing question:** name the **worker** (apprentice, aprendiz), the
**place** (oficina, foundry, workshop), or the **transaction** (delegate, commission)?
Worker-names capture the flywheel relationship; place-names capture the deterministic
harness and dodge anthropomorphism; transaction-names are safe and bland.

**Composition option (may dissolve the either/or):** name the *system* as the place and keep
guild language for the *roles* — the **oficina** where the **aprendiz** works under the
**mestre** (Claude), with **graduation to journeyman** as the H2 gate (V-D2). The metaphor
system stays fully coherent in PT-BR and mostly transparent in English.

**Leans as they stood before the decision (kept for the record):**
- After the 2026-07-11 round, shortlist: **oficina** (place, PT — user-highlighted) ·
  **aprendiz** (worker, PT — near-cognate, instantly parsed by EN speakers) · **apprentice**
  (worker, EN) · **delegate** (descriptive fallback, current label).
- *foundry*/*forge*/*runner* effectively eliminated by C2/C3 collisions
  (Azure AI Foundry / Laravel-Atlassian Forge / `fd` finder / `fg` builtin / CI runners).
- *journeyman* is RESERVED as H2 milestone language regardless of the system name.
- The Sorcerer's Apprentice shadow on worker-names: automation escaping the master is this
  design's canonical failure mode — budgets/gates/intake exist to prevent it. Read as a
  built-in reminder, but it needs a conscious yes; place-names avoid it entirely.

**User signals log:**
- 2026-07-11: "No name yet, but I like the suggestions; we have to discuss them more deeply
  later." Then: PT-BR signature "can be interesting; *some* names may work, like 'oficina' —
  an English speaker can still catch/say that, even if they don't know the meaning."
- 2026-07-11 (deciding round): "Oficina works for now" — followed by the correction that
  settled the *framing*: the flywheel/fine-tuning is NOT the objective ("not every model
  allows that; putting it as the objective itself is already a problem… it getting better is
  a property of it") — the tool's identity is the delegation harness itself. And the
  `my-aprendiz-*` persona idea is incoherent with the estate: it would either duplicate or
  flatten the per-language+role persona matrix (`my-python-*` vs `my-mcp-*` etc.).
<!-- /ref:delegate-naming -->

<!-- ref:delegate-naming-candidates -->
## Candidate register

| Name | Subject | Lang | Story / meaning | Collisions | CLI | EN-catchability (C4) | Notes |
|---|---|---|---|---|---|---|---|
| **oficina** | place | PT | Workshop; in PT-BR strongly connotes the **repair garage** — diagnose → fix → verify in bounded time, which is literally the loop | ~zero in dev tooling (ITC Officina is a typeface; harmless) | `oficina <verb>` or `ofi-` | **High** — accent-free, phonetic; Latin *officina* (workshop; survives in EN "officinal"); "office" adjacency aids recall | Strongest place candidate; garage connotation fits repair-loop identity better than foundry's casting metaphor |
| **aprendiz** | worker | PT | Apprentice — the supervised flywheel, PT signature | ~zero | `ap-` clean | **High** — near-cognate, EN speakers parse it instantly | Best dual-language worker option |
| **apprentice** | worker | EN | Learns from the master's corrections until trusted (DPO flywheel) | Generic word; Sorcerer's Apprentice culture | `ap-` clean | native | Graduation arc built in; anthropomorphic |
| **delegate** | transaction | EN | You delegate to the delegate | .NET delegates (mild, dev-familiar) | `dg-`/`del-` (delete-ish) | native | Current working label; safest, blandest |
| **commission** | transaction | EN | Brief → draft → revision rounds → acceptance — the most semantically accurate word here | Art commissions (harmless) | `cm-`; long | native | Accuracy champion, ergonomics loser |
| **obra** | deliverable | PT | A (commissioned) work — each run delivers an *obra* | "opera" false-friend, minor | `ob-` | Medium-high — short, easy | Names the deliverable, not the system; could coexist with any system name |
| **workshop** | place | EN | Where the work happens | Generic word, meeting-culture baggage | `ws-` (websocket-ish) | native | Too generic |
| **bancada** | place | PT | Workbench (also lab/political bench) | ~zero | `bc-` | Medium — sayable, no EN anchor | Meaning fully opaque to EN |
| **understudy** | worker | EN | Learns the role by watching; performs when ready | Theater term, mild | `us-` (US!), `und-` | native | Weak CLI; passive connotation misses the loop |
| **forge** | place | EN | Shaping by repeated hammering — actually the best *iterative* metaphor | SEVERE: software forges, Laravel/Atlassian Forge | `fg-` = shell builtin | native | Eliminated on C2+C3 despite good metaphor |
| **foundry** | place | EN | Casts deliverables from spec-molds | SEVERE: Azure AI Foundry, Palantir Foundry | `fd-` = fd finder | native | Eliminated; casting is also the *wrong* metaphor (no iteration) |
| **runner** | transaction | EN | Runs deliverable runs | CI runners, heavy | `rn-` | native | Eliminated on C2 |
| **journeyman** | worker (H2) | EN | The graduated apprentice — bounded unsupervised plans | — | — | native | RESERVED: H2 milestone language, not a system name |

Accent-filtered out before the table (fail C3/C4): *ateliê*, *fábrica*, *ofício*, *máquina* —
diacritics disqualify CLI/package names, and de-accenting reads wrong in PT.
<!-- /ref:delegate-naming-candidates -->

## Decision record

**Decided 2026-07-11. Pick: `oficina`. Runner-up: `aprendiz`.**

**Why oficina (and why the decision got easier mid-discussion):** the deciding move was a
user correction to the C1 identity framing. C1 originally named *two* distinctive traits —
the deterministic harness and the supervised flywheel — and the discussion had drifted toward
weighting the flywheel (apprenticeship → corrections → DPO → autonomy) as the identity. The
user rejected that weighting: **the objective is the delegation harness itself** — an async
alternative to doing the grind by hand (the four measured problems in `ref:delegate-vision`
are all delegation problems); self-improvement is a *property* of operating it, not the
purpose — and fine-tuning is the least certain part of the design (model-dependent, Layer-7
future; V-D2 is explicitly allowed to fail). With C1 recalibrated to harness-first, the
worker-names (aprendiz/apprentice — whose entire story is the flywheel) lose to the
place-name that names the harness: intake → bounded loop → verify → deliver. Oficina's PT-BR
repair-garage connotation is literally that loop; it passes C2 (~zero dev-tooling collisions),
C3/C4 (accent-free, EN-catchable — user's own example), and C7 ("a repair-shop harness for
local models"). Naming principle worth keeping: **name what the thing does, not what it might
become** — consistent with the estate's descriptive-functional culture (C5).

**Guild-roles composition: DEMOTED to narrative garnish.** No aprendiz/mestre anywhere
operational — no personas, no config fields, no schema/event names. Specifically rejected:
a `my-aprendiz-*` persona family — the run spec's `model: auto | <persona>` routing already
consumes the existing per-language+role persona matrix, and a new family would either
duplicate it (drift) or flatten it (losing the earned per-language constraints). **Exception
kept: `journeyman`** stays RESERVED as H2 milestone language for V-D2 ("bounded unsupervised
work, earned by evidence") — one reserved word, no frame around it.

**Metaphor boundary rule (binding on phase plans):**
- README / portfolio / docs prose / report tone: metaphor allowed where it clarifies.
- CLI + package: `oficina` with plain literal verbs (`oficina submit|status|result|cancel|answer`).
- Code identifiers, schema fields, ledger event names, MCP tool names: **no metaphor** —
  standard vocabulary only (S6 already adopts MCP Tasks state names for interop; identifiers
  must not require translation to reason about).

**What carries the name:** Python package + CLI entry point (P1), portfolio narrative.
**What keeps the working label:** this folder (`docs/vision/coding-delegate/`), the
`delegate-*` ref keys, and the T-84 task language — they name the transaction, are load-bearing
as anchors/links, and renaming them buys nothing (C2 greppability argues for leaving them).
