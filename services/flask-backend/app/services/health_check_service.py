"""System health check service for monitoring component health and status."""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import redis

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for performing health checks on all system components."""

    def __init__(self):
        """Initialize health check service."""
        self.start_time = time.time()

    def check_all(self) -> Dict[str, Any]:
        """
        Perform health checks on all system components.

        Returns:
            Dictionary containing overall health status and component details
        """
        timestamp = datetime.utcnow()
        components = {}
        component_status = []

        # Check database
        db_health = self._check_database()
        components["database"] = db_health
        component_status.append(db_health["status"])

        # Check Redis
        redis_health = self._check_redis()
        components["redis"] = redis_health
        component_status.append(redis_health["status"])

        # Check storage
        storage_health = self._check_storage()
        components["storage"] = storage_health
        component_status.append(storage_health["status"])

        # Check API service
        api_health = self._check_api_service()
        components["api"] = api_health
        component_status.append(api_health["status"])

        # Check system resources
        system_health = self._check_system_resources()
        components["system"] = system_health
        component_status.append(system_health["status"])

        # Determine overall status
        overall_status = self._determine_overall_status(component_status)

        return {
            "status": overall_status,
            "timestamp": timestamp.isoformat(),
            "uptime_seconds": int(time.time() - self.start_time),
            "components": components,
        }

    def _check_database(self) -> Dict[str, Any]:
        """
        Check PostgreSQL database connectivity and health.

        Returns:
            Dictionary with database health status
        """
        start_time = time.time()
        try:
            from flask import current_app

            from app.models import get_db

            db = get_db()

            # Execute a simple query to test connectivity
            result = db.executesql("SELECT 1")

            response_time_ms = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "message": "Database connection OK",
                "response_time_ms": round(response_time_ms, 2),
                "type": "postgresql",
                "details": {
                    "host": current_app.config.get("DB_HOST", "unknown"),
                    "port": current_app.config.get("DB_PORT", "unknown"),
                    "database": current_app.config.get("DB_NAME", "unknown"),
                },
            }
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "response_time_ms": round(response_time_ms, 2),
                "error": str(e),
            }

    def _check_redis(self) -> Dict[str, Any]:
        """
        Check Redis connectivity and health.

        Returns:
            Dictionary with Redis health status
        """
        start_time = time.time()
        try:
            from flask import current_app

            redis_url = current_app.config.get("REDIS_URL")
            if not redis_url:
                return {
                    "status": "unknown",
                    "message": "Redis not configured",
                    "response_time_ms": 0,
                }

            # Create Redis connection
            r = redis.from_url(redis_url, decode_responses=True)

            # Test connection with PING
            pong = r.ping()

            response_time_ms = (time.time() - start_time) * 1000

            if pong:
                # Get Redis info
                info = r.info()
                return {
                    "status": "healthy",
                    "message": "Redis connection OK",
                    "response_time_ms": round(response_time_ms, 2),
                    "details": {
                        "version": info.get("redis_version", "unknown"),
                        "connected_clients": info.get("connected_clients", 0),
                        "memory_usage_mb": round(
                            info.get("used_memory", 0) / (1024 * 1024), 2
                        ),
                        "uptime_seconds": info.get("uptime_in_seconds", 0),
                    },
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Redis PING failed",
                    "response_time_ms": round(response_time_ms, 2),
                }
        except redis.ConnectionError as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Cannot connect to Redis: {str(e)}",
                "response_time_ms": round(response_time_ms, 2),
                "error": str(e),
            }
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check error: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Redis check failed: {str(e)}",
                "response_time_ms": round(response_time_ms, 2),
                "error": str(e),
            }

    def _check_storage(self) -> Dict[str, Any]:
        """
        Check MinIO/S3 storage connectivity and basic operations.

        Returns:
            Dictionary with storage health status
        """
        start_time = time.time()
        try:
            from flask import current_app

            from app.models import get_db

            db = get_db()

            # Get active storage providers from database
            storage_configs = db(
                (db.storage_providers.is_active == True)
                & (db.storage_providers.is_system_default == True)
            ).select()

            response_time_ms = (time.time() - start_time) * 1000

            if not storage_configs:
                return {
                    "status": "unknown",
                    "message": "No active storage providers configured",
                    "response_time_ms": round(response_time_ms, 2),
                }

            providers_status = []
            all_healthy = True

            for config in storage_configs:
                provider_health = self._check_storage_provider(config)
                providers_status.append(provider_health)
                if provider_health["status"] != "healthy":
                    all_healthy = False

            overall_status = "healthy" if all_healthy else "degraded"

            return {
                "status": overall_status,
                "message": f"{len(providers_status)} storage provider(s) configured",
                "response_time_ms": round(response_time_ms, 2),
                "providers": providers_status,
            }
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Storage health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Storage check failed: {str(e)}",
                "response_time_ms": round(response_time_ms, 2),
                "error": str(e),
            }

    def _check_storage_provider(self, config) -> Dict[str, Any]:
        """
        Check individual storage provider health.

        Args:
            config: Storage provider configuration record

        Returns:
            Dictionary with provider health status
        """
        provider_type = config.provider_type
        name = config.name
        start_time = time.time()

        try:
            if provider_type == "s3":
                return self._check_s3_storage(config, start_time)
            elif provider_type == "minio":
                return self._check_minio_storage(config, start_time)
            elif provider_type == "gdrive":
                return {
                    "provider": name,
                    "type": provider_type,
                    "status": "configured",
                    "message": "Google Drive configured (OAuth-based)",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                }
            elif provider_type == "onedrive":
                return {
                    "provider": name,
                    "type": provider_type,
                    "status": "configured",
                    "message": "OneDrive configured (OAuth-based)",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                }
            else:
                return {
                    "provider": name,
                    "type": provider_type,
                    "status": "unknown",
                    "message": f"Unknown provider type: {provider_type}",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                }
        except Exception as e:
            logger.error(f"Storage provider {name} health check failed: {str(e)}")
            return {
                "provider": name,
                "type": provider_type,
                "status": "unhealthy",
                "message": f"Provider check failed: {str(e)}",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
            }

    def _check_s3_storage(self, config, start_time) -> Dict[str, Any]:
        """Check AWS S3 storage connectivity."""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            config_json = config.config_json or {}
            bucket = config_json.get("bucket")
            region = config_json.get("region", "us-east-1")
            endpoint = config_json.get("endpoint")

            if not bucket:
                return {
                    "provider": config.name,
                    "type": "s3",
                    "status": "unhealthy",
                    "message": "S3 bucket not configured",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Create S3 client
            kwargs = {
                "region_name": region,
                "aws_access_key_id": config_json.get("access_key"),
                "aws_secret_access_key": config_json.get("secret_key"),
            }

            if endpoint:
                kwargs["endpoint_url"] = endpoint

            s3_client = boto3.client("s3", **kwargs)

            # Try to list buckets as a connectivity test
            s3_client.head_bucket(Bucket=bucket)

            return {
                "provider": config.name,
                "type": "s3",
                "status": "healthy",
                "message": "S3 bucket accessible",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "details": {
                    "bucket": bucket,
                    "region": region,
                },
            }
        except NoCredentialsError:
            return {
                "provider": config.name,
                "type": "s3",
                "status": "unhealthy",
                "message": "S3 credentials not found",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
            }
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            return {
                "provider": config.name,
                "type": "s3",
                "status": "unhealthy",
                "message": f"S3 error: {error_code}",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
            }

    def _check_minio_storage(self, config, start_time) -> Dict[str, Any]:
        """Check MinIO storage connectivity."""
        try:
            from minio import Minio
            from minio.error import S3Error

            config_json = config.config_json or {}
            endpoint = config_json.get("endpoint")
            access_key = config_json.get("access_key")
            secret_key = config_json.get("secret_key")
            bucket = config_json.get("bucket")
            secure = config_json.get("secure", True)

            if not all([endpoint, bucket]):
                return {
                    "provider": config.name,
                    "type": "minio",
                    "status": "unhealthy",
                    "message": "MinIO endpoint or bucket not configured",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Create MinIO client
            minio_client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )

            # Try to check if bucket exists
            exists = minio_client.bucket_exists(bucket)

            if exists:
                return {
                    "provider": config.name,
                    "type": "minio",
                    "status": "healthy",
                    "message": "MinIO bucket accessible",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "details": {
                        "endpoint": endpoint,
                        "bucket": bucket,
                    },
                }
            else:
                return {
                    "provider": config.name,
                    "type": "minio",
                    "status": "unhealthy",
                    "message": f"MinIO bucket '{bucket}' does not exist",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                }
        except ImportError:
            return {
                "provider": config.name,
                "type": "minio",
                "status": "unknown",
                "message": "MinIO client library not installed",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
            }
        except Exception as e:
            return {
                "provider": config.name,
                "type": "minio",
                "status": "unhealthy",
                "message": f"MinIO check failed: {str(e)}",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
            }

    def _check_api_service(self) -> Dict[str, Any]:
        """
        Check API service status.

        Returns:
            Dictionary with API service health status
        """
        try:
            from flask import current_app

            return {
                "status": "healthy",
                "message": "API service operational",
                "response_time_ms": 0,
                "details": {
                    "version": current_app.config.get("APP_VERSION", "unknown"),
                    "environment": current_app.config.get("ENV", "unknown"),
                    "debug": current_app.config.get("DEBUG", False),
                },
            }
        except Exception as e:
            logger.error(f"API service check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"API service check failed: {str(e)}",
                "response_time_ms": 0,
                "error": str(e),
            }

    def _check_system_resources(self) -> Dict[str, Any]:
        """
        Check system resource usage (memory, disk, CPU).

        Returns:
            Dictionary with system resource information
        """
        try:
            import os

            import psutil

            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_status = (
                "healthy"
                if memory_percent < 80
                else ("degraded" if memory_percent < 95 else "unhealthy")
            )

            # Disk
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_status = (
                "healthy"
                if disk_percent < 80
                else ("degraded" if disk_percent < 95 else "unhealthy")
            )

            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Determine overall system status
            overall_status = "healthy"
            if memory_status == "unhealthy" or disk_status == "unhealthy":
                overall_status = "unhealthy"
            elif memory_status == "degraded" or disk_status == "degraded":
                overall_status = "degraded"

            return {
                "status": overall_status,
                "message": f"System resources: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%",
                "response_time_ms": 0,
                "details": {
                    "cpu": {
                        "usage_percent": round(cpu_percent, 2),
                        "count": cpu_count,
                    },
                    "memory": {
                        "usage_percent": round(memory_percent, 2),
                        "total_gb": round(memory.total / (1024**3), 2),
                        "available_gb": round(memory.available / (1024**3), 2),
                        "used_gb": round(memory.used / (1024**3), 2),
                        "status": memory_status,
                    },
                    "disk": {
                        "usage_percent": round(disk_percent, 2),
                        "total_gb": round(disk.total / (1024**3), 2),
                        "used_gb": round(disk.used / (1024**3), 2),
                        "free_gb": round(disk.free / (1024**3), 2),
                        "status": disk_status,
                    },
                },
            }
        except ImportError:
            return {
                "status": "unknown",
                "message": "psutil library not installed for system monitoring",
                "response_time_ms": 0,
            }
        except Exception as e:
            logger.warning(f"System resource check failed: {str(e)}")
            return {
                "status": "unknown",
                "message": f"System check failed: {str(e)}",
                "response_time_ms": 0,
                "error": str(e),
            }

    @staticmethod
    def _determine_overall_status(component_statuses: list) -> str:
        """
        Determine overall system status based on component statuses.

        Args:
            component_statuses: List of component status strings

        Returns:
            Overall status string (healthy, degraded, or unhealthy)
        """
        unhealthy_count = sum(1 for s in component_statuses if s == "unhealthy")
        degraded_count = sum(1 for s in component_statuses if s == "degraded")

        # If any critical component is unhealthy, system is unhealthy
        if unhealthy_count > 0:
            return "unhealthy"
        # If multiple components are degraded, system is degraded
        elif degraded_count > 1:
            return "degraded"
        # If one component is degraded, system is degraded
        elif degraded_count == 1:
            return "degraded"
        # Otherwise, system is healthy
        else:
            return "healthy"
