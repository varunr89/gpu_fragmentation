# Paper Additions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add four sections to the IEEE paper: JCT comparison figure, literature genealogy illustration, wall time analysis (appendix), and viz tool showcase (appendix).

**Architecture:** Each task produces a figure PNG + LaTeX text. Tasks 1/3 use Python scripts reading experiment JSON files. Task 2 uses the paper-banana skill. Task 4 uses the browser agent for screenshots.

**Tech Stack:** Python (pandas, matplotlib, json, glob), PaperBanana/Nano-Banana-Pro (via paper-banana skill), Playwright (via browser agent), LaTeX/tectonic.

---

### Task 1: JCT Comparison Figure (Cluster H vs Alibaba Split)

**Files:**
- Create: `scripts/plot_jct_comparison.py`
- Modify: `main.tex:248-267` (Analysis section, after "Role of Node Topology" subsection)
- Output: `figures/fig_jct_comparison.png`

**Step 1: Write the plotting script**

```python
"""JCT comparison: Cluster H vs Alibaba Split across 4 placement strategies."""
import json
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path

GAVEL_ROOT = Path("/Users/varunr/projects/courses/stanford/cs244c/gavel")
OUT_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures")

plt.rcParams.update({
    'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 9,
    'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 7,
    'figure.dpi': 300, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.05,
})

COLORS = {
    'strided': '#8B4513',   # Brown
    'random': '#3498DB',    # Blue
    'bestfit': '#E67E22',   # Orange
    'fgd': '#2C3E50',       # Dark
}
LABELS = {
    'strided': 'Strided (default)',
    'random': 'Random',
    'bestfit': 'BestFit',
    'fgd': 'FGD',
}


def load_results(results_dir):
    """Load all experiment JSONs from a directory into a list of dicts."""
    rows = []
    for fp in sorted(glob.glob(str(results_dir / "exp_*.json"))):
        with open(fp) as f:
            data = json.load(f)
            if isinstance(data, list):
                rows.extend(data)
            else:
                rows.append(data)
    return rows


def aggregate(rows, policy_filter=None):
    """Group by (placement, lam) and compute mean/std of avg_jct (in hours)."""
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        if policy_filter and r['policy'] != policy_filter:
            continue
        if r.get('saturated', False):
            continue
        key = (r['fgd_placement_mode'], r['lam'])
        groups[key].append(r['avg_jct'] / 3600.0)  # sec -> hours

    result = {}
    for (placement, lam), jcts in groups.items():
        if placement not in result:
            result[placement] = {'lam': [], 'mean': [], 'std': []}
        result[placement]['lam'].append(lam)
        result[placement]['mean'].append(np.mean(jcts))
        result[placement]['std'].append(np.std(jcts) if len(jcts) > 1 else 0)

    # Sort by lam
    for placement in result:
        order = np.argsort(result[placement]['lam'])
        for k in ['lam', 'mean', 'std']:
            result[placement][k] = np.array(result[placement][k])[order]
    return result


def main():
    cluster_h_dir = GAVEL_ROOT / "experiments/combined/results/fgd_replication_cluster_h"
    alibaba_dir = GAVEL_ROOT / "experiments/combined/results/fgd_replication"

    cluster_h_rows = load_results(cluster_h_dir)
    alibaba_rows = load_results(alibaba_dir)

    cluster_h_agg = aggregate(cluster_h_rows, policy_filter='max_min_fairness')
    alibaba_agg = aggregate(alibaba_rows, policy_filter='max_min_fairness')

    fig = plt.figure(figsize=(5, 5))
    gs = GridSpec(2, 1, height_ratios=[1, 1], hspace=0.35)

    panels = [
        (gs[0, 0], cluster_h_agg, '(a) Cluster H (Mixed Node Sizes)'),
        (gs[1, 0], alibaba_agg, '(b) Alibaba Split (Uniform 8-GPU Nodes)'),
    ]

    for gs_pos, agg, label in panels:
        ax = fig.add_subplot(gs_pos)
        for placement in ['strided', 'random', 'bestfit', 'fgd']:
            if placement not in agg:
                continue
            d = agg[placement]
            ax.errorbar(d['lam'], d['mean'], yerr=d['std'],
                       fmt='-o', color=COLORS[placement], markersize=3,
                       linewidth=1.2, capsize=2, label=LABELS[placement])
        ax.set_ylabel('Avg JCT (hrs)')
        ax.set_xlabel(label, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
        ax.legend(loc='upper left', fontsize=6)

    fig.savefig(OUT_DIR / "fig_jct_comparison.png")
    plt.close()
    print(f"Saved {OUT_DIR / 'fig_jct_comparison.png'}")


if __name__ == '__main__':
    main()
```

