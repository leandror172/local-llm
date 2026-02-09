#!/usr/bin/env python3
"""Extract HTML from an Ollama API JSON response.

Handles multiple output formats:
  1. ```html ... ``` code blocks (picks the longest)
  2. Any code block containing <html or <!DOCTYPE
  3. Raw HTML (response starts with <!DOCTYPE or <html)
  4. Inline HTML anywhere in the response

Strips Qwen3 <think>...</think> blocks before extraction.

Usage:
  python3 extract-html.py response.json output.html
  Exit code 0 = HTML extracted, 1 = no valid HTML found
"""

import json
import re
import sys


def strip_thinking(content):
    """Remove Qwen3 thinking blocks, return (cleaned_content, think_text)."""
    think_blocks = re.findall(r'<think>(.*?)</think>', content, re.DOTALL)
    cleaned = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    think_text = '\n'.join(think_blocks) if think_blocks else ''
    return cleaned, think_text


def extract_html(content):
    """Try multiple strategies to extract HTML from model output."""
    # Strategy 1: ```html blocks
    html_blocks = re.findall(r'```html\s*\n(.*?)```', content, re.DOTALL)
    if html_blocks:
        return max(html_blocks, key=len).strip()

    # Strategy 2: Any fenced block containing <html or <!DOCTYPE
    all_blocks = re.findall(r'```\w*\s*\n(.*?)```', content, re.DOTALL)
    for block in all_blocks:
        if '<html' in block.lower() or '<!doctype' in block.lower():
            return block.strip()

    # Strategy 3: Content itself is raw HTML
    if content.strip().lower().startswith(('<!doctype', '<html')):
        return content.strip()

    # Strategy 4: Find HTML document anywhere in content
    match = re.search(
        r'(<!DOCTYPE\s+html.*?</html>)',
        content, re.DOTALL | re.IGNORECASE
    )
    if match:
        return match.group(1).strip()

    return None


def validate_html(html):
    """Basic structural validation."""
    lower = html.lower()
    return '<html' in lower and '</html>' in lower


def main():
    if len(sys.argv) < 3:
        print("Usage: extract-html.py response.json output.html", file=sys.stderr)
        sys.exit(2)

    json_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(json_file) as f:
        data = json.load(f)

    content = data.get('message', {}).get('content', '')
    if not content:
        print("No content in response", file=sys.stderr)
        sys.exit(1)

    content, think_text = strip_thinking(content)

    html = extract_html(content)
    if html is None:
        print("No HTML found in response", file=sys.stderr)
        sys.exit(1)

    valid = validate_html(html)
    if not valid:
        print("Warning: extracted HTML may be incomplete", file=sys.stderr)

    with open(output_file, 'w') as f:
        f.write(html)

    lines = html.count('\n') + 1
    print(f"{lines}|{'true' if valid else 'false'}")


if __name__ == '__main__':
    main()
