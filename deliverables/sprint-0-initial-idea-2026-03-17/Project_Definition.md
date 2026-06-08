# Project definition — Network Traffic Anomaly Detector

**Student:** Angel Rusev · **Minor:** Cybersecurity — Attack & Defend · Fontys, Spring 2026
**Date:** 17 March 2026

## The idea

Build a machine-learning system that learns the statistical shape of *normal*
network traffic and flags deviations as cyber attacks — in real time and at a
controlled false-positive rate. Unlike signature-based IDS (Snort, Suricata),
which can only recognise attacks it has seen before, an anomaly detector can
surface novel and zero-day behaviour. Its known weakness — false positives that
drown a SOC analyst — is treated here as a first-class design target, not an
afterthought.

## The problem

Modern organisations generate more network traffic in an hour than an analyst
can review in a year. Signature IDS cannot catch the unseen; pure anomaly
detection is noisy. The project investigates how to get the upside of anomaly
detection (novel-attack coverage) without the downside (alert fatigue).

## Main research question

> How can a machine-learning-based network-traffic anomaly detector be designed
> and implemented to accurately identify cyber attacks in real time while
> maintaining an acceptable false-positive rate?

## Sub-questions (decomposition)

1. **SRQ1** — Which flow features are most indicative of anomalous behaviour, and how should they be extracted?
2. **SRQ2** — Which ML algorithms best balance accuracy, speed and false-positive rate?
3. **SRQ3** — How can the system run in real time without unacceptable latency?
4. **SRQ4** — What threshold and tuning strategies minimise false positives?
5. **SRQ5** — How should anomalies be presented to analysts in an actionable way?
6. **SRQ6** — How does the detector perform across the different attack categories?

## Scope

**In scope:** flow-level feature engineering; a benchmark of supervised and
unsupervised algorithms; a real-time inference API; an analyst dashboard; a
containerised attack/defend lab that drives real offensive tooling through the
detector; evaluation against eight CICIDS-style categories.

**Out of scope:** deep-learning baselines (autoencoders/LSTMs); deep packet
inspection / payload analysis; production-scale multi-writer storage. These are
recorded as future work.

## Intended deliverables (per the phased plan)

Project plan & user stories (Sprint 1) → technical design, PoC, attack scenarios
(Sprint 2) → validated implementation & test results (Sprint 3) → research
document, advisory report & presentation (Sprint 4).
