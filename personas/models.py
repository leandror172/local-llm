#!/usr/bin/env python3
"""
models.py — Centralized model selection and configuration.

Extracted from create-persona.py (Task 3.4 refactoring).
Provides a single source of truth for:
  - Domain → (display_name, ollama_tag, num_ctx, default_temp_category)
  - Temperature metadata (value + description)
  - Model tag → filename suffix mappings

Used by:
  - personas/create-persona.py (interactive persona creator)
  - Future: personas/detect-persona.py (codebase analyzer for model hints)
  - Future: Task 3.5 conversational builder
"""

# ──────────────────────────────────────────────────────────────────────────────
# Model Selection Matrix (Task 3.3)
# Each entry: (display_name, ollama_tag, num_ctx, default_temp_category)
# ──────────────────────────────────────────────────────────────────────────────

MODEL_MATRIX = {
    "code":           ("Qwen3-8B",              "qwen3:8b",                     16384, "quality"),
    "reasoning":      ("Qwen3-14B",             "qwen3:14b",                     4096, "quality"),
    "classification": ("Qwen3-4B",              "qwen3:4b-q8_0",                 4096, "correctness"),
    "writing":        ("Llama-3.1-8B",          "llama3.1:8b-instruct-q5_K_M", 16384, "quality"),
    "translation":    ("Qwen3-8B",              "qwen3:8b",                     16384, "quality"),
    "other":          ("Qwen3-8B",              "qwen3:8b",                     16384, "quality"),
}

DOMAIN_CHOICES = ["code", "reasoning", "classification", "writing", "translation", "other"]


def get_model(domain: str) -> tuple:
    """
    Get model recommendation for a domain.

    Args:
        domain: One of DOMAIN_CHOICES

    Returns:
        Tuple of (display_name, ollama_tag, num_ctx, default_temp_category)
    """
    if domain not in MODEL_MATRIX:
        domain = "other"  # Fallback
    return MODEL_MATRIX[domain]


# ──────────────────────────────────────────────────────────────────────────────
# Temperature Configuration (Consolidated in Task 3.4 refactoring)
# Single source of truth for all temperature metadata
# ──────────────────────────────────────────────────────────────────────────────

TEMPERATURES = {
    "deterministic": {
        "value": 0.1,
        "description": "0.1 — same input → same output (classifier, codegen)",
        "use_case": "correctness: classifier, codegen",
    },
    "balanced": {
        "value": 0.3,
        "description": "0.3 — accurate with mild variation (coder, translator)",
        "use_case": "quality: coder, translator, summarizer",
    },
    "creative": {
        "value": 0.7,
        "description": "0.7 — diverse phrasing (writer, brainstormer)",
        "use_case": "creativity: writer, brainstormer",
    },
}

# Mapping: default_temp_category (from MODEL_MATRIX) → temperature name
TEMP_CATEGORY_TO_CHOICE = {
    "correctness": "deterministic",
    "quality": "balanced",
    "creativity": "creative",
}

# Mapping: temperature name → float value (for backward compatibility)
TEMPERATURE_MAP = {name: data["value"] for name, data in TEMPERATURES.items()}

# Mapping: temperature value → description (for backward compatibility)
TEMP_DESCRIPTIONS = {name: data["description"] for name, data in TEMPERATURES.items()}


def get_temperature_value(name: str) -> float:
    """Get temperature float value by name."""
    return TEMPERATURES.get(name, TEMPERATURES["balanced"])["value"]


def get_temperature_description(name: str) -> str:
    """Get human-readable temperature description by name."""
    return TEMPERATURES.get(name, TEMPERATURES["balanced"])["description"]


# ──────────────────────────────────────────────────────────────────────────────
# Model Tag Mappings
# ──────────────────────────────────────────────────────────────────────────────

# Model-tag → Modelfile filename suffix
MODEL_TAG_TO_SUFFIX = {
    "qwen3:8b": "qwen3",
    "qwen3:14b": "qwen3",
    "qwen3:4b-q8_0": "qwen3",
    "qwen2.5-coder:7b": "qwen25",
    "llama3.1:8b-instruct-q5_K_M": "llama31",
}

# Model-tag → persona name q-suffix (appended to "my-<slug>")
MODEL_TAG_TO_Q_SUFFIX = {
    "qwen3:8b": "-q3",
    "qwen3:14b": "-q3",
    "qwen3:4b-q8_0": "-q3",
    "qwen2.5-coder:7b": "",
    "llama3.1:8b-instruct-q5_K_M": "",
}


def get_modelfile_suffix(model_tag: str) -> str:
    """Get Modelfile filename suffix for a model tag."""
    return MODEL_TAG_TO_SUFFIX.get(model_tag, "custom")


def get_persona_name_suffix(model_tag: str) -> str:
    """Get persona name q-suffix for a model tag (appended to 'my-<slug>')."""
    return MODEL_TAG_TO_Q_SUFFIX.get(model_tag, "")


if __name__ == "__main__":
    # Quick verification
    print("Available domains:", DOMAIN_CHOICES)
    print("Available temperatures:", list(TEMPERATURES.keys()))
    print("\nExample: code domain →", get_model("code"))
    print("Example: balanced temp →", get_temperature_value("balanced"))
