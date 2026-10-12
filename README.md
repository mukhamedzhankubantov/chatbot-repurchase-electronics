# Chatbot Personalization, 24/7 Availability and Repurchase Intention in Online Consumer Electronics

**Authors:** Kubantov Mukhamedzhan, Rakhimbek Baizhan  
**Course:** Research Methods (Task 2: Reproducible Research Repository)

## Overview

This repository accompanies a quantitative survey study on how AI chatbot personalization and perceived 24/7 availability affect customer satisfaction, brand trust and repurchase intention in online consumer electronics. It contains the methodology card, configuration, sample data and a reproducible analysis pipeline.

## System Requirements

- Docker (recommended), or Python 3.12 with the packages in `requirements.txt`
- Git
- About 500 MB of free disk space for the Docker image; no GPU needed

## Research Question

How do AI chatbot personalization and perceived 24/7 availability, individually and jointly, influence customer satisfaction, brand trust and repurchase intention in the online consumer electronics segment, and how is this moderated by tech-savviness and product price/complexity?

| ID | Hypothesis (alternative) | Dependent variable |
|----|--------------------------|--------------------|
| H1 | Chatbot personalization positively affects satisfaction | Satisfaction |
| H2 | Perceived 24/7 availability positively affects brand trust | Brand trust |
| H3a | Personalization x availability interaction positively affects repurchase intention | Repurchase intention |
| H3b | Tech-savviness and price/complexity moderate availability -> trust | Brand trust |

## Methodology Note

The full study uses a survey (Likert items) analysed with PLS-SEM. This repository contains a lightweight, fully reproducible pipeline: construct scores (mean of items), reliability check (Cronbach's alpha), and one OLS model per hypothesis with standardized betas, bootstrap confidence intervals, VIF and a controls-only baseline. The full PLS-SEM analysis is carried out on the collected survey data in the main study phase.

The file in `data/sample/` is **synthetic** (10 rows) and is meant only to verify that the code runs. Its results have no statistical meaning.

## Repository Structure

    .
    |-- configs/config.yaml     # all settings
    |-- data/
    |   |-- sample/             # synthetic 10-row sample (tracked)
    |   +-- raw/                # real survey data (git-ignored)
    |-- src/benchmark.py        # analysis pipeline
    |-- notebooks/              # exploratory notebooks
    |-- docs/                   # methodology card and notes
    |-- results/                # generated outputs (git-ignored)
    |-- Dockerfile
    |-- requirements.txt        # pinned dependencies
    +-- LICENSE                 # MIT

## Quickstart

**With Docker (recommended):**

```bash
docker build -t chatbot-repurchase .
docker run --rm -v "$(pwd)/results:/app/results" chatbot-repurchase
```

(PowerShell: replace `$(pwd)` with `${PWD}`.)

**Without Docker (Python 3.12):**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/benchmark.py --config configs/config.yaml
```

Outputs are written to `results/`: `results.csv` (coefficients), `reliability.csv`, `summary.json` (including runtime and memory) and `run.log`.

## Benchmarks

Run on the synthetic sample (`seed: 42`, 2000 bootstrap resamples). Metrics: R-squared of the full model versus the controls-only baseline; the guardrail is the maximum VIF among predictors (threshold 5.0).

| Hypothesis | Key term | R2 (full) | R2 (baseline) | Max VIF |
|---|---|---|---|---|
| H1 | PERS | 0.991 | 0.890 | 7.06 |
| H2 | AVAIL | 0.984 | 0.836 | 4.01 |
| H3a | PERS:AVAIL | 1.0 | 0.858 | 21764.75 |
| H3b | AVAIL:TECH, AVAIL:COMPLEX | 0.994 | 0.836 | 151.38 |

Runtime: 1.214 s, peak Python memory: 0.47 MB (Python 3.12.15, N = 10 synthetic respondents).

Reliability guardrail: Cronbach's alpha >= 0.70 for every construct (see `results/reliability.csv`).

## Reproducibility

- Random seed fixed in `configs/config.yaml`.
- Dependency versions pinned in `requirements.txt`; base image `python:3.12-slim`.
- Every parameter is in the config file; no values are hard-coded in the script.

## Citation

Kubantov, M., & Baizhan, R. (2026). *Chatbot personalization, 24/7 availability and repurchase intention in online consumer electronics* [Computer software]. GitHub. https://github.com/mukhamedzhankubantov/chatbot-repurchase-electronics

## License

MIT, see [LICENSE](LICENSE).