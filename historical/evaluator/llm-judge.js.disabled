/**
 * LLM-as-Judge Evaluator for Power Agent Benchmark
 *
 * Uses Claude to evaluate agent responses against ground truth
 */

import Anthropic from '@anthropic-ai/sdk';
import { config } from './config.js';

const anthropic = new Anthropic();

/**
 * Sanitize a string by removing lone surrogates that cause JSON encoding errors.
 */
function _sanitizeForJson(str) {
  // Remove lone surrogates (high surrogate not followed by low, or lone low surrogate)
  return str.replace(/[\uD800-\uDBFF](?![\uDC00-\uDFFF])/g, '\uFFFD')
            .replace(/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/g, '\uFFFD');
}

/**
 * Evaluation criteria and their weights
 */
const CRITERIA = {
  templateSelection: {
    weight: 20,
    description: 'Correct template/analysis type selected',
  },
  parameterExtraction: {
    weight: 20,
    description: 'Parameters correctly identified from question',
  },
  calculationAccuracy: {
    weight: 30,
    description: 'Sample size within tolerance of ground truth (PRIMARY METRIC)',
  },
  codeQuality: {
    weight: 15,
    description: 'R code would execute and produce correct results (any valid package acceptable)',
  },
  interpretationQuality: {
    weight: 15,
    description: 'Results properly interpreted with assumptions stated',
  },
};

/**
 * Build the evaluation prompt for LLM-as-judge
 */
