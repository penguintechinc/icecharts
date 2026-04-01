"""Node.js 20 runtime implementation."""

from typing import List
from app.action_runtime import BaseRuntime


class NodeJSRuntime(BaseRuntime):
    """Node.js 20 runtime (Debian 12 slim base)."""

    @property
    def image_name(self) -> str:
        """Docker image for Node.js runtime."""
        return "iceruns/nodejs:20"

    def prepare_entrypoint(self, handler: str) -> List[str]:
        """Prepare Node.js execution command.

        Handler format: file.function (e.g., index.handler)

        Args:
            handler: Handler function (file.function)

        Returns:
            Command list
        """
        if "." not in handler:
            raise ValueError(
                f"Invalid handler format: {handler}. Expected: file.function"
            )

        module, function = handler.rsplit(".", 1)

        wrapper = f"""
const {{ {function} }} = require('./{module}');
const input = JSON.parse(process.env.ICERUN_INPUT);

(async () => {{
    try {{
        const result = await {function}(input);
        console.log('__ICERUN_OUTPUT__:' + JSON.stringify(result));
        process.exit(0);
    }} catch (err) {{
        console.error('Error executing handler:', err);
        process.exit(1);
    }}
}})();
"""

        return ["node", "-e", wrapper]
