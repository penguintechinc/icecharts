# IceCharts Connector Framework

The Connector Framework provides a modular, plugin-style architecture for integrating external services into IceCharts workflows. Connectors are defined declaratively in YAML manifests and automatically generate workflow nodes.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      IceCharts Connector Framework                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     Connector Registry                           │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │    │
│  │  │ WaddleBot │  │ WaddleAI  │  │   Elder   │  │  Future   │    │    │
│  │  │ Connector │  │ Connector │  │ Connector │  │ Connector │    │    │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │    │
│  │        └──────────────┴──────────────┴──────────────┘           │    │
│  │                              │                                   │    │
│  │              ┌───────────────▼───────────────┐                  │    │
│  │              │   Base Connector Class        │                  │    │
│  │              │   - HTTP Client (auth, retry) │                  │    │
│  │              │   - Node Generation           │                  │    │
│  │              │   - Config Schema Handling    │                  │    │
│  │              └───────────────────────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Generated Nodes                               │    │
│  │  Triggers: trigger_{connector}_{action}                         │    │
│  │  Actions:  action_{connector}_{action}                          │    │
│  │  Transforms: transform_{connector}_{action}                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Zero-code connector additions** - Add new connectors by creating a YAML manifest
- **Dynamic node generation** - Nodes created at runtime from manifest definitions
- **Schema-driven UI** - Config panels render from `config_schema` definitions
- **Variable interpolation** - Support for `{{input.field}}`, `{{config.field}}` syntax
- **Multi-output nodes** - Connector nodes support multiple input/output handles
- **Authentication support** - API Key and OAuth/JWT authentication methods

## Quick Start

### Using Connectors in Workflows

1. Open the **Playbook Editor**
2. In the left palette, scroll down to the **Connectors** section
3. Expand a connector (e.g., WaddleBot) to see its triggers, actions, and transforms
4. Drag nodes onto the canvas and connect them
5. Click a node to configure it using the schema-driven config panel

### Viewing Available Connectors

1. Go to **Settings** > **Connectors** tab
2. View all installed connectors with their node counts
3. Expand a connector to see available nodes and configuration status

## Creating a New Connector

### Step 1: Create the Manifest File

Create a YAML file in `services/icestreams-worker/connectors/manifests/`:

```yaml
# services/icestreams-worker/connectors/manifests/myservice.yaml
connector:
  id: myservice
  name: My Service
  description: Integration with My Service API
  icon: "🔧"
  color: "#4F46E5"
  version: "1.0.0"

  auth:
    methods:
      - type: api_key
        header: X-API-Key
        env_var: MYSERVICE_API_KEY

  connection:
    base_url_env: MYSERVICE_URL
    default_url: https://api.myservice.com
    health_endpoint: /health

  triggers:
    - id: webhook
      name: Webhook Event
      description: Triggered by incoming webhook
      icon: "🪝"
      webhook_path: /webhooks/myservice
      outputs:
        - name: out
          type: object
          description: Webhook payload
      config_schema:
        - field: event_type
          type: select
          label: Event Type
          options: [created, updated, deleted]
          required: true

  actions:
    - id: create_item
      name: Create Item
      description: Create a new item in My Service
      icon: "➕"
      endpoint: /api/items
      method: POST
      inputs:
        - name: in
          type: any
          required: true
      outputs:
        - name: out
          type: object
      config_schema:
        - field: name
          type: string
          label: Item Name
          placeholder: "New Item"
          required: true
          supports_variables: true
        - field: description
          type: textarea
          label: Description
          supports_variables: true

  transforms:
    - id: lookup_item
      name: Lookup Item
      description: Find an item by ID
      icon: "🔍"
      endpoint: /api/items/{id}
      method: GET
      inputs:
        - name: in
          type: any
          required: true
      outputs:
        - name: out
          type: object
      config_schema:
        - field: item_id
          type: string
          label: Item ID
          supports_variables: true
          required: true
```

### Step 2: Connector Discovery

Connectors are automatically discovered on startup. The framework:

1. Scans `connectors/manifests/` for `.yaml` files
2. Parses each manifest into a `ConnectorManifest` object
3. Registers the connector in the `ConnectorRegistry`
4. Generates node classes for each trigger, action, and transform

No code changes required - just add the manifest file!

## Manifest Schema Reference

### Connector Root

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (lowercase, no spaces) |
| `name` | string | Yes | Display name |
| `description` | string | Yes | Human-readable description |
| `icon` | string | Yes | Emoji or icon identifier |
| `color` | string | Yes | Hex color code for UI styling |
| `version` | string | Yes | Semver version string |
| `auth` | object | No | Authentication configuration |
| `connection` | object | No | Connection settings |
| `triggers` | array | No | Trigger definitions |
| `actions` | array | No | Action definitions |
| `transforms` | array | No | Transform definitions |

### Authentication Methods

```yaml
auth:
  methods:
    - type: api_key
      header: X-API-Key        # Header name for API key
      env_var: SERVICE_API_KEY # Environment variable name
    - type: oauth
      token_header: Authorization
      token_prefix: Bearer
      env_var: SERVICE_TOKEN
```

