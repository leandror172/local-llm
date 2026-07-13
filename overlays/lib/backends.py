"""AI backend abstraction: enums, ABC, concrete implementations, loader, resolver."""

import json
import os
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

# Context-size buckets, ascending. 32768 = probed 14B ceiling w/ q8_0 KV
# (ref:model-selection); never exceed it (VRAM).
_CTX_BUCKETS = (4096, 8192, 16384, 32768)

# Defaults for the Ollama merge call, overridable per-backend in ai-backends.yaml.
_DEFAULT_READ_TIMEOUT_S = 120   # per-socket-read timeout (cold load + think bursts)
_DEFAULT_MERGE_TIMEOUT_S = 600  # overall wall-clock deadline; on exceed → None


def fit_num_ctx(prompt_chars: int, output_headroom_tokens: int = 1024) -> int:
    """Smallest ctx bucket that holds the INPUT prompt, plus output headroom.

    The context window must fit the *input* prompt (~chars/4 tokens, this repo's
    diagnostic heuristic), NOT the small JSON output — sizing to the output was
    the RC1 bug that truncated full-file merges. Capped at the 14B VRAM ceiling.
    """
    need = (prompt_chars // 4) + output_headroom_tokens
    for bucket in _CTX_BUCKETS:
        if bucket >= need:
            return bucket
    return _CTX_BUCKETS[-1]

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


class BackendType(str, Enum):
    OLLAMA_API = "ollama_api"
    CLI = "cli"
    CLAUDE_API = "claude_api"
    OPENAI_COMPATIBLE = "openai_compatible_api"


class SchemaMode(str, Enum):
    FORMAT_PARAM = "format_param"
    PROMPT_INJECTION = "prompt_injection"
    TOOL_USE = "tool_use"


class Backend(ABC):
    def __init__(self, config: dict):
        self.config = config

    @property
    def id(self) -> str:
        return self.config["id"]

    @property
    def schema_mode(self) -> SchemaMode:
        return SchemaMode(self.config.get("schema_mode", SchemaMode.PROMPT_INJECTION))

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def call(self, prompt: str, fmt: dict | None = None,
             model_override: str | None = None, debug: bool = False) -> str | None: ...


class OllamaApiBackend(Backend):

    def is_available(self) -> bool:
        import urllib.request
        try:
            base = self.config["address"].split("/api/")[0]
            urllib.request.urlopen(f"{base}/api/tags", timeout=2)
            return True
        except Exception:
            return False

    def call(self, prompt: str, fmt: dict | None = None,
             model_override: str | None = None, debug: bool = False) -> str | None:
        import urllib.request

        # model_override may carry +think suffix (CLI convenience)
        raw_model = model_override or self.config.get("model", "")
        think_override = raw_model.endswith("+think")
        model = raw_model.removesuffix("+think")

        # think: from config, overridden if +think suffix was used on CLI
        think = think_override if model_override else self.config.get("think")

        # Size the context window to the INPUT prompt (full-file merges overflow
        # a fixed constant); output is small JSON, covered by fit_num_ctx headroom.
        num_ctx = fit_num_ctx(len(prompt))
        payload: dict = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "options": {"num_ctx": num_ctx},
        }
        # think is Qwen3-specific; null config means don't send the param
        if think is not None:
            payload["think"] = think
        if fmt is not None:
            payload["format"] = fmt

        # Per-read socket timeout tolerates cold model load + silent think bursts;
        # the overall wall-clock deadline bounds the whole call. Both config-driven.
        read_timeout = self.config.get("read_timeout_s", _DEFAULT_READ_TIMEOUT_S)
        merge_timeout = self.config.get("merge_timeout_s", _DEFAULT_MERGE_TIMEOUT_S)

        try:
            req = urllib.request.Request(
                self.config["address"],
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            chunks = []
            deadline_start = time.monotonic()
            with urllib.request.urlopen(req, timeout=read_timeout) as resp:
                for line in resp:
                    if merge_timeout is not None and \
                            time.monotonic() - deadline_start > merge_timeout:
                        # A timeout is not a quality failure — caller treats None
                        # as "add manually"; there is no DPO triple to record.
                        print(f"  WARNING: Ollama merge exceeded {merge_timeout}s "
                              f"wall-clock deadline — TIMEOUT (add manually)",
                              file=sys.stderr)
                        return None
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    if chunk.get("message", {}).get("content"):
                        chunks.append(chunk["message"]["content"])
                    if chunk.get("done"):
                        break
            return "".join(chunks)
        except Exception as e:
            print(f"  WARNING: Ollama API call failed: {e}", file=sys.stderr)
            return None


class CliBackend(Backend):

    def is_available(self) -> bool:
        if not shutil.which(self.config["command"]):
            return False
        # claude CLI cannot be nested inside an active Claude Code session
        if self.config["command"] == "claude" and os.environ.get("CLAUDECODE"):
            return False
        return True

    def call(self, prompt: str, fmt: dict | None = None,
             model_override: str | None = None, debug: bool = False) -> str | None:
        # Pass prompt via stdin — more robust than positional arg for long prompts
        command = [self.config["command"]] + self.config.get("args", [])
        try:
            result = subprocess.run(
                command, input=prompt, capture_output=True, text=True, timeout=120
            )
            if debug:
                print(f"  DEBUG stdout: {result.stdout[:500]!r}", file=sys.stderr)
                print(f"  DEBUG stderr: {result.stderr[:200]!r}", file=sys.stderr)
                print(f"  DEBUG exit:   {result.returncode}", file=sys.stderr)
            if result.returncode != 0:
                print(f"  WARNING: CLI call failed: {result.stderr}", file=sys.stderr)
                return None
            stdout = result.stdout.strip()
            if not stdout:
                print("  WARNING: CLI call returned empty output", file=sys.stderr)
                return None
            # If --output-format json is in args, unwrap the envelope
            if "--output-format" in self.config.get("args", []):
                try:
                    envelope = json.loads(stdout)
                    if envelope.get("is_error"):
                        print(f"  WARNING: CLI returned error: {envelope.get('result', '')}", file=sys.stderr)
                        return None
                    result_text = envelope.get("result", "")
                    if not result_text:
                        print("  WARNING: CLI envelope has empty result field", file=sys.stderr)
                        return None
                    return result_text
                except json.JSONDecodeError:
                    pass  # not a JSON envelope — return raw
            return stdout
        except Exception as e:
            print(f"  WARNING: CLI call failed: {e}", file=sys.stderr)
            return None


class ClaudeApiBackend(Backend):

    def is_available(self) -> bool:
        key_spec = self.config.get("api_key", "")
        if str(key_spec).startswith("env:"):
            return os.environ.get(key_spec[4:]) is not None
        return bool(key_spec)

    def call(self, prompt: str, fmt: dict | None = None,
             model_override: str | None = None, debug: bool = False) -> str | None:
        import urllib.request
        key_spec = self.config.get("api_key", "")
        api_key = os.environ.get(key_spec[4:]) if str(key_spec).startswith("env:") else key_spec
        if not api_key:
            print("  WARNING: Claude API key not available", file=sys.stderr)
            return None

        model = model_override or self.config.get("model", "claude-haiku-4-5")
        if fmt is not None:
            payload = {
                "model": model,
                "max_tokens": 512,
                "tools": [{"name": "merge_plan", "description": "Output the merge plan",
                            "input_schema": fmt}],
                "tool_choice": {"type": "tool", "name": "merge_plan"},
                "messages": [{"role": "user", "content": prompt}],
            }
        else:
            payload = {
                "model": model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
        try:
            req = urllib.request.Request(
                self.config["address"],
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json",
                         "x-api-key": api_key,
                         "anthropic-version": "2023-06-01"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            for block in data.get("content", []):
                if block.get("type") == "tool_use":
                    return json.dumps(block["input"])
                if block.get("type") == "text":
                    return block["text"]
        except Exception as e:
            print(f"  WARNING: Claude API call failed: {e}", file=sys.stderr)
        return None


_BACKEND_CLASSES: dict[BackendType, type[Backend]] = {
    BackendType.OLLAMA_API: OllamaApiBackend,
    BackendType.CLI: CliBackend,
    BackendType.CLAUDE_API: ClaudeApiBackend,
}


def load_backends(script_dir: Path) -> list[Backend]:
    """Load ai-backends.yaml; return list of Backend instances sorted by priority."""
    path = script_dir / "ai-backends.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text()).get("backends", [])
    backends = []
    for cfg in sorted(raw, key=lambda b: b.get("priority", 99)):
        t = BackendType(cfg["type"])
        cls = _BACKEND_CLASSES.get(t)
        if cls:
            backends.append(cls(cfg))
        else:
            print(f"  WARNING: unknown backend type '{cfg['type']}' — skipping", file=sys.stderr)
    return backends


def resolve_backend(backends: list[Backend], preference: str,
                    model_override: str | None) -> Backend | None:
    """Return first available backend. 'auto' tries in priority order; otherwise match by id."""
    if preference == "auto":
        return next((b for b in backends if b.is_available()), None)
    return next((b for b in backends if b.id == preference and b.is_available()), None)
