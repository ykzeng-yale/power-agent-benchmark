#!/usr/bin/env node
// Generate a horizontal grouped bar chart (SVG) for the benchmark leaderboard.
// Zero dependencies — run with: node leaderboard/generate-chart.js

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------------------------------------------------------------------------
// Data (same as README table, sorted by overall score descending)
// ---------------------------------------------------------------------------
const models = [
  { name: 'Power Agent (Claude Opus 4.5)',                     t1: 100,  t2: 100,  t3: 100,  t4: 95.2, overall: 99.1 },
  { name: 'Gemini 3.1 Pro Preview + Code Exec',                t1: 86.7, t2: 74.3, t3: 70.0, t4: 38.1, overall: 69.8 },
  { name: 'ChatGPT Thinking Mode (Web UI)',                    t1: 60.0, t2: 62.9, t3: 75.0, t4: 28.6, overall: 57.5 },
  { name: 'ChatGPT Auto Mode (Web UI)',                        t1: 56.7, t2: 65.7, t3: 70.0, t4: 28.6, overall: 56.6 },
  { name: 'GPT-5.2 Pro (API Only)',                            t1: 60.0, t2: 60.0, t3: 80.0, t4:  9.5, overall: 53.8 },
  { name: 'Gemini 3.1 Pro Preview (API Only)',                 t1: 60.0, t2: 62.9, t3: 70.0, t4:  4.8, overall: 51.9 },
  { name: 'Gemini 2.5 Pro + Code Exec',                       t1: 73.3, t2: 57.1, t3: 50.0, t4:  4.8, overall: 50.0 },
  { name: 'Claude Opus 4.6 (API Only)',                        t1: 43.3, t2: 62.9, t3: 80.0, t4:  4.8, overall: 49.1 },
  { name: 'GPT-5.2 + Code Interpreter (API)',                  t1: 63.3, t2: 60.0, t3: 50.0, t4:  4.8, overall: 48.1 },
  { name: 'Gemini 2.5 Flash + Code Exec',                     t1: 70.0, t2: 51.4, t3: 50.0, t4:  0.0, overall: 46.2 },
  { name: 'Gemini 2.5 Pro (API Only)',                         t1: 43.3, t2: 54.3, t3: 55.0, t4:  4.8, overall: 41.5 },
  { name: 'GPT-5.2 (API Only)',                                t1: 30.0, t2: 65.7, t3: 45.0, t4:  4.8, overall: 39.6 },
  { name: 'Claude Sonnet 4.6 (API Only)',                      t1: 33.3, t2: 37.1, t3: 65.0, t4:  4.8, overall: 34.9 },
  { name: 'Gemini 2.5 Flash (API Only)',                       t1: 33.3, t2: 34.3, t3: 45.0, t4:  0.0, overall: 29.2 },
];

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------
const CHART_LEFT   = 310;   // space for model labels
const CHART_RIGHT  = 60;
const CHART_TOP    = 60;    // space for legend
const CHART_BOTTOM = 40;
const BAR_GROUP_H  = 48;    // height per model group
const BAR_H        = 7;     // individual bar height
const BAR_GAP      = 1.5;   // gap between bars within a group
const GROUP_GAP    = 10;    // gap between model groups

const chartW = 560;         // width of the bar area
const chartH = models.length * (BAR_GROUP_H + GROUP_GAP) - GROUP_GAP;
const svgW   = CHART_LEFT + chartW + CHART_RIGHT;
const svgH   = CHART_TOP + chartH + CHART_BOTTOM;

// ---------------------------------------------------------------------------
// Colors
// ---------------------------------------------------------------------------
const COLORS = {
  t1:      '#4A90D9',  // blue
  t2:      '#50B86C',  // green
  t3:      '#E8943A',  // orange
  t4:      '#D94A4A',  // red
  overall: '#2C3E50',  // dark navy
};

