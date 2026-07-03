"""
Tests for retrieval/relate.py — T4 prose synthesis (mocked ModelClient, no Ollama).

Covers:
- render_summary_facts: flatten the structured relation dict into string slots.
- build_summary_prompt: template loads and ALL named slots resolve (both nearest_miss
  shapes: None for strong/moderate, populated for weak/unrelated).
- synthesize_summary: contract with a mocked client — builds prompt, calls
  client.relate_summary, returns stripped content; summary is added in relate(), never
  in build_relation.
- The SHIPPED relate_summary.txt pins the load-bearing carry-forward wording (P5-D3):
  nearest_miss is "no stored edge" / "closest topic pair", never "sub-threshold";
  a bare cross-reference must be flagged as not-strong.
"""

import string
from pathlib import Path
from types import SimpleNamespace

import pytest

from relate import (
    load_summary_template,
    render_summary_facts,
    build_summary_prompt,
    synthesize_summary,
    SUMMARY_PROMPT_PATH,
)

THRESHOLDS = {
    "tau_floor": 0.70,
    "merge_cosine": 0.85,
    "weak_floor": 0.55,
    "bands": {"strong": "...", "moderate": "...", "weak": "...", "unrelated": "..."},
}


def _positive_relation():
    """Strong verdict shape: cross edges present, nearest_miss is None."""
    return {
        "inputs": {"file_a": "docs/a.md", "file_b": "docs/b.md", "nodes_a": 4, "nodes_b": 5},
        "verdict": "strong",
        "thresholds": THRESHOLDS,
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
    }


def _negative_relation():
    """Unrelated verdict shape (first-class): zero edge_stats, disjoint communities,
    populated nearest_miss."""
    return {
        "inputs": {"file_a": "docs/a.md", "file_b": "docs/c.md", "nodes_a": 3, "nodes_b": 6},
        "verdict": "unrelated",
        "thresholds": THRESHOLDS,
        "shared_anchors": [],
        "community_overlap": {
            "coarse": {"shared": [], "jaccard": 0.0},
            "fine": {"shared": [], "jaccard": 0.0},
        },
        "top_edges": [],
        "edge_stats": {"similarity": 0, "same_as": 0, "references": 0,
                       "max_weight": 0.0, "mean_weight": 0.0},
        "provenance": {"a": {"docs-research": 3}, "b": {"archive": 6}},
        "nearest_miss": {"node_a": "a2", "node_b": "c4", "cosine": 0.41},
    }


# --- template + slot resolution -----------------------------------------------

def test_summary_template_loads_from_shipped_file():
    template = load_summary_template()
    assert isinstance(template, str)
    assert "{verdict}" in template


def test_render_summary_facts_covers_every_template_slot():
    template = load_summary_template()
    slots = {name for _, name, _, _ in string.Formatter().parse(template) if name}
    facts = render_summary_facts(_positive_relation())
    missing = slots - set(facts)
    assert missing == set(), f"unresolved template slots: {missing}"


def test_build_summary_prompt_resolves_positive_case():
    # real .format() call catches any stray literal brace the template author left in.
    prompt = build_summary_prompt(_positive_relation())
    assert "docs/a.md" in prompt
    assert "docs/b.md" in prompt
    assert "strong" in prompt


def test_build_summary_prompt_resolves_negative_case_with_populated_nearest_miss():
    prompt = build_summary_prompt(_negative_relation())
    assert "unrelated" in prompt
    # populated nearest_miss must surface node ids + cosine, described as no-stored-edge
    assert "a2" in prompt and "c4" in prompt
    assert "0.41" in prompt


def test_build_summary_prompt_handles_none_nearest_miss():
    facts = render_summary_facts(_positive_relation())
    # nearest_miss None renders to a non-empty, non-crashing string slot
    assert isinstance(facts["nearest_miss"], str)
    assert facts["nearest_miss"] != ""


# --- synthesize_summary contract (mocked client) ------------------------------

class _MockClient:
    def __init__(self, content):
        self._content = content
        self.calls = []

    def relate_summary(self, prompt):
        self.calls.append(prompt)
        return SimpleNamespace(content=self._content)


def test_synthesize_summary_calls_client_and_strips_content():
    client = _MockClient("  These two documents are strongly related.\n")
    relation = _positive_relation()
    summary = synthesize_summary(relation, client)
    assert summary == "These two documents are strongly related."
    # the client received a prompt built from the structured data
    assert len(client.calls) == 1
    assert "docs/a.md" in client.calls[0]
    assert "strong" in client.calls[0]


def test_synthesize_summary_does_not_mutate_the_relation_dict():
    client = _MockClient("summary text")
    relation = _positive_relation()
    synthesize_summary(relation, client)
    # seam contract: build_relation stays summary-free; synthesize returns the string,
    # the caller (relate) decides where to attach it.
    assert "summary" not in relation


# --- shipped-prompt wording pins (load-bearing carry-forward, P5-D3) ----------

def test_shipped_prompt_never_uses_threshold_language_for_nearest_miss():
    text = SUMMARY_PROMPT_PATH.read_text(encoding="utf-8").lower()
    assert "sub-threshold" not in text
    assert "below threshold" not in text
    assert "below the cutoff" not in text


def test_shipped_prompt_uses_no_stored_edge_phrasing():
    text = SUMMARY_PROMPT_PATH.read_text(encoding="utf-8").lower()
    assert "no stored edge" in text
    assert "closest topic pair" in text


def test_shipped_prompt_cautions_against_over_reading_a_bare_reference():
    text = SUMMARY_PROMPT_PATH.read_text(encoding="utf-8").lower()
    # constraint (b): a lone references edge does not imply strong relation
    assert "references" in text


def test_shipped_prompt_makes_structured_data_the_source_of_truth():
    text = SUMMARY_PROMPT_PATH.read_text(encoding="utf-8").lower()
    assert "source of truth" in text


# --- config role wiring (catches a relate_summary role typo before T6's live run) ---

def test_relate_summary_role_resolves_in_shipped_config():
    from model_client import load_config
    from relate import DEFAULT_CONFIG

    config = load_config(DEFAULT_CONFIG)
    assert "relate_summary" in config, "config.yaml roles: must define relate_summary (P5-D5)"
    role = config["relate_summary"]
    # think:false is a top-level payload key (Ollama ignores it inside options{})
    assert role.get("think") is False
    assert role["model"] == "qwen3:14b"
