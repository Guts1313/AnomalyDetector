# Threat Model & Architecture

This document is the **D7 deliverable** of the PRP — architecture documentation
including a threat model. It supports LO1 (Offensive Security — methodical
threat analysis) and LO2 (Defensive Security — non-functional requirements:
security, monitoring, ethics, compliance, usability).

## 1. C4 — Context

The system is a single-purpose internal analytic for a hypothetical Network
Operations Centre (NOC).

```
              ┌────────────────────────────────────────────────────┐
              │             NOC / SOC environment                  │
              │                                                    │
   PCAP/CSV ──┼──► [Ingestion] ─► [Anomaly Detector] ─► [Dashboard]│
              │       (offline)        (FastAPI)        (Streamlit)│
              │                            │                       │
              │                            ▼                       │
              │                       [Alert store]                │
              │                        (SQLite)                    │
              └────────────────────────────────────────────────────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │ Security        │
                              │ analyst         │
                              └────────────────┘
```

* **Primary actor:** Security analyst (consumes the dashboard, drills into alerts).
* **Secondary actor:** ML engineer (re-trains the model and `POST /admin/reload`s it).
* **Data sources:** offline PCAP captures parsed by CICFlowMeter, or CSVs ingested at the `POST /predict/csv` endpoint.

## 2. C4 — Container

```
┌───────────────────────────┐     ┌─────────────────────────────┐
│ Streamlit dashboard       │◄────│ FastAPI service             │
│ - Streamlit + Plotly      │     │ - Pydantic v2 schemas       │
│ - reads via HTTP/JSON     │     │ - scikit-learn predict()    │
│ - port 8501               │     │ - port 8000                 │
└───────────────────────────┘     └──────────┬──────────────────┘
                                              │
                                              ▼
                                       ┌─────────────────┐
                                       │ Model bundle    │
                                       │ best.joblib     │
                                       │ (pipeline+model)│
                                       └─────────────────┘
                                              │
                                              ▼
                                       ┌─────────────────┐
                                       │ SQLite          │
                                       │ alerts.db       │
                                       │ (audit log)     │
                                       └─────────────────┘
```

## 3. Data classification & flow

| Data                         | Classification | Stored?           | Retention   |
|------------------------------|----------------|-------------------|-------------|
| Flow features (volumetric, distributional) | Internal       | Yes (SQLite)      | Indefinite (analytic) |
| Source/destination IP        | Restricted     | Yes — pseudonymisable | Configurable |
| Packet payload               | Confidential   | **Never** ingested | n/a         |
| Model artefact               | Internal       | `models/best.joblib` | Versioned per training run |

**Ethical-handling rule (LO2 / LO3):** the detector **never inspects packet payloads**, only flow-level statistics. This is enforced by the canonical schema (`schema.py`) — no field can carry user PII at the application layer. This decision pre-empts the GDPR/AVG concern that anomaly detectors often double as deep-packet inspectors.

## 4. STRIDE — threats

| # | Threat (STRIDE)        | Vector                                                      | Impact | Mitigation                                                                                                                                              |
|---|------------------------|-------------------------------------------------------------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| T1 | **Spoofing** of source IP in submitted flows | Adversary forges `src_ip` in `POST /predict` payloads | Low (analytic-only; no enforcement decisions are made on the IP) | IPs are stored as labels for analyst context, not used as features. Pipeline drops `src_ip` / `dst_ip` from the feature vector (`ColumnTransformer(remainder='drop')`). |
| T2 | **Tampering** with `best.joblib` | Attacker with FS access swaps the model        | High   | Container mounts `models/` **read-only**; integrity-check hash recorded in `models/per_class_report.json`; `POST /admin/reload` is an explicit operator action. |
| T3 | **Repudiation** of an analyst action  | Analyst denies dismissing an alert         | Medium | Every classification is logged to SQLite with timestamp + model name (`alerts.db`); `/predictions` exposes the audit trail. |
| T4 | **Information disclosure** via SQLite | DB file copied off the host                  | Medium | DB stores IPs but no payloads; volume permissions restricted via Docker non-root user (`detector` / `dash`). |
| T5 | **Denial of service** via large batches | Adversary submits 10 M flows at once         | Medium | Pydantic + FastAPI cap implicit at request size; recommended rate-limit (issue #11) via an upstream nginx/traefik. |
| T6 | **Elevation of privilege** via Docker | Container break-out                          | High   | Both containers run as non-root (`Dockerfile.api` / `Dockerfile.dashboard`). No bind-mount of `/var/run/docker.sock`. |
| T7 | **Model evasion / adversarial flows** | Attacker crafts flows that look benign       | High   | Documented limitation (SRQ6 — Infiltration class). Mitigation: combine with signature IDS (Snort) — flagged as PRP risk R4 follow-up work. |
| T8 | **Data poisoning** at training time   | Adversary contaminates the training CSV     | High   | Out of scope for the live system; training pipeline is offline + version-controlled. Recommended control: signed dataset hashes. |

## 5. Non-functional requirements (LO2)

| NFR        | Target                                                       | Implemented by                                                       |
|------------|---------------------------------------------------------------|----------------------------------------------------------------------|
| Security   | No PII in inference path; least-privilege containers          | `schema.py`, Dockerfiles, non-root user                              |
| Monitoring | Every prediction audited                                      | `api/store.py` SQLite + `GET /metrics`, `GET /predictions`           |
| Ethics     | No payload inspection; clear opt-out path for stored IPs      | Flow-level features only; `src_ip` is optional in `FlowRecord`        |
| Compliance | GDPR/AVG: pseudonymisable IPs, no special-category data       | IPs are not features; can be redacted at ingest                       |
| Usability  | Severity-coded analyst dashboard with drill-down               | `dashboard/app.py` — see SRQ5                                         |

## 6. Procedural response runbooks (LO2)

Three runbooks are wired into the design:

1. **High-severity alert (`severity = critical`)** → analyst opens the dashboard's Alerts tab → drills into the flow's src/dst IPs → cross-references against `GET /predictions` to confirm the verdict is not a recurring FP → escalates per SOC SLA.
2. **Model drift detection** → if `GET /metrics` shows `total_alerts / total_predictions` deviating from the historical baseline by >10 % over a rolling 24 h window, the ML engineer re-runs `scripts/train.py` and calls `POST /admin/reload`.
3. **Incident triage with audit trail** → after a confirmed incident, the analyst pulls the relevant time-window from `/predictions?limit=...` to reconstruct the model's view of the attack.

## 7. Compliance posture (summary)

* **GDPR / AVG**: IPs are pseudonymous identifiers; no payload data is processed; all stored data is on-host and revocable.
* **NCSC-NL CSIR guidance**: aligns with the "detect" stage of the lifecycle; expected to be combined with prevention (firewall) and response (SOAR) controls.
* **OWASP ML Security Top-10 (2023)**: T2/T8 above map to ML02 (data poisoning) and ML06 (output integrity); T7 maps to ML01 (adversarial attacks).
