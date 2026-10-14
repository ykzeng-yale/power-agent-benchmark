const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const RESULTS_FILE = path.join(__dirname, 'results', 'results.json');
const STATE_FILE = path.join(__dirname, 'results', 'state.json');
const TASKS_FILE = path.join(__dirname, 'all_tasks.json');
const RESPONSES_DIR = path.join(__dirname, 'results', 'responses');
const CDP_URL = 'http://127.0.0.1:18800';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function loadResults() { try { return JSON.parse(fs.readFileSync(RESULTS_FILE, 'utf8')); } catch { return []; } }
function saveResults(r) { fs.writeFileSync(RESULTS_FILE, JSON.stringify(r, null, 2)); }
function loadState() { try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch { return { completed: [], current_index: 0 }; } }
function saveState(s) { fs.writeFileSync(STATE_FILE, JSON.stringify(s, null, 2)); }

if (!fs.existsSync(RESPONSES_DIR)) fs.mkdirSync(RESPONSES_DIR, { recursive: true });

function getExpectedAnswer(task) {
  const gt = task.ground_truth;
  const keys = ['sample_size_per_group','sample_size','n_per_group','n','total_sample_size',
    'n_clusters','n_per_cluster','n_events','minimum_n','events_required'];
  for (const k of keys) if (gt[k] !== undefined && typeof gt[k] === 'number') return { value: gt[k], key: k };
  const skip = ['effect_size_d','power','alpha','effect_size','icc','r_squared','variance_explained','odds_ratio','hazard_ratio','kappa'];
  for (const [k,v] of Object.entries(gt)) if (typeof v === 'number' && !skip.includes(k)) return { value: v, key: k };
  return null;
}

function getTolerance(task) {
  const tol = task.tolerance; if (!tol) return 1;
  for (const [k,v] of Object.entries(tol)) if (typeof v === 'number') return v;
  return 1;
}

