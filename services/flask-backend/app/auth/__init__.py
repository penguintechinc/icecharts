"""Authentication and SSO handlers."""

import bcrypt

# Lazy import SAML handlers to avoid xmlsec dependency issues during development
# SAML/OIDC are enterprise features gated by license server
try:
    from .saml_handler import SAMLConfig, SAMLHandler
except (ImportError, Exception):
    SAMLConfig = None
    SAMLHandler = None

try:
    from .oidc_handler import OIDCConfig, OIDCHandler
except (ImportError, Exception):
    OIDCConfig = None
    OIDCHandler = None

try:
    from .jit_provisioning import AttributeMapping, JITConfig, JITProvisioner
except (ImportError, Exception):
    AttributeMapping = None
    JITConfig = None
    JITProvisioner = None


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


__all__ = [
    'SAMLConfig',
    'SAMLHandler',
    'OIDCConfig',
    'OIDCHandler',
    'AttributeMapping',
    'JITConfig',
    'JITProvisioner',
    'hash_password',
    'verify_password',
]
