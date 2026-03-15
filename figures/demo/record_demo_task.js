'use strict';

/**
 * record_demo_task.js
 *
 * Records three demo segments of the GPU Scheduling Workbench:
 *   Segment 1: Design Tab
 *   Segment 2: Run Tab (first 30 seconds of live execution)
 *   Segment 3: Analyze Tab
 *
 * Run: node record_demo_task.js
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const DEMO_DIR = '/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures/demo';
const BASE_URL = 'http://127.0.0.1:8000/workbench';

let _shotIdx = 0;

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
  // Find any .webm not yet renamed to a segment_*.webm
  const files = fs.readdirSync(DEMO_DIR).filter(f =>
    (f.endsWith('.webm') || f.endsWith('.mp4')) && !f.startsWith('segment_')
  );
  if (files.length === 0) {
    console.log('  No new video found to rename');
    return null;
  }
  // Sort by mtime descending, take newest
  const sorted = files.sort((a, b) => {
    return fs.statSync(path.join(DEMO_DIR, b)).mtimeMs - fs.statSync(path.join(DEMO_DIR, a)).mtimeMs;
  });
  const src = path.join(DEMO_DIR, sorted[0]);
  const dst = path.join(DEMO_DIR, `segment_${suffix}.webm`);
  fs.renameSync(src, dst);
  console.log(`  Video saved: ${dst}`);
  return dst;
}

// ─────────────────────────────────────────────────────────────────────────────

async function segment1Design(browser) {
  console.log('\n=== SEGMENT 1: Design Tab ===');

  const ctx = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    recordVideo: { dir: DEMO_DIR, size: { width: 1400, height: 900 } },
  });
  const page = await ctx.newPage();

  try {
    // 1. Navigate to workbench
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(1500);
    await shot(page, 'design_01_initial');

    // 2. Click the Design tab (should already be active)
    const designTab = page.locator('.nav-tab[data-tab="design"]');
    await designTab.click();
    await sleep(800);
    await shot(page, 'design_02_design_tab');

    // 3. The group "Baseline vs Gavel vs Gavel+FGD" was pre-created via API.
    //    Find it in the sidebar and click it.
    console.log('  Looking for experiment group in sidebar...');
    await page.waitForSelector('#design-group-list', { timeout: 10000 });
    await sleep(1000);
    await shot(page, 'design_03_sidebar_loaded');

    // Click the group by name
    const groupItem = page.locator('#design-group-list .group-item, #design-group-list .group-row, #design-group-list li, #design-group-list .group-name').filter({ hasText: 'Baseline vs Gavel vs Gavel+FGD' }).first();
    const groupVisible = await groupItem.isVisible().catch(() => false);
    if (groupVisible) {
      console.log('  Clicking group item...');
      await groupItem.click();
      await sleep(2000);
      await shot(page, 'design_04_group_selected');
    } else {
      // Maybe the group-item contains the name in a child element
      const allItems = await page.locator('#design-group-list *').allInnerTexts();
      console.log('  Sidebar items:', allItems.slice(0, 10).join(' | '));

      // Try clicking any group list item
      const anyItem = page.locator('#design-group-list .group-item, #design-group-list li').first();
      if (await anyItem.isVisible().catch(() => false)) {
        await anyItem.click();
        await sleep(2000);
        await shot(page, 'design_04_group_clicked');
      } else {
        await shot(page, 'design_04_no_group_found');
      }
    }

    // 4. Screenshot of the "+ New" button area
    await shot(page, 'design_05_new_button_visible');

    // 5. Click "+ New" to show the dialog for demo purposes
    const newBtn = page.locator('#btn-new-group');
    await newBtn.waitFor({ state: 'visible', timeout: 10000 });
    await newBtn.click();
    await sleep(800);
    await shot(page, 'design_06_new_group_dialog');

    // 6. Fill in the group name
    const nameInput = page.locator('#new-group-name');
    await nameInput.waitFor({ state: 'visible', timeout: 5000 });
    await nameInput.fill('Baseline vs Gavel vs Gavel+FGD');
    await sleep(400);
    await shot(page, 'design_07_group_name_filled');

    // 7. Select Gavel simulator if present
    const simSelect = page.locator('#new-group-simulator');
    if (await simSelect.isVisible().catch(() => false)) {
      await simSelect.selectOption('Gavel');
      await sleep(300);
      await shot(page, 'design_08_simulator_selected');
    }

    // 8. Click Create
    const createBtn = page.locator('.modal-footer .btn-primary, .modal-footer button[type="submit"], .modal-footer .btn:has-text("Create")').first();
    if (await createBtn.isVisible().catch(() => false)) {
      await createBtn.click();
      await sleep(2000);
      await shot(page, 'design_09_group_created');
    } else {
      // Close the modal
      const closeBtn = page.locator('.modal-close, .modal-overlay').first();
      await closeBtn.click().catch(() => {});
      await sleep(500);
    }

    // 9. Now navigate to the pre-created group to show its config
    //    Scroll the sidebar to find it
    await sleep(1000);
    const targetGroup = page.locator('#design-group-list').locator('text=Baseline vs Gavel vs Gavel+FGD').first();
    if (await targetGroup.isVisible().catch(() => false)) {
      await targetGroup.click();
      await sleep(2000);
      await shot(page, 'design_10_target_group_selected');
    } else {
      // Try to find the group by scrolling
      const allGroups = await page.locator('#design-group-list').allInnerTexts();
      console.log('  All sidebar content:', allGroups);
      await shot(page, 'design_10_sidebar_state');
    }

    // 10. Show cluster preset field
    const clusterField = page.locator('#field-cluster_preset');
    if (await clusterField.isVisible().catch(() => false)) {
      await shot(page, 'design_11_cluster_field');
      // Scroll to show more of the form
      await page.evaluate(() => {
        const form = document.querySelector('.schema-form, .main-panel');
        if (form) form.scrollTop = 200;
      });
      await sleep(500);
      await shot(page, 'design_12_form_scrolled');
    } else {
      await shot(page, 'design_11_form_not_found');
    }

    // Final screenshot
    await shot(page, 'design_13_final');

  } catch (err) {
    console.error('  Error in segment 1:', err.message);
    await shot(page, 'design_ERROR').catch(() => {});
  }

  await page.close();
  await ctx.close();
  return await renameLatestVideo('1_design');
}

// ─────────────────────────────────────────────────────────────────────────────

async function segment2Run(browser) {
  console.log('\n=== SEGMENT 2: Run Tab ===');

  const ctx = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    recordVideo: { dir: DEMO_DIR, size: { width: 1400, height: 900 } },
  });
  const page = await ctx.newPage();

  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(1500);

    // Switch to Run tab
    const runTab = page.locator('.nav-tab[data-tab="run"]');
    await runTab.click();
    await sleep(1500);
    await shot(page, 'run_01_run_tab');

    // Find and click the "Baseline vs Gavel vs Gavel+FGD" group
    await page.waitForSelector('#run-group-list', { timeout: 10000 });
    const targetGroup = page.locator('#run-group-list').locator('text=Baseline vs Gavel vs Gavel+FGD').first();
    if (await targetGroup.isVisible().catch(() => false)) {
      await targetGroup.click();
      await sleep(1500);
      await shot(page, 'run_02_group_selected');
    } else {
      // Try first available group
      const firstGroup = page.locator('#run-group-list .group-item, #run-group-list li').first();
      if (await firstGroup.isVisible().catch(() => false)) {
        await firstGroup.click();
        await sleep(1500);
        await shot(page, 'run_02_first_group_selected');
      } else {
        await shot(page, 'run_02_no_groups');
      }
    }

    // Take screenshot showing experiment list
    await shot(page, 'run_03_experiment_list');

    // Find "Run All" button
    const runAllBtn = page.locator('button:has-text("Run All"), button:has-text("Run")').first();
    if (await runAllBtn.isVisible().catch(() => false)) {
      console.log('  Clicking Run All...');
      await runAllBtn.click();
      await sleep(2000);
      await shot(page, 'run_04_started');

      // Capture 5 seconds in
      await sleep(5000);
      await shot(page, 'run_05_live_5s');

      // Capture 10 more seconds in
      await sleep(10000);
      await shot(page, 'run_06_live_15s');

      // Capture 10 more seconds
      await sleep(10000);
      await shot(page, 'run_07_live_25s');

    } else {
      console.log('  Run button not found');
      const allBtns = await page.locator('button').allInnerTexts();
      console.log('  Available buttons:', allBtns.join(' | '));
      await shot(page, 'run_04_no_run_button');
    }

    await shot(page, 'run_08_final');

  } catch (err) {
    console.error('  Error in segment 2:', err.message);
    await shot(page, 'run_ERROR').catch(() => {});
  }

  await page.close();
  await ctx.close();
  return await renameLatestVideo('2_run');
}

// ─────────────────────────────────────────────────────────────────────────────

async function segment3Analyze(browser) {
  console.log('\n=== SEGMENT 3: Analyze Tab ===');

  const ctx = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    recordVideo: { dir: DEMO_DIR, size: { width: 1400, height: 900 } },
  });
  const page = await ctx.newPage();

  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(1500);

    // Switch to Analyze tab
    const analyzeTab = page.locator('.nav-tab[data-tab="analyze"]');
    await analyzeTab.click();
    await sleep(3000);
    await shot(page, 'analyze_01_analyze_tab');

    // Take full page screenshot
    const fullPath = path.join(DEMO_DIR, 'analyze_02_full.png');
    await page.screenshot({ path: fullPath, fullPage: true });
    console.log(`  [shot] analyze_02_full.png`);
    _shotIdx++; // bump index so next auto-name doesn't collide

    // Wait for iframe to load
    await sleep(3000);
    await shot(page, 'analyze_03_viz_loaded');

    // Try to interact with the iframe
    const iframe = page.frameLocator('#viz-iframe');
    const iframeEl = page.locator('#viz-iframe');
    if (await iframeEl.isVisible().catch(() => false)) {
      console.log('  Iframe found');
      await sleep(2000);
      await shot(page, 'analyze_04_iframe_content');
    }

    await shot(page, 'analyze_05_final');

  } catch (err) {
    console.error('  Error in segment 3:', err.message);
    await shot(page, 'analyze_ERROR').catch(() => {});
  }

  await page.close();
  await ctx.close();
  return await renameLatestVideo('3_analyze');
}

// ─────────────────────────────────────────────────────────────────────────────

async function main() {
  console.log('Starting GPU Scheduling Workbench demo recording...');
  console.log(`Output directory: ${DEMO_DIR}`);

  const browser = await chromium.launch({
    headless: false,
    slowMo: 60,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });

  const videos = [];
  const errors = [];

  try {
    const v1 = await segment1Design(browser).catch(err => {
      errors.push(`Segment 1: ${err.message}`);
      return null;
    });
    if (v1) videos.push(v1);

    const v2 = await segment2Run(browser).catch(err => {
      errors.push(`Segment 2: ${err.message}`);
      return null;
    });
    if (v2) videos.push(v2);

    const v3 = await segment3Analyze(browser).catch(err => {
      errors.push(`Segment 3: ${err.message}`);
      return null;
    });
    if (v3) videos.push(v3);

  } finally {
    await browser.close();
  }

  // Summary
  console.log('\n=== RECORDING COMPLETE ===');

  const allPngs = fs.readdirSync(DEMO_DIR)
    .filter(f => f.endsWith('.png'))
    .sort()
    .map(f => path.join(DEMO_DIR, f));

  console.log('\nScreenshots:');
  allPngs.forEach(f => console.log(' ', f));

  console.log('\nVideos:');
  videos.forEach(v => console.log(' ', v));

  if (errors.length > 0) {
    console.log('\nErrors:');
    errors.forEach(e => console.log(' ', e));
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
