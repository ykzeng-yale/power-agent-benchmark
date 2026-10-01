#!/usr/bin/env node

/**
 * Simple Value-Based Evaluator
 *
 * This is the PRIMARY evaluation method for the benchmark.
 * It performs direct numerical comparison with tolerance checking.
 *
 * Usage:
 *   node simple-evaluator.js results.json
 *
 * Input format (results.json):
 *   {
 *     "t1-ttest-001": { "value": 64, "unit": "per_group" },
 *     "t1-ttest-002": { "value": 86, "unit": "per_group" },
 *     ...
 *   }
 *
 * Or with just values:
 *   {
 *     "t1-ttest-001": 64,
 *     "t1-ttest-002": 86,
 *     ...
 *   }
 */

import { readFile } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Load all tasks from a tier
 */
async function loadTasks(tier) {
  const filePath = path.join(__dirname, '..', 'tasks', `tier${tier}`, 'tasks.json');
  const content = await readFile(filePath, 'utf-8');
  const data = JSON.parse(content);
  return data.tasks.map((t) => ({ ...t, tier }));
}

/**
 * Get expected value from ground truth
 */
function getExpectedValue(groundTruth) {
  // Priority order for sample size fields
  const sampleSizeFields = [
    'sample_size_per_group',
    'subjects_per_group',
    'subjects_per_arm',
    'sample_size',
    'subjects',
    'per_cell',
    'subjects_per_cluster',
    'patients_per_cluster',
    'total_sample_size',
    'total_subjects',
  ];

  for (const field of sampleSizeFields) {
    if (groundTruth[field] != null) {
      return { value: groundTruth[field], type: 'sample_size', field };
    }
  }

  // Check for power (when sample size is given and power is the answer)
  if (groundTruth.power != null && !sampleSizeFields.some((f) => groundTruth[f] != null)) {
    return { value: groundTruth.power, type: 'power', field: 'power' };
  }

  // Check for detectable effect size
  if (groundTruth.detectable_effect_d != null) {
    return { value: groundTruth.detectable_effect_d, type: 'effect_size', field: 'detectable_effect_d' };
  }

  return null;
}

/**
 * Get tolerance for a task
 */
function getTolerance(task, expectedType) {
  const tol = task.tolerance;

  if (expectedType === 'power') {
    return tol.power || 0.05;
  }

  if (expectedType === 'effect_size') {
    return tol.effect_size || 0.05;
  }

  // Sample size tolerance
  return tol.sample_size || tol.subjects || tol.clusters || 10;
}

/**
 * Evaluate a single task
 */
function evaluateTask(task, agentValue) {
  const expected = getExpectedValue(task.ground_truth);

  if (expected === null) {
    return {
      id: task.id,
      passed: false,
      error: 'No expected value found in ground truth',
    };
  }

  if (agentValue === null || agentValue === undefined) {
    return {
      id: task.id,
      passed: false,
      expected: expected.value,
      tolerance: getTolerance(task, expected.type),
      error: 'No agent value provided',
    };
  }

  const tolerance = getTolerance(task, expected.type);
  const diff = Math.abs(agentValue - expected.value);
  const passed = diff <= tolerance;
  const percentError = (100 * diff) / expected.value;

  return {
    id: task.id,
    tier: task.tier,
    template: task.template,
    passed,
    agentValue,
    expected: expected.value,
    expectedField: expected.field,
    tolerance,
    difference: diff,
    percentError: percentError.toFixed(2),
  };
}

/**
 * Main evaluation function
 */
async function evaluate(agentResults) {
  const allTasks = [];

  // Load all tiers
  for (const tier of [1, 2, 3, 4]) {
    try {
      const tasks = await loadTasks(tier);
      allTasks.push(...tasks);
    } catch (e) {
      console.error(`Warning: Could not load tier ${tier}: ${e.message}`);
    }
  }

  console.log(`Loaded ${allTasks.length} tasks\n`);

  const results = [];
  const summary = {
    total: 0,
    passed: 0,
    failed: 0,
    missing: 0,
    byTier: {},
  };

  for (const task of allTasks) {
    let agentValue = agentResults[task.id];

    // Handle structured vs simple format
    if (agentValue && typeof agentValue === 'object') {
      agentValue = agentValue.value;
    }

    const result = evaluateTask(task, agentValue);
    results.push(result);

    // Update summary
    summary.total++;
    if (result.error && result.error.includes('No agent value')) {
      summary.missing++;
    } else if (result.passed) {
      summary.passed++;
    } else {
      summary.failed++;
    }

    // By tier
    const tierKey = `tier${task.tier}`;
    if (!summary.byTier[tierKey]) {
      summary.byTier[tierKey] = { total: 0, passed: 0 };
    }
    summary.byTier[tierKey].total++;
    if (result.passed) {
      summary.byTier[tierKey].passed++;
    }
  }

  return { results, summary };
}

/**
 * Print results to console
 */
function printResults(evaluation) {
  const { results, summary } = evaluation;

  console.log('=' .repeat(70));
  console.log('POWER AGENT BENCHMARK - VALUE-BASED EVALUATION');
  console.log('=' .repeat(70));
  console.log();

  // Print failed tasks
  const failed = results.filter((r) => !r.passed);
  if (failed.length > 0) {
    console.log('FAILED TASKS:');
    console.log('-'.repeat(70));
    for (const r of failed) {
      if (r.error) {
        console.log(`  ${r.id}: ${r.error}`);
      } else {
        console.log(
          `  ${r.id}: agent=${r.agentValue}, expected=${r.expected} ` +
            `(diff=${r.difference}, tol=${r.tolerance})`
        );
      }
    }
    console.log();
  }

  // Print summary
  console.log('SUMMARY:');
  console.log('-'.repeat(70));
  console.log(`  Total tasks:  ${summary.total}`);
  console.log(`  Passed:       ${summary.passed} (${((100 * summary.passed) / summary.total).toFixed(1)}%)`);
  console.log(`  Failed:       ${summary.failed}`);
  console.log(`  Missing:      ${summary.missing}`);
  console.log();

  // By tier
  console.log('BY TIER:');
  console.log('-'.repeat(70));
  for (const [tier, data] of Object.entries(summary.byTier).sort()) {
    const pct = ((100 * data.passed) / data.total).toFixed(1);
    console.log(`  ${tier}: ${data.passed}/${data.total} (${pct}%)`);
  }
  console.log();

  // Overall result
  const passRate = summary.passed / summary.total;
  console.log('=' .repeat(70));
  console.log(`OVERALL PASS RATE: ${(100 * passRate).toFixed(1)}%`);
  console.log('=' .repeat(70));
}

/**
 * Main entry point
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: node simple-evaluator.js <results.json>');
    console.log();
    console.log('Input format:');
    console.log('  {');
    console.log('    "t1-ttest-001": 64,');
    console.log('    "t1-ttest-002": { "value": 86, "unit": "per_group" },');
    console.log('    ...');
    console.log('  }');
    process.exit(1);
  }

  const resultsPath = args[0];

  try {
    const content = await readFile(resultsPath, 'utf-8');
    const agentResults = JSON.parse(content);

    const evaluation = await evaluate(agentResults);
    printResults(evaluation);

    // Exit with code based on pass rate
    const passRate = evaluation.summary.passed / evaluation.summary.total;
    process.exit(passRate >= 0.7 ? 0 : 1);
  } catch (e) {
    console.error(`Error: ${e.message}`);
    process.exit(1);
  }
}

main();
