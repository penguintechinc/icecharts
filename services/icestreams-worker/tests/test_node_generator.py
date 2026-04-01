#!/usr/bin/env python3
"""
Tests for the dynamic node generator (connectors/node_generator.py).

Tests cover:
- create_trigger_node: type naming, no inputs, default outputs
- create_action_node: type naming, default inputs/outputs
- create_transform_node: type naming, default inputs/outputs
- generate_nodes_from_connector: returns correct count, NodeRegistry registration
- display_name format: "ConnectorName: NodeName"
- Multiple connectors registered without collision
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.base import (
    ActionDefinition,
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


@pytest.fixture(autouse=True)
def clean_registries():
    """Clear both registries before and after each test."""
    NodeRegistry.clear()
    ConnectorRegistry.clear()
    yield
    NodeRegistry.clear()
    ConnectorRegistry.clear()


def _make_trigger(trigger_id: str = "on_event") -> TriggerDefinition:
    """Create a minimal TriggerDefinition."""
    return TriggerDefinition(
        id=trigger_id,
        name="On Event",
        description="Fires when an event occurs",
        icon="",
        webhook_path="/webhooks/test",
        outputs=(
            PortDefinition(name="out", type="object", description="Event output"),
        ),
        config_schema=(),
    )


def _make_action(action_id: str = "send_message") -> ActionDefinition:
    """Create a minimal ActionDefinition."""
    return ActionDefinition(
        id=action_id,
        name="Send Message",
        description="Sends a message",
        endpoint="/api/send",
        method="POST",
        inputs=(PortDefinition(name="in", type="any", description="Input data"),),
        outputs=(PortDefinition(name="out", type="object", description="Result"),),
        config_schema=(),
    )


def _make_transform(transform_id: str = "get_data") -> TransformDefinition:
    """Create a minimal TransformDefinition."""
    return TransformDefinition(
        id=transform_id,
        name="Get Data",
        description="Fetches data",
        endpoint="/api/data",
        method="GET",
        inputs=(PortDefinition(name="in", type="any", description="Input"),),
        outputs=(PortDefinition(name="out", type="object", description="Data"),),
        config_schema=(),
    )


def _make_manifest(
    connector_id: str = "test_conn",
    name: str = "Test Connector",
) -> ConnectorManifest:
    """Create a ConnectorManifest with one trigger, action, and transform."""
    return ConnectorManifest(
        id=connector_id,
        name=name,
        description="A test connector",
        version="1.0.0",
        vendor="test",
        triggers=(_make_trigger(),),
        actions=(_make_action(),),
        transforms=(_make_transform(),),
    )


class TestCreateTriggerNode:
    """create_trigger_node must produce correct node class."""

    def test_trigger_node_type_naming(self):
        """Trigger node_type must be 'trigger_{connector_id}_{trigger_id}'."""
        trigger = _make_trigger("on_event")
        cls = create_trigger_node("myconn", trigger, "My Connector", "#fff")
        assert cls.node_type == "trigger_myconn_on_event"

    def test_trigger_has_no_inputs(self):
        """Generated trigger node must have no input ports."""
        trigger = _make_trigger()
        cls = create_trigger_node("myconn", trigger, "My Connector", "#fff")
        assert cls.inputs() == []

    def test_trigger_has_outputs_from_manifest(self):
        """Generated trigger node must include outputs defined in manifest."""
        trigger = _make_trigger()
        cls = create_trigger_node("myconn", trigger, "My Connector", "#fff")
        outputs = cls.outputs()
        assert len(outputs) >= 1
        output_names = [o.name for o in outputs]
        assert "out" in output_names

    def test_trigger_default_output_when_none_defined(self):
        """If no outputs in manifest, must generate default 'out' output."""
        trigger = TriggerDefinition(
            id="bare_trigger",
            name="Bare Trigger",
            description="No outputs defined",
            outputs=(),
            config_schema=(),
        )
        cls = create_trigger_node("conn", trigger, "Conn", "#000")
        outputs = cls.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"

    def test_trigger_display_name_format(self):
        """Trigger name must be 'ConnectorName: TriggerName'."""
        trigger = _make_trigger()
        cls = create_trigger_node("myconn", trigger, "My Connector", "#fff")
        assert cls.name == "My Connector: On Event"

    def test_trigger_category_is_triggers(self):
        """Trigger node category must be 'triggers'."""
        trigger = _make_trigger()
        cls = create_trigger_node("myconn", trigger, "My Connector", "#fff")
        assert cls.category == "triggers"

    def test_trigger_description_from_manifest(self):
        """Trigger description must match manifest definition."""
        trigger = _make_trigger()
        cls = create_trigger_node("myconn", trigger, "My Connector", "#fff")
        assert cls.description == trigger.description

    def test_trigger_stores_connector_id(self):
        """Generated node must store connector_id_attr."""
        trigger = _make_trigger()
        cls = create_trigger_node("myconn", trigger, "My Connector", "#fff")
        assert cls.connector_id_attr == "myconn"

    def test_trigger_validate_config_empty_ok(self):
        """validate_config with no required fields should return no errors."""
        trigger = _make_trigger()
        cls = create_trigger_node("myconn", trigger, "My Connector", "#fff")
        errors = cls.validate_config({})
        assert errors == []


class TestCreateActionNode:
    """create_action_node must produce correct node class."""

    def test_action_node_type_naming(self):
        """Action node_type must be 'action_{connector_id}_{action_id}'."""
        action = _make_action("send_msg")
        cls = create_action_node("myconn", action, "My Connector", "#fff")
        assert cls.node_type == "action_myconn_send_msg"

    def test_action_has_inputs_from_manifest(self):
        """Generated action node must include inputs from manifest."""
        action = _make_action()
        cls = create_action_node("myconn", action, "My Connector", "#fff")
        inputs = cls.inputs()
        assert len(inputs) >= 1

    def test_action_has_default_input_when_none_defined(self):
        """If no inputs in manifest, must generate default 'in' input."""
        action = ActionDefinition(
            id="bare_action",
            name="Bare Action",
            description="No inputs defined",
            endpoint="/api/bare",
            method="POST",
            inputs=(),
            outputs=(),
            config_schema=(),
        )
        cls = create_action_node("conn", action, "Conn", "#000")
        inputs = cls.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "in"

    def test_action_has_outputs_from_manifest(self):
        """Generated action node must include outputs from manifest."""
        action = _make_action()
        cls = create_action_node("myconn", action, "My Connector", "#fff")
        outputs = cls.outputs()
        assert len(outputs) >= 1

    def test_action_has_default_output_when_none_defined(self):
        """If no outputs in manifest, must generate default 'out' output."""
        action = ActionDefinition(
            id="bare_action",
            name="Bare Action",
            description="No outputs",
            endpoint="/api/bare",
            method="POST",
            inputs=(),
            outputs=(),
            config_schema=(),
        )
        cls = create_action_node("conn", action, "Conn", "#000")
        outputs = cls.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"

    def test_action_display_name_format(self):
        """Action name must be 'ConnectorName: ActionName'."""
        action = _make_action()
        cls = create_action_node("myconn", action, "My Connector", "#fff")
        assert cls.name == "My Connector: Send Message"

    def test_action_category_is_actions(self):
        """Action node category must be 'actions'."""
        action = _make_action()
        cls = create_action_node("myconn", action, "My Connector", "#fff")
        assert cls.category == "actions"

    def test_action_stores_endpoint(self):
        """Generated action node must store action endpoint."""
        action = _make_action()
        cls = create_action_node("myconn", action, "My Connector", "#fff")
        assert cls.action_endpoint == "/api/send"

    def test_action_stores_method(self):
        """Generated action node must store HTTP method."""
        action = _make_action()
        cls = create_action_node("myconn", action, "My Connector", "#fff")
        assert cls.action_method == "POST"


class TestCreateTransformNode:
    """create_transform_node must produce correct node class."""

    def test_transform_node_type_naming(self):
        """Transform node_type must be 'transform_{connector_id}_{transform_id}'."""
        transform = _make_transform("get_data")
        cls = create_transform_node("myconn", transform, "My Connector", "#fff")
        assert cls.node_type == "transform_myconn_get_data"

    def test_transform_has_inputs_from_manifest(self):
        """Generated transform node must include inputs from manifest."""
        transform = _make_transform()
        cls = create_transform_node("myconn", transform, "My Connector", "#fff")
        inputs = cls.inputs()
        assert len(inputs) >= 1

    def test_transform_has_default_input_when_none_defined(self):
        """If no inputs in manifest, must generate default 'in' input."""
        transform = TransformDefinition(
            id="bare_transform",
            name="Bare Transform",
            description="No inputs defined",
            inputs=(),
            outputs=(),
            config_schema=(),
        )
        cls = create_transform_node("conn", transform, "Conn", "#000")
        inputs = cls.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "in"

    def test_transform_display_name_format(self):
        """Transform name must be 'ConnectorName: TransformName'."""
        transform = _make_transform()
        cls = create_transform_node("myconn", transform, "My Connector", "#fff")
        assert cls.name == "My Connector: Get Data"

    def test_transform_category_is_transforms(self):
        """Transform node category must be 'transforms'."""
        transform = _make_transform()
        cls = create_transform_node("myconn", transform, "My Connector", "#fff")
        assert cls.category == "transforms"

    def test_transform_stores_endpoint(self):
        """Generated transform node must store transform endpoint."""
        transform = _make_transform()
        cls = create_transform_node("myconn", transform, "My Connector", "#fff")
        assert cls.transform_endpoint == "/api/data"


class TestGenerateNodesFromConnector:
    """generate_nodes_from_connector must register nodes and return correct count."""

    def test_generates_correct_count(self):
        """Should return count = triggers + actions + transforms."""
        manifest = _make_manifest()
        count = generate_nodes_from_connector(manifest)
        # 1 trigger + 1 action + 1 transform
        assert count == 3

    def test_registers_trigger_in_node_registry(self):
        """Trigger node must be registered in NodeRegistry."""
        manifest = _make_manifest("reg_conn")
        generate_nodes_from_connector(manifest)
        expected_type = "trigger_reg_conn_on_event"
        assert NodeRegistry.is_registered(expected_type)

    def test_registers_action_in_node_registry(self):
        """Action node must be registered in NodeRegistry."""
        manifest = _make_manifest("reg_conn2")
        generate_nodes_from_connector(manifest)
        expected_type = "action_reg_conn2_send_message"
        assert NodeRegistry.is_registered(expected_type)

    def test_registers_transform_in_node_registry(self):
        """Transform node must be registered in NodeRegistry."""
        manifest = _make_manifest("reg_conn3")
        generate_nodes_from_connector(manifest)
        expected_type = "transform_reg_conn3_get_data"
        assert NodeRegistry.is_registered(expected_type)

    def test_returns_zero_for_empty_manifest(self):
        """Manifest with no triggers/actions/transforms should return 0."""
        manifest = ConnectorManifest(
            id="empty_conn",
            name="Empty Connector",
            description="No nodes",
            version="1.0.0",
            vendor="test",
        )
        count = generate_nodes_from_connector(manifest)
        assert count == 0

    def test_multiple_connectors_no_collision(self):
        """Generating nodes for multiple connectors must not cause collisions."""
        m1 = _make_manifest("conn_a", "Connector A")
        m2 = ConnectorManifest(
            id="conn_b",
            name="Connector B",
            description="Second connector",
            version="1.0.0",
            vendor="test",
            triggers=(
                TriggerDefinition(
                    id="fire",
                    name="Fire",
                    description="Fires",
                    outputs=(
                        PortDefinition(name="out", type="any", description="Output"),
                    ),
                    config_schema=(),
                ),
            ),
            actions=(),
            transforms=(),
        )
        count1 = generate_nodes_from_connector(m1)
        count2 = generate_nodes_from_connector(m2)
        assert count1 == 3
        assert count2 == 1

        # Verify both are registered distinctly
        assert NodeRegistry.is_registered("trigger_conn_a_on_event")
        assert NodeRegistry.is_registered("trigger_conn_b_fire")

    def test_node_registry_display_name_set(self):
        """NodeRegistry entry must have a display_name set."""
        manifest = _make_manifest("disp_conn")
        generate_nodes_from_connector(manifest)
        info = NodeRegistry.get_info("trigger_disp_conn_on_event")
        assert info is not None
        assert info.display_name  # non-empty
