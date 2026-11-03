"""Turn the raw benchmark log into a clean summary table.

Reads data/raw/test_run.jsonl, drops warm-up runs, and for every
(method, n_respondents) pair computes latency statistics on the evaluation runs:
median, mean, SD, p25, p75, p95, p99, a bootstrap 95% CI of the median,
the error rate and the median peak memory.

Usage:
    python src/process_data.py --raw data/raw/test_run.jsonl \
        --out data/processed/metrics_summary.csv
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_BOOT = 2000
REQUIRED = {"run_id", "method", "n_respondents", "phase", "latency_ms",
            "peak_mem_mb", "error", "seed"}


def load_raw(path):
    raw = pd.read_json(path, lines=True)
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
    return raw


def bootstrap_median_ci(x, rng, n_boot=N_BOOT):
    """95% percentile bootstrap CI of the median."""
    idx = rng.integers(0, len(x), (n_boot, len(x)))
    medians = np.median(x[idx], axis=1)
    return np.percentile(medians, [2.5, 97.5])


def summarize(raw, rng):
    ev = raw[raw["phase"] == "evaluation"]  # warm-up runs are discarded
    rows = []
    for (method, n), g in ev.groupby(["method", "n_respondents"]):
        ok = g[~g["error"]]
        x = ok["latency_ms"].to_numpy(dtype=float)
        lo, hi = bootstrap_median_ci(x, rng)
        rows.append({
            "method": method,
            "n_respondents": int(n),
            "n_runs": int(len(g)),
            "median_ms": np.median(x),
            "mean_ms": x.mean(),
            "sd_ms": x.std(ddof=1),
            "p25_ms": np.percentile(x, 25),
            "p75_ms": np.percentile(x, 75),
            "p95_ms": np.percentile(x, 95),
            "p99_ms": np.percentile(x, 99),
            "ci_low_ms": lo,
            "ci_high_ms": hi,
            "error_rate": float(g["error"].mean()),
            "peak_mem_mb_median": ok["peak_mem_mb"].median(),
        })
    return pd.DataFrame(rows).sort_values(["method", "n_respondents"]).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Summarize raw benchmark log")
    parser.add_argument("--raw", default="data/raw/test_run.jsonl")
    parser.add_argument("--out", default="data/processed/metrics_summary.csv")
    args = parser.parse_args()

    raw = load_raw(args.raw)
    n_warm = int((raw["phase"] == "warmup").sum())
    n_eval = int((raw["phase"] == "evaluation").sum())
    print(f"Loaded {len(raw)} runs: {n_warm} warm-up (discarded), {n_eval} evaluation")

    summary = summarize(raw, np.random.default_rng(SEED))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary.round(4).to_csv(out, index=False)
    print(summary[["method", "n_respondents", "median_ms", "p95_ms", "error_rate"]]
          .round(2).to_string(index=False))
    print(f"Saved {out}")


if __name__ == "__main__":
    main()