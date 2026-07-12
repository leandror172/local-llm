# coding-delegate — Folder Index

*Authoritative local index for the coding-delegate vision (system name: **oficina**, decided
2026-07-11 — V-D1). The root
`.claude/index.md` holds only a pointer here; new files or ref keys in this folder get
indexed HERE, not there.*

## Files — by the question a future session has

| You need to recontextualize… | Read | Ref keys |
|---|---|---|
| *What is this? End state? What is it NOT?* | `vision.md` | `delegate-vision`, `delegate-first-principles`, `delegate-non-goals` |
| *What is it named, and why?* | `naming.md` | `delegate-naming` (DECIDED: oficina — record + boundary rule), `delegate-naming-candidates` (13-name register) |
| *How is the system shaped?* | `architecture.md` | 10 keys — see inventory |
| *What's settled (and why), what's open?* | `decisions.md` | `delegate-stances` (S1–S21), `delegate-open-decisions` (V-D1–V-D13) |
| *What do we know? Evidence per stance?* | `evidence.md` | `delegate-evidence-*` (6 keys) |
| *What gets built, in what order?* | `phasing.md` | `delegate-phasing` (P1–P6) |
| *What events exist? What's frozen vs draft?* | `event-model.md` | `delegate-event-model` (vocabulary + freeze ladder; Mermaid `eventmodeling` slices; medium-decision record) |
| *How is P1 built?* | `../../plans/oficina-p1-async-substrate.md` (FROZEN 2026-07-11) | `delegate-p1-goal`, `delegate-p1-decisions` (P1-D1–D11), `delegate-p1-acceptance` |
| *What does it touch in the estate?* | `integration.md` | `delegate-conventions-mapping`, `delegate-estate-map`, `delegate-cross-repo` |
| *Human intro + provenance* | `README.md` | — |
| *Current project state (~30 lines)* | `.memories/QUICK.md` | — |

Cold-start order: `vision.md` → `phasing.md` → `architecture.md`; pull `evidence.md` sections
on demand via `.claude/tools/ref-lookup.sh KEY`.

## Ref key inventory (28 — all resolve via `ref-lookup.sh`)

| Key | One-liner |
|---|---|
| `delegate-vision` | Intent, the 4 measured problems, the two horizons (H1 Claude-gated / H2 autonomous) |
| `delegate-first-principles` | 8 principles: deterministic spine, structured-output-only, async-buys-quality, narrow intake, events, discriminating signals, failure triad, flywheel |
| `delegate-non-goals` | Not an architect / not a framework / not on MCP Tasks or sampling / single-run v1 / license exclusions |
| `delegate-naming` | V-D1 status, criteria C1–C7 (incl. cross-language catchability), composition option, current shortlist |
| `delegate-naming-candidates` | Full 13-name register scored on subject/lang/collisions/CLI/EN-catchability |
| `delegate-architecture` | Component diagram + ownership |
| `delegate-mcp-surface` | submit / status(since_offset) / result / cancel / answer; polling-only rationale; run-ID hygiene |
| `delegate-run-spec` | Draft spec fields + deterministic intake rejections |
| `delegate-worker` | Detached lifecycle: survives session, not reboot; crash containment; cold-start grace |
| `delegate-ledger` | Event-sourced JSONL; KurrentDB decision + named upgrade trigger |
| `delegate-state-machine` | MCP-Tasks state names + internal phases; approval gate; exhaustion = degraded delivery |
| `delegate-loop` | Iteration anatomy: generate → evaluate(delta) → classify → repair/fresh-start → budget; escalation ladder |
| `delegate-workspace` | `in_place \| worktree` seam; deliverable-as-branch; security note |
| `delegate-gpu-policy` | Phase-batching math; same-base judge; app-level queue vs Ollama queue |
| `delegate-monitoring` | watch-run.sh background pattern; hook polish later; what MCP measurably can't do |
| `delegate-stances` | S1–S21 settled stances, each citing its evidence |
| `delegate-open-decisions` | V-D1–V-D13 with leans + named triggers |
| `delegate-evidence-verdicts` | calls.jsonl analysis (457 calls / 49 verdicts): defect classes, trend, caveats, regen commands |
| `delegate-evidence-prior-art` | Aider / mini-swe-agent / SWE-agent / OpenHands / Agentless / AutoCodeRover — architectures + licenses |
| `delegate-evidence-mcp` | Client blocking-only (issue #31893); Tasks extension flux (2026-07-28 RC); sampling deprecated; WorkOS notes |
| `delegate-evidence-selfrepair` | Decay data, 2–3 iteration budget, fresh start, scale caveats, 14B floor, paper IDs |
| `delegate-evidence-dpo` | Target-DPO, token-level diff masking, reward hacking, judge-gate rule, Layer-7 math |
| `delegate-evidence-clones` | claude-code patterns (Task.ts store, lockfile, offset polling) + OMA LoopDetector; provenance rules |
| `delegate-phasing` | P1 substrate → P2 loop → P3 assembly → P4 judge/report → P5 questions → P6 flywheel + H2 pilot |
| `delegate-event-model` | Event vocabulary + freeze ladder (envelope + P1 freeze candidates vs draft-PN); run-ledger vs worker-ledger split |
| `delegate-conventions-mapping` | `local-model-conventions` rule → component table (the design's core justification) |
| `delegate-estate-map` | Consumed assets; tasks fed (T-81/T-77/T-76/T-55/T-21/T-14/M-P1b); plan-v2 refs; inherited constraints |
| `delegate-cross-repo` | web-research field report; LTG dependency direction; clones verdicts |

## Supporting research artifacts (produced 2026-07-11, same session)

| What | Where | Notes |
|---|---|---|
| Prior-art survey (frontier arm) | `docs/research/coding-subagent-prior-art.md` | Harness architectures + licenses; MCP async spec state; self-repair evidence; DPO pitfalls; AutoCodeRover exclusion |
| Prior-art survey (web-research arm) | `docs/research/coding-subagent-prior-art-webresearch.md` | Same topics via web-research MCP only; per-call operational appendix — the comparison artifact |
| Clones survey | `docs/research/coding-subagent-clones-survey.md` | `~/workspaces/clones/` patterns, file-path-cited; claude-code = patterns only (proprietary); open-multi-agent MIT |
| web-research field report (cross-repo) | `~/workspaces/web-research/docs/reports/2026-07-11-field-report-llm-prior-art-run.md` | Defects D1–D5 + proposed fixes + triage order, for that repo |

## Memory files

| QUICK.md | KNOWLEDGE.md |
|---|---|
| `.memories/QUICK.md` — current project state, next step, ~30 lines | **Deferred.** `decisions.md` + `evidence.md` already play the semantic-memory role (decisions + rationale, ref-keyed). Create a real KNOWLEDGE.md when implementation experience accretes beyond vision level — trigger: first phase built. |
