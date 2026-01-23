# IceRuns and IceStreams Integration

Use IceRuns serverless functions as nodes in IceStreams playbooks.

## Overview

IceStreams playbooks can execute IceRuns functions as action nodes, enabling powerful workflow automation that combines:
- **IceStreams**: Workflow orchestration and data transformation
- **IceRuns**: Serverless function execution

This allows you to:
- Execute custom code as part of a playbook
- Process data through external services
- Implement complex business logic
- Chain multiple functions together

## Node Types

### IceRun Execute Node

Execute a serverless function with input data.

**Node Type:** `iceruns.execute`

**Configuration:**
```json
{
  "function_id": "f7e8d9c0-...",
  "input_mode": "from_previous",
  "timeout_override": 120,
  "async": false
}
```

**Input Options:**
- `from_previous` - Use output from previous node
- `static` - Use fixed JSON input

**Output:**
```json
{
  "activation_id": "e1a2b3c4-...",
  "status": "completed",
  "result": {
    "output": "from_function"
  },
  "duration_ms": 2345
}
```

### IceRun Wait Node

Wait for async function completion (optional).

**Node Type:** `iceruns.wait_for_completion`

**Configuration:**
```json
{
  "activation_id": "e1a2b3c4-...",
  "timeout_seconds": 300
}
```

**Use Case:**
- Long-running functions
- Parallel execution
- Deferred processing

## Adding IceRuns to a Playbook

### Step 1: Create the Function

Create an IceRuns function that processes your data:

```python
# process_image.py
def handler(event):
    image_url = event.get('url')
    width = event.get('width', 800)

    # Your processing logic here
    # Download, process, upload...

    return {
        'result_url': 'https://cdn.example.com/processed.jpg',
        'size': width,
        'success': True
    }
```

### Step 2: Open Playbook Editor

1. Go to **IceStreams** → **Playbooks**
2. Open or create a playbook
3. Click **Edit** to enter workflow editor

### Step 3: Add IceRuns Node

1. Open **Node Palette** (left sidebar)
2. Find **IceRuns** category (purple section)
3. Drag **Execute IceRun** node to canvas
4. Configure the node

### Step 4: Configure Node

**Select Function:**
```
Function: [Dropdown showing all active IceRuns functions]
```

**Choose Input Mode:**
- **From Previous** - Use data from previous node
- **Static** - Provide fixed JSON

**Static Input Example:**
```json
{
  "environment": "production",
  "quality": 85,
  "format": "webp"
}
```

**Optional Settings:**
- Override timeout (1-900 seconds)
- Enable async mode (for long-running)

### Step 5: Connect to Other Nodes

```
Trigger
  ↓
[Data Transform] (extract image URL)
  ↓
[IceRun Execute] (process image)
  ↓
[HTTP Request] (upload result)
```

### Step 6: Test and Deploy

1. Click **Test Playbook**
2. Provide sample input
3. Watch execution flow through nodes
4. Check IceRuns execution logs
5. Deploy when satisfied

## Playbook Examples

### Example 1: Image Processing Pipeline

```yaml
Trigger: Webhook receives image URL
  ↓
Extract Image Metadata (Transform)
  - Extract URL, dimensions from input
  ↓
Validate Image (IceRun)
  - Function: validate_image
  - Input from previous
  ↓
Process Image (IceRun)
  - Function: resize_and_optimize
  - Input from previous
  ↓
Upload to CDN (HTTP Request)
  - POST to CDN with processed image
  ↓
Send Notification (HTTP Request)
  - POST to Slack/email with result
```

### Example 2: Data Processing with Parallel Execution

```yaml
Trigger: CSV file upload
  ↓
Parse CSV (Transform)
  ↓
Process Row 1 (IceRun - async)
Process Row 2 (IceRun - async)
Process Row 3 (IceRun - async)
  ↓
Wait for All (IceRun Wait)
  ↓
Aggregate Results (Transform)
  ↓
Store in Database (HTTP Request)
```

### Example 3: Multi-Step Workflow

```yaml
Trigger: Scheduled (Daily at 3 AM)
  ↓
Fetch Data (HTTP Request)
  - Get data from external API
  ↓
Clean Data (IceRun)
  - Function: data_cleanup
  - Input from previous
  ↓
Generate Report (IceRun)
  - Function: generate_report
  - Input from previous
  ↓
Upload Report (HTTP Request)
  - POST to S3 bucket
  ↓
Send Email (HTTP Request)
  - Send via email service
```

## Data Flow

### Simple Sync Execution

```
Trigger Input
  ↓
[Node 1] outputs data_a
  ↓
[IceRun Node] receives data_a
  ↓
Function executes with data_a
  ↓
[IceRun Node] outputs {result, duration_ms}
  ↓
[Node 2] receives IceRun output
```

### Async Execution with Wait

```
Trigger Input
  ↓
[Node 1] outputs data_a
  ↓
[IceRun Execute] (async: true)
  ↓
Returns immediately with activation_id
  ↓
[Other Nodes] execute in parallel
  ↓
[IceRun Wait] polls for activation_id
  ↓
Once complete, continues with result
```

