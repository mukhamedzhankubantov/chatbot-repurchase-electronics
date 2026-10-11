"""Analysis / benchmark pipeline for the AI chatbot repurchase-intention study.

Reads a survey CSV, builds construct scores, checks reliability (Cronbach's alpha),
estimates one OLS model per hypothesis (standardized betas, bootstrap CIs, VIF),
and writes results + run metadata (runtime, peak memory) to the results folder.

Usage:
    python src/benchmark.py --config configs/config.yaml
"""
import argparse
import json
import logging
import platform
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import statsmodels
import statsmodels.api as sm
import yaml
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Hypotheses that test moderation without a predicted sign
NON_DIRECTIONAL = {"H3b"}


def setup_logging(log_file):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        ],
    )
    return logging.getLogger("benchmark")


def num(x):
    """Convert to a JSON-safe float (NaN/inf -> None)."""
    x = float(x)
    return None if (np.isnan(x) or np.isinf(x)) else x


def zscore(s):
    sd = s.std(ddof=1)
    if sd is None or np.isnan(sd) or sd == 0:
        sd = 1.0
    return (s - s.mean()) / sd


def cronbach_alpha(items):
    items = items.dropna()
    k = items.shape[1]
    if k < 2 or len(items) < 2:
        return float("nan")
    item_var = items.var(axis=0, ddof=1).sum()
    total_var = items.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return float("nan")
    return float(k / (k - 1) * (1 - item_var / total_var))


def build_scores(df, cfg):
    needed = [c for items in cfg["constructs"].values() for c in items] + list(cfg["controls"])
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Columns missing in the data file: {missing}")
    scores = pd.DataFrame(index=df.index)
    for name, items in cfg["constructs"].items():
        scores[name] = df[items].mean(axis=1)
    for c in cfg["controls"]:
        scores[c] = df[c]
    return scores


def design(z, terms):
    """Build the predictor matrix; 'A:B' means an interaction of standardized A and B."""
    X = pd.DataFrame(index=z.index)
    for t in terms:
        if ":" in t:
            a, b = t.split(":")
            X[t] = zscore(z[a] * z[b])
        else:
            X[t] = z[t]
    return X


def bootstrap_ci(y, X, n_resamples, alpha, rng):
    Xc = np.column_stack([np.ones(len(X)), X.values])
    yv = y.values
    draws = np.empty((n_resamples, Xc.shape[1]))
    for i in range(n_resamples):
        idx = rng.integers(0, len(yv), len(yv))
        draws[i] = np.linalg.lstsq(Xc[idx], yv[idx], rcond=None)[0]
    lo, hi = np.percentile(draws, [100 * alpha / 2, 100 * (1 - alpha / 2)], axis=0)
    return lo[1:], hi[1:]


def run_model(name, spec, z, cfg, rng, log):
    controls = list(cfg["controls"])
    terms = list(spec["predictors"])
    alpha = cfg["alpha"]
    y = z[spec["dv"]]

    # Baseline: controls only
    base = sm.OLS(y, sm.add_constant(design(z, controls), has_constant="add")).fit()

    # Full model: predictors + controls
    X = design(z, terms + controls)
    Xc = sm.add_constant(X, has_constant="add")
    fit = sm.OLS(y, Xc).fit()

    if fit.df_resid < 10:
        log.warning("%s: only %d residual degrees of freedom - results are a smoke test, "
                    "not statistical evidence.", name, int(fit.df_resid))

    with np.errstate(all="ignore"):
        vifs = {col: float(variance_inflation_factor(Xc.values, i))
                for i, col in enumerate(Xc.columns) if col != "const"}

    if cfg["bootstrap"]["enabled"]:
        lo, hi = bootstrap_ci(y, X, cfg["bootstrap"]["n_resamples"], alpha, rng)
        ci = dict(zip(X.columns, zip(lo, hi)))
    else:
        ci = {c: (np.nan, np.nan) for c in X.columns}

    rows = []
    for col in X.columns:
        rows.append({
            "hypothesis": name,
            "dv": spec["dv"],
            "term": col,
            "role": "predictor" if col in terms else "control",
            "std_beta": fit.params[col],
            "std_error": fit.bse[col],
            "p_value": fit.pvalues[col],
            "ci_low": ci[col][0],
            "ci_high": ci[col][1],
            "vif": vifs.get(col, np.nan),
            "r_squared": fit.rsquared,
            "baseline_r_squared": base.rsquared,
            "n": int(fit.nobs),
        })

    # Decision on the key term(s): interaction terms if present, else the first predictor
    key_terms = [t for t in terms if ":" in t] or [terms[0]]
    supported = False
    for t in key_terms:
        p, b = fit.pvalues[t], fit.params[t]
        if not np.isnan(p) and p < alpha and (name in NON_DIRECTIONAL or b > 0):
            supported = True

    max_vif = max([v for k, v in vifs.items() if k in terms], default=float("nan"))
    summary = {
        "key_terms": key_terms,
        "h1_supported": bool(supported),
        "r_squared": num(fit.rsquared),
        "baseline_r_squared": num(base.rsquared),
        "max_vif_predictors": num(max_vif),
        "vif_ok": bool(not np.isnan(max_vif) and max_vif <= cfg["metrics"]["guardrail"]["vif_max"]),
    }
    return rows, summary


