# Ruby 3.3 runtime image (Debian 12 slim)
FROM debian:12-slim

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
