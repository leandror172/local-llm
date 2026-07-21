"""FastMCP server exposing Ollama models as tools for Claude Code.

This is the heart of the MCP server. It defines the tools that Claude Code
can discover and invoke. Each tool is a Python function decorated with
@mcp.tool() — FastMCP automatically:
  1. Generates a JSON schema from the function's type hints and docstring
  2. Validates incoming arguments against that schema
  3. Handles the JSON-RPC protocol over stdio

The server uses a "lifespan" pattern to manage the Ollama HTTP client:
- On startup: create a shared httpx client (connection pooling)
- On shutdown: close the client cleanly (release TCP connections)
"""

import asyncio
import json
import os
import pathlib
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from ollama_mcp.client import OllamaClient, OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError
from ollama_mcp.config import DEFAULT_MODEL, MODELS, REGISTRY_PATH, REPO_ROOT, TEMPS
from ollama_mcp import debug_log
from ollama_mcp import registry
from ollama_mcp.oficina import config as oficina_config
from ollama_mcp.oficina import service as oficina_service
from ollama_mcp.oficina.store import UnknownRunError

# ---------------------------------------------------------------------------
# context_files support
# ---------------------------------------------------------------------------

class ContextFile(BaseModel):
    """A file (or slice of a file) to inject into the Ollama prompt server-side.

    The server reads the file at `path` and prepends its content as a fenced
    code block to the prompt. This avoids passing file content through Claude's
    context (which costs tokens twice: once to read, once to embed in the prompt).

    Attributes:
        path: Absolute path to the file. Must exist and be readable.
        start_line: First line to include (1-based, inclusive). Omit for full file.
        end_line: Last line to include (1-based, inclusive). Omit for full file.
    """
    path: str
    start_line: int | None = None
    end_line: int | None = None


def _build_context_block(context_files: list[ContextFile]) -> str:
    """Read each file (with optional line slice) and format as a fenced block.

    Returns a <context>...</context> string ready to prepend to the prompt,
    or an error string if any file cannot be read.
    """
    sections: list[str] = []

    for cf in context_files:
        p = pathlib.Path(cf.path)
        if not p.is_absolute():
            return f"Error: context_files path must be absolute: {cf.path!r}"
        if not p.exists():
            return f"Error: context_files path not found: {cf.path!r}"
        if not p.is_file():
            return f"Error: context_files path is not a file: {cf.path!r}"

        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as e:
            return f"Error: cannot read {cf.path!r}: {e}"

        # Apply line slice (1-based, inclusive → 0-based slice)
        if cf.start_line is not None or cf.end_line is not None:
            start = max(0, (cf.start_line or 1) - 1)
            end = cf.end_line if cf.end_line is not None else len(lines)
            lines = lines[start:end]
            label = f"{cf.path} (lines {cf.start_line or 1}–{cf.end_line or len(lines) + start})"
        else:
            label = cf.path

        # Infer language hint from extension for the fenced block
        suffix = p.suffix.lstrip(".") or "text"
        content = "\n".join(lines)
        sections.append(f"### {label}\n```{suffix}\n{content}\n```")

    return "<context>\n" + "\n\n".join(sections) + "\n</context>"


# ---------------------------------------------------------------------------
# refs param support
# ---------------------------------------------------------------------------

def _ref_lookup_script() -> str:
    """Resolve ref-lookup.sh: ``OFICINA_REF_LOOKUP`` env, else ``LLM_REPO_ROOT``, else package-relative.

    Env is read at CALL time (not config.REPO_ROOT's import-time snapshot) so a
    detached oficina worker spawned without the server's env still resolves refs
    (T-96). Mirrors ``evaluator._validate_code_script``.
    """
    override = os.environ.get("OFICINA_REF_LOOKUP")
    if override:
        return override
    repo_root = os.environ.get("LLM_REPO_ROOT") or str(
        pathlib.Path(__file__).resolve().parents[3]
    )
    return os.path.join(repo_root, ".claude", "tools", "ref-lookup.sh")


