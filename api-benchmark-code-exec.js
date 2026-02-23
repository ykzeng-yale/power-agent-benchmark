#!/usr/bin/env node
/**
 * API Benchmark Runner - WITH CODE EXECUTION enabled
 *
 * Tests OpenAI models with Code Interpreter and Gemini models with Code Execution.
 * This represents the default user experience on these platforms.
 *
 * Usage:
 *   node api-benchmark-code-exec.js --model gpt-5.2-code     # Run specific model
 *   node api-benchmark-code-exec.js --all                      # Run all models
 */

process.on('unhandledRejection', (err) => {
  console.error('[FATAL] Unhandled rejection:', err);
});
process.on('uncaughtException', (err) => {
  console.error('[FATAL] Uncaught exception:', err);
});

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import { GoogleGenerativeAI } from '@google/generative-ai';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ========================
// Configuration
// ========================

const API_KEYS = {
  openai: process.env.OPENAI_API_KEY || '',
  gemini: process.env.GEMINI_API_KEY || '',
};

const MODELS = [
  // OpenAI models with Code Interpreter
  { id: 'gpt-5.2', provider: 'openai', slug: 'gpt-5.2-code', displayName: 'GPT-5.2 + Code Interpreter' },
  { id: 'gpt-5.2-pro', provider: 'openai', slug: 'gpt-5.2-pro-code', displayName: 'GPT-5.2 Pro + Code Interpreter' },
  // Gemini models with Code Execution
  { id: 'gemini-2.5-pro', provider: 'gemini', slug: 'gemini-2.5-pro-code', displayName: 'Gemini 2.5 Pro + Code Execution' },
  { id: 'gemini-2.5-flash', provider: 'gemini', slug: 'gemini-2.5-flash-code', displayName: 'Gemini 2.5 Flash + Code Execution' },
  { id: 'gemini-3.1-pro-preview', provider: 'gemini', slug: 'gemini-3.1-pro-preview-code', displayName: 'Gemini 3.1 Pro Preview + Code Execution' },
];

const RATE_LIMITS = {
  openai: 3000,      // Slower due to code execution overhead
  gemini: 20000,     // Gemini rate limits
};

// Per-model delay overrides (some preview models have tighter limits)
const MODEL_RATE_LIMITS = {
  'gemini-3.1-pro-preview': 45000,  // 45s between requests for preview model
};

const MAX_RETRIES = 2;  // Reduced from 5 - preview model times out on some tasks
const TASKS_FILE = path.join(__dirname, 'all_tasks.json');
const OUTPUT_BASE = path.join(__dirname, 'test-results', 'raw-responses');

const SYSTEM_PROMPT = `You are a biostatistics expert. Answer the following statistical power analysis or sample size calculation question. You have access to code execution - use it to run R-equivalent calculations in Python (e.g., using scipy, statsmodels, or manual formulas). Provide your numerical answer clearly. If calculating sample size, round up to the nearest integer. Always state the final answer prominently.`;

// ========================
// API Clients
// ========================

let openaiClient, geminiClient;

function initClients() {
  openaiClient = new OpenAI({ apiKey: API_KEYS.openai });
  geminiClient = new GoogleGenerativeAI(API_KEYS.gemini);
}

// ========================
// API Call Functions - WITH CODE EXECUTION
// ========================

async function callOpenAIWithCode(modelId, question) {
  // All OpenAI models use the Responses API with code_interpreter tool
  const start = Date.now();
  const response = await openaiClient.responses.create({
    model: modelId,
    instructions: SYSTEM_PROMPT,
    input: question,
    tools: [
      {
        type: 'code_interpreter',
        container: { type: 'auto' }
      }
    ],
    max_output_tokens: 16384,
  });
  const latency = Date.now() - start;

  // Extract text from output messages (skip code_interpreter_call items)
  const textParts = [];
  const codeParts = [];
  for (const item of (response.output || [])) {
    if (item.type === 'message') {
      for (const c of (item.content || [])) {
        if (c.type === 'output_text') textParts.push(c.text);
      }
    } else if (item.type === 'code_interpreter_call') {
      codeParts.push({
        code: item.code || '',
        output: item.results?.map(r => r.text || r.content || '').join('\n') || ''
      });
    }
  }

  return {
    response_text: textParts.join('\n'),
    code_executed: codeParts,
    latency_ms: latency,
    tokens: {
      input: response.usage?.input_tokens || 0,
      output: response.usage?.output_tokens || 0,
      total: response.usage?.total_tokens || 0,
    },
    finish_reason: response.status || 'unknown',
    model_used: response.model || modelId,
    used_code: codeParts.length > 0,
  };
}

async function callGeminiWithCode(modelId, question) {
  const abortController = new AbortController();
  const model = geminiClient.getGenerativeModel({
    model: modelId,
    systemInstruction: SYSTEM_PROMPT,
    tools: [{ codeExecution: {} }],
  });

  const start = Date.now();
  const timeoutMs = 180000; // 3 minute timeout
  const timer = setTimeout(() => abortController.abort(), timeoutMs);
  let result;
  try {
    result = await model.generateContent({ contents: [{ role: 'user', parts: [{ text: question }] }] }, { signal: abortController.signal });
  } catch (err) {
    clearTimeout(timer);
    if (abortController.signal.aborted) {
      throw new Error('API call timed out after 5 minutes');
    }
    throw err;
  }
  clearTimeout(timer);
  const latency = Date.now() - start;
  const response = result.response;

  // Extract text and code parts
  const textParts = [];
  const codeParts = [];
  for (const candidate of (response.candidates || [])) {
    for (const part of (candidate.content?.parts || [])) {
      if (part.text) {
        textParts.push(part.text);
      } else if (part.executableCode) {
        codeParts.push({
          code: part.executableCode.code || '',
          language: part.executableCode.language || 'python'
        });
      } else if (part.codeExecutionResult) {
        codeParts.push({
          output: part.codeExecutionResult.output || '',
          outcome: part.codeExecutionResult.outcome || ''
        });
      }
    }
  }

  const usage = response.usageMetadata;

  return {
    response_text: textParts.join('\n'),
    code_executed: codeParts,
    latency_ms: latency,
    tokens: {
      input: usage?.promptTokenCount || 0,
      output: usage?.candidatesTokenCount || 0,
      total: usage?.totalTokenCount || 0,
    },
    finish_reason: response.candidates?.[0]?.finishReason || 'unknown',
    model_used: modelId,
    used_code: codeParts.length > 0,
  };
}

