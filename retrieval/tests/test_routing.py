"""
Tests for retrieval/routing.py

Covers:
- route(): code extensions map to "extraction_code"
- route(): all other extensions map to "extraction_prose"
- route(): case-insensitive extension matching
- CODE_EXTENSIONS: exported set contains the four supported code types
"""

import sys
from pathlib import Path

import pytest

RETRIEVAL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(RETRIEVAL_DIR))

import routing  # noqa: E402


# ---------------------------------------------------------------------------
# route() — code extensions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filepath", [
    "src/main.py",
    "lib/util.go",
    "app/component.ts",
    "src/Parser.java",
    "scripts/run.py",
    "pkg/service/handler.go",
])
def test_route_code_extensions_return_extraction_code(filepath):
    assert routing.route(filepath) == "extraction_code"


# ---------------------------------------------------------------------------
# route() — prose extensions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filepath", [
    "docs/design.md",
    ".memories/QUICK.md",
    "notes.txt",
    "README.rst",
    ".claude/plan-v2.md",
    "personas/persona-template.md",
])
def test_route_prose_extensions_return_extraction_prose(filepath):
    assert routing.route(filepath) == "extraction_prose"


# ---------------------------------------------------------------------------
# route() — case insensitivity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filepath,expected", [
    ("src/Main.PY",   "extraction_code"),
    ("lib/Util.GO",   "extraction_code"),
    ("App.TS",        "extraction_code"),
    ("Readme.MD",     "extraction_prose"),
])
def test_route_is_case_insensitive(filepath, expected):
    assert routing.route(filepath) == expected


# ---------------------------------------------------------------------------
# route() — no extension
# ---------------------------------------------------------------------------

def test_route_no_extension_returns_extraction_prose():
    assert routing.route("Makefile") == "extraction_prose"


def test_route_hidden_file_no_extension_returns_extraction_prose():
    assert routing.route(".gitignore") == "extraction_prose"


# ---------------------------------------------------------------------------
# CODE_EXTENSIONS — exported set
# ---------------------------------------------------------------------------

def test_code_extensions_contains_python():
    assert ".py" in routing.CODE_EXTENSIONS


def test_code_extensions_contains_go():
    assert ".go" in routing.CODE_EXTENSIONS


def test_code_extensions_contains_typescript():
    assert ".ts" in routing.CODE_EXTENSIONS


def test_code_extensions_contains_java():
    assert ".java" in routing.CODE_EXTENSIONS


def test_code_extensions_is_lowercase():
    for ext in routing.CODE_EXTENSIONS:
        assert ext == ext.lower(), f"Extension {ext!r} must be lowercase"