async def _run_script(
    args: list[str],
    *,
    timeout: int,
    label: str,
    on_error: Callable[[int, str, str], str] | None = None,
    on_success: Callable[[str], None] | None = None,
) -> str:
    """Run a subprocess, returning stripped stdout or an ``Error:`` string.

    Centralizes the ``create_subprocess_exec`` → ``wait_for`` → returncode → decode
    dance shared by every script-backed tool (ref-lookup, detect/build/create-persona).
    ``label`` names the tool in the default non-zero-exit, timeout, and generic-error
    messages. Hooks let callers that need to differ opt out of the defaults:

    - ``on_error(returncode, stdout, stderr) -> str`` overrides the non-zero-exit
      message (the ref tools word theirs differently — that historical drift is now
      explicit at the call site rather than copy-pasted).
    - ``on_success(stdout)`` runs on a zero exit before the stripped stdout is
      returned (create_persona reloads the registry here). Anything it raises is
      caught by the generic handler, matching the pre-extraction inline behavior.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out, err = stdout.decode(), stderr.decode()

        if proc.returncode != 0:
            if on_error is not None:
                return on_error(proc.returncode, out, err)
            err_msg = err.strip() if err else "Unknown error"
            return f"Error: {label} exited with code {proc.returncode}: {err_msg}"

        if on_success is not None:
            on_success(out)
        return out.strip()

    except asyncio.TimeoutError:
        proc.kill()
        return f"Error: {label} timed out after {timeout} seconds."
    except Exception as e:
        return f"Error running {label}: {e}"


async def _resolve_ref_key(key: str, root: str | None) -> str:
    """Run ref-lookup.sh for a single key. Return stdout or an Error: string.

    root is forwarded as --root only when not None (matches ref_lookup tool
    behaviour — lets the script handle its own default when omitted).
    Expected to be called against small ref folders; the script has no
    internal timeout, so keep ref roots compact.
    """
    script = _ref_lookup_script()
    if not os.path.isfile(script):
        return f"Error: ref-lookup script not found at {script}"

    args = [script, key]
    if root is not None:
        args += ["--root", root]

    return await _run_script(
        args,
        timeout=10,
        label="ref-lookup",
        on_error=lambda rc, out, err: (
            f"Error: ref:'{key}' not found — {out.strip() or err.strip() or 'Unknown error'}"
        ),
    )


async def _build_refs_block(refs: list[str], root: str | None) -> str:
    """Resolve each ref key and format as a <refs>…</refs> block.

    Returns a <refs>...</refs> string ready to prepend to the prompt,
    or an error string if any resolution fails.
    """
    if root is not None:
        if not pathlib.Path(root).is_absolute():
            return f"Error: refs_root must be an absolute path: {root!r}"

    results = await asyncio.gather(*(_resolve_ref_key(key, root) for key in refs))

    for result in results:
        if result.startswith("Error:"):
            return result

    return "<refs>\n" + "\n\n".join(results) + "\n</refs>"


async def _assemble_prompt(
    base: str,
    context_files: list[ContextFile] | None,
    refs: list[str] | None,
    refs_root: str | None,
) -> tuple[str, str | None]:
    """Wrap ``base`` outward with <context> then <refs> layers (<refs> → <context> → base).

    Returns ``(assembled_prompt, None)`` on success, or ``(base, error_string)`` if any
    block fails to build — the caller returns the error verbatim. A tuple (rather than a
    sentinel ``Error:`` string) is deliberate: ``base`` is caller-supplied and may itself
    legitimately start with ``"Error:"``, so success must not be distinguishable by prefix.

    ``base`` must already carry any caller-specific prefix (e.g. generate_code's
    ``[Language: X]`` hint) — this helper is prompt-content-agnostic.
    """
    full_prompt = base
    if context_files:
        context_block = _build_context_block(context_files)
        if context_block.startswith("Error:"):
            return base, context_block
        full_prompt = f"{context_block}\n\n{full_prompt}"
    if refs:
        refs_block = await _build_refs_block(refs, refs_root)
        if refs_block.startswith("Error:"):
            return base, refs_block
        full_prompt = f"{refs_block}\n\n{full_prompt}"
    return full_prompt, None


# ---------------------------------------------------------------------------
# output_file support
# ---------------------------------------------------------------------------

def _resolve_output_path(path: str) -> pathlib.Path | str:
    """Resolve a path string to an absolute Path, or return an Error: string.

    Leading ``~`` is expanded to ``$HOME`` first (Claude passes strings
    unprocessed by any shell, so we must expand them ourselves). Absolute paths
    are used as-is. Relative paths are anchored to REPO_ROOT. Returns an error
    string if path is relative and REPO_ROOT is not set. Note: does NOT call
    .resolve() — callers that need canonical paths should call .resolve()
    after ensuring parent directories exist.
    """
    p = pathlib.Path(path).expanduser()
    if p.is_absolute():
        return p
    if REPO_ROOT is not None:
        return pathlib.Path(REPO_ROOT) / p
    return "Error: output_file is a relative path but REPO_ROOT is not set"


def _write_output_file(path: pathlib.Path | str, content: str) -> str:
    """Write content to path atomically. Returns a status string or Error: string.

    Accepts either a pre-resolved pathlib.Path (from an earlier _resolve_output_path
    call) or a raw string (resolved internally). Callers that already validated the
    path should pass the Path directly to avoid resolving twice.
    """
    if isinstance(path, str):
        resolved = _resolve_output_path(path)
        if isinstance(resolved, str):
            return resolved
    else:
        resolved = path
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        # Resolve AFTER mkdir so symlinked parents are traversable for canonicalization.
        resolved = resolved.resolve()
        tmp = pathlib.Path(str(resolved) + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, resolved)
    except OSError as e:
        return f"Error writing to {resolved}: {e}"
    return f"Written {resolved.stat().st_size} bytes to {resolved}"


# ---------------------------------------------------------------------------
# Language → persona routing for generate_code
# ---------------------------------------------------------------------------

# Fallback routes used only when the persona registry isn't loaded.
# When the registry IS loaded, registry.get_language_routes() provides a
# richer mapping built from actual persona metadata (see registry.py).
_FALLBACK_LANGUAGE_ROUTES: dict[str, str] = {
    "java": "my-coder-q3",
    "go": "my-coder-q3",
    "html": "my-creative-coder-q3",
    "javascript": "my-creative-coder-q3",
    "css": "my-creative-coder-q3",
}

_DEFAULT_CODEGEN_MODEL = "my-codegen-q3"

# ---------------------------------------------------------------------------
# Module-level client (set during server lifespan)
# ---------------------------------------------------------------------------

# This variable holds the shared OllamaClient instance. It's None until the
# server starts (lifespan __aenter__) and None again after shutdown (__aexit__).
# Tools call _get_client() to access it safely.
_client: OllamaClient | None = None


def _get_client() -> OllamaClient:
    """Get the shared Ollama client. Raises if server hasn't started yet."""
    if _client is None:
        raise RuntimeError("OllamaClient not initialized — server not running?")
    return _client


# ---------------------------------------------------------------------------
# Server lifespan (startup/shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastMCP) -> AsyncIterator[None]:
    """Manage the Ollama HTTP client lifecycle.

    This is an async context manager — Python's pattern for "setup, yield,
    teardown". The code before `yield` runs on startup, the code after runs
    on shutdown (even if an error occurred). FastMCP calls this automatically.
    """
    global _client
    _client = OllamaClient()

    banner = debug_log.setup()
    print(
        f"[ollama-bridge] pid={banner['pid']} ppid={banner['ppid']} "
        f"git={banner['git']} branch={banner['branch']} "
        f"client_id={banner['client_id']} log_level={banner['log_level']} "
        f"log_file={banner['log_file']}",
        file=sys.stderr,
    )
    debug_log.info("server_start", **banner)

    # Non-blocking health probe — log Ollama status at startup for diagnostics.
    # Tools handle errors individually, so failure here doesn't block the server.
    try:
        models = await _client.list_models()
        print(
            f"[ollama-bridge] Ollama connected — {len(models)} model(s) available",
            file=sys.stderr,
        )
    except OllamaConnectionError:
        print(
            "[ollama-bridge] Warning: Ollama is not reachable. "
            "Tools will return friendly errors until Ollama starts.",
            file=sys.stderr,
        )
    except Exception as e:
        print(
            f"[ollama-bridge] Warning: Health probe failed: {e}",
            file=sys.stderr,
        )

    # Load persona registry (used for query_personas, language routing, and
    # persona validation). Non-fatal: tools degrade gracefully if missing.
    if REGISTRY_PATH:
        try:
            reg = registry.load_registry(REGISTRY_PATH)
            active = sum(1 for v in reg.values() if v.get("status") == "active")
            print(
                f"[ollama-bridge] Persona registry loaded — {active} active persona(s)",
                file=sys.stderr,
            )
        except Exception as e:
            print(
                f"[ollama-bridge] Warning: Could not load persona registry: {e}",
                file=sys.stderr,
            )
    else:
        print(
            "[ollama-bridge] Warning: LLM_REPO_ROOT not set — persona registry unavailable",
            file=sys.stderr,
        )

    try:
        yield
    finally:
        debug_log.info("server_stop")
        await _client.close()
        _client = None


# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

# This creates the MCP server object. The `name` appears in Claude Code's
# tool list. `instructions` helps Claude understand when to use these tools.
mcp = FastMCP(
    name="ollama-bridge",
    instructions=(
        "Local LLM gateway via Ollama. Use for simple tasks that don't need "
        "frontier-level intelligence: boilerplate code, text transformation, "
        "explanations, summaries. Models run on a local GPU — fast but less "
        "capable than Claude."
    ),
    lifespan=_lifespan,
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def ask_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
    persona: str | None = None,
    context_files: list[ContextFile] | None = None,
    refs: list[str] | None = None,
    refs_root: str | None = None,
    output_file: str | None = None,
    output_only: bool = False,
    timeout: int = 120,
) -> str:
    """Ask a question to a local Ollama model.

    General-purpose tool for explanations, Q&A, brainstorming, and analysis.
    For specialized tasks, prefer the dedicated tools:
    - generate_code: code generation (auto-routes to language-specific personas)
    - summarize: text summarization (bullet points)
    - classify_text: text classification (structured JSON output)
    - translate: language translation

    Args:
        prompt: The question or instruction for the model.
        model: Ollama model to use. Available: my-coder, my-coder-q3,
               my-creative-coder, my-creative-coder-q3, my-codegen-q3,
               my-summarizer-q3, my-classifier-q3, my-translator-q3.
               Default: my-coder-q3 (Qwen3-8B, good all-rounder).
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
                     Default: model's built-in default.
        persona: Use a specific persona by name (e.g., "my-python-q3").
                 Overrides the model parameter. Use query_personas to discover
                 available personas. Returns an error if the persona is not
                 found in the registry.
        context_files: Files to inject into the prompt server-side. Each entry
                       requires an absolute `path`; optional `start_line` and
                       `end_line` (1-based, inclusive) select a slice. Content
                       is prepended as fenced code blocks — avoids passing file
                       content through Claude's context (saves tokens).
        refs: Reference keys to resolve and inject as documentation context.
              Each key must match a <!-- ref:KEY --> marker in a *.md file under
              refs_root. Resolved content is prepended as a <refs> block before
              the prompt — no Claude token cost. Use ref_lookup(key="list") to
              see available keys in a folder.
        refs_root: Folder to search for ref markers (any folder with *.md files
                   using <!-- ref:KEY --> convention). Defaults to REPO_ROOT.
                   Must be an absolute path. Pass any project folder to look up
                   its own refs.
        output_file: Path to write the response to (relative or absolute).
                     Relative paths are resolved from REPO_ROOT. Parent directories
                     are created automatically. Content is always returned to the
                     caller as well, unless output_only=True.
        output_only: If True and output_file is set, write to file and return only
                     a compact status string ("Written N bytes to /path") instead
                     of the full response. Defers verdict assessment to after file
                     inspection. Ignored if output_file is not set.
        timeout: Max seconds to wait for a response. Default 120. Increase for
                 large models (30B+) or complex prompts (e.g., 300 for hybrid models).

    Returns:
        The model's text response. If Ollama is unreachable, returns an error
        message instead of raising (so Claude can handle it gracefully).
    """
    t0 = time.perf_counter()
    debug_log.debug(
        "tool_enter",
        tool="ask_ollama",
        model=model,
        persona=persona,
        output_file=output_file,
        output_only=output_only,
        timeout=timeout,
        prompt_chars=len(prompt),
    )

    def _done(ok: bool, **fields):
        debug_log.debug(
            "tool_exit",
            tool="ask_ollama",
            ok=ok,
            ms=round((time.perf_counter() - t0) * 1000, 2),
            **fields,
        )

    if output_file is not None:
        _pre = _resolve_output_path(output_file)
        if isinstance(_pre, str):
            _done(False, reason="resolve_failed")
            return _pre

    # Persona override: validate against registry and use as model name
    if persona is not None:
        reg = registry.get_registry()
        if reg and persona not in reg:
            # Suggest similar names to help the caller
            suggestions = [n for n in reg if persona.split("-")[1] in n] if "-" in persona else []
            msg = f"Error: Persona '{persona}' not found in registry."
            if suggestions:
                msg += f" Similar: {', '.join(suggestions[:5])}"
            msg += " Use query_personas() to list available personas."
            _done(False, reason="persona_not_found", persona=persona)
            return msg
        model = persona

    client = _get_client()

    # Build prompt outward: context_files first, refs outermost (<refs> → <context> → prompt)
    full_prompt, prompt_err = await _assemble_prompt(prompt, context_files, refs, refs_root)
    if prompt_err is not None:
        _done(False, reason="prompt_assembly_error")
        return prompt_err

    try:
        response = await client.chat(
            prompt=full_prompt,
            model=model,
            temperature=temperature,
            timeout=timeout,
            tool="ask_ollama",
        )
        content = response.content
        if output_file:
            write_result = _write_output_file(_pre, content)
            if write_result.startswith("Error:"):
                _done(False, reason="write_failed", model=model)
                return write_result
            if output_only:
                _done(True, model=model, output_only=True, content_chars=len(content))
                return write_result
        _done(True, model=model, content_chars=len(content))
        return content

    except OllamaConnectionError:
        _done(False, reason="OllamaConnectionError", model=model)
        return (
            "Error: Cannot connect to Ollama. "
            "Is it running? Start with: ollama serve"
        )
    except OllamaModelNotFoundError:
        _done(False, reason="OllamaModelNotFoundError", model=model)
        return (
            f"Error: Model '{model}' not found. "
            f"Available models: {', '.join(MODELS)}"
        )
    except OllamaTimeoutError:
        _done(False, reason="OllamaTimeoutError", model=model)
        return (
            "Error: Ollama timed out. The model may be loading (cold start). "
            "Try again in a few seconds."
        )


