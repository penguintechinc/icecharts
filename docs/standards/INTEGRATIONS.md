# 🔌 Integrations Guide - Connecting All The Things
# Integration Standards

Part of [Development Standards](../STANDARDS.md)

---

## Overview

This guide covers integrating your application with external services and platforms. We support three major integrations to power your apps:

- **🤖 WaddleAI** - AI and machine learning features (optional, when you need smarts)
- **🚦 MarchProxy** - Load balancing and API gateway (recommended for production)
- **🔑 License Server** - Feature gating and entitlements (enterprise control)

Each integration is optional depending on your needs, but when you use them, follow these patterns.

---

## 🚦 MarchProxy (Load Balancer & API Gateway)

Your app runs behind **MarchProxy** (`~/code/MarchProxy`) for routing, load balancing, and API gateway features.

**Important:** Don't include MarchProxy in your `docker-compose.yml` - it's external infrastructure managed separately. Just generate config files and import them via MarchProxy's API.

### How It Works

1. Your services run in containers (Flask API, Go backend, React WebUI)
2. MarchProxy handles routing, TLS termination, and load balancing
3. You generate config files describing your services
4. Import config via MarchProxy REST API
5. MarchProxy routes traffic to your containers

### Service Configuration

Generate service definitions in `config/marchproxy/services.json`:
## MarchProxy API Gateway Integration

Applications are expected to run behind **MarchProxy** (`~/code/MarchProxy`) for API gateway and load balancing functionality.

**IMPORTANT:** Do NOT include MarchProxy in the application's `docker-compose.yml` - it's external infrastructure managed separately.

### Configuration Export

Generate MarchProxy-compatible import configuration files in `config/marchproxy/`:

```
config/
└── marchproxy/
    ├── services.json          # Service definitions
    ├── mappings.json          # Route mappings
    └── import-config.json     # Combined import file
```

### Service Definition Format

```json
{
  "services": [
    {
      "name": "myapp-flask-api",
      "ip_fqdn": "flask-backend",
      "port": 8080,
      "protocol": "http",
      "collection": "myapp",
      "auth_type": "jwt",
      "tls_enabled": false,
      "health_check_enabled": true,
      "health_check_path": "/healthz",
      "health_check_interval": 30
    },
    {
      "name": "myapp-go-backend",
      "ip_fqdn": "go-backend",
      "port": 50051,
      "protocol": "grpc",
      "collection": "myapp",
      "auth_type": "none",
      "tls_enabled": false,
      "health_check_enabled": true,
      "health_check_path": "/grpc.health.v1.Health/Check",
      "health_check_interval": 10
    },
    {
      "name": "myapp-webui",
      "ip_fqdn": "webui",
      "port": 80,
      "protocol": "http",
      "collection": "myapp",
      "health_check_enabled": true,
      "health_check_path": "/"
      "auth_type": "none",
      "tls_enabled": false,
      "health_check_enabled": true,
      "health_check_path": "/",
      "health_check_interval": 30
    }
  ]
}
```

**Key fields:**
- `name`: Use `{app_name}-{service}` for easy filtering
- `protocol`: `http` (REST), `grpc` (high-performance), `tcp` (raw)
- `auth_type`: `jwt` (external APIs), `none` (internal gRPC)
- `health_check_enabled`: Always true for production

### Route Configuration

Define routes in `config/marchproxy/mappings.json`:
### Mapping Definition Format

```json
{
  "mappings": [
    {
      "name": "myapp-external-api",
      "description": "External REST API access",
      "source_services": ["external"],
      "dest_services": ["myapp-flask-api"],
      "listen_port": 443,
      "protocol": "https",
      "path_prefix": "/api/v1"
    },
    {
      "name": "myapp-webui-access",
      "description": "WebUI frontend access",
      "source_services": ["external"],
      "dest_services": ["myapp-webui"],
      "listen_port": 443,
      "protocol": "https",
      "path_prefix": "/"
    }
  ]
}
```

### Python Config Generator

Auto-generate MarchProxy config from your app settings:

```python
"""Generate MarchProxy import configuration"""
### Import Script

Create `scripts/marchproxy-import.sh`:

```bash
#!/bin/bash
# Import service configuration into MarchProxy

MARCHPROXY_API="${MARCHPROXY_API:-http://localhost:8000}"
CLUSTER_API_KEY="${CLUSTER_API_KEY:-}"

if [ -z "$CLUSTER_API_KEY" ]; then
    echo "Error: CLUSTER_API_KEY environment variable required"
    exit 1
fi

# Import services
curl -X POST "$MARCHPROXY_API/api/v1/services/import" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $CLUSTER_API_KEY" \
    -d @config/marchproxy/import-config.json

