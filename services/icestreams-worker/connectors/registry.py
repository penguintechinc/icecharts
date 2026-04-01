"""
Connector Registry for IceCharts Connector Framework.

This module provides a centralized registry for managing connectors,
discovering manifests, and coordinating connector lifecycle.
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import BaseConnector, ConnectorConfig, ConnectorManifest

logger = logging.getLogger(__name__)


class ConnectorRegistryError(Exception):
    """Base exception for connector registry errors."""

    pass


class ConnectorNotFoundError(ConnectorRegistryError):
    """Raised when a requested connector is not registered."""

    pass


class DuplicateConnectorError(ConnectorRegistryError):
    """Raised when attempting to register a connector that already exists."""

    pass


class ConnectorRegistry:
    """
    Thread-safe singleton registry for IceCharts connectors.

    Manages connector registration, discovery, and instantiation.
    Connectors are loaded from YAML manifests in the manifests/ directory.

    Example:
        # Discover and register all connectors
        discover_connectors()

        # Get a connector instance
        waddlebot = ConnectorRegistry.get_instance("waddlebot")

        # Get connector manifest for API
        manifest = ConnectorRegistry.get_manifest("waddlebot")

        # List all connectors
        for connector in ConnectorRegistry.get_all():
            print(connector.connector_id)
    """

    # Class-level storage
    _manifests: Dict[str, ConnectorManifest] = {}
    _connector_classes: Dict[str, Type[BaseConnector]] = {}
    _instances: Dict[str, BaseConnector] = {}
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def register_manifest(
        cls,
        manifest: ConnectorManifest,
        allow_override: bool = False,
    ) -> None:
        """
        Register a connector manifest.

        Args:
            manifest: Parsed connector manifest.
            allow_override: Allow overriding existing registration.

        Raises:
            DuplicateConnectorError: If connector already registered.
        """
        with cls._lock:
            if manifest.id in cls._manifests and not allow_override:
                raise DuplicateConnectorError(
                    f"Connector '{manifest.id}' is already registered"
                )

            cls._manifests[manifest.id] = manifest
            logger.info(
                f"Registered connector manifest: {manifest.id} "
                f"({len(manifest.triggers)} triggers, "
                f"{len(manifest.actions)} actions, "
                f"{len(manifest.transforms)} transforms)"
            )

    @classmethod
    def register_class(
        cls,
        connector_id: str,
        connector_class: Type[BaseConnector],
        allow_override: bool = False,
    ) -> None:
        """
        Register a connector class for custom implementations.

        Args:
            connector_id: Connector identifier.
            connector_class: Connector class to register.
            allow_override: Allow overriding existing registration.

        Raises:
            DuplicateConnectorError: If connector class already registered.
        """
        with cls._lock:
            if connector_id in cls._connector_classes and not allow_override:
                raise DuplicateConnectorError(
                    f"Connector class for '{connector_id}' is already registered"
                )

            cls._connector_classes[connector_id] = connector_class
            logger.info(f"Registered connector class: {connector_id}")

    @classmethod
    def get_manifest(cls, connector_id: str) -> Optional[ConnectorManifest]:
        """
        Get connector manifest by ID.

        Args:
            connector_id: Connector identifier.

        Returns:
            ConnectorManifest if found, None otherwise.
        """
        with cls._lock:
            return cls._manifests.get(connector_id)

    @classmethod
    def get_instance(
        cls,
        connector_id: str,
        config: Optional[ConnectorConfig] = None,
        raise_on_missing: bool = True,
    ) -> Optional[BaseConnector]:
        """
        Get or create a connector instance.

        Args:
            connector_id: Connector identifier.
            config: Optional runtime configuration.
            raise_on_missing: Raise exception if not found.

        Returns:
            BaseConnector instance if found.

        Raises:
            ConnectorNotFoundError: If connector not found and raise_on_missing.
        """
        with cls._lock:
            # Return cached instance if config matches
            if connector_id in cls._instances and config is None:
                return cls._instances[connector_id]

            # Check if we have a manifest
            manifest = cls._manifests.get(connector_id)
            if manifest is None:
                if raise_on_missing:
                    available = ", ".join(sorted(cls._manifests.keys()))
                    raise ConnectorNotFoundError(
                        f"Connector '{connector_id}' not found. "
                        f"Available: {available or 'none'}"
                    )
                return None

            # Use custom class if registered, otherwise create generic
            if connector_id in cls._connector_classes:
                connector_class = cls._connector_classes[connector_id]
            else:
                # Create a dynamic connector class
                connector_class = cls._create_generic_connector(manifest)

            # Create instance
            instance = connector_class(config)
            if config is None:
                cls._instances[connector_id] = instance

            return instance

    @classmethod
    def _create_generic_connector(
        cls, manifest: ConnectorManifest
    ) -> Type[BaseConnector]:
        """Create a generic connector class from manifest."""
        # Use prefixed names to avoid class-body scoping bug where
        # `manifest = manifest` would shadow the enclosing variable.
        _manifest = manifest
        _connector_id = manifest.id

        class GenericConnector(BaseConnector):
            connector_id = _connector_id
            manifest = _manifest

        GenericConnector.__name__ = f"{manifest.name.replace(' ', '')}Connector"
        return GenericConnector

    @classmethod
    def get_all_manifests(cls) -> List[ConnectorManifest]:
        """Get all registered connector manifests."""
        with cls._lock:
            return list(cls._manifests.values())

    @classmethod
    def get_all_ids(cls) -> List[str]:
        """Get all registered connector IDs."""
        with cls._lock:
            return list(cls._manifests.keys())

    @classmethod
    def is_registered(cls, connector_id: str) -> bool:
        """Check if a connector is registered."""
        with cls._lock:
            return connector_id in cls._manifests

    @classmethod
    def unregister(cls, connector_id: str) -> bool:
        """
        Unregister a connector.

        Args:
            connector_id: Connector identifier.

        Returns:
            True if unregistered, False if not found.
        """
        with cls._lock:
            removed = False
            if connector_id in cls._manifests:
                del cls._manifests[connector_id]
                removed = True
            if connector_id in cls._connector_classes:
                del cls._connector_classes[connector_id]
            if connector_id in cls._instances:
                del cls._instances[connector_id]
            if removed:
                logger.info(f"Unregistered connector: {connector_id}")
            return removed

    @classmethod
    def clear(cls) -> int:
        """
        Clear all registered connectors.

        Returns:
            Number of connectors cleared.
        """
        with cls._lock:
            count = len(cls._manifests)
            cls._manifests.clear()
            cls._connector_classes.clear()
            cls._instances.clear()
            cls._initialized = False
            logger.warning(f"Cleared {count} connectors from registry")
            return count

    @classmethod
    def count(cls) -> int:
        """Get number of registered connectors."""
        with cls._lock:
            return len(cls._manifests)

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if discovery has been run."""
        with cls._lock:
            return cls._initialized

    @classmethod
    def mark_initialized(cls) -> None:
        """Mark registry as initialized."""
        with cls._lock:
            cls._initialized = True


