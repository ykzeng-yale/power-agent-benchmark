/**
 * Scoring and Analytics for Power Agent Benchmark
 *
 * Aggregates evaluation results and computes metrics
 */

import { config } from './config.js';

/**
 * Compute aggregate statistics from evaluation results
 */
export function computeAggregateStats(evaluations) {
  if (!evaluations || evaluations.length === 0) {
    return null;
  }

  const stats = {
    total: evaluations.length,
    passed: 0,
    failed: 0,
    passRate: 0,
    averageScore: 0,
    medianScore: 0,
    scoreDistribution: {
      excellent: 0,  // 90-100
      good: 0,       // 80-89
      acceptable: 0, // 70-79
      poor: 0,       // 50-69
      failing: 0,    // 0-49
    },
    byCategory: {
      templateSelection: { total: 0, average: 0, scores: [] },
      parameterExtraction: { total: 0, average: 0, scores: [] },
      calculationAccuracy: { total: 0, average: 0, scores: [] },
      codeQuality: { total: 0, average: 0, scores: [] },
      interpretationQuality: { total: 0, average: 0, scores: [] },
    },
    byTier: {},
    byTemplate: {},
    byDifficulty: {
      basic: { total: 0, passed: 0, averageScore: 0 },
      intermediate: { total: 0, passed: 0, averageScore: 0 },
      advanced: { total: 0, passed: 0, averageScore: 0 },
    },
    sampleSizeAccuracy: {
      withinTolerance: 0,
      within2xTolerance: 0,
      averageError: 0,
      averageErrorPercent: 0,
    },
    commonErrors: {},
    timestamp: new Date().toISOString(),
  };

  const scores = [];
  const sampleSizeErrors = [];
  const sampleSizeErrorPercents = [];

  for (const eval_ of evaluations) {
    // Basic counts
    if (eval_.passed) {
      stats.passed++;
    } else {
      stats.failed++;
    }

    scores.push(eval_.totalScore);

    // Score distribution
    if (eval_.totalScore >= 90) {
      stats.scoreDistribution.excellent++;
    } else if (eval_.totalScore >= 80) {
      stats.scoreDistribution.good++;
    } else if (eval_.totalScore >= 70) {
      stats.scoreDistribution.acceptable++;
    } else if (eval_.totalScore >= 50) {
      stats.scoreDistribution.poor++;
    } else {
      stats.scoreDistribution.failing++;
    }

    // By category
    if (eval_.scores) {
      for (const category of Object.keys(stats.byCategory)) {
        if (eval_.scores[category] !== undefined) {
          stats.byCategory[category].scores.push(eval_.scores[category]);
          stats.byCategory[category].total += eval_.scores[category];
        }
      }
    }

    // By tier
    const tier = `tier${eval_.tier}`;
    if (!stats.byTier[tier]) {
      stats.byTier[tier] = { total: 0, passed: 0, scores: [], averageScore: 0 };
    }
    stats.byTier[tier].total++;
    stats.byTier[tier].scores.push(eval_.totalScore);
    if (eval_.passed) stats.byTier[tier].passed++;

    // By template
    const template = eval_.template;
    if (template) {
      if (!stats.byTemplate[template]) {
        stats.byTemplate[template] = { total: 0, passed: 0, scores: [], averageScore: 0 };
      }
      stats.byTemplate[template].total++;
      stats.byTemplate[template].scores.push(eval_.totalScore);
      if (eval_.passed) stats.byTemplate[template].passed++;
    }

    // By difficulty
    const difficulty = eval_.difficulty;
    if (difficulty && stats.byDifficulty[difficulty]) {
      stats.byDifficulty[difficulty].total++;
      if (eval_.passed) stats.byDifficulty[difficulty].passed++;
      stats.byDifficulty[difficulty].averageScore += eval_.totalScore;
    }

    // Sample size accuracy
    if (eval_.sampleSizeError !== null && eval_.sampleSizeError !== undefined) {
      sampleSizeErrors.push(eval_.sampleSizeError);
      const groundTruthN = eval_.groundTruth?.sample_size_per_group ||
                          eval_.groundTruth?.sample_size ||
                          eval_.groundTruth?.subjects_per_group ||
                          eval_.groundTruth?.total_sample_size;
      if (groundTruthN) {
        const errorPercent = (eval_.sampleSizeError / groundTruthN) * 100;
        sampleSizeErrorPercents.push(errorPercent);
      }
    }

    // Track common errors
    if (eval_.criticalErrors) {
      for (const error of eval_.criticalErrors) {
        const errorKey = normalizeError(error);
        stats.commonErrors[errorKey] = (stats.commonErrors[errorKey] || 0) + 1;
      }
    }
  }

  // Compute averages
  stats.passRate = stats.passed / stats.total;
  stats.averageScore = scores.reduce((a, b) => a + b, 0) / scores.length;

  // Median score
  const sortedScores = [...scores].sort((a, b) => a - b);
  const mid = Math.floor(sortedScores.length / 2);
  stats.medianScore = sortedScores.length % 2
    ? sortedScores[mid]
    : (sortedScores[mid - 1] + sortedScores[mid]) / 2;

  // Category averages
  for (const category of Object.keys(stats.byCategory)) {
    const catScores = stats.byCategory[category].scores;
    if (catScores.length > 0) {
      stats.byCategory[category].average = catScores.reduce((a, b) => a + b, 0) / catScores.length;
    }
    delete stats.byCategory[category].scores; // Remove raw scores from output
  }

  // Tier averages
  for (const tier of Object.keys(stats.byTier)) {
    const tierData = stats.byTier[tier];
    if (tierData.scores.length > 0) {
      tierData.averageScore = tierData.scores.reduce((a, b) => a + b, 0) / tierData.scores.length;
      tierData.passRate = tierData.passed / tierData.total;
    }
    delete tierData.scores;
  }

  // Template averages
  for (const template of Object.keys(stats.byTemplate)) {
    const templateData = stats.byTemplate[template];
    if (templateData.scores.length > 0) {
      templateData.averageScore = templateData.scores.reduce((a, b) => a + b, 0) / templateData.scores.length;
      templateData.passRate = templateData.passed / templateData.total;
    }
    delete templateData.scores;
  }

  // Difficulty averages
  for (const diff of Object.keys(stats.byDifficulty)) {
    const diffData = stats.byDifficulty[diff];
    if (diffData.total > 0) {
      diffData.averageScore = diffData.averageScore / diffData.total;
      diffData.passRate = diffData.passed / diffData.total;
    }
  }

  // Sample size accuracy
  if (sampleSizeErrors.length > 0) {
    stats.sampleSizeAccuracy.averageError = sampleSizeErrors.reduce((a, b) => a + b, 0) / sampleSizeErrors.length;
  }
  if (sampleSizeErrorPercents.length > 0) {
    stats.sampleSizeAccuracy.averageErrorPercent = sampleSizeErrorPercents.reduce((a, b) => a + b, 0) / sampleSizeErrorPercents.length;
  }

  // Sort common errors by frequency
  stats.commonErrors = Object.entries(stats.commonErrors)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .reduce((obj, [k, v]) => ({ ...obj, [k]: v }), {});

  return stats;
}