@mcp.tool()
async def list_models() -> str:
    """List all models currently available in Ollama.

    Returns model names and sizes. Useful for checking which models are
    pulled and ready to use before calling ask_ollama.
    """
    client = _get_client()

    try:
        models = await client.list_models()
    except OllamaConnectionError:
        return (
            "Error: Cannot connect to Ollama. "
            "Is it running? Start with: ollama serve"
        )

    if not models:
        return "No models found. Pull one with: ollama pull <model-name>"

    # Format each model as "name (size)" for easy reading.
    # The size comes in bytes from the API; convert to GB for readability.
    lines = []
    for m in models:
        name = m.get("name", "unknown")
        size_bytes = m.get("size", 0)
        size_gb = size_bytes / (1024 ** 3)
        lines.append(f"  - {name} ({size_gb:.1f} GB)")

    return "Available Ollama models:\n" + "\n".join(lines)


def _model_matches(loaded_name: str, requested: str) -> bool:
    """True if an Ollama model name (possibly ``model:tag``) matches a requested
    base or fully-qualified name — tolerant of an implicit ``:latest`` tag.

    Ollama reports loaded/available models as ``model:tag`` (e.g. ``my-coder-q3:latest``).
    Callers request either the bare base (``my-coder-q3``) or the tagged form, so a
    match holds three ways: exact, requested-plus-implicit-``:latest``, or base-only.
    """
    return (
        loaded_name == requested
        or loaded_name == f"{requested}:latest"
        or requested == loaded_name.split(":")[0]
    )


async def _check_model_exists(client: OllamaClient, model: str) -> str | None:
    try:
        models = await client.list_models()
    except OllamaConnectionError:
        return "Error: Cannot connect to Ollama. Is it running? Start with: ollama serve"

    available_names = [m.get("name", "") for m in models]
    found = any(_model_matches(name, model) for name in available_names)

    if not found:
        base_names = [n.split(":")[0] for n in available_names]
        return f"Error: Model '{model}' not found. Available: {', '.join(base_names)}"


@mcp.tool()
async def warm_model(
    model: str,
    force: bool = False,
) -> str:
    """Pre-load a model into VRAM to avoid cold-start timeouts on the next call.

    Checks if the target model is already loaded. If not, safely evicts the
    current model (checking for in-flight requests first) and sends a trivial
    prompt to force-load the target model.

    Use at session start or before switching between models (e.g., switching
    from a coding persona to a summarizer). Prevents the first real call from
    timing out due to model loading.

    NOTE: The in-flight safety check is single-session only. Each Claude Code
    session has its own MCP server process with its own in-flight counter, so
    calls from a different session (e.g., the expense repo) are not visible.
    Cross-session protection requires the file-based coordination layer
    described in docs/ideas/ollama-coordination-layer.md (Option 2).

    Args:
        model: The Ollama model/persona name to pre-load (e.g., "my-coder-q3").
        force: If True, skip the in-flight safety check and evict anyway.
               Use only when you're certain no other calls are active.

    Returns:
        Status message describing what was done.
    """
    client = _get_client()

    try:
        running = await client.list_running()
    except OllamaConnectionError:
        return (
            "Error: Cannot connect to Ollama. "
            "Is it running? Start with: ollama serve"
        )

    # Check if target model is already loaded (matcher handles the "model:tag" format)
    running_names = [m.get("name", "") for m in running]
    target_loaded = any(_model_matches(name, model) for name in running_names)

    if target_loaded:
        return f"Model '{model}' is already loaded in VRAM. No action needed."

    # Validate target exists BEFORE evicting — prevents "evict then 404" bug.
    if err := await _check_model_exists(client, model):
        return err

    # Check if any currently loaded model has in-flight requests
    if running and not force:
        busy_models = []
        for m in running:
            name = m.get("name", "")
            # Check all name variations against in-flight tracker
            if client.is_busy(name) or client.is_busy(name.split(":")[0]):
                busy_models.append(name)

        if busy_models:
            return (
                f"Cannot warm '{model}': model(s) {', '.join(busy_models)} "
                f"have in-flight requests. Use force=True to override, "
                f"or wait for current requests to complete."
            )

    # Evict currently loaded model(s)
    evicted = []
    for m in running:
        name = m.get("name", "")
        try:
            await client.unload_model(name)
            evicted.append(name)
        except Exception as e:
            return f"Error evicting '{name}': {e}"

    # Send a trivial prompt to force-load the target model.
    # num_predict: 1 ensures minimal generation (just load the model).
    # keep_alive: 5m keeps it loaded for subsequent real calls.
    try:
        resp = await client._http.post(
            "/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "."}],
                "stream": False,
                "keep_alive": "5m",
                "options": {"num_predict": 1},
            },
            timeout=120,  # Cold load can take a while on 12GB GPU
        )
        resp.raise_for_status()
    except Exception as e:
        return f"Error loading '{model}': {e}"

    evict_msg = f" Evicted: {', '.join(evicted)}." if evicted else ""
    return f"Model '{model}' is now loaded and warm.{evict_msg}"


# ---------------------------------------------------------------------------
# Code-fence stripper (generate_code output cleanup)
# ---------------------------------------------------------------------------

def _strip_code_fences(content: str) -> str:
    """Remove markdown code fences that models sometimes wrap generated code in.

    Handles opening fences with or without a language tag (```python, ```, etc.)
    and a matching closing fence. Content without fences is returned unchanged.
    Uses splitlines(keepends=True) to preserve original line endings exactly.
    """
    lines = content.splitlines(keepends=True)
    if not lines:
        return content
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].rstrip() == "```":
        lines = lines[:-1]
    return "".join(lines)


# ---------------------------------------------------------------------------
# Shared error handler
# ---------------------------------------------------------------------------

def _format_error(e: Exception) -> str:
    """Convert Ollama exceptions to user-friendly error strings."""
    if isinstance(e, OllamaConnectionError):
        return (
            "Error: Cannot connect to Ollama. "
            "Is it running? Start with: ollama serve"
        )
    if isinstance(e, OllamaModelNotFoundError):
        return (
            f"Error: Model not found. "
            f"Available models: {', '.join(MODELS)}"
        )
    if isinstance(e, OllamaTimeoutError):
        return (
            "Error: Ollama timed out. The model may be loading (cold start). "
            "Try again in a few seconds."
        )
    return f"Error: {e}"


