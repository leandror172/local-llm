#!/usr/bin/env python3
"""
detect-persona.py — Analyze a codebase to detect appropriate Ollama personas.

Analyzes file extensions, import statements, and config files to determine
what language/framework a codebase uses, then queries the persona registry
to recommend the most appropriate persona(s).

Usage (as library):
  from personas.detect_persona import detect
  results = detect('/path/to/codebase')
  print(f"Top persona: {results[0]['persona_name']}")

Usage (CLI):
  python3 personas/detect-persona.py /path/to/codebase
  python3 personas/detect-persona.py --verbose /path/to/codebase
  python3 personas/detect-persona.py --json-compact /path/to/codebase

Exit codes:
  0 = success (detected personas or fallback)
  1 = invalid path or permission denied
  2 = no code files found
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ──────────────────────────────────────────────────────────────────────────────
# File extension signals (50% weight)
# ──────────────────────────────────────────────────────────────────────────────

EXTENSION_SIGNALS = {
    # Backend languages
    '.java': {'lang': 'java', 'category': 'backend', 'strength': 1.0},
    '.go': {'lang': 'go', 'category': 'backend', 'strength': 1.0},
    '.py': {'lang': 'python', 'category': 'backend', 'strength': 0.9},
    '.rs': {'lang': 'rust', 'category': 'backend', 'strength': 1.0},

    # Frontend languages (TypeScript/React preferred over plain JS)
    '.tsx': {'lang': 'typescript', 'framework': 'react', 'strength': 1.0},
    '.jsx': {'lang': 'javascript', 'framework': 'react', 'strength': 0.9},
    '.ts': {'lang': 'typescript', 'category': 'frontend', 'strength': 0.7},
    '.js': {'lang': 'javascript', 'category': 'frontend', 'strength': 0.5},  # ambiguous
    '.html': {'lang': 'html', 'category': 'frontend', 'strength': 0.3},  # weak signal
    '.css': {'lang': 'css', 'category': 'frontend', 'strength': 0.2},  # weak signal

    # Infrastructure/scripting
    '.sh': {'lang': 'bash', 'category': 'scripting', 'strength': 1.0},
    '.bash': {'lang': 'bash', 'category': 'scripting', 'strength': 1.0},
    '.yml': {'lang': 'yaml', 'category': 'config', 'strength': 0.3},
    '.yaml': {'lang': 'yaml', 'category': 'config', 'strength': 0.3},

    # Other languages
    '.cpp': {'lang': 'cpp', 'category': 'backend', 'strength': 0.9},
    '.c': {'lang': 'c', 'category': 'backend', 'strength': 0.8},
    '.rb': {'lang': 'ruby', 'category': 'backend', 'strength': 0.9},
    '.php': {'lang': 'php', 'category': 'backend', 'strength': 0.8},
}

# ──────────────────────────────────────────────────────────────────────────────
# Import patterns (30% weight)
# Language-specific regex patterns to detect frameworks
# ──────────────────────────────────────────────────────────────────────────────

IMPORT_PATTERNS = {
    # Python frameworks
    r'^\s*import\s+fastapi': {'lang': 'python', 'framework': 'fastapi', 'strength': 0.95},
    r'^\s*from\s+fastapi\s+import': {'lang': 'python', 'framework': 'fastapi', 'strength': 0.95},
    r'^\s*import\s+flask': {'lang': 'python', 'framework': 'flask', 'strength': 0.9},
    r'^\s*from\s+flask\s+import': {'lang': 'python', 'framework': 'flask', 'strength': 0.9},
    r'^\s*import\s+django': {'lang': 'python', 'framework': 'django', 'strength': 0.9},
    r'^\s*import\s+pandas': {'lang': 'python', 'category': 'data-science', 'strength': 0.7},
    r'^\s*import\s+numpy': {'lang': 'python', 'category': 'data-science', 'strength': 0.7},

    # Java frameworks
    r'^\s*import\s+org\.springframework': {'lang': 'java', 'framework': 'spring-boot', 'strength': 1.0},
    r'^\s*import\s+jakarta\.': {'lang': 'java', 'framework': 'spring-boot', 'strength': 0.9},
    r'^\s*import\s+javax\.servlet': {'lang': 'java', 'category': 'backend', 'strength': 0.8},

    # Go frameworks
    r'^\s*import\s+\(\s*"github\.com/grpc': {'lang': 'go', 'framework': 'grpc', 'strength': 0.95},
    r'^\s*import\s+"github\.com/gin-gonic/gin': {'lang': 'go', 'framework': 'gin', 'strength': 0.9},
    r'^\s*import\s+"database/sql': {'lang': 'go', 'category': 'backend', 'strength': 0.7},

    # JavaScript/TypeScript frameworks
    r"^\s*import\s+.*from\s+['\"]react['\"]": {'lang': 'javascript', 'framework': 'react', 'strength': 1.0},
    r"^\s*import\s+.*from\s+['\"]@angular": {'lang': 'typescript', 'framework': 'angular', 'strength': 1.0},
    r"^\s*import\s+.*from\s+['\"]vue['\"]": {'lang': 'javascript', 'framework': 'vue', 'strength': 0.95},
    r"^\s*import\s+.*from\s+['\"]express['\"]": {'lang': 'javascript', 'framework': 'express', 'strength': 0.9},
    r"^\s*const\s+\w+\s*=\s*require\(['\"]react['\"]\)": {'lang': 'javascript', 'framework': 'react', 'strength': 0.9},

    # Config/markup
    r'^\s*<!DOCTYPE\s+html': {'lang': 'html', 'category': 'frontend', 'strength': 0.6},
    r'^\s*<html': {'lang': 'html', 'category': 'frontend', 'strength': 0.5},
}

# ──────────────────────────────────────────────────────────────────────────────
# Config file signals (20% weight)
# ──────────────────────────────────────────────────────────────────────────────

CONFIG_SIGNALS = {
    'package.json': {'default_lang': 'javascript', 'default_framework': 'node', 'strength': 0.9},
    'go.mod': {'default_lang': 'go', 'strength': 1.0},
    'pom.xml': {'default_lang': 'java', 'default_framework': 'maven', 'strength': 1.0},
    'build.gradle': {'default_lang': 'java', 'default_framework': 'gradle', 'strength': 1.0},
    'requirements.txt': {'default_lang': 'python', 'strength': 0.9},
    'Pipfile': {'default_lang': 'python', 'strength': 0.8},
    'Dockerfile': {'strength': 0.3},  # Multi-language, weak signal
    'docker-compose.yml': {'strength': 0.2},
    'Gemfile': {'default_lang': 'ruby', 'strength': 0.9},
    'Cargo.toml': {'default_lang': 'rust', 'strength': 1.0},
}

# Directories to exclude from scanning
EXCLUDED_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'node_modules',
    '.next', 'dist', 'build', 'target', '.gradle', '.maven',
    '.idea', '.vscode', 'coverage', '.pytest_cache', '.mypy_cache',
    'bin', 'obj', '.egg-info',
}

# Code file extensions to scan
CODE_EXTENSIONS = set(EXTENSION_SIGNALS.keys()) | {'.jsx', '.tsx'}


def scan_codebase(path: str, verbose: bool = False) -> list:
    """
    Recursively scan a codebase and return all code files.

    Args:
        path: Root directory path
        verbose: Print progress to stderr

    Returns:
        List of Path objects, sorted by name
    """
    root = Path(path).resolve()

    if not root.exists():
        if verbose:
            print(f"[scan] Path does not exist: {path}", file=sys)
        return []

    if not root.is_dir():
        if verbose:
            print(f"[scan] Path is not a directory: {path}", file=sys)
        return []

    files = []

    try:
        for item in root.rglob('*'):
            # Skip excluded directories
            if any(excluded in item.parts for excluded in EXCLUDED_DIRS):
                continue

            if not item.is_file():
                continue

            if item.suffix in CODE_EXTENSIONS:
                files.append(item)

        if verbose:
            print(f"[scan] Found {len(files)} code files", file=sys.stderr)

    except PermissionError as e:
        if verbose:
            print(f"[scan] Permission denied: {e}", file=sys.stderr)
        return []

    return sorted(files)


def score_extensions(files: list, verbose: bool = False) -> dict:
    """
    Score languages based on file extensions.

    Weight: 50% of total score

    Args:
        files: List of Path objects
        verbose: Print debug info

    Returns:
        Dict of {language/framework: confidence_score}
    """
    scores = defaultdict(float)

    if not files:
        return dict(scores)

    total = len(files)
    ext_counts = defaultdict(int)

    # Count extensions
    for f in files:
        ext_counts[f.suffix] += 1

    # Score each language
    for ext, count in ext_counts.items():
        if ext not in EXTENSION_SIGNALS:
            continue

        signal = EXTENSION_SIGNALS[ext]
        proportion = count / total
        score = proportion * signal['strength'] * 0.50  # 50% weight

        # Primary signal: language
        if 'lang' in signal:
            scores[signal['lang']] += score

        # Secondary signal: framework (if present)
        if 'framework' in signal:
            scores[signal['framework']] += score * 0.5

        if verbose:
            print(f"[ext] {ext:8} x {count:3} = {score:.3f} (lang: {signal.get('lang', 'N/A')})",
                  file=sys.stderr)

    return dict(scores)


def score_imports(files: list, verbose: bool = False) -> dict:
    """
    Score languages based on import statements in source files.

    Weight: 30% of total score

    Args:
        files: List of Path objects
        verbose: Print debug info

    Returns:
        Dict of {language/framework: confidence_score}
    """
    scores = defaultdict(float)

    if not files:
        return dict(scores)

    files_with_imports = 0

    for f in files:
        try:
            content = f.read_text(errors='ignore')
            lines = content.split('\n')[:100]  # First 100 lines only

            found_match = False

            for pattern, signal in IMPORT_PATTERNS.items():
                for line in lines:
                    if re.match(pattern, line, re.MULTILINE):
                        found_match = True
                        score = signal['strength'] * 0.30 / max(1, len(files))  # 30% weight

                        if 'lang' in signal:
                            scores[signal['lang']] += score

                        if 'framework' in signal:
                            scores[signal['framework']] += score * 0.6

                        if verbose:
                            print(f"[imp] {f.name}: {signal.get('framework', signal.get('lang', 'N/A'))}",
                                  file=sys.stderr)
                        break

            if found_match:
                files_with_imports += 1

        except (OSError, UnicodeDecodeError):
            pass

    if verbose and files_with_imports > 0:
        print(f"[imp] {files_with_imports}/{len(files)} files with recognized imports",
              file=sys.stderr)

    return dict(scores)


def score_configs(root: Path, verbose: bool = False) -> dict:
    """
    Score languages based on presence and content of config files.

    Weight: 20% of total score

    Args:
        root: Root directory Path
        verbose: Print debug info

    Returns:
        Dict of {language/framework: confidence_score}
    """
    scores = defaultdict(float)

    for config_name, signal in CONFIG_SIGNALS.items():
        config_path = root / config_name

        if config_path.exists():
            strength = signal.get('strength', 0.5)
            score = strength * 0.20  # 20% weight

            # Primary signal
            if 'default_lang' in signal:
                scores[signal['default_lang']] += score

            if 'default_framework' in signal:
                scores[signal['default_framework']] += score * 0.3

            if verbose:
                print(f"[cfg] {config_name}: +{score:.3f}", file=sys.stderr)

    return dict(scores)


def aggregate_scores(ext_scores: dict, imp_scores: dict, cfg_scores: dict,
                     verbose: bool = False) -> dict:
    """
    Combine three signal dicts and normalize to 0-1 range.

    Args:
        ext_scores: Extension-based scores
        imp_scores: Import-based scores
        cfg_scores: Config-based scores
        verbose: Print debug info

    Returns:
        Normalized dict of {language/framework: confidence_score}
    """
    combined = defaultdict(float)

    for k, v in ext_scores.items():
        combined[k] += v
    for k, v in imp_scores.items():
        combined[k] += v
    for k, v in cfg_scores.items():
        combined[k] += v

    if not combined:
        return {}

    # Normalize
    max_score = max(combined.values())
    if max_score > 0:
        normalized = {k: v / max_score for k, v in combined.items()}
    else:
        normalized = dict(combined)

    if verbose:
        print(f"[agg] Aggregated scores: {dict(sorted(normalized.items(), key=lambda x: -x[1])[:5])}",
              file=sys.stderr)

    return normalized


def load_registry(registry_path: str = None) -> dict:
    """
    Load the persona registry from YAML.

    Args:
        registry_path: Path to registry.yaml. If None, uses default path.

    Returns:
        Dict of {persona_name: persona_dict}
    """
    if registry_path is None:
        # Infer default location
        script_dir = Path(__file__).parent
        registry_path = script_dir / 'registry.yaml'

    if not Path(registry_path).exists():
        return {}

    if yaml is None:
        # Fallback: parse manually (basic YAML subset)
        return _parse_registry_basic(registry_path)

    try:
        with open(registry_path) as f:
            data = yaml.safe_load(f)
            return data or {}
    except Exception:
        return {}


def _parse_registry_basic(registry_path: str) -> dict:
    """
    Basic YAML parser for registry.yaml (manual fallback if PyYAML unavailable).
    Extracts persona name, role, and base_model fields.
    """
    personas = {}
    current_persona = None
    current_data = {}

    with open(registry_path) as f:
        for line in f:
            line = line.rstrip()

            # Skip comments and blank lines
            if not line.strip() or line.strip().startswith('#'):
                continue

            # Detect persona section (e.g., "my-java-q3:")
            if line and not line[0].isspace() and ':' in line:
                if current_persona:
                    personas[current_persona] = current_data

                current_persona = line.split(':')[0]
                current_data = {}

            # Parse key-value pairs (indented)
            elif line.startswith('  ') and ':' in line:
                parts = line.strip().split(':', 1)
                key = parts[0].strip()
                value = parts[1].strip() if len(parts) > 1 else ''

                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                current_data[key] = value

    if current_persona:
        personas[current_persona] = current_data

    return personas


def extract_language_hints(role_str: str) -> list:
    """
    Extract language/framework keywords from a persona's role description.

    Examples:
        "Java 21 backend..." → ['java']
        "React 18+ TypeScript..." → ['react', 'typescript']
        "Go 1.22+ backend..." → ['go']

    Args:
        role_str: The role field value

    Returns:
        List of detected language/framework keywords
    """
    hints = []

    keywords = {
        'java': ['java'],
        'go': ['go'],
        'python': ['python'],
        'typescript': ['typescript', 'ts'],
        'javascript': ['javascript', 'js'],
        'react': ['react'],
        'angular': ['angular'],
        'vue': ['vue'],
        'fastapi': ['fastapi'],
        'spring': ['spring', 'spring-boot'],
        'bash': ['bash', 'shell'],
        'rust': ['rust'],
        'cpp': ['c\\+\\+', 'cpp'],
        'ruby': ['ruby'],
        'php': ['php'],
        'grpc': ['grpc'],
    }

    role_lower = role_str.lower()

    for keyword, patterns in keywords.items():
        for pattern in patterns:
            if re.search(r'\b' + pattern + r'\b', role_lower):
                hints.append(keyword)
                break  # Don't add duplicates

    return list(set(hints))  # Deduplicate


def find_matching_personas(detected: dict, personas: dict, verbose: bool = False) -> dict:
    """
    Query registry to find personas matching detected languages.

    Args:
        detected: Dict of {language: confidence} from aggregation
        personas: Loaded registry dict
        verbose: Print debug info

    Returns:
        Dict of {persona_name: confidence}
    """
    matches = defaultdict(float)

    for persona_name, persona_info in personas.items():
        role = persona_info.get('role', '')
        hints = extract_language_hints(role)

        if not hints:
            continue

        # Match detected languages to persona hints
        for detected_lang, detected_conf in detected.items():
            if detected_lang in hints:
                # Primary match: language directly mentioned in role
                score = detected_conf * 0.95
                matches[persona_name] = max(matches[persona_name], score)

                if verbose:
                    print(f"[reg] {persona_name}: +{score:.3f} (matched {detected_lang})",
                          file=sys.stderr)

            # Fuzzy match: similar patterns
            elif detected_lang in role.lower():
                score = detected_conf * 0.6
                if score > matches[persona_name]:
                    matches[persona_name] = score

                    if verbose:
                        print(f"[reg] {persona_name}: +{score:.3f} (fuzzy match {detected_lang})",
                              file=sys.stderr)

    return dict(matches)


def detect(path: str, registry_path: str = None, verbose: bool = False) -> list:
    """
    Analyze a codebase and return ranked persona recommendations.

    Main entry point (importable as a function for Task 3.5).

    Args:
        path: Root directory path
        registry_path: Optional path to registry.yaml
        verbose: Print debug info to stderr

    Returns:
        List of dicts, each with keys:
          - persona_name (str)
          - confidence (0.0–1.0)
          - reason (str)
          - base_model (str)
          - role (str)
          - tier (str)
    """
    if verbose:
        print(f"[main] Scanning {path}...", file=sys.stderr)

    # Scan codebase
    files = scan_codebase(path, verbose)

    if not files:
        if verbose:
            print(f"[main] No code files found; using fallback", file=sys.stderr)
        # Fallback: empty codebase
        registry = load_registry(registry_path)
        my_codegen = registry.get('my-codegen-q3', {})
        return [{
            'persona_name': 'my-codegen-q3',
            'confidence': 0.5,
            'reason': 'No code files detected; using polyglot fallback',
            'base_model': my_codegen.get('base_model', 'qwen3:8b'),
            'role': my_codegen.get('role', 'General-purpose code generator'),
            'tier': my_codegen.get('tier', 'full'),
        }]

    root = Path(path).resolve()

    # Score three signals
    ext_scores = score_extensions(files, verbose)
    imp_scores = score_imports(files, verbose)
    cfg_scores = score_configs(root, verbose)

    # Aggregate and normalize
    detected = aggregate_scores(ext_scores, imp_scores, cfg_scores, verbose)

    if not detected:
        if verbose:
            print(f"[main] No signals detected; using fallback", file=sys.stderr)
        # Fallback: no recognizable patterns
        registry = load_registry(registry_path)
        my_codegen = registry.get('my-codegen-q3', {})
        return [{
            'persona_name': 'my-codegen-q3',
            'confidence': 0.5,
            'reason': 'Could not detect language or framework',
            'base_model': my_codegen.get('base_model', 'qwen3:8b'),
            'role': my_codegen.get('role', 'General-purpose code generator'),
            'tier': my_codegen.get('tier', 'full'),
        }]

    # Load registry
    registry = load_registry(registry_path)

    # Find matching personas
    candidates = find_matching_personas(detected, registry, verbose)

    if not candidates:
        if verbose:
            print(f"[main] No matching personas in registry; using fallback", file=sys.stderr)
        # Fallback: detected language but no persona
        my_codegen = registry.get('my-codegen-q3', {})
        detected_str = ', '.join(f"{k} ({v:.2f})" for k, v in sorted(detected.items(), key=lambda x: -x[1])[:3])
        return [{
            'persona_name': 'my-codegen-q3',
            'confidence': 0.5,
            'reason': f'Detected: {detected_str}, but no specialist persona found',
            'base_model': my_codegen.get('base_model', 'qwen3:8b'),
            'role': my_codegen.get('role', 'General-purpose code generator'),
            'tier': my_codegen.get('tier', 'full'),
        }]

    # Rank top 3
    ranked = sorted(candidates.items(), key=lambda x: -x[1])[:3]

    results = []
    for persona_name, confidence in ranked:
        persona_info = registry.get(persona_name, {})
        detected_str = ', '.join(f"{k} ({v:.2f})"
                                 for k, v in sorted(detected.items(), key=lambda x: -x[1])[:2])
        results.append({
            'persona_name': persona_name,
            'confidence': round(confidence, 3),
            'reason': f'Detected: {detected_str}',
            'base_model': persona_info.get('base_model', 'qwen3:8b'),
            'role': persona_info.get('role', ''),
            'tier': persona_info.get('tier', 'full'),
        })

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze a codebase to detect appropriate Ollama personas'
    )
    parser.add_argument('path', help='Path to codebase root directory')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print debug info to stderr')
    parser.add_argument('--dry-run', action='store_true',
                        help='Scan without modifying state (info only)')
    parser.add_argument('--json-compact', action='store_true',
                        help='Output compact JSON (no pretty-print)')
    parser.add_argument('--registry', help='Path to registry.yaml')

    args = parser.parse_args()

    # Validate path
    try:
        path = Path(args.path).resolve()
        if not path.exists():
            print(f"Error: path does not exist: {args.path}", file=sys.stderr)
            sys.exit(1)
        if not path.is_dir():
            print(f"Error: path is not a directory: {args.path}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Detect personas
    results = detect(str(path), registry_path=args.registry, verbose=args.verbose)

    # Output
    if args.json_compact:
        print(json.dumps(results, separators=(',', ':')))
    else:
        print(json.dumps(results, indent=2))

    sys.exit(0)


if __name__ == '__main__':
    main()
