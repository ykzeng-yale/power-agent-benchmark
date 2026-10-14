#!/usr/bin/env node
/**
 * Evaluate API benchmark responses using LLM-as-extractor + value comparison.
 *
 * Usage:
 *   node evaluate-api-models.js --model gpt-5.2          # Evaluate one model
 *   node evaluate-api-models.js --all                     # Evaluate all models
 *   node evaluate-api-models.js --list                    # List available models
 */

import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs/promises';
import path from 'path';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || ''
});

const TASKS_DIR = 'tasks';
const RAW_DIR = 'test-results/raw-responses';
const EVAL_DIR = 'test-results/evaluation';
const CONCURRENCY = 5; // parallel LLM extraction calls

// All models with raw responses
const ALL_MODELS = [
  'gpt-5.2', 'gpt-5.2-pro',
  'claude-sonnet-4-6', 'claude-opus-4-6',
  'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-3.1-pro-preview',
  // Code execution models
  'gpt-5.2-code', 'gemini-2.5-flash-code', 'gemini-2.5-pro-code', 'gemini-3.1-pro-preview-code',
];

// Display names
const DISPLAY_NAMES = {
  'gpt-5.2': 'GPT-5.2',
  'gpt-5.2-pro': 'GPT-5.2 Pro',
  'claude-sonnet-4-6': 'Claude Sonnet 4.6',
  'claude-opus-4-6': 'Claude Opus 4.6',
  'gemini-2.5-flash': 'Gemini 2.5 Flash',
  'gemini-2.5-pro': 'Gemini 2.5 Pro',
  'gemini-3.1-pro-preview': 'Gemini 3.1 Pro Preview',
  'gpt-5.2-code': 'GPT-5.2 + Code Interpreter',
  'gemini-2.5-flash-code': 'Gemini 2.5 Flash + Code Execution',
  'gemini-2.5-pro-code': 'Gemini 2.5 Pro + Code Execution',
  'gemini-3.1-pro-preview-code': 'Gemini 3.1 Pro Preview + Code Execution',
};

async function loadAllTasks() {
  const allTasks = {};
  for (const tier of ['tier1', 'tier2', 'tier3', 'tier4']) {
    const data = JSON.parse(await fs.readFile(path.join(TASKS_DIR, tier, 'tasks.json'), 'utf-8'));
    for (const task of data.tasks) {
      allTasks[task.id] = task;
    }
  }
  return allTasks;
}

async function extractValues(taskId, question, groundTruth, response) {
  const fieldsNeeded = [];
  for (const [key, val] of Object.entries(groundTruth)) {
    if (typeof val === 'number') {
      fieldsNeeded.push({ key, expected: val });
    }
  }

  const fieldList = fieldsNeeded.map(f => `- "${f.key}": (expected type: number, ground truth hint: ${f.expected})`).join('\n');

  const prompt = `You are a precise numerical value extractor for biostatistics benchmark evaluation.

TASK: Extract the FINAL numerical answers from the AI response below for each requested field.

RESEARCH QUESTION:
${question}

FIELDS TO EXTRACT (with ground truth field names and hints):
${fieldList}

AI RESPONSE:
${response}

INSTRUCTIONS:
1. Find the FINAL answer the AI gives for each field. Look for boxed answers, bold answers, or concluding statements.
2. For sample_size / total_subjects / total_sample_size: extract the TOTAL sample size across all groups.
3. For subjects_per_arm / subjects_per_group / n_per_group: extract the PER-GROUP sample size.
4. For events / events_needed: extract the number of events.
5. For power: extract as a decimal (e.g., 0.80 not 80%).
6. For subjects_per_cell / per_cell: extract per-cell count in factorial designs.
7. If the AI only provides R code but no final numerical answer, set the value to null.
8. If the AI gives a range, use the primary/recommended value.
9. If the field is not addressed at all, set to null.

Return ONLY a JSON object mapping field names to extracted numeric values (or null if not found).
Example: {"sample_size": 185, "events": 222, "power": 0.80}

JSON:`;

  try {
    const msg = await anthropic.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 500,
      messages: [{ role: 'user', content: prompt }]
    });
    const text = msg.content[0].text.trim();
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return null;
  } catch (err) {
    console.error(`  LLM extraction failed for ${taskId}: ${err.message?.slice(0, 100)}`);
    return null;
  }
}

