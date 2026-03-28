# PowerShell 7.4 runtime image (Debian 12 slim)
FROM debian:bookworm-slim@sha256:f06537653ac770703bc45b4b113475bd402f451e85223f0f2837acbf89ab020a

# Install PowerShell 7.4
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    apt-transport-https \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-debian-bookworm-prod bookworm main" > /etc/apt/sources.list.d/microsoft.list \
    && apt-get update \
    && apt-get install -y powershell \
    && rm -rf /var/lib/apt/lists/*

# Action container server
COPY action-server/powershell-server.ps1 /app/server.ps1
WORKDIR /app

EXPOSE 8080

CMD ["pwsh", "-File", "server.ps1"]
