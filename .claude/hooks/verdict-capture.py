#!/usr/bin/env python3
"""verdict-capture.py — Stop hook that captures structured verdicts.

Reads the session transcript, finds filled [VERDICT ...] blocks written
by Claude after ollama tool calls, and appends them as typed records to
calls.jsonl. Keyed by prompt_hash so they can be joined with the original
call record for DPO pair assembly.

Deduplicates: skips any prompt_hash that already has a verdict record.
No-op if no new verdict blocks are found.

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
transcript_path = data.get("transcript_path", "")
if not transcript_path:
    sys.exit(0)

transcript_file = pathlib.Path(transcript_path)
if not transcript_file.exists():
    sys.exit(0)

# --- Load existing verdict hashes to deduplicate ---
existing_verdict_hashes: set[str] = set()
if CALLS_LOG.exists():
    for line in CALLS_LOG.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            if entry.get("type") == "verdict":
                existing_verdict_hashes.add(entry.get("prompt_hash", ""))
        except Exception:
            continue

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
#   [VERDICT prompt_hash=<hex12>]
#   verdict: ACCEPTED | IMPROVED | REJECTED
#   reason: <one line>
#   est_claude_tokens: <number>
#   [/VERDICT]
pattern = re.compile(
    r"\[VERDICT prompt_hash=([a-f0-9]+)\]\s*"
    r"verdict:\s*(ACCEPTED|IMPROVED|REJECTED)[^\n]*\n"
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
for prompt_hash, verdict, reason, est_tokens in matches:
    if prompt_hash in existing_verdict_hashes:
        continue
    new_records.append({
        "type": "verdict",
        "ts": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        "prompt_hash": prompt_hash,
        "verdict": verdict.upper(),
        "reason": reason.strip(),
        "est_claude_tokens": int(est_tokens),
    })

if not new_records:
    sys.exit(0)

CALLS_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(CALLS_LOG, "a", encoding="utf-8") as f:
    for record in new_records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

sys.exit(0)
