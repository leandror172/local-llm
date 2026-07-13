# Session Log

**Current Layer:** "Layer 5 — Expense Classifier (side-track: T-88 model-call gate decision recorded; next: T-86 distribution runbook + oficina P2/first-client, G-D4 priority open)"
**Current Session:** 2026-07-13 — Session 116: "2026-07-13 — Session 116: model-call gate decision (T-88) — oficina is not the gate"

---
## 2026-07-13 - Session 116: "2026-07-13 — Session 116: model-call gate decision (T-88) — oficina is not the gate"

### Context

Short discussion session after PR #75 merged and master updated. Entry point was the session-115 Next list (T-86 / P2 / first-client), but the user brought a candidate first client (LTG refresh + expense-reporter probes) that surfaced a deeper architectural question: is oficina the long-imagined async queue/gate between ALL tools and model calls?

### What Was Done

- `docs(gate)`: model-call gate decision record — oficina is not the gate (T-88): new `docs/ideas/model-call-gate.md` (G-D1–G-D6), `ollama-coordination-layer.md` marked superseded-in-scope, T-88 filed, index row added, `ref:model-gate-altitude`/`ref:model-gate-decisions` verified resolving
- `feat(personas)`: my-go-q3-14b — Go backend persona on qwen3:14b (registry entry + Modelfile verified consistent before commit)
- PR #75 (T-81 AI-merge stage/apply) merged to master at session start

### Decisions Made

- **G-D1 (decided): oficina is NOT the model-call gate.** Two altitudes: oficina schedules *runs* (product); the gate schedules *calls* (layer-0 primitive). LTG refresh / expense probes / benchmarks are gate clients, never oficina clients (they have no loop; forcing them through `submit_run` means faking deliverable specs). oficina's worker becomes a gate client behind its injectable `GenerateFn` seam. Queue-of-queues is fine because the units differ (run admission vs GPU access).
- **G-D2 (decided): client-owns-plan / gate-owns-admission** — clients submit batches with model-affinity hints + priority class; the gate does placement and swap-minimizing interleave. Keeps the gate dumb and product-agnostic.
- **G-D3 (decided): resource model = two constraint families, vocabulary now, capacity-only v1.** Family A capacity/placement (single GPU, hybrid VRAM+RAM, CPU, network/cloud GPUs); Family B rate/budget (Claude API, Groq — tokens/min, spend). v1 = local Ollama only; the descriptor just must not hardcode one GPU. User's "might be scoping too large" handled as: large scope costs one paragraph of vocabulary, zero design.
- **Open: G-D4** (gate before or after oficina P2 — user: "deserves soon, undecided"), **G-D5** (mechanism: T-21 dir-contract vs broker vs library semaphore — v1 is policy OVER Ollama's own scheduler), **G-D6** (extract oficina's generic substrate modules only when the gate is real — T-76 second-consumer rule).
- Build triggers named: observed swap-thrash; LTG `on_commit: refresh` going automatic (that decision IS the gate decision); explicit gate-first call.

### Next

- **T-86** — oficina distribution model decision + new-machine provisioning runbook (mostly transcribing what the folder KNOWLEDGE.md already establishes).
- **oficina P2 / first-client** — sharpened by T-88: LTG and expense workloads are ruled out (gate clients), so the first client must be an agent-driven multi-deliverable flow; persona hygiene (T-26/T-27) driven from a Claude loop is the standing candidate. G-D4 (gate vs P2 priority) is the open prioritization.
- Side options unchanged: T-83 freeze, T-56, classifier benchmark (M-P1b/P2), persona hygiene (T-27/T-49).

### Gotchas

- The embed/infer sequential constraint exists ONLY as a convention line in `ltg/.memories/QUICK.md` — first concrete rule the gate would own in code (recorded in the T-88 doc).
