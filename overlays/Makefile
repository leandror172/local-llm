# Makefile for overlay development tasks.
# Test targets run each overlay's own test suite. Suites are hermetic
# (self-contained fixtures), so they pass from any checkout — no repo coupling.
#
# Add new overlays as `test-<overlay>` targets and wire them into `test`.

# Directory of this Makefile, so targets work regardless of invocation dir
# (`make -C overlays test`, `cd overlays && make test`, etc.).
HERE := $(dir $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: help test test-ref-indexing

help:
	@echo "overlays — development targets"
	@echo
	@echo "  make test               Run every overlay's test suite"
	@echo "  make test-ref-indexing  Hermetic tests for ref-lookup.sh (ref-indexing overlay)"

## test: run all overlay test suites (extend as overlays gain tests)
test: test-ref-indexing

## test-ref-indexing: hermetic tests for the ref-indexing overlay
test-ref-indexing:
	@$(HERE)ref-indexing/files/tests/test-ref-lookup-paths.sh
