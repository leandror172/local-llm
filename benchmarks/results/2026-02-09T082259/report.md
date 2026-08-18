# Benchmark Report: Qwen2.5-Coder vs Qwen3 Personas

**Date:** 2026-02-09 08:23:31
**Run ID:** 2026-02-09T082259

---

## Performance Summary

### Backend Prompts (my-coder vs my-coder-q3)

| Prompt | my-coder (Qwen2.5-7B) | my-coder-q3 (Qwen3-8B) |
|--------|-----------------------|------------------------|
| Concurrent-safe LRU cache with TTL expiration in Go | 1475 tok, 66.1 tok/s, 31.9s | N/A |
| **Average tok/s** | **66.1** | **N/A** |

## Detailed Results

### 01-go-lru-cache
**Prompt:** Concurrent-safe LRU cache with TTL expiration in Go

#### my-coder (qwen2.5-coder:7b)
**Performance:** 66.1 tok/s | 1475 tokens | 31.9s total
**Output:** `code/my-coder--01-go-lru-cache.go` (158 lines)

## Observations

_To be filled after reviewing outputs._
