## 2026-07-01 - Session 99: Career chatbot Groq TPM fix — routed quick files, budget guards, RAG heading vocabulary

### Context

Side-track session: the career chatbot HF Space free backend (Llama 3.3 70B via Groq) was 413-ing on every question.

### What Was Done

- fix(hf-space): keep Groq requests under the 12K TPM free-tier limit — 16 non-root quick files demoted from static SYSTEM_PROMPT (~20K→~4.2K tokens) into the routed section index (cap 3→5, headings-only), CONTEXT_CHAR_BUDGET guard, HISTORY_CHAR_BUDGET=3000 history window (Sonnet subagent + main-session follow-ups; 66→68 tests)
- docs(retrieval): add RAG/LTG query vocabulary to .memories headings — post-deploy probe showed "work on RAG?" missed all LTG sections because headings-only routing carries no lexical signal from insider headings; after rename the router selected 4/4 LTG sections
- fix(hf-space): retry on sub-second Groq rate-limit waits — _retry_after only parsed h/m/s, Groq's "try again in 85ms" was misclassified non-retriable; measured overshoot was 17 tokens (12,017 vs 12,000), now absorbed by retry
- Expenses repo (parallel session) consolidated .memories/QUICK.md 46.3K→16.2K chars per the Tier-0 contract; audit at ~/workspaces/expenses/code/.claude/quick-memory-audit-2026-07-01.md; regrowth root cause (handoff episodic append) filed here as T-67
- Deployed to leandror777/engineer-profile twice and live-verified both probe questions ("LLM projects", "work on RAG?")

### Decisions Made

- Routing index is headings-only (snippets would cost ~7.6K tokens); consequence: corpus authors own the retrieval vocabulary — section headings must carry query terms (RAG, embedding, vector store), recorded in the docs(retrieval) commit message
- HISTORY_CHAR_BUDGET default 3000 chars (~750 tok) — must fit inside the ~970-token slack left after baseline + routing + max_tokens; env-tunable on the Space without redeploy
- Left worst-case at ~11.9K vs the 12K ceiling rather than trimming more context — transient clips are absorbed by retry (Groq waits are sub-second at that margin)

### Next

- LTG Phase 4 — graph + communities (unchanged top priority)
- T-67: make session-handoff consolidate QUICK.md into KNOWLEDGE.md instead of appending (prevents the chatbot regression from regrowing)
- Optional: re-run the two probe questions after future sync-context.sh runs as a retrieval smoke test

### Gotchas

- Groq 413 "Payload Too Large" on the free tier is actually the 12K TPM rate limit (input + max_tokens across all calls in the minute), not a message-size limit — unretryable if a single request exceeds the budget
- Python 3.13 asyncio "Invalid file descriptor: -1" traceback at HF Space startup is benign GC noise (Exception ignored in BaseEventLoop.__del__), present before and after the fix
- char/4 token estimates proved accurate to ~0.5% (predicted ~11.95K worst case; Groq measured 12,017)
