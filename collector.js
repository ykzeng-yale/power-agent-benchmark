const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TASKS_FILE = path.join(__dirname, 'all_tasks.json');
const RAW_DIR = path.join(__dirname, 'results', 'raw');
const LOG_FILE = path.join(__dirname, 'results', 'collector.log');
const CDP_URL = 'http://127.0.0.1:18800';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG_FILE, line + '\n');
}

if (!fs.existsSync(RAW_DIR)) fs.mkdirSync(RAW_DIR, { recursive: true });

async function getResponseText(page) {
  // Method 1: Click copy button
  try {
    const copyBtns = page.locator('button[data-testid="copy-turn-action-button"]');
    const count = await copyBtns.count();
    if (count > 0) {
      await copyBtns.last().click();
      await sleep(500);
      const text = await page.evaluate(() => navigator.clipboard.readText());
      if (text && text.length > 20) return text;
    }
  } catch {}
  
  // Method 2: Extract from assistant messages
  try {
    const msgs = page.locator('[data-message-author-role="assistant"]');
    const count = await msgs.count();
    if (count > 0) return await msgs.last().innerText();
  } catch {}
  
  // Method 3: Get all markdown containers
  try {
    const containers = page.locator('.markdown');
    const count = await containers.count();
    if (count > 0) return await containers.last().innerText();
  } catch {}
  
  return null;
}

async function collectOne(page, task, idx, total) {
  const outFile = path.join(RAW_DIR, `${task.id}.txt`);
  
  // Skip if already collected with real content
  if (fs.existsSync(outFile)) {
    const existing = fs.readFileSync(outFile, 'utf8');
    if (existing.length > 50 && !existing.startsWith('FAILED:')) {
      log(`[${idx+1}/${total}] SKIP ${task.id} (${existing.length}c)`);
      return 'skip';
    }
  }
  
  log(`[${idx+1}/${total}] ${task.id} (tier${task.tier} ${task.template})`);
  const startTime = Date.now();
  
  // Navigate to new chat
  await page.goto('https://chatgpt.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(3000);
  
  // Click the ProseMirror input
  const input = page.locator('div#prompt-textarea');
  await input.waitFor({ state: 'visible', timeout: 15000 });
  await input.click();
  await sleep(300);
  
  // Paste query via clipboard (fast)
  await page.evaluate(text => navigator.clipboard.writeText(text), task.question);
  await page.keyboard.press('Meta+v');
  await sleep(500);
  
  // Verify text was entered
  const entered = await input.innerText();
  if (entered.length < 20) {
    // Fallback: type it
    log('  Paste failed, typing...');
    await input.click();
    await page.keyboard.type(task.question, { delay: 5 });
    await sleep(500);
  }
  
  // Send
  try {
    const sendBtn = page.locator('button[data-testid="send-button"]');
    await sendBtn.waitFor({ state: 'visible', timeout: 5000 });
    await sendBtn.click();
  } catch {
    await page.keyboard.press('Enter');
  }
  
  // Wait for response (up to 4 min)
  let responseText = null;
  for (let t = 0; t < 240; t += 3) {
    await sleep(3000);
    const generating = await page.locator('button[aria-label="Stop generating"], button[data-testid="stop-button"]').count();
    if (generating === 0 && t > 9) {
      responseText = await getResponseText(page);
      if (responseText && responseText.length > 50) break;
    }
    if (t > 0 && t % 30 === 0) log(`  ...${t}s`);
  }
  
  if (!responseText || responseText.length < 50) {
    responseText = await getResponseText(page);
  }
  
  const elapsed = Math.round((Date.now() - startTime) / 1000);
  
  if (responseText && responseText.length > 30) {
    fs.writeFileSync(outFile, responseText);
    log(`  OK ${responseText.length}c in ${elapsed}s`);
    return 'ok';
  } else {
    fs.writeFileSync(outFile, `FAILED: No response after ${elapsed}s`);
    log(`  FAIL (${elapsed}s)`);
    return 'fail';
  }
}

async function main() {
  const tasks = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf8'));
  log(`=== COLLECTOR | ${tasks.length} tasks ===`);
  
  let collected = 0;
  for (const t of tasks) {
    const f = path.join(RAW_DIR, `${t.id}.txt`);
    if (fs.existsSync(f)) {
      const c = fs.readFileSync(f, 'utf8');
      if (c.length > 50 && !c.startsWith('FAILED:')) collected++;
    }
  }
  log(`Done: ${collected}/${tasks.length}, Remaining: ${tasks.length - collected}`);
  
  const browser = await chromium.connectOverCDP(CDP_URL);
  const ctx = browser.contexts()[0] || await browser.newContext();
  const page = await ctx.newPage();
  
  let [ok, fail, skip] = [0, 0, 0];
  
  for (let i = 0; i < tasks.length; i++) {
    try {
      const r = await collectOne(page, tasks[i], i, tasks.length);
      if (r === 'ok') ok++;
      else if (r === 'fail') fail++;
      else skip++;
    } catch (err) {
      log(`  ERR ${tasks[i].id}: ${err.message.split('\n')[0]}`);
      fail++;
    }
    if (i < tasks.length - 1) await sleep(2000);
  }
  
  log(`=== DONE: ${ok} new, ${fail} failed, ${skip} skipped ===`);
  await page.close();
}

main().catch(e => { log(`Fatal: ${e.message}`); process.exit(1); });
