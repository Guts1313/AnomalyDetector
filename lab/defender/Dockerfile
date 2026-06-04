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
    && pip install --no-cache-dir cicflowmeter==0.2.0 scapy==2.5.0 \
    # Patch cicflowmeter's flow-expiry timeout from 240s to 30s. 240s means
    # the live classifier waits 4 minutes before emitting a flow, which made
    # per-attack verdicts impossible to attribute. We tried 5s but that
    # produced features wildly different from what the model was trained on
    # (captures use the SAME patched cicflowmeter, so train and inference now
    # agree on the same flow boundary).
    && python3 -c "import cicflowmeter, os; p=os.path.join(os.path.dirname(cicflowmeter.__file__), 'constants.py'); s=open(p).read(); open(p,'w').write(s.replace('EXPIRED_UPDATE = 240', 'EXPIRED_UPDATE = 30')); print('patched cicflowmeter EXPIRED_UPDATE -> 30s')"

# sshd needs a host key + privsep dir + a user with a password so hydra has
# something to brute-force. We add a "victim" user but DON'T set a weak password —
# the goal is repeated failed logins (the traffic pattern), not a real compromise.
RUN ssh-keygen -A \
    && mkdir -p /var/run/sshd \
    && useradd -m -s /bin/bash victim \
    && echo 'victim:S3cure!ButLong#Pass-2026' | chpasswd \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    # Disable PerSourcePenalties so hydra/raw-TCP floods don't get rate-limited
    # at the OS level — otherwise the kernel drops thousands of subsequent SYN
    # packets that cicflowmeter still emits as ghost flows, polluting the live
    # classifier with phantom BruteForce-shaped traffic.
    && echo 'PerSourcePenalties no'        >> /etc/ssh/sshd_config \
    && echo 'MaxStartups 1000:30:5000'     >> /etc/ssh/sshd_config \
    && echo 'LoginGraceTime 2'             >> /etc/ssh/sshd_config

# Replace nginx default page with a small site that has links and forms, so
# sqlmap's --crawl mode has something to walk and probe. The endpoints don't
# exist (they 404) — what matters is that sqlmap fires many parameterised
# requests, which is the traffic shape the model needs to see.
RUN printf '%s\n' \
    '<!doctype html><html><head><title>Defender target</title></head><body>' \
    '<h1>Defender target</h1><p>OK.</p>' \
    '<ul>' \
    '  <li><a href="/login.php?user=admin">login</a></li>' \
    '  <li><a href="/search.php?q=test">search</a></li>' \
    '  <li><a href="/product.php?id=1">product 1</a></li>' \
    '  <li><a href="/product.php?id=2">product 2</a></li>' \
    '  <li><a href="/api/users?id=1">user 1</a></li>' \
    '  <li><a href="/api/orders?order_id=42">order</a></li>' \
    '</ul>' \
    '<form action="/login.php" method="POST">' \
    '  <input name="username" /><input name="password" type="password" />' \
    '  <button type="submit">Sign in</button>' \
    '</form>' \
    '</body></html>' \
    > /var/www/html/index.html

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY flow_streamer.py /app/flow_streamer.py
COPY server.py /app/server.py
COPY supervisord.conf /etc/supervisor/conf.d/defender.conf

EXPOSE 80 22 8002
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
