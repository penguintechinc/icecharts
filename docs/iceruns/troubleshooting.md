# IceRuns Troubleshooting Guide

Common issues and solutions.

## General Issues

### API Authentication Failures

**Error:** "Unauthorized" or "Authentication failed"

**Diagnosis:**
```bash
# Verify token is valid
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/whoami

# Check token expiration
token_parts=$(echo $TOKEN | tr '.' '\n')
echo $token_parts | base64 -d  # Decode payload
```

**Solutions:**
1. Token expired → Refresh or re-authenticate
2. Invalid scope → Request token with `iceruns:execute` scope
3. Service account disabled → Re-activate or create new
4. Bearer prefix missing → Use `Authorization: Bearer <token>`

---

### Authorization Failures

**Error:** "Insufficient scope" or "Permission denied"

**Diagnosis:**
```bash
# Check what scopes user has
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/user/scopes
```

**Solutions:**
1. Missing scope → Contact admin to grant scope
2. Wrong token type → Use JWT for API, webhook token for webhooks
3. Function-specific permission → Check function ownership

---

### Package Upload Failures

**Error:** "Upload failed" or "Invalid package"

**Diagnosis:**
1. Check file size:
   ```bash
   ls -lh function.zip
   # Max: 512 MB
   ```

2. Verify ZIP is valid:
   ```bash
   unzip -t function.zip
   ```

3. Check file structure:
   ```bash
   unzip -l function.zip | head
   ```

**Solutions:**
1. File too large → Compress more, remove dependencies
2. Invalid ZIP → Recreate with `zip -r function.zip .`
3. Missing files → Verify entrypoint file is included
4. Wrong file type → Upload .zip, .tar.gz, or single source file

---

## Execution Issues

### Function Not Found

**Error:** "Function not found"

**Diagnosis:**
```bash
# List functions
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns

# Check specific function
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/{function_id}
```

**Solutions:**
1. Function deleted → Recreate function
2. Wrong function_id → Copy from UI or list all
3. Different account → Verify you own the function
4. Typo in URL → Double-check function_id

---

### Function Status is "Draft"

**Error:** "Function must be active to execute"

**Solution:**
1. Go to function detail page
2. Click **Activate** button
3. Status changes to "active"

---

### Execution Timeout

**Error:** "Function timeout exceeded" or status: "timeout"

**Causes:**
1. Function takes too long
2. Cold start causing delay
3. External API is slow
4. Insufficient resources

**Solutions:**

```bash
# 1. Increase timeout (max 900s)
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"timeout_seconds": 300}'

# 2. Optimize function code
# - Reduce complexity
# - Cache external calls
# - Use faster algorithms

# 3. Increase memory (speeds up execution)
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"memory_limit_mb": 1024}'

# 4. Use async mode
curl -X POST https://your-icecharts.com/api/v1/iceruns/{id}/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"async": true}'
```

---

### Out of Memory Error

**Error:** "Process was killed due to memory limit" or status: "failed"

**Causes:**
1. Function uses too much memory
2. Memory limit too low
3. Memory leak in function

**Diagnosis:**
```bash
# Check execution details
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/executions/{execution_id}

# Check memory_used_mb field
```

**Solutions:**

```bash
# Increase memory limit (max 4096 MB)
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"memory_limit_mb": 2048}'

# Optimize memory usage:
# - Process in chunks, not all at once
# - Use generators instead of lists
# - Delete large objects when done
# - Profile memory usage locally

# Check for memory leaks
# - Add logging to track allocation
# - Test with max input size
# - Compare memory usage over time
```

---

### Function Exits with Non-Zero Code

**Error:** status: "failed" with exit_code != 0

**Diagnosis:**
```bash
# Get execution details
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/executions/{execution_id}

# Check logs
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/executions/{execution_id}/logs
```

**Solutions:**
1. Check stderr for error message
2. Verify input is correct format
3. Check environment variables are set
4. Test function locally with same input

---

## Webhook Issues

### Webhook Token Not Working

**Error:** HTTP 401 or "Invalid webhook token"

**Diagnosis:**
```bash
# Check webhook config
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/{id}/webhook

# Verify token is in URL
echo $WEBHOOK_URL
```

**Solutions:**
1. Copy exact token from WebUI
2. Include in URL: `/hook/{token}`
3. Regenerate if not working:
   ```bash
   curl -X POST https://your-icecharts.com/api/v1/iceruns/{id}/webhook/regenerate \
     -H "Authorization: Bearer $TOKEN"
   ```

---

### Rate Limit Exceeded on Webhook

