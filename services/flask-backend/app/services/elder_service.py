"""Elder API client and entity-to-shape mapping service.

This module provides integration with Elder for importing infrastructure entities
and dependencies as shapes into IceCharts drawings.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class EntityTypeMapping(Enum):
    """Maps Elder entity types to IceCharts node types and icons."""

    COMPUTE = {
        "node_type": "rectangle",
        "icon": "server",
        "color": "#3B82F6",
        "description": "Compute Device",
    }
    VPC = {
        "node_type": "rectangle",
        "icon": "network",
        "color": "#10B981",
        "description": "Virtual Private Cloud",
    }
    SUBNET = {
        "node_type": "rectangle",
        "icon": "share-2",
        "color": "#6366F1",
        "description": "Subnet",
    }
    DATACENTER = {
        "node_type": "rectangle",
        "icon": "database",
        "color": "#F59E0B",
        "description": "Datacenter",
    }
    NETWORK = {
        "node_type": "diamond",
        "icon": "router",
        "color": "#8B5CF6",
        "description": "Network Device",
    }
    USER = {
        "node_type": "circle",
        "icon": "user",
        "color": "#EC4899",
        "description": "User",
    }
    SECURITY_ISSUE = {
        "node_type": "diamond",
        "icon": "alert-triangle",
        "color": "#EF4444",
        "description": "Security Issue",
    }


@dataclass(slots=True)
class ElderEntity:
    """Represents an Elder entity with all relevant metadata."""

    id: int
    unique_id: int
    name: str
    entity_type: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    owner_id: Optional[int] = None
    organization_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "id": self.id,
            "unique_id": self.unique_id,
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "metadata": self.metadata,
            "owner_id": self.owner_id,
            "organization_id": self.organization_id,
        }


@dataclass(slots=True)
class ElderDependency:
    """Represents a dependency relationship between Elder entities."""

    id: int
    source_entity_id: int
    target_entity_id: int
    dependency_type: str
    description: Optional[str] = None
    strength: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dependency to dictionary."""
        return {
            "id": self.id,
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "dependency_type": self.dependency_type,
            "description": self.description,
            "strength": self.strength,
        }


@dataclass(slots=True)
class IceChartsNode:
    """Represents an IceCharts node created from an Elder entity."""

    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]
    style: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "data": self.data,
            "style": self.style,
        }


@dataclass(slots=True)
class IceChartsConnector:
    """Represents an IceCharts edge/connector created from an Elder dependency."""

    id: str
    source: str
    target: str
    type: str = "default"
    data: Optional[Dict[str, Any]] = None
    animated: bool = False
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "data": self.data,
            "animated": self.animated,
            "label": self.label,
        }