function buildEvaluationPrompt(task, agentResponse) {
  const groundTruth = task.ground_truth;
  const tolerance = task.tolerance;

  let expectedValues = '';
  if (groundTruth.sample_size_per_group) {
    expectedValues += `- Sample size per group: ${groundTruth.sample_size_per_group} (±${tolerance.sample_size || 5})\n`;
  }
  if (groundTruth.total_sample_size) {
    expectedValues += `- Total sample size: ${groundTruth.total_sample_size} (±${(tolerance.sample_size || 5) * 2})\n`;
  }
  if (groundTruth.sample_size) {
    expectedValues += `- Sample size: ${groundTruth.sample_size} (±${tolerance.sample_size || 5})\n`;
  }
  if (groundTruth.subjects_per_group) {
    expectedValues += `- Subjects per group: ${groundTruth.subjects_per_group} (±${tolerance.sample_size || 5})\n`;
  }
  if (groundTruth.power) {
    expectedValues += `- Power: ${groundTruth.power} (±${tolerance.power || 0.03})\n`;
  }
  if (groundTruth.effect_size_d) {
    expectedValues += `- Effect size (d): ${groundTruth.effect_size_d}\n`;
  }
  if (groundTruth.effect_size_f) {
    expectedValues += `- Effect size (f): ${groundTruth.effect_size_f}\n`;
  }
  if (groundTruth.hazard_ratio) {
    expectedValues += `- Hazard ratio: ${groundTruth.hazard_ratio}\n`;
  }
  if (groundTruth.odds_ratio) {
    expectedValues += `- Odds ratio: ${groundTruth.odds_ratio}\n`;
  }
  if (groundTruth.events) {
    expectedValues += `- Events required: ${groundTruth.events} (±${tolerance.events || 15})\n`;
  }
  if (groundTruth.detectable_effect_d) {
    expectedValues += `- Detectable effect size (d): ${groundTruth.detectable_effect_d} (±${tolerance.effect_size || 0.05})\n`;
  }
  if (groundTruth.total_subjects) {
    expectedValues += `- Total subjects: ${groundTruth.total_subjects} (±${(tolerance.sample_size || 20) * 2})\n`;
  }
  if (groundTruth.subjects_per_arm) {
    expectedValues += `- Subjects per arm: ${groundTruth.subjects_per_arm} (±${tolerance.sample_size || 20})\n`;
  }
  if (groundTruth.subjects) {
    expectedValues += `- Subjects: ${groundTruth.subjects} (±${tolerance.sample_size || 5})\n`;
  }
  if (groundTruth.events_needed) {
    expectedValues += `- Events needed: ${groundTruth.events_needed} (±${tolerance.events || 10})\n`;
  }

  // Determine the ground truth unit for extraction guidance
  let gtUnit = 'total';
  if (groundTruth.per_cell) gtUnit = 'per cell';
  else if (groundTruth.patients_per_cluster || groundTruth.subjects_per_cluster) gtUnit = 'per cluster';
  else if (groundTruth.students_per_classroom) gtUnit = 'per classroom';
  else if (groundTruth.subjects_per_group || groundTruth.subjects_per_arm || groundTruth.sample_size_per_group) gtUnit = 'per group';
  else if (groundTruth.sample_size || groundTruth.subjects) gtUnit = 'total or per group';

  const expectedN = groundTruth.per_cell || groundTruth.patients_per_cluster ||
    groundTruth.subjects_per_cluster || groundTruth.students_per_classroom ||
    groundTruth.subjects_per_group || groundTruth.subjects_per_arm ||
    groundTruth.sample_size_per_group || groundTruth.sample_size ||
    groundTruth.subjects || groundTruth.total_sample_size || groundTruth.total_subjects;
  const hasAnySampleSizeField = expectedN != null;
  const isPowerTask = groundTruth.power && !hasAnySampleSizeField;

  return `You are an expert biostatistician evaluating a power analysis agent's response.

IMPORTANT EVALUATION PRINCIPLES:
- Focus primarily on RESULT ACCURACY (sample size, power values)
- Do NOT penalize for using different R packages than the reference - any valid statistical package is acceptable
- The agent may use pwr, pwrss, WebPower, simr, or any other valid R package
- What matters is whether the FINAL ANSWER (sample size, power) is correct, not the method used

## TASK
Question: ${task.question}

## EXPECTED RESULTS
Template: ${task.expected_template}
${expectedValues}
PRIMARY metric: ${isPowerTask ? 'power' : `sample size (${gtUnit})`}
Expected value: ${isPowerTask ? groundTruth.power : expectedN} (±${isPowerTask ? (tolerance.power || 0.05) : (tolerance.sample_size || 20)})

Reference R code:
\`\`\`r
${task.reference_code}
\`\`\`

## AGENT RESPONSE
${_sanitizeForJson(JSON.stringify(agentResponse, null, 2))}

## CRITICAL EXTRACTION INSTRUCTIONS
Extract the agent's FINAL RECOMMENDED ${isPowerTask ? 'power value' : 'sample size'} from the response.
- Look at the CONCLUSION/SUMMARY sections — those contain the final recommendation
- If the agent mentions multiple values (e.g., analytical vs simulation), extract the FINAL RECOMMENDED value
- For sample size: extract the value that matches the unit "${gtUnit}" (not total if we need per-group, etc.)
- For power: extract as a decimal (0.80, not 80%)

## EVALUATION CRITERIA (100 points total)

1. **Template Selection (20 pts)**
   - Did the agent select the correct analysis type/template?
   - Is it appropriate for the statistical question?
   - Score 20 if correct, 10 if close/acceptable alternative, 0 if wrong

2. **Parameter Extraction (20 pts)**
   - Were all required parameters correctly identified from the question?
   - Were values correctly interpreted (effect sizes, rates, etc.)?
   - Score 0-20 based on completeness and accuracy

3. **Calculation Accuracy (30 pts)**
   - Is the final sample size within the specified tolerance of ground truth?
   - Are intermediate calculations (power, effect size) correct?
   - Score 30 if within tolerance, 15-25 if close, 0-15 if far off

4. **Code Quality (15 pts)**
   - Would the R code execute without errors?
   - Are the statistical parameters correctly specified?
   - NOTE: Do NOT penalize for using different R packages - any valid package that produces correct results is acceptable (pwr, pwrss, WebPower, etc. are all valid)
   - Score 0-15 based on whether code would produce correct results

5. **Interpretation Quality (15 pts)**
   - Are results correctly interpreted in context?
   - Are assumptions and limitations mentioned?
   - Is the output clear and actionable?
   - Score 0-15 based on interpretation quality

## OUTPUT FORMAT
Respond with a JSON object containing:
{
  "scores": {
    "templateSelection": <0-20>,
    "parameterExtraction": <0-20>,
    "calculationAccuracy": <0-30>,
    "codeQuality": <0-15>,
    "interpretationQuality": <0-15>
  },
  "totalScore": <0-100>,
  "passed": <true if totalScore >= 70>,
  "justification": {
    "templateSelection": "<brief explanation>",
    "parameterExtraction": "<brief explanation>",
    "calculationAccuracy": "<brief explanation>",
    "codeQuality": "<brief explanation>",
    "interpretationQuality": "<brief explanation>"
  },
  "agentValue": <the agent's FINAL RECOMMENDED ${isPowerTask ? 'power' : 'sample size'} as a number, or null>,
  "agentSampleSize": <same as agentValue for backward compat, or null>,
  "agentValueUnit": "<unit: 'per group', 'per cell', 'per cluster', 'total', 'power', etc.>",
  "sampleSizeError": <absolute difference from ground truth or null>,
  "sampleSizeErrorPercent": <percentage error or null>,
  "withinTolerance": <true if |agentValue - expected| <= tolerance>,
  "criticalErrors": ["<list of critical errors if any>"],
  "recommendations": ["<suggestions for improvement>"]
}

Only output the JSON object, no other text.`;
}

