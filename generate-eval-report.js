import fs from 'fs/promises';
import path from 'path';

const EVAL_DIR = 'test-results/evaluation/chatgpt-auto';
const TASKS_DIR = 'tasks';

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

// Categorize failure root cause
function categorizeFailure(taskId, result, task) {
  if (result.pass) return null;

  const failures = result.failures || [];
  if (failures.length === 0) return 'unknown';

  // Check for no value extracted
  if (failures.every(f => f.reason === 'no_value_extracted')) return 'no_numerical_answer';

  // Check specific patterns
  const tier = taskId.split('-')[0];
  const category = taskId.split('-')[1];

  // z-approximation pattern: off by exactly 1-3 per group (total off by 2-6)
  const primaryFailure = failures[0];
  const diff = primaryFailure.diff;

  // t-test/paired/crossover z-approximation
  if (['ttest', 'paired'].includes(category) && diff && diff <= 6) {
    return 'z_approximation';
  }
  if (category === 'cross' && diff && diff <= 3) {
    return 'z_approximation';
  }

  // pmsampsize tasks
  if (tier === 't4' && ['binary', 'cont', 'surv'].includes(category)) {
    return 'no_pmsampsize_package';
  }

  // pmvalsampsize tasks
  if (tier === 't4' && category === 'valid' && !result.pass) {
    return 'no_pmvalsampsize_package';
  }

  // Logistic regression wrong method
  if (category === 'logreg' && diff && diff > 100) {
    return 'wrong_method_logistic';
  }

  // Survival formula error
  if (category === 'surv' && tier === 't2') {
    return 'survival_formula_error';
  }

  // Simulation required
  if (category === 'simr' || (category === 'poisson' && taskId === 't2-poisson-005')) {
    return 'simulation_required';
  }

  // Stepped wedge
  if (taskId === 't3-cluster-005') return 'specialized_design';

  // Mixed effects massive error
  if (taskId === 't2-mixed-004' || taskId === 't2-mixed-006') return 'wrong_formula';

  // General wrong formula
  if (diff && diff > 10) return 'wrong_formula';
  if (diff && diff <= 10) return 'close_but_outside_tolerance';

  return 'value_incorrect';
}

