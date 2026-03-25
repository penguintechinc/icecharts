# IceRuns Scheduling Guide

Schedule functions to run automatically on a recurring basis using cron expressions.

## Cron Expression Syntax

IceRuns uses standard Unix cron syntax:

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 7, 0=Sunday, 7=Sunday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

## Common Examples

### Every Minute
```
* * * * *
```

### Every Hour at :00
```
0 * * * *
```

### Every Day at 3 AM
```
0 3 * * *
```

### Every Weekday at 9 AM
```
0 9 * * 1-5
```

### Every Monday
```
0 0 * * 1
```

### First Day of Month at Midnight
```
0 0 1 * *
```

### Every 15 Minutes
```
*/15 * * * *
```

### 6 AM and 6 PM Every Day
```
0 6,18 * * *
```

### Every Quarter (Every 6 Hours)
```
0 */6 * * *
```

### Every Sunday at Midnight
```
0 0 * * 0
```

### First Monday of Month at 8 AM
```
0 8 1-7 * 1
```

### Last Day of Month
```
0 0 L * *
```

### Weekdays at 12 PM
```
0 12 * * 1-5
```

### Every 30 Seconds (Continuous)
```
* * * * *  # Every minute, plus code-level 30s interval
```

## Timezone Support

### Setting Timezone

1. Create schedule in WebUI or via API
2. Select timezone from dropdown
3. Default: UTC

**Supported Timezones:**
- UTC/GMT
- US Eastern (EST/EDT)
- US Central (CST/CDT)
- US Mountain (MST/MDT)
- US Pacific (PST/PDT)
- Europe/London
- Europe/Paris
- Europe/Berlin
- Asia/Tokyo
- Asia/Hong_Kong
- Australia/Sydney
- And 300+ others (IANA format)

### Example: 9 AM Pacific Time

```json
{
  "function_id": "f7e8d9c0-...",
  "cron_expression": "0 9 * * *",
  "timezone": "America/Los_Angeles"
}
```

IceRuns automatically converts to UTC for storage and execution.

## Creating Schedules

### Via WebUI

1. Open function → **Schedules** tab
2. Click **Add Schedule**
3. Enter cron expression
4. Select timezone
5. Optional: Add static input JSON
6. Click **Create Schedule**

### Via API

```bash
curl -X POST https://your-icecharts.com/api/v1/iceruns/{function_id}/schedules \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "cron_expression": "0 3 * * *",
    "timezone": "America/New_York",
    "static_input": {
      "environment": "production",
      "action": "backup"
    }
  }'
```

### Response

```json
{
  "schedule_id": "s1a2b3c4-...",
  "function_id": "f7e8d9c0-...",
  "cron_expression": "0 3 * * *",
  "timezone": "America/New_York",
  "is_active": true,
  "next_run_at": "2026-01-21T08:00:00Z",
  "last_run_at": null,
  "run_count": 0,
  "created_at": "2026-01-20T12:00:00Z"
}
```

## Managing Schedules

### List Schedules

```bash
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/{function_id}/schedules"
```

### Get Schedule Details

```bash
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/schedules/{schedule_id}"
```

### Update Schedule

```bash
curl -X PUT "https://your-icecharts.com/api/v1/iceruns/schedules/{schedule_id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "cron_expression": "0 2 * * *",
    "timezone": "UTC"
  }'
```

### Disable Schedule

```bash
curl -X PUT "https://your-icecharts.com/api/v1/iceruns/schedules/{schedule_id}/disable" \
  -H "Authorization: Bearer {token}"
```

### Enable Schedule

```bash
curl -X PUT "https://your-icecharts.com/api/v1/iceruns/schedules/{schedule_id}/enable" \
  -H "Authorization: Bearer {token}"
```

### Delete Schedule

```bash
curl -X DELETE "https://your-icecharts.com/api/v1/iceruns/schedules/{schedule_id}" \
  -H "Authorization: Bearer {token}"
```

## Static Input for Scheduled Runs

Provide fixed input data for scheduled executions:

```json
{
  "cron_expression": "0 3 * * *",
  "static_input": {
    "environment": "production",
    "backup_type": "full",
    "retention_days": 30,
    "notify_on_complete": true
  }
}
```

### Python Function

```python
def handler(event):
    # event contains static_input provided in schedule
    environment = event.get('environment')
    backup_type = event.get('backup_type')

    return {
        'environment': environment,
        'backup_type': backup_type,
        'status': 'backup_initiated'
    }
```

## Common Scheduling Patterns

### 1. Daily Backup at 3 AM UTC

```
Schedule:
- Cron: 0 3 * * *
- Timezone: UTC
- Input: {"type": "daily"}
```

### 2. Hourly Health Check

```
Schedule:
- Cron: 0 * * * *
- Timezone: UTC
- Input: {"service": "api", "check": "health"}
```

