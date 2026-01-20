FROM python:3.11-slim-bookworm

# 1. Install dependencies for Edge
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    apt-transport-https \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Microsoft Edge (Stable)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg && \
    install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ && \
    sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list' && \
    rm microsoft.gpg && \
    apt-get update && \
    apt-get install -y microsoft-edge-stable && \
    rm -rf /var/lib/apt/lists/*

# 3. Setup App Directory
WORKDIR /project

# 4. Copy Files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY app/ app/
COPY assets/ assets/


# 5. Environment
ENV PORT=8000
ENV EDGE_BIN=/usr/bin/microsoft-edge-stable
ENV PYTHONPATH=/project

# 6. Run
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "app/main.py"]
