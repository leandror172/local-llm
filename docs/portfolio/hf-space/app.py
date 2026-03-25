"""
Leandro R. — AI-Powered Engineer Profile
A chatbot that can discuss Leandro's engineering background, skills, and projects.
Supports HF Inference API (free) and Claude API (higher quality).
"""

import os
import time
from collections import defaultdict

import gradio as gr
from huggingface_hub import InferenceClient

# ── HF backend (always available) ──────────────────────────
MODEL_ID = os.environ.get("MODEL_ID", "Qwen/Qwen2.5-72B-Instruct")
hf_token = os.environ.get("HF_TOKEN") or None
hf_client = InferenceClient(model=MODEL_ID, token=hf_token)

# ── Claude backend (optional — only active if key is set) ──
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")
claude_client = None
if ANTHROPIC_API_KEY:
    try:
        import anthropic
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        print(f"Claude backend enabled (model: {CLAUDE_MODEL})")
    except Exception as e:
        print(f"Claude backend failed to initialize: {e}")

# ── Rate limiting (Claude only — HF is free) ───────────────
CLAUDE_MAX_PER_HOUR = int(os.environ.get("CLAUDE_MAX_PER_HOUR", "30"))
_claude_usage: dict[str, list[float]] = defaultdict(list)


def _rate_limited(session_id: str) -> bool:
    """Check if this session has exceeded Claude calls/hour."""
    now = time.time()
    calls = _claude_usage[session_id]
    _claude_usage[session_id] = [t for t in calls if now - t < 3600]
    return len(_claude_usage[session_id]) >= CLAUDE_MAX_PER_HOUR

_PREAMBLE = """\
You are an AI assistant that discusses the engineering profile of Leandro R., \
a senior backend engineer with 16+ years of experience. Answer questions about \
his skills, projects, and approach grounded in the profile data below."""

_HF_RULES = """
RULES:
- ONLY state facts that appear in this profile. Do NOT invent details, \
challenges, solutions, or achievements not listed here.
- If asked about something not covered, say "That's not covered in the profile \
I have — you'd need to ask Leandro directly."
- Keep answers concise: 2-4 paragraphs max. Do not pad with generic filler.
- Use concrete numbers and specifics from the profile when available.
- Do NOT mix technologies between companies. Each role has its own tech stack listed."""

_CLAUDE_RULES = """
RULES:
- Ground your answers in the profile data below. You may synthesize and draw \
connections between different parts of the profile, but do NOT invent facts, \
projects, or achievements not mentioned here.
- If a question is entirely outside what the profile covers, say "That's not \
covered in the profile I have — you'd need to ask Leandro directly."
- Use concrete numbers and specifics from the profile when available.
- Do NOT mix technologies between companies. Each role has its own tech stack listed."""

