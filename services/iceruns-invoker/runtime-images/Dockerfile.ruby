# Ruby 3.3 runtime image (Debian 12 slim)
FROM debian:bookworm-slim@sha256:f06537653ac770703bc45b4b113475bd402f451e85223f0f2837acbf89ab020a

# Install Ruby 3.3
RUN apt-get update && apt-get install -y \
    ruby \
    ruby-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install common gems
RUN gem install httparty redis

# Action container server
COPY action-server/ruby-server.rb /app/server.rb
WORKDIR /app

EXPOSE 8080

CMD ["ruby", "server.rb"]
