🗄️ Database Guide - Your Data's New Home
==========================================

Part of [Development Standards](../STANDARDS.md)

Welcome to the database standards! This guide explains how to set up, manage, and query data safely and efficiently. Think of databases as libraries—they organize your information so you can find and update it quickly.

## What Databases Do We Support?

Your application speaks the language of **four databases**. Pick one to start, and your code will work with the rest:

| Database | Identifier | Version | Best For | Emoji |
|----------|-----------|---------|----------|-------|
| **PostgreSQL** | `postgresql` | **16.x** (standard) | Production, real apps | ⭐⭐⭐⭐⭐ |
| **MySQL** | `mysql` | 8.0+ | Production alternative | ⭐⭐⭐⭐ |
| **MariaDB Galera** | `mysql` | 10.11+ | High-availability clusters | ⭐⭐⭐⭐⭐ |
| **SQLite** | `sqlite` | 3.x | Development, testing | ⭐⭐⭐ |

---

## The Secret Sauce: Two Libraries (Not One!)

Here's the magic trick: we use **two different libraries** working together. It sounds odd, but trust us—it's brilliant.

### The Analogy 🎭

Think of a restaurant kitchen:
- **SQLAlchemy** = Head chef who designs the kitchen layout and equipment (schemas, tables, structure)
- **PyDAL** = Line cooks who prep and serve food every day (queries, operations, data handling)

The head chef designs once. The line cooks execute thousands of times. Both need to see the same kitchen design, but they have different jobs.

### Why Two Libraries? (The Real Reasons)

✅ **SQLAlchemy + Alembic** handles:
- Defining your database structure (schemas, tables, columns)
- Creating migrations (versioned changes to your database)
- Type-safe schema definitions
- One-time setup tasks

✅ **PyDAL** handles:
- Day-to-day queries (SELECT, INSERT, UPDATE, DELETE)
- Connection pooling (reusing connections efficiently)
- Thread-safe access (safe for multiple requests)
- Runtime operations

**Result?** Clean separation, fewer bugs, easier maintenance.

---

## Step-by-Step: Set Up Your Database

### Step 1: Choose Your Database

Pick one from the table above. For development, SQLite is easiest. For production, use PostgreSQL.

### Step 2: Define Your Schema (SQLAlchemy)

This runs **once** during initial setup:

```python
"""Database initialization - Run ONCE during setup"""
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime
import os

def initialize_database():
    """Create tables in your database"""
# Database Standards

Part of [Development Standards](../STANDARDS.md)

## Supported Databases

ALL applications MUST support the following databases by default:

| Database | DB_TYPE Value | Use Case | Notes |
|----------|---------------|----------|-------|
| **PostgreSQL** | `postgresql` | Production (default) | Primary database for all deployments |
| **MySQL** | `mysql` | Production alternative | Full support for MySQL 8.0+ |
| **MariaDB Galera** | `mysql` | High-availability clusters | Requires special handling (see below) |
| **SQLite** | `sqlite` | Development/lightweight | File-based, no server required |

## Dual-Library Architecture (Python) - MANDATORY

ALL Python applications MUST use a dual-library approach for database access:

1. **SQLAlchemy + Alembic** - Schema Definition and Migrations
   - Define database schemas using SQLAlchemy ORM models
   - Generate and manage migrations with Alembic
   - Version-controlled migration history
   - NOT used for runtime queries

2. **PyDAL** - Runtime Operations Only
   - ALL runtime database queries and operations
   - Connection pooling and thread-safe access
   - Table definitions matching SQLAlchemy schema

**Why This Approach:**
- SQLAlchemy ORM provides type-safe schema definition
- Alembic enables explicit, version-controlled migrations
- PyDAL offers simpler runtime query syntax
- Clear separation: schema (SQLAlchemy/Alembic) vs operations (PyDAL)
- Better compatibility with MariaDB Galera cluster requirements
- Explicit migration control with rollback capability

### SQLAlchemy Initialization Example

```python
"""Database initialization using SQLAlchemy - RUN ONCE during setup"""
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.schema import CreateTable
import os

