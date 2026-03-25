"""Just-In-Time (JIT) user provisioning for SSO."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .oidc_handler import OIDCConfig
from .saml_handler import SAMLConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AttributeMapping:
    """SAML/OIDC attribute to user field mapping."""

    email_field: str = "email"
    name_field: str = "name"
    groups_field: Optional[str] = None
    custom_fields: Dict[str, str] = None

    def __post_init__(self):
        """Initialize custom_fields if None."""
        if self.custom_fields is None:
            self.custom_fields = {}


@dataclass(slots=True)
class JITConfig:
    """JIT provisioning configuration."""

    enabled: bool = True
    auto_assign_role: str = "viewer"
    attribute_mapping: AttributeMapping = None
    group_role_mapping: Dict[str, str] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.attribute_mapping is None:
            self.attribute_mapping = AttributeMapping()
        if self.group_role_mapping is None:
            self.group_role_mapping = {}


class JITProvisioner:
    """Just-In-Time user provisioning handler."""

    def __init__(self, jit_config: JITConfig):
        """Initialize JIT provisioner.

        Args:
            jit_config: JIT configuration
        """
        self.config = jit_config

    def get_or_create_saml_user(
        self, saml_attributes: Dict[str, Any], saml_config: SAMLConfig
    ) -> Dict[str, Any]:
        """Get or create user from SAML attributes.

        Args:
            saml_attributes: User attributes from SAML response
            saml_config: SAML IdP configuration

        Returns:
            User identity information (email, name, role, groups)

        Raises:
            ValueError: If required attributes missing
        """
        from ..models import create_user, get_user_by_email

        # Map attributes to user identity
        user_identity = self.map_attributes_to_identity(
            saml_attributes, self.config.attribute_mapping
        )

        email = user_identity["email"]
        name = user_identity["name"]
        groups = user_identity.get("groups", [])

        # Check if user exists
        existing_user = get_user_by_email(email)

        if existing_user:
            logger.info(f"SAML user exists: {email}")
            return {
                "id": existing_user["id"],
                "email": existing_user["email"],
                "full_name": existing_user.get("full_name", ""),
                "role": existing_user["role"],
                "is_new": False,
            }

        # Create new user if JIT enabled
        if not self.config.enabled:
            raise ValueError(
                f"User {email} does not exist and JIT provisioning is disabled"
            )

        # Determine role from groups or use default
        role = self._determine_role_from_groups(groups)

        logger.info(f"Creating new SAML user: {email}")

        # Create user with placeholder password (won't be used)
        import secrets

        placeholder_password = secrets.token_urlsafe(32)

        new_user = create_user(
            email=email,
            password_hash=self._hash_password(placeholder_password),
            full_name=name,
            role=role,
        )

        return {
            "id": new_user["id"],
            "email": new_user["email"],
            "full_name": new_user.get("full_name", ""),
            "role": new_user["role"],
            "is_new": True,
        }

    def get_or_create_oidc_user(
        self, userinfo: Dict[str, Any], oidc_config: OIDCConfig
    ) -> Dict[str, Any]:
        """Get or create user from OIDC userinfo.

        Args:
            userinfo: User information from OIDC userinfo endpoint
            oidc_config: OIDC provider configuration

        Returns:
            User identity information (email, name, role, groups)

        Raises:
            ValueError: If required attributes missing
        """
        from ..models import create_user, get_user_by_email

        # Map userinfo to user identity
        user_identity = self.map_oidc_userinfo_to_identity(
            userinfo, self.config.attribute_mapping
        )

        email = user_identity["email"]
        name = user_identity["name"]
        groups = user_identity.get("groups", [])

        # Check if user exists
        existing_user = get_user_by_email(email)

        if existing_user:
            logger.info(f"OIDC user exists: {email}")
            return {
                "id": existing_user["id"],
                "email": existing_user["email"],
                "full_name": existing_user.get("full_name", ""),
                "role": existing_user["role"],
                "is_new": False,
            }

        # Create new user if JIT enabled
        if not self.config.enabled:
            raise ValueError(
                f"User {email} does not exist and JIT provisioning is disabled"
            )

        # Determine role from groups or use default
        role = self._determine_role_from_groups(groups)

        logger.info(f"Creating new OIDC user: {email}")

        # Create user with placeholder password (won't be used)
        import secrets

        placeholder_password = secrets.token_urlsafe(32)

        new_user = create_user(
            email=email,
            password_hash=self._hash_password(placeholder_password),
            full_name=name,
            role=role,
        )

        return {
            "id": new_user["id"],
            "email": new_user["email"],
            "full_name": new_user.get("full_name", ""),
            "role": new_user["role"],
            "is_new": True,
        }

    def map_attributes_to_identity(
        self,
        attributes: Dict[str, List[str]],
        mapping: Optional[AttributeMapping] = None,
    ) -> Dict[str, Any]:
        """Map SAML attributes to user identity fields.

        Args:
            attributes: SAML attributes (list values)
            mapping: Attribute mapping configuration

        Returns:
            Mapped user identity with email, name, groups
        """
        if mapping is None:
            mapping = self.config.attribute_mapping

        # Extract email
        email_attr = mapping.email_field
        email = None

        if email_attr in attributes and attributes[email_attr]:
            email = attributes[email_attr][0].lower()

        if not email:
            raise ValueError(f"Required attribute '{email_attr}' not found")

        # Extract name
        name_attr = mapping.name_field
        name = ""

        if name_attr in attributes and attributes[name_attr]:
            name = attributes[name_attr][0]

        # Extract groups if configured
        groups = []
        if mapping.groups_field and mapping.groups_field in attributes:
            groups = attributes[mapping.groups_field]

        return {
            "email": email,
            "name": name,
            "groups": groups,
        }

    def map_oidc_userinfo_to_identity(
        self, userinfo: Dict[str, Any], mapping: Optional[AttributeMapping] = None
    ) -> Dict[str, Any]:
        """Map OIDC userinfo to user identity fields.

        Args:
            userinfo: OIDC userinfo (direct values, not lists)
            mapping: Attribute mapping configuration

        Returns:
            Mapped user identity with email, name, groups
        """
        if mapping is None:
            mapping = self.config.attribute_mapping

        # Extract email
        email_field = mapping.email_field
        email = userinfo.get(email_field, "").lower()

        if not email:
            raise ValueError(f"Required field '{email_field}' not found in userinfo")

        # Extract name
        name_field = mapping.name_field
        name = userinfo.get(name_field, "") or userinfo.get("name", "")

        # Extract groups if configured
        groups = []
        if mapping.groups_field:
            groups_value = userinfo.get(mapping.groups_field, [])
            if isinstance(groups_value, list):
                groups = groups_value
            elif groups_value:
                groups = [str(groups_value)]

        return {
            "email": email,
            "name": name,
            "groups": groups,
        }

    def _determine_role_from_groups(self, groups: List[str]) -> str:
        """Determine user role from group membership.

        Args:
            groups: List of groups the user belongs to

        Returns:
            Role: 'admin', 'maintainer', or 'viewer'
        """
        # Map groups to roles (configurable)
        for group in groups:
            if group in self.config.group_role_mapping:
                return self.config.group_role_mapping[group]

        # Check for common admin/maintainer group names
        group_lower = [g.lower() for g in groups]

        if any("admin" in g for g in group_lower):
            return "admin"

        if any("maintain" in g or "editor" in g for g in group_lower):
            return "maintainer"

        # Default role
        return self.config.auto_assign_role

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        import bcrypt

        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


__all__ = [
    "AttributeMapping",
    "JITConfig",
    "JITProvisioner",
]
