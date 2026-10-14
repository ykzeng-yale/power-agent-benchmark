# GPT-5.2 Pro - Raw Responses

- **Model**: `gpt-5.2-pro`
- **Provider**: openai
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
  "model": "gpt-5.2-pro",
  "provider": "openai",
  "response_text": "full raw API response text",
  "latency_ms": 1234,
  "tokens": { "input": 100, "output": 500, "total": 600 },
  "finish_reason": "stop",
  "timestamp": "2026-02-21T..."
}
```
