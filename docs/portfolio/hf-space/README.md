---
title: Leandro R. — Engineer Profile
emoji: 💬
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.9.0
app_file: app.py
pinned: false
thumbnail: https://huggingface.co/spaces/leandror777/engineer-profile/resolve/main/leandro-profile-banner.png
license: mit
---

# Engineer Profile Chatbot

An AI-powered chatbot that can discuss Leandro R.'s engineering background,
skills, and projects. Supports two backends: HF Inference API (free, Llama 3.3 70B
via Groq) and Claude API (Haiku, rate-limited).

The chatbot loads cross-project context from `.memories/` files synced across 3
repositories (LLM platform, expense classifier, web research tool), giving it
awareness of all active projects, architecture decisions, and tooling.

## Setup

Set the `HF_TOKEN` secret in your Space settings.

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_TOKEN` | (required) | HF Inference API authentication |
| `MODEL_ID` | `meta-llama/Llama-3.3-70B-Instruct` | HF model |
| `HF_PROVIDER` | `groq` | Inference provider |
| `ANTHROPIC_API_KEY` | (optional) | Enables Claude backend |
| `CLAUDE_MODEL` | `claude-haiku-4-5` | Claude model |
| `CLAUDE_MAX_PER_HOUR` | `30` | Per-session rate limit |

## Context Sync

Before uploading, run `sync-context.sh` to copy `.memories/` and README files
from all 3 repos into `context/`. The app loads `*-quick.md` files at startup
as always-available project context (~5K tokens).
