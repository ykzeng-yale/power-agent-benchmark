#!/usr/bin/env node

/**
 * Example: Run a Single Benchmark Task
 *
 * This is a reference example using the Power Agent SSE API.
 * Adapt the runAgentTask() function to call your own agent.
 *
 * Demonstrates how to:
 * 1. Load a specific task
 * 2. Send it to an agent
 * 3. Evaluate the response
 */

import { readFile } from 'fs/promises';
import Anthropic from '@anthropic-ai/sdk';

const AGENT_API_URL = process.env.POWER_AGENT_API_URL || 'https://your-agent-api.com';
const anthropic = new Anthropic();

/**
 * Load a task by ID
 */
async function loadTask(taskId) {
  // Parse tier from task ID (e.g., "t1-ttest-001" -> tier 1)
  const tierMatch = taskId.match(/^t(\d)-/);
  if (!tierMatch) {
    throw new Error(`Invalid task ID format: ${taskId}`);
  }
  const tier = tierMatch[1];

  const filePath = `../tasks/tier${tier}/tasks.json`;
  const content = await readFile(filePath, 'utf-8');
  const data = JSON.parse(content);

  const task = data.tasks.find((t) => t.id === taskId);
  if (!task) {
    throw new Error(`Task not found: ${taskId}`);
  }

  return { ...task, tier: parseInt(tier) };
}

/**
 * Send task to agent (placeholder - implement your agent call)
 */
async function runAgentTask(task) {
  console.log(`\nSending to agent: ${task.question.substring(0, 100)}...`);

  // Example: Call your agent API
  // Replace this with your actual agent implementation
  try {
    const response = await fetch(`${AGENT_API_URL}/api/analyze-biostat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: task.question,
        mode: 'full_analysis',
        sessionId: `example-${Date.now()}`,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    // Handle SSE response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
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
            if (data.step === 'executing' && data.output) {
              analysisOutput += data.output + '\n';
            }
            if (data.step === 'chatbot_conclusion_stream' && data.text) {
              conclusionText += data.text;
            }
          } catch (e) {
            // Ignore parse errors
          }
        }
      }
    }

    return {
      success: true,
      response: {
        analysisOutput,
        conclusionText,
      },
    };
  } catch (error) {
    console.error(`Agent error: ${error.message}`);
    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * Evaluate agent response using LLM judge
 */
async function evaluateResponse(task, result) {
  if (!result.success) {
    return {
      passed: false,
      totalScore: 0,
      error: result.error,
    };
  }

  const gt = task.ground_truth;
  const tol = task.tolerance;

  // Find expected value
  const expectedN =
    gt.sample_size_per_group ||
    gt.sample_size ||
    gt.subjects_per_group ||
    gt.subjects ||
    gt.total_sample_size;
  const toleranceN = tol.sample_size || 20;

  const prompt = `You are evaluating a power analysis response.

QUESTION: ${task.question}

EXPECTED ANSWER: ${expectedN} (tolerance: ±${toleranceN})

AGENT RESPONSE:
${result.response.analysisOutput}
${result.response.conclusionText}

Extract the agent's final sample size recommendation and score:
1. Template Selection (0-20): Correct analysis type?
2. Parameter Extraction (0-20): Parameters correct?
3. Calculation Accuracy (0-30): Within tolerance of ${expectedN}?
4. Code Quality (0-15): Valid R code?
5. Interpretation (0-15): Clear explanation?

Return JSON only:
{
  "agentValue": <extracted sample size or null>,
  "scores": {"templateSelection": N, "parameterExtraction": N, "calculationAccuracy": N, "codeQuality": N, "interpretationQuality": N},
  "totalScore": N,
  "passed": <true if score >= 70 and within tolerance>,
  "justification": "brief explanation"
}`;

  const response = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 1000,
    temperature: 0,
    messages: [{ role: 'user', content: prompt }],
  });

  const content = response.content[0].text;
  const jsonMatch = content.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    const evaluation = JSON.parse(jsonMatch[0]);

    // Strict tolerance check
    if (evaluation.agentValue != null) {
      const diff = Math.abs(evaluation.agentValue - expectedN);
      evaluation.withinTolerance = diff <= toleranceN;

      if (!evaluation.withinTolerance) {
        evaluation.scores.calculationAccuracy = 0;
        evaluation.totalScore =
          evaluation.scores.templateSelection +
          evaluation.scores.parameterExtraction +
          evaluation.scores.codeQuality +
          evaluation.scores.interpretationQuality;
        evaluation.passed = false;
      }
    }

    return evaluation;
  }

  return { passed: false, totalScore: 0, error: 'Evaluation failed' };
}

/**
 * Main function
 */
async function main() {
  const taskId = process.argv[2] || 't1-ttest-001';

  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║         POWER AGENT BENCHMARK - SINGLE TASK                ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  try {
    // Load task
    console.log(`\nLoading task: ${taskId}`);
    const task = await loadTask(taskId);
    console.log(`Tier: ${task.tier}`);
    console.log(`Template: ${task.template}`);
    console.log(`Difficulty: ${task.difficulty}`);
    console.log(`\nQuestion: ${task.question}`);
    console.log(`\nGround Truth:`, task.ground_truth);
    console.log(`Tolerance:`, task.tolerance);

    // Run agent
    const result = await runAgentTask(task);

    // Evaluate
    console.log('\nEvaluating response...');
    const evaluation = await evaluateResponse(task, result);

    // Display results
    console.log('\n' + '─'.repeat(60));
    console.log('EVALUATION RESULTS');
    console.log('─'.repeat(60));
    console.log(`Agent Value: ${evaluation.agentValue}`);
    console.log(`Within Tolerance: ${evaluation.withinTolerance}`);
    console.log(`Total Score: ${evaluation.totalScore}/100`);
    console.log(`Passed: ${evaluation.passed ? '✓ YES' : '✗ NO'}`);

    if (evaluation.scores) {
      console.log('\nScores:');
      console.log(`  Template Selection:    ${evaluation.scores.templateSelection}/20`);
      console.log(`  Parameter Extraction:  ${evaluation.scores.parameterExtraction}/20`);
      console.log(`  Calculation Accuracy:  ${evaluation.scores.calculationAccuracy}/30`);
      console.log(`  Code Quality:          ${evaluation.scores.codeQuality}/15`);
      console.log(`  Interpretation:        ${evaluation.scores.interpretationQuality}/15`);
    }

    if (evaluation.justification) {
      console.log(`\nJustification: ${evaluation.justification}`);
    }
  } catch (error) {
    console.error(`\nError: ${error.message}`);
    process.exit(1);
  }
}

main();
