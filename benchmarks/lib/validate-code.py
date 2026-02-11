#!/usr/bin/env python3
"""Validate LLM-generated code files using native compilers/linters.

Scaffolds code snippets into compilable units (adds package declaration,
main function if missing), compiles, runs static analysis, and reports
results as JSON matching the validate-html.js contract.

Supported languages:
  - Go: go build + go vet

Usage:
  python3 lib/validate-code.py [options] <file1.go> [file2.go ...]

Options:
  --timeout <sec>   Max compile time per file (default: 30)
  --quiet           JSON only to stdout, no progress on stderr
  --keep-temp       Keep temp compilation directories (debugging)

Exit codes:
  0 = all files pass (no errors)
  1 = one or more files have errors
  2 = tool error (missing files, missing compiler, etc.)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description='Validate LLM-generated code via compilation + static analysis')
    p.add_argument('files', nargs='+', help='Code files to validate')
    p.add_argument('--timeout', type=int, default=30,
                   help='Max compile time per file in seconds (default: 30)')
    p.add_argument('--quiet', action='store_true',
                   help='JSON only to stdout, suppress progress on stderr')
    p.add_argument('--keep-temp', action='store_true',
                   help='Keep temp compilation directories (debugging)')
    return p.parse_args()


# ---------------------------------------------------------------------------
# Go scaffolding
# ---------------------------------------------------------------------------

def scaffold_go(source_lines):
    """Scaffold raw Go code into a compilable unit.

    Returns (scaffolded_lines, line_mapping) where line_mapping maps
    scaffolded line numbers (1-based) to original line numbers (1-based).
    Original lines get their real number; injected lines map to 0.
    """
    scaffolded = []
    line_mapping = []  # index i = scaffolded line i+1, value = original line or 0

    has_package = any(re.match(r'^\s*package\s+\w+', line) for line in source_lines)
    has_main = any(re.match(r'^\s*func\s+main\s*\(', line) for line in source_lines)

    # Prepend package declaration if missing
    if not has_package:
        scaffolded.append('package main\n')
        line_mapping.append(0)
        scaffolded.append('\n')
        line_mapping.append(0)

    # Copy original source, tracking line numbers
    for i, line in enumerate(source_lines):
        scaffolded.append(line)
        line_mapping.append(i + 1)  # 1-based original line

    # Append main() if missing
    if not has_main:
        scaffolded.append('\n')
        line_mapping.append(0)
        scaffolded.append('func main() {}\n')
        line_mapping.append(0)

    return scaffolded, line_mapping


def map_line_to_original(scaffolded_line, line_mapping):
    """Convert a scaffolded line number (1-based) to the original line number.

    Returns the original line number, or None if the line was injected.
    """
    idx = scaffolded_line - 1
    if 0 <= idx < len(line_mapping):
        orig = line_mapping[idx]
        return orig if orig > 0 else None
    return None


# ---------------------------------------------------------------------------
# Go error parsing
# ---------------------------------------------------------------------------

# Pattern: ./main.go:15:2: error message
GO_ERROR_RE = re.compile(r'^.*?:(\d+):\d+:\s*(.+)$')


def classify_go_error(text):
    """Classify a Go compiler error by its message text."""
    t = text.lower()
    if 'undefined:' in t or 'undefined name' in t:
        return 'undefined_reference'
    if 'syntax error' in t or 'expected' in t:
        return 'syntax_error'
    if 'cannot use' in t or 'type ' in t or 'cannot convert' in t:
        return 'type_error'
    if 'imported and not used' in t:
        return 'unused_import'
    return 'compile_error'


def parse_go_output(stderr_text, line_mapping, is_vet=False):
    """Parse go build or go vet stderr into structured error/warning dicts."""
    items = []
    for raw_line in stderr_text.strip().splitlines():
        raw_line = raw_line.strip()
        if not raw_line or raw_line.startswith('#'):
            continue

        m = GO_ERROR_RE.match(raw_line)
        if m:
            scaffolded_line = int(m.group(1))
            message = m.group(2)

            original_line = map_line_to_original(scaffolded_line, line_mapping)

            if is_vet:
                error_type = 'vet_warning'
            else:
                error_type = classify_go_error(message)

            items.append({
                'type': error_type,
                'text': message,
                'line': original_line,
            })
        elif not raw_line.startswith('exit status'):
            # Capture non-pattern errors (rare but possible)
            items.append({
                'type': 'vet_warning' if is_vet else 'compile_error',
                'text': raw_line,
                'line': None,
            })

    return items


# ---------------------------------------------------------------------------
# Go validation
# ---------------------------------------------------------------------------

def validate_go(file_path, timeout, keep_temp):
    """Validate a single Go file. Returns a result dict."""
    basename = os.path.basename(file_path)
    abs_path = os.path.abspath(file_path)
    start_time = time.time()

    # Read source
    try:
        with open(abs_path) as f:
            source_lines = f.readlines()
    except (OSError, IOError) as e:
        return {
            'file': basename,
            'path': abs_path,
            'status': 'fail',
            'errors': [{'type': 'io_error', 'text': str(e), 'line': None}],
            'warnings': [],
            'error_count': 1,
            'warning_count': 0,
            'load_time_ms': int((time.time() - start_time) * 1000),
            'validated_at': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
        }

    # Scaffold
    scaffolded_lines, line_mapping = scaffold_go(source_lines)

    # Write to temp directory
    temp_dir = tempfile.mkdtemp(prefix='validate-go-')
    temp_file = os.path.join(temp_dir, 'main.go')
    try:
        with open(temp_file, 'w') as f:
            f.writelines(scaffolded_lines)

        # Initialize go module (required since Go 1.16 default module mode)
        subprocess.run(
            ['go', 'mod', 'init', 'validate-temp'],
            cwd=temp_dir,
            capture_output=True,
            timeout=10,
        )

        errors = []
        warnings = []

        # Step 1: go build
        try:
            build_result = subprocess.run(
                ['go', 'build', '-o', '/dev/null', './'],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if build_result.returncode != 0:
                parsed = parse_go_output(build_result.stderr, line_mapping, is_vet=False)
                # Separate unused_import (warning-level) from real errors
                for item in parsed:
                    if item['type'] == 'unused_import':
                        warnings.append(item)
                    else:
                        errors.append(item)
        except subprocess.TimeoutExpired:
            errors.append({
                'type': 'timeout',
                'text': f'go build timed out after {timeout}s',
                'line': None,
            })
        except FileNotFoundError:
            return _tool_error('go compiler not found — install Go first')

        # Step 2: go vet (only if build succeeded with no real errors)
        if not errors:
            try:
                vet_result = subprocess.run(
                    ['go', 'vet', './'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if vet_result.returncode != 0:
                    vet_items = parse_go_output(
                        vet_result.stderr, line_mapping, is_vet=True)
                    warnings.extend(vet_items)
            except subprocess.TimeoutExpired:
                warnings.append({
                    'type': 'vet_warning',
                    'text': f'go vet timed out after {timeout}s',
                    'line': None,
                })
            except FileNotFoundError:
                pass  # go vet not found is non-fatal

        load_time_ms = int((time.time() - start_time) * 1000)
        status = 'fail' if errors else 'pass'

        return {
            'file': basename,
            'path': abs_path,
            'status': status,
            'errors': errors,
            'warnings': warnings,
            'error_count': len(errors),
            'warning_count': len(warnings),
            'load_time_ms': load_time_ms,
            'validated_at': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
        }

    finally:
        if not keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            print(f'  temp dir kept: {temp_dir}', file=sys.stderr)


# ---------------------------------------------------------------------------
# Language dispatch
# ---------------------------------------------------------------------------

VALIDATORS = {
    '.go': validate_go,
}


def detect_validator(file_path):
    """Return the appropriate validator function for a file, or None."""
    ext = os.path.splitext(file_path)[1].lower()
    return VALIDATORS.get(ext)


# ---------------------------------------------------------------------------
# Tool error helper
# ---------------------------------------------------------------------------

def _tool_error(message):
    """Print a tool error to stderr and exit with code 2."""
    print(f'Error: {message}', file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # Validate file paths up front
    resolved = []
    for f in args.files:
        abs_path = os.path.abspath(f)
        if not os.path.isfile(abs_path):
            _tool_error(f'file not found: {abs_path}')
        validator = detect_validator(abs_path)
        if validator is None:
            ext = os.path.splitext(abs_path)[1]
            _tool_error(f'unsupported file type: {ext} (supported: {", ".join(VALIDATORS.keys())})')
        resolved.append((abs_path, validator))

    # Check that the compiler is available
    if any(ext == '.go' for ext in (os.path.splitext(p)[1] for p, _ in resolved)):
        if shutil.which('go') is None:
            _tool_error('go compiler not found in PATH — install Go first')

    results = []
    any_fail = False

    for file_path, validator in resolved:
        basename = os.path.basename(file_path)
        if not args.quiet:
            print(f'  validating: {basename} ... ', end='', file=sys.stderr, flush=True)

        result = validator(file_path, args.timeout, args.keep_temp)
        results.append(result)

        if result['status'] == 'fail':
            any_fail = True

        if not args.quiet:
            if result['status'] == 'pass':
                tag = 'PASS'
            else:
                tag = f'FAIL ({result["error_count"]} error(s))'
            print(f'{tag}  [{result["load_time_ms"]}ms]', file=sys.stderr)

    # Output JSON array to stdout
    print(json.dumps(results, indent=2))

    # Summary on stderr
    if not args.quiet:
        passed = sum(1 for r in results if r['status'] == 'pass')
        failed = sum(1 for r in results if r['status'] == 'fail')
        print(f'\n  {passed} passed, {failed} failed out of {len(results)} file(s)',
              file=sys.stderr)

    sys.exit(1 if any_fail else 0)


if __name__ == '__main__':
    main()