# ---------------------------------------------------------------------------
# Specialized tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def generate_code(
    prompt: str,
    language: str | None = None,
    model: str | None = None,
    context_files: list[ContextFile] | None = None,
    refs: list[str] | None = None,
    refs_root: str | None = None,
    output_file: str | None = None,
    output_only: bool = False,
    timeout: int = 120,
) -> str:
    """Generate code using a local Ollama model with smart persona routing.

    Automatically selects the best persona based on the target language
    using the persona registry. Examples:
    - Java → my-java-q3, Go → my-go-q3, Python → my-python-q3
    - React → my-react-q3, Rust → my-rust-async-q3
    - HTML/JS/CSS → my-creative-coder-q3 (browser/Canvas specialist)
    - Other languages → my-codegen-q3 (general-purpose fallback)

    An explicit model parameter overrides the automatic routing.

    Args:
        prompt: What code to generate (e.g., "binary search function").
        language: Target programming language (e.g., "python", "rust").
                  Used for persona routing and prepended as a hint to the prompt.
                  If omitted, the model infers the language from context.
        model: Override automatic persona routing with a specific model name.
        context_files: Existing files to inject into the prompt server-side.
                       Each entry requires an absolute `path`; optional
                       `start_line` and `end_line` (1-based, inclusive) select
                       a slice. Content is prepended as fenced code blocks —
                       avoids passing file content through Claude's context
                       (saves tokens). Use for "modify this existing file" tasks.
        refs: Reference keys to resolve and inject as documentation context.
              Each key must match a <!-- ref:KEY --> marker in a *.md file under
              refs_root. Resolved content is prepended as a <refs> block before
              the prompt — no Claude token cost. Use ref_lookup(key="list") to
              see available keys in a folder.
        refs_root: Folder to search for ref markers (any folder with *.md files
                   using <!-- ref:KEY --> convention). Defaults to REPO_ROOT.
                   Must be an absolute path. Pass any project folder to look up
                   its own refs.
        output_file: Path to write the response to (relative or absolute).
                     Relative paths are resolved from REPO_ROOT. Parent directories
                     are created automatically. Content is always returned to the
                     caller as well, unless output_only=True.
        output_only: If True and output_file is set, write to file and return only
                     a compact status string ("Written N bytes to /path") instead
                     of the full response. Defers verdict assessment to after file
                     inspection. Ignored if output_file is not set.
        timeout: Max seconds to wait for a response. Default 120. Increase for
                 large models (30B+) or complex prompts (e.g., 300 for hybrid models).

    Returns:
        Generated code (typically in a fenced code block). Returns an error
        message string if Ollama is unreachable.
    """
    t0 = time.perf_counter()
    debug_log.debug(
        "tool_enter",
        tool="generate_code",
        language=language,
        model=model,
        output_file=output_file,
        output_only=output_only,
        timeout=timeout,
        prompt_chars=len(prompt),
    )

    def _done(ok: bool, **fields):
        debug_log.debug(
            "tool_exit",
            tool="generate_code",
            ok=ok,
            ms=round((time.perf_counter() - t0) * 1000, 2),
            **fields,
        )

    if output_file is not None:
        _pre = _resolve_output_path(output_file)
        if isinstance(_pre, str):
            _done(False, reason="resolve_failed")
            return _pre

    client = _get_client()

    # Determine which persona to use: explicit override > language route > default
    if model is not None:
        chosen_model = model
    elif language is not None:
        lang_key = language.lower()
        # Resolve aliases (js→javascript, ts→typescript, golang→go, etc.)
        lang_key = registry._LANGUAGE_ALIASES.get(lang_key, lang_key)
        # Merge: registry routes override fallback, but fallback fills gaps
        # (e.g., javascript/css → creative-coder not detectable from role text)
        routes = {**_FALLBACK_LANGUAGE_ROUTES, **registry.get_language_routes()}
        chosen_model = routes.get(lang_key, _DEFAULT_CODEGEN_MODEL)
    else:
        chosen_model = _DEFAULT_CODEGEN_MODEL

    # Prepend language hint so the persona knows what to generate; the hint must be
    # part of `base` so it lands innermost (<refs> → <context> → [Language] → prompt).
    base = f"[Language: {language}]\n{prompt}" if language else prompt

    full_prompt, prompt_err = await _assemble_prompt(base, context_files, refs, refs_root)
    if prompt_err is not None:
        _done(False, reason="prompt_assembly_error")
        return prompt_err

    try:
        response = await client.chat(
            prompt=full_prompt,
            model=chosen_model,
            think=False,
            timeout=timeout,
            tool="generate_code",
        )
        content = _strip_code_fences(response.content)
        if output_file:
            write_result = _write_output_file(_pre, content)
            if write_result.startswith("Error:"):
                _done(False, reason="write_failed", model=chosen_model)
                return write_result
            if output_only:
                _done(True, model=chosen_model, output_only=True, content_chars=len(content))
                return write_result
        _done(True, model=chosen_model, content_chars=len(content))
        return content
    except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError) as e:
        _done(False, reason=type(e).__name__, model=chosen_model)
        return _format_error(e)


@mcp.tool()
async def summarize(
    text: str,
    max_points: int | None = None,
    model: str = "my-summarizer-q3",
) -> str:
    """Summarize text into concise bullet points using a local Ollama model.

    The summarizer preserves facts, numbers, and conclusions from the source.
    Output is bullet points by default.

    Args:
        text: The text to summarize.
        max_points: Maximum number of bullet points. If omitted, the model
                    decides based on content length.
        model: Ollama model to use. Default: my-summarizer-q3.

    Returns:
        Bullet-point summary. Returns an error message string if Ollama
        is unreachable.
    """
    client = _get_client()

    # Build prompt with optional constraint
    if max_points is not None:
        prompt = f"Summarize the following text in at most {max_points} bullet points:\n\n{text}"
    else:
        prompt = f"Summarize the following text:\n\n{text}"

    try:
        response = await client.chat(
            prompt=prompt,
            model=model,
            think=False,
            tool="summarize",
        )
        return response.content
    except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError) as e:
        return _format_error(e)


@mcp.tool()
async def classify_text(
    text: str,
    categories: list[str],
    model: str = "my-classifier-q3",
) -> str:
    """Classify text into one of the provided categories using a local Ollama model.

    Uses grammar-constrained decoding (Ollama's format parameter) to guarantee
    valid JSON output with the category restricted to the provided list.

    Args:
        text: The text to classify.
        categories: List of valid category names (e.g., ["food", "transport", "housing"]).
                    The model must pick exactly one.
        model: Ollama model to use. Default: my-classifier-q3.

    Returns:
        JSON string with keys: category, confidence (0.0-1.0), reasoning.
        Returns an error message string if Ollama is unreachable.
    """
    client = _get_client()

    # Build dynamic JSON schema — the enum constrains the model's output
    # to only the provided categories via grammar-constrained decoding.
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": categories,
            },
            "confidence": {
                "type": "number",
            },
            "reasoning": {
                "type": "string",
            },
        },
        "required": ["category", "confidence", "reasoning"],
    }

    prompt = (
        f"Classify the following text into one of these categories: "
        f"{', '.join(categories)}.\n\n{text}"
    )

    try:
        response = await client.chat(
            prompt=prompt,
            model=model,
            format=schema,
            think=False,
            tool="classify_text",
        )
        return response.content
    except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError) as e:
        return _format_error(e)


