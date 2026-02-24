---
id: go-05-worker-pool
domain: go
difficulty: medium

description: Worker pool with graceful shutdown and result collection
---

Implement a worker pool in Go that processes jobs concurrently and collects results.

Requirements:

1. Generic types: `Job[I, O any]` and `WorkerPool[I, O any]`
2. Constructor: `NewWorkerPool[I, O](workers int, fn func(I) (O, error)) *WorkerPool[I, O]`
   - `workers` is the number of concurrent goroutines
   - `fn` is the processing function applied to each job input
3. Methods:
   - `Submit(input I)` — enqueue a job (blocks if pool is full; buffer size = 2 × workers)
   - `Results() <-chan Result[O]` — channel of results (each result has the output and any error)
   - `Shutdown()` — stop accepting new jobs, wait for all in-flight jobs to complete, close Results channel
4. The pool must:
   - Start workers on construction
   - Handle panics in `fn` gracefully (recover, wrap as error in Result)
   - Preserve order: Results appear in the order jobs were submitted

Requirements:
- Use `context.Context` for cancellation in Shutdown
- Use `sync.WaitGroup` to wait for workers
- Include a `main()` that submits 20 jobs to a pool of 4 workers, each sleeping a random duration, and prints results
