#!/usr/bin/env python3
"""Run a decomposed visual prompt pipeline: stages execute sequentially,
each stage receives the previous stage's HTML output as context.

Usage:
  decomposed-run.py --model my-creative-coder-q3 --stages prompts/decomposed/01-bouncing-ball/
  decomposed-run.py --model my-creative-coder --stages prompts/decomposed/01-bouncing-ball/ --start 2
  decomposed-run.py --model my-creative-coder-q3 --stages prompts/decomposed/01-bouncing-ball/ --no-think
"""

import argparse, json, urllib.request, time, re, sys, os, glob, subprocess


def call_ollama(base_url, model, prompt, timeout, think):
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'stream': False,
    }
    if not think:
        payload['think'] = False

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f'{base_url}/api/chat', data=data,
        headers={'Content-Type': 'application/json'}
    )
    start = time.time()
    resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    wall = time.time() - start

    msg = resp.get('message', {})
    content = msg.get('content', '')
    eval_count = resp.get('eval_count', 0)
    eval_dur = resp.get('eval_duration', 0) / 1e9

    return {
        'content': content,
        'eval_count': eval_count,
        'eval_duration': round(eval_dur, 2),
        'wall_time': round(wall, 2),
        'tok_per_sec': round(eval_count / eval_dur, 1) if eval_dur > 0 else 0,
        'thinking_chars': len(msg.get('thinking') or ''),
    }


