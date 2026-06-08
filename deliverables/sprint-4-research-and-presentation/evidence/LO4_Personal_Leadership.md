# LO4 — Personal Leadership · Evidence Dossier

> **Learning outcome (verbatim):** *You are aware of your own strengths and
> weaknesses, both in the field of ICT and in your personal development. You
> choose actions in line with your core values to promote your personal growth
> and develop your learning attitude.*

**Student:** Angel Rusev · **Project:** Network Traffic Anomaly Detector ·
**Minor:** Cybersecurity — Attack & Defend (Fontys, Spring 2026)

---

## 1. Self-assessment going into the project

| Area                              | Self-rating (1–5) | Comment                                                                                                   |
|-----------------------------------|--------------------|------------------------------------------------------------------------------------------------------------|
| Python + scikit-learn             | 4                  | Comfortable from the main programme — picked it as the project's primary language.                          |
| FastAPI / REST API design          | 4                  | Used FastAPI in previous projects; expected the API to be the easy part.                                    |
| Container orchestration            | 3                  | Familiar with Docker basics; multi-image Compose with healthchecks was a stretch goal.                      |
| Network forensics / CICIDS dataset | 2                  | New territory from the minor — biggest learning area.                                                       |
| Anomaly-detection algorithms       | 2                  | Knew supervised ML; Isolation Forest and One-Class SVM were new.                                            |
| Research-writing in the DOT style  | 3                  | Familiar with the framework from prior semesters; new in combination with a security-focused topic.        |
| Time management on a 14-week PRP   | 3                  | Comfortable on shorter sprints; needed to discipline the 7-phase plan.                                      |

## 2. Core values that guided the project

* **Falsifiability over confidence.** Claims in the research document are made with reproducible commands attached. The Infiltration F1 = 0.35 is *not* hidden — it's spotlighted in the SRQ6 answer because honesty about a model's limits is more useful than optimistic marketing.
* **Bias toward shipping.** Streamlit was picked over React (D3 in `LO3_Professional_Standard.md` §6) explicitly to get the analyst tool in front of stakeholders sooner. A working SOC dashboard in week 9 is more valuable than a polished React app in week 14.
* **Defensive-mindedness over offensive flash.** The PRP is positioned as a detection tool, not a red-team toy. The threat model takes the detector itself as a target and the synthetic dataset doesn't include any "live-fire" exploit details.

## 3. Strengths I leaned on

* Strong Python + ML pipeline experience let me parallelise feature pipeline + 4-algorithm training in days rather than weeks, which freed time for the research document.
* Comfortable with FastAPI → the API was effectively a sprint-zero deliverable. Reusing that comfort gave headroom for the unfamiliar parts (threat modelling, DOT triangulation).

## 4. Weaknesses I confronted

| Weakness                                                                       | Action taken                                                                                                  | Outcome                                                                                  |
|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| Less experience with network-traffic features and CICFlowMeter feature catalogue | Read Sharafaldin et al. 2018 and Ring et al. 2019 end-to-end; tabulated the canonical 20-feature subset.       | `schema.py` + `pipeline.py` with documented rationale for each design choice.            |
| Limited prior exposure to threat modelling                                      | Used STRIDE as the simplest professional method; cross-walked against MITRE ATT&CK tactics the detector spots. | `Threat_Model.md` with 8 STRIDE rows + per-tactic mapping.                                |
| Tendency to over-engineer (e.g. wanting to ship a React app from day 1)         | Wrote the decision log (`LO3_Professional_Standard.md` §6) and forced myself to justify every "extra" feature. | 6 explicit decisions in the log, two of which deferred work to future phases.            |
| Comfort with English technical writing but not always concise                    | Adopted a "TL;DR + table" pattern at the top of every doc to discipline myself.                                | Each document opens with a one-paragraph TL;DR and a navigation table.                    |

## 5. Learning-attitude actions

* **Active feedback loop** — every phase is a GitHub issue with explicit acceptance criteria, so I get feedback from the supervisor against a stable spec instead of a moving target.
* **Reproducibility as a teaching tool** — `python -m scripts.generate_synthetic_dataset && python -m scripts.train` reproduces the comparison matrix in <2 minutes. If someone wants to challenge a claim, the script is there.
* **Code review as self-development** — the workshop-style peer-review checklist in `Architecture_Review.md` is essentially me reviewing my own work against an external standard.

## 6. Personal growth — concrete deltas

Comparing the self-rating in §1 with the post-project state:

| Area                              | Pre | Post | Delta |
|-----------------------------------|-----|------|-------|
| Python + scikit-learn             | 4   | 4    | 0 (already strong)                                              |
| FastAPI / REST API design          | 4   | 5    | +1 (now confident with Pydantic v2 + DI patterns)               |
| Container orchestration            | 3   | 4    | +1 (multi-image Compose with healthchecks + non-root)            |
| Network forensics / CICIDS dataset | 2   | 4    | +2 (biggest delta — flow-feature schema is now second nature)    |
| Anomaly-detection algorithms       | 2   | 4    | +2 (4-algorithm comparison + understanding of family trade-offs)  |
| Research-writing in the DOT style  | 3   | 5    | +2 (DOT triangulation now an instinct, not a checklist)          |
| Time management on a 14-week PRP   | 3   | 4    | +1 (phased delivery + issue tracking kept the project on rails)   |

## 7. Next-step development plan

Based on the deltas above the next-step plan picks three areas:

1. **Adversarial ML** — currently a documented gap (Infiltration F1 = 0.35 and SR1/SR7 in the LO1 risk register). I'll allocate the next semester's elective to MLSec / adversarial-robustness reading.
2. **Production-grade observability** — replace SQLite with PostgreSQL + structured logging + OpenTelemetry; tracked as issues #9 and #10.
3. **Communication** — practice 5-minute technical demos using the dashboard as a tangible artefact; rehearse the showroom defence.

## 8. Mapping to the rubric

* "Aware of strengths and weaknesses" ← §1 self-rating + §6 deltas.
* "ICT and personal development" ← §3 + §4 (technical + personal).
* "Choose actions in line with core values" ← §2 + §5.
* "Promote personal growth" ← §4 actions + §6 deltas.
* "Develop learning attitude" ← §5 + §7 next-step plan.
