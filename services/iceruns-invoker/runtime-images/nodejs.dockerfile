# Node.js 20 runtime image (Debian 12 slim)
FROM debian:bookworm-slim@sha256:f06537653ac770703bc45b4b113475bd402f451e85223f0f2837acbf89ab020a

# Install Node.js 20
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install common npm packages
RUN npm install -g axios redis

# Action container server
COPY action-server/nodejs-server.js /app/server.js
WORKDIR /app

EXPOSE 8080

CMD ["node", "server.js"]
