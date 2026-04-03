"""
Unit tests for Phase 2 routing logic in app.py.

Covers:
- _build_section_index()  — markdown parsing
- _format_routing_index() — index formatting
- _enrich_prompt()        — context injection
- _route_sections()       — routing call + JSON parse + graceful degradation
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest

# conftest.py patches huggingface_hub/gradio/anthropic before this import
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import app  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "context")


# ── _build_section_index ──────────────────────────────────────────────────────

class TestBuildSectionIndex:
    def test_section_count(self):
        sections = app._build_section_index(FIXTURES)
        # 2 sections in alpha, 2 in beta = 4 total
        assert len(sections) == 4

    def test_file_header_skipped(self):
        sections = app._build_section_index(FIXTURES)
        headings = [s.heading for s in sections]
        assert not any("Semantic Memory" in h for h in headings)
        assert not any("Knowledge" in h and "/" not in h for h in headings)

    def test_source_is_filename_without_extension(self):
        sections = app._build_section_index(FIXTURES)
        sources = {s.source for s in sections}
        assert sources == {"alpha-knowledge", "beta-knowledge"}

    def test_key_format(self):
        sections = app._build_section_index(FIXTURES)
        for s in sections:
            assert s.key == f"{s.source}:{s.heading}"

    def test_heading_extracted_correctly(self):
        sections = app._build_section_index(FIXTURES)
        alpha_headings = [s.heading for s in sections if s.source == "alpha-knowledge"]
        assert "Section One (2026-01)" in alpha_headings
        assert "Section Two (2026-02)" in alpha_headings

    def test_snippet_uses_first_two_body_lines(self):
        sections = app._build_section_index(FIXTURES)
        s1 = next(s for s in sections if s.heading == "Section One (2026-01)")
        # First two non-empty body lines joined
        assert "Body line one." in s1.snippet
        assert "Body line two." in s1.snippet
        # Third line must not appear (only 2 lines in snippet)
        assert "Body line three." not in s1.snippet

    def test_snippet_capped_at_200_chars(self):
        sections = app._build_section_index(FIXTURES)
        for s in sections:
            assert len(s.snippet) <= 200

    def test_content_includes_heading_line(self):
        sections = app._build_section_index(FIXTURES)
        s1 = next(s for s in sections if s.heading == "Section One (2026-01)")
        assert s1.content.startswith("## Section One (2026-01)")

    def test_missing_directory_returns_empty(self):
        sections = app._build_section_index("/nonexistent/path/xyz")
        assert sections == []

    def test_sorted_by_filename(self):
        sections = app._build_section_index(FIXTURES)
        # alpha-knowledge sections come before beta-knowledge sections
        sources = [s.source for s in sections]
        assert sources.index("alpha-knowledge") < sources.index("beta-knowledge")


# ── _format_routing_index ─────────────────────────────────────────────────────

class TestFormatRoutingIndex:
    def test_empty_index(self):
        assert app._format_routing_index([]) == ""

    def test_format(self):
        sections = app._build_section_index(FIXTURES)
        result = app._format_routing_index(sections)
        lines = result.splitlines()
        assert len(lines) == len(sections)
        assert lines[0].startswith("[0]")
        assert "alpha-knowledge / Section One" in lines[0]

    def test_indices_are_sequential(self):
        sections = app._build_section_index(FIXTURES)
        result = app._format_routing_index(sections)
        for i, line in enumerate(result.splitlines()):
            assert line.startswith(f"[{i}]")


# ── _enrich_prompt ────────────────────────────────────────────────────────────

class TestEnrichPrompt:
    def test_empty_sections_returns_base_unchanged(self):
        base = "base prompt text"
        assert app._enrich_prompt(base, []) == base

    def test_single_section_appended(self):
        sections = app._build_section_index(FIXTURES)
        result = app._enrich_prompt("BASE", [sections[0]])
        assert "BASE" in result
        assert "## Retrieved Knowledge Sections" in result
        assert sections[0].heading in result
        assert sections[0].source in result

    def test_multiple_sections_all_present(self):
        sections = app._build_section_index(FIXTURES)
        result = app._enrich_prompt("BASE", sections[:3])
        for s in sections[:3]:
            assert s.heading in result

    def test_base_prompt_prefix_preserved(self):
        sections = app._build_section_index(FIXTURES)
        base = "IDENTITY AND RULES"
        result = app._enrich_prompt(base, sections[:1])
        assert result.startswith(base)


# ── _route_sections ───────────────────────────────────────────────────────────

class TestRouteSections:
    def _mock_response(self, content: str) -> MagicMock:
        """Build a fake hf_client.chat_completion response."""
        msg = MagicMock()
        msg.content = content
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    def test_empty_index_returns_empty(self):
        with patch.object(app, "_SECTION_INDEX", []):
            result = app._route_sections("anything")
        assert result == []

    def test_valid_indices_returns_sections(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections):
            with patch.object(app, "hf_client") as mock_client:
                mock_client.chat_completion.return_value = self._mock_response("[0, 2]")
                result = app._route_sections("tell me about section one")
        assert result == [sections[0], sections[2]]

    def test_invalid_json_returns_empty(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections):
            with patch.object(app, "hf_client") as mock_client:
                mock_client.chat_completion.return_value = self._mock_response("not json at all")
                result = app._route_sections("question")
        assert result == []

    def test_non_list_json_returns_empty(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections):
            with patch.object(app, "hf_client") as mock_client:
                mock_client.chat_completion.return_value = self._mock_response('{"key": 0}')
                result = app._route_sections("question")
        assert result == []

    def test_out_of_range_indices_ignored(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections):
            with patch.object(app, "hf_client") as mock_client:
                mock_client.chat_completion.return_value = self._mock_response("[0, 999]")
                result = app._route_sections("question")
        assert len(result) == 1
        assert result[0] == sections[0]

    def test_non_int_indices_ignored(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections):
            with patch.object(app, "hf_client") as mock_client:
                mock_client.chat_completion.return_value = self._mock_response('[0, "two", 1]')
                result = app._route_sections("question")
        assert len(result) == 2

    def test_capped_at_six(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections * 5):  # 20 sections
            with patch.object(app, "hf_client") as mock_client:
                indices = list(range(10))
                mock_client.chat_completion.return_value = self._mock_response(json.dumps(indices))
                result = app._route_sections("question")
        assert len(result) == 6

    def test_exception_returns_empty(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections):
            with patch.object(app, "hf_client") as mock_client:
                mock_client.chat_completion.side_effect = RuntimeError("network error")
                result = app._route_sections("question")
        assert result == []