**Step 2: Run the script and verify output**

Run: `python3 scripts/plot_jct_comparison.py`
Expected: Saves `figures/fig_jct_comparison.png`

**Step 3: Add figure and text to main.tex**

Insert after the "Role of Node Topology" subsection text (around line 267), before "Policy Independence":

```latex
\subsection{JCT Impact of Placement Strategy}
Fig.~\ref{fig:jct_comparison} compares average job completion time across four placement strategies on both cluster topologies under Max-Min Fairness allocation.
On Cluster H (Fig.~\ref{fig:jct_comparison}a), FGD placement reduces JCT at moderate load by consolidating jobs onto fewer nodes, freeing capacity for incoming jobs.
BestFit achieves partial improvement, while Random and Strided perform similarly.
On Alibaba Split (Fig.~\ref{fig:jct_comparison}b), all four strategies produce equivalent JCT across the entire load range, confirming that uniform node topology eliminates the placement advantage.

\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{fig_jct_comparison.png}
  \caption{Average JCT vs. arrival rate under Max-Min Fairness allocation. (a)~Cluster H: FGD placement reduces JCT vs. Random/Strided at moderate load. (b)~Alibaba Split: all placements converge. Mean $\pm$ std over 3 seeds.}
  \label{fig:jct_comparison}
\end{figure}
```

**Step 4: Compile and verify**

Run: `tectonic main.tex`
Expected: Compiles without errors, new figure appears in Analysis section.

**Step 5: Commit**

```bash
git add scripts/plot_jct_comparison.py figures/fig_jct_comparison.png main.tex
git commit -m "Add JCT comparison figure: Cluster H vs Alibaba Split"
```

---

### Task 2: Literature Genealogy Illustration

**Files:**
- Output: `figures/fig_literature_genealogy.png`
- Modify: `main.tex:114-117` (Other Related Work subsection)
- Modify: `main.tex:307-314` (bibliography)

**Step 1: Generate illustration with paper-banana skill**

Invoke `paper-banana:paper-banana` skill with this prompt:

> Generate an academic illustration showing the research lineage of GPU cluster scheduling papers. Layout as a timeline/tree flowing left to right (2018-2026).
>
> Nodes (paper name, venue, year):
> - Optimus (EuroSys 2018) -- root, dynamic resource scheduling
> - Gandiva (OSDI 2018) -- time-slicing and migration
> - Tiresias (NSDI 2019) -- 2D-LAS priority scheduling
> - Gavel (OSDI 2020) -- heterogeneity-aware allocation [highlight in green]
> - Themis (NSDI 2020) -- fairness-aware scheduling
> - HiveD (OSDI 2020) -- GPU sharing with guarantees
> - Pollux (OSDI 2021) -- co-adaptive scheduling
> - Salus (MLSys 2020) -- fine-grained GPU sharing
> - FGD (ATC 2023) -- fragmentation-aware placement [highlight in blue]
> - Sia (SOSP 2023) -- heterogeneity + goodput
> - Our Work (2026) -- Gavel + FGD integration [highlight in red]
>
> Color-code branches by aspect:
> - Green: heterogeneity-awareness (Gavel, Sia)
> - Blue: fragmentation/sharing (FGD, Salus, HiveD)
> - Orange: fairness/priority (Tiresias, Themis)
> - Gray: general scheduling (Optimus, Gandiva, Pollux)
>
> Arrows show "builds on" relationships. Style: clean academic diagram, white background, no decorative elements, suitable for IEEE single-column width.