@mcp.tool()
async def translate(
    text: str,
    target_language: str,
    source_language: str | None = None,
    model: str = "my-translator-q3",
) -> str:
    """Translate text to a target language using a local Ollama model.

    The translator preserves meaning, tone, and formatting. Outputs only the
    translated text with no preamble or explanation.

    Args:
        text: The text to translate.
        target_language: Language to translate into (e.g., "Spanish", "Japanese").
        source_language: Language of the input text. If omitted, the model
                         auto-detects the source language.
        model: Ollama model to use. Default: my-translator-q3.

    Returns:
        Translated text only. Returns an error message string if Ollama
        is unreachable.
    """
    client = _get_client()

    # Build prompt with language pair info
    if source_language:
        prompt = f"Translate the following text from {source_language} to {target_language}:\n\n{text}"
    else:
        prompt = f"Translate the following text to {target_language}:\n\n{text}"

    try:
        response = await client.chat(
            prompt=prompt,
            model=model,
            think=False,
            tool="translate",
        )
        return response.content
    except (OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError) as e:
        return _format_error(e)


# ---------------------------------------------------------------------------
# Persona tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def query_personas(
    language: str | None = None,
    domain: str | None = None,
    tier: str | None = None,
    name: str | None = None,
) -> str:
    """Query available Ollama personas from the registry.

    Returns matching personas as a JSON array. All filters are optional
    and combined with AND logic. With no filters, returns all active personas.

    Use this to discover which specialized personas exist before choosing
    a model for ask_ollama or generate_code.

    Args:
        language: Filter by language (e.g., "java", "python", "rust").
        domain: Filter by domain keyword in role (e.g., "frontend", "review", "architect").
        tier: Filter by tier ("full" = standalone persona, "bare" = host-tool controlled).
        name: Filter by substring in persona name (e.g., "coder", "architect").

    Returns:
        JSON array of matching personas with their attributes.
    """
    results = registry.query_personas(
        language=language,
        domain=domain,
        tier=tier,
        name=name,
    )

    if not results:
        return json.dumps({"message": "No personas match the given filters.", "filters": {
            k: v for k, v in {"language": language, "domain": domain, "tier": tier, "name": name}.items() if v
        }})

    return json.dumps(results, indent=2)


@mcp.tool()
async def detect_persona(path: str) -> str:
    """Analyze a codebase and return ranked persona matches.

    Scans the directory for language files, frameworks, and patterns, then
    matches against the persona registry. No LLM call — purely file-based
    analysis, so it completes in seconds.

    Args:
        path: Absolute path to the codebase root directory to analyze.

    Returns:
        JSON array of persona matches ranked by confidence, each with:
        persona_name, confidence, reason, base_model, role, tier.
        Returns an error message if the path doesn't exist or REPO_ROOT is not set.
    """
    if not REPO_ROOT:
        return "Error: LLM_REPO_ROOT not set — cannot locate detect-persona script."

    script = os.path.join(REPO_ROOT, "personas", "run-detect-persona.sh")
    if not os.path.isfile(script):
        return f"Error: Detection script not found at {script}"

    if not os.path.isdir(path):
        return f"Error: Directory not found: {path}"

    # create_subprocess_exec passes args as an array — no shell injection risk
    # (equivalent to Node's execFile, not exec).
    return await _run_script(
        [script, "--json-compact", path], timeout=30, label="detect-persona"
    )


@mcp.tool()
async def build_persona(
    description: str,
    codebase_path: str | None = None,
) -> str:
    """Propose a new persona spec from a natural-language description.

    Uses an LLM (my-persona-designer-q3) to analyze the description and
    generate a complete persona specification. This is read-only — it
    proposes a spec but does NOT create the persona. The user must review
    and approve before creation.

    Args:
        description: What the persona should do (e.g., "Rust async systems
                     programmer using Tokio and Axum").
        codebase_path: Optional path to a codebase for context. The builder
                       will analyze it to tailor the persona to the project.

    Returns:
        JSON object with proposed spec: persona_name, domain, language,
        temperature, role, constraints, output_format, tier.
        Returns an error message if REPO_ROOT is not set or the script fails.
    """
    if not REPO_ROOT:
        return "Error: LLM_REPO_ROOT not set — cannot locate build-persona script."

    script = os.path.join(REPO_ROOT, "personas", "run-build-persona.sh")
    if not os.path.isfile(script):
        return f"Error: Builder script not found at {script}"

    # Build argument list: --describe "..." --json-only --skip-refinement
    # create_subprocess_exec passes args as array — no shell injection risk.
    args = [script, "--describe", description, "--json-only", "--skip-refinement"]

    if codebase_path:
        if not os.path.isdir(codebase_path):
            return f"Error: Codebase directory not found: {codebase_path}"
        args.extend(["--codebase", codebase_path])

    return await _run_script(args, timeout=120, label="build-persona")


