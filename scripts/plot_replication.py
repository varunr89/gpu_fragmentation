"""Generate unified replication figures for Gavel and FGD with RMSE subplots."""
import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path

GAVEL_ROOT = Path("/Users/varunr/projects/courses/stanford/cs244c/gavel")
OUT_DIR = Path("/Users/varunr/projects/courses/stanford/cs244c/gpu_fragmentation/figures")

# Shared style
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
    'baseline': '#E74C3C',
    'gavel': '#27AE60',
    'paper_baseline': '#E74C3C',
    'paper_gavel': '#27AE60',
    'Random': '#3498DB',
    'DotProd': '#9B59B6',
    'Clustering': '#2ECC71',
    'Packing': '#E67E22',
    'BestFit': '#F39C12',
    'FGD': '#2C3E50',
}


def plot_gavel():
    """Generate Gavel replication figure: 3 panels + RMSE subplots.

    Data sources:
        - CSV: experiments/combined/results/gavel_replication_combined.csv
          (per-seed raw data: policy, figure, jobs_per_hr, seed, jct_sec, saturated)
        - Paper ref: experiments/gavel-replication/scripts/paper_reference_curves.json
    """
    csv_path = GAVEL_ROOT / "experiments/combined/results/gavel_replication_combined.csv"
    ref_path = GAVEL_ROOT / "experiments/gavel-replication/scripts/paper_reference_curves.json"

    df = pd.read_csv(csv_path)
    df['jct_hours'] = pd.to_numeric(df['jct_sec'], errors='coerce') / 3600.0
    # Exclude saturated runs (partial JCT unreliable)
    mask_sat = df['saturated'].astype(str).str.lower().isin(['true', '1', 'yes'])
    df.loc[mask_sat, 'jct_hours'] = np.nan

    with open(ref_path) as f:
        ref = json.load(f)

    # Map CSV policy names -> role for colors/labels
    policy_map = {
        'max_min_fairness':      'baseline',
        'max_min_fairness_perf': 'gavel',
    }

    fig_configs = [
        ('fig9',  ['max_min_fairness', 'max_min_fairness_perf'],
         '(a) Single-GPU Jobs (Max-Min Fairness / LAS)'),
        ('fig10', ['max_min_fairness', 'max_min_fairness_perf'],
         '(b) Multi-GPU Jobs (Max-Min Fairness / LAS)'),
        ('fig11', ['finish_time_fairness', 'finish_time_fairness_perf'],
         '(c) Multi-GPU Jobs (Finish-Time Fairness)'),
    ]
    # fig11 uses different policy names
    policy_map_fig11 = {
        'finish_time_fairness':      'baseline',
        'finish_time_fairness_perf': 'gavel',
    }

    # 9 rows: [main, err, gap] x 3 groups (gap rows are spacers for labels)
    fig = plt.figure(figsize=(5, 9))
    gs = GridSpec(9, 1, height_ratios=[3, 1, 0.6, 3, 1, 0.6, 3, 1, 0.6], hspace=0.08)

    for row_idx, (fig_name, policies, title) in enumerate(fig_configs):
        ax_main = fig.add_subplot(gs[row_idx * 3, 0])
        ax_rmse = fig.add_subplot(gs[row_idx * 3 + 1, 0])

        pmap = policy_map_fig11 if fig_name == 'fig11' else policy_map
        ref_data = ref.get(fig_name, {})
        ref_x = np.array(ref_data.get('jobs_per_hr', []))

        for csv_policy in policies:
            role = pmap[csv_policy]
            label_ours = 'Baseline (ours)' if role == 'baseline' else 'Gavel (ours)'
            label_paper = 'Baseline (paper)' if role == 'baseline' else 'Gavel (paper)'
            marker = 's' if role == 'baseline' else 'o'
            color = COLORS[role]

            # Aggregate across seeds
            sub = df[(df['figure'] == fig_name) & (df['policy'] == csv_policy)].copy()
            sub = sub.dropna(subset=['jct_hours'])
            if sub.empty:
                continue
            stats = sub.groupby('jobs_per_hr')['jct_hours'].agg(['mean', 'std']).reset_index()
            stats['std'] = stats['std'].fillna(0)
            stats = stats.sort_values('jobs_per_hr')

            ax_main.errorbar(stats['jobs_per_hr'], stats['mean'],
                           yerr=stats['std'], fmt=f'-{marker}',
                           color=color, markersize=3, linewidth=1.2,
                           capsize=2, label=label_ours, zorder=3)

            # Paper reference (dashed)
            ref_y_raw = ref_data.get(role, [])
            if ref_y_raw:
                valid = [(x, y) for x, y in zip(ref_x, ref_y_raw) if y is not None]
                if valid:
                    px, py = zip(*valid)
                    px, py = np.array(px), np.array(py)
                    ax_main.plot(px, py, '--', color=color, alpha=0.5,
                               linewidth=1.2, label=label_paper, zorder=2)

                    if len(stats) > 1:
                        our_interp = np.interp(px, stats['jobs_per_hr'].values, stats['mean'].values)
                        rel_err = np.where(np.abs(py) > 1e-6,
                                           np.abs(our_interp - py) / np.abs(py) * 100,
                                           0.0)
                        bar_w = 0.15 if fig_name == 'fig9' else 0.08
                        ax_rmse.bar(px, rel_err, width=bar_w, color=color,
                                  alpha=0.6, label=role.capitalize())

        ax_main.set_ylabel('Avg JCT (hrs)')
        ax_main.set_ylim(0, 130)
        ax_main.grid(True, alpha=0.3)
        plt.setp(ax_main.get_xticklabels(), visible=False)
        if row_idx == 0:
            ax_main.legend(loc='upper left', framealpha=0.9, ncol=1, fontsize=6)

        ax_rmse.set_ylabel('Rel. Err (%)')
        ax_rmse.grid(True, alpha=0.3)
        ax_rmse.set_ylim(bottom=0)
        # Subfigure label below error subplot
        ax_rmse.set_xlabel(title, fontweight='bold')
        plt.setp(ax_rmse.get_xticklabels(), visible=False)

    fig.savefig(OUT_DIR / "fig_gavel_replication.png")
    plt.close()
    print(f"Saved {OUT_DIR / 'fig_gavel_replication.png'}")


