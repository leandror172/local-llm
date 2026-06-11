# Ollama Monitoring Setup

<!-- ref:ollama-monitoring -->
## Architecture

Port-swap proxy pattern — all existing clients remain unchanged:

```
Clients → :11434 (ollama-metrics proxy) → :11435 (Ollama)
                      ↓
               /metrics (Prometheus format)
                      ↓
              Prometheus :9090 (Docker)
                      ↓
               Grafana :3000 (Docker)
```

**Why port swap over client reconfigure:** The MCP bridge, benchmarks, Claude Code tools,
and Aider all hardcode `:11434`. Rerouting clients would require changes across three repos.
Moving Ollama to `:11435` (one systemd env var) is strictly less disruptive.

## Components

| Component | Location | How to start |
|---|---|---|
| ollama-metrics proxy | `~/workspaces/clones/ollama-metrics/` | `systemctl start ollama-metrics` (auto-starts with Ollama) |
| Prometheus | Docker (`prometheus_monitoring` network) | `make stack` |
| Grafana | Docker, port 3000 | included in `make stack` |

Makefile lives at `~/workspaces/clones/ollama-metrics/Makefile`.
Systemd unit: `/etc/systemd/system/ollama-metrics.service` — `After=ollama.service`, `Restart=on-failure`.

## Ollama Systemd Config

`OLLAMA_HOST=0.0.0.0:11435` set via `sudo systemctl edit ollama`.
All other env vars unchanged (`OLLAMA_FLASH_ATTENTION`, `OLLAMA_KV_CACHE_TYPE=q8_0`, etc.).

## Docker-Compose Modifications (from upstream)

Repo: `https://github.com/NorskHelsenett/ollama-metrics`
Modified files in `prometheus/`:

1. **`docker-compose.yml`** — removed `node-exporter` service (WSL2 `/sys` mount issues);
   changed Prometheus from `expose: 9090` to `ports: ["9090:9090"]`
2. **`prometheus.yml`** — removed `node` scrape job; reverted ollama target to
   `host.docker.internal:11434` (works correctly with `extra_hosts: host-gateway`)

## WSL2 Networking Gotcha

`host.docker.internal` in Docker Desktop with WSL2 resolves to the **Windows host**
(`192.168.100.101`), not the WSL2 instance where Ollama and the proxy run.

Correct address for reaching WSL2 from a Docker container: the **bridge network gateway**
(`172.18.0.1` for the `prometheus_monitoring` network — the container's default route).

Diagnosis: `docker exec prometheus ip route | grep default` shows the gateway.
Verification: `docker exec prometheus wget -qO- http://172.18.0.1:11434/metrics`.

## Grafana Dashboard

Pre-built dashboard at `prometheus/dashboard.json` in the repo.

**Import:** Grafana (`localhost:3000`, admin/password) → Dashboards → Import → Upload JSON.
The import dialog will prompt for a Prometheus datasource — select the one you add (URL: `http://prometheus:9090`).

**Panels available:**
- Average Token Generation Time by Model
- Most Used Models
- Models Loaded
- Request Duration (p95)
- Token Generation Time (p95)
- Token Generation Rate (per model)
- Generated Tokens by Model
- Prompt Tokens by Model

**Empty panels:** CPU and MEM (relied on node-exporter, which was removed due to WSL2
`/sys` mount issues). GPU metrics come from `nvidia-smi` separately if needed.

## Metrics Collected (by proxy)

Verified against actual output (`curl localhost:11434/metrics | grep ollama` after a real request):

| Metric | Type | Labels | Notes |
|---|---|---|---|
| `ollama_generated_tokens_total` | counter | model | |
| `ollama_prompt_tokens_total` | counter | model | |
| `ollama_request_duration_seconds` | histogram | endpoint, model | buckets: 0.1s–60s |
| `ollama_time_per_token_seconds` | histogram | model | buckets: 0.01s–2s |
| `ollama_model_ram_mb` | gauge | model | MB (not bytes) |
| `ollama_model_loaded` | gauge | model | 0 or 1 — per model |
| `ollama_loaded_models` | gauge | — | total count of loaded models |

Request count: use `ollama_request_duration_seconds_count` (no separate `_requests_total` counter).

## Deferred

- **Systemd unit for proxy:** done (2026-05-30) — `/etc/systemd/system/ollama-metrics.service`.
- **Systemd unit for Prometheus+Grafana stack:** `make stack` still manual. Deferred — tracked in `.claude/tasks.md`.
- **Native `/metrics` endpoint PR #11159:** OTel-based, per-model labels, 41+ commits, actively
  rebased since June 2025, not yet merged. When merged, port-swap proxy becomes unnecessary.
  PR: `https://github.com/ollama/ollama/pull/11159`
<!-- /ref:ollama-monitoring -->
