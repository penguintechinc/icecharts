"""OpenID Connect (OIDC) handler for enterprise SSO integration."""

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlencode, parse_qs, urlparse

import requests
import jwt
from flask import current_app

try:
    from authlib.integrations.flask_client import OAuth2Session
except ImportError:
    OAuth2Session = None

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OIDCConfig:
    """OpenID Connect configuration."""
    issuer: str
    client_id: str
    client_secret: str
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    scopes: tuple = ('openid', 'profile', 'email')

    @classmethod
    def from_discovery(cls, issuer: str, client_id: str, client_secret: str) -> "OIDCConfig":
        """Load OIDC configuration from issuer's discovery endpoint.

        Args:
            issuer: OIDC issuer URL (e.g., https://accounts.google.com)
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret

        Returns:
            OIDCConfig instance with discovered endpoints

        Raises:
            ValueError: If discovery fails or required endpoints missing
        """
        logger.info(f"Discovering OIDC configuration from {issuer}")

        # Normalize issuer URL
        issuer = issuer.rstrip('/')

        try:
            # Fetch well-known discovery document
            discovery_url = f"{issuer}/.well-known/openid-configuration"
            response = requests.get(discovery_url, timeout=10)
            response.raise_for_status()

            discovery = response.json()

            # Validate required endpoints
            required_endpoints = [
                'authorization_endpoint',
                'token_endpoint',
                'userinfo_endpoint',
            ]

            for endpoint in required_endpoints:
                if endpoint not in discovery:
                    raise ValueError(f"Missing required endpoint: {endpoint}")

            return cls(
                issuer=issuer,
                client_id=client_id,
                client_secret=client_secret,
                authorization_endpoint=discovery['authorization_endpoint'],
                token_endpoint=discovery['token_endpoint'],
                userinfo_endpoint=discovery['userinfo_endpoint'],
                jwks_uri=discovery.get('jwks_uri'),
                scopes=tuple(discovery.get('scopes_supported', ['openid', 'profile', 'email']))
            )
        except requests.RequestException as e:
            logger.error(f"Failed to discover OIDC configuration: {e}")
            raise ValueError(f"Could not discover OIDC configuration: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid OIDC discovery response: {e}")
            raise ValueError(f"Invalid OIDC configuration: {e}")


class OIDCHandler:
    """OpenID Connect authentication handler with PKCE support."""

    def __init__(self, oidc_config: OIDCConfig):
        """Initialize OIDC handler.

        Args:
            oidc_config: OIDC configuration
        """
        self.oidc_config = oidc_config
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_time: Optional[float] = None

    def generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code challenge and verifier.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge_b64 = (
            __import__('base64').urlsafe_b64encode(code_challenge)
            .decode()
            .rstrip('=')
        )
        return code_verifier, code_challenge_b64

    def build_authorization_url(
        self,
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        additional_params: Optional[Dict[str, str]] = None
    ) -> str:
        """Build authorization URL with PKCE.

        Args:
            state: State parameter for CSRF protection (auto-generated if not provided)
            code_challenge: PKCE code challenge
            additional_params: Additional query parameters

        Returns:
            Authorization URL to redirect user to
        """
        if not state:
            state = secrets.token_urlsafe(16)

        params = {
            'client_id': self.oidc_config.client_id,
            'response_type': 'code',
            'scope': ' '.join(self.oidc_config.scopes),
            'redirect_uri': self._get_callback_url(),
            'state': state,
        }

        if code_challenge:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = 'S256'

        if additional_params:
            params.update(additional_params)

        auth_url = self.oidc_config.authorization_endpoint
        return f"{auth_url}?{urlencode(params)}"

    def exchange_code_for_token(
        self,
        code: str,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback
            code_verifier: PKCE code verifier (required if PKCE was used)

        Returns:
            Token response with access_token, id_token, etc.

        Raises:
            ValueError: If token exchange fails
        """
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.oidc_config.client_id,
            'client_secret': self.oidc_config.client_secret,
            'redirect_uri': self._get_callback_url(),
        }

        if code_verifier:
            data['code_verifier'] = code_verifier

        try:
            response = requests.post(
                self.oidc_config.token_endpoint,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            raise ValueError(f"Failed to exchange code for token: {e}")

    def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        """Fetch user information using access token.

        Args:
            access_token: OAuth2 access token

        Returns:
            User information from userinfo endpoint
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        try:
            response = requests.get(
                self.oidc_config.userinfo_endpoint,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Userinfo request failed: {e}")
            raise ValueError(f"Failed to fetch userinfo: {e}")

    def validate_id_token(
        self,
        id_token: str,
        nonce: Optional[str] = None,
        audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate and decode ID token JWT.

        Args:
            id_token: ID token JWT
            nonce: Optional nonce for validation
            audience: Expected audience (defaults to client_id)

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is invalid
        """
        if not audience:
            audience = self.oidc_config.client_id

        try:
            # Try to decode without verification first to get headers
            unverified = jwt.decode(id_token, options={"verify_signature": False})

            # Fetch JWKS if not cached
            if not self._jwks_cache:
                self._fetch_jwks()

            # Get the key ID from token header
            token_header = jwt.get_unverified_header(id_token)
            kid = token_header.get('kid')

            if not kid:
                raise ValueError("ID token missing 'kid' header")

            # Find the key in JWKS
            key = self._find_key_in_jwks(kid)
            if not key:
                raise ValueError(f"Key with id '{kid}' not found in JWKS")

            # Convert JWK to PEM
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend
            import base64

            if key['kty'] != 'RSA':
                raise ValueError(f"Unsupported key type: {key['kty']}")

            # Reconstruct RSA public key from JWK
            n = base64.urlsafe_b64decode(key['n'] + '==')
            e = base64.urlsafe_b64decode(key['e'] + '==')

            n_int = int.from_bytes(n, 'big')
            e_int = int.from_bytes(e, 'big')

            public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key(default_backend())

            # Verify and decode token
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=audience,
                options={'verify_aud': True}
            )

            # Verify nonce if provided
            if nonce and payload.get('nonce') != nonce:
                raise ValueError("ID token nonce mismatch")

            return payload

        except jwt.DecodeError as e:
            logger.error(f"ID token decode failed: {e}")
            raise ValueError(f"Invalid ID token: {e}")
        except jwt.InvalidTokenError as e:
            logger.error(f"ID token validation failed: {e}")
            raise ValueError(f"ID token validation failed: {e}")

    def _fetch_jwks(self) -> None:
        """Fetch and cache JWKS from issuer."""
        if not self.oidc_config.jwks_uri:
            raise ValueError("JWKS URI not available")

        try:
            response = requests.get(
                self.oidc_config.jwks_uri,
                timeout=10
            )
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_cache_time = datetime.utcnow().timestamp()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise ValueError(f"Failed to fetch JWKS: {e}")

    def _find_key_in_jwks(self, kid: str) -> Optional[Dict[str, Any]]:
        """Find key in JWKS by key ID."""
        if not self._jwks_cache:
            return None

        for key in self._jwks_cache.get('keys', []):
            if key.get('kid') == kid:
                return key

        return None

    def _get_callback_url(self) -> str:
        """Get OIDC callback URL."""
        api_url = current_app.config.get('API_URL', 'http://localhost:5000')
        return f"{api_url}/api/v1/sso/oidc/callback"


__all__ = [
    'OIDCConfig',
    'OIDCHandler',
]
