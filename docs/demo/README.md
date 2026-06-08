# Demo — attack → detect → auto-block

[`demo-attack-block.mp4`](demo-attack-block.mp4) (Git LFS) is a screen recording
of the live attack/defend laboratory: a real offensive tool is launched from the
React frontend's *Run on lab* button, the defender container captures the
traffic, the trained model classifies it via `POST /predict`, and an
`iptables DROP` rule is installed automatically for the attacker's IP — after
which subsequent probes time out and the verdict appears as a severity-coloured
row in the analyst's Alerts tab.

This is the **Showroom** evidence for the project and a core artefact for
**LO1** (methodical offensive testing) and **LO2** (automated defensive
response). The runtime sequence it captures is drawn in
[`../screenshots/24_attack_defend_sequence.png`](../screenshots/24_attack_defend_sequence.png).

> The file is stored with Git LFS. Clone with `git lfs pull` (or install Git LFS
> first) to fetch the actual video; GitHub also serves it from the web UI.
