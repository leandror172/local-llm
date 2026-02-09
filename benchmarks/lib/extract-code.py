#!/usr/bin/env python3
"""Extract code blocks from an Ollama API JSON response.

Infers the expected language from the prompt ID and extracts the most
relevant code block. Strips Qwen3 <think> blocks before extraction.

Usage:
  python3 extract-code.py response.json output_base prompt_id
  # Writes output_base.go, output_base.java, etc.
  Exit code 0 = code extracted, 1 = no code found
"""

import json
import re
import sys

# Map prompt ID patterns to expected languages and file extensions
LANG_MAP = {
    'go': ('go', '.go'),
    'java': ('java', '.java'),
    'python': ('python', '.py'),
    'rust': ('rust', '.rs'),
}


def strip_thinking(content):
    """Remove Qwen3 thinking blocks."""
    cleaned = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    return cleaned


def infer_language(prompt_id):
    """Guess the expected language from prompt ID."""
    pid = prompt_id.lower()
    if 'go-' in pid or 'go_' in pid:
        return 'go', '.go'
    if 'java-' in pid or 'java_' in pid:
        return 'java', '.java'
    if 'python-' in pid or 'python_' in pid:
        return 'python', '.py'
    return None, '.txt'


def extract_code(content, preferred_lang=None):
    """Extract the most relevant code block."""
    # Find all fenced code blocks with language tags
    blocks = re.findall(r'```(\w+)\s*\n(.*?)```', content, re.DOTALL)

    if preferred_lang and blocks:
        # Filter by preferred language
        lang_blocks = [(lang, code) for lang, code in blocks if lang == preferred_lang]
        if lang_blocks:
            longest = max(lang_blocks, key=lambda x: len(x[1]))
            return longest[1].strip(), longest[0]

    if blocks:
        # Return the longest code block
        longest = max(blocks, key=lambda x: len(x[1]))
        return longest[1].strip(), longest[0]

    # Try blocks without language tags
    untagged = re.findall(r'```\s*\n(.*?)```', content, re.DOTALL)
    if untagged:
        longest = max(untagged, key=len)
        return longest.strip(), preferred_lang or 'txt'

    return None, None


def main():
    if len(sys.argv) < 4:
        print("Usage: extract-code.py response.json output_base prompt_id", file=sys.stderr)
        sys.exit(2)

    json_file = sys.argv[1]
    output_base = sys.argv[2]
    prompt_id = sys.argv[3]

    with open(json_file) as f:
        data = json.load(f)

    content = data.get('message', {}).get('content', '')
    if not content:
        print("No content in response", file=sys.stderr)
        sys.exit(1)

    content = strip_thinking(content)

    preferred_lang, default_ext = infer_language(prompt_id)
    code, detected_lang = extract_code(content, preferred_lang)

    if code is None:
        print("No code found in response", file=sys.stderr)
        sys.exit(1)

    # Determine file extension
    ext = default_ext
    if detected_lang and detected_lang in LANG_MAP:
        ext = LANG_MAP[detected_lang][1]
    elif detected_lang:
        ext = f'.{detected_lang}'

    output_file = f"{output_base}{ext}"
    with open(output_file, 'w') as f:
        f.write(code)

    lines = code.count('\n') + 1
    print(f"{lines}|{detected_lang or 'unknown'}|{ext}")


if __name__ == '__main__':
    main()
