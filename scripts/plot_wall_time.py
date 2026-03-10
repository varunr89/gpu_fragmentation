"""Generate wall-time vs arrival-rate figure with three vertically stacked panels."""
import pandas as pd
import numpy as np
import json
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

GAVEL_ROOT = Path("/Users/varunr/projects/courses/stanford/cs244c/gavel")
OUT_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures")

plt.rcParams.update({
    'font.size': 9,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'figure.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
})

# --- Panel (a): Gavel Replication (Philly, 108 GPUs) ---

GAVEL_POLICY_COLORS = {
    'max_min_fairness': '#E74C3C',
    'max_min_fairness_perf': '#27AE60',
    'finish_time_fairness': '#3498DB',
    'finish_time_fairness_perf': '#9B59B6',
}
GAVEL_POLICY_LABELS = {
    'max_min_fairness': 'Baseline',
    'max_min_fairness_perf': 'Gavel',
    'finish_time_fairness': 'FTF Baseline',
    'finish_time_fairness_perf': 'FTF Gavel',
}

# --- Panels (b)/(c): FGD placement mode colors ---

FGD_COLORS = {
    'strided': '#8B4513',
    'random': '#3498DB',
    'bestfit': '#E67E22',
    'fgd': '#2C3E50',
}
FGD_LABELS = {
    'strided': 'Strided',
    'random': 'Random',
    'bestfit': 'BestFit',
    'fgd': 'FGD',
}


def load_fgd_jsons(result_dir):
    """Load all exp_*.json from a directory and return a DataFrame."""
    rows = []
    for fp in glob.glob(str(result_dir / "exp_*.json")):
        with open(fp) as f:
            data = json.load(f)
        d = data[0]
        # Determine effective placement mode from name
        parts = d['name'].split('_')
        # Names like: ch_fifo_strided_5jph_s0 or fgd_strided_5jph_s0
        # Find placement keyword
        if d['enable_fgd'] is False:
            mode = 'strided'
        else:
            mode = d['fgd_placement_mode']
        rows.append({
            'mode': mode,
            'lam': d['lam'],
            'jph': 3600.0 / d['lam'],
            'wall_time_seconds': d['wall_time_seconds'],
        })
    return pd.DataFrame(rows)


def main():
    fig, axes = plt.subplots(3, 1, figsize=(5, 7.5))
    fig.subplots_adjust(hspace=0.35)

    # ---- Panel (a): Gavel Replication ----
    ax_a = axes[0]
    csv_path = GAVEL_ROOT / "experiments/combined/results/gavel_replication_combined.csv"
    df_gavel = pd.read_csv(csv_path)
    df_gavel['wall_time_hrs'] = df_gavel['wall_time_sec'] / 3600.0

    for policy in ['max_min_fairness', 'max_min_fairness_perf',
                    'finish_time_fairness', 'finish_time_fairness_perf']:
        sub = df_gavel[df_gavel['policy'] == policy].copy()
        if sub.empty:
            continue
        stats = sub.groupby('jobs_per_hr')['wall_time_hrs'].agg(['mean', 'std']).reset_index()
        stats['std'] = stats['std'].fillna(0)
        stats = stats.sort_values('jobs_per_hr')

        ax_a.errorbar(stats['jobs_per_hr'], stats['mean'],
                      yerr=stats['std'], fmt='-o',
                      color=GAVEL_POLICY_COLORS[policy],
                      markersize=3, linewidth=1.2, capsize=2,
                      label=GAVEL_POLICY_LABELS[policy])

    ax_a.set_yscale('log')
    ax_a.set_ylabel('Wall Time (hours)')
    ax_a.legend(loc='upper left', fontsize=6, framealpha=0.9)
    ax_a.grid(True, alpha=0.3)
    ax_a.set_xlabel('Job Arrival Rate (jobs/hr)\n(a) Gavel Replication (Philly, 108 GPUs)', fontweight='bold')

    # ---- Panel (b): Cluster H ----
    ax_b = axes[1]
    df_ch = load_fgd_jsons(GAVEL_ROOT / "experiments/combined/results/fgd_replication_cluster_h")
    df_ch['wall_time_min'] = df_ch['wall_time_seconds'] / 60.0

    for mode in ['strided', 'random', 'bestfit', 'fgd']:
        sub = df_ch[df_ch['mode'] == mode].copy()
        if sub.empty:
            continue
        stats = sub.groupby('jph')['wall_time_min'].agg(['mean', 'std']).reset_index()
        stats['std'] = stats['std'].fillna(0)
        stats = stats.sort_values('jph')

        ax_b.errorbar(stats['jph'], stats['mean'],
                      yerr=stats['std'], fmt='-o',
                      color=FGD_COLORS[mode],
                      markersize=3, linewidth=1.2, capsize=2,
                      label=FGD_LABELS[mode])

    ax_b.set_ylabel('Wall Time (minutes)')
    ax_b.legend(loc='upper left', fontsize=6, framealpha=0.9)
    ax_b.grid(True, alpha=0.3)
    ax_b.set_xlabel('Job Arrival Rate (jobs/hr)\n(b) Combined Cluster H (5,592 GPUs)', fontweight='bold')

    # ---- Panel (c): Alibaba Split ----
    ax_c = axes[2]
    df_ali = load_fgd_jsons(GAVEL_ROOT / "experiments/combined/results/fgd_replication")
    df_ali['wall_time_min'] = df_ali['wall_time_seconds'] / 60.0

    for mode in ['strided', 'random', 'bestfit', 'fgd']:
        sub = df_ali[df_ali['mode'] == mode].copy()
        if sub.empty:
            continue
        stats = sub.groupby('jph')['wall_time_min'].agg(['mean', 'std']).reset_index()
        stats['std'] = stats['std'].fillna(0)
        stats = stats.sort_values('jph')

        ax_c.errorbar(stats['jph'], stats['mean'],
                      yerr=stats['std'], fmt='-o',
                      color=FGD_COLORS[mode],
                      markersize=3, linewidth=1.2, capsize=2,
                      label=FGD_LABELS[mode])

    ax_c.set_ylabel('Wall Time (minutes)')
    ax_c.legend(loc='upper left', fontsize=6, framealpha=0.9)
    ax_c.grid(True, alpha=0.3)
    ax_c.set_xlabel('Job Arrival Rate (jobs/hr)\n(c) Combined Alibaba Split (6,212 GPUs)', fontweight='bold')

    # Save
    out_path = OUT_DIR / "fig_wall_time.png"
    fig.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


if __name__ == '__main__':
    main()
