# Architecture review — Workshop strategy (DOT)

This document captures the *workshop* leg of the DOT-framework triangulation
for SRQ3 — designing the system for real-time inference. It is a peer-style
review of the architecture decisions taken in this repository, executed as a
self-checklist against a published reference (FastAPI patterns documentation
and Microsoft's "Azure ML reference architecture for online inference").

## Decisions reviewed

| # | Decision                                                                                 | Pros                                                                                              | Cons / risks                                                                                              | Verdict |
|---|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|---------|
| 1 | **Persist the fitted ColumnTransformer with the model in a single joblib bundle**         | Guarantees train/inference parity (eliminates a classical FP source).                              | Bundle is larger; reloading after retraining requires a process restart or `/admin/reload`.                 | ✅ Accept |
| 2 | **Stateless `/predict` endpoint, audit logging written *after* the verdict**             | Critical-path latency stays bounded; failure to log does not block the analyst from getting a verdict. | An ingest spike with a slow disk could fill the in-process queue; mitigated by SQLite's write speed.       | ✅ Accept |
| 3 | **Batch-first API (`/predict` always accepts a list of flows)**                          | Vectorised scikit-learn predict is ~3× faster than a Python loop.                                  | Per-flow error handling is uniform per batch — one malformed flow rejects the whole request.               | ✅ Accept |
| 4 | **SQLite for the audit store (rather than PostgreSQL as PRP §5 mentions)**                | Zero operational overhead; trivial to ship in Docker; perfectly adequate for the demo scope.       | Will not scale to multi-writer production; PRP risk R4 documents PostgreSQL upgrade path as future work.    | ✅ Accept |
| 5 | **Streamlit dashboard (rather than the React option listed in PRP)**                     | Delivers SRQ5 in days, not weeks; analyst-facing semantics are identical; full Plotly support.    | Sessions are not multi-user out of the box; React option remains documented as Phase 7 follow-up work.     | ✅ Accept |
| 6 | **Docker Compose orchestration, two-image split (API + dashboard)**                       | Each can be scaled independently; image sizes stay small; healthchecks supported.                  | Slightly heavier on Cold-start than a single image.                                                        | ✅ Accept |
| 7 | **Non-root container users (`detector`, `dash`)**                                         | Least-privilege; mitigates T6 of the threat model.                                                | Volume mount permissions need explicit handling in `docker-compose.yml`.                                  | ✅ Accept |

## Code-review checklist (applied)

* [x] Public functions documented with intent (why, not what).
* [x] Pipeline composability: train and inference share the same `FeaturePipeline` instance.
* [x] No mutable global state outside the registry + alert store.
* [x] Error responses are explicit HTTP codes (400 for malformed input, 503 when the model bundle is missing).
* [x] Tests exist for the feature pipeline (incl. inf/NaN robustness) and the API surface (happy path + attack flow + threshold).
* [x] CI runs the full train→serve→smoke-test loop on a 4 000-row dataset.
* [x] Synthetic dataset is reproducible — pinned seed in `scripts/generate_synthetic_dataset.py`.
* [x] All container images run as non-root.
* [x] No secrets committed; LICENSE file present.

## Open items (logged as GitHub issues)

* Replace SQLite with PostgreSQL when running outside the demo (`#9`).
* Rate-limit the API with an upstream reverse-proxy (`#11`).
* Train and evaluate against the *real* CICIDS2017 dataset (`#6`).
* Optional React frontend for multi-user deployments (`#5b` — Phase 7 follow-up).
