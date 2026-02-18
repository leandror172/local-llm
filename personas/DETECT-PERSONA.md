# Codebase Analyzer: detect-persona.py

**Auto-detect appropriate Ollama personas from a codebase using file-based heuristics.**

## Overview

Analyzes any directory to identify the primary programming languages and frameworks, then recommends the top 3 matching personas from the registry. No LLM calls, no side effects — pure deterministic heuristics.

## Quick Start

```bash
# Analyze a codebase
personas/run-detect-persona.sh /path/to/my-repo

# Output (JSON)
[
  {
    "persona_name": "my-java-q3",
    "confidence": 0.92,
    "reason": "Detected: java (1.00), spring-boot (0.25)",
    "base_model": "qwen3:8b",
    "role": "Java 21 backend developer (Spring Boot 3.x, Jakarta EE)",
    "tier": "full"
  },
  ...
]
```

## Detection Algorithm

The detector uses three independent signals (weighted and aggregated):

### 1. File Extensions (50% weight)

Counts code files by extension and maps to languages:
- `.java` → Java (strength: 1.0)
- `.go` → Go (strength: 1.0)
- `.py` → Python (strength: 0.9)
- `.tsx` → TypeScript + React (strength: 1.0)
- `.js`, `.ts` → JavaScript/TypeScript (strength: 0.5–0.7, ambiguous)

**Example:** Directory with 50 `.java` files and 10 `.go` files → `java: 0.83, go: 0.17`

### 2. Import Statements (30% weight)

Parses source files for framework-specific imports:
- Python: `import fastapi`, `from flask import`, `import django`
- Java: `import org.springframework.*`, `import jakarta.*`
- Go: `import "google.golang.org/grpc"`, `import "github.com/gin-gonic/gin"`
- JavaScript: `import React from 'react'`, `import Angular from '@angular'`

**Example:** File with `import fastapi` → `fastapi: 0.95, python: 0.30`

### 3. Config Files (20% weight)

Detects presence and *content* of configuration files:
- **package.json** → extracts React, Angular, Vue, Express from dependencies
- **pom.xml** → extracts Spring Boot, Jakarta, Maven from artifactIds
- **requirements.txt** → extracts FastAPI, Django, Flask, pytest from packages
- **go.mod** → extracts gRPC, Gin from import paths
- **Dockerfile** → weak signal (multi-language possible)

**Example:** `package.json` with `"react": "^18.2.0"` → `react: 0.20, javascript: 0.15`

### Scoring & Normalization

1. Sum all three signals across detected languages
2. Normalize to 0.0–1.0 range (max score → 1.0)
3. Query registry: find personas matching detected languages
4. Rank top 3 by confidence and return

**Confidence interpretation:**
- 0.95–1.0: High confidence (clear signals, dedicated persona exists)
- 0.70–0.95: Good confidence (mixed signals or polyglot persona)
- 0.50–0.70: Moderate confidence (weak signals or fallback)
- < 0.50: Fallback to `my-codegen-q3` (generic)

## Usage

### CLI: Standalone

```bash
# Basic analysis
personas/run-detect-persona.sh /path/to/codebase

# Verbose output (debug info to stderr)
personas/run-detect-persona.sh --verbose /path/to/codebase

# Compact JSON (single line)
personas/run-detect-persona.sh --json-compact /path/to/codebase

# Custom registry path
personas/run-detect-persona.sh --registry /custom/registry.yaml /path/to/codebase

# Help
personas/detect-persona.py --help
```

### Python: Importable Function

```python
from personas.detect_persona import detect

# Analyze a codebase
results = detect('/path/to/codebase')

# Access results
top_persona = results[0]
print(f"Recommended: {top_persona['persona_name']}")
print(f"Confidence: {top_persona['confidence']:.1%}")
print(f"Reason: {top_persona['reason']}")

# Use in Task 3.5 (conversational builder)
for persona_info in results:
    print(f"  - {persona_info['persona_name']} ({persona_info['confidence']:.1%})")
```

## Examples

### Java + Spring Boot

**Files:**
```
src/main/java/com/example/Main.java (imports org.springframework.*)
pom.xml (spring-boot-starter-web)
```

**Detection:**
```
Signals: java (1.0) + spring-boot (0.25)
Top persona: my-java-q3 (0.95 confidence)
```

