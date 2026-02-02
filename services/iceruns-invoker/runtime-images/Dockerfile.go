# Go 1.23 runtime image (Debian 12 slim)
FROM debian:12-slim

# Install Go 1.23
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && curl -OL https://golang.org/dl/go1.23.0.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz \
    && rm go1.23.0.linux-amd64.tar.gz \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/local/go/bin:${PATH}"

# Action container server
COPY action-server/go-server.go /app/server.go
WORKDIR /app

EXPOSE 8080

CMD ["go", "run", "server.go"]
