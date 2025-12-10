"""Authentication and SSO handlers."""

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

__all__ = [
    'SAMLConfig',
    'SAMLHandler',
    'OIDCConfig',
    'OIDCHandler',
    'AttributeMapping',
    'JITConfig',
    'JITProvisioner',
]
