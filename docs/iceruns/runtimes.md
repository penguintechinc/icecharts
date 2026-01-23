# IceRuns Runtimes Guide

Complete reference for all supported runtimes.

## Python 3.13

### Handler Format
```python
# File: main.py
def handler(event):
    """Main entry point"""
    # event: dict with input data
    # returns: JSON-serializable dict or object
    return {'result': 'success', 'data': event}
```

**Configuration:**
- **Entrypoint:** `main.py` (filename)
- **Handler:** `main.handler` (module.function)

### Dependencies
```
# requirements.txt
requests>=2.31.0
boto3>=1.26.0
redis>=5.0.0
```

**Installation:**
- Automatically run `pip install -r requirements.txt` during cold start
- Maximum 512 MB for all dependencies

### Environment Variables
```python
import os

def handler(event):
    api_key = os.getenv('API_KEY')  # From function config
    region = os.getenv('REGION', 'us-east-1')  # With default
    return {'api_key_set': api_key is not None}
```

### Input/Output Format
```python
def handler(event):
    # Input is JSON dict
    name = event.get('name', 'World')
    age = event.get('age')  # None if not provided

    # Output must be JSON-serializable
    return {
        'greeting': f'Hello {name}',
        'age_info': f'Age: {age}' if age else 'Age unknown',
        'success': True,
        'nested': {
            'data': [1, 2, 3],
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
    }
```

### Example: API Wrapper
```python
import requests
import json

def handler(event):
    url = event.get('url')
    if not url:
        return {'error': 'url parameter required', 'success': False}

    try:
        response = requests.get(url, timeout=10)
        return {
            'status_code': response.status_code,
            'content': response.text[:1000],  # First 1000 chars
            'success': True
        }
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }
```

### Best Practices
- Keep functions stateless
- Use environment variables for configuration
- Handle errors gracefully
- Return JSON-serializable objects
- Avoid large dependencies (size limit: 512 MB)

---

## Node.js 20

### Handler Format
```javascript
// File: index.js
exports.handler = async (event) => {
  // event: object with input data
  // returns: JSON-serializable object or Promise
  return {
    result: 'success',
    data: event
  };
};
```

**Configuration:**
- **Entrypoint:** `index.js` (filename)
- **Handler:** `index.handler` (module.export)

### Dependencies
```json
{
  "name": "my-function",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "axios": "^1.6.0",
    "aws-sdk": "^2.1000.0",
    "express": "^4.18.0"
  }
}
```

**Installation:**
- Automatically run `npm install` during cold start
- Uses `package-lock.json` if present

### Async/Await Support
```javascript
exports.handler = async (event) => {
  const data = await someAsyncOperation();
  return { success: true, data };
};
```

### Environment Variables
```javascript
exports.handler = (event) => {
  const apiKey = process.env.API_KEY;
  const region = process.env.REGION || 'us-east-1';

  return {
    apiKeySet: !!apiKey,
    region: region
  };
};
```

### Example: Image Processing
```javascript
const AWS = require('aws-sdk');
const sharp = require('sharp');

const s3 = new AWS.S3();

exports.handler = async (event) => {
  const { bucket, key, width } = event;

  try {
    // Download from S3
    const obj = await s3.getObject({ Bucket: bucket, Key: key }).promise();

    // Resize image
    const resized = await sharp(obj.Body)
      .resize(width, width, { fit: 'cover' })
      .toBuffer();

    // Upload back
    await s3.putObject({
      Bucket: bucket,
      Key: `resized-${key}`,
      Body: resized
    }).promise();

    return { success: true, key: `resized-${key}` };
  } catch (error) {
    return { error: error.message, success: false };
  }
};
```

### Best Practices
- Always use `async/await` for asynchronous operations
- Handle errors with try/catch
- Return JSON-serializable objects
- Use `process.env` for configuration
- Install `package-lock.json` for deterministic builds

---

## Go 1.23

### Handler Format
```go
package main

import (
    "encoding/json"
    "fmt"
)

type Input struct {
    Name string `json:"name"`
}

type Output struct {
    Message string `json:"message"`
    Success bool   `json:"success"`
}

func Handler(input Input) (Output, error) {
    return Output{
        Message: fmt.Sprintf("Hello, %s!", input.Name),
        Success: true,
    }, nil
}
```

**Configuration:**
- **Entrypoint:** `main.go`
- **Handler:** `main.Handler`

### Dependencies
```go
// go.mod
module my-function

go 1.23

require (
    github.com/aws/aws-sdk-go-v2 v1.24.0
    github.com/redis/go-redis/v9 v9.0.0
)
```

**Build Process:**
- Automatically run `go mod download` and `go build`
- Binary compiled for Linux AMD64/ARM64

### Input/Output Format
```go
type Event struct {
    URL    string `json:"url"`
    Params map[string]string `json:"params"`
}

type Result struct {
    Data interface{} `json:"data"`
    Duration int64  `json:"duration_ms"`
}
```

