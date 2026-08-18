# Benchmark Report: Qwen2.5-Coder vs Qwen3 Personas

**Date:** 2026-02-11 23:11:47
**Run ID:** 2026-02-11T224710

---

## Performance Summary

### Backend Prompts (my-coder vs my-coder-q3)

| Prompt | my-coder (Qwen2.5-7B) | my-coder-q3 (Qwen3-8B) |
|--------|-----------------------|------------------------|
| Concurrent-safe LRU cache with TTL expiration in Go | 1017 tok, 66.2 tok/s, 16.4s | 8307 tok, 53.0 tok/s, 159.3s |
| Stream-based CSV parser with error handling in Java | 821 tok, 66.1 tok/s, 13.3s | N/A |
| Merge overlapping intervals algorithm | 750 tok, 66.4 tok/s, 12.1s | N/A |
| **Average tok/s** | **66.2** | **53.0** |

### Visual Prompts (my-creative-coder vs my-creative-coder-q3)

| Prompt | my-creative-coder (Qwen2.5-7B) | my-creative-coder-q3 (Qwen3-8B) |
|--------|--------------------------------|---------------------------------|
| Ball bouncing inside a slowly rotating square without gravity | 461 tok, 66.4 tok/s, 7.5s | N/A |
| 20 colored balls bouncing inside a spinning heptagon with physics | 1637 tok, 64.6 tok/s, 27.2s | N/A |
| Animated fish tank screensaver with procedural fish, bubbles, and plants | 1194 tok, 65.6 tok/s, 19.6s | 2603 tok, 56.7 tok/s, 46.8s |
| **Average tok/s** | **65.5** | **56.7** |

## Detailed Results

### 01-bouncing-ball-rotating-square
**Prompt:** Ball bouncing inside a slowly rotating square without gravity

#### my-creative-coder (qwen2.5-coder:7b)
**Performance:** 66.4 tok/s | 461 tokens | 7.5s total
**Output:** `html/my-creative-coder--01-bouncing-ball-rotating-square.html` (64 lines)

#### my-creative-coder-q3 (qwen3:8b)
**Status:** Timed out after 180s

### 01-go-lru-cache
**Prompt:** Concurrent-safe LRU cache with TTL expiration in Go

#### my-coder (qwen2.5-coder:7b)
**Performance:** 66.2 tok/s | 1017 tokens | 16.4s total
**Output:** `code/my-coder--01-go-lru-cache.go` (169 lines)

#### my-coder-q3 (qwen3:8b)
**Performance:** 53.0 tok/s | 8307 tokens | 159.3s total
**Output:** `code/my-coder-q3--01-go-lru-cache.go` (182 lines)

### 02-java-csv-parser
**Prompt:** Stream-based CSV parser with error handling in Java

#### my-coder (qwen2.5-coder:7b)
**Performance:** 66.1 tok/s | 821 tokens | 13.3s total
**Output:** `code/my-coder--02-java-csv-parser.java` (74 lines)

#### my-coder-q3 (qwen3:8b)
**Status:** Timed out after 300s

### 02-twenty-balls-heptagon
**Prompt:** 20 colored balls bouncing inside a spinning heptagon with physics

#### my-creative-coder (qwen2.5-coder:7b)
**Performance:** 64.6 tok/s | 1637 tokens | 27.2s total
**Output:** `html/my-creative-coder--02-twenty-balls-heptagon.html` (171 lines)

#### my-creative-coder-q3 (qwen3:8b)
**Status:** Timed out after 300s

### 03-aquarium-screensaver
**Prompt:** Animated fish tank screensaver with procedural fish, bubbles, and plants

#### my-creative-coder (qwen2.5-coder:7b)
**Performance:** 65.6 tok/s | 1194 tokens | 19.6s total
**Output:** `html/my-creative-coder--03-aquarium-screensaver.html` (145 lines)

#### my-creative-coder-q3 (qwen3:8b)
**Performance:** 56.7 tok/s | 2603 tokens | 46.8s total
**Output:** `html/my-creative-coder-q3--03-aquarium-screensaver.html` (263 lines)

### 03-merge-intervals
**Prompt:** Merge overlapping intervals algorithm

#### my-coder (qwen2.5-coder:7b)
**Performance:** 66.4 tok/s | 750 tokens | 12.1s total
**Output:** `code/my-coder--03-merge-intervals.java` (79 lines)

#### my-coder-q3 (qwen3:8b)
**Status:** Timed out after 300s

## Visual Results

HTML files can be opened directly in a browser:

| File | Model | Prompt |
|------|-------|--------|
| `html/my-creative-coder--01-bouncing-ball-rotating-square.html` | my-creative-coder | Ball bouncing inside a slowly rotating square without gravity |
| `html/my-creative-coder--02-twenty-balls-heptagon.html` | my-creative-coder | 20 colored balls bouncing inside a spinning heptagon with physics |
| `html/my-creative-coder--03-aquarium-screensaver.html` | my-creative-coder | Animated fish tank screensaver with procedural fish, bubbles, and plants |
| `html/my-creative-coder-q3--03-aquarium-screensaver.html` | my-creative-coder-q3 | Animated fish tank screensaver with procedural fish, bubbles, and plants |

## Observations

_To be filled after reviewing outputs._
