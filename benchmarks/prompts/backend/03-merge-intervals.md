---
id: 03-merge-intervals
category: backend
models: my-coder,my-coder-q3
timeout: 300
description: Merge overlapping intervals algorithm
source: closing-the-gap benchmark
---

Implement a function that takes a collection of intervals (each with a start and end value) and merges all overlapping intervals, returning the result as a list of non-overlapping intervals sorted by start value.

Requirements:
- Handle edge cases: empty input, single interval, fully contained intervals, adjacent intervals (e.g., [1,3] and [3,5] should merge)
- The function should work with any comparable numeric type
- Include comprehensive tests covering: no overlaps, all overlapping, partial overlaps, contained intervals, single element, empty input, unsorted input
- Write clean, idiomatic code with proper error handling
