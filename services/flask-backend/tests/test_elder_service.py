"""Tests for ElderService - Elder API client and entity mapping."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.elder_service import (
    ElderClient,
    ElderDependency,
    ElderEntity,
    EntityTypeMapping,
    IceChartsConnector,
    IceChartsNode,
)


class TestElderEntity:
    """Test ElderEntity dataclass."""

    def test_elder_entity_creation_with_required_fields(self):
        """Test creating an ElderEntity with required fields."""
        entity = ElderEntity(
            id=1,
            unique_id=100,
            name="test-entity",
            entity_type="compute",
        )
        assert entity.id == 1
        assert entity.unique_id == 100
        assert entity.name == "test-entity"
        assert entity.entity_type == "compute"
        assert entity.description is None
        assert entity.metadata == {}
        assert entity.owner_id is None
        assert entity.organization_id is None

    def test_elder_entity_creation_with_all_fields(self):
        """Test creating an ElderEntity with all fields."""
        metadata = {"region": "us-west-2", "tags": ["prod"]}
        entity = ElderEntity(
            id=1,
            unique_id=100,
            name="test-entity",
            entity_type="vpc",
            description="Test VPC",
            metadata=metadata,
            owner_id=42,
            organization_id=10,
        )
        assert entity.description == "Test VPC"
        assert entity.metadata == metadata
        assert entity.owner_id == 42
        assert entity.organization_id == 10

    def test_elder_entity_to_dict(self):
        """Test converting ElderEntity to dictionary."""
        entity = ElderEntity(
            id=1,
            unique_id=100,
            name="test-entity",
            entity_type="compute",
            description="Test",
            owner_id=42,
        )
        result = entity.to_dict()
        assert isinstance(result, dict)
        assert result["id"] == 1
        assert result["unique_id"] == 100
        assert result["name"] == "test-entity"
        assert result["entity_type"] == "compute"
        assert result["description"] == "Test"
        assert result["owner_id"] == 42


class TestElderDependency:
    """Test ElderDependency dataclass."""

    def test_elder_dependency_creation(self):
        """Test creating an ElderDependency."""
        dep = ElderDependency(
            id=1,
            source_entity_id=10,
            target_entity_id=20,
            dependency_type="depends_on",
        )
        assert dep.id == 1
        assert dep.source_entity_id == 10
        assert dep.target_entity_id == 20
        assert dep.dependency_type == "depends_on"
        assert dep.description is None
        assert dep.strength is None

    def test_elder_dependency_with_optional_fields(self):
        """Test ElderDependency with optional fields."""
        dep = ElderDependency(
            id=1,
            source_entity_id=10,
            target_entity_id=20,
            dependency_type="hosted_on",
            description="App hosted on VM",
            strength=0.95,
        )
        assert dep.description == "App hosted on VM"
        assert dep.strength == 0.95

    def test_elder_dependency_to_dict(self):
        """Test converting ElderDependency to dictionary."""
        dep = ElderDependency(
            id=1,
            source_entity_id=10,
            target_entity_id=20,
            dependency_type="manages",
            description="Control relationship",
            strength=0.8,
        )
        result = dep.to_dict()
        assert isinstance(result, dict)
        assert result["source_entity_id"] == 10
        assert result["target_entity_id"] == 20
        assert result["dependency_type"] == "manages"
        assert result["description"] == "Control relationship"
        assert result["strength"] == 0.8


class TestElderClientInit:
    """Test ElderClient initialization."""

    def test_elder_client_initialization(self):
        """Test creating an ElderClient."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key-123",
            timeout=30,
        )
        assert client.base_url == "https://elder.example.com"
        assert client.api_key == "test-key-123"
        assert client.timeout == 30

    def test_elder_client_strips_trailing_slash(self):
        """Test that base URL has trailing slash removed."""
        client = ElderClient(
            base_url="https://elder.example.com/",
            api_key="test-key",
        )
        assert client.base_url == "https://elder.example.com"

    def test_elder_client_headers_include_auth(self):
        """Test that client headers include authorization."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key-123",
        )
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test-key-123"
        assert client.headers["Content-Type"] == "application/json"


class TestElderClientGetEntities:
    """Test fetching entities from Elder API."""

    @pytest.mark.asyncio
    async def test_get_entities_success(self):
        """Test successful entity fetch."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entities": [
                {
                    "id": 1,
                    "unique_id": 100,
                    "name": "server-1",
                    "entity_type": "compute",
                    "description": "Web server",
                    "metadata": {"region": "us-west"},
                    "owner_identity_id": 42,
                    "organization_id": 10,
                },
                {
                    "id": 2,
                    "unique_id": 101,
                    "name": "vpc-prod",
                    "entity_type": "vpc",
                },
            ]
        }

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.return_value = mock_response

            entities = await client.get_entities(org_id=10)

            assert len(entities) == 2
            assert entities[0].id == 1
            assert entities[0].name == "server-1"
            assert entities[0].entity_type == "compute"
            assert entities[1].id == 2
            assert entities[1].entity_type == "vpc"

    @pytest.mark.asyncio
    async def test_get_entities_with_type_filter(self):
        """Test fetching entities with type filter."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entities": [
                {
                    "id": 1,
                    "unique_id": 100,
                    "name": "server-1",
                    "entity_type": "compute",
                }
            ]
        }

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.return_value = mock_response

            entities = await client.get_entities(
                org_id=10,
                entity_type="compute",
            )

            assert len(entities) == 1
            assert entities[0].entity_type == "compute"

            # Verify filter was passed in params
            mock_async_client.get.assert_called_once()
            call_kwargs = mock_async_client.get.call_args[1]
            assert call_kwargs["params"]["entity_type"] == "compute"

    @pytest.mark.asyncio
    async def test_get_entities_empty_response(self):
        """Test handling empty entity list."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"entities": []}

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.return_value = mock_response

            entities = await client.get_entities(org_id=10)

            assert entities == []

    @pytest.mark.asyncio
    async def test_get_entities_http_error_raises(self):
        """Test that HTTP errors are raised."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=MagicMock(status_code=401),
            )

            with pytest.raises(httpx.HTTPError):
                await client.get_entities(org_id=10)

    @pytest.mark.asyncio
    async def test_get_entities_connection_error_raises(self):
        """Test that connection errors are raised."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.side_effect = httpx.ConnectError(
                "Connection failed"
            )

            with pytest.raises(httpx.HTTPError):
                await client.get_entities(org_id=10)


