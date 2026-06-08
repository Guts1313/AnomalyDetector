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
├── frontend/            # React + TypeScript SPA (Vite, light/dark themes)
├── lab/                 # Attack/defend lab (attacker + defender containers)
├── scripts/             # CLI utilities (train, capture, diagram + doc builders)
├── data/
│   ├── raw/             # CICIDS2017 / synthetic raw CSVs
│   └── processed/       # Cleaned + feature-engineered datasets
├── models/              # Serialised trained models (.joblib) + metadata
├── docs/
│   ├── research/        # DOT-framework research document
│   ├── evidence/        # LO1–LO4 evidence dossiers
│   ├── architecture/    # threat model, architecture review
│   ├── demo/            # demo-attack-block.mp4 (Git LFS)
│   ├── screenshots/     # diagrams + frontend captures used in evidence
│   └── Research_Report.pdf
├── additional-docs/     # Technical Design Document + user stories (HTML)
├── deliverables/        # Per-sprint hand-in deliverables (one folder per sprint)
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

## Deliverables & key documents

Hand-in deliverables are organised per sprint under [`deliverables/`](deliverables/), each with its own README manifest. The headline documents:

| Document | Type | Where |
|---|---|---|
| **PRP project proposal** (initial idea & definition) | Word | [`deliverables/.../PRP_Project_Proposal.docx`](deliverables/sprint-0-initial-idea-2026-03-17/PRP_Project_Proposal.docx) |
| **DOT-framework research** (the proof / substantiation) | Markdown | [`docs/research/DOT_Research.md`](docs/research/DOT_Research.md) |
| **Research Report** (final, ~44 pp) | PDF | [`docs/Research_Report.pdf`](docs/Research_Report.pdf) |
| **Technical Design Document** | Word/PDF | [`additional-docs/Technical_Design_Document.docx`](additional-docs/Technical_Design_Document.docx) |
| **User stories** (12 across 6 epics) | HTML + PNG | [`additional-docs/user_stories.html`](additional-docs/user_stories.html) |
| **Project plan + Gantt** | Markdown + PNG | [`deliverables/sprint-1-define-and-analyse-2026-03-26/`](deliverables/sprint-1-define-and-analyse-2026-03-26/) |
| **Attack scenarios** | Markdown | [`deliverables/sprint-2-design-and-implement-2026-04-13/Attack_Scenarios.md`](deliverables/sprint-2-design-and-implement-2026-04-13/Attack_Scenarios.md) |
| **Validation report + test results** | Markdown + charts | [`deliverables/sprint-3-optimise-and-validate-2026-05-11/`](deliverables/sprint-3-optimise-and-validate-2026-05-11/) |
| **Advisory report** | Markdown | [`deliverables/sprint-4-research-and-presentation/Advisory_Report.md`](deliverables/sprint-4-research-and-presentation/Advisory_Report.md) |
| **Presentation deck** | PowerPoint | [`docs/AnomalyDetector-Presentation.pptx`](docs/AnomalyDetector-Presentation.pptx) |

### Live demo (attack → detect → auto-block)

A screen recording of the full attack/defend loop — real tool launched from the UI, captured, classified, and the attacker auto-blocked by `iptables` — is in [`docs/demo/demo-attack-block.mp4`](docs/demo/demo-attack-block.mp4) (Git LFS). See [`docs/demo/README.md`](docs/demo/README.md).

### Diagrams

Styled **C4** [context](docs/screenshots/21_c4_context.png) and [container](docs/screenshots/img-fixed.png) diagrams, the [attack→detect→block sequence](docs/screenshots/24_attack_defend_sequence.png), the [security risk heat-map](docs/screenshots/25_risk_heatmap.png), the [dataset/feature fingerprint](docs/screenshots/26_dataset_fingerprint.png) and the [delivery Gantt](docs/screenshots/20_gantt.png) live in `docs/screenshots/`. They are mapped to the learning outcomes in the LO dossiers below.

> The system also ships a polished **React + TypeScript** frontend (light & dark themes) alongside the Streamlit dashboard, and a containerised **attack/defend lab** (`lab/`) that drives real `nmap`/`hping3`/`hydra`/`sqlmap` traffic through the detector.

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
