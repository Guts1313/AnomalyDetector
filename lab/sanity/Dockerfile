# Sanity runner: a single container that has every tool we need to capture
# a real port-scan and translate it into the CIC-flow features the model expects.
FROM python:3.11-slim

# nmap   — generates the port-scan traffic
# tcpdump — captures it from the runner's NIC to a .pcap
# iproute2/dnsutils/curl — sanity-check the network from inside the container
# libpcap is pulled in by tcpdump's dependencies, so scapy / cicflowmeter work.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        nmap tcpdump iproute2 dnsutils curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# cicflowmeter — Python re-implementation of the UNB CICFlowMeter. Takes a pcap
# and writes the same flow-feature CSV the model was trained on.
# scapy — pinned so cicflowmeter has a known-good packet library underneath.
# requests — to POST flows at the API.
RUN pip install --no-cache-dir \
        cicflowmeter==0.2.0 \
        scapy==2.5.0 \
        requests==2.32.3

WORKDIR /app
COPY sanity.py /app/sanity.py

# One-shot: runs the full capture → extract → predict pipeline then exits.
CMD ["python", "/app/sanity.py"]
