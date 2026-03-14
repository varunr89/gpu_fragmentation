# Conference Talk Slides Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 10-slide Beamer presentation for a 10-minute CS244C class talk on the Gavel+FGD paper.

**Architecture:** Single LaTeX Beamer file (`talk.tex`) in the `gpu_fragmentation/` directory, reusing all existing figures from `figures/`. Compiled with `tectonic`. Speaker notes embedded as `\note{}` commands. Dark blue theme with clean typography.

**Tech Stack:** LaTeX Beamer, tectonic compiler, existing PNG figures

---

## File Structure

| File | Purpose |
|------|---------|
| Create: `talk.tex` | Main Beamer presentation (10 slides + backup slides) |
| Existing: `figures/*.png` | All figures reused from paper |

## Chunk 1: Build the Slide Deck

### Task 1: Create Beamer skeleton with preamble and slides 1-5

**Files:**
- Create: `talk.tex`

- [ ] **Step 1: Create `talk.tex` with Beamer preamble and theme**

```latex
\documentclass[aspectratio=169]{beamer}
\usetheme{Madrid}
\usecolortheme{whale}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tikz}
\graphicspath{{figures/}}

% Clean up navigation symbols
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}[frame number]

% Title info
\title{Pack Smart, Schedule Fair}
\subtitle{Unifying Heterogeneity and Fragmentation Awareness\\in GPU Scheduling}
\author{Varun Ramesh \and Jiayu Chang \and Hyeonggyu Kim \and Stefan Gabriel Ene}
\institute{Stanford University -- CS244C}
\date{Winter 2026}
```

Then add slides 1-5:

**Slide 1 (Problem):** Title + stat callout "21-42% of free GPU capacity unusable" + simplified fragmentation diagram using the topology figure.

**Slide 2 (Two Systems):** Two-column layout. Left: `fig2_gavel_algorithm.png` with "Gavel: which GPU type?" Right: `fig3_fgd_algorithm.png` with "FGD: which node?" Center gap text.

**Slide 3 (Architecture):** `fig1_architecture.png` centered with two-stage callouts.

**Slide 4 (Eval Setup):** Table I from paper recreated in Beamer + "900 experiments" callout.

**Slide 5 (Replication):** Two-column. Left: `fig_gavel_replication.png`. Right: `fig_fgd_replication.png`. Key stats below each.

- [ ] **Step 2: Compile and verify slides 1-5**

Run: `/opt/homebrew/bin/tectonic talk.tex`
Expected: Compiles without error, produces `talk.pdf` with 5 slides.

- [ ] **Step 3: Visually verify the PDF**

Check: Read talk.pdf pages 1-5. Verify figures render, text is readable, layout is clean.

---

### Task 2: Add slides 6-10 (results, limitations, takeaway)

**Files:**
- Modify: `talk.tex`

- [ ] **Step 1: Add slides 6-10**

**Slide 6 (FGD works on mixed nodes):** `fig_jct_comparison.png` panel (a) only, or full figure with panel (a) highlighted. Annotation: "30-40% fragmentation reduction."

**Slide 7 (The twist):** Two-column. Left: Cluster H panel (spread). Right: Alibaba Split panel (converged). Plus `fig2_topology.png` below or inset showing *why*. Bold text: "Fragmentation depends on node topology diversity, not GPU type heterogeneity."

**Slide 8 (Impact):** `fig_utilization_impact.png`. Callout box: "280 recoverable GPUs. 17% more completed jobs."

**Slide 9 (Limitations + Viz):** Top: 3 bullet limitations. Bottom: `fig_viz_timeseries.png` (placeholder for where screen recording will go, with note "Demo clip here").

**Slide 10 (Takeaway):** Large centered text: thesis statement. Three bullet implications. Repo URLs.

- [ ] **Step 2: Compile and verify slides 6-10**

Run: `/opt/homebrew/bin/tectonic talk.tex`
Expected: Compiles without error, 10 slides total.

- [ ] **Step 3: Visually verify the full PDF**

Check: Read talk.pdf pages 1-10. Verify the slide 6->7 transition reads as setup->payoff. Check all figures render at readable size.

---

### Task 3: Add backup slides and speaker notes

**Files:**
- Modify: `talk.tex`

- [ ] **Step 1: Add backup slides after `\appendix`**

5 backup slides:
1. Arrival order sensitivity table (Table II from paper)
2. GavelFGD+ POA results (`gavelfgd_combined_absolute.png`)
3. Wall time analysis (`fig_wall_time.png`)
4. Per-utilization Cluster H (`fig7_combined_cluster_h.png`)
5. Per-utilization Alibaba Split (`fig8_combined_uniform.png`)

- [ ] **Step 2: Add `\note{}` speaker notes to each main slide**

Use the talking points from the design doc. Each note should have:
- 3-4 bullet talking points
- The transition sentence to the next slide

- [ ] **Step 3: Compile final version**

Run: `/opt/homebrew/bin/tectonic talk.tex`
Expected: Compiles without error. 10 main slides + 5 backup slides.

- [ ] **Step 4: Visually verify the complete PDF**

Check: Read full talk.pdf. Verify backup slides are clearly marked. Verify speaker notes compile (visible in notes mode).

- [ ] **Step 5: Commit**

```bash
git add talk.tex docs/2026-03-13-conference-talk-design.md docs/plans/2026-03-14-conference-talk-slides.md
git commit -m "Add conference talk slide deck (Beamer, 10 slides + backup)"
```