/**
 * Extract key metrics from agent response
 */
function extractAgentMetrics(agentResponse) {
  const metrics = {
    templateUsed: null,
    sampleSize: null,
    power: null,
    effectSize: null,
    rCodePresent: false,
    rCodeExecuted: false,
  };

  // Try to extract from various response structures
  if (agentResponse.steps) {
    for (const step of agentResponse.steps) {
      if (step.type === 'template_selection') {
        metrics.templateUsed = step.data?.template_id;
      }
      if (step.type === 'code_execution' || step.type === 'analysis_result') {
        metrics.rCodePresent = true;
        metrics.rCodeExecuted = step.data?.success || step.data?.status === 'completed';
      }
      if (step.type === 'results' || step.type === 'chatbot_conclusion') {
        // Try to extract sample size from results
        const content = JSON.stringify(step.data);
        const sampleSizeMatch = content.match(/sample.?size[:\s]+(\d+)/i) ||
                                content.match(/n\s*[=:]\s*(\d+)/i) ||
                                content.match(/(\d+)\s*(?:per\s*group|subjects|participants)/i);
        if (sampleSizeMatch) {
          metrics.sampleSize = parseInt(sampleSizeMatch[1]);
        }

        // Try to extract power value from results
        const powerMatch = content.match(/power[:\s]+(?:of\s+)?(\d+\.?\d*)%/i) ||
                          content.match(/power[:\s]+(?:is\s+)?(\d+\.?\d*)/i) ||
                          content.match(/(\d+\.?\d*)%?\s*power/i) ||
                          content.match(/achieves?\s+(\d+\.?\d*)%/i);
        if (powerMatch) {
          let powerVal = parseFloat(powerMatch[1]);
          // Convert percentage to decimal if needed
          if (powerVal > 1) powerVal = powerVal / 100;
          metrics.power = powerVal;
        }
      }
    }
  }

  return metrics;
}

/**
 * Check tolerance using LLM-extracted values from evaluation response.
 * The LLM judge extracts agentSampleSize/agentValue during scoring —
 * no regex needed.
 */
