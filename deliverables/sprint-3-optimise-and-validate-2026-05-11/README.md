# Sprint 3 — Optimise & Validate

**Hand-in:** 11 May 2026 · **Phase:** Optimise & Validate

| Required (example) deliverable | Provided |
|---|---|
| Test results | [test-results/](test-results/) — comparison matrix, per-class F1, confusion matrix |
| Feedback & validation | [Validation_Report.md](Validation_Report.md) |
| Implementation documents / code | Repository: `src/`, `lab/`, `tests/`, `frontend/` (pointers below) |

## Contents

- **Validation_Report.md** — what was optimised, the benchmark results, per-class validation, false-positive control, and how each SRQ was answered/validated.
- **test-results/** — `comparison_matrix.md` / `.csv` (4-algorithm benchmark), `per_class_report.json`, and the charts `algo_comparison.png`, `per_class_f1.png`, `confusion_matrix.png`.

## Code (in the repository)

| Area | Location |
|---|---|
| Feature pipeline & schema | `src/anomaly_detector/features/` |
| Model trainers & registry | `src/anomaly_detector/models/` |
| FastAPI service & audit store | `src/anomaly_detector/api/` |
| Training / evaluation / data scripts | `scripts/` |
| Tests | `tests/` |
| React frontend | `frontend/` |
| Attack/defend lab | `lab/` |

Reproduce the benchmark: `python -m scripts.train --out-dir models`.
