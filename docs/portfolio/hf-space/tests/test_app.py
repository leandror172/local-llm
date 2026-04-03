"""
Unit tests for Phase 2 routing logic in app.py.

Covers:
- _build_section_index()  — markdown parsing
- _format_routing_index() — index formatting
- _enrich_prompt()        — context injection
- _route_sections()       — routing call + JSON parse + graceful degradation
- _retry_after()          — rate limit wait time parsing
- _with_retry()           — retry wrapper behaviour
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

    def test_capped_at_three(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections * 5):  # 20 sections
            with patch.object(app, "hf_client") as mock_client:
                indices = list(range(10))
                mock_client.chat_completion.return_value = self._mock_response(json.dumps(indices))
                result = app._route_sections("question")
        assert len(result) == 3

    def test_exception_returns_empty(self):
        sections = app._build_section_index(FIXTURES)
        with patch.object(app, "_SECTION_INDEX", sections):
            with patch.object(app, "hf_client") as mock_client:
                mock_client.chat_completion.side_effect = RuntimeError("network error")
                result = app._route_sections("question")
        assert result == []


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_hf_exc(status_code: int, code: str = "", message: str = "") -> Exception:
    """Build a mock HfHubHTTPError using Groq's real nested error format."""
    exc = Exception(str(status_code))
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"error": {"code": code, "message": message, "type": ""}}
    exc.response = resp
    return exc


# ── _retry_after ──────────────────────────────────────────────────────────────

class TestRetryAfter:
    def test_no_response(self):
        assert app._retry_after(Exception("test")) is None

    def test_429_rate_limit_with_time(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "try again in 9.67s")
        assert app._retry_after(exc) == pytest.approx(10.67)

    def test_429_rate_limit_over_60s(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "try again in 47m49.344s")
        assert app._retry_after(exc) is None

    def test_429_rate_limit_no_time(self):
        assert app._retry_after(_make_hf_exc(429, "rate_limit_exceeded", "no time here")) is None

    def test_429_other_code(self):
        assert app._retry_after(_make_hf_exc(429, "other_error")) is None

    def test_500_rate_limit(self):
        assert app._retry_after(_make_hf_exc(500, "rate_limit_exceeded")) is None

    def test_exactly_60s(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "try again in 1m0.0s")
        assert app._retry_after(exc) == pytest.approx(61.0)

    def test_61s(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "try again in 1m1.0s")
        assert app._retry_after(exc) is None


# ── _with_retry ───────────────────────────────────────────────────────────────

class TestWithRetry:
    def test_fn_succeeds_first_try(self):
        fn = MagicMock(return_value="success")
        with patch("time.sleep") as mock_sleep:
            result = app._with_retry(fn)
        assert result == "success"
        assert fn.call_count == 1
        mock_sleep.assert_not_called()

    def test_fn_raises_rate_limit_then_succeeds(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "try again in 2.0s")
        fn = MagicMock(side_effect=[exc, "success"])
        with patch("time.sleep") as mock_sleep:
            result = app._with_retry(fn)
        assert result == "success"
        assert fn.call_count == 2
        mock_sleep.assert_called_once_with(pytest.approx(3.0))

    def test_fn_raises_rate_limit_twice(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "try again in 2.0s")
        fn = MagicMock(side_effect=[exc, exc])
        with patch("time.sleep"):
            with pytest.raises(Exception):
                app._with_retry(fn)
        assert fn.call_count == 2

    def test_fn_raises_non_retriable_error(self):
        fn = MagicMock(side_effect=ValueError("bad input"))
        with patch("time.sleep") as mock_sleep:
            with pytest.raises(ValueError):
                app._with_retry(fn)
        assert fn.call_count == 1
        mock_sleep.assert_not_called()


# ── _classify_error ───────────────────────────────────────────────────────────

class TestParseHfError:
    def test_groq_nested_error_format(self):
        """Groq wraps errors under an 'error' key (OpenAI format)."""
        exc = Exception("429")
        resp = MagicMock()
        resp.status_code = 429
        resp.json.return_value = {
            "error": {
                "message": ("Rate limit reached for model `llama-3.3-70b-versatile`"
                            " in organization `org_01k...`. Please try again in 1h59m7.008s."
                            " Need more tokens?"),
                "type": "tokens",
                "code": "rate_limit_exceeded",
            }
        }
        exc.response = resp
        status, code, message = app._parse_hf_error(exc)
        assert status == 429
        assert code == "rate_limit_exceeded"
        assert "1h59m7.008s" in message

    def test_classify_groq_hourly_limit(self):
        """End-to-end: Groq nested format → correct user message with wait time."""
        exc = Exception("429")
        resp = MagicMock()
        resp.status_code = 429
        resp.json.return_value = {
            "error": {
                "message": "Please try again in 1h59m7.008s.",
                "type": "tokens",
                "code": "rate_limit_exceeded",
            }
        }
        exc.response = resp
        msg = app._classify_error(exc)
        assert "about 2 hours" in msg  # ceil(7147s / 60) = 120min = 2h
        assert "Haiku" in msg


class TestClassifyError:
    def test_daily_quota_includes_wait_time(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "try again in 47m49.344s")
        msg = app._classify_error(exc)
        assert "48 minutes" in msg  # ceil(47m49s) = 48 min
        assert "Haiku" in msg

    def test_short_rate_limit(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "try again in 9.67s")
        msg = app._classify_error(exc)
        assert "few minutes" in msg
        assert "Haiku" in msg

    def test_no_time_rate_limit(self):
        exc = _make_hf_exc(429, "rate_limit_exceeded", "no time here")
        msg = app._classify_error(exc)
        assert "few minutes" in msg
        assert "Haiku" in msg

    def test_401(self):
        assert "Authentication" in app._classify_error(_make_hf_exc(401))

    def test_413(self):
        assert "too long" in app._classify_error(_make_hf_exc(413))

    def test_500(self):
        assert "temporarily down" in app._classify_error(_make_hf_exc(500))

    def test_503(self):
        assert "temporarily down" in app._classify_error(_make_hf_exc(503))

    def test_no_response(self):
        assert "temporarily unavailable" in app._classify_error(Exception("test"))

    def test_unknown_status(self):
        assert "temporarily unavailable" in app._classify_error(_make_hf_exc(418))
