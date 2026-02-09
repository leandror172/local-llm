---
id: 02-java-csv-parser
category: backend
models: my-coder,my-coder-q3
timeout: 300
description: Stream-based CSV parser with error handling in Java
source: closing-the-gap benchmark
---

Write a CSV parser in Java 21 with the following requirements:
- Parse CSV input from a String or InputStream
- Handle quoted fields (fields containing commas, newlines, and escaped quotes)
- Use Java Records for parsed rows
- Return results as a Stream<Record> for lazy processing
- Collect parsing errors (malformed rows) without stopping — return both valid rows and a list of errors
- Support custom delimiter and quote character configuration
- Include a main() method that demonstrates: parsing a sample CSV with edge cases, filtering rows with Stream operations, and printing any parsing errors
