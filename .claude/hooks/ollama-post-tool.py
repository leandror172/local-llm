#!/usr/bin/env python3
"""ollama-post-tool.py — PostToolUse hook for mcp__ollama-bridge__* calls.

Fires after every ollama-bridge tool call. Reads the most recent call
record from calls.jsonl to get the prompt_hash, then injects a compact
verdict template into Claude's context via additionalContext.

Claude fills the template inline in its response. The Stop hook
(verdict-capture.py) later scans the transcript and appends the
structured verdict record to calls.jsonl.

Hook output: JSON with "additionalContext" key (Claude Code spec).
"""

import json
import pathlib
import sys

CALLS_LOG = pathlib.Path.home() / ".local/share/ollama-bridge/calls.jsonl"

data = json.load(sys.stdin)

# The judgeable set (T-105, V-D1): tools whose output is code the session reviews
# anyway. Deliberately NOT summarize/translate/classify_text — a 0/1/2 *quality*
# verdict is not meaningful there, and prompting for one only yields filler that
# pollutes the DPO corpus. Infrastructure tools (warm_model, list_models,
# ref_lookup, query_personas) are fire-and-forget.
#
# oficina is absent on purpose: it bypasses these tools entirely (its GenerateFn
# seam calls the client directly), and its verdict is per-RUN via run_result —
# judging the N internal repair iterations would be the wrong granularity.
GENERATION_TOOLS = {
    "mcp__ollama-bridge__generate_code",
    "mcp__ollama-bridge__ask_ollama",
}
RUN_RESULT_TOOL = "mcp__ollama-bridge__run_result"

tool_name = data.get("tool_name", "")
if tool_name not in GENERATION_TOOLS and tool_name != RUN_RESULT_TOOL:
    print(json.dumps({}))
    sys.exit(0)


def emit_call_verdict(call_id: str) -> None:
    """Ask for a verdict on ONE model call."""
    _emit("call_id", call_id)


def emit_run_verdict(run_id: str) -> None:
    """Ask for a verdict on an oficina RUN's deliverable (never a single call)."""
    _emit("run_id", run_id)


def _emit(key: str, value: str) -> None:
    """Owns the template text and the hook output envelope; exits when done."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"[VERDICT {key}={value}]\n"
                "verdict: 0 | 1 | 2  ← 0=rejected 1=improved 2=accepted; pick one, delete the others\n"
                "reason: <one line>\n"
                "est_claude_tokens: <number — (prompt chars + response chars) / 4, mentally>\n"
                "[/VERDICT]"
            ),
        }
    }))
    sys.exit(0)


def _silent() -> None:
    print(json.dumps({}))
    sys.exit(0)


def _returned_text(response):
    """Extract the tool's text from tool_response (a JSON string {"result": ...})."""
    if isinstance(response, str):
        try:
            parsed = json.loads(response)
        except Exception:
            return response
        if isinstance(parsed, dict):
            return parsed.get("result", response)
        return response
    if isinstance(response, dict):
        return response.get("result", "")
    return ""


if tool_name == RUN_RESULT_TOOL:
    # oficina is judged PER RUN, on the finished deliverable — never per loop
    # iteration. A run's internal repair attempts are not what the session reviews.
    #
    # Identity is free here: run_result takes run_id as an explicit argument, so it
    # is read from tool_input rather than inferred from the response.
    run_id = (data.get("tool_input") or {}).get("run_id")
    if not run_id:
        _silent()

    # Decide on the parse, not on a prefix. run_result returns JSON on success and
    # prose on failure ("Error: unknown run_id", "Error: run not terminal yet"), so
    # "did it parse as an object" IS the channel — sniffing for an "Error:" prefix
    # would be inspecting the value to infer failure.
    payload = _returned_text(data.get("tool_response"))
    try:
        result = json.loads(payload) if isinstance(payload, str) else None
    except ValueError:
        result = None

    if not isinstance(result, dict) or not result.get("deliverable"):
        # No deliverable → nothing to judge. Failed / IntakeRejected / Cancelled land
        # here, and the ledger's auto_verdict already records those as 0; polling
        # before terminal lands here too. Exhausted DOES surface a best attempt, so
        # it is judged.
        _silent()

    emit_run_verdict(run_id)


# Identify the call that just ran by matching what it RETURNED against the log.
#
# The previous implementation read the LAST record in calls.jsonl. That is a
# positional guess, not provenance: with parallel tool calls every concurrent hook
# reads the same tail record. Measured effect before this fix — 217 injections
# carrying only 75 distinct hashes, one hash emitted 16 times.
#
# Response content is ~97.5% unique across the corpus (547/563 distinct), so it
# identifies the record precisely. The server returns bare content (no id), so
# there is nothing better available on this side.
call_id = "unknown"
returned = _returned_text(data.get("tool_response"))
if CALLS_LOG.exists():
    records = []
    for line in CALLS_LOG.read_text(encoding="utf-8").strip().splitlines():
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") != "verdict":
            records.append(entry)

    match = None
    if returned:
        # Newest-first: if an identical response was ever produced twice, the call
        # that just ran is the later one.
        needle = returned.strip()
        for entry in reversed(records):
            logged = (entry.get("response") or "").strip()
            if not logged:
                continue
            # Exact match is the common case (ask_ollama returns content verbatim).
            #
            # Containment covers the tools that post-process before returning:
            # generate_code returns _strip_code_fences(content) while _log_call
            # records the RAW content, so the returned text is a substring of the
            # logged text and never equals it. Observed live 2026-07-21 — exact
            # match alone silently skipped every generate_code call, i.e. exactly
            # the tool this harness exists to judge.
            if logged == needle or (len(needle) > 20 and needle in logged):
                match = entry
                break
    if match is not None:
        # Pre-T-105 records have no call_id; prompt_hash keeps them joinable.
        call_id = match.get("call_id") or match.get("prompt_hash", "unknown")

# NO last-record fallback. Observed 2026-07-21: when a call exceeds the MCP
# deadline it is moved to the background, the hook fires before anything is
# logged, and a positional fallback confidently names the PREVIOUS call. A verdict
# attached to the wrong call is worse than a missing one — it silently mislabels
# the DPO corpus. Stay silent instead and let that call go unjudged.
if call_id == "unknown":
    _silent()

# Claude fills the template inline; the Stop hook matches verdict → call record
# by the embedded key.
emit_call_verdict(call_id)
