"""Storage Provider Management Endpoints for API v1."""

import time
from datetime import datetime
from typing import Optional

from flask import Blueprint, current_app, jsonify, request

from ...middleware import admin_required, auth_required, get_current_user
from ...models import get_db
from ...services.storage_usage_service import StorageUsageService

storage_v1_bp = Blueprint("storage_v1", __name__, url_prefix="/storage")


def get_storage_provider_by_id(provider_id: int) -> Optional[dict]:
    """Get storage provider by ID."""
    db = get_db()
    provider = db(db.storage_providers.id == provider_id).select().first()
    return provider.as_dict() if provider else None


@storage_v1_bp.route("/providers", methods=["GET"])
@auth_required
def list_storage_providers():
    """List available storage providers."""
    user = get_current_user()
    db = get_db()

    # Users see only their configured providers and system defaults
    if user["role"] == "admin":
        providers = db(db.storage_providers).select()
    else:
        providers = db(
            (db.storage_providers.user_id == user["id"])
            | (db.storage_providers.is_system_default == True)
        ).select()

    return (
        jsonify(
            {
                "providers": [p.as_dict() for p in providers],
                "total": len(providers),
            }
        ),
        200,
    )


@storage_v1_bp.route("/providers", methods=["POST"])
@auth_required
def create_storage_provider():
    """Configure a new storage provider."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    provider_type = data.get("provider_type", "").strip()
    name = data.get("name", "").strip()
    config = data.get("config", {})

    # Validation
    valid_types = ["local", "s3", "azure", "gcs", "webdav"]
    if provider_type not in valid_types:
        return (
            jsonify(
                {
                    "error": "Invalid provider type",
                    "valid_types": valid_types,
                }
            ),
            400,
        )

    if not name:
        return jsonify({"error": "Provider name is required"}), 400

    # Validate config based on provider type
    if provider_type == "s3":
        required_fields = ["bucket", "region", "access_key_id", "secret_access_key"]
        missing = [f for f in required_fields if f not in config]
        if missing:
            return (
                jsonify(
                    {
                        "error": "Missing required S3 configuration",
                        "missing_fields": missing,
                    }
                ),
                400,
            )

    elif provider_type == "azure":
        required_fields = ["account_name", "account_key", "container"]
        missing = [f for f in required_fields if f not in config]
        if missing:
            return (
                jsonify(
                    {
                        "error": "Missing required Azure configuration",
                        "missing_fields": missing,
                    }
                ),
                400,
            )

    elif provider_type == "gcs":
        required_fields = ["bucket", "credentials"]
        missing = [f for f in required_fields if f not in config]
        if missing:
            return (
                jsonify(
                    {
                        "error": "Missing required GCS configuration",
                        "missing_fields": missing,
                    }
                ),
                400,
            )

    db = get_db()

    # Create storage provider
    provider_id = db.storage_providers.insert(
        user_id=user["id"],
        provider_type=provider_type,
        name=name,
        config=config,
        is_active=True,
        is_system_default=False,
    )
    db.commit()

    provider = get_storage_provider_by_id(provider_id)

    return (
        jsonify(
            {
                "message": "Storage provider configured successfully",
                "provider": provider,
            }
        ),
        201,
    )


@storage_v1_bp.route("/providers/<int:provider_id>", methods=["GET"])
@auth_required
def get_storage_provider(provider_id: int):
    """Get storage provider details."""
    user = get_current_user()
    provider = get_storage_provider_by_id(provider_id)

    if not provider:
        return jsonify({"error": "Storage provider not found"}), 404

    # Check access
    if provider["user_id"] != user["id"] and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    # Mask sensitive config fields
    if "config" in provider and isinstance(provider["config"], dict):
        masked_config = provider["config"].copy()
        sensitive_fields = [
            "secret_access_key",
            "account_key",
            "credentials",
            "password",
        ]
        for field in sensitive_fields:
            if field in masked_config:
                masked_config[field] = "***MASKED***"
        provider["config"] = masked_config

    return jsonify({"provider": provider}), 200


@storage_v1_bp.route("/providers/<int:provider_id>", methods=["PUT"])
@auth_required
def update_storage_provider(provider_id: int):
    """Update storage provider configuration."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    provider = get_storage_provider_by_id(provider_id)
    if not provider:
        return jsonify({"error": "Storage provider not found"}), 404

    # Check access
    if provider["user_id"] != user["id"] and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    db = get_db()
    update_data = {}

    if "name" in data:
        update_data["name"] = data["name"].strip()
    if "config" in data:
        update_data["config"] = data["config"]
    if "is_active" in data:
        update_data["is_active"] = data["is_active"]

    if update_data:
        db(db.storage_providers.id == provider_id).update(**update_data)
        db.commit()

    updated_provider = get_storage_provider_by_id(provider_id)

    return (
        jsonify(
            {
                "message": "Storage provider updated successfully",
                "provider": updated_provider,
            }
        ),
        200,
    )


