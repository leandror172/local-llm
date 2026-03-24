"""
Leandro R. — AI-Powered Engineer Profile
A chatbot that can discuss Leandro's engineering background, skills, and projects.
Powered by HF Inference API.
"""

import os

import gradio as gr
from huggingface_hub import InferenceClient

MODEL_ID = os.environ.get("MODEL_ID", "Qwen/Qwen2.5-72B-Instruct")
token = os.environ.get("HF_TOKEN") or None
client = InferenceClient(model=MODEL_ID, token=token)

SYSTEM_PROMPT = """\
You are an AI assistant that discusses the engineering profile of Leandro R., \
a senior backend engineer with 16+ years of experience. Answer questions about \
his skills, projects, and approach grounded ONLY in the profile data below.

RULES:
- ONLY state facts that appear in this profile. Do NOT invent details, \
challenges, solutions, or achievements not listed here.
- If asked about something not covered, say "That's not covered in the profile \
I have — you'd need to ask Leandro directly."
- Keep answers concise: 2-4 paragraphs max. Do not pad with generic filler.
- Use concrete numbers and specifics from the profile when available.
- Do NOT mix technologies between companies. Each role has its own tech stack listed.

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

EXAMPLES = [
    "What local AI infrastructure has Leandro built, and why?",
    "How do you decide when to use a local model vs. a frontier model?",
    "What surprised you most about running LLMs on consumer hardware?",
    "How does your backend background inform your AI infrastructure work?",
    "Tell me about the Aerospike pipeline at InMarket",
    "What's the DDD connection to agent architecture?",
]


def respond(message: str, history: list[dict]) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = ""
    try:
        for chunk in client.chat_completion(
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


demo = gr.ChatInterface(
    fn=respond,
    title="Leandro R. — Engineer Profile",
    description=(
        "Ask me about Leandro's engineering background, projects, and technical approach. "
        "I have context about his 16+ years in Java backend systems and his current "
        "local AI infrastructure work."
    ),
    examples=EXAMPLES,
)

if __name__ == "__main__":
    demo.launch()