/**
 * Normalize error messages for grouping
 */
function normalizeError(error) {
  // Remove specific numbers/identifiers
  let normalized = error
    .replace(/\d+/g, 'N')
    .replace(/['"][^'"]+['"]/g, '"..."')
    .toLowerCase()
    .trim();

  // Truncate long errors
  if (normalized.length > 100) {
    normalized = normalized.substring(0, 100) + '...';
  }

  return normalized;
}

/**
 * Compare results against target metrics
 */
export function compareToTargets(stats) {
  const targets = config.targets;
  const comparison = {
    overall: {},
    byTier: {},
    met: [],
    notMet: [],
  };

  // Overall targets
  comparison.overall.templateAccuracy = {
    target: targets.overall.templateAccuracy,
    actual: stats.byCategory.templateSelection.average / 20, // Normalize to 0-1
    met: (stats.byCategory.templateSelection.average / 20) >= targets.overall.templateAccuracy,
  };

  comparison.overall.calculationAccuracy = {
    target: targets.overall.calculationAccuracy,
    actual: stats.byCategory.calculationAccuracy.average / 30, // Normalize to 0-1
    met: (stats.byCategory.calculationAccuracy.average / 30) >= targets.overall.calculationAccuracy,
  };

  comparison.overall.passRate = {
    target: targets.overall.passRate,
    actual: stats.passRate,
    met: stats.passRate >= targets.overall.passRate,
  };

  // Tier targets
  for (const [tier, targetRate] of Object.entries(targets.byTier)) {
    const tierStats = stats.byTier[tier];
    if (tierStats) {
      comparison.byTier[tier] = {
        target: targetRate,
        actual: tierStats.passRate,
        met: tierStats.passRate >= targetRate,
      };

      if (tierStats.passRate >= targetRate) {
        comparison.met.push(`${tier} pass rate`);
      } else {
        comparison.notMet.push(`${tier} pass rate (${(tierStats.passRate * 100).toFixed(1)}% < ${(targetRate * 100)}%)`);
      }
    }
  }

  // Overall met/not met
  for (const [metric, data] of Object.entries(comparison.overall)) {
    if (data.met) {
      comparison.met.push(metric);
    } else {
      comparison.notMet.push(`${metric} (${(data.actual * 100).toFixed(1)}% < ${(data.target * 100)}%)`);
    }
  }

  comparison.allTargetsMet = comparison.notMet.length === 0;

  return comparison;
}