### 3. Weekly Report on Monday Morning

```
Schedule:
- Cron: 0 8 * * 1
- Timezone: America/New_York
- Input: {"report_type": "weekly", "format": "email"}
```

### 4. Cleanup Every Night at Midnight

```
Schedule:
- Cron: 0 0 * * *
- Timezone: UTC
- Input: {"cleanup": "old_logs", "older_than_days": 30}
```

### 5. Sync Data Every 30 Minutes (via polling function)

```
Schedule:
- Cron: */30 * * * *
- Timezone: UTC
- Input: {"sync": "database", "source": "remote"}
```

### 6. Monthly Report on 1st at 9 AM

```
Schedule:
- Cron: 0 9 1 * *
- Timezone: America/Los_Angeles
- Input: {"report": "monthly", "email_to": "admin@example.com"}
```

### 7. Every 6 Hours (Business Hours)

```
Schedule:
- Cron: 0 */6 * * 1-5
- Timezone: America/New_York
- Input: {"check": "status"}
```

## Schedule Execution Flow

```
1. IceRuns scheduler checks all active schedules
   - Every minute or as configured
   - Compares current time against cron expression
   - Converts to function timezone

2. When schedule fires:
   - Create execution record
   - Enqueue to Redis Streams
   - Set trigger_type = "schedule"
   - Include static_input as payload

3. Invoker processes:
   - Pull from queue
   - Execute function
   - Capture results/logs
   - Update schedule metadata

4. Schedule metadata updated:
   - last_run_at = execution timestamp
   - run_count += 1
   - next_run_at = next occurrence
```

## Monitoring Scheduled Executions

### View Execution History

```bash
# Get all executions for a function
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/{function_id}/executions?trigger_type=schedule"

# Check most recent scheduled run
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/executions/{execution_id}"
```

### Check Next Scheduled Run

```json
{
  "schedule_id": "s1a2b3c4-...",
  "function_id": "f7e8d9c0-...",
  "cron_expression": "0 3 * * *",
  "timezone": "UTC",
  "is_active": true,
  "next_run_at": "2026-01-21T03:00:00Z",
  "last_run_at": "2026-01-20T03:00:05Z",
  "run_count": 125
}
```

## Error Handling

### Failed Scheduled Execution

If a scheduled function fails:
1. Execution marked as failed
2. Error stored with timestamp
3. Schedule continues (not disabled)
4. Set up monitoring to detect patterns

### Late Execution

If a scheduled execution is delayed:
1. Function still executes when invoker becomes available
2. Execution timestamp reflects actual start time
3. Retries depend on failure reason

### Timezone Change

If you change function timezone:
1. next_run_at is recalculated
2. Existing schedule continues
3. No impact on past executions

## Best Practices

### 1. Set Realistic Intervals
- Don't schedule more frequently than needed
- Consider function execution time
- Leave buffer for overhead

### 2. Use Descriptive Input
- Document what static_input means
- Include environment/context
- Make debugging easier

### 3. Monitor Executions
- Check execution history regularly
- Set up alerts for failures
- Track success rate

### 4. Handle Overlaps
- If function takes longer than interval, handle gracefully
- Use distributed locks for critical operations
- Track last successful completion

### 5. Plan for Maintenance
- Schedule during low-traffic periods
- Account for database maintenance windows
- Test schedule before production

### 6. Document Schedules
- Add description/tags to schedules
- Keep track of why each exists
- Review quarterly

### 7. Use Appropriate Timezones
- Be aware of DST transitions
- Document timezone choice
- Test before deployment

## Limitations

- **Precision**: Nearest minute (60-second granularity)
- **Maximum Interval**: No limit, but consider storage
- **Concurrent Executions**: Same function can run multiple times if previous execution delayed
- **Missed Executions**: If all invokers down, executions are queued when available

## Troubleshooting

### Schedule Not Firing

**Check:**
1. Is schedule enabled? (`is_active: true`)
2. Is function active? (`status: active`)
3. Is next_run_at in the future?
4. Check server time matches expected time
5. Verify timezone setting is correct

**Debug:**
```bash
# Verify current time in schedule timezone
TZ='America/New_York' date

# Check next calculated execution
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/schedules/{schedule_id}"
```

### Function Executes Too Often

**Causes:**
- Cron expression is too frequent
- Previous execution is still running
- Clock skew between services

**Solution:**
- Adjust cron expression
- Increase function timeout
- Check invoker logs

### Wrong Timezone

**Fix:**
1. Update schedule timezone
2. Verify next_run_at is correct
3. Test with manual execution
4. Monitor next scheduled run

---

See also:
- [API Reference](./api-reference.md)
- [Runtimes Guide](./runtimes.md)
- [Troubleshooting](./troubleshooting.md)
