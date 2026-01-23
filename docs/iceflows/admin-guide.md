# IceFlows Administration Guide

IceFlows is a branch-centric CI/CD pipeline solution for IceCharts.

## Table of Contents
1. [Overview](#overview)
2. [Setup](#setup)
3. [Configuration](#configuration)
4. [Managing Flows](#managing-flows)
5. [Approval Workflows](#approval-workflows)
6. [GitOps Integration](#gitops-integration)
7. [Notifications](#notifications)
8. [Troubleshooting](#troubleshooting)

## Overview

IceFlows models CI/CD pipelines as ordered git branches, where each branch represents a deployment stage:

```
alpha → beta → main (production)
```

Key concepts:
- **Flow**: A pipeline definition tied to a repository
- **Stage**: A branch that code must pass through (with tests, approvals)
- **Promotion**: A request to merge from one stage to the next
- **Approval**: A vote from an authorized approver

## Setup

### Prerequisites
- IceCharts backend running
- Redis for task queue
- PostgreSQL/MySQL database
- GitHub or GitLab repository access

### Worker Service
Start the IceFlows worker:
```bash
docker-compose up -d iceflows-worker
```

### Webhook Configuration
Configure webhooks in your repository settings:
- **GitHub**: Settings → Webhooks → Add webhook
  - URL: `https://your-icecharts.com/api/v1/iceflows/hooks/github/{webhook_id}`
  - Content type: application/json
  - Secret: (your webhook secret)
  - Events: Push events, Pull requests

- **GitLab**: Settings → Webhooks
  - URL: `https://your-icecharts.com/api/v1/iceflows/hooks/gitlab/{webhook_id}`
  - Secret token: (your webhook secret)
  - Triggers: Push events, Merge request events

## Configuration

### Environment Variables
```bash
# Worker settings
ICEFLOWS_WORKER_ID=iceflows-worker-1
WORKER_CONCURRENCY=4

# Darwin code review (optional)
DARWIN_API_URL=https://darwin.example.com/api/v1
DARWIN_API_KEY=your-api-key
```

### Service Account Scopes
Create service accounts with appropriate scopes:
- **Read-only**: `iceflows:read`
- **Operator**: `iceflows:read`, `iceflows:execute`, `iceflows:approve`
- **Admin**: `iceflows:admin`

## Managing Flows

### Creating a Flow
1. Navigate to IceFlows in WebUI
2. Click "Create Pipeline"
3. Configure:
   - Name and description
   - Repository URL
   - Provider (GitHub/GitLab)
   - Add stages in order

### Stage Configuration
Each stage can have:
- **Branch name**: The git branch (e.g., `alpha`, `beta`, `main`)
- **Minimum approvers**: Required approvals before merge
- **Override threshold**: Approvers needed to bypass day restrictions
- **Day restrictions**: Block deployments on specific days (e.g., Friday, weekends)
- **Time restrictions**: Deploy window (e.g., 9am-5pm)
- **Tests**: Commands to run before merge
- **Calls**: IceStreams playbooks or IceRuns functions to trigger

## Approval Workflows

### Day Restrictions
Configure blocked days per stage:
```json
{
  "blocked_days": [5, 6, 0],  // Friday, Saturday, Sunday
  "time_restrictions": {
    "start_hour": 9,
    "end_hour": 17,
    "timezone": "America/New_York"
  }
}
```

### Override Policy
When day/time is blocked:
- Standard approval threshold doesn't apply
- Override threshold (e.g., 2 approvers) is required
- Only approvers with `can_override=True` count toward override

## GitOps Integration

### YAML Schema
```yaml
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: my-application
spec:
  repository:
    url: https://github.com/org/my-app
    provider: github
  stages:
    - name: Alpha
      branch: alpha
      order: 1
      approval:
        minApprovers: 1
      tests:
        - name: Unit Tests
          command: npm test
```

### Export to YAML
1. Open flow detail page
2. Click "Export YAML"
3. Save to your GitOps repository

### Sync from YAML
Enable GitOps on a flow to auto-sync from YAML file changes.

## Notifications

### Supported Channels
- **Email**: SMTP configuration
- **Slack**: Webhook URL
- **Generic Webhook**: Custom endpoint with HMAC signature

### Events
- `promotion_requested` - New promotion awaiting approval
- `promotion_approved` - Approval received
- `promotion_rejected` - Rejection received
- `execution_started` - Pipeline started
- `execution_completed` - Pipeline succeeded
- `execution_failed` - Pipeline failed

## Troubleshooting

### Common Issues

**Promotion stuck in pending**
- Check approver configuration
- Verify user has `iceflows:approve` scope
- Check day/time restrictions

**Webhook not triggering**
- Verify webhook URL and secret
- Check webhook is enabled in repository settings
- Review webhook delivery logs in GitHub/GitLab

**Worker not processing tasks**
- Check Redis connection
- Verify worker container is running
- Review worker logs: `docker-compose logs iceflows-worker`

### Logs
```bash
# Worker logs
docker-compose logs -f iceflows-worker

# API logs
docker-compose logs -f api | grep iceflows
```
