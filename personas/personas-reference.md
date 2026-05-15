# Personas Reference

**Registry:** `personas/registry.yaml` (machine-readable source of truth)
**Template:** `personas/persona-template.md` (spec for creating new personas)
**Ideas / future candidates:** `personas/ideas.md`

---

<!-- ref:personas -->
## Persona Catalog

### Specialized Coding
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-java-q3 | `modelfiles/java-qwen3.Modelfile` | Qwen3-8B | Java 21, Spring Boot 3.x |
| my-go-q3 | `modelfiles/go-qwen3.Modelfile` | Qwen3-8B | Go 1.22+, Effective Go |
| my-python-q3 | `modelfiles/python-qwen3.Modelfile` | Qwen3-8B | Python 3.11+, FastAPI, CLI |
| my-react-q3 | `modelfiles/react-qwen3.Modelfile` | Qwen3-8B | React frontend |
| my-angular-q3 | `modelfiles/angular-qwen3.Modelfile` | Qwen3-8B | Angular frontend |
| my-creative-coder | `modelfiles/creative-coder-qwen25.Modelfile` | Qwen2.5-Coder-7B | Visual/creative coding |
| my-creative-coder-q3 | `modelfiles/creative-coder-qwen3.Modelfile` | Qwen3-8B | Visual/creative (Qwen3) |
| my-codegen-q3 | `modelfiles/codegen-qwen3.Modelfile` | Qwen3-8B | General-purpose code gen (polyglot fallback) |
| my-rust-async-q3 | `modelfiles/rust-async-qwen3.Modelfile` | Qwen3-8B | Rust async (added during 3.5 live e2e test) |

### Code Review
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-java-reviewer-q3 | `modelfiles/java-reviewer-qwen3.Modelfile` | Qwen3-8B | Java code review |
| my-go-reviewer-q3 | `modelfiles/go-reviewer-qwen3.Modelfile` | Qwen3-8B | Go code review |

### Architecture
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-architect-q3 | `modelfiles/architect-qwen3.Modelfile` | Qwen3-14B | System architecture (14B) |
| my-be-architect-q3 | `modelfiles/be-architect-qwen3.Modelfile` | Qwen3-8B | Backend architecture |
| my-fe-architect-q3 | `modelfiles/fe-architect-qwen3.Modelfile` | Qwen3-8B | Frontend architecture |

### Cloud Consulting
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-aws-q3 | `modelfiles/aws-qwen3.Modelfile` | Qwen3-8B | AWS cloud patterns |
| my-gcp-q3 | `modelfiles/gcp-qwen3.Modelfile` | Qwen3-8B | GCP cloud patterns |

### LLM Infrastructure
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-shell-q3 | `modelfiles/shell-qwen3.Modelfile` | Qwen3-8B | Bash/shell, Linux/WSL2 |
| my-mcp-q3 | `modelfiles/mcp-qwen3.Modelfile` | Qwen3-8B | MCP server dev (FastMCP) |
| my-prompt-eng-q3 | `modelfiles/prompt-eng-qwen3.Modelfile` | Qwen3-8B | Prompt engineering (7-14B) |

### NLP / Utility
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-classifier-q3 | `modelfiles/classifier-qwen3.Modelfile` | Qwen3-8B | Text classification (JSON) |
| my-summarizer-q3 | `modelfiles/summarizer-qwen3.Modelfile` | Qwen3-8B | Text summarization |
| my-translator-q3 | `modelfiles/translator-qwen3.Modelfile` | Qwen3-8B | Language translation (generic) |
| my-ptbr-q3 | `modelfiles/ptbr-translator-qwen3.Modelfile` | Qwen3-8B | PT-BR ↔ English specialist |
| my-tech-writer-q3 | `modelfiles/tech-writer-qwen3.Modelfile` | Qwen3-8B | Technical docs, READMEs |

### Life / Career / Meta
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-career-coach-q3 | `modelfiles/career-coach-qwen3.Modelfile` | Qwen3-8B | Career coaching and advice |
| my-persona-designer-q3 | `modelfiles/persona-designer-qwen3.Modelfile` | Qwen3-8B | Persona design and specification |

### Legacy / Fallback
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-coder | `modelfiles/coding-assistant.Modelfile` | Qwen2.5-Coder-7B | Java/Go backend (polyglot) |
| my-coder-q3 | `modelfiles/coding-assistant-qwen3.Modelfile` | Qwen3-8B | Java/Go backend (polyglot, Qwen3) |

### Bare (Tool Wrappers)
| Persona | Modelfile | Base Model | Host Tool |
|---------|-----------|------------|-----------|
| my-aider | `modelfiles/aider-qwen25.Modelfile` | Qwen2.5-Coder-7B | Aider |
| my-opencode | `modelfiles/opencode-qwen3.Modelfile` | Qwen3-8B | OpenCode |

### Layer 5+ Comparison Personas (DPO data collection)
| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-go-q25c14 | `modelfiles/go-qwen25c14.Modelfile` | Qwen2.5-Coder-14B | Go comparison partner — code-specialized 14B, full VRAM |
| my-java-q25c14 | `modelfiles/java-qwen25c14.Modelfile` | Qwen2.5-Coder-14B | Java 21 + Spring Boot 3.x — code-specialized 14B, full VRAM |
| my-go-q3-q8 | `modelfiles/go-qwen3-q8.Modelfile` | Qwen3-8B-Q8 | Go Q4 vs Q8 quantization comparison |
| my-go-q3-30b | `modelfiles/go-qwen3-30b.Modelfile` | Qwen3-30B-A3B | Go quality ceiling — hybrid VRAM+RAM, ~10-20 tok/s |
<!-- /ref:personas -->