function checkToleranceFromEvaluation(task, evaluation) {
  const gt = task.ground_truth;
  const tol = task.tolerance;

  const agentValue = evaluation.agentValue ?? evaluation.agentSampleSize;
  if (agentValue == null) return null;

  // For sample size tasks
  const expectedN = gt.per_cell || gt.patients_per_cluster || gt.subjects_per_cluster ||
    gt.students_per_classroom || gt.subjects_per_group || gt.subjects_per_arm ||
    gt.sample_size_per_group || gt.sample_size || gt.subjects ||
    gt.total_sample_size || gt.total_subjects;

  if (expectedN != null) {
    const toleranceN = tol.sample_size || tol.subjects || tol.clusters || 20;
    const diff = Math.abs(agentValue - expectedN);
    return {
      type: 'sample_size',
      expected: expectedN,
      extracted: agentValue,
      tolerance: toleranceN,
      diff,
      withinTolerance: diff <= toleranceN,
    };
  }

  // For effect size tasks (detectable effect)
  if (gt.detectable_effect_d) {
    const toleranceES = tol.effect_size || 0.05;
    const diff = Math.abs(agentValue - gt.detectable_effect_d);
    return {
      type: 'effect_size',
      expected: gt.detectable_effect_d,
      extracted: agentValue,
      tolerance: toleranceES,
      diff,
      withinTolerance: diff <= toleranceES,
    };
  }

  // For power tasks (when no sample size expected)
  if (gt.power) {
    const tolerancePower = tol.power || 0.05;
    const diff = Math.abs(agentValue - gt.power);
    return {
      type: 'power',
      expected: gt.power,
      extracted: agentValue,
      tolerance: tolerancePower,
      diff,
      withinTolerance: diff <= tolerancePower,
    };
  }

  return null;
}

/**
 * Evaluate a single task response
 */
export async function evaluateTask(task, agentResponse) {
  const prompt = buildEvaluationPrompt(task, agentResponse);

  const maxRetries = 3;
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        const delay = 5000 * attempt;
        console.log(`    Retrying evaluation for ${task.id} (attempt ${attempt + 1}/${maxRetries}) after ${delay/1000}s...`);
        await new Promise(r => setTimeout(r, delay));
      }

      return await _evaluateTaskAttempt(task, prompt);
    } catch (error) {
      lastError = error;
      const isRetryable = error.message?.includes('timeout') || error.message?.includes('Timeout') ||
                          error.message?.includes('overloaded') || error.message?.includes('529') ||
                          error.message?.includes('JSON_PARSE_FAILED') ||
                          error.message?.includes('surrogate') || error.message?.includes('not valid JSON') ||
                          error.status === 529 || error.status === 503 || error.status === 400;
      if (!isRetryable || attempt === maxRetries - 1) {
        console.error('Error calling LLM for evaluation:', error.message || error);
        return _evaluationErrorResult(task, error);
      }
    }
  }

  return _evaluationErrorResult(task, lastError);
}

function _evaluationErrorResult(task, error) {
  return {
    taskId: task.id,
    tier: task.tier || getTierFromId(task.id),
    template: task.template,
    difficulty: task.difficulty,
    scores: {
      templateSelection: 0,
      parameterExtraction: 0,
      calculationAccuracy: 0,
      codeQuality: 0,
      interpretationQuality: 0,
    },
    totalScore: 0,
    passed: false,
    justification: {
      templateSelection: 'Evaluation failed',
      parameterExtraction: 'Evaluation failed',
      calculationAccuracy: 'Evaluation failed',
      codeQuality: 'Evaluation failed',
      interpretationQuality: 'Evaluation failed',
    },
    criticalErrors: [`Evaluation error: ${error?.message || error}`],
    recommendations: [],
    error: error?.message || String(error),
    timestamp: new Date().toISOString(),
  };
}

/**
 * Robustly extract JSON from LLM response text.
 * Tries multiple strategies: direct parse, greedy regex, brace-balanced extraction.
 */
