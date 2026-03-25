#!/bin/bash
# Action container server for Bash runtime (OpenWhisk /init and /run pattern)

# Simple HTTP server using netcat
while true; do
  echo -e "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"status\":\"ready\"}" | nc -l -p 8080 -q 1
done
