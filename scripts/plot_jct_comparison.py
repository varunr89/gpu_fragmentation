"""Plot fragmentation rate vs arrival rate for 4 placement strategies across two cluster topologies.

Key finding: JCT is invariant to placement strategy (Gavel's LP allocation is placement-agnostic),
but fragmentation rate differs significantly -- BestFit and FGD reduce fragmentation by ~50%
compared to Strided on mixed-node clusters.
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
# Style (matches existing scripts)
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

        # Filter: only max_min_fairness
        if d['policy'] != 'max_min_fairness':
            continue

        # Derive placement label
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

        # lam is mean inter-arrival time in seconds; convert to jobs/hr
        jobs_per_hr = 3600.0 / d['lam']
        records.append({
            'placement': placement,
            'jobs_per_hr': jobs_per_hr,
            'avg_frag_rate': d.get('avg_frag_rate', 0),
            'avg_jct_hrs': d['avg_jct'] / 3600.0,
            'seed': d['seed'],
        })
    return records


def aggregate(records, metric='avg_frag_rate'):
    """Group by (placement, jobs_per_hr), compute mean and std.

    Returns dict: placement -> (jphs_sorted, means, stds).
    """
    buckets = defaultdict(list)
    for r in records:
        buckets[(r['placement'], r['jobs_per_hr'])].append(r[metric])

    result = defaultdict(lambda: {'jph': [], 'mean': [], 'std': []})
    for (placement, jph), values in sorted(buckets.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        result[placement]['jph'].append(jph)
        result[placement]['mean'].append(np.mean(values))
        result[placement]['std'].append(np.std(values))

    out = {}
    for placement, data in result.items():
        order = np.argsort(data['jph'])
        out[placement] = (
            np.array(data['jph'])[order],
            np.array(data['mean'])[order],
            np.array(data['std'])[order],
        )
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

    ch_frag = aggregate(ch_records, 'avg_frag_rate')
    ab_frag = aggregate(ab_records, 'avg_frag_rate')

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(5, 5))
    fig.subplots_adjust(hspace=0.45)

    plot_panel(ax_top, ch_frag, 'Avg Fragmentation Rate (%)',
              '(a) Cluster H (Mixed Node Sizes)')
    plot_panel(ax_bot, ab_frag, 'Avg Fragmentation Rate (%)',
              '(b) Alibaba Split (Uniform 8-GPU Nodes)')

    out_path = OUT_DIR / "fig_jct_comparison.png"
    fig.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


if __name__ == '__main__':
    main()