### React TypeScript Frontend

**Files:**
```
src/App.tsx (import React from 'react')
src/components/*.tsx (React JSX)
package.json (dependencies: react, @types/react)
```

**Detection:**
```
Signals: typescript (1.0) + react (1.0) + javascript (0.96)
Top persona: my-react-q3 (0.95 confidence)
```

### Monorepo (Java backend + React frontend)

**Files:**
```
backend/
  src/main/java/...
  pom.xml (Spring Boot)
frontend/
  src/App.tsx
  package.json (React)
scripts/
  build.sh
```

**Detection:**
```
Signals: java (0.67) + react (0.50) + typescript (0.40) + bash (0.20)
Top persona: my-java-q3 (0.95 confidence)
Alternative: my-react-q3 (0.94 confidence)
```

## Edge Cases & Fallbacks

### Empty Codebase
```json
{
  "persona_name": "my-codegen-q3",
  "confidence": 0.5,
  "reason": "No code files detected; using polyglot fallback"
}
```

### Mixed Language, No Clear Winner
```json
{
  "persona_name": "my-codegen-q3",
  "confidence": 0.5,
  "reason": "Detected: go (0.50), python (0.50); no specialist persona"
}
```

### Unknown Language
```json
{
  "persona_name": "my-codegen-q3",
  "confidence": 0.5,
  "reason": "Could not detect language or framework"
}
```

## Supported Languages & Frameworks

| Language | Frameworks |
|----------|-----------|
| **Java** | Spring Boot 3.x, Jakarta EE |
| **Go** | gRPC, Gin, GORM |
| **Python** | FastAPI, Flask, Django, pytest, pandas/numpy |
| **JavaScript** | React, Angular, Vue, Express, Next.js |
| **TypeScript** | React, Angular |
| **Bash/Shell** | Shell scripting, build scripts |
| **HTML/CSS** | Frontend markup |

## Implementation Details

### No Side Effects
- Read-only analysis
- No files created, modified, or deleted
- No external API calls (except registry.yaml read)
- Exit code: 0 (success), 1 (error)

### Performance
- Scans 1000+ files in <1 second
- Excludes: node_modules, .git, __pycache__, target, etc.
- First 100 lines of each file scanned for imports (enough for framework detection)

### Robustness
- Handles permission errors gracefully
- Resilient to malformed config files (JSON, XML parsing with try/except)
- Case-insensitive matching (fastapi, FastAPI, FASTAPI all detected)
- Multiline regex support for import statements

### Registry Lookup
- Loads `personas/registry.yaml` (or custom path)
- Extracts language/framework hints from persona.role
- Falls back to `my-codegen-q3` if no match found
- Returns top 3 candidates by confidence

## Testing

**Fixtures:** `benchmarks/test-fixtures/`
- `java-backend/` → my-java-q3
- `go-grpc/` → my-go-q3
- `react-frontend/` → my-react-q3
- `python-fastapi/` → my-python-q3
- `monorepo-mixed/` → my-java-q3 (primary)

**Run tests:**
```bash
bash benchmarks/test-detect.sh           # Run all tests
bash benchmarks/test-detect.sh --verbose # With debug output
```

All tests should pass (5/5).

## Integration with Task 3.5

The conversational persona builder (Task 3.5) will:
1. Call `detect(user_repo_path)` to get initial language hints
2. Use results to seed dialogue ("I detected Java — is this correct?")
3. Fall back to manual constraint entry if user disagrees with detection
4. Offer specialist personas first, polyglot as fallback

## Limitations & Future Work

**Current limitations:**
- Single-language recommendation (top-1 focus for monorepos)
- Import parsing limited to first 100 lines per file
- Config file parsing relies on keyword matching (not full parsing)
- No detection of: Rust, C++, C#, Ruby, PHP (extensible)

**Future enhancements:**
- Monorepo decomposition: return separate recommendations for each language group
- Framework version detection (Spring Boot 2.x vs 3.x)
- Dependency tree analysis (transitive imports)
- Custom registry per organization

## See Also

- `personas/registry.yaml` — Persona definitions
- `personas/create-persona.py` — Interactive persona creator
- `personas/persona-template.md` — Persona template reference
- Task 3.5 — Conversational builder (will use detect())
