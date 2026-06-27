"""
Integration tests for create-persona.py collect_from_flags + argparse.

Loads the hyphenated module via importlib (it can't be imported with 'import').
All tests drive parse_args() + collect_from_flags() directly — no Ollama needed.

Expected RED on two tests before implementation:
  - test_numeric_temperature_accepted: argparse choices= rejects '0.5' → SystemExit(2)
  - test_out_of_range_temperature_exits: argparse error says 'invalid choice', not 'range'
"""
import importlib.util
import sys
from pathlib import Path

import pytest

PERSONAS_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cp():
    """Load create-persona.py as module 'create_persona'."""
    path = PERSONAS_DIR / "create-persona.py"
    spec = importlib.util.spec_from_file_location("create_persona", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_and_collect(cp, monkeypatch, argv: list[str]) -> dict:
    """Run parse_args + collect_from_flags with a patched sys.argv."""
    monkeypatch.setattr(sys, "argv", ["prog"] + argv)
    args = cp.parse_args()
    return cp.collect_from_flags(args)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_numeric_temperature_accepted(cp, monkeypatch):
    """--temperature 0.5 must produce temperature == 0.5 (RED until choices= removed)."""
    config = _parse_and_collect(
        cp, monkeypatch,
        ["--non-interactive", "--role", "x", "--temperature", "0.5"],
    )
    assert config["temperature"] == pytest.approx(0.5)


def test_out_of_range_temperature_exits(cp, monkeypatch, capsys):
    """--temperature 3 must exit 2 with a message mentioning the valid range."""
    monkeypatch.setattr(sys, "argv", ["prog", "--non-interactive", "--role", "x", "--temperature", "3"])
    with pytest.raises(SystemExit) as exc_info:
        args = cp.parse_args()
        cp.collect_from_flags(args)
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    # Our validation message must mention "range" or the bounds (not just "invalid choice")
    combined = captured.err + captured.out
    assert "range" in combined.lower() or "2.0" in combined or "[0" in combined


def test_named_temperature_regression(cp, monkeypatch):
    """--temperature deterministic must still resolve to 0.1 (regression guard)."""
    config = _parse_and_collect(
        cp, monkeypatch,
        ["--non-interactive", "--role", "x", "--temperature", "deterministic"],
    )
    assert config["temperature"] == pytest.approx(0.1)


def test_no_temperature_flag_uses_domain_default(cp, monkeypatch):
    """When --temperature is omitted, domain default applies (code → balanced → 0.3)."""
    config = _parse_and_collect(
        cp, monkeypatch,
        ["--non-interactive", "--role", "x", "--domain", "code"],
    )
    assert config["temperature"] == pytest.approx(0.3)


def test_generate_modelfile_numeric_temperature(cp):
    """generate_modelfile with temperature=0.5 must produce 'PARAMETER temperature 0.5'."""
    content = cp.generate_modelfile(
        base_tag="qwen3:8b",
        num_ctx=32768,
        temperature=0.5,
        role="test persona",
        constraints=["MUST do something"],
        output_format="plain text",
        tier="full",
    )
    assert "PARAMETER temperature 0.5" in content
