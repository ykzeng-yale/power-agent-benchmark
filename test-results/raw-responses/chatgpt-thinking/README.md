# ChatGPT Thinking Mode — Raw Responses

Raw responses from automated Playwright-based ChatGPT Thinking Mode benchmark collection.

- **106/106 tasks collected** across all 4 tiers using GPT Thinking Mode
- Responses collected via automated browser interaction (no API)
- Each `.txt` file contains ChatGPT Thinking Mode's text response to one benchmark task
- **Note:** ChatGPT used Python Code Interpreter for these tasks, but code execution blocks were folded/collapsed in the UI and were not captured by the Playwright collector. The `.txt` files contain only the visible text output.

## Evaluation Results

**Results (LLM-based extraction):**

| Tier | Pass | Total | Rate |
|------|------|-------|------|
| Tier 1 | 18 | 30 | 60.0% |
| Tier 2 | 22 | 35 | 62.9% |
| Tier 3 | 15 | 20 | 75.0% |
| Tier 4 | 6 | 21 | 28.6% |
| **Overall** | **61** | **106** | **57.5%** |

See [evaluation/chatgpt-thinking/](../../evaluation/chatgpt-thinking/) for detailed per-task judgments.

## Files

- `t1-*.txt` through `t4-*.txt` — Raw ChatGPT Thinking Mode responses (106 files)