echo "MarchProxy configuration imported"
```

### Python Configuration Generator

```python
"""Generate MarchProxy import configuration from application settings"""
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class MarchProxyService:
    name: str
    ip_fqdn: str
    port: int
    protocol: str = "http"
    collection: Optional[str] = None
    auth_type: str = "none"
    tls_enabled: bool = False
    health_check_enabled: bool = True
    health_check_path: str = "/healthz"
    health_check_interval: int = 30

def generate_marchproxy_config(app_name: str, services: list[MarchProxyService]) -> dict:
    """Generate MarchProxy-compatible configuration"""
    """Generate MarchProxy-compatible import configuration"""
    return {
        "services": [asdict(s) for s in services],
        "metadata": {
            "app_name": app_name,
            "generated_by": "project-template",
            "version": os.getenv("APP_VERSION", "0.0.0")
        }
    }

def write_marchproxy_config(config: dict, output_dir: str = "config/marchproxy"):
    """Write configuration to file"""
    os.makedirs(output_dir, exist_ok=True)
    """Write configuration files for MarchProxy import"""
    os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/import-config.json", "w") as f:
        json.dump(config, f, indent=2)

# Example usage
if __name__ == "__main__":
    services = [
        MarchProxyService(
            name="myapp-flask-api",
            ip_fqdn="flask-backend",
            port=8080,
            protocol="http",
            collection="myapp",
            auth_type="jwt"
        ),
        MarchProxyService(
            name="myapp-go-backend",
            ip_fqdn="go-backend",
            port=50051,
            protocol="grpc"
        ),
    ]
            protocol="grpc",
            collection="myapp"
        ),
    ]

    config = generate_marchproxy_config("myapp", services)
    write_marchproxy_config(config)
```

### Import Script

Create `scripts/marchproxy-import.sh` to import your config:

```bash
#!/bin/bash
MARCHPROXY_API="${MARCHPROXY_API:-http://localhost:8000}"
CLUSTER_API_KEY="${CLUSTER_API_KEY:-}"

if [ -z "$CLUSTER_API_KEY" ]; then
    echo "Error: CLUSTER_API_KEY environment variable required"
    exit 1
fi

curl -X POST "$MARCHPROXY_API/api/v1/services/import" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $CLUSTER_API_KEY" \
    -d @config/marchproxy/import-config.json

echo "MarchProxy configuration imported"
```

### MarchProxy API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/services` | POST | Create a service |
| `/api/v1/services/import` | POST | Bulk import services |
| `/api/v1/services` | GET | List all services |
### Integration Notes

1. **Service Names**: Use `{app_name}-{service}` naming convention for easy filtering
2. **Collection**: Group all app services under same collection for bulk operations
3. **Protocol Selection**:
   - `http`/`https`: REST API endpoints (Flask)
   - `grpc`: Internal high-performance services (Go backend)
   - `tcp`: Raw TCP connections
4. **Health Checks**: Always enable for production services
5. **Auth Type**: Use `jwt` for external-facing APIs, `none` for internal gRPC

### MarchProxy API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/services` | POST | Create service |
| `/api/v1/services/import` | POST | Bulk import services |
| `/api/v1/services` | GET | List services |
| `/api/v1/services/{id}` | PUT | Update service |
| `/api/v1/services/{id}` | DELETE | Delete service |
| `/api/v1/config/{cluster_id}` | GET | Get cluster config |

📚 **Full docs:** See `~/code/MarchProxy/api-server/README.md`

---

## 🤖 WaddleAI Integration

Add AI superpowers to your app with WaddleAI - NLP, ML inference, chatbots, and more.

### When to Use WaddleAI

Consider WaddleAI if your app needs:
- Natural language processing (sentiment analysis, text classification)
- Machine learning model inference
- Chatbots or conversational interfaces
- Document understanding and extraction
- Predictive analytics
- AI-powered automation

**Not needed?** Skip it. It's optional and only adds complexity if you don't use it.

### Architecture Pattern

WaddleAI runs as a separate microservice in your docker-compose:

```
services/
├── flask-backend/     # Your Flask API
├── webui/            # Your React frontend
├── go-backend/       # Optional: High-performance backend
└── ai/               # Optional: WaddleAI service (if using AI)
```

### Setup Steps

**1. Add WaddleAI to your project:**

```bash
git submodule add ~/code/WaddleAI services/ai/waddleai
```

**2. Update docker-compose.dev.yml:**

