---
id: python-09-plugin-system
domain: python
difficulty: hard
timeout: 420
description: Plugin system with dynamic loading and interface enforcement
---

Implement a plugin system using `importlib` for dynamic loading.

1. Abstract base `TransformerPlugin(abc.ABC)`: `name` (property), `version` (property), `transform(data: str) -> str`, `validate(data: str) -> bool`

2. `PluginRegistry`:
   - `load_from_directory(path: str)` — scans `*.py`, loads subclasses of `TransformerPlugin`
   - `load_from_module(module_name: str)`
   - `register`, `get`, `list_plugins() -> list[PluginMeta]`, `unload`
   - Raises `PluginConflictError` on duplicate registration

3. `PluginPipeline(plugins: list[str], registry: PluginRegistry)`:
   - `execute(data: str) -> PipelineResult` — chains plugins, captures errors per step
   - `PipelineResult(output, steps: list[StepResult])`; `StepResult(plugin_name, input, output, duration_ms, error)`

4. Three example plugin files: uppercase, word-counter, JSON prettifier

Requirements: `importlib.util.spec_from_file_location`, thread-safe with `threading.RLock`, full type hints
