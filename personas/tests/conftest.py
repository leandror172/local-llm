"""Pytest configuration — insert personas/ onto sys.path for all tests."""
import sys
from pathlib import Path

# Add personas/ directory so `import models` and `from lib.interactive import ...` work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
