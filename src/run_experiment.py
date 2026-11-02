"""Generate raw timing logs (data/raw/test_run.jsonl) for the Task 3 benchmark.

System under test: bootstrap confidence intervals for OLS coefficients, the
core of the Task 2 analysis pipeline, run on synthetic survey-like data.

- baseline: one least-squares fit per resample inside a Python loop
- proposed: all resamples solved in one vectorized batch (resample counts and
  two matrix products instead of a Python loop)

Usage:
    python src/run_experiment.py --out data/raw/test_run.jsonl
"""
import argparse
import json
import time
import tracemalloc
from pathlib import Path

import numpy as np

SEED = 42
LOADS = [50, 100, 200, 500, 1000, 2000, 5000]  # respondents
N_WARMUP = 5
N_EVAL = 50
N_RESAMPLES = 200
N_PREDICTORS = 6


def make_data(n, p, rng):
    """Synthetic standardized predictors and outcome with a known linear signal."""
    X = rng.normal(size=(n, p))
    beta = np.linspace(0.8, 0.1, p)
    y = X @ beta + rng.normal(scale=1.0, size=n)
    return np.column_stack([np.ones(n), X]), y


def bootstrap_baseline(Xc, y, n_resamples, rng):
    n = len(y)
    draws = np.empty((n_resamples, Xc.shape[1]))
    for b in range(n_resamples):
        idx = rng.integers(0, n, n)
        draws[b] = np.linalg.lstsq(Xc[idx], y[idx], rcond=None)[0]
    return draws


def bootstrap_proposed(Xc, y, n_resamples, rng):
    """Bootstrap via resample counts: X'WX and X'Wy for all resamples in two matrix products."""
    n, k = Xc.shape
    counts = rng.multinomial(n, np.full(n, 1.0 / n), size=n_resamples).astype(float)
    outer = (Xc[:, :, None] * Xc[:, None, :]).reshape(n, k * k)
    xtx = (counts @ outer).reshape(n_resamples, k, k)
    xty = counts @ (Xc * y[:, None])
    return np.linalg.solve(xtx, xty[..., None])[..., 0]


METHODS = {"baseline": bootstrap_baseline, "proposed": bootstrap_proposed}


def one_run(func, Xc, y, run_seed):
    """Return latency (ms), peak memory (MB) and an error flag for one run."""
    error = False
    try:
        t0 = time.perf_counter()
        draws = func(Xc, y, N_RESAMPLES, np.random.default_rng(run_seed))
        latency_ms = (time.perf_counter() - t0) * 1000.0
        error = not bool(np.all(np.isfinite(draws)))
    except Exception:
        latency_ms, error = float("nan"), True

    # memory is measured in a separate pass so tracemalloc does not distort latency
    tracemalloc.start()
    try:
        func(Xc, y, N_RESAMPLES, np.random.default_rng(run_seed))
    except Exception:
        error = True
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return latency_ms, peak / 1024 / 1024, error


def main():
    parser = argparse.ArgumentParser(description="Generate raw benchmark logs")
    parser.add_argument("--out", default="data/raw/test_run.jsonl")
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    run_id = 0
    with open(out, "w", encoding="utf-8") as f:
        for method, func in METHODS.items():
            for n in LOADS:
                Xc, y = make_data(n, N_PREDICTORS, np.random.default_rng(SEED + n))
                for phase, count in (("warmup", N_WARMUP), ("evaluation", N_EVAL)):
                    for _ in range(count):
                        run_id += 1
                        lat, mem, err = one_run(func, Xc, y, SEED + run_id)
                        rec = {
                            "run_id": run_id,
                            "method": method,
                            "n_respondents": n,
                            "phase": phase,
                            "latency_ms": None if np.isnan(lat) else round(lat, 4),
                            "peak_mem_mb": round(mem, 4),
                            "error": bool(err),
                            "seed": SEED + run_id,
                        }
                        f.write(json.dumps(rec) + "\n")
                print(f"{method:9s} n={n:5d} done", flush=True)
    print(f"Wrote {run_id} runs to {out}")


if __name__ == "__main__":
    main()