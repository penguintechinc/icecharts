# Rust 1.75 runtime image (Debian 12 slim)
FROM debian:bookworm-slim@sha256:f06537653ac770703bc45b4b113475bd402f451e85223f0f2837acbf89ab020a

# Install Rust 1.75
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    build-essential \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

# Action container server
COPY action-server/rust-server.rs /app/server.rs
WORKDIR /app

EXPOSE 8080

CMD ["cargo", "run"]
