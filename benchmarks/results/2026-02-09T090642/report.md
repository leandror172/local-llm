# Benchmark Report: Qwen2.5-Coder vs Qwen3 Personas

**Date:** 2026-02-09 09:16:48
**Run ID:** 2026-02-09T090642

---

## Performance Summary

### Backend Prompts (my-coder vs my-coder-q3)

| Prompt | my-coder (Qwen2.5-7B) | my-coder-q3 (Qwen3-8B) |
|--------|-----------------------|------------------------|
| Concurrent-safe LRU cache with TTL expiration in Go | N/A | 9372 tok, 51.8 tok/s, 183.5s |
| Stream-based CSV parser with error handling in Java | N/A | N/A |
| Merge overlapping intervals algorithm | N/A | 6155 tok, 53.5 tok/s, 116.9s |
| **Average tok/s** | **N/A** | **52.6** |

## Detailed Results

### 01-go-lru-cache
**Prompt:** Concurrent-safe LRU cache with TTL expiration in Go

#### my-coder-q3 (qwen3:8b)
**Performance:** 51.8 tok/s | 9372 tokens | 183.5s total
**Output:** `code/my-coder-q3--01-go-lru-cache.go` (199 lines)

### 02-java-csv-parser
**Prompt:** Stream-based CSV parser with error handling in Java

#### my-coder-q3 (qwen3:8b)
**Status:** Timed out after 300s

### 03-merge-intervals
**Prompt:** Merge overlapping intervals algorithm

#### my-coder-q3 (qwen3:8b)
**Performance:** 53.5 tok/s | 6155 tokens | 116.9s total
**Output:** `code/my-coder-q3--03-merge-intervals.java` (52 lines)

## Observations

_To be filled after reviewing outputs._
