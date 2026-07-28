# Makefile for the ollama-bridge MCP server.
# Diagnostic + test helpers — the server itself is launched by Claude Code via
# run-server.sh; these targets are for observing and verifying it.

LOG_FILE ?= /tmp/ollama-bridge.jsonl
SCRIPTS  := scripts

.PHONY: help logs logs-raw bridges test test-oficina accept-p4

help:
	@echo "ollama-bridge — diagnostic + test targets"
	@echo
	@echo "  make test                  Run the full pytest suite (uv run pytest tests/)"
	@echo "  make test-oficina          Run only the oficina suite (tests/oficina/)"
	@echo "  make test ARGS='-k refs'   Pass pytest args through (any test target)"
	@echo
	@echo "  make accept-p4             Live P4 judge-gate acceptance (real Ollama calls, ~1 min)"
	@echo "  make accept-p4 CASES='A1'  Narrow it to named cases (A1 A2 A5)"
	@echo
	@echo "  make logs                  Tail $(LOG_FILE) with pretty formatting"
	@echo "  make logs CLIENT=abcd1234  Tail filtered to one bridge's client_id"
	@echo "  make logs-raw              Tail $(LOG_FILE) as raw JSONL (for grep/jq)"
	@echo "  make bridges               List live bridge processes with banner info"
	@echo
	@echo "Override the log path: make logs LOG_FILE=/path/to/file.jsonl"

test:
	uv run pytest tests/ $(ARGS)

test-oficina:
	uv run pytest tests/oficina/ $(ARGS)

accept-p4:
	@./run-acceptance-p4.sh $(CASES)

logs:
	@OLLAMA_BRIDGE_LOG_FILE=$(LOG_FILE) $(SCRIPTS)/watch-logs.sh $(CLIENT)

logs-raw:
	@tail -F $(LOG_FILE)

bridges:
	@OLLAMA_BRIDGE_LOG_FILE=$(LOG_FILE) $(SCRIPTS)/which-bridge.sh
