# Project plan — Network Traffic Anomaly Detector

**Student:** Angel Rusev · **Minor:** Cybersecurity — Attack & Defend · Fontys, Spring 2026
**Phase:** Define & Analyse · **Sprint 1 hand-in:** 26 March 2026

## 1. Goal

Design and build a machine-learning network-traffic anomaly detector that
identifies cyber attacks in real time while keeping the analyst-visible
false-positive rate low, and demonstrate it inside a real attack/defend lab.

## 2. Research questions

**Main RQ:** How can a machine-learning-based network-traffic anomaly detector be
designed and implemented to accurately identify cyber attacks in real time while
maintaining an acceptable false-positive rate?

| SRQ | Question | DOT strategies |
|---|---|---|
| SRQ1 | Which flow features are most indicative of anomalous behaviour, and how extracted? | Library + Lab |
| SRQ2 | Which ML algorithms balance accuracy, speed and false positives best? | Library + Lab + Showroom |
| SRQ3 | How can it run in real time without unacceptable latency? | Lab + Workshop |
| SRQ4 | What threshold/tuning strategies minimise false positives? | Lab |
| SRQ5 | How should anomalies be presented to analysts? | Library + Field + Showroom |
| SRQ6 | How does it perform across attack categories? | Lab |

## 3. Methodology — DOT framework

The project uses Development-Oriented Triangulation (DOT), triangulating each
conclusion across at least three method strategies: **Library** (literature +
product analysis), **Lab** (feature engineering, benchmarking, the live lab),
**Field** (SOC-analyst persona + SIEM conventions), **Workshop** (architecture
review), **Showroom** (live demonstration). Delivery is Scrum-flavoured across
four sprints.

## 4. Sprint plan

| Sprint | Dates | Phase | Primary outputs |
|---|---|---|---|
| 1 | 17–26 Mar | Define & Analyse | Project plan, user stories, Scrum board, trend analysis |
| 2 | 26 Mar–13 Apr | Design & Implement | Feature schema, dataset generator, 4-algorithm benchmark, FastAPI PoC, network drawing, flowcharts, technical design, attack scenarios |
| 3 | 13 Apr–11 May | Optimise & Validate | Threshold/severity tuning, per-class evaluation, tests, dashboards, attack/defend lab, validation |
| 4 | 11 May–11 Jun | Deliver | Research document, advisory report, presentation |

See `planning/gantt.png` for the work-item-level timeline.

## 5. Scope

**In scope:** flow-level features; supervised + unsupervised algorithm benchmark;
real-time inference API; analyst dashboards (React + Streamlit); containerised
attack/defend lab; eight-class evaluation.
**Out of scope:** deep-learning baselines; payload/DPI inspection; multi-writer
production storage. Tracked as future work.

## 6. Risks (initial register)

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Class imbalance biases the model | Stratified split; per-class evaluation; transparent reporting |
| R2 | Latency too high for "real time" | Stateless, batch-first inference; latency benchmark |
| R3 | High false-positive rate | Two-layer control: threshold + severity bucketing |
| R4 | Flow-level blind spots (e.g. infiltration) | Name the limitation; recommend pairing with signature IDS |
| R5 | Scope creep (deep learning, React from day 1) | Decision log; defer to future phases |

## 7. Stakeholders

Supervisor (methodological rigour), hypothetical SOC analyst (usability),
peer reviewer (architecture review), NOC operator (runbooks). See the user
stories and the Sprint 2 Technical Design Document for the persona detail.