**Error:** HTTP 429 "Rate limit exceeded"

**Diagnosis:**
```bash
# Check rate limit config
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/{id}/webhook
```

**Solutions:**

```bash
# Increase rate limit (per hour)
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id}/webhook/config \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"rate_limit": 1000}'

# Implement backoff on client:
for attempt in {1..3}; do
  result=$(curl -X POST $WEBHOOK_URL -d $data)
  if [ $? -eq 0 ]; then
    break
  fi
  sleep $((2 ** attempt))
done
```

---

### HMAC Signature Validation Failed

**Error:** HTTP 400 "Invalid signature"

**Causes:**
1. Wrong webhook secret
2. Request body modified
3. Signature calculation error

**Diagnosis:**
```bash
# Verify signature is correct
webhook_secret="your-secret"
body='{"test": true}'

# Calculate expected signature
signature=$(echo -n "$body" | openssl dgst -sha256 -hmac "$webhook_secret" -hex | cut -d' ' -f2)
echo "Expected: sha256=$signature"
```

**Solutions:**
1. Ensure webhook secret matches
2. Use raw body (not parsed JSON)
3. Use correct algorithm (SHA256)
4. Don't modify request between signing and sending

---

### IP Whitelisting Blocks Webhook

**Error:** HTTP 403 "IP not whitelisted"

**Diagnosis:**
```bash
# Check your source IP
curl https://ifconfig.me

# Check webhook config
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/{id}/webhook
```

**Solutions:**

```bash
# Update IP whitelist
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id}/webhook/config \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "ip_whitelist": [
      "203.0.113.42/32",
      "203.0.113.0/24"
    ]
  }'

# Or disable for testing:
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id}/webhook/config \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ip_whitelist": []}'
```

---

## Invoker Issues

### Invoker Not Processing Tasks

**Symptoms:**
- Queue has tasks but they're not executing
- Execution status stuck in "queued"

**Diagnosis:**
```bash
# Check queue size
redis-cli XLEN iceruns:tasks

# Check consumer lag
redis-cli XINFO STREAM iceruns:tasks

# Check invoker logs
docker logs iceruns-invoker
# or
kubectl logs deployment/iceruns-invoker -n iceruns
```

**Solutions:**
1. Restart invoker:
   ```bash
   docker restart iceruns-invoker
   # or
   kubectl rollout restart deployment/iceruns-invoker -n iceruns
   ```

2. Check invoker connectivity:
   ```bash
   # Can invoker reach Redis?
   docker exec iceruns-invoker redis-cli -h redis PING

   # Can invoker reach database?
   docker exec iceruns-invoker psql -h postgres -U icecharts
   ```

3. Increase invoker replicas:
   ```bash
   docker-compose up -d --scale iceruns-invoker=3
   # or
   kubectl scale deployment iceruns-invoker --replicas=3 -n iceruns
   ```

---

### Invoker High Memory Usage

**Symptoms:**
- Invoker container uses >8GB memory
- Kubernetes OOMKilled

**Causes:**
1. Too many warm containers
2. Memory leak
3. Invoker concurrency too high

**Solutions:**

```bash
# Reduce container TTL
export WARM_CONTAINER_TTL=300

# Reduce concurrency
export INVOKER_CONCURRENCY=3

# Increase memory limit
docker update --memory 16g iceruns-invoker

# Or in Kubernetes:
kubectl set resources deployment iceruns-invoker \
  -n iceruns \
  --limits memory=16Gi
```

---

### Cold Start Failures

**Error:** Function fails only first time, works on retry

**Causes:**
1. Dependencies not installed
2. Entrypoint not found
3. Runtime not available

**Diagnosis:**
```bash
# Test runtime locally
docker run -it python:3.13-slim python --version

# Test dependency installation
pip install -r requirements.txt

# Verify entrypoint
python -m main.handler
```

**Solutions:**
1. Fix requirements.txt syntax
2. Verify entrypoint file in package
3. Pre-warm containers before traffic
4. Increase timeout to allow full cold start

---

## Database Issues

### Database Connection Failed

**Error:** "Cannot connect to database" in invoker logs

**Diagnosis:**
```bash
# Check database is running
psql -h db_host -U icecharts -c "SELECT 1"

# Check environment variables
env | grep DB_

# Check connection from container
docker exec iceruns-invoker \
  psql -h postgres -U icecharts -c "SELECT 1"
```

**Solutions:**
1. Verify database is running
2. Check credentials in environment
3. Verify network connectivity
4. Check database max_connections limit
5. Increase connection pool size

---

