"""Optional structured debug logging for the ollama-bridge MCP server.

Enabled by environment variables (read once at import time):
  OLLAMA_BRIDGE_LOG_LEVEL  DEBUG | INFO | WARNING | ERROR  (default: WARNING)
  OLLAMA_BRIDGE_LOG_FILE   path                              (default: /tmp/ollama-bridge.jsonl)

Output is one JSON object per line. Every record carries the process's
`client_id` (random 4-byte hex assigned at startup) and `pid`, so multiple
bridges writing to the same file can be demultiplexed with:
  jq 'select(.client_id=="ab12cd34")' /tmp/ollama-bridge.jsonl
"""
import datetime
import json
import logging
import os
import pathlib
import secrets
import subprocess

CLIENT_ID = secrets.token_hex(4)
PID = os.getpid()

_LOGGER_NAME = "ollama_mcp"


def _git_field(*args: str) -> str:
    try:
        out = subprocess.check_output(
            ["git", *args],
            cwd=pathlib.Path(__file__).parent,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


_RESERVED = {"t", "level", "ev", "client_id", "pid"}


class _JsonlFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {}
        extra = getattr(record, "fields", None)
        if extra:
            # Drop any user-supplied keys that would shadow reserved fields.
            payload.update({k: v for k, v in extra.items() if k not in _RESERVED})
        payload["t"] = datetime.datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        payload["level"] = record.levelname
        payload["ev"] = record.getMessage()
        payload["client_id"] = CLIENT_ID
        payload["pid"] = PID
        return json.dumps(payload, default=str)


def setup() -> dict:
    """Configure the ollama_mcp logger from env. Returns banner info."""
    level_name = os.environ.get("OLLAMA_BRIDGE_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    log_file = os.environ.get("OLLAMA_BRIDGE_LOG_FILE", "/tmp/ollama-bridge.jsonl")

    logger = logging.getLogger(_LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False

    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    handler.setFormatter(_JsonlFormatter())
    logger.addHandler(handler)

    return {
        "log_level": level_name,
        "log_file": log_file,
        "client_id": CLIENT_ID,
        "pid": PID,
        "ppid": os.getppid(),
        "git": _git_field("rev-parse", "--short", "HEAD"),
        "branch": _git_field("rev-parse", "--abbrev-ref", "HEAD"),
    }


def _emit(level: int, event: str, fields: dict) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.isEnabledFor(level):
        logger.log(level, event, extra={"fields": fields})


def debug(event: str, **fields) -> None:
    _emit(logging.DEBUG, event, fields)


def info(event: str, **fields) -> None:
    _emit(logging.INFO, event, fields)


def error(event: str, **fields) -> None:
    _emit(logging.ERROR, event, fields)
