# Sprint 2 — Design & Implement

**Hand-in:** 13 April 2026 · **Phase:** Design & Implement

| Required (example) deliverable | Provided |
|---|---|
| Technical design document | [Technical_Design_Document.docx](Technical_Design_Document.docx) / [.pdf](Technical_Design_Document.pdf) |
| Network drawing | [network-drawing/](network-drawing/) — C4 context + container diagrams (PNG + source HTML) |
| Flowcharts | [flowcharts/attack_defend_sequence.png](flowcharts/attack_defend_sequence.png) |
| Attack scenarios | [Attack_Scenarios.md](Attack_Scenarios.md) |
| Threat model (architecture documentation) | [Threat_Model.md](Threat_Model.md) |
| Implementation document / design decisions | [Architecture_Review.md](Architecture_Review.md) |
| Proof of concept / initial setup | FastAPI service + 4-algorithm benchmark — see `src/`, `scripts/` in the repo |

## Contents

- **Technical_Design_Document** — user stories, architecture, component & data design, API spec, runtime flows, NFRs, traceability matrix.
- **network-drawing/** — C4 level-1 (context) and level-2 (container) diagrams; `c4_diagrams.html` is the styled source.
- **flowcharts/** — the attack→detect→block runtime sequence.
- **Attack_Scenarios.md** — the eight emulated attack categories, the real tool each maps to, the flow signature it produces, and the STRIDE/MITRE linkage.
- **Threat_Model.md** — C4 diagrams, data classification, STRIDE table, NFRs, response runbooks.
- **Architecture_Review.md** — the Workshop-strategy peer review of every architecture decision, with trade-offs and verdicts.