### Database Connection Pool Exhausted

**Error:** "Connection pool exhausted" or "No available connections"

**Causes:**
1. Too many concurrent connections
2. Connections not being released
3. Connection timeout too long

**Solutions:**

```bash
# Check current connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max_connections
psql -U postgres -c "ALTER SYSTEM SET max_connections = 500;"
sudo systemctl restart postgresql

# Increase DB_POOL_SIZE
export DB_POOL_SIZE=50

# Restart invoker to apply
```

---

## Storage Issues

### Cannot Upload Package

**Error:** "Storage upload failed" or "MinIO error"

**Diagnosis:**
```bash
# Check MinIO is running
curl http://minio:9000

# Check bucket exists
mc ls minio/icecharts

# Check credentials
export MINIO_ACCESS_KEY=<key>
export MINIO_SECRET_KEY=<secret>
mc config host add minio http://minio:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
```

**Solutions:**
1. Start MinIO:
   ```bash
   docker-compose up -d minio
   ```

2. Create bucket:
   ```bash
   mc mb minio/icecharts
   ```

3. Check credentials match environment variables
4. Verify network connectivity to MinIO

---

### Cannot Download Package During Execution

**Error:** "Failed to download function package"

**Diagnosis:**
```bash
# Check package exists in MinIO
mc ls minio/icecharts/{function_id}/

# Check package is readable
curl http://minio:9000/icecharts/...
```

**Solutions:**
1. Re-upload package
2. Check MinIO connectivity from invoker
3. Verify bucket permissions

---

## Performance Issues

### Slow Execution

**Symptoms:** Function takes longer than expected

**Diagnosis:**
```bash
# Check execution metrics
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/{id}/stats

# Check specific execution
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/executions/{id}
```

**Solutions:**

1. **Cold Start Latency:**
   - Keep function warm with periodic calls
   - Or use higher memory (faster cold starts)

2. **Code Performance:**
   - Profile locally: `python -m cProfile main.py`
   - Check for N+1 database queries
   - Optimize algorithms

3. **Resource Bottlenecks:**
   - Increase memory (faster CPU)
   - Increase timeout for external calls
   - Cache results where possible

4. **Network Latency:**
   - Enable warm containers
   - Use connection pooling
   - Batch requests

---

### High Latency on Multiple Concurrent Runs

**Symptoms:** When running many functions simultaneously, all become slow

**Causes:**
1. Insufficient invoker resources
2. Database connection bottleneck
3. Redis latency
4. Network saturation

**Solutions:**

```bash
# Scale horizontally
docker-compose up -d --scale iceruns-invoker=5

# Or in Kubernetes
kubectl scale deployment iceruns-invoker --replicas=10 -n iceruns

# Monitor queue depth
redis-cli XLEN iceruns:tasks

# If queue grows, add more invokers
```

---

## Monitoring & Debugging

### Check System Health

```bash
# Invoker status
curl http://invoker:8081/healthz

# Queue size
redis-cli XLEN iceruns:tasks

# Database connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# MinIO bucket size
mc du minio/icecharts

# Docker resource usage
docker stats iceruns-invoker
```

### View Detailed Logs

```bash
# Local logs
docker logs -f iceruns-invoker --tail 100

# Kubernetes logs
kubectl logs -f deployment/iceruns-invoker -n iceruns --tail 100

# From specific pod
kubectl logs -f iceruns-invoker-abc123 -n iceruns

# Previous pod logs
kubectl logs iceruns-invoker-abc123 -n iceruns --previous
```

### Enable Debug Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Or via environment
docker run -e LOG_LEVEL=DEBUG ...

# In Kubernetes
kubectl set env deployment/iceruns-invoker \
  LOG_LEVEL=DEBUG -n iceruns
```

---

## Getting Help

### Collect Diagnostic Information

When reporting issues, provide:

```bash
# 1. IceRuns version
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/version

# 2. Function details
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/{function_id}

# 3. Execution details
curl -H "Authorization: Bearer $TOKEN" \
  https://your-icecharts.com/api/v1/iceruns/executions/{execution_id}

# 4. System information
docker version
docker-compose version
kubectl version

# 5. Invoker logs
docker logs iceruns-invoker > /tmp/logs.txt
```

### Support Resources

- Documentation: See links in README
- GitHub Issues: https://github.com/penguin-tech/icecharts/issues
- Community Chat: Discord/Slack channel
- Email Support: support@penguintech.io

---

See also:
- [API Reference](./api-reference.md)
- [Deployment](./deployment.md)
- [Security](./security.md)