def plot_fgd():
    """Generate combined FGD replication figure: 8 rows (4 subfigures, each main + rel. error)."""
    # Load paper reference
    with open(GAVEL_ROOT / "experiments/fgd-standalone/paper_reference_curves.json") as f:
        paper = json.load(f)

    # Load our results
    fig7_csv = pd.read_csv(GAVEL_ROOT / "standalone_fgd_replication/result/fig7-runs10-seed42/figure7_results.csv")
    fig9a_csv = pd.read_csv(GAVEL_ROOT / "standalone_fgd_replication/result/fig9-runs10-seed42/figure9a_unalloc.csv")
    fig9b_csv = pd.read_csv(GAVEL_ROOT / "standalone_fgd_replication/result/fig9-runs10-seed42/figure9b_occupied.csv")

    # Aggregate our results across runs (mean)
    fig7_agg = fig7_csv.groupby(['scheduler', 'arrived_workload_pct']).agg(
        frag_rate=('frag_rate', 'mean'),
        frag_total=('frag_total_pct', 'mean'),
    ).reset_index()

    fig9a_agg = fig9a_csv.groupby(['scheduler', 'arrived_pct']).agg(
        unalloc=('unalloc_gpu_pct', 'mean'),
    ).reset_index()

    fig9b_agg = fig9b_csv.groupby(['scheduler', 'arrived_pct']).agg(
        nodes=('occupied_nodes', 'mean'),
    ).reset_index()

    # Policy name mapping (our CSV -> paper JSON key)
    policy_map = {
        'Random': 'random',
        'DotProd': 'dotprod',
        'Clustering': 'clustering',
        'Packing': 'packing',
        'BestFit': 'bestfit',
        'FGD': 'fgd',
    }
    policies_to_plot = ['Random', 'DotProd', 'Clustering', 'Packing', 'BestFit', 'FGD']

    # All 4 panels in one figure
    panels = [
        {'key': 'fig7a_frag_rate_pct', 'label': '(a) Fragmentation Rate',
         'ylabel': 'Frag Rate (%)',
         'our_df': fig7_agg, 'x_col': 'arrived_workload_pct', 'y_col': 'frag_rate',
         'xlabel': 'Arrived Workload (%)'},
        {'key': 'fig7b_frag_over_total_pct', 'label': '(b) Frag / Total',
         'ylabel': 'Frag / Total (%)',
         'our_df': fig7_agg, 'x_col': 'arrived_workload_pct', 'y_col': 'frag_total',
         'xlabel': 'Arrived Workload (%)'},
        {'key': 'fig9a_unalloc_gpu_pct', 'label': '(c) Unallocated GPU',
         'ylabel': 'Unalloc GPU (%)',
         'our_df': fig9a_agg, 'x_col': 'arrived_pct', 'y_col': 'unalloc',
         'xlabel': 'Demand (%)'},
        {'key': 'fig9b_occupied_nodes', 'label': '(d) Occupied Nodes',
         'ylabel': 'Occupied Nodes',
         'our_df': fig9b_agg, 'x_col': 'arrived_pct', 'y_col': 'nodes',
         'xlabel': 'Demand (%)'},
    ]

    # 12 rows: [main, rel_err, gap] x 4 subfigures (gap rows are spacers for labels)
    fig = plt.figure(figsize=(5, 10))
    gs = GridSpec(12, 1,
                  height_ratios=[3, 1, 0.6, 3, 1, 0.6, 3, 1, 0.6, 3, 1, 0.6],
                  hspace=0.08)

    for panel_idx, panel in enumerate(panels):
        row_main = panel_idx * 3
        row_err = panel_idx * 3 + 1
        ax_main = fig.add_subplot(gs[row_main, 0])
        ax_err = fig.add_subplot(gs[row_err, 0])

        paper_data = paper[panel['key']]
        paper_x = np.array(paper_data['demand_pct'])

        for policy_name in policies_to_plot:
            paper_key = policy_map[policy_name]
            color = COLORS[policy_name]

            # Our results
            p = panel['our_df'][panel['our_df']['scheduler'] == policy_name].sort_values(panel['x_col'])
            our_x = p[panel['x_col']].values
            our_y = p[panel['y_col']].values

            ax_main.plot(our_x, our_y, '-', color=color, linewidth=1.5,
                        label=f'{policy_name} (ours)', zorder=3)

            # Paper reference (dashed)
            if paper_key in paper_data:
                paper_y_raw = paper_data[paper_key]
                mask = [i for i, v in enumerate(paper_y_raw) if v is not None]
                px = np.array([paper_x[i] for i in mask])
                py = np.array([paper_y_raw[i] for i in mask])

                ax_main.plot(px, py, '--', color=color, alpha=0.5, linewidth=1.5,
                            label=f'{policy_name} (paper)', zorder=2)

                if len(our_x) > 1 and len(px) > 1:
                    our_interp = np.interp(px, our_x, our_y)
                    # Relative error: |ours - paper| / |paper| * 100, guard div-by-zero
                    rel_err = np.where(np.abs(py) > 1e-6,
                                       np.abs(our_interp - py) / np.abs(py) * 100,
                                       0.0)
                    bar_width = (px[-1] - px[0]) / len(px) * 0.25
                    offset = (list(policies_to_plot).index(policy_name) - 1) * bar_width
                    ax_err.bar(px + offset, rel_err, width=bar_width,
                              color=color, alpha=0.6, label=policy_name)

        ax_main.set_ylabel(panel['ylabel'])
        ax_main.grid(True, alpha=0.3)
        plt.setp(ax_main.get_xticklabels(), visible=False)
        if panel_idx == 0:
            ax_main.legend(loc='best', framealpha=0.9, ncol=2, fontsize=6)

        ax_err.set_ylabel('Rel. Err (%)')
        ax_err.grid(True, alpha=0.3)
        ax_err.set_ylim(bottom=0)
        # Subfigure label below the error subplot
        ax_err.set_xlabel(panel['label'], fontweight='bold')
        plt.setp(ax_err.get_xticklabels(), visible=False)

    fig.savefig(OUT_DIR / "fig_fgd_replication.png")
    plt.close()
    print(f"Saved {OUT_DIR / 'fig_fgd_replication.png'}")


if __name__ == '__main__':
    plot_gavel()
    plot_fgd()
    print("Done.")
