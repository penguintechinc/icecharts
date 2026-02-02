# IceRuns Quickstart Guide

Get your first serverless function running in 5 minutes.

## Step 1: Write Your Function (2 minutes)

Create a simple Python function:

```python
# main.py
def handler(event):
    """Simple hello world function"""
    name = event.get('name', 'World')
    return {
        'message': f'Hello, {name}!',
        'timestamp': str(__import__('datetime').datetime.utcnow()),
        'success': True
    }
```

## Step 2: Create Deployment Package (1 minute)

```bash
# Create a directory with your function
mkdir my-function
cd my-function
cp ../main.py .

# Create a zip package
zip -r function.zip main.py
```

## Step 3: Upload Function via WebUI (1 minute)

1. **Navigate to IceRuns**
   - Open IceCharts WebUI
   - Click **IceRuns** in the sidebar

2. **Create Function**
   - Click **Create Function** button (top-right)
   - Fill in basic information:
     - **Name**: "Hello World"
     - **Description**: "My first IceRuns function"
     - **Tags**: `hello, tutorial`
   - Click **Next**

3. **Select Runtime**
   - Choose **Python 3.13**
   - Click **Next**

4. **Upload Package**
   - Drag and drop `function.zip` or click to browse
   - Wait for upload to complete
   - Click **Next**

5. **Configure Runtime**
   - **Entrypoint**: `main.py`
   - **Handler**: `main.handler`
   - **Memory**: 128 MB (default)
   - **Timeout**: 60 seconds (default)
   - Click **Next**

6. **Webhook Settings**
   - Toggle **Enable Webhook** ON
   - Allow GET requests: **ON** (for testing)
   - Click **Create**

7. **Activate Function**
   - In the function detail page, click **Activate**
   - Status changes to **active**
   - Copy your **Webhook URL**

## Step 4: Test Your Function (1 minute)

### Option A: Test via WebUI

1. Go to function detail page
2. Click **Test** tab
3. Enter input JSON:
   ```json
   {"name": "Alice"}
   ```
4. Click **Run Test**
5. See output in real-time

### Option B: Test via Webhook

```bash
# Get your webhook URL from the function detail page
WEBHOOK_URL="https://your-icecharts.com/api/v1/iceruns/hook/abc123..."

# Make a request
curl -X POST $WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
```

Response:
```json
{
  "execution_id": "e1a2b3c4-5d6e-7f8g-9h0i-1j2k3l4m5n6o",
  "status": "completed",
  "output": {
    "message": "Hello, Alice!",
    "timestamp": "2026-01-20T12:00:00.123456",
    "success": true
  },
  "duration_ms": 245
}
```

### Option C: Test via API

```bash
# Using your JWT token
TOKEN="your-jwt-token"
FUNCTION_ID="f7e8d9c0-..."

curl -X POST "https://your-icecharts.com/api/v1/iceruns/${FUNCTION_ID}/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "async": false}'
```

## What's Next?

### 1. **Explore Other Runtimes**
   - Try [Node.js](./runtimes.md#nodejs) or [Go](./runtimes.md#go)
   - See [Runtimes Guide](./runtimes.md) for language-specific details

### 2. **Use Advanced Features**
   - [Add environment variables](./api-reference.md#update-function-configuration)
   - [Store secrets securely](./api-reference.md#update-function-secrets)
   - [Set up webhooks with HMAC signing](./webhook-guide.md#hmac-signature-validation)
   - [Schedule recurring runs with cron](./scheduling.md)

### 3. **Integrate with IceStreams**
   - Use IceRuns in playbooks
   - See [IceStreams Integration](./icestreams-integration.md)

### 4. **Monitor Production Functions**
   - View execution history and logs
   - Check metrics and performance
   - Set up alerts

## Common Issues

### "Authentication failed"
- Check your JWT token is valid: `curl -H "Authorization: Bearer $TOKEN" https://your-icecharts.com/api/v1/whoami`
- Verify you have `iceruns:execute` scope
- For webhooks, token should be in the URL

### "Package upload failed"
- Ensure ZIP file is valid: `unzip -t function.zip`
- Maximum size is 512 MB
- Check file has correct structure

### "Timeout"
- Function took longer than timeout setting
- Increase timeout: Edit function → Configuration → Timeout
- Optimize function performance

### "Memory exceeded"
- Function used more memory than limit
- Increase memory: Edit function → Configuration → Memory
- Check for memory leaks in code

## Next Steps

- Read the full [API Reference](./api-reference.md) for all endpoints
- Check [Security Best Practices](./security.md)
- Explore [Example Functions](./examples/)
- Join the [community](https://github.com/penguin-tech/icecharts)

---

Happy coding with IceRuns!