class TestElderClientGetRelationships:
    """Test fetching dependencies from Elder API."""

    @pytest.mark.asyncio
    async def test_get_relationships_success(self):
        """Test successful dependency fetch."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "dependencies": [
                {
                    "id": 1,
                    "source_entity_id": 10,
                    "target_entity_id": 20,
                    "dependency_type": "depends_on",
                    "description": "App depends on DB",
                    "strength": 0.95,
                },
                {
                    "id": 2,
                    "source_entity_id": 20,
                    "target_entity_id": 30,
                    "dependency_type": "hosted_on",
                },
            ]
        }

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.return_value = mock_response

            deps = await client.get_relationships(org_id=10)

            assert len(deps) == 2
            assert deps[0].id == 1
            assert deps[0].dependency_type == "depends_on"
            assert deps[0].strength == 0.95
            assert deps[1].dependency_type == "hosted_on"

    @pytest.mark.asyncio
    async def test_get_relationships_with_filters(self):
        """Test fetching relationships with source/target filters."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "dependencies": [
                {
                    "id": 1,
                    "source_entity_id": 10,
                    "target_entity_id": 20,
                    "dependency_type": "depends_on",
                }
            ]
        }

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.return_value = mock_response

            deps = await client.get_relationships(
                org_id=10,
                source_entity_id=10,
                target_entity_id=20,
            )

            assert len(deps) == 1
            mock_async_client.get.assert_called_once()
            call_kwargs = mock_async_client.get.call_args[1]
            assert call_kwargs["params"]["source_entity_id"] == 10
            assert call_kwargs["params"]["target_entity_id"] == 20

    @pytest.mark.asyncio
    async def test_get_relationships_empty(self):
        """Test handling empty dependency list."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"dependencies": []}

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.return_value = mock_response

            deps = await client.get_relationships(org_id=10)

            assert deps == []


class TestElderClientGetGraph:
    """Test fetching dependency graph from Elder API."""

    @pytest.mark.asyncio
    async def test_get_graph_success(self):
        """Test successful graph fetch."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        graph_data = {
            "entities": [
                {"id": 1, "name": "entity1"},
                {"id": 2, "name": "entity2"},
            ],
            "dependencies": [
                {"id": 1, "source": 1, "target": 2}
            ],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = graph_data

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.return_value = mock_response

            graph = await client.get_graph(org_id=10)

            assert graph == graph_data

    @pytest.mark.asyncio
    async def test_get_graph_with_entity_and_depth(self):
        """Test graph fetch with entity filter and depth."""
        client = ElderClient(
            base_url="https://elder.example.com",
            api_key="test-key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"entities": [], "dependencies": []}

        with patch("app.services.elder_service.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.get.return_value = mock_response

            await client.get_graph(org_id=10, entity_id=42, depth=3)

            call_kwargs = mock_async_client.get.call_args[1]
            assert call_kwargs["params"]["entity_id"] == 42
            assert call_kwargs["params"]["depth"] == 3


class TestEntityTypeMapping:
    """Test entity type mapping."""

    def test_entity_type_mapping_compute(self):
        """Test COMPUTE entity type mapping."""
        mapping = EntityTypeMapping.COMPUTE.value
        assert mapping["node_type"] == "rectangle"
        assert mapping["icon"] == "server"
        assert mapping["color"] == "#3B82F6"

    def test_entity_type_mapping_vpc(self):
        """Test VPC entity type mapping."""
        mapping = EntityTypeMapping.VPC.value
        assert mapping["icon"] == "network"
        assert mapping["description"] == "Virtual Private Cloud"

    def test_all_entity_types_have_required_fields(self):
        """Test that all entity type mappings have required fields."""
        required_fields = {"node_type", "icon", "color", "description"}
        for entity_type in EntityTypeMapping:
            mapping = entity_type.value
            assert required_fields.issubset(mapping.keys())


class TestMapEntityToShape:
    """Test mapping Elder entities to IceCharts shapes."""

    def test_map_entity_to_shape_known_type(self):
        """Test mapping entity with known type."""
        entity = ElderEntity(
            id=1,
            unique_id=100,
            name="web-server",
            entity_type="compute",
            description="Web server VM",
        )

        node = ElderClient.map_entity_to_shape(entity, x=100, y=200)

        assert isinstance(node, IceChartsNode)
        assert node.id == "elder_1_100"
        assert node.type == "rectangle"
        assert node.position == {"x": 100, "y": 200}
        assert node.data["label"] == "web-server"
        assert node.data["icon"] == "server"
        assert node.data["description"] == "Web server VM"
        assert node.style["backgroundColor"] == "#3B82F6"

    def test_map_entity_to_shape_unknown_type(self):
        """Test mapping entity with unknown type."""
        entity = ElderEntity(
            id=1,
            unique_id=100,
            name="unknown-resource",
            entity_type="custom_type",
        )

        node = ElderClient.map_entity_to_shape(entity)

        assert node.type == "rectangle"
        assert node.data["icon"] == "package"
        assert node.data["elder_type"] == "custom_type"

    def test_map_entity_to_shape_includes_metadata(self):
        """Test that metadata is preserved in mapped shape."""
        metadata = {"region": "us-west-2", "tags": ["prod", "critical"]}
        entity = ElderEntity(
            id=1,
            unique_id=100,
            name="db-instance",
            entity_type="datacenter",
            metadata=metadata,
        )

        node = ElderClient.map_entity_to_shape(entity)

        assert node.data["metadata"] == metadata

    def test_map_entity_to_shape_default_position(self):
        """Test that default position is 0, 0."""
        entity = ElderEntity(
            id=1,
            unique_id=100,
            name="test",
            entity_type="network",
        )

        node = ElderClient.map_entity_to_shape(entity)

        assert node.position == {"x": 0, "y": 0}


class TestMapRelationshipToConnector:
    """Test mapping Elder dependencies to IceCharts connectors."""

    def test_map_dependency_depends_on(self):
        """Test mapping depends_on dependency."""
        dep = ElderDependency(
            id=1,
            source_entity_id=10,
            target_entity_id=20,
            dependency_type="depends_on",
        )

        connector = ElderClient.map_relationship_to_connector(
            dep,
            source_node_id="elder_10_100",
            target_node_id="elder_20_200",
        )

        assert isinstance(connector, IceChartsConnector)
        assert connector.id == "elder_dep_1"
        assert connector.source == "elder_10_100"
        assert connector.target == "elder_20_200"
        assert connector.label == "depends on"
        assert connector.animated is True

    def test_map_dependency_hosted_on(self):
        """Test mapping hosted_on dependency."""
        dep = ElderDependency(
            id=1,
            source_entity_id=10,
            target_entity_id=20,
            dependency_type="hosted_on",
        )

        connector = ElderClient.map_relationship_to_connector(
            dep,
            source_node_id="elder_10_100",
            target_node_id="elder_20_200",
        )

        assert connector.label == "hosted on"
        assert connector.animated is False

    def test_map_dependency_connects_to(self):
        """Test mapping connects_to dependency."""
        dep = ElderDependency(
            id=1,
            source_entity_id=10,
            target_entity_id=20,
            dependency_type="connects_to",
        )

        connector = ElderClient.map_relationship_to_connector(
            dep,
            source_node_id="elder_10_100",
            target_node_id="elder_20_200",
        )

        assert connector.animated is True

    def test_map_dependency_with_description_and_strength(self):
        """Test mapping dependency with optional fields."""
        dep = ElderDependency(
            id=1,
            source_entity_id=10,
            target_entity_id=20,
            dependency_type="manages",
            description="Control relationship",
            strength=0.85,
        )

        connector = ElderClient.map_relationship_to_connector(
            dep,
            source_node_id="node1",
            target_node_id="node2",
        )

        assert connector.data["description"] == "Control relationship"
        assert connector.data["strength"] == 0.85


class TestCalculateLayoutPositions:
    """Test calculating layout positions for entities."""

    def test_calculate_layout_positions_empty_entities(self):
        """Test layout calculation with empty entity list."""
        positions = ElderClient.calculate_layout_positions(
            entities=[],
            dependencies=[],
        )
        assert positions == {}

    def test_calculate_layout_positions_single_entity(self):
        """Test layout with single entity."""
        entities = [
            ElderEntity(id=1, unique_id=100, name="entity1", entity_type="compute")
        ]

        positions = ElderClient.calculate_layout_positions(
            entities=entities,
            dependencies=[],
        )

        assert 1 in positions
        assert "x" in positions[1]
        assert "y" in positions[1]

    def test_calculate_layout_positions_multiple_entities(self):
        """Test layout calculation distributes entities."""
        entities = [
            ElderEntity(id=i, unique_id=100 + i, name=f"entity{i}", entity_type="compute")
            for i in range(1, 10)
        ]

        positions = ElderClient.calculate_layout_positions(
            entities=entities,
            dependencies=[],
            canvas_width=1600,
            canvas_height=900,
        )

        assert len(positions) == 9
        for entity in entities:
            assert entity.id in positions
            assert "x" in positions[entity.id]
            assert "y" in positions[entity.id]

    def test_calculate_layout_positions_within_canvas_bounds(self):
        """Test that positions are within canvas bounds."""
        entities = [
            ElderEntity(id=i, unique_id=100 + i, name=f"entity{i}", entity_type="compute")
            for i in range(1, 10)
        ]

        canvas_width = 1600
        canvas_height = 900
        positions = ElderClient.calculate_layout_positions(
            entities=entities,
            dependencies=[],
            canvas_width=canvas_width,
            canvas_height=canvas_height,
        )

        for pos in positions.values():
            assert 0 <= pos["x"] <= canvas_width
            assert 0 <= pos["y"] <= canvas_height

    def test_calculate_layout_positions_respects_dependencies(self):
        """Test that layout respects dependency structure."""
        entities = [
            ElderEntity(id=1, unique_id=100, name="root", entity_type="compute"),
            ElderEntity(id=2, unique_id=101, name="child", entity_type="compute"),
        ]
        dependencies = [
            ElderDependency(
                id=1,
                source_entity_id=1,
                target_entity_id=2,
                dependency_type="depends_on",
            )
        ]

        positions = ElderClient.calculate_layout_positions(
            entities=entities,
            dependencies=dependencies,
        )

        assert len(positions) == 2
        assert positions[1] != positions[2]


class TestIceChartsNode:
    """Test IceChartsNode dataclass."""

    def test_ice_charts_node_creation(self):
        """Test creating an IceChartsNode."""
        node = IceChartsNode(
            id="node1",
            type="rectangle",
            position={"x": 100, "y": 200},
            data={"label": "Test Node"},
        )
        assert node.id == "node1"
        assert node.type == "rectangle"
        assert node.position == {"x": 100, "y": 200}

    def test_ice_charts_node_to_dict(self):
        """Test converting IceChartsNode to dictionary."""
        node = IceChartsNode(
            id="node1",
            type="rectangle",
            position={"x": 100, "y": 200},
            data={"label": "Test"},
            style={"backgroundColor": "#fff"},
        )
        result = node.to_dict()
        assert isinstance(result, dict)
        assert result["id"] == "node1"
        assert result["position"] == {"x": 100, "y": 200}


class TestIceChartsConnector:
    """Test IceChartsConnector dataclass."""

    def test_ice_charts_connector_creation(self):
        """Test creating an IceChartsConnector."""
        connector = IceChartsConnector(
            id="conn1",
            source="node1",
            target="node2",
            label="depends on",
        )
        assert connector.id == "conn1"
        assert connector.source == "node1"
        assert connector.target == "node2"
        assert connector.type == "default"
        assert connector.animated is False

    def test_ice_charts_connector_to_dict(self):
        """Test converting IceChartsConnector to dictionary."""
        connector = IceChartsConnector(
            id="conn1",
            source="node1",
            target="node2",
            type="default",
            data={"strength": 0.9},
            animated=True,
            label="depends on",
        )
        result = connector.to_dict()
        assert isinstance(result, dict)
        assert result["id"] == "conn1"
        assert result["source"] == "node1"
        assert result["animated"] is True
        assert result["label"] == "depends on"
