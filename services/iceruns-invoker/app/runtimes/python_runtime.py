"""Python 3.13 runtime implementation."""

from typing import List
from app.action_runtime import BaseRuntime


class PythonRuntime(BaseRuntime):
    """Python 3.13 runtime (Debian 12 slim base)."""

    @property
    def image_name(self) -> str:
        """Docker image for Python runtime."""
        return "iceruns/python:3.13"

    def prepare_entrypoint(self, handler: str) -> List[str]:
        """Prepare Python execution command.

        Handler format: module.function (e.g., main.process)

        Args:
            handler: Handler function (module.function)

        Returns:
            Command list
        """
        if '.' not in handler:
            raise ValueError(f"Invalid handler format: {handler}. Expected: module.function")

        module, function = handler.rsplit('.', 1)

        # Wrapper script to invoke handler and capture output
        wrapper = f"""
import sys
import json
import os
import importlib

# Load input
input_data = json.loads(os.environ['ICERUN_INPUT'])

# Import handler
try:
    module = importlib.import_module('{module}')
    handler_fn = getattr(module, '{function}')
except (ImportError, AttributeError) as e:
    print(f'Error loading handler: {{e}}', file=sys.stderr)
    sys.exit(1)

# Execute
try:
    result = handler_fn(input_data)
    # Output JSON on last line with marker
    print('__ICERUN_OUTPUT__:' + json.dumps(result))
    sys.exit(0)
except Exception as e:
    print(f'Error executing handler: {{e}}', file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

        return ['python3', '-c', wrapper]