### Example: Data Processing
```go
package main

import (
    "encoding/json"
    "sort"
)

type Item struct {
    ID    int    `json:"id"`
    Value float64 `json:"value"`
}

type Request struct {
    Items []Item `json:"items"`
}

type Response struct {
    Count float64   `json:"count"`
    Total float64   `json:"total"`
    Average float64 `json:"average"`
    Sorted []Item   `json:"sorted"`
}

func Handler(req Request) (Response, error) {
    if len(req.Items) == 0 {
        return Response{}, nil
    }

    total := 0.0
    for _, item := range req.Items {
        total += item.Value
    }

    sort.Slice(req.Items, func(i, j int) bool {
        return req.Items[i].Value > req.Items[j].Value
    })

    return Response{
        Count: float64(len(req.Items)),
        Total: total,
        Average: total / float64(len(req.Items)),
        Sorted: req.Items,
    }, nil
}
```

### Best Practices
- Use struct tags for JSON marshaling
- Handle errors explicitly
- Keep functions pure (no global state)
- Cross-compile for target platform

---

## Ruby 3.3

### Handler Format
```ruby
# File: handler.rb
def handler(event)
  # event: Hash with input data
  # returns: Hash or JSON-serializable object
  {
    result: 'success',
    data: event
  }
end
```

**Configuration:**
- **Entrypoint:** `handler.rb`
- **Handler:** `handler` (method name)

### Dependencies
```ruby
# Gemfile
source 'https://rubygems.org'

gem 'httparty', '~> 0.21.0'
gem 'aws-sdk-s3', '~> 1.120.0'
gem 'redis', '~> 5.0.0'
```

**Installation:**
- Automatically run `bundle install`
- Gemfile.lock used for reproducible builds

### Environment Variables
```ruby
def handler(event)
  api_key = ENV['API_KEY']
  region = ENV['REGION'] || 'us-east-1'

  { api_key_set: !api_key.nil?, region: region }
end
```

### Example: Web Scraping
```ruby
require 'httparty'
require 'json'

def handler(event)
  url = event['url']
  raise 'url parameter required' unless url

  begin
    response = HTTParty.get(url, timeout: 10)

    {
      status_code: response.code,
      content_length: response.body.length,
      headers: response.headers.slice('content-type', 'content-length'),
      success: true
    }
  rescue StandardError => e
    { error: e.message, success: false }
  end
end
```

### Best Practices
- Use Gemfile for dependency management
- Handle exceptions with begin/rescue
- Return JSON-compatible hashes
- Keep gems lightweight (dependency size matters)

---

## Bash 5.2

### Handler Format
```bash
#!/bin/bash
# File: handler.sh
# Input available as: $1 (JSON string) or via ICERUN_INPUT env var
# Output via: echo (JSON to stdout)

input_json="$1"
echo "{\"result\": \"success\", \"input\": $input_json}"
```

**Configuration:**
- **Entrypoint:** `handler.sh`
- **Handler:** `handler` (script name, no extension)

### Input/Output Format
```bash
#!/bin/bash
# Input passed as JSON string in $1
# Parse with jq for reliability

name=$(echo "$1" | jq -r '.name // "World"')
echo "{\"message\": \"Hello, $name!\"}"
```

### Environment Variables
```bash
#!/bin/bash
# Access via standard ENV variables

api_key="${API_KEY:-not-set}"
region="${REGION:-us-east-1}"

echo "{\"api_key_set\": $([ -z \"$API_KEY\" ] && echo 'false' || echo 'true'), \"region\": \"$region\"}"
```

### Example: File Processing
```bash
#!/bin/bash
# Process files and generate report

input_file="$1"
output_json=$(jq '{
  name: .filename,
  size: .size,
  processed_at: now | todate,
  success: true
}' <<< "$input_file")

echo "$output_json"
```

### Best Practices
- Use `jq` for JSON parsing (always available)
- Quote variables properly
- Handle empty input gracefully
- Use absolute paths for external tools
- Keep scripts concise

---

## PowerShell 7.4

### Handler Format
```powershell
# File: handler.ps1
param([hashtable]$event)

return @{
    result = "success"
    data = $event
}
```

**Configuration:**
- **Entrypoint:** `handler.ps1`
- **Handler:** `handler` (function/script name)

### Input/Output Format
```powershell
param([hashtable]$event)

$name = $event['name'] ?? 'World'

@{
    message = "Hello, $name!"
    timestamp = (Get-Date -Format 'u')
    success = $true
}
```

### Environment Variables
```powershell
param([hashtable]$event)

$apiKey = $env:API_KEY
$region = $env:REGION ?? 'us-east-1'

@{
    apiKeySet = $null -ne $apiKey
    region = $region
}
```

### Example: Azure Automation
```powershell
param([hashtable]$event)

# Note: Requires Azure SDK in dependencies
try {
    $resourceGroup = $event['resourceGroup']
    $vmName = $event['vmName']

    # PowerShell would connect to Azure here
    # This is example structure

    @{
        action = "restarted"
        vm = $vmName
        resourceGroup = $resourceGroup
        timestamp = (Get-Date -Format 'u')
        success = $true
    }
}
catch {
    @{
        error = $_.Exception.Message
        success = $false
    }
}
```

