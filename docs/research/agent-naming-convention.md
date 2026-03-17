<!-- ref:agent-naming-convention -->
# Agent Naming Convention

*Established session 44b. Applies to all web research tool documentation.*

---

## Role-Based Agent Names

| Role | Name | Why | Alternatives Considered |
|------|------|-----|------------------------|
| Research manager, orchestrates, iterates | **Conductor** | Orchestrates the ensemble, doesn't play instruments | Planner, Director, Pilot |
| Pipeline builder, tool caller, data router | **Dispatcher** | Dispatches work to tools, routes data | Router, Operator, Switchboard |
| Sufficiency reviewer, quality gate | **Auditor** | Reviews quality, gives go/no-go verdict | Critic, Gatekeeper, Sentinel |
| Context proxy, sifts results for Conductor | **Lens** | Focuses on specific parts of accumulated knowledge | Scout, Sifter, Librarian |

## Legacy Designations

Original names from the user's initial architecture thinking (session 44):

| Legacy | Current |
|--------|---------|
| Agent A | Conductor |
| Agent Tool | Dispatcher |
| Agent B | Auditor |
| Agent A2 | Lens |

Legacy names are preserved in `web-research-tool-user-notes.md` (raw user text) with a naming key header.
All other research documents use the current role-based names.

## Usage Notes

- These names are specific to the **web research tool** architecture
- In generic/abstract discussions (e.g., anti-pattern examples in `ddd-agent-decisions.md`), use Agent X/Y to avoid conflation
- The names reflect roles, not implementations — Conductor could be an LLM or a script; Dispatcher is likely deterministic code
<!-- /ref:agent-naming-convention -->