### Error Handling

```
[IceRun Execute]
  ↓
Success?
  ├─ Yes → Continue to next node
  └─ No → [Error Handler]
           ├─ Retry logic
           ├─ Alert notification
           └─ Fallback action
```

## Advanced Configuration

### Timeout Override

For functions that need custom timeout:

```json
{
  "function_id": "f7e8d9c0-...",
  "timeout_override": 300,
  "async": false
}
```

Overrides the function's default timeout setting.

### Async Mode

For long-running functions:

```json
{
  "function_id": "f7e8d9c0-...",
  "async": true
}
```

Returns immediately with `activation_id`, allowing other nodes to proceed.

### Conditional Execution

Use IceStreams conditions with IceRun output:

```json
{
  "type": "condition",
  "input": "${iceruns_node.result.success}",
  "true_branch": "[Next Node]",
  "false_branch": "[Error Node]"
}
```

### Retry Logic

Implement retries for failed IceRun executions:

```json
{
  "type": "retry_node",
  "max_retries": 3,
  "backoff": "exponential",
  "target": "${iceruns_node}",
  "fallback": "[Fallback Node]"
}
```

## Variable Mapping

### Access IceRun Output

In downstream nodes, reference IceRun output:

```json
${iceruns_execute.result.field_name}
${iceruns_execute.activation_id}
${iceruns_execute.duration_ms}
${iceruns_execute.status}
```

### Pass Data Between Nodes

```
[Transform Node]
  Output: {
    "image_url": "https://example.com/photo.jpg",
    "width": 800
  }
  ↓
[IceRun Execute]
  Input: ${previous.result}
  Function receives: {
    "image_url": "https://example.com/photo.jpg",
    "width": 800
  }
  ↓
[IceRun] Output: {
    "processed_url": "https://cdn.example.com/photo.jpg"
  }
  ↓
[HTTP Request]
  URL: ${previous.result.processed_url}
```

## Monitoring

### View Execution History

1. **Playbook Detail** → **Executions** tab
2. Click execution to see full flow
3. Click IceRun node to see function logs

### Check Function Metrics

1. Go to IceRuns function detail
2. View execution history
3. Check triggered from playbook (trigger_type = "playbook")

### Debug IceRun Failures

1. Open playbook execution
2. Click failed IceRun node
3. View function logs, exit code
4. Check input/output JSON

## Best Practices

### 1. Function Design
- Keep functions focused and single-purpose
- Handle all error cases
- Return meaningful output
- Keep execution time reasonable (< 60s for sync)

### 2. Input Validation
- Validate input in function
- Handle missing fields gracefully
- Return error status
- Don't assume data structure

### 3. Timeout Management
- Use realistic timeouts
- Account for cold starts
- Override only when necessary
- Monitor actual execution times

### 4. Error Handling
- Wrap IceRun nodes with error handlers
- Implement retry logic
- Set up alerts for failures
- Test failure scenarios

### 5. Testing
- Test function independently first
- Test in playbook with sample data
- Monitor production executions
- Keep function versions stable

### 6. Performance
- Use async for long-running operations
- Implement parallel processing where possible
- Cache function results if applicable
- Monitor overall playbook latency

## Troubleshooting

### Function Not Found

**Error:** "Function not found"

**Causes:**
- Function deleted
- Function in different account
- Function_id typo

**Solution:**
- Verify function still exists
- Check function_id matches
- Recreate node with function selector

### Timeout

**Error:** "Function execution timeout"

**Causes:**
- Function takes too long
- Cold start causing delay
- External service delay

**Solution:**
- Increase timeout override
- Optimize function code
- Enable warm start (use frequently)

### Input Mismatch

**Error:** "Function error with provided input"

**Causes:**
- Input data structure wrong
- Missing required fields
- Type mismatch

**Solution:**
- Check output from previous node
- Validate function expects that format
- Use static input for testing

### Authorization Failed

**Error:** "User lacks iceruns:execute scope"

**Causes:**
- User doesn't have execute permission
- Service account missing scope

**Solution:**
- Grant user iceruns:execute scope
- Add scope to service account
- Contact administrator

## Integration Patterns

### Pattern 1: Enrich Data

```
[Fetch External Data]
  ↓
[Transform/Extract]
  ↓
[IceRun: Enrich]
  ↓
[Store Enriched Data]
```

### Pattern 2: Custom Validation

```
[Extract Form Input]
  ↓
[IceRun: Validate]
  ↓
Valid? → [Process]
Invalid? → [Return Error]
```

### Pattern 3: Complex Calculation

```
[Aggregate Data]
  ↓
[IceRun: Calculate]
  ↓
[Format Output]
```

### Pattern 4: External Service Call

```
[Prepare Request]
  ↓
[IceRun: Call Service]
  ↓
[Process Response]
```

---

See also:
- [IceStreams Documentation](../icestreams/README.md)
- [Quickstart](./quickstart.md)
- [API Reference](./api-reference.md)
- [Runtimes Guide](./runtimes.md)
