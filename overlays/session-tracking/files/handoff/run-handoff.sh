#!/usr/bin/env bash
# Whitelist-safe entrypoint for the session-handoff pipeline.
#
# Engine resolution, in order (R-D9 — code ships as a package, config as an overlay):
#   1. `st-handoff` on PATH     — the installed package (uv tool / pipx). Preferred.
#   2. a sibling src/ tree      — the overlay source checkout, so the dev home repo
#                                 tests against source without installing.
#   3. ~/.claude/tools/handoff/ — LEGACY flat-module copy from the pre-package
#                                 installer. Transitional: keeps consumer repos working
#                                 until the package is installed there. Remove once
#                                 every repo is migrated.
#
# The shim is the stable per-repo seam: migrating the engine changes only this file.
#
# Registry guard: no-ops silently in repos that have no handoff registry, so the
# user-level hook is safe in uninstalled repos. An explicit --registry (the
# home-repo / overlay-source invocation) bypasses the guard.
set -euo pipefail
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_root="$(git rev-parse --show-toplevel 2>/dev/null)" || _root="$PWD"

# An explicit --registry ("--registry path" or "--registry=path") bypasses the
# per-repo registry-file guard.
_explicit_registry=0
for _arg in "$@"; do
  case "$_arg" in
    --registry|--registry=*) _explicit_registry=1; break ;;
  esac
done
if [ "$_explicit_registry" -eq 0 ]; then
  [ -f "$_root/.claude/handoff/registry.yaml" ] || exit 0
fi

# 1. Installed package.
if command -v st-handoff >/dev/null 2>&1; then
  exec st-handoff "$@"
fi

# 2. Overlay source checkout: this shim sits at <overlay>/files/handoff/, so the
#    package source is two levels up, in src/.
_src="$(cd "$_here/../.." >/dev/null 2>&1 && pwd)/src"
if [ -d "$_src/sessiontracking" ]; then
  exec env PYTHONPATH="$_src${PYTHONPATH:+:$PYTHONPATH}" python3 -m sessiontracking.handoff.cli "$@"
fi

# 3. Legacy flat-module install (pre-package). Transitional.
_legacy="$HOME/.claude/tools/handoff/handoff.py"
if [ -f "$_legacy" ]; then
  exec python3 "$_legacy" "$@"
fi

echo "session-handoff: no engine found. Install the package:" >&2
echo "  uv tool install --editable <llm-repo>/overlays/session-tracking" >&2
exit 127