def get_sqlalchemy_engine():
    """Create SQLAlchemy engine for initialization only"""
    db_type = os.getenv('DB_TYPE', 'postgresql')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'app_db')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', 'app_pass')

    # Build the database URL
    if db_type == 'sqlite':
        db_url = f"sqlite:///{db_name}.db"
    else:
        dialect_map = {
            'postgresql': 'postgresql',
            'mysql': 'mysql+pymysql',
        }
        dialect = dialect_map.get(db_type, 'postgresql')
        db_url = f"{dialect}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    # Create engine and schema
    engine = create_engine(db_url)
    metadata = MetaData()

    # Define your tables
    users_table = Table('auth_user', metadata,
    # Map DB_TYPE to SQLAlchemy dialect
    dialect_map = {
        'postgresql': 'postgresql',
        'mysql': 'mysql+pymysql',
        'sqlite': 'sqlite',
    }
    dialect = dialect_map.get(db_type, 'postgresql')

    if db_type == 'sqlite':
        db_url = f"sqlite:///{db_name}.db"
    else:
        db_url = f"{dialect}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    return create_engine(db_url)

def initialize_database():
    """One-time database schema initialization"""
    engine = get_sqlalchemy_engine()
    metadata = MetaData()

    # Define tables for initial schema creation
    users = Table('auth_user', metadata,
        Column('id', Integer, primary_key=True),
        Column('email', String(255), unique=True, nullable=False),
        Column('password', String(255)),
        Column('active', Boolean, default=True),
        Column('fs_uniquifier', String(64), unique=True),
        Column('confirmed_at', DateTime),
    )

    # Create all tables
    metadata.create_all(engine)
    print("✅ Database schema created!")

# Run this ONCE when setting up
    roles = Table('auth_role', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(80), unique=True),
        Column('description', String(255)),
    )

    # Create all tables
    metadata.create_all(engine)
    print("Database schema initialized via SQLAlchemy")

# Run during application first-time setup ONLY
if __name__ == '__main__':
    initialize_database()
```

💡 **Tip:** Run this once, then move on. You don't need this code in your daily application.

### Step 3: Query Your Data (PyDAL)

This is what your app does **every single day**:

```python
"""Runtime database operations - Use this in your app"""
from pydal import DAL, Field
import os

def get_db_connection():
    """Connect to the database for queries"""
### PyDAL Runtime Example

```python
"""Runtime database operations using PyDAL"""
from pydal import DAL, Field
import os

def get_pydal_connection():
    """Get PyDAL connection for runtime operations"""
    db_type = os.getenv('DB_TYPE', 'postgresql')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'app_db')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', 'app_pass')
    pool_size = int(os.getenv('DB_POOL_SIZE', '10'))

    # Build connection string
    if db_type == 'sqlite':
        db_uri = f"sqlite://{db_name}.db"
    else:
        db_uri = f"{db_type}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    # Connect with connection pooling
    db = DAL(
        db_uri,
        pool_size=pool_size,     # Reuse connections
        migrate=True,             # Auto-create tables if missing
    db = DAL(
        db_uri,
        pool_size=pool_size,
        migrate=True,  # PyDAL handles all migrations
        check_reserved=['all'],
        lazy_tables=True
    )

    # Define tables (mirrors your SQLAlchemy schema)
    # Define tables for PyDAL (mirrors SQLAlchemy schema)
    db.define_table('auth_user',
        Field('email', 'string', unique=True, notnull=True),
        Field('password', 'password'),
        Field('active', 'boolean', default=True),
        Field('fs_uniquifier', 'string', unique=True),
        Field('confirmed_at', 'datetime'),
        migrate=True
    )

    return db

# Use in your app
db = get_db_connection()

# Query examples
all_active_users = db(db.auth_user.active == True).select()
specific_user = db(db.auth_user.email == 'user@example.com').select().first()
# Create: db.auth_user.insert(email='new@example.com', active=True)
# Update: db(db.auth_user.id == 1).update(active=False)
# Delete: db(db.auth_user.id == 1).delete()
```