```yaml
version: '3.8'

services:
  flask-backend:
    build: ./services/flask-backend
📚 **Full MarchProxy Documentation**: See `~/code/MarchProxy/api-server/README.md`

---

## WaddleAI Integration

**Optional AI capabilities - integrate only when AI features are required**

### When to Use WaddleAI

Consider WaddleAI integration for projects requiring:
- Natural language processing (NLP)
- Machine learning model inference
- AI-powered features and automation
- Intelligent data analysis
- Chatbots and conversational interfaces
- Document understanding and extraction
- Predictive analytics

### Architecture Pattern

**WaddleAI runs as a separate microservice:**

```
project-name/
├── services/
│   ├── api/           # Flask backend API
│   ├── webui/         # ReactJS frontend
│   ├── connector/     # Integration services
│   └── ai/            # WaddleAI service (optional)
```

### Integration Setup

**1. Reference WaddleAI from ~/code/WaddleAI:**

```bash
# Add as git submodule or copy required components
git submodule add ~/code/WaddleAI services/ai/waddleai
```

**2. Docker Compose Integration:**

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  api:
    build: ./services/api
    environment:
      - WADDLEAI_URL=http://waddleai:8000
    depends_on:
      - waddleai

  waddleai:
    build: ./services/ai/waddleai
    environment:
      - MODEL_PATH=/models
      - MAX_WORKERS=4
    volumes:
      - ai-models:/models
    # Internal only - not exposed to host
    # Not exposed to host - internal network only

volumes:
  ai-models:
```

**3. Python API client for Flask backend:**
### API Client for WaddleAI

**Python integration in Flask backend:**

```python
import os
import httpx
from typing import Dict, Any, Optional

class WaddleAIClient:
    """Client for WaddleAI service"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv('WADDLEAI_URL', 'http://localhost:8000')
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def analyze_text(self, text: str, task: str = "sentiment") -> Dict[str, Any]:
        """Analyze text with AI model"""
        response = await self.client.post(
            "/api/v1/analyze",
            json={"text": text, "task": task}
        )
        response.raise_for_status()
        return response.json()

    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate AI response"""
        response = await self.client.post(
            "/api/v1/generate",
            json={"prompt": prompt, "context": context}
        )
        response.raise_for_status()
        return response.json()["response"]

    async def close(self):
        await self.client.aclose()

# Flask integration
from flask import Flask, request, jsonify
from shared.licensing import requires_feature

app = Flask(__name__)
ai_client = WaddleAIClient()

@app.route('/api/v1/ai/analyze', methods=['POST'])
@app.route('/api/ai/analyze', methods=['POST'])
@auth_required()
@requires_feature('ai_analysis')  # License-gate AI features
async def ai_analyze():
    """AI-powered analysis - enterprise feature"""
    data = request.get_json()
    result = await ai_client.analyze_text(data['text'], data.get('task', 'sentiment'))
    return jsonify(result)
```

**4. React component to use AI features:**

```javascript
import { useState } from 'react';
import { apiClient } from '../services/apiClient';

const aiService = {
  analyzeText: (text, task = 'sentiment') =>
    apiClient.post('/api/v1/ai/analyze', { text, task })
};

**ReactJS integration:**

```javascript
// src/services/aiClient.js
import { apiClient } from './apiClient';

export const aiService = {
  async analyzeText(text, task = 'sentiment') {
    const response = await apiClient.post('/api/ai/analyze', { text, task });
    return response.data;
  },

  async generateResponse(prompt, context = null) {
    const response = await apiClient.post('/api/ai/generate', { prompt, context });
    return response.data;
  }
};

// React component
import { useState } from 'react';
import { aiService } from '../services/aiClient';

