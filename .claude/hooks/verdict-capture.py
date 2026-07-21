#!/usr/bin/env python3
"""verdict-capture.py — Stop hook that captures structured verdicts.

Reads the session transcript, finds filled [VERDICT ...] blocks written
by Claude after ollama tool calls, and appends them as typed records to
calls.jsonl. Keyed by call_id (T-105) so a verdict names exactly one call;
prompt_hash is recorded alongside it for joins with pre-T-105 records.

Deduplicates: skips any call_id (or legacy prompt_hash) that already has a
verdict record. No-op if no new verdict blocks are found.

Scans the WHOLE transcript, not `last_assistant_message`: verdict blocks are
routinely emitted mid-turn, before further tool calls, so the final message
alone would miss most of them (verified 2026-07-21).

Hook output: none (exits 0 silently — never blocks the session).
"""

import datetime
import json
import pathlib
import re
import sys

CALLS_LOG = pathlib.Path.home() / ".local/share/ollama-bridge/calls.jsonl"

# --- Load hook input ---
data = json.load(sys.stdin)

# SubagentStop provides agent_transcript_path (the subagent's own transcript).
# Stop provides transcript_path (the main session transcript).
# Always prefer the transcript that contains the assistant messages with verdicts.
if data.get("hook_event_name") == "SubagentStop":
    transcript_path = data.get("agent_transcript_path", "")
else:
    transcript_path = data.get("transcript_path", "")

if not transcript_path:
    sys.exit(0)

transcript_file = pathlib.Path(transcript_path)
if not transcript_file.exists():
    sys.exit(0)

# --- Index the log: existing verdict keys (dedupe) + call records (join) ---
#
# T-105: dedupe on the CALL key, not prompt_hash. prompt_hash is a content address,
# so identical prompts share one — deduping on it meant that once any call with a
# given prompt was judged, no sibling could ever be judged again. One hash covered
# 24 calls across 8 models (a compare-models sweep), so that sweep could record
# exactly one verdict.
existing_verdict_keys: set[str] = set()
calls_by_id: dict[str, dict] = {}
if CALLS_LOG.exists():
    for line in CALLS_LOG.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") == "verdict":
            for key in ("call_id", "prompt_hash", "run_id"):
                if entry.get(key):
                    existing_verdict_keys.add(entry[key])
        else:
            # Pre-T-105 records have no call_id; index them under prompt_hash so
            # legacy-keyed blocks still resolve.
            for key in (entry.get("call_id"), entry.get("prompt_hash")):
                if key and key not in calls_by_id:
                    calls_by_id[key] = entry

# --- Extract text from all assistant messages in the transcript ---
# Handles two content formats:
#   string:  {"role": "assistant", "content": "text"}
#   array:   {"role": "assistant", "content": [{"type": "text", "text": "..."}]}
# Also handles the nested {"message": {...}} wrapper Claude Code sometimes uses.
assistant_chunks: list[str] = []
for line in transcript_file.read_text(encoding="utf-8").splitlines():
    try:
        msg = json.loads(line)
    except Exception:
        continue

    # Unwrap {"message": {...}} envelope if present
    if "message" in msg and isinstance(msg["message"], dict):
        msg = msg["message"]

    if msg.get("role") != "assistant":
        continue

    content = msg.get("content", "")
    if isinstance(content, str):
        assistant_chunks.append(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                assistant_chunks.append(block.get("text", ""))

full_text = "\n".join(assistant_chunks)

# --- Find filled VERDICT blocks ---
# Template format injected by ollama-post-tool.py:
#   [VERDICT call_id=<hex12>]
#   verdict: 0 | 1 | 2  (0=rejected 1=improved 2=accepted)
#   reason: <one line>
#   est_claude_tokens: <number>
#   [/VERDICT]
#
# `prompt_hash=` is still accepted so blocks written before T-105 — and any still
# sitting in an open transcript when this shipped — are not silently dropped.
#
# The value charset is [A-Za-z0-9_-], NOT [a-f0-9]: oficina run ids are
# base64url-shaped (e.g. `-L-rwoCLLsoL33eirtSRzw`), so a hex-only class would
# reject every run-keyed block *silently* — the same class of failure this whole
# harness was repaired for. call_id remains lowercase hex; the wider class admits
# it unchanged.
pattern = re.compile(
    r"\[VERDICT (call_id|prompt_hash|run_id)=([A-Za-z0-9_-]+)\]\s*"
    r"verdict:\s*([012])[^\n]*\n"
    r"reason:\s*([^\n]+)\n"
    r"est_claude_tokens:\s*(\d+)[^\n]*\n"
    r"\[/VERDICT\]",
    re.IGNORECASE,
)

matches = pattern.findall(full_text)
if not matches:
    sys.exit(0)

# --- Append new verdict records ---
new_records = []
for key_name, key, verdict, reason, est_tokens in matches:
    if key in existing_verdict_keys:
        continue
    record = {
        "type": "verdict",
        "ts": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        "verdict": int(verdict),
        "reason": reason.strip(),
        "est_claude_tokens": int(est_tokens),
    }
    if key_name.lower() == "run_id":
        # oficina: one verdict for the RUN's deliverable, not its N iterations.
        # There is deliberately no call_id — the run spans several calls, and
        # picking one would misattribute the judgment.
        record["run_id"] = key
        record["tool"] = "oficina"
    else:
        call = calls_by_id.get(key, {})
        # Both keys are written: call_id is identity, prompt_hash keeps the record
        # joinable with pre-T-105 data and with readers that still expect it.
        record["call_id"] = call.get("call_id") or key
        record["prompt_hash"] = call.get("prompt_hash") or key
        if call.get("tool"):
            record["tool"] = call["tool"]
    new_records.append(record)
    existing_verdict_keys.add(key)  # a block repeated within one turn is one verdict

if not new_records:
    sys.exit(0)

CALLS_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(CALLS_LOG, "a", encoding="utf-8") as f:
    for record in new_records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

sys.exit(0)