✅ **Now your app can read, write, and update data!**

---

## 💡 Pro Tips for Database Work

**Connection Pooling is Your Friend**
```python
# Pool size calculation: (2 × CPU cores) + disk spindles
# Example: 4 CPUs + 1 disk = pool size of 9
# This reuses connections, making your app 10× faster
db = DAL(db_uri, pool_size=9)
```

**Always Wait for the Database to Be Ready**
```python
import time

def wait_for_database(max_retries=5, retry_delay=5):
    """Don't start until database is ready"""
    for attempt in range(max_retries):
        try:
            test_db = get_db_connection()
            test_db.close()
            print("✅ Database is ready!")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    return False

# In your app startup:
if not wait_for_database():
    raise Exception("Could not connect to database!")
```

---

## ⚠️ Common Pitfalls (Don't Do These!)

❌ **Mistake 1: Sharing a DAL instance across threads**
```python
# WRONG - will cause errors!
db = DAL(db_uri)  # Global instance
def worker():
    db.auth_user.select()  # Multiple threads using same object
```

✅ **Right way:**
```python
import threading
thread_local = threading.local()

def get_thread_db():
    if not hasattr(thread_local, 'db'):
        thread_local.db = DAL(db_uri)  # Each thread gets its own
    return thread_local.db

def worker():
    db = get_thread_db()  # Safe to use
    db.auth_user.select()
```

---

❌ **Mistake 2: Not waiting for the database**
```python
# WRONG - starts immediately!
app = Flask(__name__)
db = DAL(db_uri)  # Might not exist yet!
```

✅ **Right way:**
```python
# Implement retry logic (see "Pro Tips" above)
if not wait_for_database():
    sys.exit(1)
db = DAL(db_uri)  # Now safe!
```

---

❌ **Mistake 3: Hardcoding database settings**
```python
# WRONG - breaks on different servers
db = DAL("mysql://root:password@localhost/mydb")
```

✅ **Right way:**
```python
# Use environment variables
db_uri = f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
db = DAL(db_uri)
```

---

❌ **Mistake 4: Mixing SQLAlchemy and PyDAL for queries**
```python
# WRONG - SQLAlchemy is only for setup!
from sqlalchemy import select
engine = create_engine(db_uri)
session = Session(engine)
users = session.query(User).all()  # Don't do this at runtime
```

✅ **Right way:**
```python
# SQLAlchemy = setup only (initialize_database function)
# PyDAL = queries (in your app)
db = DAL(db_uri)
users = db(db.auth_user.id > 0).select()  # Clean and fast
```

---

## 🔧 Troubleshooting Common Errors

### Problem: "Connection refused" or "Cannot connect to database"

**Solution 1: Check the database is running**
```bash
# For PostgreSQL
docker ps | grep postgres

# For MySQL
docker ps | grep mysql

# For SQLite (always runs)
ls -la *.db
```

**Solution 2: Verify environment variables**
```bash
echo $DB_TYPE
echo $DB_HOST
echo $DB_PORT
echo $DB_USER
echo $DB_NAME
```

**Solution 3: Check the connection string**
```python
print(f"Connecting to: {db_uri}")  # What does it look like?
```

### Problem: "Table already exists" error

**Solution:** This is usually harmless. It means the table was created on a previous run.
```python
# This is safe - PyDAL won't recreate if it already exists
db = DAL(db_uri, migrate=True)
```

### Problem: "Too many connections"

**Solution:** Increase your pool size or reduce concurrent requests
```python
# Before: pool_size=5 (only 5 connections)
db = DAL(db_uri, pool_size=5)

# After: pool_size=20 (handle more requests)
db = DAL(db_uri, pool_size=20)
```

### Problem: "Unique constraint violated" when inserting

**Solution:** Check if the record already exists
```python
existing = db(db.auth_user.email == 'test@example.com').select().first()
if existing:
    print("User already exists!")
else:
    db.auth_user.insert(email='test@example.com')
```

---

## Environment Variables (Your Database Config)

Your database talks to your app through these settings:

```bash
DB_TYPE=postgresql           # postgresql, mysql, sqlite
DB_HOST=localhost            # Where the database lives
DB_PORT=5432                 # Port number (5432=postgres, 3306=mysql)
DB_NAME=app_db              # Database name
DB_USER=app_user            # Username
DB_PASS=app_pass            # Password
DB_POOL_SIZE=10             # How many connections to keep ready
DB_MAX_RETRIES=5            # How many times to try connecting
DB_RETRY_DELAY=5            # Seconds between retry attempts
```

---

## Special Handling: MariaDB Galera Clusters

MariaDB Galera is like having multiple database copies that stay in sync. Special care needed:

```python
def get_galera_db():
    """MariaDB Galera configuration"""
# Runtime usage
db = get_pydal_connection()
# Query example: db(db.auth_user.active == True).select()
```

## MariaDB Galera Cluster Support

MariaDB Galera requires special handling for cluster-aware operations:

```python
"""MariaDB Galera-specific configuration"""
import os

def get_galera_pydal_connection():
    """PyDAL connection with Galera-specific settings"""
    db_uri = f"mysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

    db = DAL(
        db_uri,
        pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
        migrate=True,
        check_reserved=['all'],
        lazy_tables=True,
        driver_args={'charset': 'utf8mb4'}  # Galera requirement
    )
    return db
```

**Galera Tips:**
- ✅ Keep transactions short (avoid conflicts)
- ✅ Avoid long-running queries (they block other nodes)
- ✅ DDL changes (ALTER TABLE) should happen during low-traffic times

---

## Go Applications (High-Performance Backend)

When using Go, use GORM for database access:

        # Galera-specific: Use ROW format for binary logging
        driver_args={'charset': 'utf8mb4'}
    )

    return db

# Galera-specific considerations:
# 1. AUTO_INCREMENT: Use larger increment steps for multi-node writes
# 2. WSREP: Check wsrep_ready before critical operations
# 3. Transactions: Avoid long-running transactions (certification conflicts)
# 4. DDL: Schema changes replicate as TOI (Total Order Isolation)
```

**Galera Requirements:**
- Use `innodb_autoinc_lock_mode=2` for interleaved auto-increment
- Check `wsrep_ready` status before writes
- Keep transactions short to avoid certification failures
- Plan DDL operations during low-traffic periods

## Async and Multi-Threading Requirements

Database operations MUST use appropriate concurrency patterns based on workload characteristics:

### Decision Matrix

| Workload Type | Recommended Approach | Libraries | Use Case |
|---------------|---------------------|-----------|----------|
| **I/O-bound (network, disk)** | Async/await | `asyncio`, `aiohttp`, `databases` | Web APIs, external service calls |
| **CPU-bound** | Multi-processing | `multiprocessing`, `concurrent.futures` | Data processing, calculations |
| **Mixed I/O with blocking** | Multi-threading | `threading`, `concurrent.futures` | Legacy integrations, file I/O |
| **High-concurrency web** | Async + thread pool | `asyncio` + `ThreadPoolExecutor` | Flask/async hybrid patterns |

### Async Database Operations (Recommended for Web APIs)

```python
"""Async database operations for high-concurrency scenarios"""
import asyncio
from databases import Database
import os

# Async database connection (use alongside PyDAL for specific async needs)
async def get_async_db():
    """Get async database connection for I/O-bound operations"""
    db_type = os.getenv('DB_TYPE', 'postgresql')
    db_url = f"{db_type}://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

    database = Database(db_url)
    await database.connect()
    return database

async def fetch_users_async(database: Database):
    """Example async query - better for high-concurrency web requests"""
    query = "SELECT * FROM auth_user WHERE active = :active"
    return await database.fetch_all(query=query, values={"active": True})

# Usage in async context
async def main():
    db = await get_async_db()
    users = await fetch_users_async(db)
    await db.disconnect()
```

### Multi-Threading for Blocking Operations

```python
"""Thread-safe database operations for blocking I/O"""
import threading
from concurrent.futures import ThreadPoolExecutor
from pydal import DAL, Field

