/**
 * record_demo.mjs
 *
 * Playwright demo recorder for the GPU Scheduling Workbench.
 * Records a video at 1280x720 while walking through Design -> Run -> Analyze.
 */
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const SCREENSHOT_DIR = '/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures/demo';
const VIDEO_DIR     = '/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures/demo';
const BASE_URL      = 'http://127.0.0.1:8000/workbench';

let _screenshotIdx = 0;

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function shot(page, label) {
  const idx  = String(_screenshotIdx++).padStart(2, '0');
  const name = `${idx}_${label}`;
  const fp   = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: fp, fullPage: false });
  console.log(`  [screenshot] ${name}.png`);
  return fp;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────
async function main() {
  console.log('Launching Playwright (non-headless, 1280x720, video recording)...');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 80,                    // slight slow-mo so actions are visible in video
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir:  VIDEO_DIR,
      size: { width: 1280, height: 720 },
    },
  });

  const page = await context.newPage();

  try {
    // ═══════════════════════════════════════════════════════════════════════
    // Load workbench
    // ═══════════════════════════════════════════════════════════════════════
    console.log('\n=== Loading workbench ===');
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(1500);
    await shot(page, 'workbench_loaded');

    // ═══════════════════════════════════════════════════════════════════════
    // SCENE 1 – Design Tab
    // ═══════════════════════════════════════════════════════════════════════
    console.log('\n=== SCENE 1: Design Tab ===');

    // Make sure Design tab is visible/active
    await page.locator('.nav-tab[data-tab="design"]').click();
    await sleep(600);
    await shot(page, 'design_tab_initial');

    // ── 1a. Open "New Experiment Group" dialog ─────────────────────────────
    console.log('  Clicking "+ New" button...');
    await page.locator('#btn-new-group').click();
    await sleep(800);
    await shot(page, 'new_group_dialog');

    // ── 1b. Fill group name ────────────────────────────────────────────────
    console.log('  Filling group name...');
    const nameInput = page.locator('#new-group-name');
    await nameInput.fill('Demo: FGD vs Random');
    await sleep(400);
    await shot(page, 'group_name_filled');

    // ── 1c. Select Gavel simulator ─────────────────────────────────────────
    const simSelect = page.locator('#new-group-simulator');
    const simCount  = await simSelect.count();
    if (simCount > 0) {
      console.log('  Selecting Gavel simulator...');
      await simSelect.selectOption('Gavel');
      await sleep(300);
    }

    // ── 1d. Confirm creation ────────────────────────────────────────────────
    console.log('  Clicking Create button...');
    // The Create button is the primary button in the modal footer
    await page.locator('.modal-footer .btn-primary').click();
    await sleep(1500);
    await shot(page, 'group_created');

    // ── 1e. Configure the experiment form ─────────────────────────────────
    // After creation the design main panel should show the schema form.
    console.log('  Configuring experiment -- cluster preset...');

    // Cluster preset: select "Philly 108"
    const clusterSelect = page.locator('#field-cluster_preset');
    await clusterSelect.waitFor({ state: 'visible', timeout: 10000 });
    await clusterSelect.selectOption('Philly 108');
    await sleep(600);
    await shot(page, 'cluster_preset_selected');

    // Policy: select "max_min_fairness_perf" (Gavel default)
    console.log('  Setting policy to max_min_fairness_perf...');
    const policySelect = page.locator('#field-policy');
    if (await policySelect.count() > 0) {
      await policySelect.selectOption('max_min_fairness_perf');
      await sleep(400);
    }
    await shot(page, 'policy_selected');

    // num_total_jobs: set to 20 for a quick demo
    console.log('  Setting num_total_jobs = 20...');
    const jobsInput = page.locator('#field-num_total_jobs');
    if (await jobsInput.count() > 0) {
      await jobsInput.fill('20');
      await sleep(300);
    }

    // Enable FGD: toggle the enable_fgd checkbox
    console.log('  Enabling FGD...');
    const fgdCheckbox = page.locator('#field-enable_fgd');
    if (await fgdCheckbox.count() > 0) {
      const isChecked = await fgdCheckbox.isChecked();
      if (!isChecked) {
        await fgdCheckbox.click();
        await sleep(300);
      }
    }

    await shot(page, 'fgd_enabled');

    // fgd_placement_mode: look for it and set to "random" (to demo comparison)
    // First check if the field is visible (it might appear after enabling FGD)
    await sleep(500);
    const fgdModeSelect = page.locator('#field-fgd_placement_mode');
    if (await fgdModeSelect.count() > 0 && await fgdModeSelect.isVisible()) {
      console.log('  Setting FGD placement mode...');
      // Try to select 'random' or first available
      const options = await fgdModeSelect.locator('option').allInnerTexts();
      console.log('  FGD placement options:', options.join(', '));
      if (options.some(o => o.toLowerCase().includes('fgd'))) {
        await fgdModeSelect.selectOption({ label: /fgd/i });
      } else {
        await fgdModeSelect.selectOption({ index: 0 });
      }
      await sleep(300);
    }

    await shot(page, 'experiment_form_configured');

    // ── 1f. Check "Experiments Preview" to show the generated experiments ──
    console.log('  Scrolling to preview section...');
    const previewSection = page.locator('.experiment-preview, .preview-section, .generated-experiments').first();
    if (await previewSection.count() > 0) {
      await previewSection.scrollIntoViewIfNeeded();
      await sleep(400);
    } else {
      // Scroll to bottom of form
      await page.keyboard.press('End');
      await sleep(400);
    }
    await shot(page, 'experiments_preview');

    // ═══════════════════════════════════════════════════════════════════════
    // SCENE 2 – Click "Save & Go to Run"
    // ═══════════════════════════════════════════════════════════════════════
    console.log('\n=== Saving and going to Run Tab ===');

    // Scroll back up to find the Save & Go to Run button
    await page.keyboard.press('Home');
    await sleep(300);

    const saveRunBtn = page.locator('button:has-text("Save & Go to Run")');
    if (await saveRunBtn.count() > 0) {
      console.log('  Clicking "Save & Go to Run"...');
      await saveRunBtn.click();
      await sleep(1500);
    } else {
      // Fallback: manually click the Run tab
      console.log('  Save & Go to Run not found. Clicking Run tab directly...');
      await page.locator('.nav-tab[data-tab="run"]').click();
      await sleep(1000);
    }

    await shot(page, 'run_tab_initial');

    // ── Run tab: look for the group in sidebar and select it ──────────────
    // The run sidebar should already have the group selected if Save & Go to Run worked.
    // If not, find it in the list.
    const runGroupItems = page.locator('#run-group-list .group-item, #run-group-list .group-row');
    const groupCount = await runGroupItems.count();
    console.log(`  Found ${groupCount} group(s) in run sidebar`);
    if (groupCount > 0) {
      await runGroupItems.first().click();
      await sleep(800);
    }

    await shot(page, 'run_tab_group_selected');

    // ── 2a. Click "Run All" ────────────────────────────────────────────────
    console.log('  Clicking "Run All"...');
    const runAllBtn = page.locator('button:has-text("Run All")');
    if (await runAllBtn.count() > 0) {
      await runAllBtn.click();
      await sleep(2000);
      await shot(page, 'run_started');
    } else {
      console.log('  "Run All" not found. Taking inspection screenshot.');
      await shot(page, 'run_tab_inspect');

      // Log all visible buttons
      const btns = await page.locator('button').allInnerTexts();
      console.log('  Visible buttons:', btns.join(' | '));
    }

    // ── 2b. Capture live metrics ─────────────────────────────────────────
    console.log('\n  Capturing live metrics for up to 2 minutes...');
    const startTime = Date.now();
    const maxWait   = 120_000; // 2 min

    while (Date.now() - startTime < maxWait) {
      await sleep(5000);
      const elapsed = Math.round((Date.now() - startTime) / 1000);

      // Heuristic: check for "running" vs "complete" state indicators
      // The workbench uses .status-running, .status-complete, progress elements
      const runningCount   = await page.locator('.status-running, .exp-status-running, [data-status="running"]').count();
      const completedCount = await page.locator('.status-complete, .exp-status-complete, [data-status="complete"], [data-status="completed"]').count();
      console.log(`  t=${elapsed}s running=${runningCount} completed=${completedCount}`);

      await shot(page, `live_t${elapsed}s`);

      if (completedCount > 0 && runningCount === 0) {
        console.log('  All experiments completed!');
        break;
      }
    }

    await shot(page, 'run_completed_final');

    // ── 2c. Look for Export button ────────────────────────────────────────
    const exportBtn = page.locator('button:has-text("Export"), button:has-text("Export & Analyze")');
    if (await exportBtn.count() > 0) {
      console.log('  Clicking Export...');
      await exportBtn.first().click();
      await sleep(3000);
      await shot(page, 'export_done');
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SCENE 3 – Analyze Tab
    // ═══════════════════════════════════════════════════════════════════════
    console.log('\n=== SCENE 3: Analyze Tab ===');
    await page.locator('.nav-tab[data-tab="analyze"]').click();
    await sleep(2000);
    await shot(page, 'analyze_tab');

    // Wait for iframe / viz tool to load
    await sleep(4000);
    await shot(page, 'analyze_viz_loaded');

    console.log('\nAll scenes complete.');

  } catch (err) {
    console.error('\nError during recording:', err);
    try { await shot(page, 'ERROR'); } catch (_) { /* ignore */ }
  } finally {
    // Close page first -- this triggers video flush
    await page.close();
    await context.close();

    // The video file is named by Playwright with a random UUID in VIDEO_DIR
    console.log(`\nVideo saved to directory: ${VIDEO_DIR}`);
    console.log('Look for the newest .webm file in that directory.');

    await browser.close();
  }
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
