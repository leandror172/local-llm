"""
Patch heavy external dependencies before app.py is imported.
Gradio and HF Hub both execute top-level code on import that requires
network access or a GPU — mock them out for unit tests.
"""
import sys
from unittest.mock import MagicMock

# Patch before any test module imports app
for module in ("huggingface_hub", "gradio", "anthropic"):
    sys.modules.setdefault(module, MagicMock())