### Connection Settings

```yaml
connection:
  base_url_env: SERVICE_URL      # Env var for base URL
  default_url: http://localhost  # Default if env not set
  health_endpoint: /health       # Health check endpoint
```

### Trigger Definition

```yaml
triggers:
  - id: event_name           # Unique within connector
    name: Event Name         # Display name
    description: Description
    icon: "📢"
    webhook_path: /webhooks/service/event  # Webhook endpoint
    outputs:                 # Output ports
      - name: out
        type: object
        description: Event data
    config_schema: [...]     # Configuration fields
```

### Action Definition

```yaml
actions:
  - id: action_name
    name: Action Name
    description: Description
    icon: "⚡"
    endpoint: /api/resource  # API endpoint
    method: POST             # HTTP method
    inputs:                  # Input ports
      - name: in
        type: any
        required: true
    outputs:                 # Output ports
      - name: out
        type: object
    config_schema: [...]
```

### Transform Definition

```yaml
transforms:
  - id: transform_name
    name: Transform Name
    description: Description
    icon: "🔄"
    endpoint: /api/lookup
    method: GET
    inputs:
      - name: in
        type: any
        required: true
    outputs:
      - name: out
        type: object
    config_schema: [...]
```

### Config Schema Fields

| Field Type | Description | Options |
|------------|-------------|---------|
| `string` | Single-line text input | `placeholder`, `supports_variables` |
| `number` | Numeric input | `default`, `min`, `max` |
| `textarea` | Multi-line text input | `placeholder`, `supports_variables` |
| `select` | Dropdown selection | `options` (array of strings) |
| `multiselect` | Multi-select checkboxes | `options`, `default` (array) |
| `checkbox` | Boolean toggle | `default` (boolean) |

Example config field:

```yaml
config_schema:
  - field: message           # Field key in config object
    type: textarea
    label: Message           # UI label
    placeholder: "Hello {{username}}!"
    required: true
    supports_variables: true # Show {{...}} hint
    description: Message to send
```

## Variable Interpolation

Connector actions support variable interpolation using the `{{...}}` syntax:

| Pattern | Description | Example |
|---------|-------------|---------|
| `{{input.field}}` | Access input data field | `{{input.user.name}}` |
| `{{config.field}}` | Access config value | `{{config.channel_id}}` |
| `{{variable}}` | Access workflow variable | `{{username}}` |

Example:

```yaml
config_schema:
  - field: message
    type: textarea
    label: Message
    supports_variables: true
    placeholder: "Hello {{input.username}}! Your order {{input.order_id}} is ready."
```

## API Endpoints

### List Connectors

```
GET /api/v1/connectors
```

Response:
```json
{
  "connectors": [
    {
      "id": "waddlebot",
      "name": "WaddleBot",
      "icon": "🤖",
      "color": "#6366F1",
      "version": "1.0.0",
      "triggers": [...],
      "actions": [...],
      "transforms": [...]
    }
  ]
}
```

### Get Connector

```
GET /api/v1/connectors/{connector_id}
```

### Get Connector Nodes

```
GET /api/v1/connectors/{connector_id}/nodes
```

### Get All Nodes

```
GET /api/v1/connectors/nodes?category=actions
```

Query parameters:
- `category`: Filter by `triggers`, `actions`, or `transforms`

## File Structure

```
services/icestreams-worker/
├── connectors/
│   ├── __init__.py           # Package exports
│   ├── base.py               # Base classes and dataclasses
│   ├── registry.py           # ConnectorRegistry singleton
│   ├── node_generator.py     # Dynamic node generation
│   ├── executor.py           # Action execution logic
│   └── manifests/
│       ├── waddlebot.yaml    # WaddleBot connector
│       └── elder.yaml        # Elder connector

services/flask-backend/
└── app/api/v1/
    └── connectors.py         # REST API endpoints

services/webui/src/client/
├── types/
│   └── connector.ts          # TypeScript interfaces
├── hooks/
│   └── useConnectors.ts      # React hooks
├── components/playbooks/
│   ├── ConnectorSection.tsx  # Palette component
│   └── panels/
│       └── ConnectorConfigPanel.tsx  # Config form
└── pages/
    └── Settings.tsx          # Connectors settings tab
```

## Available Connectors

### WaddleBot

Chat bot platform integration for Twitch, Discord, Slack, and Kick.

**Triggers (4):**
- `command` - Chat command execution
- `event` - Stream events (subscriptions, follows, raids)
- `message` - Chat message pattern matching
- `webhook` - Incoming HTTP webhooks

**Actions (15):**
- `send_chat` - Send chat message
- `send_reply` - Reply to message
- `send_whisper` - Send private message
- `display_media` - Show media overlay
- `update_ticker` - Update stream ticker
- `show_alert` - Display alert overlay
- `shoutout` - Shoutout streamer
- `ai_response` - Get AI response
- `spotify_play` - Control Spotify
- `youtube_play` - Control YouTube Music
- `inventory_add` - Add inventory items
- `loyalty_give` - Award loyalty points
- `reputation_update` - Update reputation
- `timeout_user` - Timeout user
- `ban_user` - Ban user

