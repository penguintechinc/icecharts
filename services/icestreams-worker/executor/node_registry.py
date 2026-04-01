#!/usr/bin/env python3
"""
Node Registry for IceStreams Playbook Executor.

This module provides a centralized registry for mapping node_type strings
to their corresponding node class implementations. Workers use this registry
to instantiate the correct node class when executing playbooks.

Thread-safe singleton pattern ensures consistent registration across the application.
"""

import logging
import threading
from typing import Dict, List, Optional, Type, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Type alias for node class (will be BaseNode once it exists)
NodeClassType = Type


@dataclass(slots=True, frozen=True)
class NodeInfo:
    """
    Metadata about a registered node type.

    Attributes:
        node_type: Unique identifier for the node type (e.g., "transform_filter")
        node_class: The class implementing this node type
        category: Node category (e.g., "transform", "action", "conditional")
        display_name: Human-readable name for UI display
        description: Brief description of what this node does
    """

    node_type: str
    node_class: NodeClassType
    category: str
    display_name: str
    description: str


class NodeRegistryError(Exception):
    """Base exception for node registry errors."""

    pass


class NodeNotFoundError(NodeRegistryError):
    """Raised when a requested node type is not registered."""

    pass


class DuplicateNodeError(NodeRegistryError):
    """Raised when attempting to register a node type that already exists."""

    pass


