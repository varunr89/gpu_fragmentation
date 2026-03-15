# Demo Video Script: Experiment Workbench

**Target:** 30s final video (with speed-up). Record ~15 min raw, then cut/speed.
**Format:** Screen recording with voiceover
**Resolution:** 1920x1080, browser at 90% zoom

---

## Locked Config

3 experiments on **Demo 504** cluster (504 GPUs: 200 v100 + 180 p100 + 124 k80, mixed node sizes 1/2/4/8):

| | Exp 1: Baseline | Exp 2: Gavel | Exp 3: Gavel+FGD |
|--|----|----|-----|
| Policy | max_min_fairness | max_min_fairness_perf | max_min_fairness_perf |
| FGD | off | off | on (fgd mode) |
| Cluster | Demo 504 | same | same |
| Mode | steady_state | steady_state | steady_state |
| Window | 4000-5000 | same | same |
| Arrival | 7 jph (lam=514) | same | same |
| Multi-GPU | true | true | true |
| Workload | philly | philly | philly |
| Seed | 0 | 0 | 0 |

**Expected results (validated):**

| Experiment | Avg JCT | vs Baseline |
|-----------|---------|-------------|
| Baseline | ~82,000s | -- |
| Gavel | ~66,000s | **20% lower JCT** |
| Gavel+FGD | ~64,000s | **22.6% lower JCT** |

---

## Pre-Recording Setup

```bash
# Start the workbench server
cd /Users/varunr/projects/courses/stanford/cs244c/gpu-scheduling-viz
PYTHONPATH=/Users/varunr/projects/courses/stanford/cs244c/gavel \
  .venv/bin/uvicorn workbench.app:app --host 127.0.0.1 --port 8000

# Open browser to http://localhost:8000/workbench
# Set browser zoom to 90%
# Increase terminal/browser font size for readability
```

---

## Scene 1: Design Tab -- Configure 3 Experiments (8s in final)

**On screen:** Workbench Design tab

**Actions (record at 1x, speed to 2x in edit):**
1. Click "New Experiment Group"
2. Name: "Baseline vs Gavel vs Gavel+FGD"
3. Select Gavel simulator
4. Set common config:
   - Cluster preset: **Demo 504**
   - Mode: steady_state
   - Window: 4000-5000
   - Arrival rate (lam): 514
   - Multi-GPU jobs: true
   - Workload: philly
   - Seed: 0
5. Create 3 experiments:
   - "Baseline": policy=max_min_fairness, enable_fgd=false
   - "Gavel": policy=max_min_fairness_perf, enable_fgd=false
   - "Gavel+FGD": policy=max_min_fairness_perf, enable_fgd=true
6. Show experiment preview: "3 experiments configured"

**Voiceover:**
> "We design three experiments on a custom 504-GPU cluster with three GPU types and mixed node sizes -- 1 to 8 GPUs per node. The baseline uses type-agnostic allocation. Gavel adds heterogeneity awareness. Gavel+FGD adds fragmentation-aware placement."

---

## Scene 2: Run Tab -- Live Execution (12s in final)

**On screen:** Workbench Run tab with live metrics

**Actions:**
1. Click "Run"
2. Experiment 1 (Baseline) starts:
   - Show live GPU heatmap updating for 3-5 seconds at 1x
   - Utilization chart climbing
   - Fragmentation metrics appearing
3. Speed up through Baseline completion (4-8x)
4. Experiment 2 (Gavel) starts:
   - Brief 1x clip showing different allocation pattern
   - Note the lower JCT on the chart
5. Speed through to completion
6. Experiment 3 (Gavel+FGD) starts:
   - Brief 1x clip
7. Speed through to completion
8. All 3 complete -- green checkmarks

**Voiceover:**
> "The simulator streams live metrics as each experiment runs. We see GPU allocations updating on the heatmap, utilization climbing to steady state, and fragmentation tracked per round. The baseline completes with an average JCT of 82,000 seconds. Gavel's heterogeneity-aware allocation drops that by 20 percent. Adding FGD further reduces JCT to 64,000 seconds -- a 22 percent total improvement. All three experiments completed in about 15 minutes."

**Speed notes:**
- First 3-5s of Baseline at 1x (show live streaming)
- 8x through bulk of each experiment
- Brief 1x at each experiment's completion moment
- Total raw time: ~15 min, compressed to ~12s

---

## Scene 3: Analyze Tab -- View Results (10s in final)

**On screen:** Workbench Analyze tab / viz tool

**Actions (record at 1x):**
1. Click "Export" to convert results to .viz.bin
2. Switch to Analyze tab
3. Load Baseline vs Gavel+FGD for side-by-side comparison
4. Show Charts view:
   - Utilization: Gavel+FGD sustains higher effective utilization
   - Fragmentation: lower with FGD
   - JCT moving average: Gavel+FGD consistently lower
5. Briefly show Results tab with aggregate curves

**Voiceover:**
> "Completed experiments export to our interactive visualizer. Side-by-side, Gavel+FGD achieves higher utilization and lower fragmentation than the baseline. This custom cluster -- with both heterogeneous GPU types and mixed node sizes -- demonstrates that our implementation generalizes beyond the paper's original traces."

---

## Full Transcript (30s final cut)

| Time | Visual | Voiceover |
|------|--------|-----------|
| 0-8s | Design tab: Demo 504 preset, 3 experiments | "Three experiments on a custom 504-GPU cluster with mixed GPU types and node sizes: baseline, Gavel, and Gavel+FGD." |
| 8-20s | Run tab: live heatmap + charts, 3 experiments completing (sped up) | "Live metrics stream as experiments run. Gavel cuts JCT by 20% through smarter GPU allocation. FGD adds another 3% through fragmentation-aware placement -- 22% total improvement." |
| 20-30s | Analyze tab: side-by-side comparison | "The visualizer confirms: heterogeneity-aware allocation and fragmentation-aware placement each contribute independently, generalizing to novel cluster configurations." |

---

## Recording Tips

1. **Browser zoom:** 90% so full workbench UI fits
2. **Memory:** The frontend is now capped at 1000 chart points -- Chrome should stay under control
3. **Speed-up overlay:** Add a "4x" or "8x" indicator during fast-forward sections
4. **Timer overlay:** Show wall time in corner
5. **Two takes:** Record Design+Run in one take, Analyze separately. Splice in editing.
6. **Screen recording:** QuickTime (Cmd+Shift+5) or OBS

---

## Startup Commands

```bash
cd /Users/varunr/projects/courses/stanford/cs244c/gpu-scheduling-viz
PYTHONPATH=/Users/varunr/projects/courses/stanford/cs244c/gavel \
  .venv/bin/uvicorn workbench.app:app --host 127.0.0.1 --port 8000

open http://localhost:8000/workbench
```