class ElderClient:
    """Client for Elder API integration."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
    ):
        """Initialize Elder API client.

        Args:
            base_url: Base URL for Elder API (e.g., https://elder.example.com)
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def get_entities(
        self,
        org_id: int,
        entity_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ElderEntity]:
        """Fetch entities from Elder API.

        Args:
            org_id: Organization ID
            entity_type: Optional filter by entity type
            limit: Maximum number of entities to return
            offset: Pagination offset

        Returns:
            List of ElderEntity objects

        Raises:
            httpx.HTTPError: If API request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {
                "organization_id": org_id,
                "limit": limit,
                "offset": offset,
            }
            if entity_type:
                params["entity_type"] = entity_type

            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/entities",
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()

                data = response.json()
                entities = data.get("entities", [])

                return [
                    ElderEntity(
                        id=e.get("id"),
                        unique_id=e.get("unique_id"),
                        name=e.get("name"),
                        entity_type=e.get("entity_type"),
                        description=e.get("description"),
                        metadata=e.get("metadata", {}),
                        owner_id=e.get("owner_identity_id"),
                        organization_id=e.get("organization_id"),
                    )
                    for e in entities
                ]
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch entities from Elder: {e}")
                raise

    async def get_relationships(
        self,
        org_id: int,
        source_entity_id: Optional[int] = None,
        target_entity_id: Optional[int] = None,
    ) -> List[ElderDependency]:
        """Fetch dependencies/relationships from Elder API.

        Args:
            org_id: Organization ID
            source_entity_id: Optional filter by source entity
            target_entity_id: Optional filter by target entity

        Returns:
            List of ElderDependency objects

        Raises:
            httpx.HTTPError: If API request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {"organization_id": org_id}
            if source_entity_id:
                params["source_entity_id"] = source_entity_id
            if target_entity_id:
                params["target_entity_id"] = target_entity_id

            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/dependencies",
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()

                data = response.json()
                dependencies = data.get("dependencies", [])

                return [
                    ElderDependency(
                        id=d.get("id"),
                        source_entity_id=d.get("source_entity_id"),
                        target_entity_id=d.get("target_entity_id"),
                        dependency_type=d.get("dependency_type", "depends_on"),
                        description=d.get("description"),
                        strength=d.get("strength"),
                    )
                    for d in dependencies
                ]
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch relationships from Elder: {e}")
                raise

    async def get_graph(
        self,
        org_id: int,
        entity_id: Optional[int] = None,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """Fetch dependency graph from Elder API.

        Args:
            org_id: Organization ID
            entity_id: Optional starting entity ID for traversal
            depth: Depth of graph traversal

        Returns:
            Dictionary with entities and dependencies

        Raises:
            httpx.HTTPError: If API request fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {"organization_id": org_id, "depth": depth}
            if entity_id:
                params["entity_id"] = entity_id

            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/graph",
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch graph from Elder: {e}")
                raise

    @staticmethod
    def map_entity_to_shape(
        entity: ElderEntity,
        x: float = 0,
        y: float = 0,
    ) -> IceChartsNode:
        """Convert Elder entity to IceCharts shape/node.

        Args:
            entity: ElderEntity to convert
            x: X position for node
            y: Y position for node

        Returns:
            IceChartsNode with appropriate styling and icon
        """
        # Get type mapping
        try:
            entity_enum = EntityTypeMapping[entity.entity_type.upper()]
            mapping = entity_enum.value
        except KeyError:
            # Default mapping for unknown types
            mapping = {
                "node_type": "rectangle",
                "icon": "package",
                "color": "#6B7280",
                "description": entity.entity_type,
            }

        # Create node
        node = IceChartsNode(
            id=f"elder_{entity.id}_{entity.unique_id}",
            type=mapping["node_type"],
            position={"x": x, "y": y},
            data={
                "label": entity.name,
                "icon": mapping["icon"],
                "description": entity.description or mapping["description"],
                "elder_id": entity.id,
                "elder_unique_id": entity.unique_id,
                "elder_type": entity.entity_type,
                "metadata": entity.metadata,
            },
            style={
                "backgroundColor": mapping["color"],
                "color": "#FFFFFF",
                "borderColor": "#000000",
                "borderWidth": 2,
            },
        )

        return node

    @staticmethod
    def map_relationship_to_connector(
        dependency: ElderDependency,
        source_node_id: str,
        target_node_id: str,
    ) -> IceChartsConnector:
        """Convert Elder dependency to IceCharts connector/edge.

        Args:
            dependency: ElderDependency to convert
            source_node_id: ID of source node in IceCharts
            target_node_id: ID of target node in IceCharts

        Returns:
            IceChartsConnector representing the relationship
        """
        # Determine edge styling based on dependency type
        edge_type = "default"
        animated = False
        label = dependency.dependency_type

        if dependency.dependency_type == "depends_on":
            animated = True
            label = "depends on"
        elif dependency.dependency_type == "hosted_on":
            label = "hosted on"
        elif dependency.dependency_type == "manages":
            label = "manages"
        elif dependency.dependency_type == "connects_to":
            animated = True

        connector = IceChartsConnector(
            id=f"elder_dep_{dependency.id}",
            source=source_node_id,
            target=target_node_id,
            type=edge_type,
            animated=animated,
            label=label,
            data={
                "elder_dependency_id": dependency.id,
                "dependency_type": dependency.dependency_type,
                "description": dependency.description,
                "strength": dependency.strength,
            },
        )

        return connector

    @staticmethod
    def calculate_layout_positions(
        entities: List[ElderEntity],
        dependencies: List[ElderDependency],
        canvas_width: float = 1600,
        canvas_height: float = 900,
    ) -> Dict[int, Dict[str, float]]:
        """Calculate positions for entities based on dependency graph.

        Uses a simple hierarchical layout algorithm based on dependencies.

        Args:
            entities: List of entities to position
            dependencies: List of dependencies for layout calculation
            canvas_width: Width of canvas for layout
            canvas_height: Height of canvas for layout

        Returns:
            Dictionary mapping entity IDs to {x, y} positions
        """
        positions: Dict[int, Dict[str, float]] = {}

        # Build dependency graph
        entity_map = {e.id: e for e in entities}
        has_incoming = {e.id: False for e in entities}

        for dep in dependencies:
            if dep.target_entity_id in has_incoming:
                has_incoming[dep.target_entity_id] = True

        # Find root entities (no incoming dependencies)
        roots = [e.id for e in entities if not has_incoming[e.id]]

        if not roots:
            roots = [e.id for e in entities]

        # Simple grid-based layout
        cols = max(1, int((len(entities) ** 0.5)))
        rows = (len(entities) + cols - 1) // cols

        cell_width = canvas_width / (cols + 1)
        cell_height = canvas_height / (rows + 1)

        for idx, entity in enumerate(entities):
            col = idx % cols
            row = idx // cols
            positions[entity.id] = {
                "x": cell_width * (col + 1) - cell_width / 2,
                "y": cell_height * (row + 1) - cell_height / 2,
            }

        return positions