Save output to `figures/fig_literature_genealogy.png`.

**Step 2: Expand Related Work text and add figure**

Replace the "Other Related Work" subsection (lines 114-117) with expanded text:

```latex
\subsection{Research Landscape}
Fig.~\ref{fig:literature} shows the evolution of GPU cluster scheduling research.
Optimus \cite{OPTIMUS} pioneered dynamic resource allocation for DL training, establishing the foundation for subsequent work.
Research then branched along several axes.

\textit{Fairness and priority:} Tiresias \cite{TIRESIAS} introduced two-dimensional Least Attained Service scheduling without requiring job duration estimates.
Themis \cite{THEMIS} formalized finish-time fairness as an allocation objective.

\textit{Heterogeneity awareness:} Gavel \cite{GAVEL} unified diverse scheduling policies through an effective throughput abstraction that accounts for job-GPU affinity.
Sia \cite{SIA} extended this with goodput-optimized scheduling across heterogeneous clusters.

\textit{GPU sharing and fragmentation:} Salus \cite{SALUS} and HiveD \cite{HIVED} enabled fine-grained GPU sharing.
FGD \cite{FGD} addressed the fragmentation problem created by partial GPU allocation through gradient-based placement.

Our work bridges the heterogeneity and fragmentation branches by integrating Gavel's allocation with FGD's placement.
This figure was generated using PaperBanana \cite{PAPERBANANA}.

\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{fig_literature_genealogy.png}
  \caption{Research lineage of GPU scheduling systems. Green: heterogeneity-aware. Blue: fragmentation/sharing-aware. Orange: fairness/priority. Our work integrates Gavel's allocation with FGD's placement.}
  \label{fig:literature}
\end{figure}
```

**Step 3: Add new bibliography entries**

Add to `\begin{thebibliography}` block:

```latex
\bibitem{OPTIMUS} Peng, Y., Bao, Y., Chen, Y., et al. ``Optimus: An Efficient Dynamic Resource Scheduler for Deep Learning Clusters.'' EuroSys 2018.
\bibitem{THEMIS} Mahajan, K., Balasubramanian, A., Singhvi, A., et al. ``Themis: Fair and Efficient GPU Cluster Scheduling.'' NSDI 2020. \href{https://www.usenix.org/conference/nsdi20/presentation/mahajan}{Usenix Web Link}.
\bibitem{HIVED} Zhao, H., Han, Z., Yang, Z., et al. ``HiveD: Sharing a GPU Cluster for Deep Learning with Guarantees.'' OSDI 2020.
\bibitem{POLLUX} Qiao, A., Agrawal, S.K., Gujarati, A., et al. ``Pollux: Co-adaptive Cluster Scheduling for Goodput-Optimized Deep Learning.'' OSDI 2021.
\bibitem{SIA} Jayaram Subramanya, S., Arfeen, D., Lin, S., et al. ``Sia: Heterogeneity-aware, Goodput-optimized ML-Cluster Scheduling.'' SOSP 2023.
\bibitem{PAPERBANANA} Zhu, D., et al. ``PaperBanana: Automating Academic Illustration for AI Scientists.'' 2025. \href{https://paperbanana.org/}{Web Link}.
```

**Step 4: Compile and verify**

Run: `tectonic main.tex`
Expected: Compiles, genealogy figure appears in Related Work section.

**Step 5: Commit**

```bash
git add figures/fig_literature_genealogy.png main.tex
git commit -m "Add literature genealogy illustration and expanded related work"
```

---

### Task 3: Wall Time Analysis (Appendix)

**Files:**
- Create: `scripts/plot_wall_time.py`
- Modify: `main.tex:316-324` (appendix section)
- Output: `figures/fig_wall_time.png`

**Step 1: Write the wall time plotting script**