def main():
    parser = argparse.ArgumentParser(description="Chatbot repurchase study - analysis pipeline")
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()

    t0 = time.perf_counter()
    tracemalloc.start()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    log = setup_logging(cfg["paths"]["log_file"])
    log.info("Config: %s | seed=%s", args.config, cfg["seed"])
    np.random.seed(cfg["seed"])
    rng = np.random.default_rng(cfg["seed"])

    data_path = Path(cfg["paths"]["data"])
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    df = pd.read_csv(data_path)
    log.info("Loaded %s: %d rows x %d columns", data_path, *df.shape)

    scores = build_scores(df, cfg)
    n_before = len(scores)
    scores = scores.dropna()
    if len(scores) < n_before:
        log.warning("Dropped %d rows with missing values", n_before - len(scores))

    # Reliability guardrail
    a_min = cfg["metrics"]["guardrail"]["cronbach_alpha_min"]
    rel_rows = []
    for name, items in cfg["constructs"].items():
        a = cronbach_alpha(df.loc[scores.index, items])
        ok = bool(not np.isnan(a) and a >= a_min)
        rel_rows.append({"construct": name, "n_items": len(items),
                         "cronbach_alpha": a, "meets_threshold": ok})
        log.info("Cronbach alpha %-8s = %.3f %s", name, a, "OK" if ok else "BELOW THRESHOLD")

    # Models
    z = scores.apply(zscore)
    all_rows, hypotheses = [], {}
    for name, spec in cfg["models"].items():
        rows, summ = run_model(name, spec, z, cfg, rng, log)
        all_rows.extend(rows)
        hypotheses[name] = summ
        log.info("%s: key=%s | R2=%.3f (baseline %.3f) | H1 supported: %s",
                 name, summ["key_terms"], summ["r_squared"],
                 summ["baseline_r_squared"], summ["h1_supported"])

    # Outputs
    out = Path(cfg["paths"]["results_dir"])
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows).to_csv(out / "results.csv", index=False)
    pd.DataFrame(rel_rows).to_csv(out / "reliability.csv", index=False)

    runtime = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    meta = {
        "n_respondents": int(len(scores)),
        "seed": cfg["seed"],
        "runtime_sec": round(runtime, 3),
        "peak_python_memory_mb": round(peak / 1024 / 1024, 2),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "versions": {"numpy": np.__version__, "pandas": pd.__version__,
                     "scipy": scipy.__version__, "statsmodels": statsmodels.__version__},
        "hypotheses": hypotheses,
        "reliability": [{k: (num(v) if isinstance(v, float) else v) for k, v in r.items()}
                        for r in rel_rows],
    }
    with open(out / "summary.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    log.info("Done in %.2f s | peak memory %.2f MB | outputs in %s",
             runtime, peak / 1024 / 1024, out)


if __name__ == "__main__":
    main()