function extractNumber(text, expectedValue, expectedKey) {
  // Clean KaTeX/LaTeX artifacts
  let clean = text
    .replace(/\\[a-zA-Z]+\{[^}]*\}/g, ' ')
    .replace(/\\[a-zA-Z]+/g, ' ')
    .replace(/[{}]/g, ' ')
    .replace(/\s+/g, ' ');
  
  const isPerGroup = expectedKey && (expectedKey.includes('per_group') || expectedKey.includes('per_cluster') || expectedKey.includes('per_arm'));
  const isTotal = expectedKey && (expectedKey.includes('total') || expectedKey === 'sample_size' || expectedKey === 'n' || expectedKey === 'n_events');
  
  // Get the last 40% of text (conclusions are at the end)
  const lastPart = clean.slice(-Math.floor(clean.length * 0.4));
  
  // Ordered by specificity
  const patterns = [
    // Exact conclusion patterns
    /(?:you(?:'ll)? need|we need|required?|recruit|enroll|plan for)\s+(?:at least\s+)?(?:about\s+)?(?:approximately\s+)?(\d+)\s*(?:per group|per arm|per cluster|per treatment|participants?|patients?|subjects?|samples?|events?|each group|in each|total)/i,
    /(?:sample size)[^.]{0,30}?(\d+)\s*(?:per group|per arm|per cluster|per treatment|participants?|patients?|total|events?)/i,
    /n\s*(?:per (?:group|arm|cluster))?\s*[=≈≥]\s*(\d+)/i,
    /(?:round(?:ing)?\s*up|ceiling)[^.]{0,20}?(\d+)/i,
    /(\d+)\s*(?:per group|per arm|per cluster|per treatment|in each group|in each arm)/i,
    /(\d+)\s*(?:participants?|patients?|subjects?)\s*(?:per|in each|total)/i,
    /(?:total(?:\s+sample)?\s+(?:size|of))\s*[=:≈]?\s*(\d+)/i,
    /(?:minimum|at least)\s*(?:of\s+)?(\d+)/i,
  ];
  
  // Try last part first, then full text
  for (const source of [lastPart, clean]) {
    for (const pat of patterns) {
      const m = source.match(pat);
      if (m) {
        const n = parseInt(m[1]);
        if (n >= 5 && n <= 100000) {
          // Sanity: if expecting per-group and got a number that's ~expected*k_groups, skip
          if (isPerGroup && expectedValue && n > expectedValue * 1.8 && n < expectedValue * 6) {
            continue; // Likely total, not per-group
          }
          return n;
        }
      }
    }
  }
  
  // Fallback: find all reasonable numbers and pick closest to expected
  if (expectedValue) {
    const allNums = [...clean.matchAll(/(\d+)/g)]
      .map(m => parseInt(m[1]))
      .filter(n => n >= Math.max(5, expectedValue * 0.3) && n <= expectedValue * 3);
    if (allNums.length > 0) {
      allNums.sort((a, b) => Math.abs(a - expectedValue) - Math.abs(b - expectedValue));
      return allNums[0];
    }
  }
  
  return null;
}

async function getCleanResponse(page) {
  // Method 1: Strip KaTeX from DOM and get clean text
  try {
    const text = await page.evaluate(() => {
      const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
      if (msgs.length === 0) return null;
      const last = msgs[msgs.length - 1];
      const clone = last.cloneNode(true);
      // Remove KaTeX rendered HTML (keep annotation/mathml)
      clone.querySelectorAll('.katex-html').forEach(el => el.remove());
      // Remove code block outputs that might have confusing numbers
      // Keep the text content
      let text = clone.innerText;
      // Clean up multiple newlines
      text = text.replace(/\n{3,}/g, '\n\n').trim();
      return text;
    });
    if (text && text.length > 30) return text;
  } catch (e) { /* fall through */ }
  
  // Method 2: Try clipboard
  try {
    const copyBtn = page.locator('button[data-testid="copy-turn-action-button"]').last();
    if (await copyBtn.count() > 0) {
      await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
      await copyBtn.click();
      await sleep(300);
      const text = await page.evaluate(() => navigator.clipboard.readText());
      if (text && text.length > 30) return text;
    }
  } catch (e) { /* fall through */ }
  
  // Method 3: Raw innerText (last resort)
  try {
    const msgs = await page.locator('[data-message-author-role="assistant"]').all();
    if (msgs.length > 0) return await msgs[msgs.length - 1].innerText();
  } catch (e) { /* fall through */ }
  
  return null;
}

async function runTask(page, task, taskIndex, total) {
  const expected = getExpectedAnswer(task);
  const tolerance = getTolerance(task);
  if (!expected) { console.log(`  SKIP ${task.id}: no expected answer`); return null; }
  
  console.log(`\n[${ new Date().toTimeString().slice(0,8)}] Task ${taskIndex+1}/${total}: ${task.id}`);
  console.log(`  Expect: ${expected.value} (${expected.key}) ±${tolerance}`);
  const startTime = Date.now();
  
  // Navigate to fresh temp chat
  await page.goto('https://chatgpt.com/?temporary-chat=true', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(3000);
  
  // Type question
  const typed = await page.evaluate((q) => {
    const el = document.querySelector('#prompt-textarea') || document.querySelector('[contenteditable="true"]');
    if (!el) return false;
    el.focus();
    document.execCommand('selectAll');
    document.execCommand('insertText', false, q);
    return true;
  }, task.question);
  if (!typed) return mkFail(task, expected, tolerance, 'no_input_field', startTime);
  await sleep(500);
  
  // Send
  try {
    const sendBtn = page.locator('button[data-testid="send-button"]');
    await sendBtn.waitFor({ state: 'visible', timeout: 5000 });
    await sendBtn.click();
  } catch { await page.keyboard.press('Enter'); }
  
  // Wait for response
  let responseText = null;
  for (let t = 0; t < 180; t += 3) {
    await sleep(3000);
    const generating = await page.locator('button[aria-label="Stop generating"], button[data-testid="stop-button"]').count();
    if (generating === 0 && t > 6) {
      responseText = await getCleanResponse(page);
      if (responseText && responseText.length > 50) break;
    }
    if (t > 0 && t % 30 === 0) console.log(`  Waiting... ${t}s`);
  }
  
  if (!responseText) responseText = await getCleanResponse(page);
  const elapsed = Math.round((Date.now() - startTime) / 1000);
  
  // Save raw response
  if (responseText) {
    fs.writeFileSync(path.join(RESPONSES_DIR, `${task.id}.txt`), responseText);
  }
  
  if (!responseText || responseText.length < 30) {
    console.log(`  FAIL: No response (${elapsed}s)`);
    return mkFail(task, expected, tolerance, 'no_response', startTime);
  }
  
  console.log(`  Got ${responseText.length} chars in ${elapsed}s`);
  
  // Extract and evaluate
  const answer = extractNumber(responseText, expected.value, expected.key);
  const diff = answer !== null ? Math.abs(answer - expected.value) : null;
  const pass = diff !== null && diff <= tolerance;
  
  console.log(`  → ${answer} vs ${expected.value} (diff=${diff}, tol=±${tolerance}) ${pass ? '✅' : '❌'}`);
  
  return {
    task_id: task.id, tier: parseInt(task.id.split('-')[0].replace('t','')),
    template: task.template, difficulty: task.difficulty || 'unknown',
    ground_truth_n: expected.value, ground_truth_key: expected.key, tolerance,
    chatgpt_answer: answer, difference: diff, within_tolerance: pass,
    result: pass ? 'PASS' : 'FAIL',
    notes: responseText.substring(0, 500),
    response_time_s: elapsed, timestamp: new Date().toISOString()
  };
}

function mkFail(task, exp, tol, reason, st) {
  return {
    task_id: task.id, tier: parseInt(task.id.split('-')[0].replace('t','')),
    template: task.template, difficulty: task.difficulty || 'unknown',
    ground_truth_n: exp?.value, ground_truth_key: exp?.key, tolerance: tol,
    chatgpt_answer: null, difference: null, within_tolerance: false,
    result: 'FAIL', notes: reason,
    response_time_s: Math.round((Date.now() - st) / 1000),
    timestamp: new Date().toISOString()
  };
}

async function main() {
  const tasks = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf8'));
  let results = loadResults();
  const state = loadState();
  const completed = new Set(state.completed);
  let [P, F] = [results.filter(r=>r.within_tolerance).length, results.filter(r=>!r.within_tolerance).length];
  
  console.log(`=== Benchmark Runner | ${tasks.length} tasks | ${completed.size} done | ${tasks.length - completed.size} remaining ===`);
  
  const browser = await chromium.connectOverCDP(CDP_URL);
  const ctx = browser.contexts()[0] || await browser.newContext();
  const page = await ctx.newPage();
  
  for (let i = 0; i < tasks.length; i++) {
    if (completed.has(tasks[i].id)) continue;
    try {
      const r = await runTask(page, tasks[i], i, tasks.length);
      if (r) {
        results.push(r); completed.add(r.task_id);
        if (r.within_tolerance) P++; else F++;
        saveResults(results); state.completed = [...completed]; state.current_index = i+1; saveState(state);
        console.log(`  Score: ${P}/${P+F} (${(P/(P+F)*100).toFixed(0)}%) | Done: ${completed.size}/${tasks.length}`);
      }
    } catch (err) {
      console.error(`  ERR ${tasks[i].id}: ${err.message}`);
      const exp = getExpectedAnswer(tasks[i]);
      results.push(mkFail(tasks[i], exp, getTolerance(tasks[i]), err.message, Date.now()));
      F++; completed.add(tasks[i].id);
      saveResults(results); state.completed = [...completed]; saveState(state);
    }
    await sleep(1500);
  }
  
  console.log(`\n=== FINAL: ${P} PASS / ${F} FAIL / ${tasks.length} total = ${(P/tasks.length*100).toFixed(1)}% ===`);
  await page.close();
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
