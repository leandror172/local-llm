---
id: 04-python-async-pipeline
category: backend
models: my-python-q25c14,my-python-deepcoder,my-python-deepcoder-vanilla
timeout: 300
description: Async file processing pipeline with Pydantic models and structured error handling
source: closing-the-gap benchmark
---

Write an async file processing pipeline in Python 3.11+ with the following requirements:
- A `FileRecord` Pydantic model with fields: `path` (Path), `size_bytes` (int), `checksum` (str), `processed_at` (datetime)
- A `PipelineError` dataclass with fields: `path` (Path), `reason` (str)
- A `PipelineResult` dataclass with fields: `records` (list[FileRecord]), `errors` (list[PipelineError])
- An async function `process_file(path: Path) -> FileRecord` that reads the file without blocking the event loop (use `asyncio.get_event_loop().run_in_executor`), computes its SHA-256 checksum, and returns a populated `FileRecord`; raises `ValueError` with a descriptive message if the file is not readable or any other I/O error occurs
- An async function `run_pipeline(paths: list[Path], concurrency: int = 4) -> PipelineResult` that processes all paths concurrently (up to `concurrency` at a time using a semaphore), collects successes into `records` and failures into `errors`; must catch **all** exceptions per path (not just `ValueError`) and map each to a `PipelineError` with the correct path; must never raise regardless of how many files fail
- A `main()` entry point that reads a directory from `sys.argv[1]`, discovers all `.txt` files, runs the pipeline, and prints a summary: total processed, total errors, and each error path + reason
