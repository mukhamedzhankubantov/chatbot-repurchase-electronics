 # Domain Model (ML Track): Formal Definition of Model, Loss and Metrics

## 1. Problem Setting

Let the dataset be $\mathcal{D}=\{(\mathbf{x}_i, y_i)\}_{i=1}^{N}$, where $\mathbf{x}_i \in \mathbb{R}^{p}$ is the vector of standardized predictors (construct scores, interaction terms and controls) and $y_i \in \mathbb{R}$ is the standardized outcome (satisfaction, trust or repurchase intention).

For each hypothesis the model is linear:

$$ f_{\boldsymbol{\beta}}(\mathbf{x}_i) = \beta_0 + \boldsymbol{\beta}^{\top}\mathbf{x}_i $$

## 2. Loss Function

The loss is the mean squared error:

$$ \mathcal{L}(\boldsymbol{\beta}) = \frac{1}{N}\sum_{i=1}^{N}\bigl(y_i - f_{\boldsymbol{\beta}}(\mathbf{x}_i)\bigr)^2 $$

It has the closed-form ordinary least squares solution:

$$ \hat{\boldsymbol{\beta}} = (\mathbf{X}^{\top}\mathbf{X})^{-1}\mathbf{X}^{\top}\mathbf{y} $$

## 3. Target Metrics

### 3.1 Model quality

$$ R^2 = 1 - \frac{\sum_{i}(y_i-\hat{y}_i)^2}{\sum_{i}(y_i-\bar{y})^2} $$

$$ \alpha = \frac{k}{k-1}\left(1-\frac{\sum_{j=1}^{k}\sigma_j^2}{\sigma_T^2}\right) $$

$$ \mathrm{VIF}_j = \frac{1}{1-R_j^2} $$

### 3.2 Uncertainty (bootstrap)

For $b = 1,\dots,B$ draw $N$ observations with replacement and compute $\hat{\boldsymbol{\beta}}^{*(b)}$. The 95% confidence interval of a coefficient is:

$$ \mathrm{CI}_{95\%} = \bigl[\,q_{0.025}\bigl(\hat{\beta}^{*}\bigr),\; q_{0.975}\bigl(\hat{\beta}^{*}\bigr)\,\bigr] $$

### 3.3 Pipeline performance (benchmark)

Let $\ell_r$ be the latency of run $r$ in milliseconds, $r = 1,\dots,R$.

$$ \tilde{\ell} = \mathrm{median}(\ell_1,\dots,\ell_R), \qquad p_{95} = q_{0.95}(\ell), \qquad p_{99} = q_{0.99}(\ell) $$

Error rate (guardrail metric):

$$ \varepsilon = \frac{1}{R}\sum_{r=1}^{R}\mathbb{1}[\text{run } r \text{ failed}] $$

Speed-up of the proposed method over the baseline:

$$ S = \frac{\tilde{\ell}_{\mathrm{baseline}}}{\tilde{\ell}_{\mathrm{proposed}}} $$

## 4. Methods Compared

- **Baseline:** the $B$ bootstrap resamples are fitted one by one in a Python loop.
- **Proposed:** all $B$ resamples are solved in one vectorized batch.

Both methods use the same seed and the same data.

## 5. Notation

| Symbol | Meaning | Unit / range |
|---|---|---|
| $N$ | Number of respondents (load) | integer |
| $p$ | Number of predictors | integer |
| $\mathbf{x}_i$ | Predictor vector of respondent $i$ | standardized |
| $y_i$ | Outcome of respondent $i$ | standardized |
| $\boldsymbol{\beta}$ | Regression coefficients | dimensionless |
| $\mathcal{L}$ | Mean squared error | dimensionless |
| $R^2$ | Share of explained variance | 0 to 1 |
| $\alpha$ | Cronbach's alpha | 0 to 1 |
| $\mathrm{VIF}_j$ | Variance inflation factor | at least 1 |
| $B$ | Number of bootstrap resamples | integer |
| $\ell_r$ | Latency of run $r$ | ms |
| $p_{95}, p_{99}$ | Latency percentiles | ms |
| $\varepsilon$ | Error rate | 0 to 1 |
| $S$ | Speed-up | dimensionless |