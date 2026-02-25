---
id: java-10-batch-processor
domain: java
difficulty: hard
timeout: 420
description: Spring Batch job for CSV import with error handling and skip policy
---

Implement a Spring Batch job that imports transactions from a CSV file.

CSV format: `id,customerId,amount,currency,date`

Requirements:

1. `TransactionRecord` (Java record for raw CSV row)
2. `Transaction` JPA entity
3. `TransactionItemReader`: `FlatFileItemReader<TransactionRecord>` for the CSV
4. `TransactionItemProcessor`: validates amount > 0, currency is 3-letter ISO code; throws `InvalidTransactionException` for invalid records
5. `TransactionItemWriter`: `JpaItemWriter<Transaction>`
6. `BatchJobConfig`:
   - Single step, chunk size 100
   - Skip policy: skip `InvalidTransactionException` up to 10 times, then fail
   - `JobExecutionListener` logging start/end/counts
   - `StepExecutionListener` logging skip count

Requirements:
- `jakarta.persistence.*`, constructor injection for all Spring components
- `@StepScope` on reader/processor/writer beans
- Job parameter for input file: `#{jobParameters['inputFile']}`
