"""AI backend abstraction: enums, ABC, concrete implementations, loader, resolver."""

import json
import os
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

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
             model_override: str | None = None) -> str | None: ...


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
             model_override: str | None = None) -> str | None:
        import urllib.request

        # model_override may carry +think suffix (CLI convenience)
        raw_model = model_override or self.config.get("model", "")
        think_override = raw_model.endswith("+think")
        model = raw_model.removesuffix("+think")

        # think: from config, overridden if +think suffix was used on CLI
        think = think_override if model_override else self.config.get("think")

        # Planner output is small JSON — 4096 ctx is sufficient.
        # Full-file merges need 8192 minimum.
        num_ctx = 4096 if fmt is not None else 8192
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

        try:
            req = urllib.request.Request(
                self.config["address"],
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            chunks = []
            with urllib.request.urlopen(req, timeout=30) as resp:
                for line in resp:
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
             model_override: str | None = None) -> str | None:
        command = [self.config["command"]] + self.config.get("args", []) + [prompt]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
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
                    return envelope.get("result", stdout)
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
             model_override: str | None = None) -> str | None:
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
