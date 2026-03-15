#!/usr/bin/env python3
"""
Additional tests for node_generator error handling and edge cases.

Tests cover:
- Generated node config validation
- Default inputs/outputs when not specified
- Node type naming and display names
- Trigger execution with trigger_data context
- Multiple outputs and event type routing
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.base import (
    ActionDefinition,
    ConfigField,
    ConnectorManifest,
    PortDefinition,
    TransformDefinition,
    TriggerDefinition,
)
from connectors.node_generator import (
    create_action_node,
    create_transform_node,
    create_trigger_node,
    generate_nodes_from_connector,
)
from executor.node_registry import NodeRegistry
from connectors.registry import ConnectorRegistry
from nodes.base import NodeContext


@pytest.fixture(autouse=True)
def clean_registries():
    """Clear both registries before and after each test."""
    NodeRegistry.clear()
    ConnectorRegistry.clear()
    yield
    NodeRegistry.clear()
    ConnectorRegistry.clear()


class TestGeneratedNodeConfigValidation:
    """Tests for generated node config validation."""

    def test_trigger_node_validate_config_missing_required_field(self):
        """Trigger validate_config returns error for missing required field."""
        required_field = ConfigField(
            field="api_key",
            type="string",
            label="API Key",
            description="API Key",
            required=True,
            supports_variables=False,
        )

        trigger = TriggerDefinition(
            id="on_event",
            name="On Event",
            description="Webhook trigger",
            icon="webhook",
            webhook_path="/webhooks/event",
            outputs=(PortDefinition(name="out", type="object", description="Event"),),
            config_schema=(required_field,),
        )

        node_class = create_trigger_node(
            connector_id="test",
            trigger=trigger,
            connector_name="Test",
            connector_color="blue",
        )

        errors = node_class.validate_config({})
        assert len(errors) > 0
        assert any("api_key" in err for err in errors)

    def test_action_node_validate_config_missing_required_field(self):
        """Action validate_config returns error for missing required field."""
        required_field = ConfigField(
            field="endpoint",
            type="string",
            label="Endpoint",
            description="API Endpoint",
            required=True,
            supports_variables=False,
        )

        action = ActionDefinition(
            id="call_api",
            name="Call API",
            description="Makes API call",
            endpoint="/api/call",
            method="POST",
            inputs=(PortDefinition(name="in", type="any", description="Input"),),
            outputs=(PortDefinition(name="out", type="object", description="Result"),),
            config_schema=(required_field,),
        )

        node_class = create_action_node(
            connector_id="test",
            action=action,
            connector_name="Test",
            connector_color="blue",
        )

        errors = node_class.validate_config({})
        assert len(errors) > 0
        assert any("endpoint" in err for err in errors)

    def test_transform_node_validate_config_multiple_missing_fields(self):
        """Transform validate_config handles multiple missing fields."""
        field1 = ConfigField(
            field="query",
            type="string",
            label="Search Query",
            description="Search Query",
            required=True,
            supports_variables=False,
        )
        field2 = ConfigField(
            field="limit",
            type="number",
            label="Result Limit",
            description="Result Limit",
            required=True,
            supports_variables=False,
        )

        transform = TransformDefinition(
            id="search",
            name="Search",
            description="Searches data",
            endpoint="/api/search",
            method="GET",
            inputs=(PortDefinition(name="in", type="any", description="Input"),),
            outputs=(PortDefinition(name="out", type="object", description="Results"),),
            config_schema=(field1, field2),
        )

        node_class = create_transform_node(
            connector_id="test",
            transform=transform,
            connector_name="Test",
            connector_color="blue",
        )

        errors = node_class.validate_config({})
        assert len(errors) == 2

    def test_action_node_validate_config_with_all_fields_present(self):
        """Action validate_config returns no errors when all required fields present."""
        required_field = ConfigField(
            field="api_key",
            type="string",
            label="API Key",
            description="API Key",
            required=True,
            supports_variables=False,
        )

        action = ActionDefinition(
            id="call_api",
            name="Call API",
            description="Makes API call",
            endpoint="/api/call",
            method="POST",
            inputs=(PortDefinition(name="in", type="any", description="Input"),),
            outputs=(PortDefinition(name="out", type="object", description="Result"),),
            config_schema=(required_field,),
        )

        node_class = create_action_node(
            connector_id="test",
            action=action,
            connector_name="Test",
            connector_color="blue",
        )

        errors = node_class.validate_config({"api_key": "secret123"})
        assert len(errors) == 0


class TestGeneratedNodeDefaults:
    """Tests for generated node defaults when not explicitly specified."""

    def test_trigger_node_has_default_output_when_none_specified(self):
        """Trigger with no outputs gets default 'out' output."""
        trigger = TriggerDefinition(
            id="on_event",
            name="On Event",
            description="Trigger",
            icon="webhook",
            webhook_path="/webhooks",
            outputs=(),  # Empty outputs
            config_schema=(),
        )

        node_class = create_trigger_node(
            connector_id="test",
            trigger=trigger,
            connector_name="Test",
            connector_color="blue",
        )

        outputs = node_class.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"

    def test_action_node_has_default_inputs_when_none_specified(self):
        """Action with no inputs gets default 'in' input."""
        action = ActionDefinition(
            id="call_api",
            name="Call API",
            description="API call",
            endpoint="/api/call",
            method="POST",
            inputs=(),  # Empty inputs
            outputs=(PortDefinition(name="out", type="object", description="Result"),),
            config_schema=(),
        )

        node_class = create_action_node(
            connector_id="test",
            action=action,
            connector_name="Test",
            connector_color="blue",
        )

        inputs_list = node_class.inputs()
        assert len(inputs_list) == 1
        assert inputs_list[0].name == "in"

    def test_action_node_has_default_output_when_none_specified(self):
        """Action with no outputs gets default 'out' output."""
        action = ActionDefinition(
            id="call_api",
            name="Call API",
            description="API call",
            endpoint="/api/call",
            method="POST",
            inputs=(PortDefinition(name="in", type="any", description="Input"),),
            outputs=(),  # Empty outputs
            config_schema=(),
        )

        node_class = create_action_node(
            connector_id="test",
            action=action,
            connector_name="Test",
            connector_color="blue",
        )

        outputs = node_class.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"

    def test_transform_node_has_default_input_when_none_specified(self):
        """Transform with no inputs gets default 'in' input."""
        transform = TransformDefinition(
            id="lookup",
            name="Lookup",
            description="Lookup",
            endpoint="/api/lookup",
            method="GET",
            inputs=(),  # Empty inputs
            outputs=(PortDefinition(name="out", type="object", description="Result"),),
            config_schema=(),
        )

        node_class = create_transform_node(
            connector_id="test",
            transform=transform,
            connector_name="Test",
            connector_color="blue",
        )

        inputs_list = node_class.inputs()
        assert len(inputs_list) == 1
        assert inputs_list[0].name == "in"

    def test_transform_node_has_default_output_when_none_specified(self):
        """Transform with no outputs gets default 'out' output."""
        transform = TransformDefinition(
            id="lookup",
            name="Lookup",
            description="Lookup",
            endpoint="/api/lookup",
            method="GET",
            inputs=(PortDefinition(name="in", type="any", description="Input"),),
            outputs=(),  # Empty outputs
            config_schema=(),
        )

        node_class = create_transform_node(
            connector_id="test",
            transform=transform,
            connector_name="Test",
            connector_color="blue",
        )

        outputs = node_class.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"


class TestGeneratedNodeNaming:
    """Tests for node type naming and display names."""

    def test_trigger_node_type_includes_connector_id(self):
        """Trigger node type includes connector ID."""
        trigger = TriggerDefinition(
            id="on_event",
            name="On Event",
            description="Trigger",
            icon="webhook",
            webhook_path="/webhooks",
            outputs=(PortDefinition(name="out", type="object", description="Event"),),
            config_schema=(),
        )

        node_class = create_trigger_node(
            connector_id="myconnector",
            trigger=trigger,
            connector_name="My Connector",
            connector_color="blue",
        )

        assert "myconnector" in node_class.node_type
        assert "trigger" in node_class.node_type

    def test_action_node_type_includes_connector_id_and_action_id(self):
        """Action node type includes connector ID and action ID."""
        action = ActionDefinition(
            id="send_message",
            name="Send Message",
            description="API call",
            endpoint="/api/send",
            method="POST",
            inputs=(PortDefinition(name="in", type="any", description="Input"),),
            outputs=(PortDefinition(name="out", type="object", description="Result"),),
            config_schema=(),
        )

        node_class = create_action_node(
            connector_id="slack",
            action=action,
            connector_name="Slack",
            connector_color="blue",
        )

        assert "slack" in node_class.node_type
        assert "send_message" in node_class.node_type
        assert "action" in node_class.node_type

    def test_trigger_display_name_format(self):
        """Trigger display name follows 'ConnectorName: TriggerName' format."""
        trigger = TriggerDefinition(
            id="on_event",
            name="On Event",
            description="Trigger",
            icon="webhook",
            webhook_path="/webhooks",
            outputs=(PortDefinition(name="out", type="object", description="Event"),),
            config_schema=(),
        )

        node_class = create_trigger_node(
            connector_id="test",
            trigger=trigger,
            connector_name="Test Connector",
            connector_color="blue",
        )

        assert node_class.name == "Test Connector: On Event"

    def test_action_display_name_format(self):
        """Action display name follows 'ConnectorName: ActionName' format."""
        action = ActionDefinition(
            id="call_api",
            name="Call API",
            description="API call",
            endpoint="/api/call",
            method="POST",
            inputs=(PortDefinition(name="in", type="any", description="Input"),),
            outputs=(PortDefinition(name="out", type="object", description="Result"),),
            config_schema=(),
        )

        node_class = create_action_node(
            connector_id="test",
            action=action,
            connector_name="Test Connector",
            connector_color="blue",
        )

        assert node_class.name == "Test Connector: Call API"

    def test_trigger_node_description_from_manifest(self):
        """Trigger node description comes from manifest."""
        trigger = TriggerDefinition(
            id="on_event",
            name="On Event",
            description="Fires when webhook is called",
            icon="webhook",
            webhook_path="/webhooks",
            outputs=(PortDefinition(name="out", type="object", description="Event"),),
            config_schema=(),
        )

        node_class = create_trigger_node(
            connector_id="test",
            trigger=trigger,
            connector_name="Test",
            connector_color="blue",
        )

        assert node_class.description == "Fires when webhook is called"


class TestGenerateNodesErrorHandling:
    """Tests for generate_nodes_from_connector error handling."""

    def test_generate_nodes_logs_error_for_invalid_trigger(self):
        """generate_nodes_from_connector logs error for invalid trigger definition."""
        trigger = TriggerDefinition(
            id="on_event",
            name="On Event",
            description="Trigger",
            icon="",
            webhook_path="/webhooks",
            outputs=(PortDefinition(name="out", type="object", description="Output"),),
            config_schema=(),
        )

        manifest = ConnectorManifest(
            id="badconn",
            name="Bad Connector",
            description="Has issues",
            version="1.0.0",
            vendor="test",
            auth_methods=(),
            triggers=(trigger,),
            actions=(),
            transforms=(),
        )

        with patch(
            "connectors.node_generator.create_trigger_node"
        ) as mock_create:
            mock_create.side_effect = ValueError("Invalid definition")

            with patch("connectors.node_generator.logger") as mock_logger:
                count = generate_nodes_from_connector(manifest)

                # Should log error but not raise
                mock_logger.error.assert_called()
                assert count == 0

    def test_generate_nodes_continues_on_action_error(self):
        """generate_nodes_from_connector continues when action fails."""
        trigger = TriggerDefinition(
            id="on_event",
            name="On Event",
            description="Trigger",
            icon="",
            webhook_path="/webhooks",
            outputs=(PortDefinition(name="out", type="object", description="Output"),),
            config_schema=(),
        )

        action = ActionDefinition(
            id="do_action",
            name="Do Action",
            description="Action",
            endpoint="/api/action",
            method="POST",
            inputs=(PortDefinition(name="in", type="any", description="Input"),),
            outputs=(PortDefinition(name="out", type="object", description="Output"),),
            config_schema=(),
        )

        manifest = ConnectorManifest(
            id="mixedconn",
            name="Mixed Connector",
            description="Mixed",
            version="1.0.0",
            vendor="test",
            auth_methods=(),
            triggers=(trigger,),
            actions=(action,),
            transforms=(),
        )

        with patch(
            "connectors.node_generator.create_action_node"
        ) as mock_create_action:
            mock_create_action.side_effect = RuntimeError("Action definition invalid")

            with patch("connectors.node_generator.logger"):
                # Should still generate trigger even if action fails
                count = generate_nodes_from_connector(manifest)

                # Should have generated 1 (trigger), action generation failed
                assert count == 1

    def test_generate_nodes_returns_zero_for_empty_manifest(self):
        """generate_nodes_from_connector returns 0 for empty manifest."""
        manifest = ConnectorManifest(
            id="empty",
            name="Empty",
            description="Empty",
            version="1.0.0",
            vendor="test",
            auth_methods=(),
            triggers=(),
            actions=(),
            transforms=(),
        )

        count = generate_nodes_from_connector(manifest)
        assert count == 0

    def test_generate_nodes_registers_in_node_registry(self):
        """Nodes are registered in NodeRegistry when generated."""
        trigger = TriggerDefinition(
            id="on_event",
            name="On Event",
            description="Trigger",
            icon="webhook",
            webhook_path="/webhooks",
            outputs=(PortDefinition(name="out", type="object", description="Output"),),
            config_schema=(),
        )

        manifest = ConnectorManifest(
            id="testconn",
            name="Test",
            description="Test",
            version="1.0.0",
            vendor="test",
            auth_methods=(),
            triggers=(trigger,),
            actions=(),
            transforms=(),
        )

        count = generate_nodes_from_connector(manifest)

        assert count == 1
        # Verify node was registered (check that get returns something)
        node_type = f"trigger_testconn_on_event"
        registered = NodeRegistry.get(node_type)
        assert registered is not None