async function callModel(modelConfig, question) {
  switch (modelConfig.provider) {
    case 'openai':
      return callOpenAIWithCode(modelConfig.id, question);
    case 'gemini':
      return callGeminiWithCode(modelConfig.id, question);
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

      if (attempt === MAX_RETRIES) throw err;

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

  const delay = MODEL_RATE_LIMITS[modelConfig.id] || RATE_LIMITS[modelConfig.provider] || 3000;
  let completed = 0, failed = 0, skipped = 0, usedCode = 0;
  const startTime = Date.now();

  for (let i = 0; i < tasks.length; i++) {
    const task = tasks[i];

    if (responses[task.id] && (
      (responses[task.id].response_text && responses[task.id].response_text.length > 20) ||
      responses[task.id].error
    )) {
      skipped++;
      if (responses[task.id].used_code) usedCode++;
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
        code_executed: result.code_executed,
        used_code: result.used_code,
        latency_ms: result.latency_ms,
        tokens: result.tokens,
        finish_reason: result.finish_reason,
        model_used: result.model_used,
        timestamp: new Date().toISOString(),
      };

      completed++;
      if (result.used_code) usedCode++;

      if (result.finish_reason === 'length') {
        log(`    ⚠️ TRUNCATED (finish_reason=length)`);
      }

      const codeFlag = result.used_code ? ' [CODE]' : '';
      log(`    ✅ ${result.response_text.length}c, ${result.latency_ms}ms, ${result.tokens.total} tok${codeFlag}`);

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

    if (i < tasks.length - 1 && !responses[tasks[i + 1].id]) {
      await sleep(delay);
    }
  }

  const elapsed = Math.round((Date.now() - startTime) / 1000);
  const totalUsedCode = Object.values(responses).filter(r => r.used_code).length;

  const summary = {
    model: modelConfig.id,
    model_display: modelConfig.displayName,
    provider: modelConfig.provider,
    code_execution: true,
    total_tasks: tasks.length,
    completed: completed,
    failed: failed,
    skipped: skipped,
    used_code_count: totalUsedCode,
    elapsed_seconds: elapsed,
    timestamp: new Date().toISOString(),
  };
  fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));

  const readme = `# ${modelConfig.displayName} - Raw Responses (Code Execution Enabled)

- **Model**: \`${modelConfig.id}\`
- **Provider**: ${modelConfig.provider}
- **Code Execution**: Enabled
- **Tasks**: ${tasks.length}
- **Collected**: ${completed + skipped}
- **Failed**: ${failed}
- **Used Code**: ${totalUsedCode}/${tasks.length}
- **Date**: ${new Date().toISOString().split('T')[0]}
`;
  fs.writeFileSync(path.join(outputDir, 'README.md'), readme);

  log(`\n  📊 ${modelConfig.displayName}: ${completed} new, ${skipped} skipped, ${failed} failed, ${totalUsedCode} used code (${elapsed}s)\n`);

  return summary;
}

// ========================
// CLI Entry Point
// ========================

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--list')) {
    console.log('\nAvailable models (with code execution):');
    for (const m of MODELS) {
      console.log(`  ${m.slug.padEnd(32)} ${m.displayName.padEnd(40)} (${m.provider})`);
    }
    process.exit(0);
  }

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
    selectedModels = selectedModels.filter(m => m.provider === args[providerArg + 1]);
  }

  const tasks = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf8'));
  log(`\n🔬 Power Agent Benchmark - Code Execution Runner`);
  log(`📋 ${tasks.length} tasks | ${selectedModels.length} models\n`);

  initClients();
  logFile = path.join(__dirname, 'api-benchmark-code-exec.log');

  const allSummaries = [];

  for (const modelConfig of selectedModels) {
    log(`\n${'='.repeat(60)}`);
    log(`🤖 ${modelConfig.displayName} (${modelConfig.id})`);
    log(`   Provider: ${modelConfig.provider} | Code Execution: ON`);
    log(`${'='.repeat(60)}`);

    try {
      const summary = await runModelBenchmark(modelConfig, tasks);
      allSummaries.push(summary);
    } catch (err) {
      log(`\n❌ Fatal error for ${modelConfig.displayName}: ${err.message}`);
      allSummaries.push({
        model: modelConfig.id,
        model_display: modelConfig.displayName,
        error: err.message,
      });
    }
  }

  log(`\n${'='.repeat(60)}`);
  log(`✅ Benchmark complete!`);
  log(`📊 Results saved to: ${OUTPUT_BASE}`);
  for (const s of allSummaries) {
    if (s.error) {
      log(`  ❌ ${s.model_display}: ERROR - ${s.error.slice(0, 80)}`);
    } else {
      log(`  ✅ ${s.model_display}: ${s.completed + s.skipped}/${s.total_tasks}, ${s.used_code_count} used code, ${s.failed} failed`);
    }
  }
  log(`${'='.repeat(60)}\n`);
}

main().catch(e => {
  console.error('Fatal:', e);
  process.exit(1);
});