### Best Practices
- Use `??` for null coalescing
- Return hashtables (converted to JSON)
- Use try/catch for error handling
- Leverage PowerShell built-in cmdlets

---

## Rust 1.75

### Handler Format
```rust
// File: src/lib.rs
use serde_json::{json, Value};

#[no_mangle]
pub extern "C" fn handler(input: &str) -> String {
    let parsed: Value = serde_json::from_str(input).unwrap_or(json!({}));

    let response = json!({
        "result": "success",
        "data": parsed
    });

    response.to_string()
}
```

**Configuration:**
- **Entrypoint:** `src/lib.rs` (or `main.rs`)
- **Handler:** `handler` (exported function)

### Dependencies
```toml
# Cargo.toml
[package]
name = "my-function"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.11", features = ["json"] }

[lib]
crate-type = ["cdylib"]
```

**Build Process:**
- Automatically compile to binary
- Optimized release build

### Example: High-Performance Processing
```rust
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

#[derive(Deserialize)]
struct Input {
    numbers: Vec<i32>,
}

#[derive(Serialize)]
struct Output {
    count: usize,
    sum: i64,
    average: f64,
    min: i32,
    max: i32,
}

#[no_mangle]
pub extern "C" fn handler(input: &str) -> String {
    let parsed: Value = serde_json::from_str(input).unwrap_or(json!({}));

    let numbers: Vec<i32> = parsed["numbers"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .filter_map(|v| v.as_i64().map(|n| n as i32))
        .collect();

    if numbers.is_empty() {
        return json!({ "error": "empty input" }).to_string();
    }

    let sum: i64 = numbers.iter().map(|&n| n as i64).sum();
    let avg = sum as f64 / numbers.len() as f64;

    let result = Output {
        count: numbers.len(),
        sum,
        average: avg,
        min: *numbers.iter().min().unwrap(),
        max: *numbers.iter().max().unwrap(),
    };

    serde_json::to_string(&result).unwrap()
}
```

### Best Practices
- Use `#[derive(Deserialize, Serialize)]` for data structures
- Handle JSON errors gracefully
- Use `#[no_mangle]` for exported functions
- Test locally before deployment
- Profile for performance-critical functions

---

## Comparison Table

| Feature | Python | Node.js | Go | Ruby | Bash | PowerShell | Rust |
|---------|--------|---------|----|----|------|-----------|------|
| Cold Start | 1-2s | 800ms | 600ms | 1.5s | 200ms | 2-3s | 500ms |
| Warm Start | 100ms | 80ms | 50ms | 150ms | 50ms | 200ms | 50ms |
| Memory Overhead | ~50MB | ~30MB | ~5MB | ~40MB | ~2MB | ~100MB | ~3MB |
| Package Size Limit | 512MB | 512MB | 512MB | 512MB | 512MB | 512MB | 512MB |
| Concurrency Support | Native | Native | Native | Limited | Limited | Limited | Native |
| Performance | Good | Excellent | Excellent | Good | Good | Fair | Excellent |
| Development Speed | Very Fast | Fast | Moderate | Fast | Moderate | Moderate | Slow |

---

## Common Patterns

### Pattern 1: API Request with Error Handling
All runtimes support:
```
1. Parse input JSON
2. Make HTTP request
3. Handle connection errors
4. Handle timeout
5. Return result JSON
```

See examples in each runtime section above.

### Pattern 2: File Processing
All runtimes can:
```
1. Download from S3
2. Process locally (/tmp)
3. Upload result
4. Return status
```

### Pattern 3: Database Queries
All runtimes can:
```
1. Connect to PostgreSQL/MySQL
2. Execute query
3. Return result set
4. Handle connection errors
```

### Pattern 4: Parallel Processing
Best for:
- **Go/Rust:** Native goroutines/async
- **Node.js:** Promises/async-await
- **Python:** ThreadPoolExecutor/asyncio
- **Ruby:** Threads (limited)
- **Bash:** GNU parallel
- **PowerShell:** ForEach-Object -Parallel

---

## Performance Tips

### Python
- Use dataclasses instead of classes
- Pre-compile regexes at module level
- Use numpy for array operations

### Node.js
- Use native modules where available
- Avoid callbacks, use async/await
- Bundle dependencies with esbuild

### Go
- Ideal for CPU-bound operations
- Concurrency via goroutines
- Static compilation (no runtime)

### Ruby
- Use C extensions for performance
- Avoid metaprogramming in hot paths
- Cache computations

### Bash
- Use compiled tools (jq, curl)
- Avoid loops for large datasets
- Process in parallel with GNU parallel

### PowerShell
- Avoid Select-Object in loops
- Use native cmdlets
- Pre-load required modules

### Rust
- Profile with flamegraph
- Use release mode
- Leverage SIMD instructions

---

See also:
- [Quickstart](./quickstart.md) - Getting started
- [API Reference](./api-reference.md) - Function management API
- [Examples](./examples/) - Complete working examples
