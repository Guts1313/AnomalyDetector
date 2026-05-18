# Evidence index — Learning Outcomes 1-4

This folder is the **portfolio dossier** for the Fontys Cybersecurity Attack &
Defend learning outcomes. Each LO has its own document; the table below maps
each LO to the artefacts that support it.

| LO  | Title                  | Dossier file                                   | Supporting artefacts in this repo                                                                                  |
|-----|------------------------|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| LO1 | Offensive Security      | [`LO1_Offensive_Security.md`](LO1_Offensive_Security.md) | `docs/architecture/Threat_Model.md` (STRIDE + risk × likelihood matrix), `scripts/generate_synthetic_dataset.py` (per-attack signatures). |
| LO2 | Defensive Security      | [`LO2_Defensive_Security.md`](LO2_Defensive_Security.md) | FastAPI service, SQLite audit store, Streamlit dashboard, Docker hardening, procedural runbooks.                  |
| LO3 | Professional Standard   | [`LO3_Professional_Standard.md`](LO3_Professional_Standard.md) | `docs/research/DOT_Research.md` (DOT triangulation), README phasing, GitHub issues per phase, decision log.       |
| LO4 | Personal Leadership     | [`LO4_Personal_Leadership.md`](LO4_Personal_Leadership.md) | Pre/post self-assessment, decision-log discipline, reproducibility-as-pedagogy.                                    |

## How to read this dossier

1. Start with the **README** of the project for the engineering context.
2. Read **`docs/research/DOT_Research.md`** for the substantive research (all six SRQs with triangulated answers).
3. Read **the LO dossiers in this folder** for the rubric-mapped evidence.
4. Check **`docs/screenshots/`** for the visual evidence of the working demo.
5. Browse the **GitHub issues** of this repository for the phased delivery history.

## Reproducing the evidence

```bash
python -m scripts.generate_synthetic_dataset --rows 20000 --out data/raw/synthetic_flows.csv
python -m scripts.train --data data/raw/synthetic_flows.csv --out-dir models
python -m scripts.make_research_charts
uvicorn anomaly_detector.api.main:app --host 0.0.0.0 --port 8000 &
streamlit run dashboard/app.py
python -m scripts.demo_traffic --n-batches 15 --batch 30
```

After this sequence:

* `models/comparison_matrix.csv` + `.md` = the SRQ2 deliverable.
* `models/per_class_report.json` = the SRQ6 deliverable.
* `docs/screenshots/04`–`06` = the auto-generated research charts.
* `docs/screenshots/01`–`03` = the live-system screenshots (dashboard + API docs + JSON).