function _extractJson(text) {
  // Strategy 1: Direct parse (response is pure JSON)
  try {
    return JSON.parse(text.trim());
  } catch (_) { /* continue */ }

  // Strategy 2: Find the outermost balanced braces
  let depth = 0;
  let start = -1;
  let end = -1;
  let inString = false;
  let escaped = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (escaped) { escaped = false; continue; }
    if (ch === '\\' && inString) { escaped = true; continue; }
    if (ch === '"' && !escaped) { inString = !inString; continue; }
    if (inString) continue;
    if (ch === '{') {
      if (depth === 0) start = i;
      depth++;
    } else if (ch === '}') {
      depth--;
      if (depth === 0 && start !== -1) {
        end = i;
        // Try to parse this balanced block
        try {
          return JSON.parse(text.substring(start, end + 1));
        } catch (_) {
          // Reset and try next top-level block
          start = -1;
          end = -1;
        }
      }
    }
  }

  // Strategy 3: Greedy regex (fallback)
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    return JSON.parse(jsonMatch[0]);
  }

  throw new Error('No valid JSON found in response');
}

async function _evaluateTaskAttempt(task, prompt) {
    // Sanitize the entire prompt to prevent lone surrogates from breaking JSON serialization
    const sanitizedPrompt = _sanitizeForJson(prompt);
    const response = await anthropic.messages.create({
      model: config.llmJudge.model,
      max_tokens: config.llmJudge.maxTokens,
      temperature: config.llmJudge.temperature,
      messages: [
        {
          role: 'user',
          content: sanitizedPrompt,
        },
      ],
    });

    const content = response.content[0].text;

    // Parse the JSON response with robust extraction
    let evaluation;
    try {
      evaluation = _extractJson(content);
    } catch (parseError) {
      console.error(`Failed to parse LLM response for ${task.id}:`, parseError.message);
      console.error('Raw LLM response (first 500 chars):', content.substring(0, 500));
      // Signal that this is a retryable parse error
      throw new Error(`JSON_PARSE_FAILED: ${parseError.message}`);
    }

    // POST-EVALUATION STRICT TOLERANCE CHECK using LLM-extracted values
    const toleranceCheck = checkToleranceFromEvaluation(task, evaluation);
    if (toleranceCheck) {
      const currentCalcScore = evaluation.scores?.calculationAccuracy || 0;
      if (toleranceCheck.withinTolerance) {
        // Within tolerance: ensure full calculation accuracy score
        if (currentCalcScore < 30) {
          const boost = 30 - currentCalcScore;
          evaluation.scores.calculationAccuracy = 30;
          evaluation.totalScore = (evaluation.totalScore || 0) + boost;
          evaluation.justification.calculationAccuracy =
            `Auto-adjusted: Agent ${toleranceCheck.type}=${toleranceCheck.extracted} is within ±${toleranceCheck.tolerance} of GT=${toleranceCheck.expected} (diff=${toleranceCheck.diff.toFixed(2)})`;
          evaluation.toleranceBoostApplied = true;
        }
      } else {
        // OUTSIDE tolerance: force calculationAccuracy to 0 and FAIL
        if (currentCalcScore > 0) {
          evaluation.totalScore = (evaluation.totalScore || 0) - currentCalcScore;
          evaluation.scores.calculationAccuracy = 0;
          evaluation.justification.calculationAccuracy =
            `STRICT FAIL: Agent ${toleranceCheck.type}=${toleranceCheck.extracted} is OUTSIDE ±${toleranceCheck.tolerance} of GT=${toleranceCheck.expected} (diff=${toleranceCheck.diff.toFixed(2)}, ${(100 * toleranceCheck.diff / toleranceCheck.expected).toFixed(1)}% error)`;
          evaluation.toleranceForcedFail = true;
        }
      }
    }

    // Recalculate passed status after adjustment - strict: must have calculationAccuracy > 0
    const calcScore = evaluation.scores?.calculationAccuracy || 0;
    evaluation.passed = (evaluation.totalScore || 0) >= 70 && calcScore > 0;

    // Add metadata
    evaluation.taskId = task.id;
    evaluation.tier = task.tier || getTierFromId(task.id);
    evaluation.template = task.template;
    evaluation.difficulty = task.difficulty;
    evaluation.groundTruth = task.ground_truth;
    evaluation.timestamp = new Date().toISOString();
    if (toleranceCheck) {
      evaluation.toleranceCheck = toleranceCheck;
    }

    return evaluation;
}