@mcp.tool()
async def create_persona(
    role: str,
    base_model: str,
    name: str | None = None,
    language: str | None = None,
    domain: str = "code",
    temperature: str = "balanced",
    constraints: list[str] | None = None,
    output_format: str | None = None,
    tier: str = "full",
    dry_run: bool = False,
) -> str:
    """Create an Ollama persona: generates a Modelfile, registers with Ollama, and updates the registry.

    This is the "execute" counterpart to build_persona (which only proposes).
    Use query_personas first to check for existing personas. Use copy_persona
    to port an existing persona to a different base model.

    Args:
        role: One-line role description (e.g., "Python 3.11+ developer specializing in FastAPI").
        base_model: Ollama model tag (e.g., "qwen3.5:9b", "qwen3:14b"). Must exist in models.yaml.
        name: Persona name (e.g., "my-python-q35"). If omitted, auto-derived from role + language + model
              using the naming convention in models.yaml (slug + model suffix).
        language: Language or framework (e.g., "python", "react"). Used for naming and routing.
        domain: Domain category (default "code"). Affects default constraints if none provided.
        temperature: Temperature preset: "deterministic" (0.1), "balanced" (0.3), or "creative" (0.7).
        constraints: List of constraint strings. Each is a separate MUST/MUST NOT rule. If omitted, domain defaults are used.
        output_format: FORMAT line for the SYSTEM prompt. If omitted, domain default is used.
        tier: "full" (with SYSTEM prompt) or "bare" (no SYSTEM, for host-tool use).
        dry_run: If True, show what would be created without writing files.

    Returns:
        Success message with persona name and Modelfile path, or dry-run preview.
    """
    if not REPO_ROOT:
        return "Error: LLM_REPO_ROOT not set — cannot locate create-persona script."

    script = os.path.join(REPO_ROOT, "personas", "run-create-persona.sh")
    if not os.path.isfile(script):
        return f"Error: Creation script not found at {script}"

    # create_subprocess_exec passes args as an array — no shell injection risk.
    cmd = [
        script, "--non-interactive",
        "--role", role,
        "--base-model", base_model,
        "--domain", domain,
        "--temperature", temperature,
        "--tier", tier,
    ]
    if name:
        cmd.extend(["--name", name])
    if language:
        cmd.extend(["--language", language])
    if constraints:
        for c in constraints:
            cmd.extend(["--constraint", c])
    if output_format:
        cmd.extend(["--output-format", output_format])
    if dry_run:
        cmd.append("--dry-run")

    def _reload_registry(_stdout: str) -> None:
        # Reload registry so subsequent queries see the new persona.
        if not dry_run and REGISTRY_PATH:
            registry.load_registry(REGISTRY_PATH)

    return await _run_script(
        cmd, timeout=60, label="create-persona", on_success=_reload_registry
    )


@mcp.tool()
async def copy_persona(
    source: str,
    base_model: str,
    name: str | None = None,
    dry_run: bool = False,
) -> str:
    """Copy an existing persona to a different base model.

    Reads the source persona's role, constraints, and output format from its
    Modelfile, then creates a new persona with the same system prompt on the
    target base model. Context size and naming suffix come from models.yaml.

    Args:
        source: Name of the existing persona to copy (e.g., "my-python-q3").
        base_model: Target Ollama model tag (e.g., "qwen3.5:9b", "qwen2.5-coder:14b").
        name: Name for the new persona. If omitted, auto-derived from source slug + model suffix.
        dry_run: If True, show what would be created without writing files.

    Returns:
        Success message with new persona details, or dry-run preview.
    """
    if not REPO_ROOT:
        return "Error: LLM_REPO_ROOT not set — cannot locate persona files."

    # Look up source persona in registry
    reg = registry.get_registry()
    if source not in reg:
        return f"Error: Source persona '{source}' not found in registry. Use query_personas to list available personas."

    source_attrs = reg[source]
    modelfile_rel = source_attrs.get("modelfile")
    if not modelfile_rel:
        return f"Error: Source persona '{source}' has no modelfile path in registry."

    modelfile_path = os.path.join(REPO_ROOT, modelfile_rel)
    if not os.path.isfile(modelfile_path):
        return f"Error: Source Modelfile not found at {modelfile_path}"

    # Parse the source Modelfile to extract SYSTEM prompt contents
    try:
        with open(modelfile_path, "r") as f:
            modelfile_content = f.read()
    except OSError as e:
        return f"Error reading source Modelfile: {e}"

    # Extract role, constraints, and format from SYSTEM block
    import re as re_mod
    system_match = re_mod.search(r'SYSTEM\s+"""(.+?)"""', modelfile_content, re_mod.DOTALL)
    if not system_match:
        return f"Error: Could not parse SYSTEM block from {modelfile_path}. Is this a 'bare' persona?"

    system_text = system_match.group(1).strip()

    # Parse ROLE line
    role_match = re_mod.search(r'^ROLE:\s*(.+)$', system_text, re_mod.MULTILINE)
    role = role_match.group(1).strip() if role_match else source_attrs.get("role", "")

    # Parse CONSTRAINTS block (lines starting with "- MUST")
    constraint_lines = re_mod.findall(r'^- (MUST.+)$', system_text, re_mod.MULTILINE)
    constraints = constraint_lines if constraint_lines else None

    # Parse FORMAT line
    format_match = re_mod.search(r'^FORMAT:\s*(.+)$', system_text, re_mod.MULTILINE)
    output_format = format_match.group(1).strip() if format_match else None

    # Detect language from source registry entry or role
    language = None
    role_lower = role.lower()
    for lang in ["python", "java", "go", "rust", "react", "angular", "bash", "shell"]:
        if lang in role_lower or lang in source.lower():
            language = lang
            break

    # Derive name if not provided: take slug from source, apply new model's suffix
    if not name:
        models_yaml_path = os.path.join(REPO_ROOT, "personas", "models.yaml")
        try:
            import yaml as yaml_mod
            with open(models_yaml_path) as f:
                models_config = yaml_mod.safe_load(f)
            model_info = models_config.get("models", {}).get(base_model)
            if not model_info:
                return f"Error: base_model '{base_model}' not found in models.yaml"
            suffix = model_info["name_suffix"]
        except Exception as e:
            return f"Error reading models.yaml: {e}"

        # Extract slug: my-python-q3 → python, my-go-q25c14 → go
        slug = source.removeprefix("my-")
        # Remove the old model suffix (try longest suffixes first to avoid partial matches)
        for old_suffix in ["-q3-30b", "-q3-q8", "-q3-14b", "-q35-27b", "-q25c14", "-qcoder", "-q35", "-q3", ""]:
            if old_suffix and slug.endswith(old_suffix):
                slug = slug[:-len(old_suffix)]
                break
        name = f"my-{slug}{suffix}"

    # Determine temperature from source
    source_temp = source_attrs.get("temperature", 0.3)
    temp_name = "balanced"
    if source_temp <= 0.1:
        temp_name = "deterministic"
    elif source_temp >= 0.7:
        temp_name = "creative"

    # Delegate to create_persona
    return await create_persona(
        role=role,
        base_model=base_model,
        name=name,
        language=language,
        domain="code",
        temperature=temp_name,
        constraints=constraints,
        output_format=output_format,
        tier=source_attrs.get("tier", "full"),
        dry_run=dry_run,
    )


