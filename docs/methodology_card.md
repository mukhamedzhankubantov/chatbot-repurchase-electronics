# Methodology Passport Card

## 1. Project Information

| Field | Value |
|---|---|
| Title | Chatbot Personalization, 24/7 Availability and Repurchase Intention in Online Consumer Electronics |
| Authors | Mukhamedzhan Kubantov, Rakhimbek Baizhan |
| Course | Research Methods, Task 2 |
| GitHub | https://github.com/mukhamedzhankubantov/chatbot-repurchase-electronics |
| License | MIT |

## 2. Research Type

**Quantitative, explanatory, cross-sectional survey study.**

Justification: the research questions ask how strongly chatbot personalization and perceived 24/7 availability affect satisfaction, trust and repurchase intention, and whether tech-savviness and product price/complexity change these effects. These are questions about the size and direction of relationships between measurable constructs, so they require numeric Likert-scale data and statistical testing (regression and PLS-SEM), not interviews or thematic analysis. The design is observational (respondents are not assigned to conditions), so the results describe associations, not proven causation.

## 3. Hypotheses

| ID | H0 (null) | H1 (alternative) |
|---|---|---|
| H1 | Chatbot personalization has no effect on customer satisfaction | Chatbot personalization has a significant positive effect on customer satisfaction |
| H2 | Perceived 24/7 availability has no effect on brand trust | Perceived 24/7 availability has a significant positive effect on brand trust |
| H3a | The personalization x availability interaction has no effect on repurchase intention | The personalization x availability interaction has a significant positive effect on repurchase intention |
| H3b | Tech-savviness and price/complexity do not moderate the availability -> trust relationship | Tech-savviness and price/complexity significantly moderate the availability -> trust relationship |

## 4. Variables Matrix

| Role | Variable | Operationalization |
|---|---|---|
| Independent (what we vary / predict from) | Chatbot personalization (PERS) | Mean of 3 Likert items (1-5) |
| Independent | Perceived 24/7 availability and response speed (AVAIL) | Mean of 3 Likert items (1-5) |
| Independent | Personalization x availability | Product of standardized PERS and AVAIL |
| Mediator | Customer satisfaction (SAT) | Mean of 3 Likert items |
| Mediator | Brand trust (TRUST) | Mean of 3 Likert items |
| Moderator | Tech-savviness (TECH) | Mean of 3 Likert items |
| Moderator | Product price/complexity (COMPLEX) | Mean of 3 Likert items |
| Dependent (what we measure) | Satisfaction (H1), Brand trust (H2, H3b), Repurchase intention (REPUR, H3a) | Mean of 3 Likert items each |
| Controlled (held constant or adjusted for) | Age, income, purchase frequency | Included as control variables in every model |
| Controlled (technical conditions) | Random seed 42, Python 3.12, pinned library versions, Docker image python:3.12-slim, 2000 bootstrap resamples | Fixed in `configs/config.yaml`, `requirements.txt`, `Dockerfile` |

## 5. Metrics and Baseline

| Type | Definition |
|---|---|
| Primary metric | Standardized regression coefficient (beta) of the key term in each model, with p-value (alpha = 0.05) and bootstrap 95% confidence interval; model R-squared |
| Guardrail metrics | Cronbach's alpha >= 0.70 for every construct (reliability); maximum VIF <= 5.0 among predictors (multicollinearity) |
| Baseline | Controls-only model (age, income, purchase frequency). A hypothesis model must explain more variance (R-squared) than this baseline to be considered informative |

## 6. Reproducibility Summary

- Pipeline: `src/benchmark.py`, configured by `configs/config.yaml`.
- Run: `docker build -t chatbot-repurchase .` then `docker run --rm -v "${PWD}/results:/app/results" chatbot-repurchase`.
- Data: a synthetic 10-row sample is tracked in `data/sample/`; real survey responses stay in `data/raw/` and are never published.
- The sample results are a smoke test only and carry no statistical meaning. The full PLS-SEM analysis is performed on the collected survey data in the main study phase.