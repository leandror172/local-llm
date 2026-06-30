# Makefile for overlay development tasks.
# Test targets delegate to scripts/ runners, so the exact same invocation works
# from make, a bare shell, or CI. Every suite is hermetic (self-contained
# fixtures / monkeypatched $HOME), so they pass from any checkout — no repo
# coupling. Add a new overlay suite by dropping a scripts/test-<name>.sh runner,
# adding a target below, and listing it in scripts/run-all-tests.sh.

# Directory of this Makefile, so targets work regardless of invocation dir
# (`make -C overlays test`, `cd overlays && make test`, etc.).
HERE    := $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
SCRIPTS := $(HERE)scripts

.PHONY: help test test-ref-indexing test-session-tracking test-installer

help:
	@echo "overlays — test targets (196 tests total)"
	@echo
	@echo "  make test                   Run every overlay suite, print a summary"
	@echo "  make test-ref-indexing      ref-lookup.sh hermetic tests   (bash,   9)"
	@echo "  make test-session-tracking  handoff pipeline tests         (pytest, 174)"
	@echo "  make test-installer         installer --verify tests       (pytest, 13)"
	@echo
	@echo "Pass pytest args to one suite:  make test-session-tracking ARGS='-k harvest'"

## test: run all overlay test suites (summary + nonzero exit on any failure)
test:
	@$(SCRIPTS)/run-all-tests.sh

## test-ref-indexing: ref-indexing overlay (bash, hermetic)
test-ref-indexing:
	@$(SCRIPTS)/test-ref-indexing.sh $(ARGS)

## test-session-tracking: session-tracking handoff suite (pytest)
test-session-tracking:
	@$(SCRIPTS)/test-session-tracking.sh $(ARGS)

## test-installer: overlay installer --verify suite (pytest)
test-installer:
	@$(SCRIPTS)/test-installer.sh $(ARGS)
