"""
Database Operations API for IceCharts Connector Framework.

Provides a gateway for database connector manifests to execute operations
against PyDAL-supported databases. All database connector YAML manifests
route their actions through these endpoints.

Endpoints:
    POST /query       - Execute SELECT query via PyDAL
    POST /insert      - Insert row(s)
    POST /update      - Update row(s) with conditions
    POST /delete      - Delete row(s) with conditions
    POST /bulk-insert - Bulk insert rows
    POST /procedure   - Call stored procedure (SQL DBs only)
    GET  /schema      - Get table/collection schema
    GET  /count       - Count rows matching criteria
    GET  /exists      - Check if record exists
    GET  /health      - Test database connectivity
"""

import logging
from typing import Any, Dict

from flask import Blueprint, jsonify, request
from pydal import DAL

from app.middleware import auth_required
from app.models import DB_TYPE_TO_PYDAL_SCHEME, VALID_DB_TYPES

logger = logging.getLogger(__name__)

database_ops_v1_bp = Blueprint("database_ops", __name__, url_prefix="/database-ops")

# NoSQL databases that don't support stored procedures
NOSQL_DB_TYPES = {"mongodb", "couchdb", "firestore"}

# Maximum limits to prevent abuse
MAX_BULK_INSERT_ROWS = 10000
MAX_QUERY_LIMIT = 10000


def _build_db_uri(config: Dict[str, Any]) -> str:
    """
    Build a PyDAL database URI from connector config.

    Args:
        config: Database connection configuration from request body.

    Returns:
        PyDAL-compatible database URI string.

    Raises:
        ValueError: If db_type is invalid or required fields are missing.
    """
    db_type = config.get("db_type", "").lower()
    if db_type not in VALID_DB_TYPES:
        raise ValueError(
            f"Invalid db_type: {db_type}. " f"Must be one of: {sorted(VALID_DB_TYPES)}"
        )

    scheme = DB_TYPE_TO_PYDAL_SCHEME[db_type]

    if scheme == "sqlite":
        db_path = config.get("db_path", ":memory:")
        return f"sqlite://{db_path}"

    if scheme == "google:datastore":
        project = config.get("project_id", "")
        return f"google:datastore+ndb://project={project}"

    host = config.get("host", "localhost")
    port = config.get("port", "")
    database = config.get("database", "")
    user = config.get("user", "")
    password = config.get("password", "")

    if not database:
        raise ValueError("database name is required")

    port_str = f":{port}" if port else ""
    auth_str = f"{user}:{password}@" if user else ""

    return f"{scheme}://{auth_str}{host}{port_str}/{database}"


def _get_connection(config: Dict[str, Any]) -> DAL:
    """
    Create a temporary PyDAL connection from config.

    Args:
        config: Database connection configuration.

    Returns:
        PyDAL DAL instance.
    """
    uri = _build_db_uri(config)
    return DAL(
        uri,
        pool_size=1,
        migrate_enabled=False,
        check_reserved=["common"],
    )


def _extract_connection_config() -> Dict[str, Any]:
    """Extract and validate connection config from request body."""
    data = request.get_json(silent=True) or {}
    connection = data.get("connection", {})
    if not connection:
        raise ValueError("connection config is required")
    if not connection.get("db_type"):
        raise ValueError("connection.db_type is required")
    return connection