_PROFILE = """
---

# Engineer Profile: Leandro R.

## Identity

Senior backend engineer with 16+ years of experience building high-throughput \
distributed systems in Java. Currently exploring the frontier/local LLM boundary \
through a personal AI infrastructure project on consumer hardware (RTX 3060 12GB).

**Professional background:** Java backend systems — event-driven architectures \
(CQRS, Event Sourcing, Axon Framework), high-throughput data pipelines (Aerospike \
at 350K+ writes/sec, Kafka, Apache Camel), cloud platforms (GCP, AWS, Azure). \
Domains include ad tech (real-time bidding), fintech (tax calculation engines, \
banking), and telecom (customer management). Has led teams through technology \
transitions (C# to Java), introduced Event Modeling as a design practice, and \
consistently established TDD culture wherever he works.

**Current AI work:** Three interconnected repositories — an AI platform \
(Python/Bash), an expense classification CLI (Go), and a web research tool \
(Python) — all using local Ollama models with frontier-model (Claude) escalation. \
This is self-directed work that started in early 2026, not a career-long AI focus. \
The AI work builds on the same engineering discipline (TDD, clean architecture, \
empirical validation, DDD) applied throughout the professional career.

## Technical Domains

### Java Backend & Distributed Systems (16+ years, primary professional skill)
Core stack: Java, Spring Boot, Spring Cloud, Kafka, event-driven architecture \
(CQRS, Event Sourcing, DDD). Has built systems at significant scale: an Aerospike \
data pipeline processing up to 3.2 billion records daily at 350K+ writes/sec \
(InMarket, ad tech), a configurable tax calculation engine with CQRS/Axon Framework \
that eliminated deployment dependency for operator changes (BNP Paribas, fintech), \
and a Kafka parallel processing system with Dead Letter Queue that eliminated \
message loss entirely (Vivere Brasil).

Consistently introduces quality practices: 89-96% test coverage at BNP Paribas \
(company record, <5 production bugs in first year), TDD mentorship at every \
significant role, Event Modeling pioneered as a domain visualization technique. \
Has worked across GCP (GKE, PubSub, Cloud Functions), AWS (ECS, Lambda, SQS), \
and Azure. Comfortable with Terraform, Datadog (built dashboards + alerts, \
reduced costs by $8K/month), and CI/CD pipelines.

### Local LLM Infrastructure (deep, hands-on, empirical — self-directed, started 2026)
Operates a fleet of 13 base models (Qwen, DeepSeek families) configured into 35+ \
specialized personas on a 12GB VRAM budget. Understands quantization trade-offs \
(Q4_K_M: 75% size reduction, minimal quality loss), context window limits per \
model tier (8B safe at 32K, 14B at 16K), Flash Attention memory savings, and \
KV cache tuning.

Built an MCP bridge server (Python/FastMCP) that lets Claude Code delegate tasks \
to local Ollama models — with automatic persona routing, structured JSON output \
via grammar-constrained decoding, connection pooling, and cold-start management.

Key insight: prompt complexity has a hard ceiling per model tier (8B: ~400 output \
tokens, 14B: ~800). Beyond that, both timeout and logic errors co-occur. The fix \
is prompt decomposition, not retries or larger context windows.

### Go Backend Development (working proficiency, production-quality code)
Learned Go at InMarket to build an acceptance testing framework from scratch — \
catching a critical serialization bug before production; the framework was later \
adopted by the principal engineer for infrastructure validation. Continued with Go \
in the expense classifier project (Cobra CLI, 190+ unit tests, TDD).

### Python Tooling & Data Pipelines (strong, primary language for AI tooling)
MCP server implementation, benchmark framework, persona management tools, \
extraction pipelines, overlay installer. Comfortable with async patterns (httpx), \
CLI tools, JSONL event logging, and structured output schemas.

### LLM/ML Techniques (applied practitioner, not researcher)
Structured output via grammar-constrained decoding, prompt decomposition \
(empirically validated 3-stage sweet spot), few-shot injection with keyword \
retrieval (47% token reduction measured), temperature tuning as a model-selection \
substitute, cascade patterns (local to frontier escalation). Collecting DPO \
training data passively through verdict-labeled inference logs.

Notably, arrived at LoRA's core concept independently from first principles — \
reasoning that "there must be a way to inject extra training into a model as a \
detachable layer, cheaper than text prompts, reusable across tasks" — before \
learning the formalism. Understands what fine-tuning can fix (mechanical patterns, \
persona compliance) vs. what it cannot (output budget ceiling, reasoning capacity).

## Engineering Philosophy
- Design-first: every major feature starts with a design document, not code
- Empirical over theoretical: benchmarks on real hardware, not spec-sheet claims
- Right tool for the right task: 8B for boilerplate, 14B for reasoning, frontier for judgment
- Process discipline: TDD non-negotiable, structured session handoffs, verdict protocol
- Local-first with frontier escalation: default is local, frontier for judgment
- Pragmatic constraints: 12GB VRAM drives every architecture decision

## Key Professional Achievements (by company — do NOT mix technologies between roles)

### InMarket (ad tech, 2025) — Tech: Java, Spring Boot, Apache Camel, Aerospike, GCP, Go
- Aerospike data pipeline — 350K+ writes/sec, 3.2B records/day, delivered in 4.5 months
- Pipeline: GCS file arrival → Cloud Function chunker → PubSub → Camel consumers → Protobuf → Aerospike
- NO Kafka at InMarket — messaging was GCP PubSub + Apache Camel
- Built Go acceptance testing framework (learned Go for this), caught critical serialization bug
- Reduced Datadog costs by $8K/month through configurable tag filtering

### BNP Paribas (fintech, 2021-2023) — Tech: Java, Spring Boot, Axon Framework, Oracle, ActiveMQ
- 89-96% test coverage (company record), <5 production bugs in first year
- Pioneered Event Modeling, implemented CQRS with Axon Framework

### Vivere Brasil (2017-2019) — Tech: Java, Kafka
- Kafka DLQ system eliminated message loss (5/week to 0)

### Unicred (fintech, 2024-2025) — Tech: Java, Spring Boot, Kafka, SQL Server
- API response from 100ms-5s to sub-150ms via parallel data consolidation

### Randstad/BV (banking, 2016) — Tech: Java, Azure
- Contributed to first Brazilian bank on public cloud (Azure)

## AI Infrastructure Projects
- MCP Bridge Server: Python/FastMCP server exposing Ollama models as Claude Code tools
- Persona System: 35+ specialized configs from 13 base models, registry-driven
- Benchmark Framework: multi-language validation (Go, Python, Shell, HTML/JS, Java)
- Expense Classifier: Go CLI with hybrid pattern-rules + LLM classification, 190+ tests
- Web Research Tool: local-model-powered extraction with DDD agent architecture
- Overlay System: portable scaffolding packages for cross-repo consistency
- Verdict Protocol: ACCEPTED/IMPROVED/REJECTED labels create DPO training data passively

## Scale and Scope
- 16+ years professional experience, 50+ AI-assisted development sessions
- 143 commits across 3 AI repositories
- 35+ model personas from 13 base models
- 190+ unit tests in the Go expense classifier
- 10-layer architectural plan — 5 layers complete, 5 planned

## What This Person Can Speak Deeply About
Professional: high-throughput pipelines (Aerospike, Kafka), event-driven architecture \
(CQRS, Event Sourcing, Axon, Event Modeling), Java ecosystem (Spring Boot, Cloud, \
Camel), cloud platforms (GCP, AWS), quality culture (TDD, mentoring), DDD.
AI: running LLMs on consumer hardware, frontier/local collaboration via MCP, persona \
engineering, QLoRA trade-offs, DPO data collection, prompt decomposition, benchmarking.

## What Would Require the Person Directly
- Team-scale AI workflow design (AI work is individual)
- Fine-tuning execution (planned, not yet implemented)
- Frontend development (backend-focused career)
"""

