# Development Standards

This document consolidates all development standards, patterns, and requirements for projects using this template.

## Table of Contents

1. [Language Selection Criteria](#language-selection-criteria)
2. [Flask-Security-Too Integration](#flask-security-too-integration)
3. [ReactJS Frontend Standards](#reactjs-frontend-standards)
4. [Database Standards](#database-standards)
5. [Protocol Support](#protocol-support)
6. [Performance Best Practices](#performance-best-practices)
7. [High-Performance Networking](#high-performance-networking)
8. [Microservices Architecture](#microservices-architecture)
9. [Docker Standards](#docker-standards)
10. [Testing Requirements](#testing-requirements)
11. [Security Standards](#security-standards)
12. [Documentation Standards](#documentation-standards)
13. [Web UI Design Standards](#web-ui-design-standards)
14. [WaddleAI Integration](#waddleai-integration)

---

## Language Selection Criteria

**Evaluate on a case-by-case basis which language to use for each project or service:**

### Python 3.13 (Default Choice)
**Use Python for most applications:**
- Web applications and REST APIs
- Business logic and data processing
- Integration services and connectors
- CRUD applications
- Admin panels and internal tools
- Low to moderate traffic applications (<10K req/sec)

**Advantages:**
- Rapid development and iteration
- Rich ecosystem of libraries
- Excellent for prototyping and MVPs
- Strong support for data processing
- Easy maintenance and debugging

### Go 1.23.x (Performance-Critical Only)
**Use Go ONLY for high-traffic, performance-critical applications:**
- Applications handling >10K requests/second
- Network-intensive services requiring low latency
- Services with latency requirements <10ms
- CPU-bound operations requiring maximum throughput
- Systems requiring minimal memory footprint
- Real-time processing pipelines

**Traffic Threshold Decision Matrix:**
| Requests/Second | Language Choice | Rationale |
|-----------------|-----------------|-----------|
| < 1K req/sec    | Python 3.13     | Development speed priority |
| 1K - 10K req/sec| Python 3.13     | Python can handle with optimization |
| 10K - 50K req/sec| Evaluate both  | Consider complexity vs performance needs |
| > 50K req/sec   | Go 1.23.x       | Performance becomes critical |

**Important Considerations:**
- Start with Python for faster iteration
- Profile and measure actual performance before switching
- Consider operational complexity of multi-language stack
- Go adds development overhead - only use when necessary

---

## Flask-Security-Too Integration

**MANDATORY for ALL Flask applications - provides comprehensive security framework**

### Core Features
- User authentication and session management
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Email confirmation and password reset
- Two-factor authentication (2FA)
- Token-based authentication for APIs
- Login tracking and session management

### Integration with PyDAL

Flask-Security-Too integrates with PyDAL for database operations:

```python
from flask import Flask
from flask_security import Security, auth_required, hash_password
from flask_security.datastore import DataStore, UserDataMixin, RoleDataMixin
from pydal import DAL, Field
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', 'salt')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'

# PyDAL database setup
db = DAL(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",
    pool_size=10,
    migrate=True
)

# Define user and role tables
db.define_table('auth_user',
    Field('email', 'string', requires=IS_EMAIL(), unique=True),
    Field('username', 'string', unique=True),
    Field('password', 'string'),
    Field('active', 'boolean', default=True),
    Field('fs_uniquifier', 'string', unique=True),
    Field('confirmed_at', 'datetime'),
    migrate=True
)

db.define_table('auth_role',
    Field('name', 'string', unique=True),
    Field('description', 'text'),
    migrate=True
)

db.define_table('auth_user_roles',
    Field('user_id', 'reference auth_user'),
    Field('role_id', 'reference auth_role'),
    migrate=True
)

# Custom PyDAL datastore for Flask-Security-Too
class PyDALUserDatastore(DataStore):
    def __init__(self, db, user_model, role_model):
        self.db = db
        self.user_model = user_model
        self.role_model = role_model

    def put(self, model):
        self.db.commit()
        return model

    def delete(self, model):
        self.db(self.user_model.id == model.id).delete()
        self.db.commit()

    def find_user(self, **kwargs):
        query = self.db(self.user_model)
        for key, value in kwargs.items():
            if hasattr(self.user_model, key):
                query = query(self.user_model[key] == value)
        row = query.select().first()
        return row

# Initialize Flask-Security-Too
user_datastore = PyDALUserDatastore(db, db.auth_user, db.auth_role)
security = Security(app, user_datastore)

# Protected route example
@app.route('/api/protected')
@auth_required()
def protected_endpoint():
    return {'message': 'Access granted', 'user': current_user.email}

# Admin-only route example
@app.route('/api/admin')
@auth_required()
@roles_required('admin')
def admin_endpoint():
    return {'message': 'Admin access granted'}
```

### SSO Integration (Enterprise Feature)

**ALWAYS license-gate SSO as an enterprise-only feature:**

```python
from shared.licensing import requires_feature
from flask_security import auth_required

@app.route('/auth/saml/login')
@requires_feature('sso_saml')
def saml_login():
    """SAML SSO login - enterprise feature"""
    # SAML authentication logic
    pass

@app.route('/auth/oauth/login')
@requires_feature('sso_oauth')
def oauth_login():
    """OAuth SSO login - enterprise feature"""
    # OAuth authentication logic
    pass
```

**SSO Configuration:**
```python
# Enterprise SSO features (license-gated)
if license_client.has_feature('sso_saml'):
    app.config['SECURITY_SAML_ENABLED'] = True
    app.config['SECURITY_SAML_IDP_METADATA_URL'] = os.getenv('SAML_IDP_METADATA_URL')

if license_client.has_feature('sso_oauth'):
    app.config['SECURITY_OAUTH_ENABLED'] = True
    app.config['SECURITY_OAUTH_PROVIDERS'] = {
        'google': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        },
        'azure': {
            'client_id': os.getenv('AZURE_CLIENT_ID'),
            'client_secret': os.getenv('AZURE_CLIENT_SECRET'),
        }
    }
```

### Environment Variables

Required environment variables for Flask-Security-Too:

```bash
# Flask-Security-Too core
SECRET_KEY=your-secret-key-here
SECURITY_PASSWORD_SALT=your-password-salt
SECURITY_REGISTERABLE=true
SECURITY_SEND_REGISTER_EMAIL=false

# SSO (Enterprise only - license-gated)
SAML_IDP_METADATA_URL=https://idp.example.com/metadata
GOOGLE_CLIENT_ID=google-oauth-client-id
GOOGLE_CLIENT_SECRET=google-oauth-client-secret
AZURE_CLIENT_ID=azure-oauth-client-id
AZURE_CLIENT_SECRET=azure-oauth-client-secret
```

---

## ReactJS Frontend Standards

**ALL frontend applications MUST use ReactJS**

### Project Structure

```
services/webui/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/      # Reusable components
│   ├── pages/           # Page components
│   ├── services/        # API client services
│   ├── hooks/           # Custom React hooks
│   ├── context/         # React context providers
│   ├── utils/           # Utility functions
│   ├── App.jsx
│   └── index.jsx
├── package.json
├── Dockerfile
└── .env
```

### Required Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0"
  }
}
```

### API Client Integration

**Create centralized API client for Flask backend:**

```javascript
// src/services/apiClient.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for session cookies
});

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login on unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Authentication Context

```javascript
// src/context/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated on mount
    const checkAuth = async () => {
      try {
        const response = await apiClient.get('/auth/user');
        setUser(response.data);
      } catch (error) {
        console.error('Not authenticated:', error);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const response = await apiClient.post('/auth/login', { email, password });
    setUser(response.data.user);
    localStorage.setItem('authToken', response.data.token);
  };

  const logout = async () => {
    await apiClient.post('/auth/logout');
    setUser(null);
    localStorage.removeItem('authToken');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
```

### Protected Routes

```javascript
// src/components/ProtectedRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};
```

### React Query for Data Fetching

```javascript
// src/hooks/useUsers.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';

export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await apiClient.get('/api/users');
      return response.data;
    },
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userData) => {
      const response = await apiClient.post('/api/users', userData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
    },
  });
};
```

### Component Standards

**Use functional components with hooks:**

```javascript
import React, { useState, useEffect } from 'react';
import { useUsers, useCreateUser } from '../hooks/useUsers';

export const UserList = () => {
  const { data: users, isLoading, error } = useUsers();
  const createUser = useCreateUser();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Users</h2>
      <ul>
        {users.map(user => (
          <li key={user.id}>{user.name} - {user.email}</li>
        ))}
      </ul>
    </div>
  );
};
```

### Docker Configuration for React

```dockerfile
# services/webui/Dockerfile
FROM node:18-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## Database Standards

### PyDAL Configuration - MANDATORY for ALL Python Applications

ALL Python applications (web or non-web) MUST implement PyDAL database access.

**Note on PyDAL Augmentation:**
- PyDAL is the PRIMARY database abstraction layer
- Other libraries can augment PyDAL when absolutely necessary
- Any additional libraries must be justified and documented

### Go Database Requirements

When using Go for high-performance applications, MUST use a DAL supporting PostgreSQL and MySQL:

**Recommended Options:**
1. **GORM** (Preferred)
   - Full-featured ORM
   - Supports PostgreSQL, MySQL, SQLite, SQL Server
   - Active maintenance and large community
   - Auto migrations and associations

2. **sqlx** (Alternative)
   - Lightweight extension of database/sql
   - Supports PostgreSQL, MySQL, SQLite
   - More control, less abstraction
   - Good for performance-critical scenarios

**Example GORM Implementation:**
```go
package main

import (
    "os"
    "gorm.io/driver/postgres"
    "gorm.io/driver/mysql"
    "gorm.io/gorm"
)

func initDB() (*gorm.DB, error) {
    dbType := os.Getenv("DB_TYPE") // "postgres" or "mysql"
    dsn := os.Getenv("DATABASE_URL")

    var dialector gorm.Dialector
    switch dbType {
    case "mysql":
        dialector = mysql.Open(dsn)
    default: // postgres
        dialector = postgres.Open(dsn)
    }

    db, err := gorm.Open(dialector, &gorm.Config{})
    return db, err
}
```

#### Environment Variables

Applications MUST accept these Docker environment variables:
- `DB_TYPE`: Database type (postgresql, mysql, sqlite, mssql, oracle, etc.)
- `DB_HOST`: Database host/IP address
- `DB_PORT`: Database port (default depends on DB_TYPE)
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASS`: Database password
- `DB_POOL_SIZE`: Connection pool size (default: 10)
- `DB_MAX_RETRIES`: Maximum connection retry attempts (default: 5)
- `DB_RETRY_DELAY`: Delay between retry attempts in seconds (default: 5)

#### Database Connection Requirements

1. **Wait for Database Initialization**: Application MUST wait for database to be ready
   - Implement retry logic with exponential backoff
   - Maximum retry attempts configurable via `DB_MAX_RETRIES`
   - Log each connection attempt for debugging
   - Fail gracefully with clear error messages

2. **Connection Pooling**: MUST use PyDAL's built-in connection pooling
   - Configure pool size via `DB_POOL_SIZE` environment variable
   - Implement proper connection lifecycle management
   - Handle connection timeouts and stale connections
   - Monitor pool utilization via metrics

3. **Database URI Construction**: Build connection string from environment variables
   ```python
   db_uri = f"{DB_TYPE}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
   ```

#### Implementation Pattern

```python
import os
import time
from pydal import DAL, Field

def wait_for_database(max_retries=5, retry_delay=5):
    """Wait for database to be available with retry logic"""
    retries = 0
    while retries < max_retries:
        try:
            db = get_db_connection(test=True)
            db.close()
            print(f"Database connection successful")
            return True
        except Exception as e:
            retries += 1
            print(f"Database connection attempt {retries}/{max_retries} failed: {e}")
            if retries < max_retries:
                time.sleep(retry_delay)
    return False

def get_db_connection():
    """Initialize PyDAL database connection with pooling"""
    db_type = os.getenv('DB_TYPE', 'postgresql')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'app_db')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', 'app_pass')
    pool_size = int(os.getenv('DB_POOL_SIZE', '10'))

    db_uri = f"{db_type}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    db = DAL(
        db_uri,
        pool_size=pool_size,
        migrate_enabled=True,
        check_reserved=['all'],
        lazy_tables=True
    )

    return db

# Application startup
if __name__ == '__main__':
    max_retries = int(os.getenv('DB_MAX_RETRIES', '5'))
    retry_delay = int(os.getenv('DB_RETRY_DELAY', '5'))

    if not wait_for_database(max_retries, retry_delay):
        print("Failed to connect to database after maximum retries")
        sys.exit(1)

    db = get_db_connection()
    # Continue with application initialization...
```

#### Thread Safety Requirements

**PyDAL MUST be used in a thread-safe manner:**

1. **Thread-local connections**: Each thread MUST have its own DAL instance
   - NEVER share a single DAL instance across multiple threads
   - Use thread-local storage (threading.local()) for per-thread DAL instances
   - Connection pooling handles multi-threaded access automatically

2. **Implementation Pattern for Threading:**
   ```python
   import threading
   from pydal import DAL

   # Thread-local storage for DAL instances
   thread_local = threading.local()

   def get_thread_db():
       """Get thread-local database connection"""
       if not hasattr(thread_local, 'db'):
           thread_local.db = DAL(
               db_uri,
               pool_size=10,
               migrate_enabled=True,
               check_reserved=['all'],
               lazy_tables=True
           )
       return thread_local.db

   # Usage in threaded context
   def worker_function():
       db = get_thread_db()  # Each thread gets its own connection
       # Perform database operations...
   ```

3. **Flask/WSGI Applications**: Flask already handles thread-local contexts
   ```python
   from flask import Flask, g

   app = Flask(__name__)

   def get_db():
       """Get database connection for current request context"""
       if 'db' not in g:
           g.db = DAL(db_uri, pool_size=10)
       return g.db

   @app.teardown_appcontext
   def close_db(error):
       """Close database connection after request"""
       db = g.pop('db', None)
       if db is not None:
           db.close()
   ```

4. **Async/Threading Considerations**:
   - When using threading.Thread, ensure each thread creates its own DAL instance
   - When using asyncio, use async-compatible database drivers if available
   - Connection pooling is thread-safe and manages concurrent access automatically
   - NEVER pass DAL instances between threads

5. **Multi-process Safety**:
   - Each process MUST create its own DAL instance
   - Connection pool is per-process, not shared across processes

---

## Protocol Support

**ALL applications MUST support multiple communication protocols:**

### Required Protocol Support

1. **REST API**: RESTful HTTP endpoints (GET, POST, PUT, DELETE, PATCH)
   - JSON request/response format
   - Proper HTTP status codes
   - Resource-based URL design

2. **gRPC**: High-performance RPC protocol
   - Protocol Buffers for message serialization
   - Bi-directional streaming support
   - Service definitions in .proto files
   - Health checking via gRPC health protocol

3. **HTTP/1.1**: Standard HTTP protocol support
   - Keep-alive connections
   - Chunked transfer encoding
   - Compression (gzip, deflate)

4. **HTTP/2**: Modern HTTP protocol
   - Multiplexing multiple requests over single connection
   - Header compression (HPACK)
   - Stream prioritization

5. **HTTP/3 (QUIC)**: Next-generation HTTP protocol
   - UDP-based transport with TLS 1.3
   - Zero round-trip time (0-RTT) connection establishment
   - Built-in encryption

### Protocol Configuration via Environment Variables

Applications must accept these environment variables:
- `HTTP1_ENABLED`: Enable HTTP/1.1 (default: true)
- `HTTP2_ENABLED`: Enable HTTP/2 (default: true)
- `HTTP3_ENABLED`: Enable HTTP/3/QUIC (default: false)
- `GRPC_ENABLED`: Enable gRPC (default: true)
- `HTTP_PORT`: HTTP/REST API port (default: 8080)
- `GRPC_PORT`: gRPC port (default: 50051)
- `METRICS_PORT`: Prometheus metrics port (default: 9090)

### Implementation Example

```python
from flask import Flask, jsonify, request
import grpc
from concurrent import futures

app = Flask(__name__)

@app.route('/api/v1/resource', methods=['GET', 'POST'])
def rest_resource():
    if request.method == 'GET':
        return jsonify({'status': 'success', 'data': []})
    elif request.method == 'POST':
        return jsonify({'status': 'created'}), 201

# gRPC Server (run alongside Flask)
def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
```

### Required Dependencies

**Python:**
```
flask>=3.0.0
grpcio>=1.60.0
grpcio-tools>=1.60.0
hypercorn>=0.16.0  # For HTTP/2 and HTTP/3 support
aioquic>=0.9.0     # For QUIC/HTTP3
protobuf>=4.25.0
```

**Go:**
- `google.golang.org/grpc` for gRPC
- `golang.org/x/net/http2` for HTTP/2
- `github.com/quic-go/quic-go` for HTTP/3/QUIC

---

## Performance Best Practices

**ALWAYS prioritize performance and stability through modern concurrency patterns**

### Python Performance Requirements

#### Concurrency Patterns - Choose Based on Use Case

1. **asyncio** - For I/O-bound operations:
   - Database queries and connections
   - HTTP/REST API calls
   - File I/O operations
   - Network communication
   - Best for operations that wait on external resources

2. **threading.Thread** - For I/O-bound operations with blocking libraries:
   - Legacy libraries without async support
   - Blocking I/O operations
   - Moderate parallelism (10-100 threads)
   - Use ThreadPoolExecutor for managed thread pools

3. **multiprocessing** - For CPU-bound operations:
   - Data processing and transformations
   - Cryptographic operations
   - Image/video processing
   - Heavy computational tasks
   - Bypasses GIL for true parallelism

**Decision Matrix:**
```python
# I/O-bound + async library available → asyncio
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# I/O-bound + blocking library → threading
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(blocking_function, data)

# CPU-bound → multiprocessing
from multiprocessing import Pool
with Pool(processes=8) as pool:
    results = pool.map(cpu_intensive_function, data)
```

#### Dataclasses with Slots - MANDATORY

**ALL data structures MUST use dataclasses with slots for memory efficiency:**

```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass(slots=True, frozen=True)
class User:
    """User model with slots for 30-50% memory reduction"""
    id: int
    name: str
    email: str
    created_at: str
    metadata: dict = field(default_factory=dict)
```

**Benefits of Slots:**
- 30-50% less memory per instance
- Faster attribute access
- Better type safety with type hints
- Immutability with `frozen=True`

#### Type Hints - MANDATORY

**Comprehensive type hints are REQUIRED for all Python code:**

```python
from typing import Optional, List, Dict
from collections.abc import AsyncIterator

async def process_users(
    user_ids: List[int],
    batch_size: int = 100,
    callback: Optional[Callable[[User], None]] = None
) -> Dict[int, User]:
    """Process users with full type hints"""
    results: Dict[int, User] = {}
    for user_id in user_ids:
        user = await fetch_user(user_id)
        results[user_id] = user
        if callback:
            callback(user)
    return results
```

### Go Performance Requirements
- **Goroutines**: Leverage goroutines and channels for concurrent operations
- **Sync primitives**: Use sync.Pool, sync.Map for concurrent data structures
- **Context**: Proper context propagation for cancellation and timeouts

---

## High-Performance Networking

**Evaluate on a case-by-case basis for network-intensive applications**

### When to Consider XDP/AF_XDP

Only evaluate XDP (eXpress Data Path) and AF_XDP for applications with extreme network requirements:

**Traffic Thresholds:**
- Standard applications: Regular socket programming (most cases)
- High traffic (>100K packets/sec): Consider XDP/AF_XDP
- Extreme traffic (>1M packets/sec): XDP/AF_XDP strongly recommended

### XDP (eXpress Data Path)

**Kernel-level packet processing:**
- Processes packets at the earliest point in networking stack
- Bypass most of kernel networking code
- Can drop, redirect, or pass packets
- Ideal for DDoS mitigation, load balancing, packet filtering

**Use Cases:**
- Network firewalls and packet filters
- Load balancers
- DDoS protection
- High-frequency trading systems
- Real-time packet inspection

**Language Considerations:**
- Typically implemented in C with BPF bytecode
- Can be triggered from Go or Python applications
- Requires kernel support (Linux 4.8+)

### AF_XDP (Address Family XDP)

**Zero-copy socket for user-space packet processing:**
- Bypass kernel networking stack entirely
- Direct packet access from NIC to user-space
- Lowest latency possible for packet processing
- More flexible than kernel XDP

**Use Cases:**
- Custom network protocols
- Ultra-low latency applications
- Network monitoring and analytics
- Packet capture at high speeds

**Implementation Notes:**
```python
# Python with pyxdp (if available)
# Generally prefer Go for AF_XDP implementations
```

```go
// Go with AF_XDP libraries
import (
    "github.com/asavie/xdp"
)

// AF_XDP socket setup for high-performance packet processing
func setupAFXDP(ifname string, queueID int) (*xdp.Socket, error) {
    program := &xdp.SocketOptions{
        NumFrames:      4096,
        FrameSize:      2048,
        FillRingSize:   2048,
        CompletionRingSize: 2048,
        RxRingSize:     2048,
        TxRingSize:     2048,
    }

    return xdp.NewSocket(ifname, queueID, program)
}
```

### Decision Matrix: Networking Implementation

| Packets/Sec | Technology | Language | Justification |
|-------------|------------|----------|---------------|
| < 10K       | Standard sockets | Python 3.13 | Regular networking sufficient |
| 10K - 100K  | Optimized sockets | Python/Go | Standard with optimization |
| 100K - 500K | Consider XDP | Go + XDP | High performance needed |
| > 500K      | XDP/AF_XDP required | Go + AF_XDP | Extreme performance critical |

**Important:**
- Start with standard networking
- Profile actual performance before optimization
- XDP/AF_XDP adds significant complexity
- Requires specialized knowledge and maintenance

---

## Microservices Architecture

**ALWAYS use microservices architecture for application development**

### Three-Container Architecture

This template provides three base containers representing the core footprints:

| Container | Technology | Purpose | When to Use |
|-----------|------------|---------|-------------|
| **flask-backend** | Flask + PyDAL | Standard APIs, auth, CRUD | <10K req/sec, business logic |
| **go-backend** | Go + XDP/AF_XDP | High-performance networking | >10K req/sec, <10ms latency |
| **webui** | Node.js + React | Frontend shell | All frontend applications |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NGINX (optional)                               │
└─────────────────────────────────────────────────────────────────────────────┘
          │                        │                          │
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌────────────┴────────────┐
│  WebUI Container  │   │  Flask Backend    │   │    Go Backend           │
│  (Node.js/React)  │   │  (Flask/PyDAL)    │   │    (XDP/AF_XDP)         │
│                   │   │                   │   │                         │
│ - React SPA       │   │ - /api/v1/auth/*  │   │ - High-perf networking  │
│ - Proxies to APIs │   │ - /api/v1/users/* │   │ - XDP packet processing │
│ - Static assets   │   │ - /api/v1/hello   │   │ - AF_XDP zero-copy      │
│ - Port 3000       │   │ - Port 5000       │   │ - NUMA-aware memory     │
└───────────────────┘   └───────────────────┘   │ - Port 8080             │
                                 │              └─────────────────────────┘
                        ┌────────┴────────┐
                        │   PostgreSQL    │
                        └─────────────────┘
```

### Container Details

1. **WebUI Container** (Node.js + React)
   - Express server proxies API calls to backends
   - React SPA with role-based navigation
   - Elder-style collapsible sidebar
   - WaddlePerf-style tab navigation
   - Gold (amber-400) text theme

2. **Flask Backend** (Flask + PyDAL)
   - JWT authentication with bcrypt
   - User management CRUD (Admin only)
   - Role-based access: Admin, Maintainer, Viewer
   - PyDAL for multi-database support
   - Health check endpoints

3. **Go Backend** (Go + XDP/AF_XDP)
   - XDP for kernel-level packet processing
   - AF_XDP for zero-copy user-space I/O
   - NUMA-aware memory allocation
   - Memory slot pools for packet buffers
   - Prometheus metrics

4. **Connector Container** (placeholder)
   - External system integration
   - Background job processing

### Default Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: user CRUD, settings, all features |
| **Maintainer** | Read/write access to resources, no user management |
| **Viewer** | Read-only access to resources |

### Design Principles

- **Single Responsibility**: Each container has one clear purpose
- **Independent Deployment**: Services can be updated independently
- **API-First Design**: All inter-service communication via well-defined APIs
- **Data Isolation**: Each service owns its data
- **Fault Isolation**: Failure in one service doesn't cascade
- **Scalability**: Scale individual services based on demand

### Service Communication Patterns

- **Synchronous**: REST API, gRPC for request/response
- **Asynchronous**: Message queues (Kafka, RabbitMQ) for events
- **Service Discovery**: Docker networking or service mesh
- **Circuit Breakers**: Fallback mechanisms for failures
- **API Gateway**: Optional reverse proxy for routing

### Container Organization

```
project-name/
├── services/
│   ├── flask-backend/      # Flask + PyDAL backend (auth, users, APIs)
│   ├── go-backend/         # Go high-performance backend (XDP, NUMA)
│   ├── webui/              # Node.js + React frontend shell
│   └── connector/          # Integration services (placeholder)
```

---

## Docker Standards

### Build Standards

**All builds MUST be executed within Docker containers:**

```bash
# Go builds (using debian-slim)
docker run --rm -v $(pwd):/app -w /app golang:1.23-slim go build -o bin/app

# Python builds (using debian-slim)
docker run --rm -v $(pwd):/app -w /app python:3.13-slim pip install -r requirements.txt
```

**Use multi-stage builds with debian-slim:**
```dockerfile
FROM golang:1.23-slim AS builder
FROM debian:stable-slim AS runtime

FROM python:3.13-slim AS builder
FROM debian:stable-slim AS runtime
```

### Docker Compose Standards

**ALWAYS create docker-compose.dev.yml for local development**

**Prefer Docker networks over host ports:**
- Minimize host port exposure
- Only expose ports for developer access
- Use named Docker networks for service-to-service communication

```yaml
# docker-compose.dev.yml
version: '3.8'

networks:
  app-network:
    driver: bridge
  db-network:
    driver: bridge

services:
  app:
    build: ./apps/app
    networks:
      - app-network
      - db-network
    ports:
      - "8080:8080"  # Only expose for developer access
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/appdb

  postgres:
    image: postgres:16-alpine
    networks:
      - db-network
    # NO ports exposed to host - only accessible via Docker network
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=appdb
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

### Multi-Arch Build Strategy

GitHub Actions should use multi-arch builds:
```yaml
- uses: docker/build-push-action@v4
  with:
    platforms: linux/amd64,linux/arm64
    context: ./apps/app
    file: ./apps/app/Dockerfile
```

---

## Testing Requirements

### Unit Testing

**All applications MUST have comprehensive unit tests:**

- **Network isolation**: Unit tests must NOT require external network connections
- **No external dependencies**: Cannot reach databases, APIs, or external services
- **Use mocks/stubs**: Mock all external dependencies and I/O operations
- **KISS principle**: Keep unit tests simple, focused, and fast
- **Test isolation**: Each test should be independent and repeatable
- **Fast execution**: Unit tests should complete in milliseconds

### Integration Testing

- Test component interactions
- Use test databases and services
- Verify API contracts
- Test authentication and authorization

### End-to-End Testing

- Test critical user workflows
- Use staging environment
- Verify full system integration

### Performance Testing

- Benchmark critical operations
- Load testing for scalability
- Regression testing for performance

---

## Security Standards

### Input Validation

- ALL inputs MUST have appropriate validators
- Use framework-native validation (PyDAL validators, Go libraries)
- Implement XSS and SQL injection prevention
- Server-side validation for all client input
- CSRF protection using framework native features

### Authentication & Authorization

- Multi-factor authentication support
- Role-based access control (RBAC)
- API key management with rotation
- JWT token validation with proper expiration
- Session management with secure cookies

### TLS/Encryption

- **TLS enforcement**: TLS 1.2 minimum, prefer TLS 1.3
- **Connection security**: Use HTTPS where possible
- **Modern protocols**: HTTP3/QUIC for high-performance
- **Standard security**: JWT, MFA, mTLS where applicable
- **Enterprise SSO**: SAML/OAuth2 as enterprise features

### Dependency Security

- **ALWAYS check Dependabot alerts** before commits
- **Monitor vulnerabilities** via Socket.dev
- **Mandatory security scanning** before dependency changes
- **Fix all security alerts immediately**
- **Version pinning**: Exact versions for security-critical dependencies

### Vulnerability Response Process

1. Identify affected packages and severity
2. Update to patched versions immediately
3. Test updated dependencies thoroughly
4. Document security fixes in commit messages
5. Verify no new vulnerabilities introduced

---

## Documentation Standards

### README.md Standards

**ALWAYS include build status badges:**
- CI/CD pipeline status (GitHub Actions)
- Test coverage status (Codecov)
- Go Report Card (for Go projects)
- Version badge
- License badge (Limited AGPL3)

**ALWAYS include catchy ASCII art** below badges

**Company homepage**: Point to **www.penguintech.io**

### CLAUDE.md File Management

- **Maximum**: 35,000 characters
- **High-level approach**: Reference detailed docs
- **Documentation strategy**: Create detailed docs in `docs/` folder
- **Keep focused**: Critical context and workflow instructions only

### API Documentation

- Comprehensive endpoint documentation
- Request/response examples
- Error codes and handling
- Authentication requirements
- Rate limiting information

### Architecture Documentation

- System architecture diagrams
- Component interaction patterns
- Data flow documentation
- Decision records (ADRs)

---

## Logging & Monitoring

### Logging Standards

- **Console logging**: Always implement console output
- **Multi-destination logging**:
  - UDP syslog (legacy)
  - HTTP3/QUIC to Kafka
  - Cloud-native services (AWS/GCP)
- **Logging levels**:
  - `-v`: Warnings and criticals only
  - `-vv`: Info level (default)
  - `-vvv`: Debug logging

### Monitoring Requirements

- **Health endpoints**: ALL applications implement `/healthz`
- **Metrics endpoints**: Prometheus metrics endpoint required
- **Structured logging**: Use correlation IDs
- **Distributed tracing**: Support for complex flows
- **Alerting**: Critical failure notifications

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.route('/metrics')
def metrics():
    return generate_latest(), {'Content-Type': 'text/plain'}
```

---

## Web Framework Standards

- **Flask primary**: Use Flask for ALL Python web applications
- **PyDAL mandatory**: ALL Python applications use PyDAL
- **Health endpoints**: `/healthz` required for all applications
- **Metrics endpoints**: Prometheus metrics required

---

## Web UI Design Standards

**ALL ReactJS frontend applications MUST follow these design patterns:**

### Design Philosophy

- **Dark Theme Default**: Use dark backgrounds with light text for reduced eye strain
- **Consistent Spacing**: Use standardized spacing scale (Tailwind's spacing utilities)
- **Smooth Transitions**: Apply `transition-colors` or `transition-all 0.2s` for state changes
- **Subtle Gradients**: Use gradient accents sparingly for modern aesthetic
- **Responsive Design**: Mobile-first approach with breakpoint-based layouts

### Color Palette (Dark Theme)

**CSS Variables (Required):**
```css
:root {
  /* Background colors */
  --bg-primary: #0f172a;      /* slate-900 - main background */
  --bg-secondary: #1e293b;    /* slate-800 - sidebar/cards */
  --bg-tertiary: #334155;     /* slate-700 - hover states */

  /* Text colors - Gold default */
  --text-primary: #fbbf24;    /* amber-400 - headings, primary text */
  --text-secondary: #f59e0b;  /* amber-500 - body text */
  --text-muted: #d97706;      /* amber-600 - secondary/muted text */
  --text-light: #fef3c7;      /* amber-100 - high contrast text */

  /* Accent colors (sky-blue for interactive elements) */
  --primary-400: #38bdf8;
  --primary-500: #0ea5e9;
  --primary-600: #0284c7;
  --primary-700: #0369a1;

  /* Border colors */
  --border-color: #334155;    /* slate-700 */

  /* Admin/Warning accent */
  --warning-color: #eab308;   /* yellow-500 */
}
```

**Gold Text Usage:**
- Default body text: `text-amber-400` or `var(--text-primary)`
- Headings: `text-amber-400` with `font-semibold`
- Muted/secondary text: `text-amber-600` or `var(--text-muted)`
- High contrast when needed: `text-amber-100` or `var(--text-light)`
- Interactive elements (links, buttons): Use primary blue accent for distinction

### Sidebar Navigation Pattern (Elder Style)

**Required for applications with complex navigation:**

**Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  Logo Section (h-16, centered)                              │
├─────────────────────────────────────────────────────────────┤
│  Primary Navigation (always visible)                        │
│    ├── Dashboard                                            │
│    ├── Search                                               │
│    └── Overview                                             │
├─────────────────────────────────────────────────────────────┤
│  Category: Assets (collapsible)           [▼]               │
│    ├── Entities                                             │
│    ├── Organizations                                        │
│    └── Services                                             │
├─────────────────────────────────────────────────────────────┤
│  Category: Settings (collapsible)         [▶]               │
│    └── (collapsed)                                          │
├─────────────────────────────────────────────────────────────┤
│  Admin Section (role-based, yellow accent)                  │
│    └── System Settings                                      │
├─────────────────────────────────────────────────────────────┤
│  User Section (bottom, border-top)                          │
│    ├── Profile                                              │
│    └── Logout                                               │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Requirements:**

1. **Fixed Positioning**: Sidebar fixed to left edge, full height
   ```jsx
   <div className="fixed inset-y-0 left-0 w-64 bg-slate-800 border-r border-slate-700">
   ```

2. **Collapsible Categories**: State-managed category groups
   ```typescript
   const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({})

   const toggleCategory = (header: string) => {
     setCollapsedCategories(prev => ({
       ...prev,
       [header]: !prev[header]
     }))
   }
   ```

3. **Navigation Item Styling**:
   ```jsx
   <Link
     to={item.href}
     className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
       isActive
         ? 'bg-primary-600 text-white'
         : 'text-amber-400 hover:bg-slate-700 hover:text-amber-200'
     }`}
   >
     <Icon className="w-5 h-5 mr-3" />
     {item.name}
   </Link>
   ```

4. **Active Route Detection**:
   ```typescript
   const isActive = location.pathname === item.href ||
                    location.pathname.startsWith(item.href + '/')
   ```

5. **Admin Items** (role-based with yellow accent):
   ```jsx
   className={isActive
     ? 'bg-yellow-600/20 text-yellow-500 border border-yellow-600/30'
     : 'text-amber-400 hover:bg-slate-700 hover:text-amber-200'}
   ```

6. **Main Content Offset**: Match sidebar width
   ```jsx
   <div className="pl-64">
     <main className="min-h-screen">
       <Outlet />
     </main>
   </div>
   ```

7. **Icons**: Use `lucide-react` with consistent sizing (`w-5 h-5`)

### Tab Navigation Pattern (WaddlePerf Style)

**Required for applications with content sections:**

**Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  [Speed Test]  [Network Tests]  [Trace Tests]  [Download]   │
│  ━━━━━━━━━━━━                                               │
│  (active tab has colored underline)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Tab Content Area                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Requirements:**

1. **Tab Container Styling**:
   ```css
   .tab-navigation {
     display: flex;
     gap: 1rem;
     margin-bottom: 2rem;
     border-bottom: 2px solid var(--border-color);
   }
   ```

2. **Tab Button Styling**:
   ```css
   .tab-button {
     padding: 0.75rem 1.5rem;
     background: transparent;
     border: none;
     border-bottom: 3px solid transparent;
     color: var(--text-secondary);    /* amber-500 - gold default */
     font-size: 1rem;
     font-weight: 500;
     cursor: pointer;
     transition: all 0.2s;
     margin-bottom: -2px;  /* Overlap container border */
   }

   .tab-button:hover {
     color: var(--text-light);        /* amber-100 - lighter gold on hover */
   }

   .tab-button.active {
     color: var(--primary-500);       /* sky-blue for active distinction */
     border-bottom-color: var(--primary-500);
     font-weight: 600;
   }
   ```

3. **React Implementation**:
   ```typescript
   type TabKey = 'overview' | 'details' | 'settings' | 'logs'
   const [activeTab, setActiveTab] = useState<TabKey>('overview')

   // Tab navigation
   <div className="tab-navigation">
     {tabs.map(tab => (
       <button
         key={tab.key}
         className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
         onClick={() => setActiveTab(tab.key)}
       >
         {tab.label}
       </button>
     ))}
   </div>

   // Tab content (conditional rendering)
   {activeTab === 'overview' && <OverviewPanel />}
   {activeTab === 'details' && <DetailsPanel />}
   {activeTab === 'settings' && <SettingsPanel />}
   {activeTab === 'logs' && <LogsPanel />}
   ```

4. **Transition Details**:
   - Duration: 200ms (0.2s)
   - Properties: color, border-bottom-color
   - Easing: linear (default)

5. **Dark Mode Support**: Use CSS variables for all colors

### Combined Layout Pattern

**For applications requiring both sidebar and tabs:**

```
┌──────────────┬──────────────────────────────────────────────┐
│              │  Page Header                                 │
│   SIDEBAR    ├──────────────────────────────────────────────┤
│              │  [Tab 1]  [Tab 2]  [Tab 3]  [Tab 4]          │
│  - Primary   │  ━━━━━━━                                     │
│  - Assets    ├──────────────────────────────────────────────┤
│  - Settings  │                                              │
│  - Admin     │           Tab Content Area                   │
│              │                                              │
│  ──────────  │                                              │
│  Profile     │                                              │
│  Logout      │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

**Layout Structure:**
```jsx
<div className="flex min-h-screen">
  {/* Sidebar - fixed left */}
  <aside className="fixed inset-y-0 left-0 w-64 bg-slate-800 border-r border-slate-700">
    <Sidebar />
  </aside>

  {/* Main content - offset for sidebar */}
  <main className="flex-1 pl-64">
    <div className="p-6">
      {/* Page header - gold text */}
      <h1 className="text-2xl font-semibold text-amber-400 mb-6">Page Title</h1>

      {/* Tab navigation */}
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Tab content */}
      <div className="mt-6">
        {renderTabContent()}
      </div>
    </div>
  </main>
</div>
```

### Right Sidebar Pattern (Detail Pages)

**For detail pages with metadata panels:**

```jsx
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
  {/* Main content */}
  <div className="lg:col-span-2">
    <MainContent />
  </div>

  {/* Right sidebar */}
  <div className="lg:col-span-1 space-y-6">
    <Card title="Related Items">
      <RelatedItemsList />
    </Card>
    <Card title="Metadata">
      <MetadataPanel />
    </Card>
  </div>
</div>
```

### Required Dependencies

```json
{
  "dependencies": {
    "lucide-react": "^0.453.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.0.0"
  },
  "devDependencies": {
    "tailwindcss": "^4.0.0",
    "@tailwindcss/postcss": "^4.0.0"
  }
}
```

### Tailwind CSS v4 Theme Configuration

```css
/* index.css */
@import "tailwindcss";

@theme {
  --color-primary-50: #f0f9ff;
  --color-primary-100: #e0f2fe;
  --color-primary-200: #bae6fd;
  --color-primary-300: #7dd3fc;
  --color-primary-400: #38bdf8;
  --color-primary-500: #0ea5e9;
  --color-primary-600: #0284c7;
  --color-primary-700: #0369a1;
  --color-primary-800: #075985;
  --color-primary-900: #0c4a6e;
}
```

### Component Library Standards

**Card Component:**
```jsx
export const Card = ({ title, children, className = '' }) => (
  <div className={`bg-slate-800 border border-slate-700 rounded-lg shadow-lg ${className}`}>
    {title && (
      <div className="px-4 py-3 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-amber-400">{title}</h3>
      </div>
    )}
    <div className="p-4 text-amber-400">{children}</div>
  </div>
)
```

**Button Component:**
```jsx
const variants = {
  primary: 'bg-primary-600 hover:bg-primary-700 text-white',
  secondary: 'bg-slate-700 hover:bg-slate-600 text-amber-400',
  danger: 'bg-red-600 hover:bg-red-700 text-white',
  ghost: 'bg-transparent hover:bg-slate-700 text-amber-400 hover:text-amber-200'
}

export const Button = ({ variant = 'primary', size = 'md', children, ...props }) => (
  <button
    className={`rounded-lg font-medium transition-colors ${variants[variant]} ${sizes[size]}`}
    {...props}
  >
    {children}
  </button>
)
```

### Accessibility Requirements

1. **Keyboard Navigation**: All interactive elements must be keyboard accessible
2. **Focus States**: Visible focus indicators using `focus:ring-2 focus:ring-primary-500`
3. **ARIA Labels**: Proper labeling for screen readers
4. **Color Contrast**: Minimum 4.5:1 contrast ratio for text
5. **Reduced Motion**: Respect `prefers-reduced-motion` preference

---

## Ansible Integration

- **Documentation Research**: ALWAYS research modules on https://docs.ansible.com
- **Module verification**: Check official docs for syntax and parameters
- **Best practices**: Follow community standards and idempotency
- **Testing**: Ensure playbooks are idempotent

---

## Git Workflow

- **NEVER commit automatically** unless explicitly requested
- **NEVER push to remote repositories** under any circumstances
- **ONLY commit when explicitly asked**
- Always use feature branches
- Require pull request reviews for main branch
- Automated testing must pass before merge

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
    # Not exposed to host - internal network only

volumes:
  ai-models:
```

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

@app.route('/api/ai/analyze', methods=['POST'])
@auth_required()
@requires_feature('ai_analysis')  # License-gate AI features
async def ai_analyze():
    """AI-powered analysis - enterprise feature"""
    data = request.get_json()
    result = await ai_client.analyze_text(data['text'], data.get('task', 'sentiment'))
    return jsonify(result)
```

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

1. **Optional Integration**: Only add WaddleAI when AI features are needed
2. **License Gating**: AI features are typically enterprise/professional tier
3. **Performance**: AI inference can be resource-intensive - monitor usage
4. **Isolation**: Run WaddleAI as separate service for resource isolation
5. **Documentation**: Refer to WaddleAI documentation at `~/code/WaddleAI`

---

## Licensing and Feature Gating

### License Enforcement Timing

**IMPORTANT: License enforcement is enabled ONLY when project is release-ready**

**Development Phase (Pre-Release):**
- License checking code is present but not enforced
- All features available during development
- Focus on feature development and testing
- No license validation failures

**Release Phase (Production):**
- User explicitly marks project as "release ready"
- License enforcement is enabled
- Feature gating becomes active
- License validation required for startup

**Implementation Pattern:**

```python
import os
from shared.licensing import license_client

# Check if in release mode
RELEASE_MODE = os.getenv('RELEASE_MODE', 'false').lower() == 'true'

def check_license():
    """Check license only in release mode"""
    if not RELEASE_MODE:
        # Development mode - bypass license checks
        return {'valid': True, 'tier': 'development', 'features': '*'}

    # Release mode - enforce license
    validation = license_client.validate()
    if not validation.get('valid'):
        raise Exception(f"License validation failed: {validation.get('message')}")
    return validation

def requires_feature(feature_name):
    """Decorator to gate features by license tier"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if RELEASE_MODE:
                # Enforce license in release mode
                if not license_client.has_feature(feature_name):
                    raise PermissionError(f"Feature '{feature_name}' requires higher license tier")
            # Development mode - allow all features
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

**Environment Variables:**
```bash
# Development (default)
RELEASE_MODE=false

# Production (explicitly set)
RELEASE_MODE=true
LICENSE_KEY=PENG-XXXX-XXXX-XXXX-XXXX-ABCD
```

### Enterprise Features

**ALWAYS license-gate these features as enterprise-only:**
- SSO (SAML, OAuth2, OIDC)
- Advanced AI capabilities
- Multi-tenancy
- Audit logging and compliance
- Advanced analytics
- Custom integrations
- Priority support

---

## Quality Checklist

Before marking any task complete, verify:
- ✅ All error cases handled properly
- ✅ Unit tests cover all code paths
- ✅ Integration tests verify component interactions
- ✅ Security requirements fully implemented
- ✅ Performance meets acceptable standards
- ✅ Documentation complete and accurate
- ✅ Code review standards met
- ✅ No hardcoded secrets or credentials
- ✅ Logging and monitoring in place
- ✅ Build passes in containerized environment
- ✅ No security vulnerabilities in dependencies
- ✅ Edge cases and boundary conditions tested
- ✅ License enforcement configured correctly (if release-ready)
