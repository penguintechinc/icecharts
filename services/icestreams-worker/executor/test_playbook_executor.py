#!/usr/bin/env python3
"""
Simple test for PlaybookExecutor to verify functionality.

This is a basic smoke test that ensures the executor can process
a simple playbook graph.
"""

import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from executor import (BaseNode, ExecutionResult, NodeContext, NodeData,
                      NodeRegistry, PlaybookExecutor)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestTransformNode(BaseNode):
    """Simple test transform node that doubles the input value."""

    async def execute(self, inputs):
        """Double the input value."""
        logger.info(f"TestTransformNode executing with inputs: {inputs}")

        if "default" in inputs:
            input_data = inputs["default"]
            result_value = input_data.data.get("value", 0) * 2

            output = NodeData(
                data={"value": result_value, "transformed": True},
                source_node_id=self.context.node_id,
            )
            return {"default": output}

        return {}


class TestOutputNode(BaseNode):
    """Simple test output node that logs the result."""

    async def execute(self, inputs):
        """Log the input data."""
        logger.info(f"TestOutputNode executing with inputs: {inputs}")

        if "default" in inputs:
            input_data = inputs["default"]
            logger.info(f"Output: {input_data.data}")

        return {}


class TestTriggerNode(BaseNode):
    """Simple test trigger node that generates initial data."""

    async def execute(self, inputs):
        """Generate initial data from config."""
        logger.info(f"TestTriggerNode executing")

        # Create output with initial data
        output = NodeData(
            data={"value": 5, "triggered": True},
            source_node_id=self.context.node_id,
        )
        return {"default": output}


async def test_simple_playbook():
    """Test a simple playbook with trigger -> transform -> output."""
    # Register test nodes
    NodeRegistry.register("trigger_manual", TestTriggerNode, "trigger")
    NodeRegistry.register("test_transform", TestTransformNode, "transform")
    NodeRegistry.register("test_output", TestOutputNode, "action")

    # Create mock Redis client
    redis_client = MagicMock()

    # Create executor
    executor = PlaybookExecutor(
        redis_client=redis_client,
        execution_id="test-exec-1",
        playbook_id="test-playbook-1",
        node_timeout_seconds=5.0,
    )

    # Define playbook data
    playbook_data = {
        "nodes": [
            {
                "id": "trigger-1",
                "type": "trigger_manual",
                "data": {"label": "Manual Trigger", "category": "triggers"},
            },
            {
                "id": "transform-1",
                "type": "test_transform",
                "data": {"label": "Double Value", "category": "transforms"},
            },
            {
                "id": "output-1",
                "type": "test_output",
                "data": {"label": "Output Result", "category": "actions"},
            },
        ],
        "edges": [
            {"source": "trigger-1", "target": "transform-1"},
            {"source": "transform-1", "target": "output-1"},
        ],
        "trigger_output": {"value": 5},
        "config": {},
    }

    # Execute playbook
    result = await executor.execute(playbook_data)

    # Verify results
    logger.info(f"Execution result: {result.to_dict()}")
    assert result.success, f"Execution failed: {result.error}"
    assert len(result.completed_nodes) == 3, "Expected 3 completed nodes"
    assert len(result.failed_nodes) == 0, "Expected no failed nodes"
    logger.info("Test passed!")


async def test_conditional_branching():
    """Test conditional branching with multiple output handles."""

    class ConditionalNode(BaseNode):
        """Node that outputs to different handles based on input value."""

        async def execute(self, inputs):
            if "default" not in inputs:
                return {}

            input_data = inputs["default"]
            value = input_data.data.get("value", 0)

            output_data = NodeData(
                data={"value": value, "condition_met": value > 10},
                source_node_id=self.context.node_id,
            )

            # Route to different handle based on value
            if value > 10:
                return {"true": output_data}
            else:
                return {"false": output_data}

    # Register conditional node
    NodeRegistry.register("test_conditional", ConditionalNode, "conditional")

    redis_client = MagicMock()
    executor = PlaybookExecutor(
        redis_client=redis_client,
        execution_id="test-exec-2",
        playbook_id="test-playbook-2",
    )

    playbook_data = {
        "nodes": [
            {
                "id": "trigger-1",
                "type": "trigger_manual",
                "data": {"category": "triggers"},
            },
            {
                "id": "conditional-1",
                "type": "test_conditional",
                "data": {"category": "conditionals"},
            },
            {
                "id": "output-true",
                "type": "test_output",
                "data": {"category": "actions"},
            },
            {
                "id": "output-false",
                "type": "test_output",
                "data": {"category": "actions"},
            },
        ],
        "edges": [
            {"source": "trigger-1", "target": "conditional-1"},
            {
                "source": "conditional-1",
                "sourceHandle": "true",
                "target": "output-true",
            },
            {
                "source": "conditional-1",
                "sourceHandle": "false",
                "target": "output-false",
            },
        ],
        "trigger_output": {"value": 15},
        "config": {},
    }

    result = await executor.execute(playbook_data)
    logger.info(f"Conditional test result: {result.to_dict()}")
    assert result.success, f"Execution failed: {result.error}"
    logger.info("Conditional test passed!")


async def main():
    """Run all tests."""
    logger.info("Starting PlaybookExecutor tests...")

    try:
        await test_simple_playbook()
        await test_conditional_branching()
        logger.info("\nAll tests passed!")
    except AssertionError as e:
        logger.error(f"Test failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