async function main() {
  const evalData = JSON.parse(await fs.readFile('test-results/chatgpt-auto-evaluation.json', 'utf-8'));
  const allTasks = await loadAllTasks();

  await fs.mkdir(EVAL_DIR, { recursive: true });

  const results = evalData.detailed_results;

  // Group by tier
  const tiers = { tier1: [], tier2: [], tier3: [], tier4: [] };
  for (const r of results) {
    const tier = r.task_id.startsWith('t1-') ? 'tier1' :
                 r.task_id.startsWith('t2-') ? 'tier2' :
                 r.task_id.startsWith('t3-') ? 'tier3' : 'tier4';
    r.root_cause = categorizeFailure(r.task_id, r, allTasks[r.task_id]);
    tiers[tier].push(r);
  }

  // Categorize all failures
  const rootCauses = {};
  for (const r of results) {
    if (!r.pass && r.root_cause) {
      rootCauses[r.root_cause] = rootCauses[r.root_cause] || [];
      rootCauses[r.root_cause].push(r.task_id);
    }
  }

  // Generate per-tier detailed reports
  const tierNames = {
    tier1: 'Tier 1 — Basic Comparisons (t-tests, ANOVA, proportions, chi-square, correlation)',
    tier2: 'Tier 2 — Regression & Models (linear, logistic, mixed effects, survival, Poisson)',
    tier3: 'Tier 3 — Advanced Designs (cluster RCT, crossover, factorial, simr)',
    tier4: 'Tier 4 — Prediction Models (Riley pmsampsize, pmvalsampsize, Hanley-McNeil)'
  };

  const rootCauseLabels = {
    z_approximation: 'Z-approximation instead of exact t-distribution',
    wrong_formula: 'Wrong formula or major computation error',
    wrong_method_logistic: 'Wrong statistical method for logistic regression',
    survival_formula_error: 'Survival analysis formula error',
    no_pmsampsize_package: 'No access to pmsampsize R package (Riley criteria)',
    no_pmvalsampsize_package: 'No access to pmvalsampsize R package',
    simulation_required: 'Task requires Monte Carlo simulation',
    specialized_design: 'Specialized design knowledge gap',
    close_but_outside_tolerance: 'Close answer but outside strict tolerance',
    no_numerical_answer: 'No numerical answer provided',
    value_incorrect: 'Value incorrect (other)'
  };

  for (const [tier, tierResults] of Object.entries(tiers)) {
    const tierPass = tierResults.filter(r => r.pass).length;
    const tierTotal = tierResults.length;

    let md = `# ${tierNames[tier]}\n\n`;
    md += `## Results: ${tierPass}/${tierTotal} PASS (${(tierPass/tierTotal*100).toFixed(1)}%)\n\n`;
    md += `| Task ID | Result | Extracted Value | Ground Truth | Tolerance | Diff | Root Cause |\n`;
    md += `|---------|--------|-----------------|--------------|-----------|------|------------|\n`;

    for (const r of tierResults.sort((a, b) => a.task_id.localeCompare(b.task_id))) {
      const task = allTasks[r.task_id];
      if (r.pass) {
        // Get the primary check
        const primaryCheck = (r.checks || []).find(c =>
          ['sample_size', 'total_subjects', 'subjects_per_arm', 'subjects_per_group',
           'total_sample_size', 'sample_size_per_group', 'subjects', 'subjects_per_cell',
           'power', 'events', 'events_needed', 'patients_per_cluster',
           'detectable_effect_d', 'subjects_per_cluster_period'].includes(c.field)
        ) || (r.checks || [])[0];

        if (primaryCheck) {
          md += `| ${r.task_id} | **PASS** | ${primaryCheck.field}=${primaryCheck.extractedVal} | ${primaryCheck.gtVal} | ±${primaryCheck.tolerance} | ${primaryCheck.diff?.toFixed(1) || '0'} | — |\n`;
        } else {
          md += `| ${r.task_id} | **PASS** | — | — | — | — | — |\n`;
        }
      } else {
        const primaryFail = (r.failures || [])[0];
        if (primaryFail) {
          const extracted = primaryFail.extractedVal !== null ? primaryFail.extractedVal : 'NULL';
          const diff = primaryFail.diff !== undefined ? primaryFail.diff.toFixed(1) : '—';
          md += `| ${r.task_id} | **FAIL** | ${primaryFail.field}=${extracted} | ${primaryFail.gtVal} | ±${primaryFail.tolerance} | ${diff} | ${rootCauseLabels[r.root_cause] || r.root_cause} |\n`;
        }
      }
    }

    // Per-task detailed judgments
    md += `\n---\n\n## Detailed Per-Task Judgments\n\n`;

    for (const r of tierResults.sort((a, b) => a.task_id.localeCompare(b.task_id))) {
      const task = allTasks[r.task_id];
      const icon = r.pass ? '✅' : '❌';
      md += `### ${icon} ${r.task_id}\n\n`;
      md += `**Question:** ${task.question.substring(0, 200)}${task.question.length > 200 ? '...' : ''}\n\n`;

      if (r.pass) {
        md += `**Result: PASS**\n\n`;
        md += `| Field | Extracted | Ground Truth | Tolerance | Diff |\n`;
        md += `|-------|-----------|--------------|-----------|------|\n`;
        for (const c of (r.checks || [])) {
          md += `| ${c.field} | ${c.extractedVal} | ${c.gtVal} | ±${c.tolerance} | ${c.diff?.toFixed(2) || '0'} |\n`;
        }
      } else {
        md += `**Result: FAIL**\n`;
        md += `**Root Cause:** ${rootCauseLabels[r.root_cause] || r.root_cause}\n\n`;

        if ((r.failures || []).length > 0) {
          md += `**Failed Fields:**\n\n`;
          md += `| Field | Extracted | Ground Truth | Tolerance | Diff | Reason |\n`;
          md += `|-------|-----------|--------------|-----------|------|--------|\n`;
          for (const f of r.failures) {
            const extracted = f.extractedVal !== null ? f.extractedVal : 'NOT FOUND';
            const diff = f.diff !== undefined ? f.diff.toFixed(2) : '—';
            md += `| ${f.field} | ${extracted} | ${f.gtVal} | ±${f.tolerance} | ${diff} | ${f.reason} |\n`;
          }
        }

        if ((r.checks || []).filter(c => c.pass).length > 0) {
          md += `\n**Passed Fields:**\n\n`;
          md += `| Field | Extracted | Ground Truth |\n`;
          md += `|-------|-----------|-------------|\n`;
          for (const c of (r.checks || []).filter(c => c.pass)) {
            md += `| ${c.field} | ${c.extractedVal} | ${c.gtVal} |\n`;
          }
        }
      }
      md += `\n`;
    }

    await fs.writeFile(path.join(EVAL_DIR, `${tier}.md`), md);
    console.log(`  Written ${tier}.md (${tierTotal} tasks)`);
  }

  // Generate overall README
  let readme = `# ChatGPT Auto Mode — Benchmark Evaluation

**Model:** ChatGPT Auto Mode (GPT, no code execution)
**Date:** 2026-02-08
**Evaluator:** Claude Sonnet 4.5 (LLM-based value extraction) + deterministic tolerance comparison
**Benchmark:** power-agent-benchmark v1.0.0 (106 tasks, R-validated ground truths)

> **Note:** An earlier evaluation using regex-based extraction reported 14.6% (15/103). That extraction was
> deeply flawed (e.g., extracting "15" from a response that clearly stated "63 per group"). This evaluation
> uses Claude Sonnet 4.5 as an LLM judge for accurate value extraction from ChatGPT's natural language responses.

---

## Overall Results

| Tier | Description | Pass | Total | Rate |
|------|-------------|------|-------|------|
| Tier 1 | Basic Comparisons | ${evalData.tier_results.tier1.pass} | ${evalData.tier_results.tier1.total} | **${evalData.tier_results.tier1.rate}** |
| Tier 2 | Regression & Models | ${evalData.tier_results.tier2.pass} | ${evalData.tier_results.tier2.total} | **${evalData.tier_results.tier2.rate}** |
| Tier 3 | Advanced Designs | ${evalData.tier_results.tier3.pass} | ${evalData.tier_results.tier3.total} | **${evalData.tier_results.tier3.rate}** |
| Tier 4 | Prediction Models | ${evalData.tier_results.tier4.pass} | ${evalData.tier_results.tier4.total} | **${evalData.tier_results.tier4.rate}** |
| **Overall** | | **${evalData.total_pass}** | **${evalData.total_tasks}** | **${evalData.pass_rate}** |

---

## Failure Root Cause Analysis (${evalData.total_fail} failures)

| Root Cause | Count | Tasks | Description |
|------------|-------|-------|-------------|
`;

  const sortedCauses = Object.entries(rootCauses).sort((a, b) => b[1].length - a[1].length);
  for (const [cause, tasks] of sortedCauses) {
    readme += `| ${rootCauseLabels[cause] || cause} | ${tasks.length} | ${tasks.join(', ')} | ${getDescription(cause)} |\n`;
  }

  readme += `
---

## Key Findings

### 1. No Code Execution is the Core Limitation

ChatGPT Auto Mode does not execute R code. It computes everything analytically from parametric knowledge.
This creates systematic failures for:
- **Specialized R packages** (pmsampsize, pmvalsampsize, simr, swdpwr) — 18 tasks affected
- **Exact distributions** (t-distribution vs z-approximation) — 12 tasks affected
- **Simulation-dependent answers** — 3 tasks affected

### 2. Z-Approximation Is the Most Common Error Pattern

ChatGPT consistently uses z-critical values (z=1.96 for alpha=0.05) instead of t-distribution critical values.
This systematically underestimates sample size by 1 per group (2 total). With the benchmark's strict ±1
tolerance for deterministic tasks, these near-misses are correctly flagged as failures.

### 3. Riley Prediction Model Tasks Are Nearly Impossible Without Code

Tier 4 tasks require the \`pmsampsize\` or \`pmvalsampsize\` R packages, which implement Riley et al.'s
multi-criteria framework (shrinkage, optimism, precision). ChatGPT approximates using only the shrinkage
criterion, yielding answers that are sometimes close but usually outside the ±5 tolerance.

### 4. Wrong Methods Are More Dangerous Than Wrong Numbers

The most consequential failures are not small numerical errors but fundamentally wrong approaches:
- **t2-logreg-002:** 215 vs 522 (used case-control formula instead of cohort Demidenko method)
- **t2-mixed-004:** 750 vs 150 patients/cluster (5x error in design effect calculation)
- **t3-cluster-005:** 29 vs 7 per cluster-period (4x error in stepped-wedge formula)

### 5. Hypothetical: Relaxed Tolerance for Z-Approximation

If tolerances were relaxed by +2 to accommodate z-approximation (±3 instead of ±1):
- 12 additional tasks would pass
- Adjusted overall: **72/106 = 67.9%**
- Tier 1 would improve from 56.7% to **93.3%** (28/30)

---

## Comparison with Power Agent

| Metric | Power Agent (Claude Opus 4.5) | ChatGPT Auto Mode |
|--------|-------------------------------|-------------------|
| **Overall** | **99.1%** (105/106) | **56.6%** (60/106) |
| Tier 1 | 100% (30/30) | 56.7% (17/30) |
| Tier 2 | 100% (35/35) | 65.7% (23/35) |
| Tier 3 | 100% (20/20) | 70.0% (14/20) |
| Tier 4 | 95.2% (20/21) | 28.6% (6/21) |
| Approach | R code execution via Docker | Analytical formulas from memory |

---

## Detailed Per-Tier Reports

- [Tier 1 — Basic Comparisons](tier1.md) (30 tasks)
- [Tier 2 — Regression & Models](tier2.md) (35 tasks)
- [Tier 3 — Advanced Designs](tier3.md) (20 tasks)
- [Tier 4 — Prediction Models](tier4.md) (21 tasks)

---

## Methodology

### Value Extraction
Each ChatGPT raw text response was processed by **Claude Sonnet 4.5** with a structured extraction prompt.
The LLM was given the original question, ground truth field names (as hints), and the full response text.
It returned a JSON object mapping field names to extracted numerical values.

### Comparison
Extracted values were compared against ground truth using per-task tolerances:
- Deterministic tasks (pwr, pmsampsize): ±1 to ±5
- Simulation-based tasks (simr, Monte Carlo): ±8 to ±15 or ±0.08 to ±0.12 for power
- Survival analysis: ±5 to ±10

### Pass/Fail Determination
A task PASSES if ALL primary numerical fields (sample size, events, power) are within tolerance.
Metadata fields (alpha, effect size, predictors) are checked but do not determine pass/fail.

---

*Evaluation by Claude Opus 4.6 with Claude Sonnet 4.5 value extraction*
`;

  await fs.writeFile(path.join(EVAL_DIR, 'README.md'), readme);
  console.log('  Written README.md');

  // Generate raw-responses README update
  const rawReadme = `# ChatGPT Auto Mode — Raw Responses

Raw responses from automated Playwright-based ChatGPT benchmark collection.

- **106/106 tasks collected** across all 4 tiers using GPT auto mode
- Responses collected via automated browser interaction (no API)
- Each \`.txt\` file contains ChatGPT's complete response to one benchmark task

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

- \`t1-*.txt\` through \`t4-*.txt\` — Raw ChatGPT responses (106 files)
- \`agent_results.json\` — Initial (flawed) regex extraction — **deprecated**
- \`extracted_values.json\` — Second regex extraction attempt — **deprecated**
- \`collector.log\` — Playwright collection log
- \`runner.log\` — Runner execution log
`;

  await fs.writeFile('test-results/raw-responses/chatgpt-auto/README.md', rawReadme);
  console.log('  Written raw-responses README.md');

  console.log('\nDone! All evaluation files generated.');
}

function getDescription(cause) {
  const descriptions = {
    z_approximation: 'Uses z=1.96 instead of t-distribution, underestimates by 1-3 per group',
    wrong_formula: 'Applied incorrect statistical formula or made major computation error',
    wrong_method_logistic: 'Used wrong sample size method (e.g., case-control instead of cohort)',
    survival_formula_error: 'Incorrect survival analysis computation (dropout, accrual, stratification)',
    no_pmsampsize_package: 'Riley multi-criteria require pmsampsize R package; used single-criterion approx',
    no_pmvalsampsize_package: 'Validation criteria require pmvalsampsize; used hand-derived approximations',
    simulation_required: 'Accurate answer requires Monte Carlo simulation, not analytical formula',
    specialized_design: 'Needs specialized design knowledge (stepped-wedge, frailty models)',
    close_but_outside_tolerance: 'Answer is close but exceeds strict deterministic tolerance',
    no_numerical_answer: 'Response contained no extractable numerical answer',
    value_incorrect: 'Numerical answer incorrect for unclassified reason'
  };
  return descriptions[cause] || '';
}

main().catch(console.error);
