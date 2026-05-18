# LO3 — Professional Standard · Evidence Dossier

> **Learning outcome (verbatim):** *Both individually and in teams, you apply a
> relevant methodological approach used in the professional field to formulate
> project goals, involve stakeholders, conduct applied research, provide advice,
> make decisions, and deliver reports. In doing so, you keep in view the
> relevant ethical, intercultural, and sustainable aspects.*

**Student:** Angel Rusev · **Project:** Network Traffic Anomaly Detector ·
**Minor:** Cybersecurity — Attack & Defend (Fontys, Spring 2026)

---

## 1. Professional methodology — DOT framework + phased delivery

Two professional methodologies are used in combination:

1. **DOT framework (Development Oriented Triangulation)** — the applied-research
   methodology required by Fontys ICT.  Each of the six SRQs in the PRP is
   substantiated across at least two DOT method strategies (Library, Lab,
   Field, Workshop, Showroom). The full triangulation is documented in
   `docs/research/DOT_Research.md`.
2. **Phased delivery (Scrum-flavoured)** — the project is broken into the
   seven phases listed in the PRP §8, each tracked as a single GitHub issue
   with explicit deliverables and acceptance criteria. Phases 1–5 are
   implemented in this repository; phases 6–7 are open issues.

## 2. Project goals — formulated and traceable

| Layer                | Goal                                                                                                | Traceable to                            |
|----------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| Main research goal   | Detect cyber attacks in real time with low FP rate                                                  | PRP §3.1 / Main RQ                       |
| Sub research goals   | SRQ1–SRQ6 (features, algorithms, latency, threshold, presentation, per-class)                       | PRP §3.2 / `docs/research/DOT_Research.md` §2 |
| Engineering goal     | A reproducible, containerised microservice with ≤50 ms inference latency                            | PRP §5 + this repo                       |
| Operational goal     | An analyst-facing dashboard usable by a SOC operator with no ML background                           | PRP §4.3 D5                              |

## 3. Stakeholder involvement

| Stakeholder              | Interest                                              | How involved                                                                                                |
|--------------------------|--------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| Supervisor (Fontys)      | Methodological rigour + PRP fidelity                  | Reviews the DOT-framework document; comments on GitHub issues #1–7 (one issue per phase).                    |
| Hypothetical SOC analyst | Dashboard usability, severity model                  | "Persona shadowing" in SRQ5; usability checked against SIEM UI conventions in `Architecture_Review.md`.       |
| Peer student / reviewer  | Code-review feedback                                  | `Architecture_Review.md` is a workshop-style peer review checklist applied to the project itself.            |
| End user (NOC operator)  | Reliability and runbooks                              | Procedural runbooks (LO2 §3) drafted in language an operator can follow.                                     |

Stakeholder feedback channels (in order of asynchrony): GitHub issues → repository PRs → DOT Showroom strategy (live demo in the final assessment).

## 4. Applied research — conducted

The research is conducted in this repository and documented in
`docs/research/DOT_Research.md`. Every SRQ has:

* A literature anchor (Library strategy).
* A lab experiment with reproducible code (Lab strategy).
* A triangulating Field/Workshop/Showroom check.
* A concrete answer (§4.1–§4.6 of the DOT document).

The research **produces falsifiable claims** — e.g. "Gradient Boosting reaches
0.99 F1 on PortScan/BruteForce/Botnet/DoS/DDoS but only 0.35 on Infiltration".
Anyone can rerun `python -m scripts.train --data <csv>` and verify or
falsify the claim. That falsifiability is the difference between an opinion
and applied research.

## 5. Advice given to the (hypothetical) client

* **Strategic advice** in `LO1_Offensive_Security.md` §4 — physical / technical / organisational improvements.
* **Operational advice** in `LO2_Defensive_Security.md` §3 — procedural runbooks and drift handling.
* **Roadmap advice** in the README "Phasing" section + GitHub issues #6 / #7 (real-dataset evaluation, deep-learning extension).

## 6. Decisions and rationale (decision log)

| # | Decision                                                       | Rationale                                                                                              | Alternatives considered                |
|---|-----------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|----------------------------------------|
| D1 | Use the CICIDS2017 schema even when training on synthetic data | Future-proofs ingestion against the real dataset; aligns with the PRP §6 deliverable.                 | Custom schema (rejected — non-portable). |
| D2 | scikit-learn rather than a deep-learning framework             | Matches PRP §4.2 out-of-scope rule; keeps the project tractable; ships per-class output for free.      | PyTorch autoencoder (deferred to future work). |
| D3 | Streamlit over React for the dashboard                          | Delivers SRQ5 in days; analyst semantics identical; React option preserved as Phase 7 follow-up.       | React + Recharts (deferred, issue #5b). |
| D4 | SQLite over PostgreSQL                                          | Demo-grade scale; zero ops overhead; PostgreSQL upgrade path documented in `Architecture_Review.md`.   | PostgreSQL, MongoDB.                   |
| D5 | Persist the production model (GB) rather than the F1-leader (OC-SVM) | Supervised per-class output is required for SRQ5/SRQ6; tie-break rule encoded in `persist_best`.   | Persist OC-SVM (rejected — only binary). |
| D6 | Severity bucketing in addition to threshold                    | Two-layer FP control proven more effective in the literature; matches SIEM conventions.                 | Single threshold (rejected — too brittle). |

Every decision is implemented as code and visible in the repo, so it can be
audited rather than taken on trust.

## 7. Reports delivered

* `README.md` — service-level summary + phasing.
* `docs/research/DOT_Research.md` — research report (D1 of the PRP).
* `docs/architecture/Threat_Model.md` — D7 of the PRP (architecture documentation).
* `docs/architecture/Architecture_Review.md` — workshop-strategy peer review.
* `docs/evidence/LO1–LO4` — per-learning-outcome dossiers.

## 8. Ethical, intercultural, sustainable considerations

* **Ethical**: detector never ingests payloads; IPs pseudonymous; explicit lab-only deployment scope. See `Threat_Model.md` §3.
* **Intercultural**: documentation written in English-as-second-language plain English so it is accessible to international supervisors and peer reviewers. SIEM conventions referenced (Splunk/Elastic/Wazuh) come from a culturally diverse open-source community, not a single vendor's worldview.
* **Sustainable**: the chosen algorithms (Gradient Boosting, Random Forest) train in ≤1 minute on a laptop — orders of magnitude lower energy footprint than a deep-learning baseline. The PRP's explicit out-of-scope rule for deep learning is therefore also a *sustainability* decision, not just a scope-management one.

## 9. Mapping to the rubric

* "Apply a relevant methodological approach" ← DOT framework + phased delivery (§1).
* "Formulate project goals" ← §2.
* "Involve stakeholders" ← §3.
* "Conduct applied research" ← §4 + `docs/research/DOT_Research.md`.
* "Provide advice" ← §5 + LO1 §4 + LO2 §3.
* "Make decisions" ← §6 decision log.
* "Deliver reports" ← §7.
* "Ethical, intercultural, sustainable" ← §8.
