#!/usr/bin/env node
/**
 * API Benchmark Runner - Collects raw responses from multiple LLM APIs
 *
 * Usage:
 *   node api-benchmark-runner.js                    # Run all models
 *   node api-benchmark-runner.js --model gpt-5.2    # Run specific model
 *   node api-benchmark-runner.js --provider openai  # Run all models from a provider
 *   node api-benchmark-runner.js --list              # List all models
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import Anthropic from '@anthropic-ai/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ========================
// Configuration
// ========================

const API_KEYS = {
  openai: process.env.OPENAI_API_KEY || '',
  anthropic: process.env.ANTHROPIC_API_KEY || '',
  gemini: process.env.GEMINI_API_KEY || '',
};

const MODELS = [
  // OpenAI models
  { id: 'gpt-5.2', provider: 'openai', slug: 'gpt-5.2', displayName: 'GPT-5.2', isReasoning: false },
  { id: 'gpt-5.2-pro', provider: 'openai', slug: 'gpt-5.2-pro', displayName: 'GPT-5.2 Pro', isReasoning: true },
  // Anthropic models
  { id: 'claude-opus-4-6', provider: 'anthropic', slug: 'claude-opus-4-6', displayName: 'Claude Opus 4.6' },
  { id: 'claude-sonnet-4-6', provider: 'anthropic', slug: 'claude-sonnet-4-6', displayName: 'Claude Sonnet 4.6' },
  // Gemini models
  { id: 'gemini-2.5-pro', provider: 'gemini', slug: 'gemini-2.5-pro', displayName: 'Gemini 2.5 Pro' },
  { id: 'gemini-2.5-flash', provider: 'gemini', slug: 'gemini-2.5-flash', displayName: 'Gemini 2.5 Flash' },
  { id: 'gemini-3.1-pro-preview', provider: 'gemini', slug: 'gemini-3.1-pro-preview', displayName: 'Gemini 3.1 Pro Preview' },
];

// Rate limiting: delay between requests (ms) per provider
const RATE_LIMITS = {
  openai: 1500,      // ~40 RPM safe margin
  anthropic: 2000,   // ~30 RPM safe margin
  gemini: 20000,     // ~3 RPM - Gemini free tier has strict RPM+TPM quota
};

const MAX_RETRIES = 5;
const TASKS_FILE = path.join(__dirname, 'all_tasks.json');
const OUTPUT_BASE = path.join(__dirname, 'test-results', 'raw-responses');

// System prompt for the benchmark
const SYSTEM_PROMPT = `You are a biostatistics expert. Answer the following statistical power analysis or sample size calculation question. Provide your numerical answer clearly. Show your work/reasoning, then state the final answer prominently. If calculating sample size, round up to the nearest integer.`;

// ========================
// API Clients
// ========================

let openaiClient, anthropicClient, geminiClient;

function initClients() {
  openaiClient = new OpenAI({ apiKey: API_KEYS.openai });
  anthropicClient = new Anthropic({ apiKey: API_KEYS.anthropic });
  geminiClient = new GoogleGenerativeAI(API_KEYS.gemini);
}

// ========================
// API Call Functions
// ========================

async function callOpenAI(modelId, question, isReasoning) {
  // gpt-5.2-pro uses Responses API, not Chat Completions
  if (modelId.includes('5.2-pro') || modelId.includes('5-pro')) {
    return callOpenAIResponses(modelId, question);
  }

  const params = {
    model: modelId,
    messages: [
      ...(isReasoning ? [] : [{ role: 'system', content: SYSTEM_PROMPT }]),
      { role: 'user', content: isReasoning ? `${SYSTEM_PROMPT}\n\n${question}` : question }
    ],
    max_completion_tokens: 16384,
  };

  // Non-reasoning models use temperature
  if (!isReasoning) {
    params.temperature = 0;
  }

  const start = Date.now();
  const response = await openaiClient.chat.completions.create(params);
  const latency = Date.now() - start;

  return {
    response_text: response.choices[0]?.message?.content || '',
    latency_ms: latency,
    tokens: {
      input: response.usage?.prompt_tokens || 0,
      output: response.usage?.completion_tokens || 0,
      total: response.usage?.total_tokens || 0,
    },
    finish_reason: response.choices[0]?.finish_reason || 'unknown',
    model_used: response.model || modelId,
  };
}

async function callOpenAIResponses(modelId, question) {
  const start = Date.now();
  const response = await openaiClient.responses.create({
    model: modelId,
    instructions: SYSTEM_PROMPT,
    input: question,
    max_output_tokens: 16384,
  });
  const latency = Date.now() - start;

  // Extract text from output messages
  const text = response.output
    ?.filter(o => o.type === 'message')
    .flatMap(o => o.content?.filter(c => c.type === 'output_text').map(c => c.text) || [])
    .join('\n') || '';

  return {
    response_text: text,
    latency_ms: latency,
    tokens: {
      input: response.usage?.input_tokens || 0,
      output: response.usage?.output_tokens || 0,
      total: response.usage?.total_tokens || 0,
    },
    finish_reason: response.status || 'unknown',
    model_used: response.model || modelId,
  };
}

async function callAnthropic(modelId, question) {
  const start = Date.now();
  const response = await anthropicClient.messages.create({
    model: modelId,
    max_tokens: 16384,
    system: SYSTEM_PROMPT,
    messages: [
      { role: 'user', content: question }
    ],
  });
  const latency = Date.now() - start;

  const text = response.content
    .filter(c => c.type === 'text')
    .map(c => c.text)
    .join('\n');

  return {
    response_text: text,
    latency_ms: latency,
    tokens: {
      input: response.usage?.input_tokens || 0,
      output: response.usage?.output_tokens || 0,
      total: (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0),
    },
    finish_reason: response.stop_reason || 'unknown',
    model_used: response.model || modelId,
  };
}

async function callGemini(modelId, question) {
  const model = geminiClient.getGenerativeModel({
    model: modelId,
    systemInstruction: SYSTEM_PROMPT,
    generationConfig: {
      // Limit thinking tokens to reduce TPM usage on free tier
      thinkingConfig: { thinkingBudget: 2048 },
    },
  });

  const start = Date.now();
  const result = await model.generateContent(question);
  const latency = Date.now() - start;
  const response = result.response;
  const text = response.text();
  const usage = response.usageMetadata;

  return {
    response_text: text,
    latency_ms: latency,
    tokens: {
      input: usage?.promptTokenCount || 0,
      output: usage?.candidatesTokenCount || 0,
      total: usage?.totalTokenCount || 0,
    },
    finish_reason: response.candidates?.[0]?.finishReason || 'unknown',
    model_used: modelId,
  };
}

async function callModel(modelConfig, question) {
  switch (modelConfig.provider) {
    case 'openai':
      return callOpenAI(modelConfig.id, question, modelConfig.isReasoning);
    case 'anthropic':
      return callAnthropic(modelConfig.id, question);
    case 'gemini':
      return callGemini(modelConfig.id, question);
    default:
      throw new Error(`Unknown provider: ${modelConfig.provider}`);
  }
}

// ========================
// Retry Logic
// ========================

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function callWithRetry(modelConfig, question, taskId) {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      return await callModel(modelConfig, question);
    } catch (err) {
      const isRateLimit = err.status === 429 || err.message?.includes('rate') || err.message?.includes('429');
      const isOverloaded = err.status === 529 || err.status === 503 || err.message?.includes('overloaded');

      if (attempt === MAX_RETRIES) {
        throw err;
      }

      if (isRateLimit || isOverloaded) {
        const backoff = Math.min(120000, (2 ** attempt) * 10000);
        log(`  ⏳ Rate limited on ${taskId}, waiting ${backoff/1000}s (attempt ${attempt}/${MAX_RETRIES})...`);
        await sleep(backoff);
      } else {
        const backoff = (2 ** attempt) * 2000;
        log(`  ⚠️ Error on ${taskId}: ${err.message?.slice(0, 100)}, retrying in ${backoff/1000}s...`);
        await sleep(backoff);
      }
    }
  }
}

// ========================
// Logging
// ========================

let logFile = null;

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  if (logFile) fs.appendFileSync(logFile, line + '\n');
}

// ========================
// Main Runner
// ========================

async function runModelBenchmark(modelConfig, tasks) {
  const slug = modelConfig.slug;
  const outputDir = path.join(OUTPUT_BASE, slug);
  const responsesFile = path.join(outputDir, 'raw-responses.json');
  const summaryFile = path.join(outputDir, 'summary.json');

  fs.mkdirSync(outputDir, { recursive: true });

  // Load existing responses for resume support
  let responses = {};
  if (fs.existsSync(responsesFile)) {
    try {
      responses = JSON.parse(fs.readFileSync(responsesFile, 'utf8'));
      log(`  📂 Loaded ${Object.keys(responses).length} existing responses for ${slug}`);
    } catch { responses = {}; }
  }

  const delay = RATE_LIMITS[modelConfig.provider] || 2000;
  let completed = 0, failed = 0, skipped = 0;
  const startTime = Date.now();

  for (let i = 0; i < tasks.length; i++) {
    const task = tasks[i];

    // Skip if already collected
    if (responses[task.id] && responses[task.id].response_text && responses[task.id].response_text.length > 20) {
      skipped++;
      continue;
    }

    log(`  [${i + 1}/${tasks.length}] ${task.id} (tier${task.tier})`);

    try {
      const result = await callWithRetry(modelConfig, task.question, task.id);

      responses[task.id] = {
        task_id: task.id,
        tier: task.tier,
        question: task.question,
        model: modelConfig.id,
        model_display: modelConfig.displayName,
        provider: modelConfig.provider,
        response_text: result.response_text,
        latency_ms: result.latency_ms,
        tokens: result.tokens,
        finish_reason: result.finish_reason,
        model_used: result.model_used,
        timestamp: new Date().toISOString(),
      };

      completed++;

      // Check for potential truncation
      if (result.finish_reason === 'length') {
        log(`    ⚠️ TRUNCATED (finish_reason=length) - response may be incomplete`);
      }

      log(`    ✅ ${result.response_text.length}c, ${result.latency_ms}ms, ${result.tokens.total} tokens`);

      // Save after each response (crash-safe)
      fs.writeFileSync(responsesFile, JSON.stringify(responses, null, 2));

    } catch (err) {
      log(`    ❌ FAILED: ${err.message?.slice(0, 200)}`);
      responses[task.id] = {
        task_id: task.id,
        tier: task.tier,
        question: task.question,
        model: modelConfig.id,
        provider: modelConfig.provider,
        error: err.message?.slice(0, 500),
        timestamp: new Date().toISOString(),
      };
      failed++;
      fs.writeFileSync(responsesFile, JSON.stringify(responses, null, 2));
    }

    // Rate limit delay
    if (i < tasks.length - 1 && !responses[tasks[i + 1].id]) {
      await sleep(delay);
    }
  }

  const elapsed = Math.round((Date.now() - startTime) / 1000);

  // Write summary
  const summary = {
    model: modelConfig.id,
    model_display: modelConfig.displayName,
    provider: modelConfig.provider,
    total_tasks: tasks.length,
    completed: completed,
    failed: failed,
    skipped: skipped,
    elapsed_seconds: elapsed,
    timestamp: new Date().toISOString(),
  };
  fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));

  // Write README
  const readme = `# ${modelConfig.displayName} - Raw Responses

- **Model**: \`${modelConfig.id}\`
- **Provider**: ${modelConfig.provider}
- **Tasks**: ${tasks.length}
- **Collected**: ${completed + skipped}
- **Failed**: ${failed}
- **Date**: ${new Date().toISOString().split('T')[0]}

## Files

- \`raw-responses.json\` - Full raw responses for all ${tasks.length} tasks
- \`summary.json\` - Collection summary statistics

## Format

Each entry in \`raw-responses.json\`:
\`\`\`json
{
  "task_id": "t1-ttest-001",
  "tier": 1,
  "question": "...",
  "model": "${modelConfig.id}",
  "provider": "${modelConfig.provider}",
  "response_text": "full raw API response text",
  "latency_ms": 1234,
  "tokens": { "input": 100, "output": 500, "total": 600 },
  "finish_reason": "stop",
  "timestamp": "2026-02-21T..."
}
\`\`\`
`;
  fs.writeFileSync(path.join(outputDir, 'README.md'), readme);

  log(`\n  📊 ${modelConfig.displayName}: ${completed} new, ${skipped} skipped, ${failed} failed (${elapsed}s)\n`);

  return summary;
}

// ========================
// CLI Entry Point
// ========================

async function main() {
  const args = process.argv.slice(2);

  // --list flag
  if (args.includes('--list')) {
    console.log('\nAvailable models:');
    for (const m of MODELS) {
      console.log(`  ${m.slug.padEnd(28)} ${m.displayName.padEnd(25)} (${m.provider})`);
    }
    process.exit(0);
  }

  // Filter by --model or --provider
  let selectedModels = [...MODELS];
  const modelArg = args.indexOf('--model');
  if (modelArg !== -1 && args[modelArg + 1]) {
    const target = args[modelArg + 1];
    selectedModels = MODELS.filter(m => m.slug === target || m.id === target);
    if (selectedModels.length === 0) {
      console.error(`Model not found: ${target}`);
      process.exit(1);
    }
  }
  const providerArg = args.indexOf('--provider');
  if (providerArg !== -1 && args[providerArg + 1]) {
    const target = args[providerArg + 1];
    selectedModels = selectedModels.filter(m => m.provider === target);
  }

  // Load tasks
  const tasks = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf8'));
  log(`\n🔬 Power Agent Benchmark - API Runner`);
  log(`📋 ${tasks.length} tasks | ${selectedModels.length} models\n`);

  initClients();
  logFile = path.join(__dirname, 'api-benchmark-runner.log');

  const allSummaries = [];

  for (const modelConfig of selectedModels) {
    log(`\n${'='.repeat(60)}`);
    log(`🤖 ${modelConfig.displayName} (${modelConfig.id})`);
    log(`   Provider: ${modelConfig.provider}`);
    log(`${'='.repeat(60)}`);

    try {
      const summary = await runModelBenchmark(modelConfig, tasks);
      allSummaries.push(summary);
    } catch (err) {
      log(`\n❌ Fatal error for ${modelConfig.displayName}: ${err.message}`);
      allSummaries.push({
        model: modelConfig.id,
        model_display: modelConfig.displayName,
        provider: modelConfig.provider,
        error: err.message,
      });
    }
  }

  // Write overall summary
  const overallFile = path.join(OUTPUT_BASE, 'api-benchmark-summary.json');
  fs.writeFileSync(overallFile, JSON.stringify({
    timestamp: new Date().toISOString(),
    models_tested: allSummaries.length,
    summaries: allSummaries,
  }, null, 2));

  log(`\n${'='.repeat(60)}`);
  log(`✅ Benchmark complete!`);
  log(`📊 Results saved to: ${OUTPUT_BASE}`);
  for (const s of allSummaries) {
    if (s.error) {
      log(`  ❌ ${s.model_display}: ERROR - ${s.error.slice(0, 80)}`);
    } else {
      log(`  ✅ ${s.model_display}: ${s.completed + s.skipped}/${s.total_tasks} collected, ${s.failed} failed`);
    }
  }
  log(`${'='.repeat(60)}\n`);
}

main().catch(e => {
  console.error('Fatal:', e);
  process.exit(1);
});