```python
"""Wall time vs arrival rate for each experiment set."""
import json
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path
from collections import defaultdict

GAVEL_ROOT = Path("/Users/varunr/projects/courses/stanford/cs244c/gavel")
OUT_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures")

plt.rcParams.update({
    'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 9,
    'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 7,
    'figure.dpi': 300, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.05,
})


def load_json_results(results_dir):
    """Load all exp_*.json files."""
    rows = []
    for fp in sorted(glob.glob(str(results_dir / "exp_*.json"))):
        with open(fp) as f:
            data = json.load(f)
            if isinstance(data, list):
                rows.extend(data)
            else:
                rows.append(data)
    return rows


def agg_wall_time(rows, rate_key='lam', wall_key='wall_time_seconds', group_key=None):
    """Aggregate wall time by arrival rate, optionally grouped by another key."""
    groups = defaultdict(lambda: defaultdict(list))
    for r in rows:
        rate = r[rate_key]
        grp = r.get(group_key, 'all') if group_key else 'all'
        groups[grp][rate].append(r[wall_key])

    result = {}
    for grp, rate_dict in groups.items():
        rates = sorted(rate_dict.keys())
        means = [np.mean(rate_dict[r]) for r in rates]
        stds = [np.std(rate_dict[r]) if len(rate_dict[r]) > 1 else 0 for r in rates]
        result[grp] = {'rate': np.array(rates), 'mean': np.array(means), 'std': np.array(stds)}
    return result


def main():
    # (a) Gavel replication
    gavel_csv = pd.read_csv(
        GAVEL_ROOT / "experiments/combined/results/gavel_replication_combined.csv")
    gavel_csv['wall_hrs'] = gavel_csv['wall_time_sec'] / 3600.0

    # (b) Combined Cluster H
    cluster_h_rows = load_json_results(
        GAVEL_ROOT / "experiments/combined/results/fgd_replication_cluster_h")

    # (c) Combined Alibaba Split
    alibaba_rows = load_json_results(
        GAVEL_ROOT / "experiments/combined/results/fgd_replication")

    fig = plt.figure(figsize=(5, 7.5))
    gs = GridSpec(3, 1, height_ratios=[1, 1, 1], hspace=0.35)

    # Panel (a): Gavel replication - by policy
    ax_a = fig.add_subplot(gs[0, 0])
    policy_colors = {'max_min_fairness': '#E74C3C', 'max_min_fairness_perf': '#27AE60',
                     'finish_time_fairness': '#3498DB', 'finish_time_fairness_perf': '#9B59B6'}
    policy_labels = {'max_min_fairness': 'Baseline', 'max_min_fairness_perf': 'Gavel',
                     'finish_time_fairness': 'FTF Baseline', 'finish_time_fairness_perf': 'FTF Gavel'}
    for policy in ['max_min_fairness', 'max_min_fairness_perf',
                    'finish_time_fairness', 'finish_time_fairness_perf']:
        sub = gavel_csv[gavel_csv['policy'] == policy]
        stats = sub.groupby('jobs_per_hr')['wall_hrs'].agg(['mean', 'std']).reset_index()
        stats['std'] = stats['std'].fillna(0)
        stats = stats.sort_values('jobs_per_hr')
        ax_a.errorbar(stats['jobs_per_hr'], stats['mean'], yerr=stats['std'],
                     fmt='-o', color=policy_colors[policy], markersize=3,
                     linewidth=1.2, capsize=2, label=policy_labels[policy])
    ax_a.set_ylabel('Wall Time (hrs)')
    ax_a.set_yscale('log')
    ax_a.set_xlabel('(a) Gavel Replication (Philly, 108 GPUs)', fontweight='bold')
    ax_a.grid(True, alpha=0.3)
    ax_a.legend(loc='upper left', fontsize=6)

    # Panel (b): Cluster H - by placement
    ax_b = fig.add_subplot(gs[1, 0])
    cluster_h_agg = agg_wall_time(cluster_h_rows, group_key='fgd_placement_mode')
    placement_colors = {'strided': '#8B4513', 'random': '#3498DB',
                        'bestfit': '#E67E22', 'fgd': '#2C3E50'}
    placement_labels = {'strided': 'Strided', 'random': 'Random',
                        'bestfit': 'BestFit', 'fgd': 'FGD'}
    for p in ['strided', 'random', 'bestfit', 'fgd']:
        if p not in cluster_h_agg:
            continue
        d = cluster_h_agg[p]
        wall_min = d['mean'] / 60.0  # sec -> min
        std_min = d['std'] / 60.0
        ax_b.errorbar(d['rate'], wall_min, yerr=std_min,
                     fmt='-o', color=placement_colors[p], markersize=3,
                     linewidth=1.2, capsize=2, label=placement_labels[p])
    ax_b.set_ylabel('Wall Time (min)')
    ax_b.set_xlabel('(b) Combined Cluster H (5,592 GPUs)', fontweight='bold')
    ax_b.grid(True, alpha=0.3)
    ax_b.legend(loc='upper left', fontsize=6)

    # Panel (c): Alibaba Split - by placement
    ax_c = fig.add_subplot(gs[2, 0])
    alibaba_agg = agg_wall_time(alibaba_rows, group_key='fgd_placement_mode')
    for p in ['strided', 'random', 'bestfit', 'fgd']:
        if p not in alibaba_agg:
            continue
        d = alibaba_agg[p]
        wall_min = d['mean'] / 60.0
        std_min = d['std'] / 60.0
        ax_c.errorbar(d['rate'], wall_min, yerr=std_min,
                     fmt='-o', color=placement_colors[p], markersize=3,
                     linewidth=1.2, capsize=2, label=placement_labels[p])
    ax_c.set_ylabel('Wall Time (min)')
    ax_c.set_xlabel('(c) Combined Alibaba Split (6,212 GPUs)', fontweight='bold')
    ax_c.grid(True, alpha=0.3)
    ax_c.legend(loc='upper left', fontsize=6)

    fig.savefig(OUT_DIR / "fig_wall_time.png")
    plt.close()
    print(f"Saved {OUT_DIR / 'fig_wall_time.png'}")


if __name__ == '__main__':
    main()
```

