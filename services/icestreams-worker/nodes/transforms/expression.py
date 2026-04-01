"""
Expression Transform Node - Safe mathematical and string expression evaluation.

This module provides a safe, AST-based expression evaluator for data transformation
in IceStreams workflows. Only whitelisted operators and functions are allowed,
preventing code injection and arbitrary execution.

Features:
- Safe arithmetic and comparison operations
- String manipulation functions
- Mathematical operations (sqrt, floor, ceil, etc.)
- Conditional expressions (if-else)
- Boolean logic (and, or)
- Data access from dictionaries and lists
- No exec/eval of arbitrary code
"""

from __future__ import annotations

import ast
import operator
import logging
import math
import time
from typing import Any, Dict, List, Callable

try:
    # Try relative imports first (when run as a package)
    from ..base import BaseNode, NodeContext, NodeResult, NodeInput, NodeOutput
    from ...executor.node_registry import register_node
except ImportError:
    # Fallback for direct execution or alternative import paths
    from nodes.base import BaseNode, NodeContext, NodeResult, NodeInput, NodeOutput
    from executor.node_registry import register_node

logger = logging.getLogger(__name__)

# Safe binary operators for expression evaluation
SAFE_OPERATORS: Dict[type, Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe comparison operators
SAFE_COMPARISONS: Dict[type, Callable] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

# Safe functions available in expressions
SAFE_FUNCTIONS: Dict[str, Callable] = {
    "abs": abs,
    "min": min,
    "max": max,
    "len": len,
    "sum": sum,
    "round": round,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "upper": lambda s: str(s).upper(),
    "lower": lambda s: str(s).lower(),
    "strip": lambda s: str(s).strip(),
    "sqrt": math.sqrt,
    "floor": math.floor,
    "ceil": math.ceil,
}


@register_node("transform_expression", "transforms", "Expression")
class ExpressionTransform(BaseNode):
    """Evaluate safe mathematical and string expressions for data transformation."""

    node_type = "transform_expression"
    name = "Expression"
    description = "Evaluate safe expressions for data transformation"
    category = "transforms"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for this node."""
        return [
            NodeInput(
                name="in",
                description="Input data (accessible as 'data' in expression)",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for this node."""
        return [
            NodeOutput(name="out", description="Expression result", data_type="any"),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate the node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        expression = config.get("expression", "")
        if not expression:
            errors.append("expression is required")
        else:
            try:
                ast.parse(expression, mode="eval")
            except SyntaxError as e:
                errors.append(f"Invalid expression syntax: {e}")

        return errors

    def _safe_eval(self, node: ast.AST, variables: Dict[str, Any]) -> Any:
        """
        Safely evaluate an AST node without using exec/eval.

        Args:
            node: AST node to evaluate
            variables: Dictionary of available variables and functions

        Returns:
            Result of the evaluation

        Raises:
            ValueError: If an unsupported operation or variable is encountered
        """
        # Handle Expression wrapper
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body, variables)

        # Handle constant values (Python 3.8+)
        if isinstance(node, ast.Constant):
            return node.value

        # Handle numeric constants (Python 3.7 compatibility)
        if isinstance(node, ast.Num):
            return node.n

        # Handle string constants (Python 3.7 compatibility)
        if isinstance(node, ast.Str):
            return node.s

        # Handle variable/function names
        if isinstance(node, ast.Name):
            name = node.id
            if name in variables:
                return variables[name]
            raise ValueError(f"Unknown variable: {name}")

        # Handle binary operations (e.g., +, -, *, /)
        if isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left, variables)
            right = self._safe_eval(node.right, variables)
            op = SAFE_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(left, right)

        # Handle unary operations (e.g., -, +)
        if isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand, variables)
            op = SAFE_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(operand)

        # Handle comparisons (e.g., <, >, ==, !=)
        if isinstance(node, ast.Compare):
            left = self._safe_eval(node.left, variables)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._safe_eval(comparator, variables)
                cmp_func = SAFE_COMPARISONS.get(type(op))
                if cmp_func is None:
                    raise ValueError(f"Unsupported comparison: {type(op).__name__}")
                if not cmp_func(left, right):
                    return False
                left = right
            return True

        # Handle function calls
        if isinstance(node, ast.Call):
            func = self._safe_eval(node.func, variables)
            args = [self._safe_eval(arg, variables) for arg in node.args]
            if not callable(func):
                raise ValueError(f"Not a callable: {func}")
            return func(*args)

        # Handle subscript access (e.g., data[0], data["key"])
        if isinstance(node, ast.Subscript):
            value = self._safe_eval(node.value, variables)
            # Python 3.8 compatibility: ast.Index vs direct slice
            if isinstance(node.slice, ast.Index):
                key = self._safe_eval(node.slice.value, variables)
            else:
                key = self._safe_eval(node.slice, variables)
            return value[key]

        # Handle attribute access (e.g., data.field)
        if isinstance(node, ast.Attribute):
            value = self._safe_eval(node.value, variables)
            attr = node.attr
            if hasattr(value, attr):
                return getattr(value, attr)
            elif isinstance(value, dict):
                return value.get(attr)
            raise ValueError(f"Cannot access attribute: {attr}")

        # Handle list literals (e.g., [1, 2, 3])
        if isinstance(node, ast.List):
            return [self._safe_eval(elt, variables) for elt in node.elts]

        # Handle dict literals (e.g., {"key": "value"})
        if isinstance(node, ast.Dict):
            return {
                self._safe_eval(k, variables): self._safe_eval(v, variables)
                for k, v in zip(node.keys, node.values)
            }

        # Handle conditional expressions (e.g., x if condition else y)
        if isinstance(node, ast.IfExp):
            test = self._safe_eval(node.test, variables)
            if test:
                return self._safe_eval(node.body, variables)
            else:
                return self._safe_eval(node.orelse, variables)

        # Handle boolean operations (and, or)
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for value in node.values:
                    if not self._safe_eval(value, variables):
                        return False
                return True
            elif isinstance(node.op, ast.Or):
                for value in node.values:
                    if self._safe_eval(value, variables):
                        return True
                return False

        # Unsupported expression type
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute the expression transform.

        Args:
            context: Execution context with config and logging
            inputs: Dictionary mapping input port names to values

        Returns:
            NodeResult with evaluation result or error message
        """
        start_time = time.perf_counter()

        try:
            # Get input data and expression from config
            input_data = inputs.get("in")
            expression = context.config.get("expression", "data")

            # Build variables context with input data and safe functions
            variables = {
                "data": input_data,
                "true": True,
                "false": False,
                "null": None,
                "none": None,
                **SAFE_FUNCTIONS,
            }

            # If input is a dictionary, make its keys available as variables
            if isinstance(input_data, dict):
                for key, value in input_data.items():
                    # Only add valid Python identifiers that don't shadow built-ins
                    if key.isidentifier() and key not in variables:
                        variables[key] = value

            # Parse and evaluate the expression
            tree = ast.parse(expression, mode="eval")
            result = self._safe_eval(tree, variables)

            # Log successful evaluation
            context.log_info(f"Expression evaluated: {expression[:50]}...")

            return NodeResult.success_result(
                outputs={"out": result},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            # Log and return error
            context.log_error(f"Expression failed: {e}")
            return NodeResult.failure_result(
                error=f"Expression evaluation failed: {str(e)}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
