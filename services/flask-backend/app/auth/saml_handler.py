"""SAML 2.0 handler for enterprise SSO integration."""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from flask import current_app

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
except ImportError:
    # python3-saml not installed, will raise error when used
    OneLogin_Saml2_Auth = None
    OneLogin_Saml2_Utils = None


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SAMLConfig:
    """SAML 2.0 configuration."""

    idp_name: str
    idp_entity_id: str
    sso_url: str
    slo_url: Optional[str]
    x509_cert: str
    name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    assertion_consumer_service_url: Optional[str] = None
    metadata_url: Optional[str] = None

    @classmethod
    def from_metadata_url(cls, metadata_url: str) -> "SAMLConfig":
        """Load SAML configuration from metadata URL."""
        logger.info(f"Loading SAML metadata from {metadata_url}")
        try:
            response = requests.get(metadata_url, timeout=10)
            response.raise_for_status()
            return cls.from_metadata_xml(response.text, metadata_url)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch SAML metadata: {e}")
            raise ValueError(f"Could not fetch SAML metadata: {e}")

    @classmethod
    def from_metadata_xml(
        cls, metadata_xml: str, metadata_url: Optional[str] = None
    ) -> "SAMLConfig":
        """Parse SAML metadata XML."""
        try:
            root = ET.fromstring(metadata_xml)

            # Extract entity ID
            entity_id = root.get("entityID")
            if not entity_id:
                raise ValueError("EntityDescriptor missing entityID")

            # Extract SSO URL and certificate
            sso_url = None
            slo_url = None
            x509_cert = None

            namespaces = {
                "md": "urn:oasis:names:tc:SAML:2.0:metadata",
                "ds": "http://www.w3.org/2000/09/xmldsig#",
            }

            # Find SingleSignOnService
            sso_element = root.find(
                './/md:SingleSignOnService[@Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"]',
                namespaces,
            )
            if sso_element is not None:
                sso_url = sso_element.get("Location")

            # Find SingleLogoutService
            slo_element = root.find(
                './/md:SingleLogoutService[@Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"]',
                namespaces,
            )
            if slo_element is not None:
                slo_url = slo_element.get("Location")

            # Extract X.509 certificate
            cert_element = root.find(".//ds:X509Certificate", namespaces)
            if cert_element is not None:
                x509_cert = cert_element.text

            if not sso_url:
                raise ValueError("Could not find SingleSignOnService in metadata")
            if not x509_cert:
                raise ValueError("Could not find X.509 certificate in metadata")

            return cls(
                idp_name=entity_id.split("/")[-1],
                idp_entity_id=entity_id,
                sso_url=sso_url,
                slo_url=slo_url,
                x509_cert=x509_cert,
                metadata_url=metadata_url,
            )
        except ET.ParseError as e:
            logger.error(f"Failed to parse SAML metadata XML: {e}")
            raise ValueError(f"Invalid SAML metadata XML: {e}")


