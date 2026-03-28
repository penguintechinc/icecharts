# Python 3.13 runtime image (Debian 12 slim)
FROM debian:bookworm-slim@sha256:f06537653ac770703bc45b4b113475bd402f451e85223f0f2837acbf89ab020a

# Install Python 3.13
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages
RUN pip3 install --no-cache-dir --break-system-packages \
    requests \
    boto3 \
    redis \
    aiohttp

# Action container server
COPY action-server/python-server.py /app/server.py
WORKDIR /app

EXPOSE 8080

CMD ["python3", "server.py"]