# Thread-local storage for DAL instances
thread_local = threading.local()

def get_thread_db():
    """Get thread-local PyDAL connection"""
    if not hasattr(thread_local, 'db'):
        db_uri = f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        thread_local.db = DAL(db_uri, pool_size=5, migrate=False)
    return thread_local.db

def process_user(user_id: int):
    """Process user in separate thread"""
    db = get_thread_db()
    user = db(db.auth_user.id == user_id).select().first()
    # Process user...
    return user

# Parallel processing with thread pool
def process_users_parallel(user_ids: list[int], max_workers: int = 10):
    """Process multiple users in parallel threads"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_user, user_ids))
    return results
```

### Flask Async Hybrid Pattern

```python
"""Flask with async database operations"""
from flask import Flask, g
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=20)

def run_async(coro):
    """Run async coroutine in thread pool for Flask compatibility"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/users')
def get_users():
    """Endpoint using async database operations"""
    async def fetch():
        db = await get_async_db()
        users = await fetch_users_async(db)
        await db.disconnect()
        return users

    # Run async operation in thread pool
    future = executor.submit(run_async, fetch())
    users = future.result(timeout=30)
    return {"users": users}
```

### Performance Guidelines

1. **Choose async when:**
   - Handling >100 concurrent requests
   - Operations are primarily network I/O (database, HTTP calls)
   - Low latency is critical (<100ms response time)

2. **Choose multi-threading when:**
   - Integrating with blocking libraries (legacy code)
   - File system operations
   - Moderate concurrency needs (10-100 concurrent operations)

3. **Choose multi-processing when:**
   - CPU-intensive calculations
   - Data transformation pipelines
   - Batch processing jobs

4. **Connection Pool Sizing:**
   - Async: Pool size = expected concurrent requests / 2
   - Threading: Pool size = number of worker threads + buffer
   - Rule of thumb: `pool_size = (2 * CPU_cores) + disk_spindles`

## Go Database Requirements

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
    dbType := os.Getenv("DB_TYPE")
    dbType := os.Getenv("DB_TYPE") // "postgres" or "mysql"
    dsn := os.Getenv("DATABASE_URL")

    var dialector gorm.Dialector
    switch dbType {
    case "mysql":
        dialector = mysql.Open(dsn)
    default:
    default: // postgres
        dialector = postgres.Open(dsn)
    }

    db, err := gorm.Open(dialector, &gorm.Config{})
    return db, err
}
```

---

## Threading & Async: Choose Your Power Level

Different workloads need different approaches:

| Your Situation | Use This | Why |
|---|---|---|
| Web API with 100+ requests | `asyncio` + `databases` | Single-threaded, super fast |
| Mixed blocking code | `threading` + `ThreadPoolExecutor` | Handles old code + new code |
| CPU-heavy calculations | `multiprocessing` | True parallel processing |

### Flask + Async Pattern (Recommended)

```python
from flask import Flask, g
from concurrent.futures import ThreadPoolExecutor
import asyncio

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=20)

def run_in_thread(async_func):
    """Run async code in Flask"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(async_func)
    finally:
        loop.close()

@app.route('/users')
def get_users():
    """Returns users quickly using async"""
    async def fetch():
        db = await get_async_db()
        users = await db.fetch_all("SELECT * FROM auth_user WHERE active = :active", values={"active": True})
        await db.disconnect()
        return users

    future = executor.submit(run_in_thread, fetch())
    return {"users": future.result(timeout=30)}
```

---

## Summary: Database Recipe

1. **Setup Once:** Use SQLAlchemy to define your schema
2. **Query Always:** Use PyDAL for all runtime operations
3. **Use Environment Variables:** Never hardcode database settings
4. **Wait for Database:** Implement retry logic on startup
5. **Thread Safety:** Each thread gets its own connection
6. **Pool Your Connections:** Formula is (2 × CPU cores) + spindles

**Your data is safe, fast, and ready to scale!** 🚀
## Environment Variables

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

## Database Connection Requirements

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

## Implementation Pattern

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

## Thread Safety Requirements

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
