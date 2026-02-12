#!/usr/bin/env python3
"""Ollama API probe: A/B test API parameters on a single prompt.

Usage:
  ollama-probe.py --model my-coder-q3 --prompt "Write hello world in Go" --vary think=true,false
  ollama-probe.py --model my-coder-q3 --prompt-file prompts/backend/03-merge-intervals.md --vary think=true,false --timeout 300
  ollama-probe.py --model qwen3:8b --prompt "Explain monads" --vary model=qwen3:8b,qwen3:14b

Structured output (JSON schema):
  ollama-probe.py --model my-coder-q3 --prompt "Classify: subway $2.75" --format-file schema.json --vary format=on,off --no-think
"""

import argparse, json, urllib.request, time, re, sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / 'examples'


def parse_value(v):
    if v.lower() == 'true': return True
    if v.lower() == 'false': return False
    if v == '': return None
    try: return int(v)
    except ValueError: pass
    try: return float(v)
    except ValueError: pass
    return v


def strip_frontmatter(text):
    m = re.match(r'^---\s*\n.*?\n---\s*\n', text, re.DOTALL)
    return text[m.end():].strip() if m else text.strip()


def parse_example_sections(text):
    """Parse ## Input and ## Output sections from an example file."""
    body = strip_frontmatter(text)
    inp = re.search(r'## Input\s*\n(.*?)(?=\n## |\Z)', body, re.DOTALL)
    out = re.search(r'## Output\s*\n(.*?)(?=\n## |\Z)', body, re.DOTALL)
    if not inp or not out:
        return None
    return (inp.group(1).strip(), out.group(1).strip())


def discover_examples(spec):
    """Resolve example spec to list of file paths.
    If spec is 'backend' or 'visual', auto-discover from examples/<category>/.
    Otherwise, treat as comma-separated file paths."""
    category_dir = EXAMPLES_DIR / spec
    if category_dir.is_dir():
        return sorted(str(p) for p in category_dir.glob('*.md'))
    return [p.strip() for p in spec.split(',') if p.strip()]


def load_examples(paths):
    """Read example files, return list of (input, output) tuples."""
    examples = []
    for path in paths:
        text = open(path).read()
        parsed = parse_example_sections(text)
        if parsed:
            examples.append(parsed)
    return examples


def format_examples_prompt(examples, original_prompt):
    """Assemble few-shot examples + original prompt into one user message."""
    parts = ['EXAMPLES (follow these patterns):\n']
    for i, (inp, out) in enumerate(examples, 1):
        parts.append(f'Example {i}:')
        parts.append(f'User: {inp}')
        parts.append(f'Assistant:\n{out}\n')
    parts.append('---\nNow complete the following task:')
    parts.append(original_prompt)
    return '\n'.join(parts)


def call_ollama(base_url, model, prompt, extra_params, timeout):
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'stream': False,
        **extra_params
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f'{base_url}/api/chat', data=data,
        headers={'Content-Type': 'application/json'}
    )
    start = time.time()
    resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    wall = time.time() - start

    msg = resp.get('message', {})
    eval_count = resp.get('eval_count', 0)
    eval_dur = resp.get('eval_duration', 0) / 1e9

    content = msg.get('content', '')
    json_valid = False
    try:
        json.loads(content)
        json_valid = True
    except (json.JSONDecodeError, ValueError):
        pass

    return {
        'eval_count': eval_count,
        'eval_duration': round(eval_dur, 2),
        'wall_time': round(wall, 2),
        'tok_per_sec': round(eval_count / eval_dur, 1) if eval_dur > 0 else 0,
        'content_chars': len(content),
        'thinking_chars': len(msg.get('thinking') or ''),
        'prompt_tokens': resp.get('prompt_eval_count', 0),
        'json_valid': json_valid,
        'content_preview': content[:200],
    }


def main():
    p = argparse.ArgumentParser(description='A/B test Ollama API parameters')
    p.add_argument('--model', required=True)
    p.add_argument('--prompt', help='Prompt string')
    p.add_argument('--prompt-file', help='Prompt file (YAML frontmatter auto-stripped)')
    p.add_argument('--vary', required=True, help='key=val1,val2,...')
    p.add_argument('--timeout', type=int, default=300)
    p.add_argument('--url', default='http://localhost:11434')
    p.add_argument('--output', help='Save JSON results to file')
    p.add_argument('--format-file', help='JSON schema file for structured output (use with --vary format=on,off)')
    p.add_argument('--no-think', action='store_true', help='Disable thinking mode (adds think: false)')
    p.add_argument('--examples', help='Few-shot examples: category name (backend|visual) or comma-separated paths')
    args = p.parse_args()

    if not args.prompt and not args.prompt_file:
        p.error('Provide --prompt or --prompt-file')

    prompt = args.prompt
    if args.prompt_file:
        prompt = strip_frontmatter(open(args.prompt_file).read())

    if args.examples:
        paths = discover_examples(args.examples)
        examples = load_examples(paths)
        if examples:
            prompt = format_examples_prompt(examples, prompt)
            print(f'Loaded {len(examples)} few-shot examples ({len(prompt)} chars total)')

    key, vals_str = args.vary.split('=', 1)
    values = [parse_value(v) for v in vals_str.split(',')]

    results = {}
    for val in values:
        label = f'{key}={val}'
        print(f'>>> {label} ...', flush=True)

        model = args.model
        extra = {}
        if key == 'model':
            model = str(val)
        elif key == 'format' and args.format_file:
            if str(val).lower() in ('on', 'true', 'yes', '1'):
                with open(args.format_file) as f:
                    extra['format'] = json.load(f)
        elif val is not None:
            extra[key] = val

        if args.no_think:
            extra['think'] = False

        try:
            r = call_ollama(args.url, model, prompt, extra, args.timeout)
            results[label] = r
            print(f'    tokens={r["eval_count"]}, wall={r["wall_time"]}s, '
                  f'tok/s={r["tok_per_sec"]}, content={r["content_chars"]}ch, '
                  f'thinking={r["thinking_chars"]}ch')
        except Exception as e:
            results[label] = {'error': str(e)}
            print(f'    FAILED: {e}')

    print(f'\n{"Variant":<25} {"Tokens":>8} {"Wall(s)":>8} {"tok/s":>7} '
          f'{"Content":>10} {"Thinking":>10} {"JSON":>6}')
    print('-' * 85)
    for label, r in results.items():
        if 'error' in r:
            print(f'{label:<25} {"FAILED":>8}  {r["error"][:45]}')
        else:
            jv = 'OK' if r.get('json_valid') else '-'
            print(f'{label:<25} {r["eval_count"]:>8} {r["wall_time"]:>8} '
                  f'{r["tok_per_sec"]:>7} {r["content_chars"]:>10} '
                  f'{r["thinking_chars"]:>10} {jv:>6}')

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f'\nResults saved to {args.output}')


if __name__ == '__main__':
    main()