export const AIAnalyzer = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);

  return (
    <div>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={async () => {
        const res = await aiService.analyzeText(text);
        setResult(res.data);
      }}>Analyze</button>
  const handleAnalyze = async () => {
    const analysis = await aiService.analyzeText(text);
    setResult(analysis);
  };

  return (
    <div>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={handleAnalyze}>Analyze</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
};
```

### AI Features License Gating

AI features should be enterprise/professional tier only:

```python
# Define feature tiers
AI_FEATURES = {
    'ai_analysis': 'professional',      # Professional tier+
    'ai_generation': 'professional',    # Professional tier+
    'ai_training': 'enterprise',        # Enterprise only
    'ai_custom_models': 'enterprise'    # Enterprise only
}

# Check what's available
### License-Gating AI Features

**ALWAYS make AI features enterprise-only:**

```python
# License configuration
AI_FEATURES = {
    'ai_analysis': 'professional',      # Professional tier+
    'ai_generation': 'professional',    # Professional tier+
    'ai_training': 'enterprise',        # Enterprise tier only
    'ai_custom_models': 'enterprise'    # Enterprise tier only
}

# Feature checking
from shared.licensing import license_client

def check_ai_features():
    """Check available AI features based on license"""
    features = {}
    for feature, required_tier in AI_FEATURES.items():
        features[feature] = license_client.has_feature(feature)
    return features
```

### Environment Variables

```bash
# WaddleAI service configuration
WADDLEAI_URL=http://waddleai:8000
WADDLEAI_API_KEY=optional-api-key
WADDLEAI_MODEL_PATH=/models
WADDLEAI_MAX_WORKERS=4
WADDLEAI_TIMEOUT=30

# License-gated AI features
AI_FEATURES_ENABLED=true
```

### Important Notes

1. **Optional**: Only add if you actually need AI features
2. **License-gated**: Make AI enterprise/professional tier
3. **Resource-intensive**: Monitor GPU/CPU usage if using inference
4. **Isolated**: Separate container prevents resource conflicts
5. **Docs**: See `~/code/WaddleAI` for detailed integration

---

## 🔑 License Server Integration

PenguinTech License Server manages feature entitlements and licensing at `https://license.penguintech.io`.

### Why License Server?

- **Feature gating**: Enable/disable features based on subscription tier
- **Entitlement checking**: Know what customers are licensed for
- **Usage tracking**: Report active users, storage, teams
- **Tier enforcement**: Community, Professional, Enterprise

### Environment Setup
1. **Optional Integration**: Only add WaddleAI when AI features are needed
2. **License Gating**: AI features are typically enterprise/professional tier
3. **Performance**: AI inference can be resource-intensive - monitor usage
4. **Isolation**: Run WaddleAI as separate service for resource isolation
5. **Documentation**: Refer to WaddleAI documentation at `~/code/WaddleAI`

---

## Configuration Management Standards

**ALL integration and system configuration MUST follow this pattern:**

### Configuration Hierarchy

1. **Initial Setup**: Docker environment variables provide bootstrap configuration
2. **Database Storage**: Validated config written to database `config` table(s)
3. **Runtime Management**: APIs and WebUI allow updates by global admins
4. **Precedence**: Database config overrides environment variables after initial setup

### Database Schema

**REQUIRED: Create `config` table for all configuration storage**

```sql
CREATE TABLE config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(50) NOT NULL,  -- 'string', 'integer', 'boolean', 'json'
    category VARCHAR(100) NOT NULL,     -- 'integration', 'system', 'security', etc.
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),            -- User who made the change
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_config_category ON config(category);
CREATE INDEX idx_config_key ON config(config_key);
```

**PyDAL Table Definition:**
```python
db.define_table('config',
    Field('config_key', 'string', unique=True, required=True),
    Field('config_value', 'text', required=True),
    Field('config_type', 'string', requires=IS_IN_SET(['string', 'integer', 'boolean', 'json'])),
    Field('category', 'string', requires=IS_IN_SET(['integration', 'system', 'security', 'database', 'email'])),
    Field('description', 'text'),
    Field('is_sensitive', 'boolean', default=False),
    Field('last_updated', 'datetime', default=request.now, update=request.now),
    Field('updated_by', 'string'),
    Field('created_at', 'datetime', default=request.now),
    migrate=True
)
```

### Bootstrap Process

**On application startup:**

1. **Load Environment Variables**
2. **Validate Configuration** (check required fields, validate formats)
3. **Check Database** for existing config
4. **Initialize Database Config** if not exists
5. **Use Database Config** for runtime

**Example Bootstrap Code:**

```python
# app.py or config/bootstrap.py
import os
from pydal import DAL, Field

def bootstrap_configuration(db):
    """
    Bootstrap configuration from environment variables on first run.
    After initial setup, database config takes precedence.
    """

    # Define config mappings
    config_mappings = {
        # Integration settings
        'smtp_host': {
            'env': 'SMTP_HOST',
            'category': 'email',
            'type': 'string',
            'description': 'SMTP server hostname',
            'sensitive': False
        },
        'smtp_port': {
            'env': 'SMTP_PORT',
            'category': 'email',
            'type': 'integer',
            'description': 'SMTP server port',
            'sensitive': False
        },
        'smtp_user': {
            'env': 'SMTP_USER',
            'category': 'email',
            'type': 'string',
            'description': 'SMTP username',
            'sensitive': False
        },
        'smtp_pass': {
            'env': 'SMTP_PASS',
            'category': 'email',
            'type': 'string',
            'description': 'SMTP password',
            'sensitive': True
        },
        'waddleai_url': {
            'env': 'WADDLEAI_URL',
            'category': 'integration',
            'type': 'string',
            'description': 'WaddleAI API endpoint',
            'sensitive': False
        },
        'waddleai_api_key': {
            'env': 'WADDLEAI_API_KEY',
            'category': 'integration',
            'type': 'string',
            'description': 'WaddleAI API key',
            'sensitive': True
        },
    }

    for config_key, config_meta in config_mappings.items():
        # Check if config already exists in database
        existing = db(db.config.config_key == config_key).select().first()

        if not existing:
            # Get value from environment variable
            env_value = os.getenv(config_meta['env'])

            if env_value:
                # Validate and insert into database
                validated_value = validate_config(
                    env_value,
                    config_meta['type']
                )

                if validated_value is not None:
                    db.config.insert(
                        config_key=config_key,
                        config_value=str(validated_value),
                        config_type=config_meta['type'],
                        category=config_meta['category'],
                        description=config_meta['description'],
                        is_sensitive=config_meta['sensitive'],
                        updated_by='system'
                    )
                    print(f"✓ Initialized config: {config_key}")

    db.commit()

def validate_config(value, config_type):
    """Validate configuration value based on type"""
    try:
        if config_type == 'integer':
            return int(value)
        elif config_type == 'boolean':
            return value.lower() in ['true', '1', 'yes']
        elif config_type == 'json':
            import json
            return json.dumps(json.loads(value))  # Validate JSON
        else:  # string
            return value
    except Exception as e:
        print(f"✗ Validation failed for {value}: {e}")
        return None

def get_config(db, config_key, default=None):
    """Get configuration value from database"""
    config = db(db.config.config_key == config_key).select().first()
    if config:
        # Parse based on type
        if config.config_type == 'integer':
            return int(config.config_value)
        elif config.config_type == 'boolean':
            return config.config_value.lower() in ['true', '1', 'yes']
        elif config.config_type == 'json':
            import json
            return json.loads(config.config_value)
        else:
            return config.config_value
    return default

# Call during application startup
bootstrap_configuration(db)
```

### API Endpoints for Configuration Management

**REQUIRED: Implement configuration management API**

**Authorization**: Global admin privileges ONLY

```python
from flask import Flask, request, jsonify
from flask_security import auth_required, roles_required, current_user

@app.route('/api/v1/config', methods=['GET'])
@auth_required()
@roles_required('admin')
def list_config():
    """List all configuration settings (masks sensitive values)"""
    configs = db(db.config).select(orderby=db.config.category)

    result = []
    for config in configs:
        result.append({
            'key': config.config_key,
            'value': '***SENSITIVE***' if config.is_sensitive else config.config_value,
            'type': config.config_type,
            'category': config.category,
            'description': config.description,
            'last_updated': config.last_updated.isoformat(),
            'updated_by': config.updated_by
        })

    return jsonify({'configs': result})

@app.route('/api/v1/config/<config_key>', methods=['GET'])
@auth_required()
@roles_required('admin')
def get_config_endpoint(config_key):
    """Get single configuration value"""
    config = db(db.config.config_key == config_key).select().first()

    if not config:
        return jsonify({'error': 'Configuration not found'}), 404

    return jsonify({
        'key': config.config_key,
        'value': '***SENSITIVE***' if config.is_sensitive else config.config_value,
        'type': config.config_type,
        'category': config.category,
        'description': config.description,
        'last_updated': config.last_updated.isoformat()
    })

@app.route('/api/v1/config/<config_key>', methods=['PUT'])
@auth_required()
@roles_required('admin')
def update_config(config_key):
    """Update configuration value"""
    data = request.get_json()
    new_value = data.get('value')

    if new_value is None:
        return jsonify({'error': 'Value is required'}), 400

    config = db(db.config.config_key == config_key).select().first()

    if not config:
        return jsonify({'error': 'Configuration not found'}), 404

    # Validate new value
    validated_value = validate_config(new_value, config.config_type)

    if validated_value is None:
        return jsonify({'error': 'Invalid value for config type'}), 400

    # Update configuration
    config.update_record(
        config_value=str(validated_value),
        updated_by=current_user.email
    )
    db.commit()

    return jsonify({
        'message': 'Configuration updated successfully',
        'key': config_key,
        'updated_by': current_user.email
    })

@app.route('/api/v1/config/<config_key>', methods=['DELETE'])
@auth_required()
@roles_required('admin')
def delete_config(config_key):
    """Delete configuration (admin only, use with caution)"""
    config = db(db.config.config_key == config_key).select().first()

    if not config:
        return jsonify({'error': 'Configuration not found'}), 404

    db(db.config.config_key == config_key).delete()
    db.commit()

    return jsonify({
        'message': 'Configuration deleted successfully',
        'key': config_key
    })
```

### WebUI Configuration Management

**REQUIRED: Implement Settings/Configuration page**

**Location**: `/settings` or `/admin/config`

**Features**:
- List all configuration by category
- Edit configuration values (admins only)
- Mask sensitive values (passwords, API keys)
- Validate input based on config type
- Show last updated timestamp and user
- Search and filter by category

**Example React Component:**

```jsx
// src/pages/Settings/Configuration.jsx
import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/apiClient';

export function ConfigurationPage() {
  const [configs, setConfigs] = useState([]);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    const response = await apiClient.get('/api/v1/config');
    setConfigs(response.data.configs);
  };

  const handleUpdate = async (key, value) => {
    try {
      await apiClient.put(`/api/v1/config/${key}`, { value });
      setEditing(null);
      loadConfigs();
    } catch (err) {
      alert('Failed to update configuration');
    }
  };

  // Group by category
  const groupedConfigs = configs.reduce((acc, config) => {
    if (!acc[config.category]) acc[config.category] = [];
    acc[config.category].push(config);
    return acc;
  }, {});

  return (
    <div className="configuration-page">
      <h1>System Configuration</h1>

      {Object.entries(groupedConfigs).map(([category, items]) => (
        <div key={category} className="config-category">
          <h2>{category.toUpperCase()}</h2>

          <table>
            <thead>
              <tr>
                <th>Setting</th>
                <th>Value</th>
                <th>Description</th>
                <th>Last Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((config) => (
                <tr key={config.key}>
                  <td><code>{config.key}</code></td>
                  <td>
                    {editing === config.key ? (
                      <input
                        type={config.value === '***SENSITIVE***' ? 'password' : 'text'}
                        defaultValue={config.value}
                        onBlur={(e) => handleUpdate(config.key, e.target.value)}
                      />
                    ) : (
                      config.value
                    )}
                  </td>
                  <td>{config.description}</td>
                  <td>{new Date(config.last_updated).toLocaleString()}</td>
                  <td>
                    <button onClick={() => setEditing(config.key)}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
```

### Security Considerations

1. **Sensitive Values**:
   - Mark passwords, API keys, tokens as `is_sensitive=True`
   - Mask sensitive values in API responses and UI
   - Never log sensitive configuration values

2. **Authorization**:
   - ONLY global admin role can view/edit configuration
   - Log all configuration changes with user attribution
   - Consider additional audit logging for sensitive changes

3. **Validation**:
   - Always validate configuration values before saving
   - Prevent SQL injection and XSS attacks
   - Validate URLs, email addresses, port numbers, etc.

4. **Encryption**:
   - Consider encrypting sensitive values at rest in database
   - Use application-level encryption for passwords/API keys
   - Never store plaintext credentials

### Configuration Categories

**Standard categories**:
- `integration` - External service integrations (WaddleAI, etc.)
- `email` - SMTP and email settings
- `security` - Security-related settings (TLS, auth)
- `database` - Database connection settings
- `system` - General system settings
- `license` - License server configuration

### Key Principles

1. **Environment Variables for Bootstrap**: Initial setup from Docker env vars
2. **Database as Source of Truth**: Config stored in database after validation
3. **Admin-Only Management**: Only global admins can modify configuration
4. **Runtime Updates**: Changes take effect without container restart
5. **Audit Trail**: Track who changed what and when
6. **Validation**: Always validate before storing
7. **Security**: Mask/encrypt sensitive values

---

## License Server Integration

PenguinTech License Server provides feature gating and entitlement management at `https://license.penguintech.io`.

### Environment Variables

```bash
# License Configuration
LICENSE_KEY=PENG-XXXX-XXXX-XXXX-XXXX-ABCD
LICENSE_SERVER_URL=https://license.penguintech.io
PRODUCT_NAME=project-template
RELEASE_MODE=false  # Dev: false (all features), Prod: true (enforce license)
RELEASE_MODE=false  # Enable license enforcement (dev: false, prod: true)
```

### Validation Flow

On startup:
1. Read license key from environment
2. Call license server to validate
3. Get back: tier, features[], expiration, limits
4. Cache result locally
5. Run hourly keepalive with usage stats

Error handling:
- **Validation fails (RELEASE_MODE=true)**: Exit with error
- **Validation fails (RELEASE_MODE=false)**: Warn, continue (development)
- **Network error**: Cache previous result, retry on next startup
- **Feature not entitled**: Return 403 Forbidden
```
1. Application startup → License validation
2. Return: { valid, tier, features[], expires_at, limits }
3. Conditional behavior based on tier and features
4. Hourly keepalive with usage stats
```

### Feature Gating

```python
# Python: Check feature entitlement
from app.license import license_manager

@require_feature('sso_integration')
def enable_sso():
    # Only runs if license allows SSO
    # Only runs if tier supports SSO
    pass

# Manual check
if license_manager.is_feature_enabled('audit_logs'):
    # Log important actions
    # Log to audit table
    pass
```

### Tiers and Features

```
Community (free):
├── Basic auth (email/password)
├── Basic authentication (email/password)
├── Up to 5 users
└── Single team

Professional:
├── Community features +
├── SSO/OAuth2
├── Multiple teams
├── API keys
└── Audit logging

Enterprise:
├── Professional features +
├── Custom SAML
├── Advanced analytics
└── Priority support
```

### Keepalive Check-in

Every hour, report usage to license server:
### Keepalive/Checkin

Background task runs hourly:

```python
{
  "license_key": "PENG-XXXX-XXXX-XXXX-XXXX-ABCD",
  "product": "project-template",
  "usage": {
    "active_users": 42,
    "team_count": 8,
    "storage_gb": 125
  }
}
```

---

## 🔧 Configuration Management

All integrations and system settings follow one pattern: **Environment variables for bootstrap, database for runtime**.

### Setup Process

1. **Docker startup** → Read environment variables
2. **Validate** → Check formats, required fields
3. **Database check** → See if config already exists
4. **Initialize** → Write validated config to database
5. **Runtime** → Use database config (takes precedence)

### Database Schema

Create `config` table for storing configuration:

```sql
CREATE TABLE config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(50) NOT NULL,  -- 'string', 'integer', 'boolean', 'json'
    category VARCHAR(100) NOT NULL,    -- 'integration', 'system', 'security', etc.
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),           -- User who made the change
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_config_category ON config(category);
CREATE INDEX idx_config_key ON config(config_key);
```

### PyDAL Table Definition

```python
db.define_table('config',
    Field('config_key', 'string', unique=True, required=True),
    Field('config_value', 'text', required=True),
    Field('config_type', 'string', requires=IS_IN_SET(['string', 'integer', 'boolean', 'json'])),
    Field('category', 'string', requires=IS_IN_SET(['integration', 'system', 'security', 'database', 'email'])),
    Field('description', 'text'),
    Field('is_sensitive', 'boolean', default=False),
    Field('last_updated', 'datetime', default=request.now, update=request.now),
    Field('updated_by', 'string'),
    Field('created_at', 'datetime', default=request.now),
    migrate=True
)
```

### Bootstrap Function

```python
import os, json

def bootstrap_configuration(db):
    """Bootstrap config from env vars on first run"""
    mappings = {
        'smtp_host': ('SMTP_HOST', 'email', 'string', 'SMTP server', False),
        'waddleai_url': ('WADDLEAI_URL', 'integration', 'string', 'WaddleAI endpoint', False),
    }

    for key, (env, cat, typ, desc, sens) in mappings.items():
        if not db(db.config.config_key == key).select().first():
            val = os.getenv(env)
            if val and (v := validate_config(val, typ)):
                db.config.insert(
                    config_key=key, config_value=str(v), config_type=typ,
                    category=cat, description=desc, is_sensitive=sens, updated_by='system'
                )
    db.commit()

def validate_config(value, config_type):
    """Validate and parse config value"""
    try:
        if config_type == 'integer': return int(value)
        elif config_type == 'boolean': return value.lower() in ['true', '1', 'yes']
        elif config_type == 'json': return json.dumps(json.loads(value))
        else: return value
    except: return None
```

### Admin API Endpoints

Expose configuration management to admins only:

```python
from flask import Flask, request, jsonify
from flask_security import auth_required, roles_required, current_user

@app.route('/api/v1/config', methods=['GET'])
@auth_required()
@roles_required('admin')
def list_config():
    """List all configurations (masks sensitive values)"""
    configs = db(db.config).select(orderby=db.config.category)
    return jsonify({'configs': [{
        'key': c.config_key,
        'value': '***SENSITIVE***' if c.is_sensitive else c.config_value,
        'type': c.config_type,
        'category': c.category,
        'description': c.description
    } for c in configs]})

@app.route('/api/v1/config/<config_key>', methods=['PUT'])
@auth_required()
@roles_required('admin')
def update_config(config_key):
    """Update configuration value"""
    config = db(db.config.config_key == config_key).select().first()
    if not config:
        return jsonify({'error': 'Not found'}), 404

    validated = validate_config(request.get_json().get('value'), config.config_type)
    if validated is None:
        return jsonify({'error': 'Invalid value'}), 400

    config.update_record(config_value=str(validated), updated_by=current_user.email)
    db.commit()
    return jsonify({'message': 'Updated'})
```

### Settings Page (React)

```jsx
import { useState, useEffect } from 'react';
import { apiClient } from '../../services/apiClient';

export function ConfigurationPage() {
  const [configs, setConfigs] = useState([]);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    (async () => {
      const res = await apiClient.get('/api/v1/config');
      setConfigs(res.data.configs);
    })();
  }, []);

  const handleUpdate = async (key, value) => {
    try {
      await apiClient.put(`/api/v1/config/${key}`, { value });
      setEditing(null);
    } catch (err) {
      alert('Failed to update');
    }
  };

  return (
    <div>
      <h1>System Configuration</h1>
      <table>
        <thead>
          <tr>
            <th>Setting</th>
            <th>Value</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {configs.map((c) => (
            <tr key={c.key}>
              <td><code>{c.key}</code></td>
              <td>
                {editing === c.key ? (
                  <input type="text" defaultValue={c.value}
                    onBlur={(e) => handleUpdate(c.key, e.target.value)} />
                ) : (
                  c.value
                )}
              </td>
              <td>
                <button onClick={() => setEditing(c.key)}>Edit</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Security Best Practices

1. **Sensitive values**: Mark passwords/API keys as `is_sensitive=True`
2. **Mask in responses**: Never return sensitive values in APIs
3. **Authorization**: Only global admins can modify config
4. **Validation**: Always validate before saving
5. **Audit trail**: Log who changed what and when
6. **Encryption**: Consider encrypting sensitive values in database

### Configuration Categories

- `integration` - External service integrations (WaddleAI, MarchProxy)
- `email` - SMTP and email settings
- `security` - Security settings (TLS, auth)
- `database` - Database connection settings
- `system` - General system settings
- `license` - License server configuration

---

## Key Principles

1. **Bootstrap from Environment**: Initial config from Docker env vars
2. **Database as Source of Truth**: Config stored and retrieved from database
3. **Admin-Only Management**: Global admins control configuration
4. **Runtime Updates**: Changes effective without restart
5. **Audit Trail**: Track all changes with user and timestamp
6. **Validation**: Validate all input before storing
7. **Security**: Mask and encrypt sensitive values

📚 **Related:** [Database Standards](DATABASE.md) | [Authentication Standards](AUTHENTICATION.md) | [Security Standards](SECURITY.md)
### Error Handling

- **Validation Fails (RELEASE_MODE=true)**: Exit with error
- **Validation Fails (RELEASE_MODE=false)**: Warn, continue
- **Network Error**: Cache previous result, retry on next startup
- **Feature Not Entitled**: Return 403 Forbidden with feature name

---

## KillKrill Integration

KillKrill provides centralized logging and metrics collection for all services.

### Environment Variables

```bash
# KillKrill Configuration
KILLKRILL_API_URL=http://killkrill-receiver:8081
KILLKRILL_GRPC_URL=killkrill-receiver:50051
KILLKRILL_CLIENT_ID=client_id
KILLKRILL_CLIENT_SECRET=client_secret
KILLKRILL_ENABLED=true
```

### Python Implementation

```python
from app.killkrill import killkrill_manager

# Initialize during app startup
killkrill_manager.setup()

# Log structured entries
killkrill_manager.log('info', 'User logged in',
    user_id='user_123',
    team_id='team_abc',
    ip_address='192.168.1.1')

# Track metrics
killkrill_manager.metric('api_request_duration', 125,
    type='histogram',
    labels={'endpoint': '/api/v1/teams', 'status': '200'})

# Health check
if not killkrill_manager.health_check():
    logger.warn("KillKrill unavailable, using local logs")
```

### Structured Logging

All logs use Elastic Common Schema (ECS):

```json
{
  "@timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "message": "User authentication",
  "service.name": "flask-backend",
  "user.id": "user_123",
  "organization.id": "team_abc",
  "event.action": "login",
  "event.outcome": "success",
  "source.ip": "192.168.1.1"
}
```

### Metrics Categories

- **API Metrics**:
  - `http.request.duration_ms` (histogram)
  - `http.requests.total` (counter)
  - `http.request.size_bytes` (histogram)

- **Business Metrics**:
  - `users.active` (gauge)
  - `teams.total` (gauge)
  - `features.used` (counter with feature label)

- **System Metrics**:
  - `database.connection.pool.used` (gauge)
  - `database.query.duration_ms` (histogram)
  - `cache.hits` / `cache.misses` (counter)

### Implementation Patterns

**Middleware Integration**:

```python
@app.before_request
def log_request():
    g.start_time = time.time()
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

@app.after_request
def log_response(response):
    duration = (time.time() - g.start_time) * 1000  # ms
    killkrill_manager.log('info', 'HTTP request',
        request_id=g.request_id,
        method=request.method,
        path=request.path,
        status=response.status_code,
        duration_ms=duration)
    return response
```

**Decorator for Tracking**:

```python
def track_action(action_name):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                killkrill_manager.log('info', action_name,
                    outcome='success')
                return result
            except Exception as e:
                killkrill_manager.log('error', action_name,
                    outcome='failure',
                    error=str(e))
                raise
        return wrapper
    return decorator

@track_action('team_creation')
def create_team(name, slug):
    # Implementation
    pass
```

### Error Handling

- **Connection Failure**: Use local logs as fallback, queue for retry
- **Invalid Credentials**: Log error, disable KillKrill, use local logs
- **Network Timeout**: Async batching prevents blocking requests
- **Buffer Full**: Drop oldest entries, prioritize error logs

### Batching

Logs/metrics batched and sent every 5 seconds:

```python
{
  "logs": [
    { "timestamp": "...", "level": "info", ... },
    { "timestamp": "...", "level": "error", ... }
  ],
  "metrics": [
    { "name": "http.requests.total", "value": 42, ... }
  ]
}
```

---

## Configuration Best Practices

1. **Environment Variables**: Use for sensitive/deployment-specific values
2. **Database Storage**: Use for user-configurable settings
3. **Code Defaults**: Use for non-sensitive, stable defaults
4. **Validation**: Always validate on load and before use
5. **Audit Trail**: Track configuration changes with timestamps and user info
6. **Hot Reload**: Implement for non-critical configuration
7. **Encryption**: Encrypt sensitive values at rest

📚 **Related Standards**: [Database](DATABASE.md) | [Authentication](AUTHENTICATION.md) | [Security](SECURITY.md)