def discover_connectors(
    manifests_dir: Optional[str] = None,
    register_nodes: bool = True,
) -> int:
    """
    Discover and load connector manifests from directory.

    Scans the manifests directory for YAML files and registers each
    as a connector. Optionally generates and registers workflow nodes.

    Args:
        manifests_dir: Directory containing manifest YAML files.
                      Defaults to connectors/manifests/ in package.
        register_nodes: Whether to generate and register workflow nodes.

    Returns:
        Number of connectors discovered.
    """
    if ConnectorRegistry.is_initialized():
        logger.warning("Connector registry already initialized")
        return ConnectorRegistry.count()

    # Determine manifests directory
    if manifests_dir is None:
        package_dir = Path(__file__).parent
        manifests_dir = package_dir / "manifests"
    else:
        manifests_dir = Path(manifests_dir)

    if not manifests_dir.exists():
        logger.warning(f"Manifests directory not found: {manifests_dir}")
        ConnectorRegistry.mark_initialized()
        return 0

    logger.info(f"Discovering connectors in: {manifests_dir}")

    discovered = 0
    for manifest_file in manifests_dir.glob("*.yaml"):
        try:
            manifest = ConnectorManifest.from_yaml(str(manifest_file))
            ConnectorRegistry.register_manifest(manifest)
            discovered += 1

            # Generate workflow nodes if requested
            if register_nodes:
                from .node_generator import generate_nodes_from_connector

                generate_nodes_from_connector(manifest)

        except Exception as e:
            logger.error(f"Failed to load manifest {manifest_file}: {e}")

    # Also check for .yml extension
    for manifest_file in manifests_dir.glob("*.yml"):
        try:
            manifest = ConnectorManifest.from_yaml(str(manifest_file))
            ConnectorRegistry.register_manifest(manifest)
            discovered += 1

            if register_nodes:
                from .node_generator import generate_nodes_from_connector

                generate_nodes_from_connector(manifest)

        except Exception as e:
            logger.error(f"Failed to load manifest {manifest_file}: {e}")

    ConnectorRegistry.mark_initialized()

    logger.info(f"Discovered {discovered} connectors")
    return discovered


def get_connectors_for_api() -> List[Dict]:
    """
    Get connector data formatted for API responses.

    Returns:
        List of connector dictionaries ready for JSON serialization.
    """
    return [manifest.to_dict() for manifest in ConnectorRegistry.get_all_manifests()]