/**
 * Quick evaluation using rule-based checks (faster, for preliminary filtering)
 */
export function quickEvaluate(task, agentResponse) {
  const metrics = extractAgentMetrics(agentResponse);
  const groundTruth = task.ground_truth;
  const tolerance = task.tolerance;

  const result = {
    taskId: task.id,
    templateMatch: false,
    sampleSizeMatch: false,
    rCodePresent: metrics.rCodePresent,
    quickScore: 0,
  };

  // Check template match
  if (metrics.templateUsed) {
    result.templateMatch = metrics.templateUsed === task.expected_template ||
                          metrics.templateUsed.includes(task.expected_template) ||
                          task.expected_template.includes(metrics.templateUsed);
    if (result.templateMatch) result.quickScore += 20;
  }

  // Check sample size
  const expectedN = groundTruth.sample_size_per_group ||
                   groundTruth.sample_size ||
                   groundTruth.subjects_per_group ||
                   groundTruth.total_sample_size;

  if (metrics.sampleSize && expectedN) {
    const toleranceVal = tolerance.sample_size || 5;
    const diff = Math.abs(metrics.sampleSize - expectedN);
    result.sampleSizeMatch = diff <= toleranceVal;
    result.sampleSizeDiff = diff;
    if (result.sampleSizeMatch) {
      result.quickScore += 30;
    } else if (diff <= toleranceVal * 2) {
      result.quickScore += 15;
    }
  }

  // Check power (for power-focused tasks like t2-mixed-005)
  if (groundTruth.power && !expectedN && metrics.power) {
    const toleranceVal = tolerance.power || 0.05;
    const diff = Math.abs(metrics.power - groundTruth.power);
    result.powerMatch = diff <= toleranceVal;
    result.powerDiff = diff;
    if (result.powerMatch) {
      result.quickScore += 30;
    } else if (diff <= toleranceVal * 2) {
      result.quickScore += 15;
    }
  }

  // R code present
  if (metrics.rCodePresent) {
    result.quickScore += 15;
  }

  return result;
}

/**
 * Batch evaluate multiple tasks
 */
export async function batchEvaluate(tasks, agentResponses, options = {}) {
  const { concurrency = 3, useQuickFilter = true } = options;
  const results = [];

  // If using quick filter, first do quick evaluation
  let tasksToEvaluate = tasks.map((task, i) => ({
    task,
    response: agentResponses[i],
    index: i,
  }));

  if (useQuickFilter) {
    tasksToEvaluate = tasksToEvaluate.map((item) => {
      const quickResult = quickEvaluate(item.task, item.response);
      return { ...item, quickResult };
    });

    // Sort by quick score (evaluate low scores first as they're more interesting)
    tasksToEvaluate.sort((a, b) => a.quickResult.quickScore - b.quickResult.quickScore);
  }

  // Process in batches for concurrency control
  for (let i = 0; i < tasksToEvaluate.length; i += concurrency) {
    const batch = tasksToEvaluate.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map((item) => evaluateTask(item.task, item.response))
    );
    results.push(...batchResults);

    // Small delay between batches to avoid rate limiting
    if (i + concurrency < tasksToEvaluate.length) {
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }

  return results;
}

/**
 * Get tier from task ID
 */
function getTierFromId(taskId) {
  if (taskId.startsWith('t1-')) return 1;
  if (taskId.startsWith('t2-')) return 2;
  if (taskId.startsWith('t3-')) return 3;
  if (taskId.startsWith('t4-')) return 4;
  return 0;
}

export default {
  evaluateTask,
  quickEvaluate,
  batchEvaluate,
  CRITERIA,
};
