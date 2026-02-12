"""Configuration for the Ollama MCP server.

All settings have sensible defaults and can be overridden via environment
variables. This module is imported by other modules — never import httpx
or mcp here to keep it dependency-free and fast to load.
"""

import os

# ---------------------------------------------------------------------------
# Ollama connection
# ---------------------------------------------------------------------------

# Base URL for the Ollama API. Override with OLLAMA_URL env var if Ollama
# runs on a different host/port (e.g., inside Docker on a custom port).
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# ---------------------------------------------------------------------------
# Model defaults
# ---------------------------------------------------------------------------

# The model to use when the caller doesn't specify one.
# "my-coder-q3" is a Qwen3-8B persona tuned for coding tasks.
DEFAULT_MODEL: str = os.environ.get("OLLAMA_MODEL", "my-coder-q3")

# ---------------------------------------------------------------------------
# Request defaults
# ---------------------------------------------------------------------------

# Maximum seconds to wait for an Ollama response. First requests are slower
# because Ollama loads the model into VRAM (cold start). 120s is generous
# enough to cover cold starts on a 12GB GPU.
DEFAULT_TIMEOUT: int = int(os.environ.get("OLLAMA_TIMEOUT", "120"))

# Qwen3 "thinking" mode. When True, the model spends extra tokens on
# internal chain-of-thought (invisible in output but counted in eval_count).
# Default False because it inflates latency 5-17x for marginal quality gains
# on simple tasks. Escalate to True for complex reasoning or retries.
DEFAULT_THINK: bool = os.environ.get("OLLAMA_THINK", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Temperature presets
# ---------------------------------------------------------------------------

# Temperature controls randomness: 0.0 = deterministic, 1.0 = very creative.
# These presets are used by specialized tools (Task 1.3). The general-purpose
# ask_ollama tool uses "general" by default.
TEMPS: dict[str, float] = {
    "code": 0.1,       # Precise, deterministic output for code generation
    "general": 0.3,    # Balanced — good for Q&A, explanations, analysis
    "creative": 0.7,   # More varied output for brainstorming, writing
}

# ---------------------------------------------------------------------------
# Available models (informational)
# ---------------------------------------------------------------------------

# These are the custom Ollama model personas configured on this system.
# Used in tool descriptions so Claude knows what models are available.
MODELS: list[str] = [
    "my-coder",             # Qwen2.5-Coder-7B — fast, good at code
    "my-coder-q3",          # Qwen3-8B — coding persona, thinking capable
    "my-creative-coder",    # Qwen2.5-Coder-7B — creative coding persona
    "my-creative-coder-q3", # Qwen3-8B — creative coding, thinking capable
]