function evaluateTask(taskId, task, extracted) {
  const gt = task.ground_truth;
  const tol = task.tolerance || {};

  if (!extracted) {
    return { pass: false, reason: 'extraction_failed', details: 'LLM could not extract values from response', checks: [], failures: [] };
  }

  const checks = [];
  const failures = [];

  const sampleSizeTolFields = ['sample_size', 'total_subjects', 'subjects_per_arm', 'subjects_per_group',
    'total_sample_size', 'patients_per_cluster', 'subjects', 'subjects_per_cell',
    'sample_size_per_group', 'n_per_group', 'n_total', 'clusters_per_arm',
    'events', 'events_needed', 'min_events'];

  const metadataFields = ['hazard_ratio', 'control_median_months', 'study_duration_months',
    'alpha', 'predictors', 'event_rate', 'r2_cs', 'r2', 'timepoint', 'mean_followup',
    'max_shrinkage', 'prevalence', 'ci_width', 'expected_c_statistic',
    'cure_rate_control', 'cure_rate_treatment', 'hazard_ratio_uncured',
    'median_survival_uncured', 'followup_years', 'intercept', 'sd',
    'interaction_or', 'main_or', 'baseline_rate', 'treatment_rate',
    'rate_ratio', 'icc', 'clusters_per_arm', 'subjects_per_cluster',
    'num_groups', 'effect_size_d', 'effect_size_f', 'effect_size_h', 'effect_size_w',
    'degrees_of_freedom', 'correlation_r', 'between_subject_d', 'within_subject_correlation',
    'paired_d', 'r2_cs', 'nagrsquared', 'cstatistic',
    'cause_specific_hr', 'control_primary_rate', 'competing_risk_rate',
    'control_event_rate', 'strata', 'mean_count_control', 'mean_count_treatment',
    'observation_period', 'dispersion_k', 'structural_zero_proportion',
    'mean_nonzero_control', 'mean_nonzero_treatment', 'baseline_annual_rate',
    'annual_rate_increase', 'followup_years_poisson', 'clusters_per_arm_poisson',
    'subjects_per_cluster_poisson', 'icc_poisson', 'baseline_rate_poisson',
    'measurements', 'within_subject_icc', 'random_intercept_sd',
    'residual_sd', 'slope_difference', 'random_slope_sd',
    'p1', 'p2', 'effect_size', 'delta', 'num_runs', 'replicates',
    'num_factors', 'num_periods', 'num_treatments'];

  for (const [field, gtVal] of Object.entries(gt)) {
    if (typeof gtVal !== 'number') continue;
    if (metadataFields.includes(field)) continue;

    const extractedVal = extracted[field];

    let tolerance = 0;
    if (sampleSizeTolFields.includes(field)) {
      tolerance = tol.sample_size || 5;
    } else if (field === 'power' || field === 'achieved_power') {
      tolerance = tol.power || 0.03;
    } else if (field === 'detectable_effect') {
      tolerance = tol.effect_size || 0.03;
    } else {
      tolerance = tol[field] || 5;
    }

    if (extractedVal === null || extractedVal === undefined) {
      failures.push({ field, gtVal, extractedVal: null, tolerance, reason: 'no_value_extracted' });
    } else {
      const diff = Math.abs(extractedVal - gtVal);
      if (diff > tolerance) {
        failures.push({ field, gtVal, extractedVal, tolerance, diff, reason: 'value_incorrect' });
      } else {
        checks.push({ field, gtVal, extractedVal, tolerance, diff, pass: true });
      }
    }
  }

  if (failures.length === 0) {
    return { pass: true, reason: 'all_values_match', checks, failures: [] };
  }

  const allNull = failures.every(f => f.reason === 'no_value_extracted');
  const someNull = failures.some(f => f.reason === 'no_value_extracted');
  let overallReason = allNull ? 'no_numerical_answer' : someNull ? 'partial_answer' : 'value_incorrect';

  return { pass: false, reason: overallReason, checks, failures };
}

