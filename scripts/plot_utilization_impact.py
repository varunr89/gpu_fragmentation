"""Plot cluster utilization and effective capacity vs arrival rate for 4 placement strategies.

Key finding: Fragmentation-aware placement (BestFit/FGD) increases cluster utilization
by up to 6-8 percentage points and effective capacity by up to 13 points at high load.
At moderate load, all placements converge.
"""
import json
import glob
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CLUSTER_H_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gavel"
                      "/experiments/combined/results/fgd_replication_cluster_h")
ALIBABA_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gavel"
                    "/experiments/combined/results/fgd_replication")
OUT_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures")

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    'font.size': 9,
    'axes.titlesize': 10,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 7,
    'figure.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
})

COLORS = {
    'strided': '#8B4513',
    'random':  '#3498DB',
    'bestfit': '#E67E22',
    'fgd':     '#2C3E50',
}
LABELS = {
    'strided': 'Strided (default)',
    'random':  'Random',
    'bestfit': 'BestFit',
    'fgd':     'FGD',
}
MARKERS = {
    'strided': 's',
    'random':  '^',
    'bestfit': 'D',
    'fgd':     'o',
}
PLACEMENT_ORDER = ['strided', 'random', 'bestfit', 'fgd']


def load_results(result_dir: Path):
    """Load experiment JSON files and return list of dicts."""
    records = []
    for fpath in glob.glob(str(result_dir / "exp_*.json")):
        with open(fpath) as f:
            data = json.load(f)
        d = data[0]

        if d['policy'] != 'max_min_fairness':
            continue

        mode = d['fgd_placement_mode']
        fgd_on = d.get('enable_fgd', False)
        if mode == 'fgd' and not fgd_on:
            placement = 'strided'
        elif mode == 'fgd' and fgd_on:
            placement = 'fgd'
        elif mode == 'random':
            placement = 'random'
        elif mode == 'bestfit':
            placement = 'bestfit'
        else:
            continue

        jobs_per_hr = 3600.0 / d['lam']
        util = d.get('avg_utilization', 0)
        frag = d.get('avg_frag_rate', 0)
        records.append({
            'placement': placement,
            'jobs_per_hr': jobs_per_hr,
            'utilization': util,
            'frag_rate': frag,
            'effective_util': util - frag,
            'seed': d['seed'],
        })
    return records


def aggregate(records, metric='utilization'):
    """Group by (placement, jobs_per_hr), compute mean and std."""
    buckets = defaultdict(list)
    for r in records:
        buckets[(r['placement'], r['jobs_per_hr'])].append(r[metric])

    out = {}
    for placement in PLACEMENT_ORDER:
        jphs, means, stds = [], [], []
        for (p, jph), values in sorted(buckets.items(), key=lambda kv: kv[0][1]):
            if p != placement:
                continue
            jphs.append(jph)
            means.append(np.mean(values))
            stds.append(np.std(values))
        if jphs:
            out[placement] = (np.array(jphs), np.array(means), np.array(stds))
    return out


def plot_panel(ax, agg_data, ylabel, xlabel_text):
    """Plot one panel with 4 placement strategies."""
    for placement in PLACEMENT_ORDER:
        if placement not in agg_data:
            continue
        jphs, means, stds = agg_data[placement]
        ax.errorbar(
            jphs, means, yerr=stds,
            fmt=f'-{MARKERS[placement]}',
            color=COLORS[placement],
            markersize=3,
            linewidth=1.2,
            capsize=2,
            label=LABELS[placement],
        )
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=6, framealpha=0.9)
    ax.set_xlabel('Job Arrival Rate (jobs/hr)\n' + xlabel_text, fontweight='bold')


def main():
    ch_records = load_results(CLUSTER_H_DIR)
    ab_records = load_results(ALIBABA_DIR)

    # 2x2 grid: rows = metric (utilization, effective), cols = cluster
    fig, axes = plt.subplots(2, 2, figsize=(7, 5))
    fig.subplots_adjust(hspace=0.55, wspace=0.35)

    # Top row: Cluster utilization
    ch_util = aggregate(ch_records, 'utilization')
    ab_util = aggregate(ab_records, 'utilization')
    plot_panel(axes[0, 0], ch_util, 'Cluster Utilization (%)',
              '(a) Cluster H')
    plot_panel(axes[0, 1], ab_util, 'Cluster Utilization (%)',
              '(b) Alibaba Split')

    # Bottom row: Effective capacity (utilization minus fragmentation)
    ch_eff = aggregate(ch_records, 'effective_util')
    ab_eff = aggregate(ab_records, 'effective_util')
    plot_panel(axes[1, 0], ch_eff, 'Effective Capacity (%)',
              '(c) Cluster H')
    plot_panel(axes[1, 1], ab_eff, 'Effective Capacity (%)',
              '(d) Alibaba Split')

    out_path = OUT_DIR / "fig_utilization_impact.png"
    fig.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


if __name__ == '__main__':
    main()