/**
 * Generate a summary report
 */
export function generateSummary(stats, comparison) {
  const lines = [];

  lines.push('═'.repeat(60));
  lines.push('POWER AGENT BENCHMARK RESULTS');
  lines.push('═'.repeat(60));
  lines.push('');

  // Overall summary
  lines.push('OVERALL PERFORMANCE');
  lines.push('─'.repeat(40));
  lines.push(`Total Tasks:     ${stats.total}`);
  lines.push(`Passed:          ${stats.passed} (${(stats.passRate * 100).toFixed(1)}%)`);
  lines.push(`Failed:          ${stats.failed}`);
  lines.push(`Average Score:   ${stats.averageScore.toFixed(1)}/100`);
  lines.push(`Median Score:    ${stats.medianScore.toFixed(1)}/100`);
  lines.push('');

  // Score distribution
  lines.push('SCORE DISTRIBUTION');
  lines.push('─'.repeat(40));
  lines.push(`Excellent (90-100): ${stats.scoreDistribution.excellent}`);
  lines.push(`Good (80-89):       ${stats.scoreDistribution.good}`);
  lines.push(`Acceptable (70-79): ${stats.scoreDistribution.acceptable}`);
  lines.push(`Poor (50-69):       ${stats.scoreDistribution.poor}`);
  lines.push(`Failing (0-49):     ${stats.scoreDistribution.failing}`);
  lines.push('');

  // By tier
  lines.push('PERFORMANCE BY TIER');
  lines.push('─'.repeat(40));
  for (const tier of ['tier1', 'tier2', 'tier3', 'tier4']) {
    const tierData = stats.byTier[tier];
    if (tierData) {
      const target = config.targets.byTier[tier] * 100;
      const actual = tierData.passRate * 100;
      const status = actual >= target ? '✓' : '✗';
      lines.push(`${tier.toUpperCase()}: ${actual.toFixed(1)}% pass rate (target: ${target}%) ${status}`);
      lines.push(`       Avg score: ${tierData.averageScore.toFixed(1)}, n=${tierData.total}`);
    }
  }
  lines.push('');

  // By category
  lines.push('PERFORMANCE BY CRITERION');
  lines.push('─'.repeat(40));
  const categoryMaxScores = {
    templateSelection: 20,
    parameterExtraction: 20,
    calculationAccuracy: 30,
    codeQuality: 15,
    interpretationQuality: 15,
  };
  for (const [category, data] of Object.entries(stats.byCategory)) {
    const maxScore = categoryMaxScores[category];
    const percent = (data.average / maxScore) * 100;
    lines.push(`${category.padEnd(25)} ${data.average.toFixed(1)}/${maxScore} (${percent.toFixed(1)}%)`);
  }
  lines.push('');

  // Target comparison
  lines.push('TARGET METRICS');
  lines.push('─'.repeat(40));
  if (comparison.allTargetsMet) {
    lines.push('✓ All targets met!');
  } else {
    lines.push('Targets met:');
    for (const met of comparison.met) {
      lines.push(`  ✓ ${met}`);
    }
    lines.push('Targets not met:');
    for (const notMet of comparison.notMet) {
      lines.push(`  ✗ ${notMet}`);
    }
  }
  lines.push('');

  // Common errors
  if (Object.keys(stats.commonErrors).length > 0) {
    lines.push('COMMON ERRORS');
    lines.push('─'.repeat(40));
    for (const [error, count] of Object.entries(stats.commonErrors)) {
      lines.push(`(${count}x) ${error}`);
    }
    lines.push('');
  }

  lines.push('═'.repeat(60));
  lines.push(`Report generated: ${stats.timestamp}`);

  return lines.join('\n');
}

/**
 * Compute score for a single evaluation
 */
export function computeScore(evaluation) {
  const scores = evaluation.scores;
  if (!scores) return 0;

  return (
    (scores.templateSelection || 0) +
    (scores.parameterExtraction || 0) +
    (scores.calculationAccuracy || 0) +
    (scores.codeQuality || 0) +
    (scores.interpretationQuality || 0)
  );
}

/**
 * Determine pass/fail based on score
 */
export function isPassing(score) {
  return score >= config.scoring.passingThreshold;
}

export default {
  computeAggregateStats,
  compareToTargets,
  generateSummary,
  computeScore,
  isPassing,
};