async function processInBatches(items, batchSize, fn) {
  const results = [];
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    const batchResults = await Promise.all(batch.map(fn));
    results.push(...batchResults);
    if (i + batchSize < items.length) {
      process.stdout.write(`  Processed ${Math.min(i + batchSize, items.length)}/${items.length}...\r`);
    }
  }
  return results;
}

async function evaluateModel(modelSlug, allTasks) {
  const displayName = DISPLAY_NAMES[modelSlug] || modelSlug;
  console.log(`\n${'='.repeat(70)}`);
  console.log(`EVALUATING: ${displayName} (${modelSlug})`);
  console.log(`${'='.repeat(70)}\n`);

  // Load raw responses
  const rawFile = path.join(RAW_DIR, modelSlug, 'raw-responses.json');
  let rawData;
  try {
    rawData = JSON.parse(await fs.readFile(rawFile, 'utf-8'));
  } catch (e) {
    console.log(`  ERROR: Could not load ${rawFile}: ${e.message}`);
    return null;
  }

  // Build evaluation items
  const evalItems = [];
  for (const [taskId, resp] of Object.entries(rawData)) {
    if (!allTasks[taskId]) {
      console.log(`  WARNING: No task definition for ${taskId}`);
      continue;
    }
    if (!resp.response_text || resp.error) continue;
    evalItems.push({ taskId, task: allTasks[taskId], response: resp.response_text });
  }

  console.log(`  Extracting values from ${evalItems.length} responses using Claude Sonnet 4.6...\n`);

  // Extract + evaluate
  const results = await processInBatches(evalItems, CONCURRENCY, async (item) => {
    const extracted = await extractValues(
      item.taskId, item.task.question, item.task.ground_truth, item.response
    );
    const evaluation = evaluateTask(item.taskId, item.task, extracted);
    return { taskId: item.taskId, extracted, evaluation };
  });

  console.log(`\n  Extraction complete. Compiling results...\n`);

  // Organize by tier
  const tiers = { tier1: [], tier2: [], tier3: [], tier4: [] };
  for (const r of results) {
    const tier = r.taskId.startsWith('t1-') ? 'tier1' :
                 r.taskId.startsWith('t2-') ? 'tier2' :
                 r.taskId.startsWith('t3-') ? 'tier3' : 'tier4';
    tiers[tier].push(r);
  }

  // Print results
  const allResults = [];
  let totalPass = 0, totalFail = 0;

  for (const [tier, tierResults] of Object.entries(tiers)) {
    const tierPass = tierResults.filter(r => r.evaluation.pass).length;
    console.log(`  ${tier.toUpperCase()}: ${tierPass}/${tierResults.length} PASS (${(tierPass/tierResults.length*100).toFixed(1)}%)`);

    for (const r of tierResults.sort((a, b) => a.taskId.localeCompare(b.taskId))) {
      if (r.evaluation.pass) {
        totalPass++;
      } else {
        const failInfo = r.evaluation.failures.map(f => {
          if (f.reason === 'no_value_extracted') return `${f.field}: NOT FOUND (GT=${f.gtVal})`;
          return `${f.field}: ${f.extractedVal} vs GT=${f.gtVal} (off by ${f.diff?.toFixed(2)}, tol=${f.tolerance})`;
        }).join('; ');
        console.log(`    ✗ ${r.taskId}: ${failInfo}`);
        totalFail++;
      }

      allResults.push({
        task_id: r.taskId,
        pass: r.evaluation.pass,
        reason: r.evaluation.reason,
        extracted: r.extracted,
        failures: r.evaluation.failures,
        checks: r.evaluation.checks
      });
    }
  }

  const total = totalPass + totalFail;
  const passRate = (totalPass / total * 100).toFixed(1);

  console.log(`\n  OVERALL: ${totalPass}/${total} PASS (${passRate}%)\n`);

  // Failure analysis
  const failReasons = {};
  for (const r of allResults.filter(r => !r.pass)) {
    failReasons[r.reason] = (failReasons[r.reason] || 0) + 1;
  }
  if (Object.keys(failReasons).length > 0) {
    console.log(`  Failure breakdown:`);
    for (const [reason, count] of Object.entries(failReasons).sort((a, b) => b[1] - a[1])) {
      console.log(`    ${reason}: ${count}`);
    }
  }

  // Save results
  const output = {
    model: displayName,
    model_slug: modelSlug,
    date: new Date().toISOString().split('T')[0],
    total_tasks: total,
    total_pass: totalPass,
    total_fail: totalFail,
    pass_rate: passRate + '%',
    tier_results: Object.fromEntries(
      Object.entries(tiers).map(([tier, tierResults]) => {
        const tierPass = tierResults.filter(r => r.evaluation.pass).length;
        return [tier, { pass: tierPass, total: tierResults.length, rate: (tierPass / tierResults.length * 100).toFixed(1) + '%' }];
      })
    ),
    failure_reasons: failReasons,
    detailed_results: allResults
  };

  // Save to evaluation dir
  const evalModelDir = path.join(EVAL_DIR, modelSlug);
  await fs.mkdir(evalModelDir, { recursive: true });
  await fs.writeFile(path.join(evalModelDir, 'evaluation.json'), JSON.stringify(output, null, 2));

  // Generate README
  const readme = `# ${displayName} - Evaluation Results

- **Model**: \`${modelSlug}\`
- **Pass Rate**: **${passRate}%** (${totalPass}/${total})
- **Date**: ${output.date}

## Tier Results

| Tier | Pass | Total | Rate |
|------|------|-------|------|
${Object.entries(output.tier_results).map(([t, r]) => `| ${t} | ${r.pass} | ${r.total} | ${r.rate} |`).join('\n')}
| **Overall** | **${totalPass}** | **${total}** | **${passRate}%** |

## Failure Analysis

${Object.keys(failReasons).length > 0 ?
  Object.entries(failReasons).sort((a, b) => b[1] - a[1]).map(([r, c]) => `- ${r}: ${c}`).join('\n') :
  'No failures!'}

## Detailed Results

See \`evaluation.json\` for per-task results with extracted values and comparison details.
`;
  await fs.writeFile(path.join(evalModelDir, 'README.md'), readme);

  return { model: displayName, slug: modelSlug, passRate, totalPass, total };
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--list')) {
    console.log('Available models:');
    ALL_MODELS.forEach(m => console.log(`  ${m}`));
    process.exit(0);
  }

  // Load all tasks once
  const allTasks = await loadAllTasks();
  console.log(`Loaded ${Object.keys(allTasks).length} tasks from benchmark`);

  let modelsToEval = [];

  if (args.includes('--all')) {
    modelsToEval = [...ALL_MODELS];
  } else {
    const modelIdx = args.indexOf('--model');
    if (modelIdx !== -1 && args[modelIdx + 1]) {
      modelsToEval = [args[modelIdx + 1]];
    } else {
      console.log('Usage: node evaluate-api-models.js --model <slug> | --all');
      process.exit(1);
    }
  }

  const summaries = [];
  for (const slug of modelsToEval) {
    const result = await evaluateModel(slug, allTasks);
    if (result) summaries.push(result);
  }

  // Print final summary
  if (summaries.length > 1) {
    console.log(`\n${'='.repeat(70)}`);
    console.log('FINAL SUMMARY - ALL MODELS');
    console.log(`${'='.repeat(70)}\n`);
    console.log('| Model | Pass | Total | Rate |');
    console.log('|-------|------|-------|------|');
    for (const s of summaries.sort((a, b) => parseFloat(b.passRate) - parseFloat(a.passRate))) {
      console.log(`| ${s.model} | ${s.totalPass} | ${s.total} | ${s.passRate}% |`);
    }
  }

  // Save combined summary
  await fs.writeFile(path.join(EVAL_DIR, 'api-models-summary.json'), JSON.stringify({
    date: new Date().toISOString().split('T')[0],
    models: summaries,
  }, null, 2));
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