SYSTEM_PROMPT = _PREAMBLE + _HF_RULES + _PROFILE
CLAUDE_SYSTEM_PROMPT = _PREAMBLE + _CLAUDE_RULES + _PROFILE

EXAMPLES = [
    ["Tell me about the LLM projects he's working on"],
    ["What local AI infrastructure has Leandro built, and why?"],
    ["How does Leandro decide when to use a local model vs. a frontier model?"],
    ["What surprised him most about running LLMs on consumer hardware?"],
    ["How does his backend background inform his AI infrastructure work?"],
    ["Tell me about the Aerospike pipeline at InMarket"],
    ["What's the DDD connection to agent architecture?"],
    ["What LLM techniques and tools does Leandro work with?"],
]


def respond_hf(message: str, history: list[dict]) -> str:
    """Stream response from HF Inference API."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = ""
    try:
        for chunk in hf_client.chat_completion(
            messages=messages,
            max_tokens=512,
            temperature=0.7,
            stream=True,
        ):
            if not chunk.choices:
                continue
            token = chunk.choices[0].delta.content or ""
            response += token
            yield response
    except Exception as e:
        if response:
            yield response + f"\n\n*[Response interrupted: {type(e).__name__}]*"
        else:
            yield f"Sorry, the model is temporarily unavailable. Error: {type(e).__name__}. Please try again."



def respond_claude(message: str, history: list[dict]) -> str:
    """Stream response from Claude API."""
    if not claude_client:
        yield "Claude backend is not configured."
        return

    # Simple session ID from first message in history
    session_id = str(hash(str(history[:1])))
    if _rate_limited(session_id):
        yield ("Rate limit reached for Claude backend. "
               "Please try again later, or switch to the open-source model.")
        return
    _claude_usage[session_id].append(time.time())

    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    messages.append({"role": "user", "content": message})

    response = ""
    try:
        with claude_client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            temperature=0.7,
            system=CLAUDE_SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                response += text
                yield response
    except Exception as e:
        if response:
            yield response + f"\n\n*[Response interrupted: {type(e).__name__}]*"
        else:
            yield f"Claude API error: {type(e).__name__}. Try the open-source model."


def respond(message: str, history: list[dict], backend: str = "") -> str:
    """Route to the selected backend."""
    if backend == "Claude (Haiku)" and claude_client:
        yield from respond_claude(message, history)
    else:
        yield from respond_hf(message, history)


PROFILE_PATH = os.path.join(os.path.dirname(__file__), "engineer-profile.md")
PORTFOLIO_PATH = os.path.join(os.path.dirname(__file__), "portfolio.md")


def read_file(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return "*File not available.*"


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (---...---) for rendering."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].lstrip()
    return text


with gr.Blocks(title="Leandro R. — Engineer Profile") as demo:
    gr.Markdown("# Leandro R. — Engineer Profile")
    gr.Markdown(
        "Senior backend engineer (16+ years, Java) · Local AI infrastructure builder · "
        "[GitHub](https://github.com/leandror172)"
    )

    with gr.Tabs():
        with gr.TabItem("Chat"):
            gr.Markdown(
                "Ask me about Leandro's engineering background, projects, and technical approach. "
                "For a deeper conversation, download/copy the profile and portfolio docs from the tabs above, and add it to Claude, ChatGPT, "
                "or your preferred tool."
            )

            backend_choices = ["Open-source (Qwen 72B)"]
            if claude_client:
                backend_choices.append("Claude (Haiku)")

            backend = gr.Radio(
                choices=backend_choices,
                value=backend_choices[0],
                label="Model",
                visible=len(backend_choices) > 1,
            )

            chat = gr.ChatInterface(
                fn=respond,
                additional_inputs=[backend],
                examples=EXAMPLES,
            )

        with gr.TabItem("Profile"):
            gr.Markdown("### AI-Readable Engineer Profile")
            gr.Markdown(
                "This document is designed to be fed to an AI model for a richer, "
                "more nuanced conversation about Leandro's background."
            )
            profile_content = read_file(PROFILE_PATH)
            with gr.Row():
                gr.File(
                    value=PROFILE_PATH if os.path.exists(PROFILE_PATH) else None,
                    label="Download",
                )
            gr.Markdown(
                strip_frontmatter(profile_content),
                buttons=["copy"],
            )

        with gr.TabItem("Portfolio"):
            gr.Markdown("### Project Portfolio")
            gr.Markdown(
                "Detailed overview of three interconnected repositories: "
                "AI platform, expense classifier, and web research tool."
            )
            portfolio_content = read_file(PORTFOLIO_PATH)
            with gr.Row():
                gr.File(
                    value=PORTFOLIO_PATH if os.path.exists(PORTFOLIO_PATH) else None,
                    label="Download",
                )
            gr.Markdown(
                portfolio_content,
                buttons=["copy"],
            )

if __name__ == "__main__":
    print("Launching Gradio app...")
    demo.launch()