@mcp.tool()
async def ref_lookup(key: str, path: str | None = None) -> str:
    """Look up a named reference block from the project's documentation index.

    The project uses a two-tier documentation system. Active reference blocks
    (<!-- ref:KEY --> markers in *.md files) hold concise, runtime-relevant
    content — model selection rules, persona inventory, bash wrapper lists,
    resume steps, etc. This tool retrieves a block by key without requiring
    file access or knowing which file it lives in.

    Pass key="list" to get all available keys.

    Args:
        key: The reference key to look up (e.g. "current-status", "bash-wrappers",
             "model-selection"). Pass "list" to enumerate all available keys.
        path: Absolute path to a different repo root to search instead of the
              default LLM repo. Use this to look up refs from another project
              (e.g. the expense reporter repo). The target repo must contain
              *.md files with <!-- ref:KEY --> markers.

    Returns:
        The content of the reference block, or a list of available keys if
        key is "list". Returns an error message if the key is not found or
        REPO_ROOT is not set.
    """
    if not REPO_ROOT:
        return "Error: LLM_REPO_ROOT not set — cannot locate ref-lookup script."

    script = os.path.join(REPO_ROOT, ".claude", "tools", "ref-lookup.sh")
    if not os.path.isfile(script):
        return f"Error: ref-lookup script not found at {script}"

    # Pass args as array — no shell involved, no injection risk.
    # key="list" maps to --list flag (exits 0); any other key is looked up directly.
    args = [script, "--list"] if key == "list" else [script, key]

    if path is not None:
        args += ["--root", path]

    return await _run_script(
        args,
        timeout=10,
        label="ref-lookup",
        on_error=lambda rc, out, err: (
            f"ref:'{key}' not found. Available keys: run ref_lookup(key='list')"
        ),
    )


@mcp.tool()
async def patch_file(
    path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    """Edit a file by exact string replacement — without reading it into Claude's context.

    Use this when the file was just generated by generate_code / output_file and you
    already know its content. Zero Claude token cost for the read step.

    When to use vs the Edit tool:
    - patch_file: file was just generated; you know exactly what's in it; no prior Read.
    - Edit tool: file already existed; you read it during orientation.

    replace_all semantics:
    - False (default): exactly one occurrence must exist — errors if 0 or >1.
      Prevents accidental mass-changes and forces a specific old_string.
    - True: replaces every occurrence; succeeds with count >= 1.

    Args:
        path: Absolute or relative path to the file (relative resolves from REPO_ROOT).
        old_string: Exact string to find in the file.
        new_string: Replacement string.
        replace_all: Replace all occurrences instead of requiring uniqueness.

    Returns:
        "Patched {path} (N replacement/s)" on success, or an "Error: ..." string.
    """
    t0 = time.perf_counter()
    debug_log.debug(
        "tool_enter",
        tool="patch_file",
        path=path,
        replace_all=replace_all,
        old_len=len(old_string),
        new_len=len(new_string),
    )

    def _done(ok: bool, **fields):
        debug_log.debug(
            "tool_exit",
            tool="patch_file",
            ok=ok,
            ms=round((time.perf_counter() - t0) * 1000, 2),
            **fields,
        )

    resolved = _resolve_output_path(path)
    if isinstance(resolved, str):
        _done(False, reason="resolve_failed")
        return resolved

    try:
        if not resolved.is_file():
            _done(False, reason="not_found", resolved=str(resolved))
            return f"Error: file not found: {resolved}"

        content = resolved.read_text(encoding="utf-8")
        count = content.count(old_string)

        if count == 0:
            _done(False, reason="old_string_absent", resolved=str(resolved))
            return f"Error: old_string not found in {resolved}."
        if count > 1 and not replace_all:
            _done(False, reason="non_unique", resolved=str(resolved), count=count)
            return (
                f"Error: old_string found {count} times in {resolved}. "
                "Use replace_all=True to replace all, or provide a more specific old_string."
            )

        new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)

        tmp = pathlib.Path(str(resolved) + ".tmp")
        tmp.write_text(new_content, encoding="utf-8")
        os.replace(tmp, resolved)

        _done(True, resolved=str(resolved), count=count)
        return f"Patched {resolved} ({count} replacement{'s' if count != 1 else ''})"
    except OSError as e:
        _done(False, reason="oserror", error=str(e))
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# oficina — async local-model deliverable runs (P1)
# ---------------------------------------------------------------------------

@mcp.tool()
async def submit_run(spec: dict) -> str:
    """Submit an async local-model deliverable run.

    Returns immediately (never blocks on the GPU) — a detached worker runs the
    generation. Poll with run_status, fetch the outcome with run_result.

    Args:
        spec: The run spec — deliverable {kind: file|answer, target?}, objective,
              optional context {files, refs}, model, timeout_s, workspace.

    Returns:
        JSON {run_id, watch_cmd, queue_position}, or an "Error: ..." string.
    """
    try:
        result = oficina_service.submit(oficina_config.default_root(), spec)
        return json.dumps(result)
    except oficina_service.SpecShapeError as e:
        return f"Error: invalid spec — {e}"


@mcp.tool()
async def run_status(run_id: str, since_offset: int = 0) -> str:
    """Poll a run's state/phase and the events at or after since_offset (0-based).

    Args:
        run_id: The run to inspect.
        since_offset: Return only events with offset >= this (for incremental polling).

    Returns:
        JSON {state, phase, events, next_offset}, or an "Error: ..." string.
    """
    try:
        result = oficina_service.status(oficina_config.default_root(), run_id, since_offset)
        return json.dumps(result)
    except UnknownRunError:
        return f"Error: unknown run_id {run_id!r}"


@mcp.tool()
async def run_result(run_id: str) -> str:
    """Fetch a terminal run's report + deliverable location.

    Distinguishes unknown run_id, not-terminal-yet, and artifacts-pruned (the
    report is still returned when the workspace has been pruned).

    Args:
        run_id: The run whose result to fetch.

    Returns:
        JSON {state, report, deliverable, artifacts_pruned}, or an "Error: ..." string.
    """
    try:
        result = oficina_service.result(oficina_config.default_root(), run_id)
        return json.dumps(result)
    except UnknownRunError:
        return f"Error: unknown run_id {run_id!r}"
    except oficina_service.RunNotTerminalError as e:
        return f"Error: run not terminal yet — {e}"


@mcp.tool()
async def cancel_run(run_id: str) -> str:
    """Request cooperative cancellation of a run.

    Writes the cancel flag and returns the current state immediately — the
    Cancelled event lands when the worker next checks between stages.

    Args:
        run_id: The run to cancel.

    Returns:
        JSON {state}, or an "Error: ..." string.
    """
    try:
        result = oficina_service.cancel(oficina_config.default_root(), run_id)
        return json.dumps(result)
    except UnknownRunError:
        return f"Error: unknown run_id {run_id!r}"