**Step 2: Run script and verify**

Run: `python3 scripts/plot_wall_time.py`
Expected: Saves `figures/fig_wall_time.png`

**Step 3: Add to appendix in main.tex**

After the existing topology figure in the appendix, add:

```latex
\section{Compute Cost}

Fig.~\ref{fig:wall_time} shows wall-clock time per experiment across all three evaluation sets.
Gavel replication on the 108-GPU Philly cluster (Fig.~\ref{fig:wall_time}a) exhibits exponential wall time growth near saturation, with runs at high arrival rates hitting the 24-hour SLURM limit.
Combined experiments on Cluster H (Fig.~\ref{fig:wall_time}b) complete in 1--6 minutes regardless of load, since the single-GPU-type cluster avoids expensive LP solves.
Alibaba Split experiments (Fig.~\ref{fig:wall_time}c) take 4--75 minutes, scaling with load due to the 12-type heterogeneous LP.
Total compute across all ~850 experiments was approximately [TODO: compute sum] GPU-hours on Stanford FarmShare.

\begin{figure}[h]
  \centering
  \includegraphics[width=\columnwidth]{fig_wall_time.png}
  \caption{Wall-clock time vs. arrival rate for each experiment set. (a)~Gavel replication shows exponential blowup near saturation (log scale). (b)~Cluster H runs complete in minutes. (c)~Alibaba Split scales with LP complexity. Mean $\pm$ std over 3 seeds.}
  \label{fig:wall_time}
\end{figure}
```

**Step 4: Compile and verify**

Run: `tectonic main.tex`

**Step 5: Commit**

```bash
git add scripts/plot_wall_time.py figures/fig_wall_time.png main.tex
git commit -m "Add wall time vs load analysis to appendix"
```

---

### Task 4: Viz Tool Screenshots (Appendix)

**Files:**
- Output: `figures/fig_viz_*.png` (multiple screenshots)
- Modify: `main.tex` (appendix section)

**Step 1: Take screenshots via browser agent**