@database_ops_v1_bp.route("/health", methods=["GET"])
@auth_required
def health_check():
    """
    Test database connectivity.

    Query params:
        db_type: Database type
        host: Database host
        port: Database port
        database: Database name
        user: Username
        password: Password
    """
    try:
        config = {
            "db_type": request.args.get("db_type", ""),
            "host": request.args.get("host", "localhost"),
            "port": request.args.get("port", ""),
            "database": request.args.get("database", ""),
            "user": request.args.get("user", ""),
            "password": request.args.get("password", ""),
        }

        if not config["db_type"]:
            return jsonify({"error": "db_type query param is required"}), 400

        db = _get_connection(config)
        db.close()

        return jsonify({"status": "connected", "db_type": config["db_type"]}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 503


@database_ops_v1_bp.route("/query", methods=["POST"])
@auth_required
def execute_query():
    """
    Execute a SELECT query via PyDAL.

    Request body:
        {
            "connection": { "db_type": "...", "host": "...", ... },
            "table": "users",
            "fields": ["id", "name", "email"],
            "where": {"status": "active"},
            "orderby": "name",
            "limit": 100,
            "offset": 0
        }
    """
    db = None
    try:
        data = request.get_json(silent=True) or {}
        connection = _extract_connection_config()

        table_name = data.get("table")
        if not table_name:
            return jsonify({"error": "table is required"}), 400

        fields = data.get("fields", [])
        where = data.get("where", {})
        limit = min(data.get("limit", 100), MAX_QUERY_LIMIT)
        offset = data.get("offset", 0)

        db = _get_connection(connection)

        # Define table dynamically if it doesn't exist in DAL
        if table_name not in db.tables:
            db.define_table(table_name, migrate=False, fake_migrate=True)

        table = db[table_name]

        # Build query from where conditions
        query = table.id > 0  # base query
        for field_name, value in where.items():
            if hasattr(table, field_name):
                query &= table[field_name] == value

        # Select fields
        if fields:
            select_fields = [table[f] for f in fields if hasattr(table, f)]
        else:
            select_fields = [table.ALL]

        rows = db(query).select(
            *select_fields,
            limitby=(offset, offset + limit),
        )

        result = [row.as_dict() for row in rows]

        return (
            jsonify(
                {
                    "data": result,
                    "count": len(result),
                    "limit": limit,
                    "offset": offset,
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()


@database_ops_v1_bp.route("/insert", methods=["POST"])
@auth_required
def insert_row():
    """
    Insert a row into a table.

    Request body:
        {
            "connection": { "db_type": "...", ... },
            "table": "users",
            "data": {"name": "John", "email": "john@example.com"}
        }
    """
    db = None
    try:
        data = request.get_json(silent=True) or {}
        connection = _extract_connection_config()

        table_name = data.get("table")
        row_data = data.get("data", {})
        if not table_name:
            return jsonify({"error": "table is required"}), 400
        if not row_data:
            return jsonify({"error": "data is required"}), 400

        db = _get_connection(connection)

        if table_name not in db.tables:
            db.define_table(table_name, migrate=False, fake_migrate=True)

        row_id = db[table_name].insert(**row_data)
        db.commit()

        return jsonify({"id": row_id, "status": "inserted"}), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Insert failed: {e}")
        if db:
            db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()


@database_ops_v1_bp.route("/update", methods=["POST"])
@auth_required
def update_rows():
    """
    Update rows matching conditions.

    Request body:
        {
            "connection": { "db_type": "...", ... },
            "table": "users",
            "where": {"id": 1},
            "data": {"name": "Updated Name"}
        }
    """
    db = None
    try:
        data = request.get_json(silent=True) or {}
        connection = _extract_connection_config()

        table_name = data.get("table")
        where = data.get("where", {})
        row_data = data.get("data", {})
        if not table_name:
            return jsonify({"error": "table is required"}), 400
        if not where:
            return jsonify({"error": "where conditions are required"}), 400
        if not row_data:
            return jsonify({"error": "data is required"}), 400

        db = _get_connection(connection)

        if table_name not in db.tables:
            db.define_table(table_name, migrate=False, fake_migrate=True)

        table = db[table_name]
        query = table.id > 0
        for field_name, value in where.items():
            if hasattr(table, field_name):
                query &= table[field_name] == value

        count = db(query).update(**row_data)
        db.commit()

        return jsonify({"updated": count, "status": "updated"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Update failed: {e}")
        if db:
            db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()


@database_ops_v1_bp.route("/delete", methods=["POST"])
@auth_required
def delete_rows():
    """
    Delete rows matching conditions.

    Request body:
        {
            "connection": { "db_type": "...", ... },
            "table": "users",
            "where": {"id": 1}
        }
    """
    db = None
    try:
        data = request.get_json(silent=True) or {}
        connection = _extract_connection_config()

        table_name = data.get("table")
        where = data.get("where", {})
        if not table_name:
            return jsonify({"error": "table is required"}), 400
        if not where:
            return jsonify({"error": "where conditions are required"}), 400

        db = _get_connection(connection)

        if table_name not in db.tables:
            db.define_table(table_name, migrate=False, fake_migrate=True)

        table = db[table_name]
        query = table.id > 0
        for field_name, value in where.items():
            if hasattr(table, field_name):
                query &= table[field_name] == value

        count = db(query).delete()
        db.commit()

        return jsonify({"deleted": count, "status": "deleted"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        if db:
            db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()


@database_ops_v1_bp.route("/bulk-insert", methods=["POST"])
@auth_required
def bulk_insert():
    """
    Bulk insert multiple rows.

    Request body:
        {
            "connection": { "db_type": "...", ... },
            "table": "users",
            "rows": [
                {"name": "John", "email": "john@example.com"},
                {"name": "Jane", "email": "jane@example.com"}
            ]
        }
    """
    db = None
    try:
        data = request.get_json(silent=True) or {}
        connection = _extract_connection_config()

        table_name = data.get("table")
        rows = data.get("rows", [])
        if not table_name:
            return jsonify({"error": "table is required"}), 400
        if not rows:
            return jsonify({"error": "rows is required"}), 400
        if len(rows) > MAX_BULK_INSERT_ROWS:
            return (
                jsonify({"error": f"Maximum {MAX_BULK_INSERT_ROWS} rows per request"}),
                400,
            )

        db = _get_connection(connection)

        if table_name not in db.tables:
            db.define_table(table_name, migrate=False, fake_migrate=True)

        inserted_ids = []
        for row in rows:
            row_id = db[table_name].insert(**row)
            inserted_ids.append(row_id)

        db.commit()

        return (
            jsonify(
                {
                    "ids": inserted_ids,
                    "count": len(inserted_ids),
                    "status": "inserted",
                }
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Bulk insert failed: {e}")
        if db:
            db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()


@database_ops_v1_bp.route("/procedure", methods=["POST"])
@auth_required
def call_procedure():
    """
    Call a stored procedure (SQL databases only).

    Request body:
        {
            "connection": { "db_type": "...", ... },
            "procedure": "my_procedure",
            "params": ["arg1", "arg2"]
        }
    """
    db = None
    try:
        data = request.get_json(silent=True) or {}
        connection = _extract_connection_config()

        db_type = connection.get("db_type", "").lower()
        if db_type in NOSQL_DB_TYPES:
            return (
                jsonify({"error": f"Stored procedures not supported for {db_type}"}),
                400,
            )

        procedure = data.get("procedure")
        params = data.get("params", [])
        if not procedure:
            return jsonify({"error": "procedure name is required"}), 400

        db = _get_connection(connection)

        # Execute stored procedure via raw SQL
        param_placeholders = ", ".join(["%s"] * len(params))
        sql = f"CALL {procedure}({param_placeholders})"
        result = db.executesql(sql, placeholders=params)

        return (
            jsonify(
                {
                    "result": result if result else [],
                    "status": "executed",
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Procedure call failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()


@database_ops_v1_bp.route("/schema", methods=["GET"])
@auth_required
def get_schema():
    """
    Get table/collection schema information.

    Query params:
        db_type, host, port, database, user, password, table
    """
    db = None
    try:
        config = {
            "db_type": request.args.get("db_type", ""),
            "host": request.args.get("host", "localhost"),
            "port": request.args.get("port", ""),
            "database": request.args.get("database", ""),
            "user": request.args.get("user", ""),
            "password": request.args.get("password", ""),
        }
        table_name = request.args.get("table")

        if not config["db_type"]:
            return jsonify({"error": "db_type is required"}), 400

        db = _get_connection(config)

        if table_name:
            # Get specific table schema
            if table_name not in db.tables:
                db.define_table(table_name, migrate=False, fake_migrate=True)
            table = db[table_name]
            fields = [
                {"name": f.name, "type": str(f.type)}
                for f in table.fields
                if f != "id" or True
            ]
            return (
                jsonify(
                    {
                        "table": table_name,
                        "fields": fields,
                    }
                ),
                200,
            )

        # List all tables
        tables = db.tables
        return jsonify({"tables": list(tables)}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Schema fetch failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()


@database_ops_v1_bp.route("/count", methods=["GET"])
@auth_required
def count_rows():
    """
    Count rows matching criteria.

    Query params:
        db_type, host, port, database, user, password, table
    Body (optional JSON):
        {"where": {"status": "active"}}
    """
    db = None
    try:
        config = {
            "db_type": request.args.get("db_type", ""),
            "host": request.args.get("host", "localhost"),
            "port": request.args.get("port", ""),
            "database": request.args.get("database", ""),
            "user": request.args.get("user", ""),
            "password": request.args.get("password", ""),
        }
        table_name = request.args.get("table")

        if not config["db_type"]:
            return jsonify({"error": "db_type is required"}), 400
        if not table_name:
            return jsonify({"error": "table is required"}), 400

        db = _get_connection(config)

        if table_name not in db.tables:
            db.define_table(table_name, migrate=False, fake_migrate=True)

        table = db[table_name]
        query = table.id > 0

        # Optional where from JSON body
        body = request.get_json(silent=True) or {}
        for field_name, value in body.get("where", {}).items():
            if hasattr(table, field_name):
                query &= table[field_name] == value

        count = db(query).count()

        return jsonify({"count": count, "table": table_name}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Count failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()


@database_ops_v1_bp.route("/exists", methods=["GET"])
@auth_required
def check_exists():
    """
    Check if a record exists matching criteria.

    Query params:
        db_type, host, port, database, user, password, table
    Body (optional JSON):
        {"where": {"email": "user@example.com"}}
    """
    db = None
    try:
        config = {
            "db_type": request.args.get("db_type", ""),
            "host": request.args.get("host", "localhost"),
            "port": request.args.get("port", ""),
            "database": request.args.get("database", ""),
            "user": request.args.get("user", ""),
            "password": request.args.get("password", ""),
        }
        table_name = request.args.get("table")

        if not config["db_type"]:
            return jsonify({"error": "db_type is required"}), 400
        if not table_name:
            return jsonify({"error": "table is required"}), 400

        db = _get_connection(config)

        if table_name not in db.tables:
            db.define_table(table_name, migrate=False, fake_migrate=True)

        table = db[table_name]
        query = table.id > 0

        body = request.get_json(silent=True) or {}
        for field_name, value in body.get("where", {}).items():
            if hasattr(table, field_name):
                query &= table[field_name] == value

        exists = db(query).count() > 0

        return jsonify({"exists": exists, "table": table_name}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Exists check failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if db:
            db.close()
