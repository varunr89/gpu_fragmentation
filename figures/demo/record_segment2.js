'use strict';

/**
 * record_segment2.js - Re-record Segment 2 (Run Tab) with better Run All targeting.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const DEMO_DIR = '/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures/demo';
const BASE_URL = 'http://127.0.0.1:8000/workbench';

// Start screenshot index at 13 to match existing naming
let _shotIdx = 13;

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function shot(page, label) {
  const idx = String(_shotIdx++).padStart(2, '0');
  const name = `${idx}_${label}`;
  const fp = path.join(DEMO_DIR, `${name}.png`);
  await page.screenshot({ path: fp, fullPage: false });
  console.log(`  [shot] ${name}.png`);
  return fp;
}

async function renameLatestVideo(suffix) {
  const files = fs.readdirSync(DEMO_DIR).filter(f =>
    (f.endsWith('.webm') || f.endsWith('.mp4')) && !f.startsWith('segment_')
  );
  if (files.length === 0) {
    console.log('  No new video found to rename');
    return null;
  }
  const sorted = files.sort((a, b) =>
    fs.statSync(path.join(DEMO_DIR, b)).mtimeMs - fs.statSync(path.join(DEMO_DIR, a)).mtimeMs
  );
  const src = path.join(DEMO_DIR, sorted[0]);
  const dst = path.join(DEMO_DIR, `segment_${suffix}.webm`);
  // Remove existing if present
  if (fs.existsSync(dst)) fs.unlinkSync(dst);
  fs.renameSync(src, dst);
  console.log(`  Video saved: ${dst}`);
  return dst;
}

async function main() {
  // First ensure we have the target experiment group via API
  const https = require('http');

  function httpGet(url) {
    return new Promise((resolve, reject) => {
      const req = https.get(url, res => {
        let data = '';
        res.on('data', d => data += d);
        res.on('end', () => resolve(JSON.parse(data)));
      });
      req.on('error', reject);
    });
  }

  // Find the group ID
  const groups = await httpGet('http://127.0.0.1:8000/api/experiments');
  const targetGroup = groups.find(g => g.name === 'Baseline vs Gavel vs Gavel+FGD' && g.status === 'draft');
  if (!targetGroup) {
    console.error('Could not find target group!');
    console.log('Available groups:', groups.map(g => g.name + ' | ' + g.status));
    process.exit(1);
  }
  console.log('Target group:', targetGroup.id, targetGroup.name);

  const browser = await chromium.launch({
    headless: false,
    slowMo: 80,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });

  const ctx = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    recordVideo: { dir: DEMO_DIR, size: { width: 1400, height: 900 } },
  });
  const page = await ctx.newPage();

  try {
    // Navigate to workbench
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(1500);

    // Click the Run tab using the nav-tab class
    const runTab = page.locator('.nav-tab[data-tab="run"]');
    await runTab.waitFor({ state: 'visible', timeout: 10000 });
    await runTab.click();
    await sleep(1500);
    await shot(page, 'run_01_run_tab');

    // Find the target group in the run sidebar
    await page.waitForSelector('#run-group-list', { timeout: 10000 });
    await sleep(1000);

    // List all sidebar items
    const sidebarItems = await page.locator('#run-group-list .group-item').allInnerTexts();
    console.log('Sidebar items:', sidebarItems.slice(0, 5).join(' | '));

    // Try to click by text
    const targetGroupEl = page.locator('#run-group-list .group-item').filter({ hasText: 'Baseline vs Gavel vs Gavel+FGD' }).first();
    if (await targetGroupEl.isVisible().catch(() => false)) {
      await targetGroupEl.click();
      console.log('  Clicked target group by text');
    } else {
      // Try clicking the last item (most recently created)
      const allItems = page.locator('#run-group-list .group-item');
      const count = await allItems.count();
      console.log(`  Found ${count} group items`);
      if (count > 0) {
        await allItems.last().click();
        console.log('  Clicked last group item');
      }
    }
    await sleep(1500);
    await shot(page, 'run_02_group_selected');

    // Scroll to see Run All button
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(500);

    // Screenshot showing experiment list
    await shot(page, 'run_03_experiment_list');

    // Find Run All button specifically - it has class btn-success and text "Run All"
    const runAllBtn = page.locator('.run-controls .btn-success, button.btn-success:has-text("Run All"), .run-controls button:has-text("Run All")').first();
    const runAllVisible = await runAllBtn.isVisible().catch(() => false);
    console.log('  Run All button visible:', runAllVisible);

    if (!runAllVisible) {
      // Debug: list all buttons and their text/classes
      const allBtns = await page.locator('button').all();
      console.log('  All buttons on page:');
      for (const btn of allBtns) {
        const text = await btn.innerText().catch(() => '?');
        const cls = await btn.getAttribute('class').catch(() => '?');
        console.log(`    "${text}" class="${cls}"`);
      }
      await shot(page, 'run_DEBUG_buttons');
    } else {
      // Take screenshot before clicking
      await shot(page, 'run_04_before_run');

      console.log('  Clicking Run All...');
      await runAllBtn.click();
      await sleep(2000);
      await shot(page, 'run_05_started');

      // Wait and capture live metrics
      await sleep(5000);
      await shot(page, 'run_06_live_5s');

      await sleep(10000);
      await shot(page, 'run_07_live_15s');

      await sleep(10000);
      await shot(page, 'run_08_live_25s');

      await shot(page, 'run_09_final');
    }

  } catch (err) {
    console.error('Error in segment 2:', err.message);
    await shot(page, 'run_ERROR').catch(() => {});
  }

  await page.close();
  await ctx.close();

  const video = await renameLatestVideo('2_run');
  await browser.close();

  console.log('\nDone. Video:', video);
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
