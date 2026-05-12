# Ollama Analysis Tools

Quick reference for DPO evaluation analysis scripts.

## Scripts

### `ollama-stats.py` — Overall Stats
Analyze total calls, model usage breakdown, and verdict distribution.

```bash
./.claude/tools/ollama-stats.py           # All reports
./.claude/tools/ollama-stats.py --by-model    # Model breakdown only
./.claude/tools/ollama-stats.py --verdicts    # Verdict distribution only
```

**Sample output:**
```
Total records:     225
Call records:      185
Verdict records:   40
Verdict coverage:  21.6%

ACCEPTED      5 ( 12.5%)
IMPROVED     28 ( 70.0%)
REJECTED      7 ( 17.5%)
```

### `ollama-verdicts.py` — Verdict Analysis
Explore individual verdicts and find failure patterns.

```bash
./.claude/tools/ollama-verdicts.py                # All verdicts with details
./.claude/tools/ollama-verdicts.py ACCEPTED       # Only ACCEPTED verdicts
./.claude/tools/ollama-verdicts.py IMPROVED       # Only IMPROVED verdicts
./.claude/tools/ollama-verdicts.py REJECTED       # Only REJECTED verdicts
./.claude/tools/ollama-verdicts.py --summary      # Stats only
./.claude/tools/ollama-verdicts.py --hints        # Rejection patterns
```

**Sample output (--hints):**
```
Total rejections: 7

Common failure reasons:
  type            4 (57%)
  wrong           2 (29%)
  error           1 (14%)
```

## Data Source

Both scripts analyze: `~/.local/share/ollama-bridge/calls.jsonl`

Records include:
- **Call records**: Ollama model invocations (model, prompt, response, latency)
- **Verdict records**: Your evaluations (ACCEPTED/IMPROVED/REJECTED + reason + token estimate)

Verdicts are linked to calls via `prompt_hash` for traceability.

## Workflow Example

1. **Check overall progress:**
   ```bash
   ./.claude/tools/ollama-stats.py
   ```

2. **Find problem patterns:**
   ```bash
   ./.claude/tools/ollama-verdicts.py --hints
   ```

3. **Review specific rejections:**
   ```bash
   ./.claude/tools/ollama-verdicts.py REJECTED
   ```

4. **Analyze high-token estimates:**
   ```bash
   ./.claude/tools/ollama-verdicts.py IMPROVED | grep tokens
   ```

## Token Estimate Notes

When you evaluate outputs, provide rough Claude token estimates:
- Ballpark: `(prompt_chars + response_chars) / 4`
- Used for DPO fine-tuning data quality assessment
- Logged to `calls.jsonl` for analysis
