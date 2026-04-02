"""Ruby 3.3 runtime implementation."""

from typing import List

from app.action_runtime import BaseRuntime


class RubyRuntime(BaseRuntime):
    """Ruby 3.3 runtime (Debian 12 slim base)."""

    @property
    def image_name(self) -> str:
        """Docker image for Ruby runtime."""
        return "iceruns/ruby:3.3"

    def prepare_entrypoint(self, handler: str) -> List[str]:
        """Prepare Ruby execution command.

        Handler format: file.method (e.g., main.handler)

        Args:
            handler: Handler method (file.method)

        Returns:
            Command list
        """
        if "." not in handler:
            raise ValueError(
                f"Invalid handler format: {handler}. Expected: file.method"
            )

        module, method = handler.rsplit(".", 1)

        wrapper = f"""
require 'json'
require_relative '{module}'

input = JSON.parse(ENV['ICERUN_INPUT'])

begin
  result = {method}(input)
  puts "__ICERUN_OUTPUT__:" + result.to_json
  exit 0
rescue => e
  STDERR.puts "Error executing handler: #{{e}}"
  STDERR.puts e.backtrace
  exit 1
end
"""

        return ["ruby", "-e", wrapper]