**Transforms (2):**
- `user_lookup` - Fetch user information
- `command_check` - Validate permissions

---

### Elder

Infrastructure discovery, documentation, and dependency mapping platform integration.

**Configuration:**
```env
ELDER_URL=http://localhost:5000
ELDER_API_KEY=your-api-key
# OR for OAuth
ELDER_TOKEN=your-jwt-token
```

**Triggers (8):**
| ID | Name | Description |
|----|------|-------------|
| `entity_created` | Entity Created | Triggered when a new entity is discovered |
| `entity_updated` | Entity Updated | Triggered when an entity is modified |
| `entity_deleted` | Entity Deleted | Triggered when an entity is removed |
| `issue_created` | Issue Created | Triggered when a new issue is reported |
| `issue_status_changed` | Issue Status Changed | Triggered when issue status changes |
| `webhook_event` | Webhook Event | Generic webhook receiver for Elder events |
| `discovery_completed` | Discovery Completed | Triggered when a discovery job finishes |
| `vulnerability_detected` | Vulnerability Detected | Triggered when SBOM scan finds vulnerability |
| `dependency_changed` | Dependency Changed | Triggered when entity dependencies change |

**Actions (18):**
| ID | Name | Description |
|----|------|-------------|
| `create_entity` | Create Entity | Create a new entity in Elder |
| `update_entity` | Update Entity | Update an existing entity |
| `delete_entity` | Delete Entity | Remove an entity from Elder |
| `create_dependency` | Create Dependency | Create a dependency relationship |
| `remove_dependency` | Remove Dependency | Remove a dependency relationship |
| `create_issue` | Create Issue | Report a new issue for an entity |
| `update_issue` | Update Issue | Update an existing issue |
| `add_comment` | Add Comment | Add a comment to an issue |
| `link_entity_issue` | Link Entity to Issue | Associate an entity with an issue |
| `create_project` | Create Project | Create a new project |
| `create_milestone` | Create Milestone | Create a project milestone |
| `trigger_discovery` | Trigger Discovery | Start an infrastructure discovery job |
| `run_sbom_scan` | Run SBOM Scan | Scan entity for software bill of materials |
| `add_identity` | Add Identity | Add an identity/credential to an entity |
| `send_notification` | Send Notification | Send notification via Elder |
| `allocate_ip` | Allocate IP Address | Allocate an IP from IPAM |
| `release_ip` | Release IP Address | Release an IP back to IPAM pool |
| `create_webhook` | Create Webhook | Register a new webhook subscription |

**Transforms (7):**
| ID | Name | Description |
|----|------|-------------|
| `entity_lookup` | Lookup Entity | Fetch entity details by ID |
| `search_entities` | Search Entities | Search entities by criteria |
| `get_dependencies` | Get Dependencies | Get entity dependencies (upstream/downstream) |
| `graph_traverse` | Traverse Graph | Traverse the entity dependency graph |
| `impact_analysis` | Impact Analysis | Analyze impact of an entity change |
| `issue_lookup` | Lookup Issue | Fetch issue details by ID |
| `check_vulnerabilities` | Check Vulnerabilities | Check entity for known vulnerabilities |

**Example Workflows:**

*Auto-create issue when vulnerability detected:*
```
[Vulnerability Detected] → [Create Issue] → [Send Notification]
                              ↳ severity: critical
                              ↳ title: "CVE-{{input.cve_id}} detected"
```

*Dependency impact notification:*
```
[Entity Updated] → [Impact Analysis] → [If] → [Send Notification]
                                        ↳ condition: affected_count > 0
```

*Automated infrastructure discovery:*
```
[Schedule Trigger] → [Trigger Discovery] → [Entity Created] → [Create Issue]
                         ↳ discovery_type: kubernetes    ↳ if: entity.status == 'unhealthy'
```

## Troubleshooting

### Connector Not Appearing

1. Check manifest file location: `connectors/manifests/*.yaml`
2. Verify YAML syntax is valid
3. Check API logs for parsing errors
4. Ensure connector ID is unique

### Authentication Failures

1. Verify environment variables are set
2. Check API key/token format
3. Review connector logs for auth errors

### Node Configuration Issues

1. Verify config_schema field types match expected values
2. Check required fields are properly marked
3. Ensure variable interpolation syntax is correct

## Future Connectors

The Connector Framework is designed for easy expansion:

- **WaddleAI** - AI/ML model integration
- **Custom connectors** - Create your own integrations

To add a new connector, simply create a YAML manifest in `services/icestreams-worker/connectors/manifests/` following the schema reference above.

## See Also

- [WORKFLOWS.md](WORKFLOWS.md) - Workflow system documentation
- [API_REFERENCE.md](API_REFERENCE.md) - Complete API documentation
- [INTEGRATION.md](INTEGRATION.md) - External integration guide
