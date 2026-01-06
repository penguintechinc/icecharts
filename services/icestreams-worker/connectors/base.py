"""
Base connector classes and data structures for the IceCharts Connector Framework.

This module defines the foundational classes that all connectors inherit from,
including configuration, manifest parsing, and API client functionality.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional, Type

import httpx
import yaml

logger = logging.getLogger(__name__)


class AuthType(str, Enum):
    """Supported authentication types for connectors."""

    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    JWT = "jwt"


@dataclass(slots=True, frozen=True)
class AuthMethod:
    """
    Authentication method configuration.

    Defines how to authenticate with a connector's API.

    Attributes:
        type: Authentication type (api_key, oauth, jwt, none).
        header: HTTP header name for the credential.
        env_var: Environment variable containing the credential.
        token_prefix: Prefix for token (e.g., "Bearer " for JWT).
    """

    type: AuthType
    header: str = ""
    env_var: str = ""
    token_prefix: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthMethod:
        """Create AuthMethod from dictionary."""
        return cls(
            type=AuthType(data.get("type", "none")),
            header=data.get("header", ""),
            env_var=data.get("env_var", ""),
            token_prefix=data.get("token_prefix", ""),
        )


@dataclass(slots=True, frozen=True)
class ConfigField:
    """
    Configuration field schema for UI rendering.

    Defines a form field that will be rendered in the node config panel.

    Attributes:
        field: Field identifier (key in config dict).
        type: Field type (string, number, select, multiselect, textarea, checkbox).
        label: Human-readable label for the field.
        placeholder: Placeholder text for input fields.
        options: Available options for select/multiselect fields.
        required: Whether the field is required.
        default: Default value for the field.
        supports_variables: Whether the field supports {{variable}} interpolation.
        description: Help text for the field.
    """

    field: str
    type: str
    label: str
    placeholder: str = ""
    options: tuple = ()
    required: bool = False
    default: Any = None
    supports_variables: bool = False
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConfigField:
        """Create ConfigField from dictionary."""
        options = data.get("options", [])
        return cls(
            field=data["field"],
            type=data.get("type", "string"),
            label=data.get("label", data["field"]),
            placeholder=data.get("placeholder", ""),
            options=tuple(options) if options else (),
            required=data.get("required", False),
            default=data.get("default"),
            supports_variables=data.get("supports_variables", False),
            description=data.get("description", ""),
        )


@dataclass(slots=True, frozen=True)
class PortDefinition:
    """
    Input/output port definition for workflow nodes.

    Attributes:
        name: Port identifier (e.g., "in", "out", "true", "false").
        type: Data type hint (any, string, number, bool, object, array).
        description: Human-readable description of the port.
        required: Whether this input port is required.
    """

    name: str
    type: str = "any"
    description: str = ""
    required: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PortDefinition:
        """Create PortDefinition from dictionary."""
        return cls(
            name=data["name"],
            type=data.get("type", "any"),
            description=data.get("description", ""),
            required=data.get("required", True),
        )


@dataclass(slots=True, frozen=True)
class TriggerDefinition:
    """
    Trigger node definition from connector manifest.

    Triggers are entry points that start workflow execution.

    Attributes:
        id: Trigger identifier (used in node_type: trigger_{connector}_{id}).
        name: Display name for the trigger.
        description: Human-readable description.
        icon: Emoji or icon identifier.
        webhook_path: Path for incoming webhooks.
        outputs: List of output port definitions.
        config_schema: List of configuration fields.
    """

    id: str
    name: str
    description: str
    icon: str = ""
    webhook_path: str = ""
    outputs: tuple = ()
    config_schema: tuple = ()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TriggerDefinition:
        """Create TriggerDefinition from dictionary."""
        outputs = tuple(
            PortDefinition.from_dict(o) for o in data.get("outputs", [])
        )
        config_schema = tuple(
            ConfigField.from_dict(f) for f in data.get("config_schema", [])
        )
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            webhook_path=data.get("webhook_path", ""),
            outputs=outputs,
            config_schema=config_schema,
        )


@dataclass(slots=True, frozen=True)
class ActionDefinition:
    """
    Action node definition from connector manifest.

    Actions execute API calls to external services.

    Attributes:
        id: Action identifier (used in node_type: action_{connector}_{id}).
        name: Display name for the action.
        description: Human-readable description.
        icon: Emoji or icon identifier.
        endpoint: API endpoint path.
        method: HTTP method (GET, POST, PUT, DELETE, PATCH).
        inputs: List of input port definitions.
        outputs: List of output port definitions.
        config_schema: List of configuration fields.
        request_body_template: Optional Jinja2 template for request body.
    """

    id: str
    name: str
    description: str
    endpoint: str
    method: str = "POST"
    icon: str = ""
    inputs: tuple = ()
    outputs: tuple = ()
    config_schema: tuple = ()
    request_body_template: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ActionDefinition:
        """Create ActionDefinition from dictionary."""
        inputs = tuple(
            PortDefinition.from_dict(i) for i in data.get("inputs", [])
        )
        outputs = tuple(
            PortDefinition.from_dict(o) for o in data.get("outputs", [])
        )
        config_schema = tuple(
            ConfigField.from_dict(f) for f in data.get("config_schema", [])
        )
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            endpoint=data.get("endpoint", ""),
            method=data.get("method", "POST"),
            icon=data.get("icon", ""),
            inputs=inputs,
            outputs=outputs,
            config_schema=config_schema,
            request_body_template=data.get("request_body_template", ""),
        )


@dataclass(slots=True, frozen=True)
class TransformDefinition:
    """
    Transform node definition from connector manifest.

    Transforms process data without side effects (e.g., lookups, validations).

    Attributes:
        id: Transform identifier (used in node_type: transform_{connector}_{id}).
        name: Display name for the transform.
        description: Human-readable description.
        icon: Emoji or icon identifier.
        endpoint: Optional API endpoint for data fetching.
        method: HTTP method if endpoint is used.
        inputs: List of input port definitions.
        outputs: List of output port definitions.
        config_schema: List of configuration fields.
    """

    id: str
    name: str
    description: str
    icon: str = ""
    endpoint: str = ""
    method: str = "GET"
    inputs: tuple = ()
    outputs: tuple = ()
    config_schema: tuple = ()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TransformDefinition:
        """Create TransformDefinition from dictionary."""
        inputs = tuple(
            PortDefinition.from_dict(i) for i in data.get("inputs", [])
        )
        outputs = tuple(
            PortDefinition.from_dict(o) for o in data.get("outputs", [])
        )
        config_schema = tuple(
            ConfigField.from_dict(f) for f in data.get("config_schema", [])
        )
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            endpoint=data.get("endpoint", ""),
            method=data.get("method", "GET"),
            inputs=inputs,
            outputs=outputs,
            config_schema=config_schema,
        )


@dataclass(slots=True)
class ConnectorConfig:
    """
    Runtime configuration for a connector instance.

    Stores connection details and authentication credentials.

    Attributes:
        connector_id: Unique connector identifier.
        base_url: API base URL.
        auth_type: Authentication type being used.
        api_key: API key credential (for api_key auth).
        oauth_token: OAuth/JWT token (for oauth/jwt auth).
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
    """

    connector_id: str
    base_url: str
    auth_type: AuthType = AuthType.NONE
    api_key: Optional[str] = None
    oauth_token: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3

    def get_auth_header(self) -> Optional[Dict[str, str]]:
        """Get authentication headers based on auth type."""
        if self.auth_type == AuthType.API_KEY and self.api_key:
            return {"X-API-Key": self.api_key}
        elif self.auth_type in (AuthType.OAUTH, AuthType.JWT) and self.oauth_token:
            return {"Authorization": f"Bearer {self.oauth_token}"}
        return None


@dataclass(slots=True)
class ConnectorManifest:
    """
    Parsed connector manifest containing all definitions.

    Attributes:
        id: Unique connector identifier.
        name: Display name.
        description: Human-readable description.
        icon: Emoji or icon identifier.
        color: UI color (hex code).
        version: Connector version.
        auth_methods: Available authentication methods.
        base_url_env: Environment variable for base URL.
        default_url: Default base URL.
        health_endpoint: Health check endpoint path.
        triggers: List of trigger definitions.
        actions: List of action definitions.
        transforms: List of transform definitions.
    """

    id: str
    name: str
    description: str
    icon: str = ""
    color: str = "#6366F1"
    version: str = "1.0.0"
    auth_methods: tuple = ()
    base_url_env: str = ""
    default_url: str = ""
    health_endpoint: str = "/health"
    triggers: tuple = ()
    actions: tuple = ()
    transforms: tuple = ()

    @classmethod
    def from_yaml(cls, yaml_path: str) -> ConnectorManifest:
        """Load connector manifest from YAML file."""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        connector = data.get("connector", data)

        auth_methods = tuple(
            AuthMethod.from_dict(m)
            for m in connector.get("auth", {}).get("methods", [])
        )

        connection = connector.get("connection", {})

        triggers = tuple(
            TriggerDefinition.from_dict(t)
            for t in connector.get("triggers", [])
        )

        actions = tuple(
            ActionDefinition.from_dict(a)
            for a in connector.get("actions", [])
        )

        transforms = tuple(
            TransformDefinition.from_dict(t)
            for t in connector.get("transforms", [])
        )

        return cls(
            id=connector["id"],
            name=connector["name"],
            description=connector.get("description", ""),
            icon=connector.get("icon", ""),
            color=connector.get("color", "#6366F1"),
            version=connector.get("version", "1.0.0"),
            auth_methods=auth_methods,
            base_url_env=connection.get("base_url_env", ""),
            default_url=connection.get("default_url", ""),
            health_endpoint=connection.get("health_endpoint", "/health"),
            triggers=triggers,
            actions=actions,
            transforms=transforms,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "version": self.version,
            "triggers": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "icon": t.icon,
                    "outputs": [
                        {"name": o.name, "type": o.type, "description": o.description}
                        for o in t.outputs
                    ],
                    "config_schema": [
                        {
                            "field": f.field,
                            "type": f.type,
                            "label": f.label,
                            "placeholder": f.placeholder,
                            "options": list(f.options),
                            "required": f.required,
                            "default": f.default,
                            "supports_variables": f.supports_variables,
                            "description": f.description,
                        }
                        for f in t.config_schema
                    ],
                }
                for t in self.triggers
            ],
            "actions": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "icon": a.icon,
                    "inputs": [
                        {"name": i.name, "type": i.type, "description": i.description}
                        for i in a.inputs
                    ],
                    "outputs": [
                        {"name": o.name, "type": o.type, "description": o.description}
                        for o in a.outputs
                    ],
                    "config_schema": [
                        {
                            "field": f.field,
                            "type": f.type,
                            "label": f.label,
                            "placeholder": f.placeholder,
                            "options": list(f.options),
                            "required": f.required,
                            "default": f.default,
                            "supports_variables": f.supports_variables,
                            "description": f.description,
                        }
                        for f in a.config_schema
                    ],
                }
                for a in self.actions
            ],
            "transforms": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "icon": t.icon,
                    "inputs": [
                        {"name": i.name, "type": i.type, "description": i.description}
                        for i in t.inputs
                    ],
                    "outputs": [
                        {"name": o.name, "type": o.type, "description": o.description}
                        for o in t.outputs
                    ],
                    "config_schema": [
                        {
                            "field": f.field,
                            "type": f.type,
                            "label": f.label,
                            "placeholder": f.placeholder,
                            "options": list(f.options),
                            "required": f.required,
                            "default": f.default,
                            "supports_variables": f.supports_variables,
                            "description": f.description,
                        }
                        for f in t.config_schema
                    ],
                }
                for t in self.transforms
            ],
        }


class BaseConnector(ABC):
    """
    Abstract base class for all IceCharts connectors.

    Provides common functionality for API calls, authentication, and
    health checking. Subclasses can override methods for custom behavior.

    Class Attributes:
        connector_id: Unique identifier for the connector.
        manifest: Parsed connector manifest.

    Instance Attributes:
        config: Runtime configuration with credentials.
        _client: HTTP client for API calls.
    """

    connector_id: str = ""
    manifest: ConnectorManifest = None

    def __init__(self, config: Optional[ConnectorConfig] = None) -> None:
        """
        Initialize the connector with optional configuration.

        Args:
            config: Runtime configuration. If None, creates from environment.
        """
        if not self.connector_id:
            raise ValueError("Connector must define connector_id")
        if not self.manifest:
            raise ValueError("Connector must have a manifest")

        if config is None:
            config = self._create_config_from_env()

        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    def _create_config_from_env(self) -> ConnectorConfig:
        """Create configuration from environment variables."""
        base_url = os.getenv(
            self.manifest.base_url_env,
            self.manifest.default_url
        )

        # Determine auth type and credentials from environment
        auth_type = AuthType.NONE
        api_key = None
        oauth_token = None

        for auth_method in self.manifest.auth_methods:
            if auth_method.env_var:
                credential = os.getenv(auth_method.env_var)
                if credential:
                    auth_type = auth_method.type
                    if auth_type == AuthType.API_KEY:
                        api_key = credential
                    elif auth_type in (AuthType.OAUTH, AuthType.JWT):
                        oauth_token = credential
                    break

        return ConnectorConfig(
            connector_id=self.connector_id,
            base_url=base_url,
            auth_type=auth_type,
            api_key=api_key,
            oauth_token=oauth_token,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        return self._client

    async def call_api(
        self,
        endpoint: str,
        method: str = "GET",
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an API call to the connector's service.

        Args:
            endpoint: API endpoint path.
            method: HTTP method.
            body: Request body (for POST/PUT/PATCH).
            params: Query parameters.
            headers: Additional headers.

        Returns:
            Response data as dictionary.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        client = await self._get_client()

        # Build headers with authentication
        request_headers = {}
        auth_header = self.config.get_auth_header()
        if auth_header:
            request_headers.update(auth_header)
        if headers:
            request_headers.update(headers)

        # Make request with retries
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    json=body,
                    params=params,
                    headers=request_headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:
                    # Rate limited - wait and retry
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                elif e.response.status_code >= 500:
                    # Server error - retry with backoff
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                else:
                    # Client error - don't retry
                    raise
            except httpx.RequestError as e:
                last_error = e
                import asyncio
                await asyncio.sleep(2 ** attempt)

        raise last_error

    async def validate_connection(self) -> bool:
        """
        Validate that the connector can reach its service.

        Returns:
            True if connection is valid, False otherwise.
        """
        try:
            await self.call_api(self.manifest.health_endpoint, method="GET")
            return True
        except Exception as e:
            logger.warning(f"Connection validation failed for {self.connector_id}: {e}")
            return False

    async def cleanup(self) -> None:
        """Close HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def get_trigger(self, trigger_id: str) -> Optional[TriggerDefinition]:
        """Get trigger definition by ID."""
        for trigger in self.manifest.triggers:
            if trigger.id == trigger_id:
                return trigger
        return None

    def get_action(self, action_id: str) -> Optional[ActionDefinition]:
        """Get action definition by ID."""
        for action in self.manifest.actions:
            if action.id == action_id:
                return action
        return None

    def get_transform(self, transform_id: str) -> Optional[TransformDefinition]:
        """Get transform definition by ID."""
        for transform in self.manifest.transforms:
            if transform.id == transform_id:
                return transform
        return None

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(id={self.connector_id!r})"