Launch browser agent to navigate to the viz tool. The tool is hosted via Azure Blob at an index.html (or can be served locally from `/Users/varunr/projects/courses/stanford/cs244c/gpu-scheduling-viz/`).

Screenshots needed:
1. **Heatmap view** (`fig_viz_heatmap.png`) -- GPU allocation grid showing jobs color-coded across nodes
2. **Time-series charts** (`fig_viz_timeseries.png`) -- Occupancy, JCT, fragmentation metrics over time
3. **Side-by-side comparison** (`fig_viz_comparison.png`) -- Two experiments loaded simultaneously (FGD vs Random)
4. **Results dashboard** (`fig_viz_results.png`) -- Aggregate curves with paper reference overlay
5. **Fragmentation panel** (`fig_viz_fragmentation.png`) -- Close-up of frag rate, frag/total, unalloc metrics

For each screenshot: load a Cluster H experiment at ~25 jph with FGD placement for visual contrast. For comparison view, load Random placement alongside.

**Step 2: Add viz tool appendix section to main.tex**

After the wall time section in the appendix:

```latex
\section{GPU Scheduling Visualization Tool}

To support interactive analysis of scheduling behavior across our 843 experiments, we developed a web-based visualization tool (Fig.~\ref{fig:viz_heatmap}--\ref{fig:viz_results}).
The tool loads experiment data from a custom binary format (\texttt{.viz.bin}) hosted on Azure Blob Storage, decoding in a Web Worker to maintain UI responsiveness at Alibaba cluster scale (6,200 GPUs).

Key features include:
\begin{itemize}
\item \textbf{Heatmap view} (Fig.~\ref{fig:viz_heatmap}): Per-GPU allocation state across scheduling rounds, with drill-down inspection of individual GPU assignments.
\item \textbf{Time-series charts} (Fig.~\ref{fig:viz_timeseries}): Six synchronized panels showing occupancy, JCT, queue length, JCT CDF, fragmentation metrics, and pending GPU demand.
\item \textbf{Side-by-side comparison} (Fig.~\ref{fig:viz_comparison}): Two experiments loaded simultaneously with synchronized playback for direct A/B comparison of placement strategies.
\item \textbf{Results dashboard} (Fig.~\ref{fig:viz_results}): Aggregate curves across all experiments with paper reference overlays, supporting click-to-drill-down into individual runs.
\end{itemize}

The tool was instrumental in debugging saturation behavior, validating replication accuracy against paper reference curves, and visually confirming that FGD consolidates jobs onto fewer nodes compared to Random placement.

\begin{figure}[h]
  \centering
  \includegraphics[width=\columnwidth]{fig_viz_heatmap.png}
  \caption{Viz tool: heatmap view showing per-GPU allocation state across scheduling rounds.}
  \label{fig:viz_heatmap}
\end{figure}

\begin{figure}[h]
  \centering
  \includegraphics[width=\columnwidth]{fig_viz_timeseries.png}
  \caption{Viz tool: time-series charts (occupancy, JCT, fragmentation).}
  \label{fig:viz_timeseries}
\end{figure}

\begin{figure}[h]
  \centering
  \includegraphics[width=\columnwidth]{fig_viz_comparison.png}
  \caption{Viz tool: side-by-side comparison of FGD vs Random placement.}
  \label{fig:viz_comparison}
\end{figure}

\begin{figure}[h]
  \centering
  \includegraphics[width=\columnwidth]{fig_viz_results.png}
  \caption{Viz tool: aggregate results dashboard with paper reference overlay.}
  \label{fig:viz_results}
\end{figure}
```

**Step 3: Compile and verify**

Run: `tectonic main.tex`

**Step 4: Commit**

```bash
git add figures/fig_viz_*.png main.tex
git commit -m "Add viz tool showcase to appendix with screenshots"
```

---

### Task 5: Final Compilation and Push

**Step 1: Full recompile**

Run: `tectonic main.tex`
Verify: No errors, all new figures appear in correct locations.

**Step 2: Push to GitHub**

```bash
git push
```

This triggers Overleaf sync for collaborative review.
