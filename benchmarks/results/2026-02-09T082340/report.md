# Benchmark Report: Qwen2.5-Coder vs Qwen3 Personas

**Date:** 2026-02-09 08:39:36
**Run ID:** 2026-02-09T082340

---

## Performance Summary

### Backend Prompts (my-coder vs my-coder-q3)

| Prompt | my-coder (Qwen2.5-7B) | my-coder-q3 (Qwen3-8B) |
|--------|-----------------------|------------------------|
| Concurrent-safe LRU cache with TTL expiration in Go | 1635 tok, 65.9 tok/s, 26.2s | N/A |
| Stream-based CSV parser with error handling in Java | 852 tok, 66.6 tok/s, 13.6s | N/A |
| Merge overlapping intervals algorithm | 854 tok, 66.6 tok/s, 13.7s | 6238 tok, 54.4 tok/s, 116.4s |
| **Average tok/s** | **66.4** | **54.4** |

### Visual Prompts (my-creative-coder vs my-creative-coder-q3)

| Prompt | my-creative-coder (Qwen2.5-7B) | my-creative-coder-q3 (Qwen3-8B) |
|--------|--------------------------------|---------------------------------|
| Ball bouncing inside a slowly rotating square without gravity | 651 tok, 66.4 tok/s, 10.4s | 8688 tok, 51.8 tok/s, 170.2s |
| 20 colored balls bouncing inside a spinning heptagon with physics | 1711 tok, 64.2 tok/s, 28.3s | 11151 tok, 50.4 tok/s, 224.6s |
| Animated fish tank screensaver with procedural fish, bubbles, and plants | 1365 tok, 64.0 tok/s, 22.7s | 2964 tok, 55.6 tok/s, 54.2s |
| **Average tok/s** | **64.9** | **52.6** |

## Detailed Results

### 01-bouncing-ball-rotating-square
**Prompt:** Ball bouncing inside a slowly rotating square without gravity

#### my-creative-coder (qwen2.5-coder:7b)
**Performance:** 66.4 tok/s | 651 tokens | 10.4s total
**Output:** `html/my-creative-coder--01-bouncing-ball-rotating-square.html` (85 lines)

#### my-creative-coder-q3 (qwen3:8b)
**Performance:** 51.8 tok/s | 8688 tokens | 170.2s total
**Output:** `html/my-creative-coder-q3--01-bouncing-ball-rotating-square.html` (124 lines)

### 01-go-lru-cache
**Prompt:** Concurrent-safe LRU cache with TTL expiration in Go

#### my-coder (qwen2.5-coder:7b)
**Performance:** 65.9 tok/s | 1635 tokens | 26.2s total
**Output:** `code/my-coder--01-go-lru-cache.go` (163 lines)

#### my-coder-q3 (qwen3:8b)
**Status:** Timed out after 120s

### 02-java-csv-parser
**Prompt:** Stream-based CSV parser with error handling in Java

#### my-coder (qwen2.5-coder:7b)
**Performance:** 66.6 tok/s | 852 tokens | 13.6s total
**Output:** `code/my-coder--02-java-csv-parser.java` (94 lines)

#### my-coder-q3 (qwen3:8b)
**Status:** Timed out after 120s

### 02-twenty-balls-heptagon
**Prompt:** 20 colored balls bouncing inside a spinning heptagon with physics

#### my-creative-coder (qwen2.5-coder:7b)
**Performance:** 64.2 tok/s | 1711 tokens | 28.3s total
**Output:** `html/my-creative-coder--02-twenty-balls-heptagon.html` (170 lines)

#### my-creative-coder-q3 (qwen3:8b)
**Performance:** 50.4 tok/s | 11151 tokens | 224.6s total
**Output:** `html/my-creative-coder-q3--02-twenty-balls-heptagon.html` (201 lines)

### 03-aquarium-screensaver
**Prompt:** Animated fish tank screensaver with procedural fish, bubbles, and plants

#### my-creative-coder (qwen2.5-coder:7b)
**Performance:** 64.0 tok/s | 1365 tokens | 22.7s total
**Output:** `html/my-creative-coder--03-aquarium-screensaver.html` (176 lines)

#### my-creative-coder-q3 (qwen3:8b)
**Performance:** 55.6 tok/s | 2964 tokens | 54.2s total
**Output:** `html/my-creative-coder-q3--03-aquarium-screensaver.html` (244 lines)

### 03-merge-intervals
**Prompt:** Merge overlapping intervals algorithm

#### my-coder (qwen2.5-coder:7b)
**Performance:** 66.6 tok/s | 854 tokens | 13.7s total
**Output:** `code/my-coder--03-merge-intervals.java` (82 lines)

#### my-coder-q3 (qwen3:8b)
**Performance:** 54.4 tok/s | 6238 tokens | 116.4s total
**Output:** `code/my-coder-q3--03-merge-intervals.java` (77 lines)

## Visual Results

HTML files can be opened directly in a browser:

| File | Model | Prompt |
|------|-------|--------|
| `html/my-creative-coder--01-bouncing-ball-rotating-square.html` | my-creative-coder | Ball bouncing inside a slowly rotating square without gravity |
| `html/my-creative-coder-q3--01-bouncing-ball-rotating-square.html` | my-creative-coder-q3 | Ball bouncing inside a slowly rotating square without gravity |
| `html/my-creative-coder--02-twenty-balls-heptagon.html` | my-creative-coder | 20 colored balls bouncing inside a spinning heptagon with physics |
| `html/my-creative-coder-q3--02-twenty-balls-heptagon.html` | my-creative-coder-q3 | 20 colored balls bouncing inside a spinning heptagon with physics |
| `html/my-creative-coder--03-aquarium-screensaver.html` | my-creative-coder | Animated fish tank screensaver with procedural fish, bubbles, and plants |
| `html/my-creative-coder-q3--03-aquarium-screensaver.html` | my-creative-coder-q3 | Animated fish tank screensaver with procedural fish, bubbles, and plants |

## Observations

_To be filled after reviewing outputs._
