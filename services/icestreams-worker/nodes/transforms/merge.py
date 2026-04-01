"""
Merge Transform node for IceStreams workflow system.

Combines multiple input sources into a single output using various merge strategies.
Supports shallow object merge, deep merge, array concatenation, and string concatenation.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


@register_node("transform_merge", "transforms", "Merge")
class MergeTransform(BaseNode):
    """Merge multiple inputs into a single output."""

    node_type = "transform_merge"
    name = "Merge"
    description = "Combine multiple data sources into one output"
    category = "transforms"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for merge node."""
        return [
            NodeInput(
                name="in1", description="First input", required=True, data_type="any"
            ),
            NodeInput(
                name="in2", description="Second input", required=False, data_type="any"
            ),
            NodeInput(
                name="in3",
                description="Third input (optional)",
                required=False,
                data_type="any",
            ),
            NodeInput(
                name="in4",
                description="Fourth input (optional)",
                required=False,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for merge node."""
        return [
            NodeOutput(name="out", description="Merged output", data_type="any"),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate merge node configuration."""
        errors = []

        mode = config.get("mode", "object")
        valid_modes = {"object", "array", "concat", "deep"}
        if mode not in valid_modes:
            errors.append(
                f"Invalid mode: {mode}. Valid modes: {', '.join(sorted(valid_modes))}"
            )

        # Validate separator for concat mode
        if mode == "concat":
            separator = config.get("separator", "")
            if not isinstance(separator, str):
                errors.append("separator must be a string when using concat mode")

        return errors

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge two dictionaries with override taking precedence."""
        result = dict(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """Execute the merge transform."""
        start_time = time.perf_counter()

        # Validate required inputs
        errors = self._validate_inputs(inputs)
        if errors:
            return NodeResult.failure_result(
                error="; ".join(errors),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        mode = context.get_config_value("mode", "object")

        # Collect all non-None inputs in order (in1 through in4)
        input_keys = ["in1", "in2", "in3", "in4"]
        values = [inputs.get(key) for key in input_keys if inputs.get(key) is not None]

        if not values:
            context.log_info("No inputs provided, returning None")
            return NodeResult.success_result(
                outputs={"out": None},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        try:
            if mode == "object":
                # Shallow merge: later objects override earlier ones
                result = {}
                for value in values:
                    if isinstance(value, dict):
                        result.update(value)
                    else:
                        # Wrap non-dict values with indexed keys
                        idx = values.index(value)
                        result[f"value_{idx}"] = value

            elif mode == "array":
                # Array mode: flatten lists and append other values
                result = []
                for value in values:
                    if isinstance(value, list):
                        result.extend(value)
                    else:
                        result.append(value)

            elif mode == "concat":
                # String/array concatenation
                separator = context.get_config_value("separator", "")

                if all(isinstance(v, str) for v in values):
                    # All strings: join with separator
                    result = separator.join(values)
                elif all(isinstance(v, list) for v in values):
                    # All lists: extend result list
                    result = []
                    for v in values:
                        result.extend(v)
                else:
                    # Mixed types: convert all to strings and join
                    result = separator.join(str(v) for v in values)

            elif mode == "deep":
                # Deep merge: recursively merge nested dictionaries
                result = {}
                for idx, value in enumerate(values):
                    if isinstance(value, dict):
                        result = self._deep_merge(result, value)
                    else:
                        result[f"value_{idx}"] = value

            else:
                # Fallback: return values as-is
                result = values

            context.log_info(f"Merged {len(values)} input(s) using mode '{mode}'")

            return NodeResult.success_result(
                outputs={"out": result},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            context.log_error(f"Merge operation failed: {e}")
            return NodeResult.failure_result(
                error=f"Merge failed: {str(e)}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
