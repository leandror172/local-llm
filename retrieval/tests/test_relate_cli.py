"""
Tests for retrieval/relate.py — T5 CLI + rendering (no live index, no Ollama).

Covers:
- build_parser: --a/--b required, --index/--json/--no-summary flags.
- render_human: readable rendering of the structured dict + summary.
- main: --json emits the full dict (including summary); default renders human text.
  relate() is monkeypatched so the CLI is exercised without a live index or model call.
"""

import json

import pytest

import relate as relate_mod
from relate import build_parser, render_human


def _relation(summary="These docs are strongly related."):
    return {
        "inputs": {"file_a": "docs/a.md", "file_b": "docs/b.md", "nodes_a": 4, "nodes_b": 5},
        "verdict": "strong",
        "thresholds": {"tau_floor": 0.70, "merge_cosine": 0.85, "weak_floor": 0.55, "bands": {}},
        "shared_anchors": [
            {"anchor_key": "ref:concept-x", "linked_from_a": ["a1"], "linked_from_b": ["b1"]},
        ],
        "community_overlap": {
            "coarse": {"shared": [1], "jaccard": 0.5},
            "fine": {"shared": [10], "jaccard": 0.33},
        },
        "top_edges": [
            {"node_a": "a1", "node_b": "b1", "edge_kind": "similarity", "weight": 0.91},
        ],
        "edge_stats": {"similarity": 1, "same_as": 0, "references": 0,
                       "max_weight": 0.91, "mean_weight": 0.91},
        "provenance": {"a": {"docs-research": 4}, "b": {"docs-ideas": 5}},
        "nearest_miss": None,
        "summary": summary,
    }


# --- argument parsing ---------------------------------------------------------

def test_parser_requires_a_and_b():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_reads_paths_and_flags():
    parser = build_parser()
    args = parser.parse_args(["--a", "docs/a.md", "--b", "docs/b.md", "--json"])
    assert args.a == "docs/a.md"
    assert args.b == "docs/b.md"
    assert args.json is True
    assert args.no_summary is False


def test_parser_no_summary_flag():
    parser = build_parser()
    args = parser.parse_args(["--a", "x", "--b", "y", "--no-summary"])
    assert args.no_summary is True


# --- human rendering ----------------------------------------------------------

def test_render_human_includes_verdict_files_and_summary():
    text = render_human(_relation())
    assert "docs/a.md" in text
    assert "docs/b.md" in text
    assert "strong" in text
    assert "These docs are strongly related." in text


def test_render_human_omits_summary_line_when_absent():
    relation = _relation()
    del relation["summary"]
    text = render_human(relation)  # must not raise when summary was suppressed
    assert "docs/a.md" in text


# --- main() end to end (relate() monkeypatched) -------------------------------

def test_main_json_emits_full_dict(monkeypatch, capsys):
    captured = {}

    def fake_relate(file_a, file_b, **kwargs):
        captured["args"] = (file_a, file_b, kwargs)
        return _relation()

    monkeypatch.setattr(relate_mod, "relate", fake_relate)
    relate_mod.main(["--a", "docs/a.md", "--b", "docs/b.md", "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["verdict"] == "strong"
    assert payload["summary"] == "These docs are strongly related."


def test_main_default_renders_human(monkeypatch, capsys):
    monkeypatch.setattr(relate_mod, "relate", lambda file_a, file_b, **kw: _relation())
    relate_mod.main(["--a", "docs/a.md", "--b", "docs/b.md"])
    out = capsys.readouterr().out
    assert "strong" in out
    assert "These docs are strongly related." in out
    # not JSON in the default path
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)


def test_main_no_summary_passes_with_summary_false(monkeypatch, capsys):
    captured = {}

    def fake_relate(file_a, file_b, **kwargs):
        captured["kwargs"] = kwargs
        r = _relation()
        del r["summary"]
        return r

    monkeypatch.setattr(relate_mod, "relate", fake_relate)
    relate_mod.main(["--a", "docs/a.md", "--b", "docs/b.md", "--no-summary"])
    assert captured["kwargs"].get("with_summary") is False
