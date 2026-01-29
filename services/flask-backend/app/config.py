"""Configuration management for IceCharts application."""

import os
from datetime import timedelta
from typing import Any

from decouple import config


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = config("SECRET_KEY", default="dev-secret-key-change-in-production")
    DEBUG = config("DEBUG", default=False, cast=bool)
    TESTING = config("TESTING", default=False, cast=bool)

    # Application
    APP_NAME = "IceCharts"
    APP_VERSION = config("APP_VERSION", default="0.2.0")

    # Database (PyDAL - use individual components or DATABASE_URL)
    DATABASE_URL = config("DATABASE_URL", default=None)
    DB_TYPE = config("DB_TYPE", default="postgres")
    DB_HOST = config("DB_HOST", default="localhost")
    DB_PORT = config("DB_PORT", default=5432, cast=int)
    DB_NAME = config("DB_NAME", default="icecharts")
    DB_USER = config("DB_USER", default="icecharts")
    DB_PASSWORD = config("DB_PASSWORD", default="icecharts")
    DB_POOL_SIZE = config("DB_POOL_SIZE", default=10, cast=int)

    # Redis
    REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")
    REDIS_PASSWORD = config("REDIS_PASSWORD", default=None)
    REDIS_SSL = config("REDIS_SSL", default=False, cast=bool)

    # Session
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "icecharts:session:"

    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    BCRYPT_LOG_ROUNDS = 12

    # JWT
    JWT_SECRET_KEY = config("JWT_SECRET_KEY", default=None)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=config("JWT_ACCESS_TOKEN_HOURS", default=4, cast=int)
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=config("JWT_REFRESH_TOKEN_DAYS", default=30, cast=int)
    )
    JWT_ALGORITHM = "HS256"

    # CORS
    SITE_URL = config("SITE_URL", default="http://localhost:3000")

    @staticmethod
    def _build_cors_origins():
        from urllib.parse import urlparse

        site_url = config("SITE_URL", default="http://localhost:3000")
        parsed = urlparse(site_url)
        scheme = parsed.scheme or "http"
        hostname = parsed.hostname or "localhost"
        port = parsed.port

        origins = []
        if port:
            origins.append(f"{scheme}://{hostname}:{port}")
        else:
            origins.append(f"{scheme}://{hostname}")

        if hostname in ("localhost", "127.0.0.1"):
            for dev_port in [3000, 3001, 3002, 3003, 3005, 5001, 5173, 8080]:
                origin = f"{scheme}://{hostname}:{dev_port}"
                if origin not in origins:
                    origins.append(origin)

        return origins

    CORS_ORIGINS = _build_cors_origins.__func__()
    CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = [
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ]
    CORS_SUPPORTS_CREDENTIALS = True

    # Rate Limiting
    RATELIMIT_ENABLED = config("RATELIMIT_ENABLED", default=True, cast=bool)
    RATELIMIT_DEFAULT = config("RATELIMIT_DEFAULT", default="100/hour")
    RATELIMIT_STORAGE_URL = REDIS_URL

    # Service Account Rate Limiting
    RATELIMIT_SERVICE_ACCOUNT_DEFAULT = config(
        "RATELIMIT_SERVICE_ACCOUNT_DEFAULT", default="1000/hour"
    )
    RATELIMIT_SERVICE_ACCOUNT_ENABLED = config(
        "RATELIMIT_SERVICE_ACCOUNT_ENABLED", default=True, cast=bool
    )

    # Service Account Token Settings
    SERVICE_ACCOUNT_TOKEN_MAX_DAYS = config(
        "SERVICE_ACCOUNT_TOKEN_MAX_DAYS", default=365, cast=int
    )  # Maximum token lifetime in days

    # License Server
    LICENSE_KEY = config("LICENSE_KEY", default=None)
    LICENSE_SERVER_URL = config(
        "LICENSE_SERVER_URL", default="https://license.penguintech.io"
    )
    PRODUCT_NAME = "icecharts"
    RELEASE_MODE = config("RELEASE_MODE", default=False, cast=bool)

    # Logging
    LOG_LEVEL = config("LOG_LEVEL", default="INFO")
    LOG_FORMAT = config("LOG_FORMAT", default="json")

    # Metrics
    METRICS_ENABLED = config("METRICS_ENABLED", default=True, cast=bool)

    # API
    API_PREFIX = "/api/v1"
    API_PAGINATION_DEFAULT = config("API_PAGINATION_DEFAULT", default=50, cast=int)
    API_PAGINATION_MAX = config("API_PAGINATION_MAX", default=1000, cast=int)

    # SocketIO
    SOCKETIO_ENABLED = config("SOCKETIO_ENABLED", default=True, cast=bool)
    SOCKETIO_MESSAGE_QUEUE = REDIS_URL
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS

    # Storage
    STORAGE_BACKEND = config("STORAGE_BACKEND", default="local")
    STORAGE_LOCAL_PATH = config("STORAGE_LOCAL_PATH", default="./storage")
    STORAGE_S3_BUCKET = config("STORAGE_S3_BUCKET", default=None)
    STORAGE_S3_REGION = config("STORAGE_S3_REGION", default="us-east-1")

    # Google OAuth2
    GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
    GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="")
    GOOGLE_REDIRECT_URI = config("GOOGLE_REDIRECT_URI", default="")

    # Email Configuration
    EMAIL_PROVIDER = config("EMAIL_PROVIDER", default="smtp")  # smtp, sendgrid, ses, mailgun, gmail
    EMAIL_FROM = config("EMAIL_FROM", default="noreply@icecharts.local")
    EMAIL_FROM_NAME = config("EMAIL_FROM_NAME", default="IceCharts")

    # SMTP Settings
    SMTP_HOST = config("SMTP_HOST", default="localhost")
    SMTP_PORT = config("SMTP_PORT", default=587, cast=int)
    SMTP_USER = config("SMTP_USER", default="")
    SMTP_PASSWORD = config("SMTP_PASSWORD", default="")
    SMTP_USE_TLS = config("SMTP_USE_TLS", default=True, cast=bool)

    # SendGrid Settings
    SENDGRID_API_KEY = config("SENDGRID_API_KEY", default="")

    # AWS SES Settings
    AWS_SES_REGION = config("AWS_SES_REGION", default="us-east-1")
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")

    # Mailgun Settings
    MAILGUN_API_KEY = config("MAILGUN_API_KEY", default="")
    MAILGUN_DOMAIN = config("MAILGUN_DOMAIN", default="")

    # Gmail Settings
    GMAIL_USER = config("GMAIL_USER", default="")
    GMAIL_APP_PASSWORD = config("GMAIL_APP_PASSWORD", default="")

    # Celery Settings
    CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL)
    CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=REDIS_URL)
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TIMEZONE = "UTC"
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

    @staticmethod
    def init_app(app: Any) -> None:
        """Initialize application with configuration."""
        pass


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    BCRYPT_LOG_ROUNDS = 13


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    DB_TYPE = "sqlite"
    DATABASE_URL = "sqlite:memory"
    DB_POOL_SIZE = 0
    RATELIMIT_ENABLED = False
    JWT_SECRET_KEY = "test-secret-key-for-pytest"
    LICENSE_KEY = "PENG-TEST-TEST-TEST-TEST-TEST"
    SOCKETIO_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str = None) -> type:
    """Get configuration by name."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    return config_by_name.get(config_name, DevelopmentConfig)
