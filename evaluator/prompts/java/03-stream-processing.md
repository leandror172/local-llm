---
id: java-03-stream-processing
domain: java
difficulty: easy
timeout: 180
description: Stream API data processing pipeline with collectors
---

Given this data class:
```java
record Transaction(String id, String customerId, String category, double amount, LocalDate date) {}
```

Write a `TransactionAnalyzer` class with these static methods using only the Stream API (no loops):

1. `totalByCategory(List<Transaction> txns)` → `Map<String, Double>` — sum amounts per category
2. `topCustomers(List<Transaction> txns, int n)` → `List<String>` — top N customer IDs by total spend, descending
3. `monthlyTotals(List<Transaction> txns)` → `Map<YearMonth, Double>` — sum per calendar month, sorted chronologically
4. `fraudCandidates(List<Transaction> txns, double threshold)` → `List<Transaction>` — transactions where a customer spent more than `threshold` in a single day, sorted by amount descending
5. `summary(List<Transaction> txns)` → a `record Summary(long count, double total, double average, double max, Optional<Transaction> largest)`

Requirements:
- Use only Stream API: `Collectors.groupingBy`, `Collectors.summingDouble`, `Comparator.comparingDouble`
- Include a `main()` with a sample dataset of 10+ transactions demonstrating all methods
