# Paper Additions Design: Analysis, Literature, and Appendix

**Date:** 2026-03-09
**Status:** Draft

## Overview

Four additions to the IEEE paper:

1. **JCT comparison figure** -- Cluster H vs Alibaba Split across all 4 placement strategies
2. **Literature genealogy illustration** -- Research lineage from Optimus to FGD, generated with canvas-design skill
3. **Wall time analysis** (appendix) -- Compute cost across all experiment types
4. **Viz tool showcase** (appendix) -- Screenshots of all features via browser agent

---

## 1. JCT Improvement: Cluster H vs Alibaba Split

### Data Sources

- **Cluster H:** `experiments/combined/results/fgd_replication_cluster_h/` (360 JSONs)
  - 2 policies (fifo, max_min_fairness) x 4 placements x 15 rates x 3 seeds
  - Cluster: 5,592 GPUs, single type, mixed nodes (1/2/4/8 GPUs)
- **Alibaba Split:** `experiments/combined/results/fgd_replication/` (180 JSONs)
  - 1 policy (max_min_fairness) x 4 placements x 15 rates x 3 seeds
  - Cluster: 6,212 GPUs, 12 heterogeneous sub-types, uniform 8-GPU nodes

### Figure Design

Single figure with 2 subfigures side-by-side (or stacked for single-column):

- **(a) Cluster H (Mixed Nodes):** JCT vs arrival rate, 4 lines (Strided, Random, BestFit, FGD), MMF policy, mean +/- std across 3 seeds
- **(b) Alibaba Split (Uniform Nodes):** Same layout, 4 lines

Key visual: FGD line separates from others on Cluster H but converges on Alibaba Split.

### Fields from JSON

```python
{
    "avg_jct": float,           # seconds
    "wall_time_seconds": float,
    "lam": float,               # arrival rate (jobs/hr)
    "fgd_placement_mode": str,  # strided/random/bestfit/fgd
    "policy": str,              # fifo/max_min_fairness
    "seed": int,
    "saturated": bool,
    "avg_frag_rate": float,     # optional: overlay fragmentation
}
```

### Placement in Paper

In "Combined Gavel+FGD Results" section, after the existing combined figures (fig7, fig8). New figure number ~8 or 9.

### Text

2-3 paragraphs analyzing:
- FGD reduces JCT on Cluster H by X% at moderate load vs Strided baseline
- On Alibaba Split (uniform 8-GPU nodes), all placements converge
- This confirms the central finding: fragmentation-aware placement matters only with mixed node topologies

---

## 2. Literature Genealogy Illustration

### Content

Research lineage tree showing how GPU scheduling papers evolved:

**Root:** Optimus (EuroSys 2018) -- pioneered dynamic DL resource scheduling

**Branches by aspect:**
- **Heterogeneity:** Gavel (OSDI 2020), Sia (SOSP 2023)
- **Fairness/Priority:** Tiresias (NSDI 2019), Themis (NSDI 2020)
- **Sharing/Consolidation:** Gandiva (OSDI 2018), HiveD (OSDI 2020), Salus (MLSys 2020)
- **Fragmentation:** FGD (ATC 2023)
- **Co-adaptive:** Pollux (OSDI 2021)
- **Our work:** Gavel + FGD integration (2026)

Each node: paper name, venue, year. Color-coded by aspect. Arrows show "builds on" relationships.

### Generation Method

Use the `paper-banana:paper-banana` skill (already configured with Gemini API key and Gemini 3 Pro model) to generate the illustration. The skill invokes PaperBanana's multi-agent pipeline (Retriever, Planner, Stylist, Visualizer, Critic) via the Nano-Banana-Pro model.

Input prompt will describe: timeline/tree layout, paper nodes with venue+year, color-coded branches by aspect (heterogeneity, fragmentation, fairness, sharing), arrow relationships showing "builds on" lineage from Optimus through to our work.

Add PaperBanana as a reference in the bibliography:
> Zhu, D. et al. "PaperBanana: Automating Academic Illustration for AI Scientists." 2025.

### Placement in Paper

Replace/expand the existing "Other Related Work" subsection (currently 3 sentences on Salus/Gandiva/Tiresias). Add the genealogy figure and expand to ~0.5 page of text organizing papers by methodological lineage rather than paper-by-paper.

---

## 3. Wall Time Analysis (Appendix)

### Data Sources

| Experiment Set | Source | Count | Wall Time Range |
|---|---|---|---|
| Gavel replication | `gavel_replication_combined.csv` | 312 | 60s -- 86,400s |
| FGD standalone | `fgd-standalone/results/full_run/` | ~15 | 28s -- 312s |
| Combined Cluster H | `results/fgd_replication_cluster_h/` | 360 | 60s -- 335s |
| Combined Alibaba | `results/fgd_replication/` | 180 | 245s -- 4,536s |

### Figure Design

One figure with multiple subfigures, each showing wall time vs arrival rate for a specific experiment set:

- **(a) Gavel Replication (Philly):** wall_time_sec vs jobs_per_hr, grouped by policy (baseline, gavel, ftf). Shows exponential blowup near saturation and 24hr SLURM cap.
- **(b) Combined Cluster H:** wall_time_seconds vs lam, 4 placement strategies. Relatively flat (~60-335s).
- **(c) Combined Alibaba Split:** wall_time_seconds vs lam, 4 placement strategies. Shows 10x increase with load (~245-4536s) due to LP solver scaling.

Each panel: line plot with mean +/- std across seeds, log-scale y-axis for Gavel replication.

### Text

Brief paragraphs noting:
- Total compute hours across all ~850 experiments
- Saturation runs dominate cost (Gavel at high load hits 24hr SLURM cap)
- Alibaba-scale experiments 10-50x slower than Cluster H due to LP solve time at scale
- Cost implications for future researchers replicating these systems

---

## 4. Viz Tool Showcase (Appendix)

### Screenshots Needed (via browser agent)

1. **Heatmap view** -- GPU allocation grid with color-coded jobs
2. **Time-series charts** -- Occupancy, JCT, fragmentation metrics
3. **Side-by-side comparison** -- Two experiments loaded simultaneously
4. **Results dashboard** -- Aggregate curves with paper reference overlay
5. **Fragmentation metrics panel** -- Close-up of frag rate, frag/total, unalloc

### Data to Load

Use a Cluster H experiment with FGD placement at moderate load (~25 jph) for the best visual contrast. For comparison view, load same config with Random placement.

### Text

~0.5 page describing:
- Purpose: interactive exploration of scheduling behavior across 843 experiments
- Key features: heatmap, time-series, comparison, results dashboard
- How it helped: visually confirmed fragmentation patterns, debugged saturation, validated replication accuracy
- Technical: custom binary format, Azure Blob hosting, Web Worker decoding

---

## Implementation Order

1. **JCT comparison** (script + figure + text) -- most impactful, uses existing data
2. **Viz tool screenshots** (browser agent) -- independent, can run in parallel
3. **Wall time analysis** (script + figure + text) -- straightforward data aggregation
4. **Literature genealogy** (illustration + expanded text) -- creative, needs careful layout
