"""Create GitHub issues for the AnomalyDetector PRP via the `gh` CLI.

All issues use TLDR-style bodies. One issue per PRP phase, plus security
hardening + roadmap follow-ups. Idempotent: skips creating issues whose title
already exists in the repo.
"""
from __future__ import annotations

import json
import subprocess
import sys

REPO = "Guts1313/AnomalyDetector"

LABELS = [
    {"name": "phase", "color": "1d4ed8", "description": "PRP phase delivery"},
    {"name": "research", "color": "8b5cf6", "description": "DOT research / SRQ"},
    {"name": "security", "color": "dc2626", "description": "Security hardening / threat model"},
    {"name": "roadmap", "color": "10b981", "description": "Future phase / out-of-scope"},
    {"name": "good-first-issue", "color": "fbbf24", "description": "Good entry point"},
]

ISSUES: list[dict] = [
    # --- PRP phases ---
    {
        "title": "[Phase 1] Literature & Setup (W1-W2)",
        "labels": ["phase", "research"],
        "body": """TL;DR: Lit review on anomaly detection, dataset exploration, dev environment.

- [x] Read Sharafaldin 2018, Liu 2008, Chandola 2009, Ring 2019.
- [x] Map references into `docs/research/DOT_Research.md` section 7.
- [x] Decide CIC-flow feature subset (`schema.py`).
- [x] Docker dev environment (`Dockerfile.api` + `Dockerfile.dashboard`).
- [x] CI workflow (`.github/workflows/ci.yml`).

**Acceptance:** Phase delivers SRQ1/SRQ2 literature notes + working dev env.""",
    },
    {
        "title": "[Phase 2] Feature Engineering Pipeline (W3-W4)",
        "labels": ["phase", "research"],
        "body": """TL;DR: Build the 20-feature flow pipeline with median imputation + RobustScaler + OHE.

- [x] `FLOW_FEATURE_COLUMNS` defined.
- [x] `build_default_pipeline()` implemented.
- [x] Robustness tests (NaN/inf) in `tests/test_features.py`.
- [x] Synthetic CICIDS dataset generator (`scripts/generate_synthetic_dataset.py`).

**Acceptance:** SRQ1 answer published; pipeline is reused unchanged at inference time.""",
    },
    {
        "title": "[Phase 3] Model Training & Comparison (W5-W6)",
        "labels": ["phase", "research"],
        "body": """TL;DR: Train 4 algorithms (Random Forest, Gradient Boosting, Isolation Forest, One-Class SVM); publish the comparison matrix.

- [x] All 4 algorithms in `src/anomaly_detector/models/trainers.py`.
- [x] Comparison matrix CSV + Markdown in `models/`.
- [x] Best-model selection rule (supervised tie-break for analyst-facing per-class output).
- [x] Algorithm comparison chart (`docs/screenshots/04_algo_comparison.png`).

**Acceptance:** SRQ2 answer with concrete F1/AUC/latency numbers.""",
    },
    {
        "title": "[Phase 4] FastAPI Backend + Threshold Tuning (W7-W8)",
        "labels": ["phase"],
        "body": """TL;DR: REST API with predict, health, metrics, alerts, audit, admin reload + threshold parameter.

- [x] `/predict`, `/predict/csv`, `/health`, `/metrics`, `/alerts`, `/predictions`, `/admin/reload`.
- [x] Pydantic v2 schemas with severity bucketing.
- [x] SQLite audit store.
- [x] OpenAPI/Swagger at `/docs` (see `docs/screenshots/02_api_swagger.png`).

**Acceptance:** SRQ3 (latency) + SRQ4 (threshold) answers backed by measurements.""",
    },
    {
        "title": "[Phase 5] Streamlit Analyst Dashboard (W9-W10)",
        "labels": ["phase"],
        "body": """TL;DR: Severity ribbon, attacks-by-class donut, manual scoring, audit table.

- [x] Overview tab with metrics + charts.
- [x] Alerts tab with sortable severity-coloured table.
- [x] Manual scoring tab with class probabilities.
- [x] About tab disclosing active model + dataset.

**Acceptance:** SRQ5 answer + screenshot `docs/screenshots/01_dashboard_overview.png`.""",
    },
    {
        "title": "[Phase 6] Evaluation on real CICIDS2017 + per-category benchmark (W11-W12)",
        "labels": ["phase", "research"],
        "body": """TL;DR: Replace the synthetic dataset with the real CICIDS2017 and re-run the matrix.

- [ ] Download & cache the official CICIDS2017 CSVs.
- [ ] Re-run `scripts/train.py` against the real dataset.
- [ ] Refresh `models/comparison_matrix.*` and the per-class report.
- [ ] Update the SRQ6 section of `docs/research/DOT_Research.md` with real-dataset numbers.

**Acceptance:** comparison matrix and per-class confusion matrix on the real dataset, committed to the repo.""",
    },
    {
        "title": "[Phase 7] Final report + user guide + presentation (W13-W14)",
        "labels": ["phase"],
        "body": """TL;DR: Polish docs, write the user guide, prepare the final defence.

- [ ] Export `docs/research/DOT_Research.md` to PDF for submission.
- [ ] Write `docs/User_Guide.md` (installation, configuration, ops runbooks).
- [ ] Record a 5-minute demo video.
- [ ] Slide deck for the showroom defence.

**Acceptance:** D1 (Report) + D8 (User Guide) committed.""",
    },

    # --- Open SRQs ---
    {
        "title": "[SRQ6] Confirm per-category performance on real CICIDS2017",
        "labels": ["research"],
        "body": """TL;DR: Synthetic per-class F1 has been measured; need real-dataset confirmation.

Current synthetic results:

- PortScan / BruteForce: 1.00
- BENIGN / DoS / DDoS / Botnet: 0.99
- WebAttack: 0.95
- **Infiltration: 0.35** (the smallest class)

Hypothesis: Infiltration F1 will remain the lowest class on the real dataset (n=36 in CICIDS2017 Thursday capture).

**Acceptance:** real-dataset confusion matrix and per-class F1 in `docs/research/DOT_Research.md` section 4.6.""",
    },

    # --- Security hardening ---
    {
        "title": "[Security] Verify model bundle hash before /admin/reload",
        "labels": ["security"],
        "body": """TL;DR: Mitigation for STRIDE-T2 (model tampering).

- [ ] Compute SHA-256 of `best.joblib` at training time; write to `models/best.sha256`.
- [ ] On `POST /admin/reload`, recompute and compare; refuse on mismatch.
- [ ] Document the chain-of-custody in `docs/architecture/Threat_Model.md` section 4.

**Acceptance:** integration test asserts a tampered bundle is rejected with HTTP 409.""",
    },
    {
        "title": "[Security] Upstream rate-limit (nginx / traefik) for /predict",
        "labels": ["security", "good-first-issue"],
        "body": """TL;DR: Mitigation for STRIDE-T5 (DoS via oversized batches).

- [ ] Add a sample `nginx.conf` with `limit_req_zone` rules.
- [ ] Add a Docker Compose profile `with-proxy`.
- [ ] Document the deployment recipe in `docs/architecture/Threat_Model.md`.

**Acceptance:** `docker compose --profile with-proxy up` brings the proxy + API together.""",
    },
    {
        "title": "[Security] Encrypted-traffic blind-spot mitigation (TLS metadata heuristics)",
        "labels": ["security", "research"],
        "body": """TL;DR: SR7 in the LO1 risk register — encrypted payloads carry less flow-level signal.

- [ ] Survey TLS-metadata features: JA3 fingerprints, SNI rarity, certificate age.
- [ ] Prototype a lightweight metadata-only sub-classifier.
- [ ] Document the gap-closure plan in `docs/evidence/LO1_Offensive_Security.md` section 4.

**Acceptance:** prototype tested against the dataset and a design write-up committed.""",
    },

    # --- Roadmap / future work ---
    {
        "title": "[Roadmap] PostgreSQL audit store",
        "labels": ["roadmap"],
        "body": """TL;DR: SQLite is fine for the demo; PostgreSQL is the production target (D6).

- [ ] Add SQLAlchemy + Alembic.
- [ ] Migrate the `predictions` table.
- [ ] Add a Docker Compose profile.

**Acceptance:** dashboard reads the same metrics from PostgreSQL via the API.""",
    },
    {
        "title": "[Roadmap] OpenTelemetry instrumentation",
        "labels": ["roadmap"],
        "body": """TL;DR: Tracing + structured logging for SOC-grade observability.

- [ ] Wrap the FastAPI app with OpenTelemetry.
- [ ] Export traces to a local Jaeger/Tempo container.
- [ ] Add a Compose profile.

**Acceptance:** every `/predict` request produces a traced span with attributes for verdict + severity.""",
    },
    {
        "title": "[Roadmap] React dashboard (multi-user)",
        "labels": ["roadmap"],
        "body": """TL;DR: Streamlit is single-user by design; the React variant remains the optional D5 alternative.

- [ ] Vite + React + Recharts scaffold.
- [ ] Auth (NextAuth or Auth0).
- [ ] Feature parity with Streamlit's Overview / Alerts / Manual scoring tabs.

**Acceptance:** the React app talks to the same FastAPI backend.""",
    },
    {
        "title": "[Roadmap] Autoencoder / LSTM baseline (deep-learning, future work)",
        "labels": ["roadmap", "research"],
        "body": """TL;DR: Deep-learning baseline — out-of-scope per PRP section 4.2, deferred to future work.

- [ ] PyTorch reconstruction-error autoencoder.
- [ ] Compare against the Gradient Boosting winner on the real CICIDS2017.
- [ ] Document in `docs/research/DOT_Research.md` section 4.2 alternatives.

**Acceptance:** comparison row appended to `models/comparison_matrix.csv`.""",
    },
]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def existing_issue_titles(repo: str) -> set[str]:
    res = run(["gh", "issue", "list", "--repo", repo, "--state", "all", "--limit", "500", "--json", "title"])
    if res.returncode != 0:
        return set()
    try:
        items = json.loads(res.stdout)
    except json.JSONDecodeError:
        return set()
    return {it["title"] for it in items}


def ensure_labels(repo: str) -> None:
    for lbl in LABELS:
        run(
            [
                "gh", "label", "create",
                lbl["name"],
                "--color", lbl["color"],
                "--description", lbl["description"],
                "--repo", repo,
            ]
        )


def create_issue(repo: str, title: str, body: str, labels: list[str]) -> tuple[bool, str]:
    args = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
    for lab in labels:
        args.extend(["--label", lab])
    res = run(args)
    if res.returncode != 0:
        return False, res.stderr.strip() or res.stdout.strip()
    return True, res.stdout.strip()


def main() -> None:
    ensure_labels(REPO)
    existing = existing_issue_titles(REPO)
    created, skipped, failed = 0, 0, 0
    for issue in ISSUES:
        if issue["title"] in existing:
            print(f"[skip] {issue['title']} (already exists)")
            skipped += 1
            continue
        ok, msg = create_issue(REPO, issue["title"], issue["body"], issue["labels"])
        if ok:
            print(f"[ ok ] {issue['title']} -> {msg}")
            created += 1
        else:
            print(f"[fail] {issue['title']} :: {msg}", file=sys.stderr)
            failed += 1
    print(f"\nDone — created {created}, skipped {skipped}, failed {failed}")


if __name__ == "__main__":
    main()