const LABELS = {
  t1:      'Tier 1',
  t2:      'Tier 2',
  t3:      'Tier 3',
  t4:      'Tier 4',
  overall: 'Overall',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

// ---------------------------------------------------------------------------
// Build SVG
// ---------------------------------------------------------------------------
let svg = '';

svg += `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${svgW} ${svgH}" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif">\n`;

// Background
svg += `<rect width="${svgW}" height="${svgH}" fill="#FAFBFC" rx="8"/>\n`;

// ---------------------------------------------------------------------------
// Legend (top)
// ---------------------------------------------------------------------------
{
  const keys = ['t1', 't2', 't3', 't4', 'overall'];
  let lx = CHART_LEFT;
  const ly = 28;
  for (const k of keys) {
    const isOverall = k === 'overall';
    const rw = 14, rh = 10;
    svg += `<rect x="${lx}" y="${ly - rh + 2}" width="${rw}" height="${rh}" rx="2" fill="${COLORS[k]}"${isOverall ? ' stroke="#1A252F" stroke-width="0.5"' : ''}/>\n`;
    lx += rw + 4;
    const label = LABELS[k];
    svg += `<text x="${lx}" y="${ly}" font-size="11" fill="#333"${isOverall ? ' font-weight="700"' : ''}>${esc(label)}</text>\n`;
    lx += label.length * 6.4 + 16;
  }
}

// ---------------------------------------------------------------------------
// Grid lines & axis labels
// ---------------------------------------------------------------------------
for (const pct of [0, 25, 50, 75, 100]) {
  const gx = CHART_LEFT + (pct / 100) * chartW;
  svg += `<line x1="${gx}" y1="${CHART_TOP}" x2="${gx}" y2="${CHART_TOP + chartH}" stroke="#E0E0E0" stroke-width="0.8"/>\n`;
  svg += `<text x="${gx}" y="${CHART_TOP + chartH + 18}" font-size="11" fill="#888" text-anchor="middle">${pct}%</text>\n`;
}

// ---------------------------------------------------------------------------
// Bars
// ---------------------------------------------------------------------------
const tiers = ['t1', 't2', 't3', 't4', 'overall'];

for (let i = 0; i < models.length; i++) {
  const m = models[i];
  const groupY = CHART_TOP + i * (BAR_GROUP_H + GROUP_GAP);

  // Model label (right-aligned)
  const labelY = groupY + BAR_GROUP_H / 2 + 4;
  const rank = i + 1;
  svg += `<text x="${CHART_LEFT - 10}" y="${labelY}" font-size="12" fill="#333" text-anchor="end">${rank}. ${esc(m.name)}</text>\n`;

  // Alternating row background
  if (i % 2 === 0) {
    svg += `<rect x="${CHART_LEFT}" y="${groupY}" width="${chartW}" height="${BAR_GROUP_H}" fill="#F4F6F8" rx="2"/>\n`;
  }

  // Individual bars
  for (let j = 0; j < tiers.length; j++) {
    const key = tiers[j];
    const val = m[key];
    const barY = groupY + 3 + j * (BAR_H + BAR_GAP);
    const barW = Math.max((val / 100) * chartW, 0);
    const isOverall = key === 'overall';
    const h = isOverall ? BAR_H + 1.5 : BAR_H;

    svg += `<rect x="${CHART_LEFT}" y="${barY}" width="${barW}" height="${h}" rx="2" fill="${COLORS[key]}"${isOverall ? ' stroke="#1A252F" stroke-width="0.4"' : ''}/>\n`;

    // Value label for overall score
    if (isOverall) {
      const labelX = CHART_LEFT + barW + 4;
      svg += `<text x="${labelX}" y="${barY + h - 1}" font-size="10" font-weight="700" fill="${COLORS.overall}">${val.toFixed(1)}%</text>\n`;
    }
  }
}

// Title
svg += `<text x="${svgW / 2}" y="${16}" font-size="13" font-weight="600" fill="#333" text-anchor="middle">Power Agent Benchmark — Model Pass Rates by Tier</text>\n`;

svg += '</svg>\n';

// ---------------------------------------------------------------------------
// Write file
// ---------------------------------------------------------------------------
const outPath = path.join(__dirname, 'leaderboard-chart.svg');
fs.writeFileSync(outPath, svg, 'utf-8');
console.log(`Written ${outPath} (${svg.length} bytes)`);