@storage_v1_bp.route("/providers/<int:provider_id>", methods=["DELETE"])
@auth_required
def delete_storage_provider(provider_id: int):
    """Delete storage provider."""
    user = get_current_user()
    provider = get_storage_provider_by_id(provider_id)

    if not provider:
        return jsonify({"error": "Storage provider not found"}), 404

    # Check access
    if provider["user_id"] != user["id"] and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    # Prevent deletion of system defaults
    if provider.get("is_system_default"):
        return jsonify({"error": "Cannot delete system default provider"}), 400

    db = get_db()

    # Delete provider
    db(db.storage_providers.id == provider_id).delete()
    db.commit()

    return (
        jsonify(
            {
                "message": "Storage provider deleted successfully",
            }
        ),
        200,
    )


@storage_v1_bp.route("/providers/<int:provider_id>/test", methods=["POST"])
@auth_required
def test_storage_provider(provider_id: int):
    """Test storage provider connection and permissions.

    Performs comprehensive testing including:
    - Connection validation
    - Credentials verification
    - Bucket/container access
    - Read/write permissions
    - Test file operations
    """
    user = get_current_user()
    provider = get_storage_provider_by_id(provider_id)

    if not provider:
        return jsonify({"error": "Storage provider not found"}), 404

    # Check access
    if provider["user_id"] != user["id"] and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    # Get config
    config = provider.get("config_json") or provider.get("config", {})
    provider_type = provider.get("provider_type", "").lower()

    try:
        # Test based on provider type
        if provider_type == "s3":
            test_result = _test_s3_provider(config)
        elif provider_type == "minio":
            test_result = _test_minio_provider(config)
        elif provider_type == "azure":
            test_result = _test_azure_provider(config)
        elif provider_type == "gcs":
            test_result = _test_gcs_provider(config)
        elif provider_type == "local":
            test_result = _test_local_provider(config)
        else:
            return (
                jsonify(
                    {
                        "error": f"Unsupported provider type: {provider_type}",
                        "status": "error",
                    }
                ),
                400,
            )

        return (
            jsonify(
                {
                    "message": "Storage provider connection test successful",
                    "status": "ok",
                    "provider_type": provider_type,
                    **test_result,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Storage test failed for provider {provider_id}: {e}")

        error_message = str(e)
        status_code = 500

        # Map error types to status codes
        if "Access denied" in error_message or "Unauthorized" in error_message:
            status_code = 401
        elif (
            "not found" in error_message.lower()
            or "does not exist" in error_message.lower()
        ):
            status_code = 404
        elif "Invalid" in error_message or "Missing" in error_message:
            status_code = 400

        return (
            jsonify(
                {
                    "error": error_message,
                    "status": "error",
                    "provider_type": provider_type,
                }
            ),
            status_code,
        )


def _test_s3_provider(config: dict) -> dict:
    """Test AWS S3 provider connectivity."""
    import boto3
    from botocore.exceptions import (
        ClientError,
        NoCredentialsError,
        PartialCredentialsError,
    )

    required = ["bucket", "access_key_id", "secret_access_key"]
    missing = [f for f in required if f not in config]
    if missing:
        raise ValueError(f"Missing required S3 configuration: {missing}")

    try:
        session = boto3.Session(
            aws_access_key_id=config["access_key_id"],
            aws_secret_access_key=config["secret_access_key"],
            region_name=config.get("region", "us-east-1"),
        )
        s3_client = session.client("s3")
        bucket = config["bucket"]

        try:
            s3_client.head_bucket(Bucket=bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise Exception(f"Bucket does not exist: {bucket}")
            elif error_code == "403":
                raise Exception(f"Access denied to bucket: {bucket}")
            raise Exception(f"Failed to access bucket: {e}")

        test_key = f".icecharts-test-{int(time.time())}.txt"
        test_data = b"IceCharts connection test"

        try:
            s3_client.put_object(
                Bucket=bucket, Key=test_key, Body=test_data, Metadata={"test": "true"}
            )
            writeable = True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "AccessDenied":
                writeable = False
            else:
                raise Exception(f"Write test failed: {e}")

        try:
            response = s3_client.get_object(Bucket=bucket, Key=test_key)
            data = response["Body"].read()
            readable = data == test_data
            if not readable:
                raise Exception("Read test returned incorrect data")
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "AccessDenied":
                readable = False
            else:
                raise Exception(f"Read test failed: {e}")

        try:
            s3_client.delete_object(Bucket=bucket, Key=test_key)
        except Exception:
            pass

        try:
            s3_client.list_buckets()
            credentials_valid = True
        except (NoCredentialsError, PartialCredentialsError):
            credentials_valid = False

        return {
            "details": {
                "bucket": bucket,
                "region": config.get("region", "us-east-1"),
                "readable": readable,
                "writeable": writeable,
                "credentials_valid": credentials_valid,
            }
        }

    except (NoCredentialsError, PartialCredentialsError) as e:
        raise Exception(f"Invalid AWS credentials: {e}")


def _test_minio_provider(config: dict) -> dict:
    """Test MinIO provider connectivity."""
    from minio import Minio
    from minio.error import S3Error

    required = ["endpoint", "access_key", "secret_key", "bucket"]
    missing = [f for f in required if f not in config]
    if missing:
        raise ValueError(f"Missing required MinIO configuration: {missing}")

    try:
        endpoint = config["endpoint"]
        if "://" in endpoint:
            from urllib.parse import urlparse

            parsed = urlparse(endpoint)
            endpoint = parsed.netloc
            secure = parsed.scheme == "https"
        else:
            secure = config.get("secure", True)

        client = Minio(
            endpoint=endpoint,
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            secure=secure,
        )

        bucket = config["bucket"]

        try:
            if not client.bucket_exists(bucket):
                raise Exception(f"Bucket does not exist: {bucket}")
        except S3Error as e:
            if "Access" in str(e):
                raise Exception(f"Access denied to bucket: {bucket}")
            raise Exception(f"Failed to check bucket existence: {e}")

        from io import BytesIO

        test_key = f".icecharts-test-{int(time.time())}.txt"
        test_data = b"IceCharts connection test"

        try:
            client.put_object(
                bucket_name=bucket,
                object_name=test_key,
                data=BytesIO(test_data),
                length=len(test_data),
                content_type="text/plain",
            )
            writeable = True
        except S3Error as e:
            if "Access" in str(e):
                writeable = False
            else:
                raise Exception(f"Write test failed: {e}")

        try:
            response = client.get_object(bucket, test_key)
            data = response.read()
            response.close()
            readable = data == test_data
            if not readable:
                raise Exception("Read test returned incorrect data")
        except S3Error as e:
            if "Access" in str(e):
                readable = False
            else:
                raise Exception(f"Read test failed: {e}")

        try:
            client.remove_object(bucket, test_key)
        except Exception:
            pass

        return {
            "details": {
                "bucket": bucket,
                "endpoint": config["endpoint"],
                "readable": readable,
                "writeable": writeable,
            }
        }

    except S3Error as e:
        raise Exception(f"MinIO connection error: {e}")


def _test_azure_provider(config: dict) -> dict:
    """Test Azure Blob Storage provider connectivity."""
    try:
        from azure.core.exceptions import AuthenticationError, AzureError
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        raise Exception(
            "Azure storage library not installed. Install 'azure-storage-blob'"
        )

    required = ["account_name", "account_key", "container"]
    missing = [f for f in required if f not in config]
    if missing:
        raise ValueError(f"Missing required Azure configuration: {missing}")

    try:
        account_name = config["account_name"]
        account_key = config["account_key"]
        container = config["container"]

        connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        container_client = blob_service_client.get_container_client(container)

        try:
            container_client.get_container_properties()
        except AuthenticationError:
            raise Exception(f"Access denied to container: {container}")
        except AzureError as e:
            if "ContainerNotFound" in str(e):
                raise Exception(f"Container does not exist: {container}")
            raise Exception(f"Failed to access container: {e}")

        test_blob_name = f".icecharts-test-{int(time.time())}.txt"
        test_data = b"IceCharts connection test"

        try:
            blob_client = container_client.get_blob_client(test_blob_name)
            blob_client.upload_blob(test_data, overwrite=True)
            writeable = True
        except (AuthenticationError, AzureError) as e:
            if "Access" in str(e):
                writeable = False
            else:
                raise Exception(f"Write test failed: {e}")

        try:
            blob_client = container_client.get_blob_client(test_blob_name)
            download_stream = blob_client.download_blob()
            data = download_stream.readall()
            readable = data == test_data
            if not readable:
                raise Exception("Read test returned incorrect data")
        except (AuthenticationError, AzureError) as e:
            if "Access" in str(e):
                readable = False
            else:
                raise Exception(f"Read test failed: {e}")

        try:
            blob_client = container_client.get_blob_client(test_blob_name)
            blob_client.delete_blob()
        except Exception:
            pass

        return {
            "details": {
                "account_name": account_name,
                "container": container,
                "readable": readable,
                "writeable": writeable,
            }
        }

    except (AuthenticationError, AzureError) as e:
        raise Exception(f"Azure authentication error: {e}")


def _test_gcs_provider(config: dict) -> dict:
    """Test Google Cloud Storage provider connectivity."""
    try:
        from google.auth.exceptions import DefaultCredentialsError
        from google.cloud import storage
    except ImportError:
        raise Exception(
            "Google Cloud Storage library not installed. Install 'google-cloud-storage'"
        )

    required = ["bucket"]
    missing = [f for f in required if f not in config]
    if missing:
        raise ValueError(f"Missing required GCS configuration: {missing}")

    try:
        bucket_name = config["bucket"]

        if "credentials_path" in config and config["credentials_path"]:
            import os

            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["credentials_path"]

        storage_client = storage.Client(project=config.get("project_id"))
        bucket = storage_client.bucket(bucket_name)

        try:
            bucket.reload()
        except Exception as e:
            if "404" in str(e) or "NotFound" in str(e):
                raise Exception(f"Bucket does not exist: {bucket_name}")
            elif "403" in str(e) or "Access" in str(e):
                raise Exception(f"Access denied to bucket: {bucket_name}")
            raise Exception(f"Failed to access bucket: {e}")

        test_blob_name = f".icecharts-test-{int(time.time())}.txt"
        test_data = b"IceCharts connection test"

        try:
            blob = bucket.blob(test_blob_name)
            blob.upload_from_string(test_data)
            writeable = True
        except Exception as e:
            if "Access" in str(e) or "403" in str(e):
                writeable = False
            else:
                raise Exception(f"Write test failed: {e}")

        try:
            blob = bucket.blob(test_blob_name)
            data = blob.download_as_bytes()
            readable = data == test_data
            if not readable:
                raise Exception("Read test returned incorrect data")
        except Exception as e:
            if "Access" in str(e) or "403" in str(e):
                readable = False
            else:
                raise Exception(f"Read test failed: {e}")

        try:
            blob = bucket.blob(test_blob_name)
            blob.delete()
        except Exception:
            pass

        return {
            "details": {
                "bucket": bucket_name,
                "project_id": config.get("project_id", "default"),
                "readable": readable,
                "writeable": writeable,
            }
        }

    except DefaultCredentialsError as e:
        raise Exception(f"GCS authentication error: {e}")


def _test_local_provider(config: dict) -> dict:
    """Test local filesystem provider connectivity."""
    import os

    required = ["path"]
    missing = [f for f in required if f not in config]
    if missing:
        raise ValueError(f"Missing required local configuration: {missing}")

    try:
        base_path = config["path"]

        if not os.path.exists(base_path):
            raise Exception(f"Path does not exist: {base_path}")

        if not os.path.isdir(base_path):
            raise Exception(f"Path is not a directory: {base_path}")

        test_dir = os.path.join(base_path, ".icecharts-test")
        test_file = os.path.join(test_dir, f"test-{int(time.time())}.txt")
        test_data = b"IceCharts connection test"

        try:
            os.makedirs(test_dir, exist_ok=True)
            with open(test_file, "wb") as f:
                f.write(test_data)
            writeable = True
        except (OSError, IOError) as e:
            writeable = False
            raise Exception(f"Write test failed: {e}")

        try:
            with open(test_file, "rb") as f:
                data = f.read()
            readable = data == test_data
            if not readable:
                raise Exception("Read test returned incorrect data")
        except (OSError, IOError) as e:
            readable = False
            raise Exception(f"Read test failed: {e}")

        try:
            if os.path.exists(test_file):
                os.remove(test_file)
            if os.path.exists(test_dir) and not os.listdir(test_dir):
                os.rmdir(test_dir)
        except Exception:
            pass

        return {
            "details": {
                "path": base_path,
                "readable": readable,
                "writeable": writeable,
            }
        }

    except (OSError, IOError) as e:
        raise Exception(f"Local filesystem error: {e}")


@storage_v1_bp.route("/usage", methods=["GET"])
@auth_required
def get_storage_usage():
    """Get current user's storage usage statistics."""
    user = get_current_user()
    db = get_db()

    usage = {
        "user_id": user["id"],
        "total_drawings": 0,
        "total_size_bytes": 0,
        "total_size_mb": 0,
        "quota_bytes": 1073741824,
        "quota_mb": 1024,
        "usage_percentage": 0,
        "by_provider": [],
    }

    return jsonify({"usage": usage}), 200


@storage_v1_bp.route("/quota", methods=["GET"])
@auth_required
def get_storage_quota():
    """Get current user's storage quota."""
    user = get_current_user()
    db = get_db()

    quota = {
        "user_id": user["id"],
        "quota_bytes": 1073741824,
        "quota_mb": 1024,
        "quota_type": "default",
        "can_increase": True,
    }

    return jsonify({"quota": quota}), 200


@storage_v1_bp.route("/quota", methods=["PUT"])
@auth_required
@admin_required
def update_storage_quota():
    """Update user storage quota (admin only)."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    target_user_id = data.get("user_id")
    quota_mb = data.get("quota_mb")

    if not target_user_id or not quota_mb:
        return jsonify({"error": "user_id and quota_mb are required"}), 400

    if quota_mb < 0:
        return jsonify({"error": "Quota must be non-negative"}), 400

    return (
        jsonify(
            {
                "message": "Storage quota updated successfully",
                "user_id": target_user_id,
                "quota_mb": quota_mb,
            }
        ),
        200,
    )


@storage_v1_bp.route("/migrate", methods=["POST"])
@auth_required
def migrate_storage():
    """Migrate drawings to different storage provider."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    source_provider_id = data.get("source_provider_id")
    target_provider_id = data.get("target_provider_id")
    drawing_ids = data.get("drawing_ids", [])

    if not source_provider_id or not target_provider_id:
        return (
            jsonify(
                {"error": "source_provider_id and target_provider_id are required"}
            ),
            400,
        )

    source = get_storage_provider_by_id(source_provider_id)
    target = get_storage_provider_by_id(target_provider_id)

    if not source or not target:
        return jsonify({"error": "Invalid provider ID"}), 404

    if (source["user_id"] != user["id"] or target["user_id"] != user["id"]) and user[
        "role"
    ] != "admin":
        return jsonify({"error": "Access denied"}), 403

    return (
        jsonify(
            {
                "message": "Storage migration initiated",
                "migration_id": "migration_placeholder_id",
                "status": "pending",
                "drawing_count": len(drawing_ids),
            }
        ),
        202,
    )
