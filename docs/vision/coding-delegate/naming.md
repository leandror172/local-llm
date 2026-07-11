# Naming (V-D1 — open)

Split from `vision.md` on 2026-07-11 when the discussion outgrew a section. This file is the
single home for the naming decision: criteria, candidate register, signals, and eventually the
decision record.

<!-- ref:delegate-naming -->
## Status, criteria, current leans

**Status:** OPEN. Working label **coding-delegate**. Deadline: decide **before P1 ships CLI
entry points** — until then everything renames for free (folder, docs, the `delegate-*` ref
keys — rename those once at decision time or never; they name the *transaction* and can
outlive any brand).

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

**Current leans (NOT decided):**
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

*(empty — filled when V-D1 closes; record the pick, the runner-up, and why)*
