# Makefile for the ollama-bridge MCP server.
# Diagnostic helpers — the server itself is launched by Claude Code via
# run-server.sh; these targets are for observing it.

LOG_FILE ?= /tmp/ollama-bridge.jsonl
SCRIPTS  := scripts

.PHONY: help logs logs-raw bridges

help:
	@echo "ollama-bridge — diagnostic targets"
	@echo
	@echo "  make logs                  Tail $(LOG_FILE) with pretty formatting"
	@echo "  make logs CLIENT=abcd1234  Tail filtered to one bridge's client_id"
	@echo "  make logs-raw              Tail $(LOG_FILE) as raw JSONL (for grep/jq)"
	@echo "  make bridges               List live bridge processes with banner info"
	@echo
	@echo "Override the log path: make logs LOG_FILE=/path/to/file.jsonl"

logs:
	@OLLAMA_BRIDGE_LOG_FILE=$(LOG_FILE) $(SCRIPTS)/watch-logs.sh $(CLIENT)

logs-raw:
	@tail -F $(LOG_FILE)

bridges:
	@OLLAMA_BRIDGE_LOG_FILE=$(LOG_FILE) $(SCRIPTS)/which-bridge.sh
