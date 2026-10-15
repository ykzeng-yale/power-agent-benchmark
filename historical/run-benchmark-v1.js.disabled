#!/usr/bin/env node

/**
 * Power Agent Benchmark Runner with SSE Support
 * Runs benchmark tasks against the Power Agent API and evaluates results
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import path from 'path';
import { config as dotenvConfig } from 'dotenv';
import Anthropic from '@anthropic-ai/sdk';

// Load environment variables from parent directory
dotenvConfig({ path: '../.env' });

const BACKEND_URL = process.env.POWER_AGENT_API_URL || 'https://power-agent-api-927325869269.us-central1.run.app';
const anthropic = new Anthropic();

/**
 * Run a single task against the Power Agent API with retry logic
 */
async function runTask(task, taskIndex, verbose = false, retryCount = 0) {
  const maxRetries = 3;
  const sessionId = `bench-${task.id}-${Date.now()}`;
  const startTime = Date.now();

  if (verbose) {
    console.log(`  [${taskIndex}] Starting: ${task.id}${retryCount > 0 ? ` (retry ${retryCount})` : ''}`);
  }

  const requestBody = {
    query: task.question,
    mode: 'full_analysis',
    sessionId: sessionId
  };

  try {
    const response = await fetch(`${BACKEND_URL}/api/analyze-biostat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      // Retry on 529 (overloaded) or 503 (service unavailable)
      if ((response.status === 529 || response.status === 503) && retryCount < maxRetries) {
        const waitTime = Math.pow(2, retryCount) * 10000; // Exponential backoff: 10s, 20s, 40s
        console.log(`  [${taskIndex}] API overloaded, waiting ${waitTime/1000}s before retry...`);
        await new Promise(r => setTimeout(r, waitTime));
        return runTask(task, taskIndex, verbose, retryCount + 1);
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Read the SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = '';
    let steps = [];
    let fullText = '';
    let outputFiles = [];
    let analysisOutput = '';
    let conclusionText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6));
            steps.push(data);

            // Collect relevant data
            if (data.step === 'chatbot_intro_stream' && data.text) {
              fullText += data.text;
            }
            if (data.step === 'chatbot_conclusion_stream' && data.text) {
              conclusionText += data.text;
            }
            if (data.step === 'outputs' && data.files) {
              outputFiles = data.files;
            }
            if (data.step === 'executing' && data.output) {
              analysisOutput += data.output + '\n';
            }
          } catch (e) {
            // Ignore parse errors
          }
        }
      }
    }

    const duration = Date.now() - startTime;

    // Check if agent actually produced analysis output (not just intro)
    const hasAnalysis = analysisOutput.trim().length > 0 || conclusionText.trim().length > 0;
    if (!hasAnalysis && retryCount < maxRetries) {
      console.log(`  [${taskIndex}] No analysis output for ${task.id} (only intro), retrying... (attempt ${retryCount + 1}/${maxRetries})`);
      await new Promise(r => setTimeout(r, 5000 * (retryCount + 1)));
      return runTask(task, taskIndex, verbose, retryCount + 1);
    }

    if (verbose) {
      console.log(`  [${taskIndex}] Completed: ${task.id} (${(duration/1000).toFixed(1)}s, ${steps.length} steps)`);
    }

    return {
      taskId: task.id,
      success: true,
      duration,
      steps,
      response: {
        introText: fullText,
        conclusionText: conclusionText,
        analysisOutput: analysisOutput,
        outputFiles: outputFiles,
        stepCount: steps.length
      }
    };

  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`  [${taskIndex}] Failed: ${task.id} - ${error.message}`);

    return {
      taskId: task.id,
      success: false,
      duration,
      error: error.message,
      steps: [],
      response: null
    };
  }
}

/**
 * Evaluate a task result using LLM-as-judge
 * LLM handles BOTH scoring AND metric extraction (no regex)
 */
async function evaluateResult(task, result) {
  if (!result.success || !result.response) {
    return {
      taskId: task.id,
      passed: false,
      totalScore: 0,
      scores: { templateSelection: 0, parameterExtraction: 0, calculationAccuracy: 0, codeQuality: 0, interpretationQuality: 0 },
      error: result.error || 'No response received'
    };
  }

  const groundTruth = task.ground_truth;
  const tolerance = task.tolerance;

  // Determine expected value and type
  const expectedN = groundTruth.per_cell || groundTruth.patients_per_cluster ||
    groundTruth.subjects_per_cluster || groundTruth.subjects_per_cluster_period ||
    groundTruth.students_per_classroom ||
    groundTruth.subjects_per_group || groundTruth.subjects_per_arm ||
    groundTruth.sample_size_per_group || groundTruth.sample_size ||
    groundTruth.subjects || groundTruth.total_sample_size || groundTruth.total_subjects;
  const toleranceN = tolerance.sample_size || tolerance.subjects || tolerance.clusters || 20;

  // Determine the unit the ground truth uses
  let gtUnit = 'total';
  if (groundTruth.per_cell) gtUnit = 'per cell';
  else if (groundTruth.patients_per_cluster || groundTruth.subjects_per_cluster) gtUnit = 'per cluster';
  else if (groundTruth.subjects_per_cluster_period) gtUnit = 'per cluster-period';
  else if (groundTruth.students_per_classroom) gtUnit = 'per classroom';
  else if (groundTruth.subjects_per_group || groundTruth.subjects_per_arm || groundTruth.sample_size_per_group) gtUnit = 'per group';
  else if (groundTruth.sample_size || groundTruth.subjects) gtUnit = 'total or per group';

  const hasAnySampleSizeField = expectedN != null;

  // Detect effect size tasks (e.g., "what effect size can we detect?")
  const isEffectSizeTask = !hasAnySampleSizeField && (groundTruth.detectable_effect_d != null || groundTruth.detectable_effect_size != null);
  const effectSizeExpected = groundTruth.detectable_effect_d || groundTruth.detectable_effect_size;
  const effectSizeTolerance = tolerance.effect_size || 0.05;

  const isPowerTask = groundTruth.power && !hasAnySampleSizeField && !isEffectSizeTask;

  // Build expected values string
  let expectedValues = '';
  for (const [key, val] of Object.entries(groundTruth)) {
    if (val != null) {
      const tolKey = key.includes('power') ? 'power' : 'sample_size';
      const tolVal = tolerance[tolKey] || '';
      expectedValues += `- ${key}: ${val}${tolVal ? ` (±${tolVal})` : ''}\n`;
    }
  }

  const prompt = `You are an expert biostatistician evaluating a power analysis agent's response.

IMPORTANT: Focus on RESULT ACCURACY. Do NOT penalize for using different R packages.

## TASK
Question: ${task.question}

## EXPECTED RESULTS
${expectedValues}
The PRIMARY metric to extract is: ${isEffectSizeTask ? 'detectable effect size (Cohen d)' : isPowerTask ? 'power' : `sample size (${gtUnit})`}
Expected value: ${isEffectSizeTask ? effectSizeExpected : isPowerTask ? groundTruth.power : expectedN} (±${isEffectSizeTask ? effectSizeTolerance : isPowerTask ? (tolerance.power || 0.05) : toleranceN})

## AGENT RESPONSE
Introduction: ${result.response.introText?.substring(0, 1000) || 'N/A'}

Analysis Output: ${result.response.analysisOutput?.substring(0, 3000) || 'N/A'}

Conclusion: ${result.response.conclusionText?.substring(0, 2000) || 'N/A'}

## CRITICAL EXTRACTION INSTRUCTIONS
Extract the agent's FINAL RECOMMENDED ${isEffectSizeTask ? 'detectable effect size (Cohen d)' : isPowerTask ? 'power value' : 'sample size'} from the response.
- Look at the CONCLUSION section first — that contains the final recommendation
- If the agent mentions multiple values (e.g., analytical vs simulation), extract the FINAL RECOMMENDED value
- For sample size: extract the value that matches the unit "${gtUnit}" (not total if we need per-group, not per-group if we need total)
- For power: extract as a decimal (0.80, not 80%)
- For effect size: extract the detectable Cohen's d value as a decimal
- If the agent recommends a different unit than expected, convert appropriately

## EVALUATION
Score each criterion (total 100 points):
1. Template Selection (20): Correct analysis type?
2. Parameter Extraction (20): Parameters correctly identified?
3. Calculation Accuracy (30): Is the FINAL RECOMMENDED value within tolerance? Score 30 if within ±${isEffectSizeTask ? effectSizeTolerance : isPowerTask ? (tolerance.power || 0.05) : toleranceN}, 15-25 if close, 0-15 if far off
4. Code Quality (15): Would code produce correct results?
5. Interpretation (15): Results properly explained?

Respond with JSON only:
{
  "scores": {"templateSelection": <0-20>, "parameterExtraction": <0-20>, "calculationAccuracy": <0-30>, "codeQuality": <0-15>, "interpretationQuality": <0-15>},
  "totalScore": <0-100>,
  "passed": <true if >= 70>,
  "agentValue": <the agent's FINAL RECOMMENDED ${isEffectSizeTask ? 'detectable effect size' : isPowerTask ? 'power' : 'sample size'} as a number, or null if not found>,
  "agentValueUnit": "<unit: 'per group', 'per cell', 'per cluster', 'total', 'power', etc.>",
  "expectedValue": ${isEffectSizeTask ? effectSizeExpected : isPowerTask ? groundTruth.power : expectedN},
  "valueDifference": <absolute difference between agent value and expected, or null>,
  "withinTolerance": <true if |agentValue - expectedValue| <= ${isEffectSizeTask ? effectSizeTolerance : isPowerTask ? (tolerance.power || 0.05) : toleranceN}>,
  "justification": "<brief explanation of scoring>"
}`;

  try {
    const response = await anthropic.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1500,
      temperature: 0,
      messages: [{ role: 'user', content: prompt }]
    });

    const content = response.content[0].text;
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const evaluation = JSON.parse(jsonMatch[0]);
      evaluation.taskId = task.id;
      evaluation.tier = task.tier;
      evaluation.template = task.template;

      // STRICT tolerance enforcement using LLM-extracted values
      if (evaluation.agentValue != null) {
        const expected = isEffectSizeTask ? effectSizeExpected : isPowerTask ? groundTruth.power : expectedN;
        const tol = isEffectSizeTask ? effectSizeTolerance : isPowerTask ? (tolerance.power || 0.03) : toleranceN;
        const diff = Math.abs(evaluation.agentValue - expected);
        const isWithin = diff <= tol;

        if (isWithin && evaluation.scores?.calculationAccuracy < 30) {
          // Within tolerance: boost to full score
          const boost = 30 - evaluation.scores.calculationAccuracy;
          evaluation.scores.calculationAccuracy = 30;
          evaluation.totalScore = (evaluation.totalScore || 0) + boost;
          evaluation.toleranceBoostApplied = true;
          evaluation.withinTolerance = true;
        } else if (!isWithin && evaluation.scores?.calculationAccuracy > 0) {
          // OUTSIDE tolerance: force to 0 and fail
          evaluation.totalScore = (evaluation.totalScore || 0) - evaluation.scores.calculationAccuracy;
          evaluation.scores.calculationAccuracy = 0;
          evaluation.toleranceForcedFail = true;
          evaluation.withinTolerance = false;
        }
        evaluation.valueDifference = diff;
      }
      // Strict pass: must have calculationAccuracy > 0 AND total >= 70
      evaluation.passed = (evaluation.totalScore || 0) >= 70 && (evaluation.scores?.calculationAccuracy || 0) > 0;

      return evaluation;
    }
  } catch (error) {
    console.error(`  Evaluation error for ${task.id}: ${error.message}`);
  }

  return {
    taskId: task.id,
    passed: false,
    totalScore: 0,
    scores: { templateSelection: 0, parameterExtraction: 0, calculationAccuracy: 0, codeQuality: 0, interpretationQuality: 0 },
    error: 'Evaluation failed'
  };
}

/**
 * Run benchmark for a specific tier
 */
async function runTierBenchmark(tier, concurrency = 5, verbose = true) {
  const filePath = `../tasks/tier${tier}/tasks.json`;
  const content = await readFile(filePath, 'utf-8');
  const data = JSON.parse(content);
  const tasks = data.tasks.map(t => ({ ...t, tier }));

  console.log(`\n${'═'.repeat(70)}`);
  console.log(`TIER ${tier}: ${data.name}`);
  console.log(`${'═'.repeat(70)}`);
  console.log(`Tasks: ${tasks.length}, Concurrency: ${concurrency}`);
  console.log(`${'─'.repeat(70)}`);

  const results = [];
  const evaluations = [];
  const startTime = Date.now();

  // Process in batches
  for (let i = 0; i < tasks.length; i += concurrency) {
    const batch = tasks.slice(i, Math.min(i + concurrency, tasks.length));
    console.log(`\nBatch ${Math.floor(i/concurrency) + 1}: Tasks ${i+1}-${Math.min(i+concurrency, tasks.length)}`);

    // Run tasks in parallel
    const batchResults = await Promise.all(
      batch.map((task, idx) => runTask(task, i + idx + 1, verbose))
    );
    results.push(...batchResults);

    // Evaluate results
    console.log(`  Evaluating batch...`);
    const batchEvaluations = await Promise.all(
      batch.map((task, idx) => evaluateResult(task, batchResults[idx]))
    );
    evaluations.push(...batchEvaluations);

    // Show batch results
    for (const eval_ of batchEvaluations) {
      const status = eval_.passed ? '✓' : '✗';
      const score = eval_.totalScore || 0;
      const sampleInfo = eval_.agentValue ? `val=${eval_.agentValue}` : (eval_.agentSampleSize ? `n=${eval_.agentSampleSize}` : '');
      console.log(`    ${status} ${eval_.taskId}: ${score}/100 ${sampleInfo}`);
    }

    // Small delay between batches
    if (i + concurrency < tasks.length) {
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  const totalDuration = Date.now() - startTime;

  // Calculate statistics
  const passed = evaluations.filter(e => e.passed).length;
  const avgScore = evaluations.reduce((sum, e) => sum + (e.totalScore || 0), 0) / evaluations.length;
  const successRate = results.filter(r => r.success).length / results.length;

  console.log(`\n${'─'.repeat(70)}`);
  console.log(`TIER ${tier} SUMMARY`);
  console.log(`${'─'.repeat(70)}`);
  console.log(`  Tasks run: ${results.length}`);
  console.log(`  API success: ${results.filter(r => r.success).length}/${results.length} (${(successRate*100).toFixed(0)}%)`);
  console.log(`  Passed: ${passed}/${evaluations.length} (${(passed/evaluations.length*100).toFixed(1)}%)`);
  console.log(`  Average score: ${avgScore.toFixed(1)}/100`);
  console.log(`  Duration: ${(totalDuration/1000).toFixed(1)}s`);

  return { tier, results, evaluations, passed, avgScore, duration: totalDuration };
}

/**
 * Main function
 */
async function main() {
  const args = process.argv.slice(2);
  const tiersArg = args.find(a => a.startsWith('--tier'));
  const tiers = tiersArg ? [parseInt(tiersArg.split('=')[1])] : [1, 2, 3, 4];
  const concurrencyArg = args.find(a => a.startsWith('--concurrency='));
  const concurrency = concurrencyArg ? parseInt(concurrencyArg.split('=')[1]) : 2; // Reduced from 5 to avoid API overload
  const verbose = args.includes('--verbose') || args.includes('-v');

  console.log('╔══════════════════════════════════════════════════════════════════════╗');
  console.log('║           POWER AGENT BENCHMARK EVALUATION                           ║');
  console.log('╚══════════════════════════════════════════════════════════════════════╝');
  console.log(`\nAPI: ${BACKEND_URL}`);
  console.log(`Tiers: ${tiers.join(', ')}`);
  console.log(`Concurrency: ${concurrency}`);

  const allResults = [];
  const runId = `benchmark_${Date.now()}`;

  for (const tier of tiers) {
    const tierResult = await runTierBenchmark(tier, concurrency, verbose);
    allResults.push(tierResult);
  }

  // Final summary
  console.log(`\n${'═'.repeat(70)}`);
  console.log('FINAL SUMMARY');
  console.log(`${'═'.repeat(70)}`);

  let totalPassed = 0;
  let totalTasks = 0;
  let totalScore = 0;

  for (const result of allResults) {
    totalPassed += result.passed;
    totalTasks += result.evaluations.length;
    totalScore += result.avgScore * result.evaluations.length;
    console.log(`  Tier ${result.tier}: ${result.passed}/${result.evaluations.length} passed (${(result.passed/result.evaluations.length*100).toFixed(1)}%), avg ${result.avgScore.toFixed(1)}`);
  }

  console.log(`${'─'.repeat(70)}`);
  console.log(`  OVERALL: ${totalPassed}/${totalTasks} passed (${(totalPassed/totalTasks*100).toFixed(1)}%)`);
  console.log(`  AVERAGE SCORE: ${(totalScore/totalTasks).toFixed(1)}/100`);

  // Save results
  await mkdir('results', { recursive: true });
  const resultsPath = `results/${runId}.json`;
  await writeFile(resultsPath, JSON.stringify({
    runId,
    timestamp: new Date().toISOString(),
    tiers: allResults,
    summary: { totalPassed, totalTasks, avgScore: totalScore/totalTasks }
  }, null, 2));
  console.log(`\nResults saved to: ${resultsPath}`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
