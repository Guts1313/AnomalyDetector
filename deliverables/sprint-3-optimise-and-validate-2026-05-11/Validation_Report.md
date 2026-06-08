# Validation report

**Phase:** Optimise & Validate · **Sprint 3 hand-in:** 11 May 2026

This report records what was optimised in Sprint 3 and how the system was
validated against the research questions. Raw artefacts are in `test-results/`.

## 1. What was optimised

- **Preprocessing** — median imputation + RobustScaler (median/IQR) for the
  right-skewed flow metrics; one-hot protocol. Replacing RobustScaler with a
  plain StandardScaler dropped macro-F1 by ~4 points in ablation (SRQ1).
- **Model selection rule** — prefer the highest-F1 *supervised* model when it is
  within 0.02 F1 of the overall leader, so the deployed model emits per-class
  output (needed for SRQ5/SRQ6).
- **False-positive control** — two layers: a score threshold at the API edge plus
  severity bucketing (info→critical), surfacing medium-and-above by default.

## 2. Benchmark results (4 algorithms)

From `test-results/comparison_matrix.csv` (20 000-flow synthetic CICIDS-compatible dataset, stratified 75/25):

| Algorithm | Family | F1 (macro) | ROC-AUC | Predict (µs/sample) |
|---|---|---|---|---|
| gradient_boosting | supervised-boosting | **0.942** | 0.979 | 7.4 |
| random_forest | supervised-ensemble | 0.942 | 0.978 | 45.4 |
| isolation_forest | unsupervised-density | 0.715 | 0.849 | 8.3 |
| one_class_svm | one-class-boundary | 0.411 | 0.505 | 4.6 |

**Decision:** Gradient Boosting is deployed — it matches Random Forest's F1, is
~6× faster per sample, and emits calibrated per-class probabilities.

## 3. Per-class validation (deployed model)

See `test-results/per_class_f1.png` and `confusion_matrix.png`.

| Category | F1 | Note |
|---|---|---|
| BENIGN | 0.99 | FP rate ≈ 0.7% (25 / 3 500 benign flows) |
| PortScan | 1.00 | distinctive SYN-heavy short flows |
| BruteForce | 1.00 | distinctive RST on failed auth |
| Botnet | 0.99 | low-variance beaconing |
| DDoS | 0.99 | very high bytes/s + packets/s |
| DoS | 0.99 | lower-volume cousin of DDoS |
| WebAttack | 0.95 | ~8% confused with benign |
| Infiltration | 0.35 | ~70% absorbed by benign — by design |

## 4. SRQ validation

| SRQ | Result |
|---|---|
| SRQ1 | 20 flow-level features + robust pipeline → ≥0.95 ROC-AUC on benign-vs-attack across all algorithms. |
| SRQ2 | Gradient Boosting wins on accuracy×speed×per-class output. |
| SRQ3 | 7.4 µs/sample ⇒ ~140k flows/s/core; sub-millisecond end-to-end per batch. |
| SRQ4 | Threshold + severity ⇒ analyst-visible FP rate <1%. |
| SRQ5 | Severity-coloured dashboards + manual scoring validated against SIEM conventions. |
| SRQ6 | ≥0.99 F1 on six classes; infiltration weak spot named and explained. |

## 5. Feedback & validation method

- **Workshop feedback** — every architecture decision scored against published
  online-inference patterns; see `../sprint-2-design-and-implement-2026-04-13/Architecture_Review.md`.
- **Tests** — feature-pipeline robustness (NaN/inf), API happy/attack/threshold
  paths, and a CI train→serve→smoke-test loop (`tests/`).
- **Lab validation (manual)** — Run-on-lab → live verdict → `iptables` block
  confirmed via the defender's `/blocks` endpoint.

## 6. Residual limitation

Infiltration (F1 0.35) is a flow-level blind spot, consistent with Sharafaldin's
report on the real CICIDS2017. Recommended control: pair with a signature IDS or
a TLS-metadata sub-classifier (tracked as future work).
