#!/usr/bin/env python3
"""
interactive.py — Reusable interactive input helpers.

Extracted from create-persona.py (Task 3.4 refactoring).
Provides generic prompting functions for CLI tools that need user interaction.

Used by:
  - personas/create-persona.py (interactive persona creator)
  - Future: Task 3.5 conversational persona builder
  - Future: Any CLI tool needing user input
"""

import sys


def ask(prompt: str, default: str | None = None) -> str:
    """
    Prompt for a single-line string. Shows default in brackets if provided.

    Args:
        prompt: Question to ask
        default: Default value if user presses Enter without typing

    Returns:
        User input (or default if provided and user presses Enter)
    """
    display = f"{prompt}"
    if default:
        display += f" [{default}]"
    display += ": "
    while True:
        try:
            value = input(display).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
        if value:
            return value
        if default is not None:
            return default
        print("  (required — please enter a value)")


def ask_choice(prompt: str, choices: list[str], default: str | None = None) -> str:
    """
    Numbered menu prompt. Returns the chosen string value.

    Args:
        prompt: Question to ask
        choices: List of option strings
        default: Default choice (if None, first choice becomes default)

    Returns:
        The selected choice string
    """
    print(f"\n{prompt}")
    for i, c in enumerate(choices, 1):
        marker = " (default)" if c == default else ""
        print(f"  {i}. {c}{marker}")
    while True:
        try:
            raw = input("  Choice [1]: " if default == choices[0] else "  Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
        if not raw and default is not None:
            return default
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            # Allow typing the value directly
            if raw in choices:
                return raw
        print(f"  Enter a number 1–{len(choices)}")


def ask_multiline(prompt: str, sentinel: str = ".") -> list[str]:
    """
    Collect lines until user enters sentinel. Returns list of non-empty strings.

    Args:
        prompt: Question to ask
        sentinel: String that signals end of input (default: ".")

    Returns:
        List of entered lines (non-empty strings)
    """
    print(f"{prompt} (one per line, '{sentinel}' when done, blank line to skip):")
    lines = []
    while True:
        try:
            line = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line == sentinel:
            break
        if line:
            lines.append(line)
    return lines


def ask_confirm(prompt: str, default: bool = True) -> bool:
    """
    Yes/no prompt. Returns bool.

    Args:
        prompt: Question to ask
        default: Default answer if user presses Enter

    Returns:
        True for yes, False for no
    """
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        try:
            raw = input(f"{prompt} {hint}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Please enter 'y' or 'n'")
