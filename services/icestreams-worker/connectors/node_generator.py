"""
Dynamic node generator for IceCharts Connector Framework.

This module generates BaseNode subclasses at runtime from connector manifests,
allowing new connectors to be added without writing Python code.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Type

from nodes.base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from executor.node_registry import NodeRegistry

from .base import (
    ActionDefinition,
    ConnectorManifest,
    PortDefinition,
    TransformDefinition,
    TriggerDefinition,
)

logger = logging.getLogger(__name__)


def _port_to_node_input(port: PortDefinition) -> NodeInput:
    """Convert PortDefinition to NodeInput."""
    return NodeInput(
        name=port.name,
        description=port.description,
        required=port.required,
        data_type=port.type,
    )


def _port_to_node_output(port: PortDefinition) -> NodeOutput:
    """Convert PortDefinition to NodeOutput."""
    return NodeOutput(
        name=port.name,
        description=port.description,
        data_type=port.type,
    )


def create_trigger_node(
    connector_id: str,
    trigger: TriggerDefinition,
    connector_name: str,
    connector_color: str,
) -> Type[BaseNode]:
    """
    Generate a trigger node class from manifest definition.

    Args:
        connector_id: Connector identifier.
        trigger: Trigger definition from manifest.
        connector_name: Display name of connector.
        connector_color: UI color for connector.

    Returns:
        Generated BaseNode subclass.
    """
    _node_type = f"trigger_{connector_id}_{trigger.id}"
    display_name = f"{connector_name}: {trigger.name}"

    # Pre-compute outputs
    _outputs = [_port_to_node_output(p) for p in trigger.outputs]
    if not _outputs:
        # Default output if none specified
        _outputs = [
            NodeOutput(name="out", description="Trigger output", data_type="any")
        ]

    # Pre-compute config schema for validation
    required_fields = [f.field for f in trigger.config_schema if f.required]

    class GeneratedTriggerNode(BaseNode):
        """Dynamically generated trigger node."""

        node_type = _node_type
        name = display_name
        description = trigger.description
        category = "triggers"

        # Store connector info for UI
        connector_id_attr = connector_id
        connector_name_attr = connector_name
        connector_color_attr = connector_color
        trigger_icon = trigger.icon
        config_schema_attr = trigger.config_schema

        @classmethod
        def inputs(cls) -> List[NodeInput]:
            """Triggers don't have inputs - they start workflows."""
            return []

        @classmethod
        def outputs(cls) -> List[NodeOutput]:
            return _outputs

        @classmethod
        def validate_config(cls, config: Dict[str, Any]) -> List[str]:
            errors = []
            for field_name in required_fields:
                if not config.get(field_name):
                    errors.append(f"Required field '{field_name}' is missing")
            return errors

        async def execute(
            self, context: NodeContext, inputs: Dict[str, Any]
        ) -> NodeResult:
            """
            Execute trigger node.

            For triggers, this is called with the incoming webhook/event data.
            The data is passed through to outputs.
            """
            import time

            start_time = time.perf_counter()

            # Get trigger data from context variables (set by webhook handler)
            trigger_data = context.variables.get("trigger_data", {})

            # Route data to appropriate outputs based on event type
            output_data = {"out": trigger_data}

            # For event triggers with multiple outputs, route by event type
            if len(_outputs) > 1 and "event_type" in trigger_data:
                event_type = trigger_data.get("event_type", "other")
                output_data = {event_type: trigger_data, "out": trigger_data}

            context.log_info(f"Trigger {trigger.name} fired")

            return NodeResult.success_result(
                outputs=output_data,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    # Set unique class name
    GeneratedTriggerNode.__name__ = (
        f"{connector_name.replace(' ', '')}_{trigger.id}_Trigger"
    )

    return GeneratedTriggerNode


def create_action_node(
    connector_id: str,
    action: ActionDefinition,
    connector_name: str,
    connector_color: str,
) -> Type[BaseNode]:
    """
    Generate an action node class from manifest definition.

    Args:
        connector_id: Connector identifier.
        action: Action definition from manifest.
        connector_name: Display name of connector.
        connector_color: UI color for connector.

    Returns:
        Generated BaseNode subclass.
    """
    _node_type = f"action_{connector_id}_{action.id}"
    display_name = f"{connector_name}: {action.name}"

    # Pre-compute inputs and outputs
    inputs_list = [_port_to_node_input(p) for p in action.inputs]
    if not inputs_list:
        # Default input if none specified
        inputs_list = [NodeInput(name="in", description="Input data", required=True)]

    outputs_list = [_port_to_node_output(p) for p in action.outputs]
    if not outputs_list:
        # Default output if none specified
        outputs_list = [
            NodeOutput(name="out", description="Action result", data_type="object")
        ]

    # Pre-compute config schema for validation
    required_fields = [f.field for f in action.config_schema if f.required]

    class GeneratedActionNode(BaseNode):
        """Dynamically generated action node."""

        node_type = _node_type
        name = display_name
        description = action.description
        category = "actions"

        # Store connector info
        connector_id_attr = connector_id
        connector_name_attr = connector_name
        connector_color_attr = connector_color
        action_icon = action.icon
        action_endpoint = action.endpoint
        action_method = action.method
        config_schema_attr = action.config_schema

        @classmethod
        def inputs(cls) -> List[NodeInput]:
            return inputs_list

        @classmethod
        def outputs(cls) -> List[NodeOutput]:
            return outputs_list

        @classmethod
        def validate_config(cls, config: Dict[str, Any]) -> List[str]:
            errors = []
            for field_name in required_fields:
                if not config.get(field_name):
                    errors.append(f"Required field '{field_name}' is missing")
            return errors

        async def execute(
            self, context: NodeContext, inputs: Dict[str, Any]
        ) -> NodeResult:
            """Execute action by calling connector API."""
            import time

            start_time = time.perf_counter()

            try:
                # Import here to avoid circular imports
                from .executor import ConnectorActionExecutor

                executor = ConnectorActionExecutor()
                result = await executor.execute_action(
                    connector_id=connector_id,
                    action_id=action.id,
                    config=context.config,
                    inputs=inputs,
                    variables=context.variables,
                )

                context.log_info(f"Action {action.name} completed")

                return NodeResult.success_result(
                    outputs={"out": result},
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            except Exception as e:
                context.log_error(f"Action {action.name} failed: {e}")
                return NodeResult.failure_result(
                    error=str(e),
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

    GeneratedActionNode.__name__ = (
        f"{connector_name.replace(' ', '')}_{action.id}_Action"
    )

    return GeneratedActionNode


def create_transform_node(
    connector_id: str,
    transform: TransformDefinition,
    connector_name: str,
    connector_color: str,
) -> Type[BaseNode]:
    """
    Generate a transform node class from manifest definition.

    Args:
        connector_id: Connector identifier.
        transform: Transform definition from manifest.
        connector_name: Display name of connector.
        connector_color: UI color for connector.

    Returns:
        Generated BaseNode subclass.
    """
    _node_type = f"transform_{connector_id}_{transform.id}"
    display_name = f"{connector_name}: {transform.name}"

    # Pre-compute inputs and outputs
    inputs_list = [_port_to_node_input(p) for p in transform.inputs]
    if not inputs_list:
        inputs_list = [NodeInput(name="in", description="Input data", required=True)]

    outputs_list = [_port_to_node_output(p) for p in transform.outputs]
    if not outputs_list:
        outputs_list = [
            NodeOutput(name="out", description="Transform result", data_type="any")
        ]

    required_fields = [f.field for f in transform.config_schema if f.required]

    class GeneratedTransformNode(BaseNode):
        """Dynamically generated transform node."""

        node_type = _node_type
        name = display_name
        description = transform.description
        category = "transforms"

        connector_id_attr = connector_id
        connector_name_attr = connector_name
        connector_color_attr = connector_color
        transform_icon = transform.icon
        transform_endpoint = transform.endpoint
        transform_method = transform.method
        config_schema_attr = transform.config_schema

        @classmethod
        def inputs(cls) -> List[NodeInput]:
            return inputs_list

        @classmethod
        def outputs(cls) -> List[NodeOutput]:
            return outputs_list

        @classmethod
        def validate_config(cls, config: Dict[str, Any]) -> List[str]:
            errors = []
            for field_name in required_fields:
                if not config.get(field_name):
                    errors.append(f"Required field '{field_name}' is missing")
            return errors

        async def execute(
            self, context: NodeContext, inputs: Dict[str, Any]
        ) -> NodeResult:
            """Execute transform by calling connector API if endpoint exists."""
            import time

            start_time = time.perf_counter()

            try:
                if transform.endpoint:
                    # Call API for data lookup/transformation
                    from .executor import ConnectorActionExecutor

                    executor = ConnectorActionExecutor()
                    result = await executor.execute_transform(
                        connector_id=connector_id,
                        transform_id=transform.id,
                        config=context.config,
                        inputs=inputs,
                        variables=context.variables,
                    )
                else:
                    # Pass-through transform (no API call)
                    result = inputs.get("in", {})

                context.log_info(f"Transform {transform.name} completed")

                return NodeResult.success_result(
                    outputs={"out": result},
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            except Exception as e:
                context.log_error(f"Transform {transform.name} failed: {e}")
                return NodeResult.failure_result(
                    error=str(e),
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

    GeneratedTransformNode.__name__ = (
        f"{connector_name.replace(' ', '')}_{transform.id}_Transform"
    )

    return GeneratedTransformNode


def generate_nodes_from_connector(manifest: ConnectorManifest) -> int:
    """
    Generate and register all nodes from a connector manifest.

    Args:
        manifest: Parsed connector manifest.

    Returns:
        Number of nodes generated.
    """
    generated = 0

    # Generate trigger nodes
    for trigger in manifest.triggers:
        try:
            node_class = create_trigger_node(
                connector_id=manifest.id,
                trigger=trigger,
                connector_name=manifest.name,
                connector_color=manifest.color,
            )
            NodeRegistry.register(
                node_type=node_class.node_type,
                node_class=node_class,
                category="triggers",
                display_name=node_class.name,
                description=node_class.description,
            )
            generated += 1
            logger.debug(f"Generated trigger node: {node_class.node_type}")
        except Exception as e:
            logger.error(f"Failed to generate trigger {trigger.id}: {e}")

    # Generate action nodes
    for action in manifest.actions:
        try:
            node_class = create_action_node(
                connector_id=manifest.id,
                action=action,
                connector_name=manifest.name,
                connector_color=manifest.color,
            )
            NodeRegistry.register(
                node_type=node_class.node_type,
                node_class=node_class,
                category="actions",
                display_name=node_class.name,
                description=node_class.description,
            )
            generated += 1
            logger.debug(f"Generated action node: {node_class.node_type}")
        except Exception as e:
            logger.error(f"Failed to generate action {action.id}: {e}")

    # Generate transform nodes
    for transform in manifest.transforms:
        try:
            node_class = create_transform_node(
                connector_id=manifest.id,
                transform=transform,
                connector_name=manifest.name,
                connector_color=manifest.color,
            )
            NodeRegistry.register(
                node_type=node_class.node_type,
                node_class=node_class,
                category="transforms",
                display_name=node_class.name,
                description=node_class.description,
            )
            generated += 1
            logger.debug(f"Generated transform node: {node_class.node_type}")
        except Exception as e:
            logger.error(f"Failed to generate transform {transform.id}: {e}")

    logger.info(
        f"Generated {generated} nodes from connector {manifest.id}: "
        f"{len(manifest.triggers)} triggers, "
        f"{len(manifest.actions)} actions, "
        f"{len(manifest.transforms)} transforms"
    )

    return generated
