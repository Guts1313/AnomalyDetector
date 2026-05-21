# Defender container: target services + IDS pipeline + auto-block enforcer.
#
# Three things share this container:
#   1. nginx :80, sshd :22 — the "victim" services the attacker actually hits
#      (so we can prove the block works: hits stop landing after we blacklist).
#   2. cicflowmeter on eth0 → live CSV → flow_streamer.py → POST /predict.
#   3. iptables INPUT chain — flow_streamer appends DROP rules for source IPs
#      classified as attacks, with a TTL so blocks expire automatically.
#
# Putting target + detector in one container is the simplest architecture for
# Docker (a separate IDS would need promiscuous bridge mode or a SPAN port,
# which Docker bridge networks don't provide). Worth noting in the LO writeup.
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Same Python (3.11) as lab/sanity/Dockerfile so the cicflowmeter version + its
# CSV column names stay identical across both. Debian Bookworm has all the
# system packages we need.
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx openssh-server \
        tcpdump iptables iproute2 dnsutils curl \
        ca-certificates \
        supervisor \
        procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir cicflowmeter==0.2.0 scapy==2.5.0

# sshd needs a host key + privsep dir + a user with a password so hydra has
# something to brute-force. We add a "victim" user but DON'T set a weak password —
# the goal is repeated failed logins (the traffic pattern), not a real compromise.
RUN ssh-keygen -A \
    && mkdir -p /var/run/sshd \
    && useradd -m -s /bin/bash victim \
    && echo 'victim:S3cure!ButLong#Pass-2026' | chpasswd \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Replace nginx default page with something tiny — log-friendly, easy to grep.
RUN echo '<!doctype html><html><body><h1>Defender target</h1><p>OK.</p></body></html>' \
        > /var/www/html/index.html

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY flow_streamer.py /app/flow_streamer.py
COPY server.py /app/server.py
COPY supervisord.conf /etc/supervisor/conf.d/defender.conf

EXPOSE 80 22 8002
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
