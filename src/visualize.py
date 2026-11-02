"""Publication-ready figures for Task 3.

fig1_latency_vs_load: median latency vs load with 95% bootstrap CI (log-log axes).
fig2_distribution_boxplot: latency distribution per method at selected loads.

Every figure is saved twice: vector .pdf and raster .png (300 DPI).

Usage:
    python src/visualize.py --summary data/processed/metrics_summary.csv \
        --raw data/raw/test_run.jsonl --out reports/figures
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import seaborn as sns

PALETTE = sns.color_palette("colorblind")
STYLE = {
    "baseline": dict(color=PALETTE[0], marker="o", linestyle="--", hatch="//"),
    "proposed": dict(color=PALETTE[1], marker="s", linestyle="-", hatch="\\\\"),
}
LABELS = {
    "baseline": "Baseline (Python loop)",
    "proposed": "Proposed (vectorized)",
}
BOX_LOADS = [100, 1000, 5000]


def apply_style():
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "figure.dpi": 100,
    })


def save_figure(fig, out_dir, name):
    """Save vector PDF and 300-DPI PNG."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_latency_vs_load(summary, out_dir):
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for method, g in summary.groupby("method"):
        g = g.sort_values("n_respondents")
        st = STYLE[method]
        x, med = g["n_respondents"].to_numpy(), g["median_ms"].to_numpy()
        lo, hi = g["ci_low_ms"].to_numpy(), g["ci_high_ms"].to_numpy()
        ax.fill_between(x, lo, hi, color=st["color"], alpha=0.25, linewidth=0)
        ax.errorbar(x, med, yerr=[med - lo, hi - med], color=st["color"],
                    marker=st["marker"], linestyle=st["linestyle"], capsize=3,
                    markersize=6, linewidth=1.6, label=LABELS[method])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Load: number of respondents (count)")
    ax.set_ylabel("Latency (ms), median with 95% bootstrap CI")
    ax.set_title("Bootstrap pipeline latency vs load")
    ax.legend(loc="upper left")
    save_figure(fig, out_dir, "fig1_latency_vs_load")


def plot_distribution_boxplot(raw, out_dir):
    ev = raw[(raw["phase"] == "evaluation") & (~raw["error"])]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    width, offset = 0.35, 0.2
    handles = []
    for k, (method, sign) in enumerate((("baseline", -1), ("proposed", 1))):
        st = STYLE[method]
        data = [ev[(ev["method"] == method) & (ev["n_respondents"] == n)]["latency_ms"].to_numpy()
                for n in BOX_LOADS]
        pos = np.arange(len(BOX_LOADS)) + sign * offset
        bp = ax.boxplot(data, positions=pos, widths=width, patch_artist=True,
                        medianprops=dict(color="black", linewidth=1.4),
                        flierprops=dict(marker=st["marker"], markersize=3,
                                        markerfacecolor=st["color"], alpha=0.6))
        for box in bp["boxes"]:
            box.set(facecolor=st["color"], alpha=0.55, hatch=st["hatch"], edgecolor="black")
        handles.append(Patch(facecolor=st["color"], alpha=0.55, hatch=st["hatch"],
                             edgecolor="black", label=LABELS[method]))
    ax.set_xticks(np.arange(len(BOX_LOADS)))
    ax.set_xticklabels([str(n) for n in BOX_LOADS])
    ax.set_yscale("log")
    ax.set_xlabel("Load: number of respondents (count)")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Latency distribution (evaluation runs; box = p25-p75)")
    ax.legend(handles=handles, loc="upper left")
    save_figure(fig, out_dir, "fig2_distribution_boxplot")


def main():
    parser = argparse.ArgumentParser(description="Generate Task 3 figures")
    parser.add_argument("--summary", default="data/processed/metrics_summary.csv")
    parser.add_argument("--raw", default="data/raw/test_run.jsonl")
    parser.add_argument("--out", default="reports/figures")
    args = parser.parse_args()

    apply_style()
    summary = pd.read_csv(args.summary)
    raw = pd.read_json(args.raw, lines=True)
    plot_latency_vs_load(summary, args.out)
    plot_distribution_boxplot(raw, args.out)
    print(f"Figures saved to {args.out}")


if __name__ == "__main__":
    main()