class SAMLHandler:
    """SAML 2.0 authentication handler."""

    def __init__(
        self, saml_config: SAMLConfig, sp_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize SAML handler.

        Args:
            saml_config: SAML IdP configuration
            sp_config: Optional custom SP configuration
        """
        if OneLogin_Saml2_Auth is None:
            raise ImportError(
                "python3-saml is not installed. "
                "Install with: pip install python3-saml"
            )

        self.saml_config = saml_config
        self.sp_config = sp_config or self._build_default_sp_config()

    def _build_default_sp_config(self) -> Dict[str, Any]:
        """Build default SP configuration."""
        site_url = current_app.config.get("SITE_URL", "http://localhost:3000")
        api_url = current_app.config.get("API_URL", "http://localhost:5000")

        acs_url = f"{api_url}/api/v1/sso/saml/acs"
        sls_url = f"{api_url}/api/v1/sso/saml/sls"

        return {
            "sp": {
                "entityID": f"{api_url}/api/v1/sso/saml/metadata",
                "assertionConsumerService": {
                    "url": acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": sls_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": "",
                "privateKey": "",
            },
            "idp": {
                "entityID": self.saml_config.idp_entity_id,
                "singleSignOnService": {
                    "url": self.saml_config.sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "singleLogoutService": {
                    "url": self.saml_config.slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": self.saml_config.x509_cert,
            },
            "security": {
                "nameIdEncrypted": False,
                "authnRequestsSigned": False,
                "wantAssertionsSigned": True,
                "wantAssertionsEncrypted": False,
                "wantNameIdEncrypted": False,
                "signMetadata": False,
                "wantAttributeStatement": True,
                "requestedAuthnContext": False,
            },
        }

    def create_saml_request(self) -> str:
        """Generate SAML AuthnRequest and return login URL.

        Returns:
            Redirect URL for IdP login
        """
        auth = OneLogin_Saml2_Auth({}, self.sp_config)
        return auth.login()

    def parse_saml_response(
        self, saml_response: str, relay_state: Optional[str] = None
    ) -> bool:
        """Parse and validate SAML response.

        Args:
            saml_response: Base64-encoded SAML response from IdP
            relay_state: Optional relay state for validation

        Returns:
            True if response is valid and authenticated

        Raises:
            ValueError: If SAML response is invalid
        """
        request_data = {
            "http_host": current_app.config.get("SERVER_NAME", "localhost"),
            "script_name": "/api/v1/sso/saml/acs",
            "get_data": {},
            "post_data": {"SAMLResponse": saml_response},
        }

        if relay_state:
            request_data["post_data"]["RelayState"] = relay_state

        auth = OneLogin_Saml2_Auth(request_data, self.sp_config)
        auth.process_response()

        if not auth.is_authenticated():
            errors = auth.get_last_error_reason()
            logger.error(f"SAML authentication failed: {errors}")
            raise ValueError(f"SAML response validation failed: {errors}")

        return True

    def get_saml_user(self, saml_response: str) -> Dict[str, Any]:
        """Extract user information from SAML response.

        Args:
            saml_response: Base64-encoded SAML response from IdP

        Returns:
            Dictionary with user attributes (email, name, etc.)

        Raises:
            ValueError: If response parsing fails
        """
        request_data = {
            "http_host": current_app.config.get("SERVER_NAME", "localhost"),
            "script_name": "/api/v1/sso/saml/acs",
            "get_data": {},
            "post_data": {"SAMLResponse": saml_response},
        }

        auth = OneLogin_Saml2_Auth(request_data, self.sp_config)
        auth.process_response()

        if not auth.is_authenticated():
            raise ValueError("SAML response is not authenticated")

        attributes = auth.get_attributes()
        name_id = auth.get_nameid()
        session_index = auth.get_session_index()

        return {
            "name_id": name_id,
            "session_index": session_index,
            "attributes": attributes,
            "email": self._extract_email(attributes, name_id),
            "name": self._extract_name(attributes),
            "groups": self._extract_groups(attributes),
        }

    def _extract_email(self, attributes: Dict[str, List[str]], name_id: str) -> str:
        """Extract email from SAML attributes."""
        # Common email attribute names
        email_attrs = [
            "email",
            "emailAddress",
            "mail",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        ]

        for attr in email_attrs:
            if attr in attributes and attributes[attr]:
                return attributes[attr][0].lower()

        # Fallback to name_id if it looks like email
        if name_id and "@" in name_id:
            return name_id.lower()

        raise ValueError("Could not extract email from SAML response")

    def _extract_name(self, attributes: Dict[str, List[str]]) -> str:
        """Extract full name from SAML attributes."""
        # Common name attribute names
        name_attrs = [
            "displayName",
            "cn",
            "commonName",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
        ]

        for attr in name_attrs:
            if attr in attributes and attributes[attr]:
                return attributes[attr][0]

        return ""

    def _extract_groups(self, attributes: Dict[str, List[str]]) -> List[str]:
        """Extract groups/roles from SAML attributes."""
        # Common group attribute names
        group_attrs = [
            "groups",
            "memberOf",
            "roles",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/groups",
        ]

        groups = []
        for attr in group_attrs:
            if attr in attributes and attributes[attr]:
                groups.extend(attributes[attr])

        return groups

    def get_metadata(self) -> str:
        """Generate SP metadata XML.

        Returns:
            SP metadata XML string
        """
        auth = OneLogin_Saml2_Auth({}, self.sp_config)
        return auth.get_settings().get_sp_metadata()

    def validate_saml_signature(self, saml_response: str) -> bool:
        """Validate SAML response signature.

        Args:
            saml_response: Base64-encoded SAML response

        Returns:
            True if signature is valid
        """
        request_data = {
            "http_host": current_app.config.get("SERVER_NAME", "localhost"),
            "script_name": "/api/v1/sso/saml/acs",
            "get_data": {},
            "post_data": {"SAMLResponse": saml_response},
        }

        auth = OneLogin_Saml2_Auth(request_data, self.sp_config)
        auth.process_response()

        # Check if response is signed and valid
        if not auth.get_last_error_reason():
            return True

        return False


__all__ = [
    "SAMLConfig",
    "SAMLHandler",
]
