# Network Traffic Anomaly Detector

Personal Research Project (PRP) — Cybersecurity Minor: **Attack & Defend** (Fontys University of Applied Sciences,  Spring 2026)

**Author:** Angel Rusev · BSc ICT & Software Engineering · Minor: Cybersecurity — Attack & Defend

---

## TL;DR

A machine-learning powered Network Traffic Anomaly Detector that classifies flow-level network features in real time as **benign** or **anomalous** (with attack-type sub-classification). Built as a containerised microservice: **FastAPI** for inference + **Streamlit** dashboard for analyst-friendly alerting + **scikit-learn** ML engine trained on **CICIDS2017**-style features.

> Research vehicle for the **DOT framework** (Development Oriented Triangulation) and Fontys Cybersecurity LOs 1–4.

## Why this matters

Signature-based IDS (Snort, Suricata) misses zero-day and novel attacks. Anomaly-based detection complements them by learning what *normal* looks like and flagging deviation — but typically at the cost of high false-positive rates. This project investigates how to balance detection rate vs. false-positive rate using classical ML, with a strict scope boundary against deep learning (reserved as future work).

## Main Research Question

> How can a machine-learning-based network-traffic anomaly detector be designed and implemented to accurately identify cyber attacks in real time while maintaining an acceptable false-positive rate?

See [`docs/research/DOT_Research.md`](docs/research/DOT_Research.md) for the full sub-research-question breakdown, DOT method matrix, and substantiation of every architectural decision.

## Demo at a glance

| Component                | Tech                                              |
|--------------------------|---------------------------------------------------|
| Traffic ingestion        | Python + Scapy / CICFlowMeter-compatible CSVs     |
| Feature pipeline         | Pandas + NumPy (80-feature CIC-flow schema)        |
| ML engine                | scikit-learn (RF, Isolation Forest, One-Class SVM, Gradient Boosting) |
| API layer                | FastAPI + Pydantic v2                              |
| Dashboard                | Streamlit (severity, per-attack, drift)            |
| Datastore                | SQLite (alerts, runs, model registry)              |
| Orchestration            | Docker Compose                                     |

```
┌──────────────┐   flows     ┌──────────────┐   features   ┌────────────┐   verdict   ┌────────────┐
│  PCAP / CSV  │ ──────────► │  Feature     │ ───────────► │  FastAPI   │ ──────────► │ Dashboard  │
│  ingestion   │             │  pipeline    │              │  /predict  │             │ (Streamlit)│
└──────────────┘             └──────────────┘              └─────┬──────┘             └────────────┘
                                                                 │
                                                                 ▼
                                                         ┌──────────────┐
                                                         │   SQLite     │
                                                         │ alerts/runs  │
                                                         └──────────────┘
```

## Phasing (14 weeks, 7 phases)

| # | Phase                  | Period   | Key activities                                                              | Deliverables               | Tracked by             |
|---|------------------------|----------|-----------------------------------------------------------------------------|----------------------------|------------------------|
| 1 | Literature & Setup     | W1–W2    | Anomaly-detection lit review, CICIDS2017 exploration, dev environment       | SRQ1/SRQ2 lit, Docker env  | Issue #1               |
| 2 | Feature Engineering    | W3–W4    | Pre-processing, feature extraction pipeline, feature importance             | D2 pipeline, SRQ1 answer   | Issue #2               |
| 3 | Model Training         | W5–W6    | Train + tune 4+ algorithms, CV, comparison matrix                           | D3 models, SRQ2 answer     | Issue #3               |
| 4 | API Development        | W7–W8    | FastAPI backend, real-time `/predict`, threshold tuning                     | D4 API, SRQ3/SRQ4 answers  | Issue #4               |
| 5 | Dashboard              | W9–W10   | Streamlit UI, severity scoring, analyst usability                           | D5 UI, SRQ5 answer         | Issue #5               |
| 6 | Evaluation             | W11–W12  | Per-attack-category metrics, latency benchmarks, FP analysis                | SRQ6 answer, D7 docs       | Issue #6               |
| 7 | Documentation          | W13–W14  | Research report, user guide, final presentation                             | D1, D8, D6                 | Issue #7               |

Status: phases 1–5 implementation complete in this repository (the rest are tracked as issues for continued work).

## Repository layout

```
AnomalyDetector/
├── src/anomaly_detector/
│   ├── features/        # Flow feature extraction + preprocessing
│   ├── models/          # Train, evaluate, registry
│   ├── api/             # FastAPI app, routes, dependencies
│   └── schemas/         # Pydantic request/response models
├── dashboard/           # Streamlit dashboard
├── scripts/             # CLI utilities (train, generate-data, ingest)
├── data/
│   ├── raw/             # CICIDS2017 / synthetic raw CSVs
│   └── processed/       # Cleaned + feature-engineered datasets
├── models/              # Serialised trained models (.joblib) + metadata
├── docs/
│   ├── research/        # DOT-framework research document
│   ├── evidence/        # LO1–LO4 evidence dossiers
│   ├── architecture/    # C4 diagrams, threat model
│   └── screenshots/     # Demo screenshots used in evidence
├── notebooks/           # Exploratory analysis
├── tests/               # pytest suite
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.dashboard
└── requirements.txt
```

## Quickstart

```bash
# 1) Install (Python 3.10+)
python -m venv .venv
.venv\Scripts\activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2) Generate a synthetic CICIDS-style dataset (if you don't have the real one)
python -m scripts.generate_synthetic_dataset --rows 20000 --out data/raw/synthetic_flows.csv

# 3) Train all four algorithms and write the comparison matrix
python -m scripts.train --data data/raw/synthetic_flows.csv --out-dir models

# 4) Run the API
uvicorn anomaly_detector.api.main:app --host 0.0.0.0 --port 8000 --reload

# 5) Run the dashboard (separate terminal)
streamlit run dashboard/app.py
```

Or with Docker:

```bash
docker compose up --build
# API:        http://localhost:8000/docs
# Dashboard:  http://localhost:8501
```

## Research output — DOT framework

The `docs/research/DOT_Research.md` document substantiates every methodological choice using the [DOT framework](https://ictresearchmethods.nl/dot-framework/) (Library, Lab, Field, Workshop, Showroom). Each of the six SRQs is mapped to one or more DOT method strategies with concrete sources, experiments, and findings.

## Learning-outcome evidence

Per-LO evidence dossiers live in `docs/evidence/`:

- **LO1 — Offensive Security**: [`docs/evidence/LO1_Offensive_Security.md`](docs/evidence/LO1_Offensive_Security.md)
- **LO2 — Defensive Security**: [`docs/evidence/LO2_Defensive_Security.md`](docs/evidence/LO2_Defensive_Security.md)
- **LO3 — Professional Standard**: [`docs/evidence/LO3_Professional_Standard.md`](docs/evidence/LO3_Professional_Standard.md)
- **LO4 — Personal Leadership**: [`docs/evidence/LO4_Personal_Leadership.md`](docs/evidence/LO4_Personal_Leadership.md)

## Ethics & responsible use

This is a defensive-research artefact built and tested in a lab/simulated environment. The threat model, data-handling rules, and ethical boundaries are documented in [`docs/architecture/Threat_Model.md`](docs/architecture/Threat_Model.md) and in the LO1/LO2 evidence dossiers.

## License

Educational / research use — see [`LICENSE`](LICENSE).