class NodeRegistry:
    """
    Thread-safe singleton registry for IceStreams node types.

    This registry maps node_type strings to their corresponding node classes,
    allowing workers to dynamically instantiate the correct node implementation
    during playbook execution.

    Example:
        # Register a node class
        NodeRegistry.register("transform_filter", FilterNode, "transform")

        # Get a node class
        node_class = NodeRegistry.get("transform_filter")
        node_instance = node_class(config)

        # Check if registered
        if NodeRegistry.is_registered("transform_filter"):
            ...
    """

    # Class-level registry storage
    _registry: Dict[str, NodeInfo] = {}
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def register(
        cls,
        node_type: str,
        node_class: NodeClassType,
        category: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        allow_override: bool = False,
    ) -> None:
        """
        Register a node class with the registry.

        Args:
            node_type: Unique identifier for the node type (e.g., "transform_filter")
            node_class: The class implementing this node type
            category: Node category (e.g., "transform", "action", "conditional")
            display_name: Optional human-readable name (defaults to node_type)
            description: Optional description (defaults to class docstring)
            allow_override: Allow overriding existing registration (default: False)

        Raises:
            DuplicateNodeError: If node_type is already registered and allow_override is False
            ValueError: If node_type is empty or invalid

        Thread-safe: Yes
        """
        if not node_type or not isinstance(node_type, str):
            raise ValueError(f"Invalid node_type: {node_type}")

        if not node_class:
            raise ValueError(f"Invalid node_class for node_type '{node_type}'")

        if not category or not isinstance(category, str):
            raise ValueError(f"Invalid category for node_type '{node_type}'")

        with cls._lock:
            # Check for duplicate registration
            if node_type in cls._registry and not allow_override:
                existing = cls._registry[node_type]
                raise DuplicateNodeError(
                    f"Node type '{node_type}' is already registered "
                    f"to {existing.node_class.__name__}. "
                    f"Use allow_override=True to override."
                )

            # Extract metadata
            final_display_name = display_name or node_type.replace("_", " ").title()
            final_description = description or (
                node_class.__doc__.strip().split("\n")[0]
                if node_class.__doc__
                else f"{node_type} node"
            )

            # Create node info
            node_info = NodeInfo(
                node_type=node_type,
                node_class=node_class,
                category=category,
                display_name=final_display_name,
                description=final_description,
            )

            # Register
            cls._registry[node_type] = node_info

            action = "Overrode" if node_type in cls._registry else "Registered"
            logger.info(
                f"{action} node type '{node_type}' -> {node_class.__name__} "
                f"(category: {category})"
            )

    @classmethod
    def get(
        cls, node_type: str, raise_on_missing: bool = True
    ) -> Optional[NodeClassType]:
        """
        Get a node class by its type identifier.

        Args:
            node_type: The node type identifier to look up
            raise_on_missing: If True, raise NodeNotFoundError when not found.
                            If False, return None when not found.

        Returns:
            The node class if found, None if not found and raise_on_missing=False

        Raises:
            NodeNotFoundError: If node_type is not registered and raise_on_missing=True

        Thread-safe: Yes
        """
        with cls._lock:
            node_info = cls._registry.get(node_type)

            if node_info is None:
                if raise_on_missing:
                    available = ", ".join(sorted(cls._registry.keys()))
                    raise NodeNotFoundError(
                        f"Node type '{node_type}' is not registered. "
                        f"Available types: {available or 'none'}"
                    )
                return None

            return node_info.node_class

    @classmethod
    def get_info(cls, node_type: str) -> Optional[NodeInfo]:
        """
        Get full node information by type identifier.

        Args:
            node_type: The node type identifier to look up

        Returns:
            NodeInfo object if found, None otherwise

        Thread-safe: Yes
        """
        with cls._lock:
            return cls._registry.get(node_type)

    @classmethod
    def get_all(cls) -> Dict[str, NodeClassType]:
        """
        Get all registered node types and their classes.

        Returns:
            Dictionary mapping node_type to node_class

        Thread-safe: Yes
        """
        with cls._lock:
            return {
                node_type: info.node_class for node_type, info in cls._registry.items()
            }

    @classmethod
    def get_all_info(cls) -> Dict[str, NodeInfo]:
        """
        Get all registered node types and their full information.

        Returns:
            Dictionary mapping node_type to NodeInfo

        Thread-safe: Yes
        """
        with cls._lock:
            return dict(cls._registry)

    @classmethod
    def get_by_category(cls, category: str) -> List[NodeInfo]:
        """
        Get all node types in a specific category.

        Args:
            category: The category to filter by (e.g., "transform", "action")

        Returns:
            List of NodeInfo objects for nodes in the specified category

        Thread-safe: Yes
        """
        with cls._lock:
            return [
                info for info in cls._registry.values() if info.category == category
            ]

    @classmethod
    def get_categories(cls) -> List[str]:
        """
        Get all unique categories of registered nodes.

        Returns:
            Sorted list of unique category names

        Thread-safe: Yes
        """
        with cls._lock:
            categories = {info.category for info in cls._registry.values()}
            return sorted(categories)

    @classmethod
    def is_registered(cls, node_type: str) -> bool:
        """
        Check if a node type is registered.

        Args:
            node_type: The node type identifier to check

        Returns:
            True if registered, False otherwise

        Thread-safe: Yes
        """
        with cls._lock:
            return node_type in cls._registry

    @classmethod
    def unregister(cls, node_type: str) -> bool:
        """
        Unregister a node type.

        Args:
            node_type: The node type identifier to unregister

        Returns:
            True if node was unregistered, False if it wasn't registered

        Thread-safe: Yes
        """
        with cls._lock:
            if node_type in cls._registry:
                del cls._registry[node_type]
                logger.info(f"Unregistered node type '{node_type}'")
                return True
            return False

    @classmethod
    def clear(cls) -> int:
        """
        Clear all registered nodes.

        Returns:
            Number of nodes that were cleared

        Thread-safe: Yes
        """
        with cls._lock:
            count = len(cls._registry)
            cls._registry.clear()
            cls._initialized = False
            logger.warning(f"Cleared {count} registered node types")
            return count

    @classmethod
    def count(cls) -> int:
        """
        Get the total number of registered nodes.

        Returns:
            Number of registered node types

        Thread-safe: Yes
        """
        with cls._lock:
            return len(cls._registry)

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if the registry has been initialized with node discoveries.

        Returns:
            True if discover_nodes() has been called, False otherwise

        Thread-safe: Yes
        """
        with cls._lock:
            return cls._initialized

    @classmethod
    def mark_initialized(cls) -> None:
        """
        Mark the registry as initialized.

        This is called by discover_nodes() after node modules are loaded.

        Thread-safe: Yes
        """
        with cls._lock:
            cls._initialized = True
            logger.info(
                f"Node registry marked as initialized ({len(cls._registry)} nodes)"
            )


def register_node(
    node_type: str,
    category: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable:
    """
    Decorator to automatically register a node class.

    This decorator should be applied to node classes to automatically
    register them with the NodeRegistry when the module is imported.

    Args:
        node_type: Unique identifier for the node type (e.g., "transform_filter")
        category: Node category (e.g., "transform", "action", "conditional")
        display_name: Optional human-readable name (defaults to node_type)
        description: Optional description (defaults to class docstring)

    Returns:
        Decorator function that registers the class and returns it unchanged

    Example:
        @register_node("transform_filter", "transform", "Filter Transform")
        class FilterNode(BaseNode):
            '''Filters data based on conditions.'''
            pass

    Raises:
        DuplicateNodeError: If node_type is already registered
    """

    def decorator(node_class: NodeClassType) -> NodeClassType:
        # Register the node class
        NodeRegistry.register(
            node_type=node_type,
            node_class=node_class,
            category=category,
            display_name=display_name,
            description=description,
        )
        return node_class

    return decorator


def discover_nodes() -> int:
    """
    Discover and import all node modules to trigger registration.

    This function should be called at worker startup to ensure all node
    types are registered before processing playbooks.

    The function attempts to import node modules from these locations:
    - nodes.transforms (transform nodes)
    - nodes.conditionals (conditional nodes)
    - nodes.actions (action nodes)
    - nodes.triggers (trigger nodes)

    Returns:
        Number of nodes discovered and registered

    Thread-safe: Yes (uses NodeRegistry's internal locking)

    Example:
        # At worker startup
        from executor.node_registry import discover_nodes

        num_nodes = discover_nodes()
        logger.info(f"Discovered {num_nodes} node types")
    """
    if NodeRegistry.is_initialized():
        logger.warning("Node registry already initialized, skipping discovery")
        return NodeRegistry.count()

    initial_count = NodeRegistry.count()
    logger.info("Starting node discovery...")

    # List of node module paths to import
    node_modules = [
        "nodes.transforms",
        "nodes.conditionals",
        "nodes.actions",
        "nodes.triggers",
    ]

    # Attempt to import each module
    for module_path in node_modules:
        try:
            # Dynamic import to trigger @register_node decorators
            __import__(module_path)
            logger.info(f"Successfully imported {module_path}")
        except ImportError as e:
            # Module doesn't exist yet, that's okay
            logger.debug(f"Module {module_path} not found: {e}")
        except Exception as e:
            # Log other errors but continue discovery
            logger.error(f"Error importing {module_path}: {e}", exc_info=True)

    # Mark as initialized
    NodeRegistry.mark_initialized()

    # Calculate how many nodes were discovered
    discovered_count = NodeRegistry.count() - initial_count
    total_count = NodeRegistry.count()

    logger.info(
        f"Node discovery complete. Discovered {discovered_count} new nodes. "
        f"Total registered: {total_count}"
    )

    # Log all registered nodes by category
    if total_count > 0:
        for category in NodeRegistry.get_categories():
            nodes_in_category = NodeRegistry.get_by_category(category)
            node_names = [info.node_type for info in nodes_in_category]
            logger.info(f"  {category}: {', '.join(node_names)}")

    return total_count


def get_registry_stats() -> Dict[str, any]:
    """
    Get statistics about the current node registry state.

    Returns:
        Dictionary containing registry statistics:
        - total_nodes: Total number of registered nodes
        - categories: Dictionary mapping category to node count
        - initialized: Whether discovery has been run
        - nodes_by_category: Dictionary mapping category to list of node types

    Thread-safe: Yes
    """
    stats = {
        "total_nodes": NodeRegistry.count(),
        "initialized": NodeRegistry.is_initialized(),
        "categories": {},
        "nodes_by_category": {},
    }

    for category in NodeRegistry.get_categories():
        nodes = NodeRegistry.get_by_category(category)
        stats["categories"][category] = len(nodes)
        stats["nodes_by_category"][category] = [n.node_type for n in nodes]

    return stats
