/**
 * Power Agent Benchmark Configuration
 *
 * Configuration settings for the end-to-end benchmark evaluation system.
 */

export const config = {
  // API endpoints
  api: {
    baseUrl: process.env.POWER_AGENT_API_URL || 'https://power-agent-api-927325869269.us-central1.run.app',
    sessionEndpoint: '/api/biostat/session',
    messageEndpoint: '/api/biostat/message',
    stepsEndpoint: '/api/biostat/steps',
    timeout: 600000, // 10 minutes max per task (complex simulations need more time)
    pollInterval: 3000, // 3 seconds
  },

  // LLM-as-Judge settings
  llmJudge: {
    model: 'claude-sonnet-4-20250514',
    maxTokens: 4000,
    temperature: 0,
  },

  // Scoring weights (total 100 points)
  scoring: {
    templateSelection: 20,
    parameterExtraction: 20,
    calculationAccuracy: 30,
    codeQuality: 15,
    interpretationQuality: 15,
    passingThreshold: 70,
  },

  // Tolerance settings for numerical comparisons (STRICT: ~5% of GT)
  // NOTE: Task-level tolerances in tasks.json override these defaults
  tolerances: {
    tier1: {
      sampleSize: 3,      // ±3 for basic calculations
      sampleSizePercent: 0.05, // or ±5%
      power: 0.03,        // ±0.03
      effectSize: 0.01,   // ±0.01
    },
    tier2: {
      sampleSize: 5,      // ±5% of GT (task-level overrides)
      sampleSizePercent: 0.05,
      power: 0.03,
      effectSize: 0.02,
    },
    tier3: {
      sampleSize: 5,      // ±5% for formula, ±8% for simr
      sampleSizePercent: 0.05,
      power: 0.03,        // formula tasks
      powerSimr: 0.08,    // simulation tasks (nsim variance)
      effectSize: 0.03,
    },
    tier4: {
      sampleSize: 5,      // ±5% of GT
      sampleSizePercent: 0.05,
      power: 0.03,
      r2: 0.02,
    },
  },

  // Task distribution
  taskCounts: {
    tier1: {
      total: 30,
      templates: {
        two_sample_ttest: 6,
        paired_ttest: 4,
        one_way_anova: 5,
        two_proportions: 5,
        chi_square: 5,
        correlation: 5,
      },
    },
    tier2: {
      total: 35,
      templates: {
        linear_regression: 6,
        logistic_regression: 6,
        mixed_effects_lmm: 8,
        survival_analysis: 8,
        poisson_regression: 7,
      },
    },
    tier3: {
      total: 20,
      templates: {
        cluster_rct: 5,
        crossover_trial: 4,
        factorial_design: 4,
        simulation_simr: 7,
      },
    },
    tier4: {
      total: 21,
      templates: {
        riley_binary: 5,
        riley_survival: 5,
        riley_continuous: 4,
        external_validation: 7,
      },
    },
  },

  // Target success rates
  targets: {
    overall: {
      templateAccuracy: 0.90,
      calculationAccuracy: 0.85,
      passRate: 0.80,
    },
    byTier: {
      tier1: 0.95,
      tier2: 0.85,
      tier3: 0.75,
      tier4: 0.70,
    },
  },

  // File paths
  paths: {
    tasks: './tasks',
    results: './results',
    reports: './results/reports',
  },

  // Retry settings
  retry: {
    maxAttempts: 3,
    delayMs: 5000,
    retryOnTimeout: true,
  },
};

// Template ID mapping to match templates.js
export const templateMapping = {
  // Tier 1
  'two_sample_ttest': 'two_sample_ttest',
  'paired_ttest': 'paired_ttest',
  'one_way_anova': 'one_way_anova',
  'two_proportions': 'two_proportions',
  'chi_square': 'chi_square_test',
  'correlation': 'correlation',

  // Tier 2
  'linear_regression': 'linear_regression',
  'logistic_regression': 'logistic_regression',
  'mixed_effects_lmm': 'mixed_effects_continuous',
  'survival_analysis': 'survival_logrank',
  'poisson_regression': 'poisson_regression',

  // Tier 3
  'cluster_rct': 'cluster_rct',
  'crossover_trial': 'crossover_2x2',
  'factorial_design': 'factorial_2x2',
  'simulation_simr': 'simulation_based_simr',

  // Tier 4
  'riley_binary': 'riley_binary',
  'riley_survival': 'riley_survival',
  'riley_continuous': 'riley_continuous',
  'external_validation': 'riley_validation',
};

export default config;
