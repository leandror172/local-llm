# Repo-root test entry point.
#
# Every target delegates to a script under the area it tests, so the same invocation
# works from make, a bare shell, or CI — and each command is defined in exactly one
# place. This mirrors overlays/Makefile, which established the convention.
#
# Counts are deliberately NOT stated in this help text. They were, in overlays/Makefile,
# and they drifted 100 tests before anyone ran the suite to check (T-136). Help says what
# runs; the run says how many.

# Directory of this Makefile, so targets work regardless of invocation dir.
HERE := $(dir $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: help test test-mcp test-overlays test-benchmarks test-hooks test-personas test-hf-space

help:
	@echo "llm — repo-wide test targets"
	@echo
	@echo "  make test                 Every suite, with a per-suite summary and a total"
	@echo
	@echo "  make test-mcp             ollama-bridge / oficina        (pytest, uv venv)"
	@echo "  make test-overlays        every overlay suite            (bash + pytest)"
	@echo "  make test-benchmarks      write-model benchmark instrument (pytest, model-free)"
	@echo "  make test-hooks           .claude/hooks scripts          (hermetic, bash+python)"
	@echo "  make test-personas        personas module                (pytest)"
	@echo "  make test-hf-space        engineer-profile Space app     (pytest, deps mocked)"
	@echo
	@echo "Pass args to one suite:     make test-mcp ARGS='-k refs'"
	@echo
	@echo "Not covered here (live model calls, not tests):"
	@echo "  make -C mcp-server accept-p4    P4 judge-gate acceptance, real Ollama, ~35 s"

## test: every suite; nonzero exit if any fails
test:
	@$(HERE)scripts/run-all-tests.sh

## test-mcp: the ollama-bridge / oficina pytest suite
test-mcp:
	@$(HERE)mcp-server/scripts/run-tests.sh $(ARGS)

## test-overlays: every overlay suite (ref-indexing, session-tracking, installer)
test-overlays:
	@$(HERE)overlays/scripts/run-all-tests.sh

## test-benchmarks: model-free unit tests for the write-model benchmark instrument
test-benchmarks:
	@$(HERE)benchmarks/lib/run-tests.sh $(ARGS)

## test-hooks: hermetic tests for the .claude/hooks scripts
test-hooks:
	@$(HERE).claude/hooks/tests/run-tests.sh

## test-personas: the personas module suite
test-personas:
	@$(HERE)personas/run-tests.sh $(ARGS)

## test-hf-space: the engineer-profile HF Space app (heavy deps mocked in conftest)
test-hf-space:
	@$(HERE)docs/portfolio/hf-space/run-tests.sh $(ARGS)
