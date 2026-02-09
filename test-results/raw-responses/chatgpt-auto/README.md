# ChatGPT Auto Mode — Raw Responses

Raw responses from automated Playwright-based ChatGPT benchmark collection.

- **106/106 tasks collected** across all 4 tiers using GPT auto mode
- Responses collected via automated browser interaction (no API)
- Each `.txt` file contains ChatGPT's text response to one benchmark task
- **Note:** ChatGPT used Python Code Interpreter for these tasks, but code execution blocks were folded/collapsed in the UI and were not captured by the Playwright collector. The `.txt` files contain only the visible text output.

## Corrected Evaluation Results

> **Note:** The initial commit reported "14.6% pass rate (15/103)" based on a flawed regex-based
> value extractor. That extractor frequently misidentified values in ChatGPT's natural language
> responses (e.g., extracting page numbers, formula coefficients, or intermediate values instead
> of final answers). The corrected evaluation uses **Claude Sonnet 4.5 as an LLM-based value
> extractor**, which accurately parses ChatGPT's prose responses.

**Corrected Results (LLM-based extraction):**

| Tier | Pass | Total | Rate |
|------|------|-------|------|
| Tier 1 | 17 | 30 | 56.7% |
| Tier 2 | 23 | 35 | 65.7% |
| Tier 3 | 14 | 20 | 70.0% |
| Tier 4 | 6 | 21 | 28.6% |
| **Overall** | **60** | **106** | **56.6%** |

See [evaluation/chatgpt-auto/](../../evaluation/chatgpt-auto/) for detailed per-task judgments.

## Files

- `t1-*.txt` through `t4-*.txt` — Raw ChatGPT responses (106 files)
- `agent_results.json` — Initial (flawed) regex extraction — **deprecated**
- `extracted_values.json` — Second regex extraction attempt — **deprecated**
- `collector.log` — Playwright collection log
- `runner.log` — Runner execution log