def extract_html(content):
    """Extract HTML from model response. Tries multiple patterns."""
    # Pattern 1: ```html ... ```
    m = re.search(r'```html\s*\n(.*?)```', content, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Pattern 2: <!DOCTYPE or <html at start of a line
    m = re.search(r'(<!DOCTYPE.*?</html>)', content, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Pattern 3: any ``` block
    m = re.search(r'```\s*\n(.*?)```', content, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Fallback: return everything (might work if model outputs raw HTML)
    return content.strip()


def validate_html(html_path):
    """Run headless browser validation on an HTML file. Returns dict or None."""
    script = os.path.join(os.path.dirname(__file__), 'validate-html.js')
    if not os.path.exists(script):
        return None
    try:
        result = subprocess.run(
            ['node', script, '--quiet', html_path],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        return data[0] if data else None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def main():
    p = argparse.ArgumentParser(description='Run decomposed visual prompt pipeline')
    p.add_argument('--model', required=True, help='Ollama model name')
    p.add_argument('--stages', required=True, help='Directory containing stage-N.md files')
    p.add_argument('--start', type=int, default=1, help='Stage to start from (default: 1)')
    p.add_argument('--inject', help='HTML file to use as previous output for --start > 1')
    p.add_argument('--timeout', type=int, default=300, help='Timeout per stage in seconds')
    p.add_argument('--url', default='http://localhost:11434', help='Ollama API URL')
    p.add_argument('--output-dir', help='Output directory (default: results/decomposed/<timestamp>)')
    p.add_argument('--no-think', action='store_true', help='Disable thinking mode')
    p.add_argument('--validate', action='store_true',
                   help='Run headless browser validation on each stage HTML')
    args = p.parse_args()

    # Find stage files
    stage_files = sorted(glob.glob(os.path.join(args.stages, 'stage-*.md')))
    if not stage_files:
        print(f'ERROR: No stage-*.md files found in {args.stages}')
        sys.exit(1)

    print(f'Pipeline: {len(stage_files)} stages in {args.stages}')
    print(f'Model: {args.model}, think: {not args.no_think}')
    print(f'Starting from stage {args.start}\n')

    # Output directory
    if args.output_dir:
        out_dir = args.output_dir
    else:
        ts = time.strftime('%Y-%m-%dT%H%M%S')
        pipeline_name = os.path.basename(os.path.normpath(args.stages))
        slug = args.model.replace(':', '-').replace('/', '-')
        out_dir = os.path.join('results', 'decomposed', f'{ts}_{pipeline_name}_{slug}')
    os.makedirs(out_dir, exist_ok=True)

    # Load initial previous output if resuming
    previous_html = ''
    if args.inject:
        with open(args.inject) as f:
            previous_html = f.read()
        print(f'Injected previous output from {args.inject} ({len(previous_html)} chars)\n')

    summary = []

    for stage_file in stage_files:
        stage_num = int(re.search(r'stage-(\d+)', stage_file).group(1))

        if stage_num < args.start:
            continue

        # Read prompt template
        with open(stage_file) as f:
            prompt_template = f.read().strip()

        # Inject previous output
        if '{{PREVIOUS_OUTPUT}}' in prompt_template:
            if not previous_html:
                print(f'ERROR: Stage {stage_num} requires {{PREVIOUS_OUTPUT}} but none available.')
                print(f'Use --inject to provide HTML from a previous run.')
                sys.exit(1)
            prompt = prompt_template.replace('{{PREVIOUS_OUTPUT}}', previous_html)
        else:
            prompt = prompt_template

        print(f'=== Stage {stage_num}: {os.path.basename(stage_file)} ===')
        print(f'    Prompt: {len(prompt)} chars (template: {len(prompt_template)}, injected: {len(previous_html)})')

        try:
            result = call_ollama(args.url, args.model, prompt, args.timeout, not args.no_think)
            html = extract_html(result['content'])

            print(f'    Tokens: {result["eval_count"]}, Wall: {result["wall_time"]}s, '
                  f'tok/s: {result["tok_per_sec"]}')
            print(f'    Output: {len(result["content"])} chars, HTML extracted: {len(html)} chars')
            if result['thinking_chars'] > 0:
                print(f'    Thinking: {result["thinking_chars"]} chars')

            # Save stage output
            html_path = os.path.join(out_dir, f'stage-{stage_num}.html')
            with open(html_path, 'w') as f:
                f.write(html)

            raw_path = os.path.join(out_dir, f'stage-{stage_num}-raw.txt')
            with open(raw_path, 'w') as f:
                f.write(result['content'])

            # Optional validation
            validation = None
            if args.validate:
                validation = validate_html(html_path)
                if validation:
                    vstatus = validation['status'].upper()
                    verrs = validation['error_count']
                    print(f'    Validation: {vstatus}' +
                          (f' ({verrs} error(s): {validation["errors"][0]["text"]})' if verrs else ''))
                else:
                    print(f'    Validation: SKIPPED (validator unavailable)')

            # Include validation in metadata
            meta = {
                'stage': stage_num,
                'model': args.model,
                'prompt_file': stage_file,
                'prompt_chars': len(prompt),
                'injected_chars': len(previous_html),
                **{k: v for k, v in result.items() if k != 'content'},
                'html_chars': len(html),
            }
            if validation is not None:
                meta['validation_status'] = validation['status']
                meta['validation_errors'] = validation['errors']
                meta['validation_warnings'] = validation['warnings']

            json_path = os.path.join(out_dir, f'stage-{stage_num}-meta.json')
            with open(json_path, 'w') as f:
                json.dump(meta, f, indent=2)

            previous_html = html
            stage_summary = {
                'stage': stage_num,
                'status': 'OK',
                'tokens': result['eval_count'],
                'wall_time': result['wall_time'],
                'tok_per_sec': result['tok_per_sec'],
                'html_chars': len(html),
            }
            if validation is not None:
                stage_summary['validation_status'] = validation['status']
                stage_summary['validation_error_count'] = validation['error_count']
            summary.append(stage_summary)
            print(f'    Saved: {html_path}')

        except Exception as e:
            print(f'    FAILED: {e}')
            summary.append({
                'stage': stage_num,
                'status': 'FAILED',
                'error': str(e),
            })
            break  # Don't continue pipeline on failure

        print()

    # Summary
    has_validation = any('validation_status' in s for s in summary)
    if has_validation:
        print(f'\n{"Stage":<8} {"Status":<8} {"Tokens":>8} {"Wall(s)":>8} {"tok/s":>7} {"HTML":>8} {"Valid":>6}')
        print('-' * 63)
    else:
        print(f'\n{"Stage":<8} {"Status":<8} {"Tokens":>8} {"Wall(s)":>8} {"tok/s":>7} {"HTML":>8}')
        print('-' * 55)
    for s in summary:
        if s['status'] == 'OK':
            line = (f'{s["stage"]:<8} {"OK":<8} {s["tokens"]:>8} {s["wall_time"]:>8} '
                    f'{s["tok_per_sec"]:>7} {s["html_chars"]:>8}')
            if has_validation:
                vs = s.get('validation_status', '?')
                line += f' {vs:>6}'
            print(line)
        else:
            print(f'{s["stage"]:<8} {"FAIL":<8} {s.get("error", "")[:40]}')

    print(f'\nOutput directory: {out_dir}')

    # Save summary
    with open(os.path.join(out_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)


if __name__ == '__main__':
    main()
