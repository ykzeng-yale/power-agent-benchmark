# Gemini 2.5 Flash - Raw Responses

- **Model**: `gemini-2.5-flash`
- **Provider**: gemini
- **Tasks**: 106
- **Collected**: 106
- **Failed**: 0
- **Date**: 2026-02-22

## Files

- `raw-responses.json` - Full raw responses for all 106 tasks
- `summary.json` - Collection summary statistics

## Format

Each entry in `raw-responses.json`:
```json
{
  "task_id": "t1-ttest-001",
  "tier": 1,
  "question": "...",
  "model": "gemini-2.5-flash",
  "provider": "gemini",
  "response_text": "full raw API response text",
  "latency_ms": 1234,
  "tokens": { "input": 100, "output": 500, "total": 600 },
  "finish_reason": "stop",
  "timestamp": "2026-02-21T..."
}
```
