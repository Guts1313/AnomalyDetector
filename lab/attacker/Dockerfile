# Attacker container: every course tool we'll use, behind a tiny HTTP API.
# All tools are real (apt packages from Ubuntu's archive) — the FastAPI service
# just wraps each one in /attack so the FE can trigger them by preset name.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Tools you studied in the Attack & Defend module:
#   nmap       - port / service scanning  → PortScan preset
#   hping3     - SYN-flood crafting       → DDoS, DoS presets
#   hydra      - credential brute-force   → BruteForce preset
#   sqlmap     - SQL injection            → WebAttack preset
#   curl       - benign + botnet beacons  → BENIGN, Botnet, Infiltration
#   netcat     - manual probing           → bonus / debug
#   tcpdump    - sniff from attacker side → debug
#   python3-pip + fastapi - the /attack HTTP wrapper
RUN apt-get update && apt-get install -y --no-install-recommends \
        nmap hping3 hydra sqlmap \
        apache2-utils slowhttptest \
        curl netcat-openbsd tcpdump iputils-ping dnsutils \
        python3 python3-pip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Small wordlists for hydra so the BruteForce preset has something to try.
# These are intentionally tiny — the *traffic shape* is what the model classifies,
# not whether hydra actually guesses the password.
COPY wordlists/ /app/wordlists/
COPY app.py /app/app.py

EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
