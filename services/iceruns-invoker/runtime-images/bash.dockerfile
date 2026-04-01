# Bash 5.2 runtime image (Debian 12 slim)
FROM debian:bookworm-slim@sha256:f06537653ac770703bc45b4b113475bd402f451e85223f0f2837acbf89ab020a

# Install Bash and common utilities
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Action container server
COPY action-server/bash-server.sh /app/server.sh
RUN chmod +x /app/server.sh
WORKDIR /app

EXPOSE 8080

CMD ["/app/server.sh"]
