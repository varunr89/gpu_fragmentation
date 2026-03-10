"""Compact utilization impact figure: 1x2 (Cluster H only).

Alibaba panels removed since they just show convergence (same as Fig 8b).
"""
import json
import glob
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

CLUSTER_H_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gavel"
                      "/experiments/combined/results/fgd_replication_cluster_h")
OUT_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures")

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


def main():
    ch_records = load_results(CLUSTER_H_DIR)

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(5, 2.2))
    fig.subplots_adjust(wspace=0.35)

    # Left: Cluster utilization
    ch_util = aggregate(ch_records, 'utilization')
    for placement in PLACEMENT_ORDER:
        if placement not in ch_util:
            continue
        jphs, means, stds = ch_util[placement]
        ax_l.errorbar(jphs, means, yerr=stds,
                      fmt=f'-{MARKERS[placement]}',
                      color=COLORS[placement],
                      markersize=3, linewidth=1.2, capsize=2,
                      label=LABELS[placement])
    ax_l.set_ylabel('Cluster Utilization (%)')
    ax_l.set_ylim(bottom=0)
    ax_l.grid(True, alpha=0.3)
    ax_l.legend(loc='lower right', fontsize=6, framealpha=0.9)
    ax_l.set_xlabel('Job Arrival Rate (jobs/hr)\n(a) Cluster Utilization')

    # Right: Effective capacity
    ch_eff = aggregate(ch_records, 'effective_util')
    for placement in PLACEMENT_ORDER:
        if placement not in ch_eff:
            continue
        jphs, means, stds = ch_eff[placement]
        ax_r.errorbar(jphs, means, yerr=stds,
                      fmt=f'-{MARKERS[placement]}',
                      color=COLORS[placement],
                      markersize=3, linewidth=1.2, capsize=2,
                      label=LABELS[placement])
    ax_r.set_ylabel('Effective Capacity (%)')
    ax_r.set_ylim(bottom=0)
    ax_r.grid(True, alpha=0.3)
    ax_r.legend(loc='lower right', fontsize=6, framealpha=0.9)
    ax_r.set_xlabel('Job Arrival Rate (jobs/hr)\n(b) Effective Capacity')

    out_path = OUT_DIR / "fig_utilization_impact.png"
    fig.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


if __name__ == '__main__':
    main()
