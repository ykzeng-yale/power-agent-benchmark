import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs/promises';
import path from 'path';

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const RESPONSE_DIR = 'test-results/raw-responses/chatgpt-auto';
const TASKS_DIR = 'tasks';
const CONCURRENCY = 10; // parallel LLM calls

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
  // Build the list of fields we need to extract
  const fieldsNeeded = [];
  const gt = groundTruth;

  // Determine the primary sample size field
  const sampleFields = ['sample_size', 'total_subjects', 'subjects_per_arm', 'subjects_per_group',
    'total_sample_size', 'patients_per_cluster', 'subjects'];
  const powerFields = ['power'];
  const eventFields = ['events', 'events_needed'];

  for (const [key, val] of Object.entries(gt)) {
    if (typeof val === 'number') {
      fieldsNeeded.push({ key, expected: val });
    }
  }

  // Build extraction prompt
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
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 500,
      messages: [{ role: 'user', content: prompt }]
    });
    const text = msg.content[0].text.trim();
    // Extract JSON from response
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return null;
  } catch (err) {
    console.error(`  LLM extraction failed for ${taskId}: ${err.message}`);
    return null;
  }
}

function evaluateTask(taskId, task, extracted) {
  const gt = task.ground_truth;
  const tol = task.tolerance || {};

  if (!extracted) {
    return { pass: false, reason: 'extraction_failed', details: 'LLM could not extract values from response' };
  }

  // Determine the primary fields to check
  // We check the "main" answer field(s) that define pass/fail
  const checks = [];
  const failures = [];

  // Map of tolerance keys to GT field names
  const sampleSizeTolFields = ['sample_size', 'total_subjects', 'subjects_per_arm', 'subjects_per_group',
    'total_sample_size', 'patients_per_cluster', 'subjects', 'subjects_per_cell'];

  for (const [field, gtVal] of Object.entries(gt)) {
    if (typeof gtVal !== 'number') continue;

    const extractedVal = extracted[field];

    // Skip non-primary metadata fields
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

    if (metadataFields.includes(field)) continue;

    // Determine tolerance for this field
    let tolerance = 0;
    if (sampleSizeTolFields.includes(field)) {
      tolerance = tol.sample_size || 5;
    } else if (field === 'power' || field === 'achieved_power') {
      tolerance = tol.power || 0.03;
    } else if (field === 'events' || field === 'events_needed') {
      tolerance = tol.events || 2;
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

  // Categorize failure
  const allNull = failures.every(f => f.reason === 'no_value_extracted');
  const someNull = failures.some(f => f.reason === 'no_value_extracted');

  let overallReason;
  if (allNull) {
    overallReason = 'no_numerical_answer';
  } else if (someNull) {
    overallReason = 'partial_answer';
  } else {
    overallReason = 'value_incorrect';
  }

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

async function main() {
  console.log('=== ChatGPT Auto Mode Benchmark Evaluation ===\n');

  // Load tasks
  const allTasks = await loadAllTasks();
  console.log(`Loaded ${Object.keys(allTasks).length} tasks from benchmark\n`);

  // Load response files
  const responseFiles = (await fs.readdir(RESPONSE_DIR)).filter(f => f.endsWith('.txt')).sort();
  console.log(`Found ${responseFiles.length} ChatGPT response files\n`);

  // Build evaluation items
  const evalItems = [];
  for (const file of responseFiles) {
    const taskId = file.replace('.txt', '');
    if (!allTasks[taskId]) {
      console.log(`  WARNING: No task definition for ${taskId}`);
      continue;
    }
    const response = await fs.readFile(path.join(RESPONSE_DIR, file), 'utf-8');
    evalItems.push({ taskId, task: allTasks[taskId], response });
  }

  console.log(`Extracting values from ${evalItems.length} responses using Claude Sonnet...\n`);

  // Extract values in batches
  const results = await processInBatches(evalItems, CONCURRENCY, async (item) => {
    const extracted = await extractValues(
      item.taskId, item.task.question, item.task.ground_truth, item.response
    );
    const evaluation = evaluateTask(item.taskId, item.task, extracted);
    return { taskId: item.taskId, extracted, evaluation };
  });

  console.log(`\nExtraction complete. Evaluating results...\n`);

  // Organize by tier
  const tiers = { tier1: [], tier2: [], tier3: [], tier4: [] };
  for (const r of results) {
    const tier = r.taskId.startsWith('t1-') ? 'tier1' :
                 r.taskId.startsWith('t2-') ? 'tier2' :
                 r.taskId.startsWith('t3-') ? 'tier3' : 'tier4';
    tiers[tier].push(r);
  }

  // Print detailed results
  const allResults = [];
  let totalPass = 0;
  let totalFail = 0;

  for (const [tier, tierResults] of Object.entries(tiers)) {
    const tierPass = tierResults.filter(r => r.evaluation.pass).length;
    const tierFail = tierResults.length - tierPass;
    console.log(`\n${'='.repeat(70)}`);
    console.log(`${tier.toUpperCase()} - ${tierPass}/${tierResults.length} PASS (${(tierPass/tierResults.length*100).toFixed(1)}%)`);
    console.log(`${'='.repeat(70)}`);

    for (const r of tierResults.sort((a, b) => a.taskId.localeCompare(b.taskId))) {
      const status = r.evaluation.pass ? 'PASS' : 'FAIL';
      const icon = r.evaluation.pass ? '✓' : '✗';

      if (r.evaluation.pass) {
        const matchInfo = r.evaluation.checks.map(c =>
          `${c.field}: ${c.extractedVal} (GT=${c.gtVal})`
        ).join(', ');
        console.log(`  ${icon} ${r.taskId}: ${status} — ${matchInfo}`);
        totalPass++;
      } else {
        const failInfo = r.evaluation.failures.map(f => {
          if (f.reason === 'no_value_extracted') {
            return `${f.field}: NOT FOUND (GT=${f.gtVal})`;
          }
          return `${f.field}: ${f.extractedVal} vs GT=${f.gtVal} (off by ${f.diff?.toFixed(2)}, tol=${f.tolerance})`;
        }).join('; ');
        const passInfo = (r.evaluation.checks || []).filter(c => c.pass).map(c =>
          `${c.field}=${c.extractedVal}✓`
        ).join(', ');
        console.log(`  ${icon} ${r.taskId}: ${status} [${r.evaluation.reason}] — ${failInfo}${passInfo ? ' | OK: ' + passInfo : ''}`);
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

  // Summary
  console.log(`\n${'='.repeat(70)}`);
  console.log('SUMMARY');
  console.log(`${'='.repeat(70)}`);
  const total = totalPass + totalFail;
  console.log(`Overall: ${totalPass}/${total} PASS (${(totalPass/total*100).toFixed(1)}%)\n`);

  for (const [tier, tierResults] of Object.entries(tiers)) {
    const tierPass = tierResults.filter(r => r.evaluation.pass).length;
    console.log(`  ${tier}: ${tierPass}/${tierResults.length} (${(tierPass/tierResults.length*100).toFixed(1)}%)`);
  }

  // Failure analysis
  const failReasons = {};
  for (const r of allResults.filter(r => !r.pass)) {
    failReasons[r.reason] = (failReasons[r.reason] || 0) + 1;
  }
  console.log(`\nFailure Breakdown:`);
  for (const [reason, count] of Object.entries(failReasons).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${reason}: ${count}`);
  }

  // Save results
  const output = {
    model: 'ChatGPT Auto Mode',
    date: new Date().toISOString().split('T')[0],
    total_tasks: total,
    total_pass: totalPass,
    total_fail: totalFail,
    pass_rate: (totalPass / total * 100).toFixed(1) + '%',
    tier_results: Object.fromEntries(
      Object.entries(tiers).map(([tier, tierResults]) => {
        const tierPass = tierResults.filter(r => r.evaluation.pass).length;
        return [tier, { pass: tierPass, total: tierResults.length, rate: (tierPass / tierResults.length * 100).toFixed(1) + '%' }];
      })
    ),
    failure_reasons: failReasons,
    detailed_results: allResults
  };

  await fs.writeFile('test-results/chatgpt-auto-evaluation.json', JSON.stringify(output, null, 2));
  console.log(`\nDetailed results saved to test-results/chatgpt-auto-evaluation.json`);
}

main().catch(console.error);
