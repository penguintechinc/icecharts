from __future__ import annotations
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from ..base import BaseNode, NodeContext, NodeResult, NodeInput, NodeOutput
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str  # "anthropic", "openai", "waddle"
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7


@register_node("transform_ask_ai", "transforms", "Ask AI")
class AskAiTransform(BaseNode):
    """Send data to an LLM for AI-powered transformation."""

    node_type = "transform_ask_ai"
    name = "Ask AI"
    description = "Process data using an AI language model"
    category = "transforms"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        return [
            NodeInput(name="in", description="Input data to send to AI", required=True, data_type="any"),
            NodeInput(name="context", description="Additional context (optional)", required=False, data_type="string"),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        return [
            NodeOutput(name="out", description="AI response", data_type="any"),
            NodeOutput(name="raw", description="Raw response text", data_type="string"),
            NodeOutput(name="usage", description="Token usage statistics", data_type="object"),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        errors = []

        prompt = config.get("prompt", "")
        if not prompt:
            errors.append("prompt is required")

        provider = config.get("provider", "anthropic")
        valid_providers = {"anthropic", "openai", "waddle", "ollama"}
        if provider not in valid_providers:
            errors.append(f"Invalid provider: {provider}. Valid: {valid_providers}")

        output_format = config.get("outputFormat", "text")
        if output_format not in ("text", "json"):
            errors.append(f"Invalid outputFormat: {output_format}. Must be 'text' or 'json'")

        max_tokens = config.get("maxTokens", 4096)
        if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 100000:
            errors.append("maxTokens must be an integer between 1 and 100000")

        temperature = config.get("temperature", 0.7)
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            errors.append("temperature must be a number between 0 and 2")

        return errors

    def _get_llm_config(self, config: Dict[str, Any]) -> LLMConfig:
        """Build LLM configuration from node config and environment."""
        provider = config.get("provider", "anthropic")

        # Get API key from config or environment
        api_key = config.get("apiKey", "")
        if not api_key:
            env_keys = {
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
                "waddle": "WADDLE_API_KEY",
                "ollama": "",  # Ollama doesn't need API key
            }
            api_key = os.getenv(env_keys.get(provider, ""), "")

        # Model defaults by provider
        model_defaults = {
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4o",
            "waddle": "default",
            "ollama": "llama3.2",
        }
        model = config.get("model", model_defaults.get(provider, ""))

        # Base URL for custom endpoints
        base_url = config.get("baseUrl", "")
        if not base_url:
            base_urls = {
                "anthropic": "https://api.anthropic.com",
                "openai": "https://api.openai.com/v1",
                "waddle": os.getenv("WADDLE_API_URL", "http://localhost:8000"),
                "ollama": os.getenv("OLLAMA_URL", "http://localhost:11434"),
            }
            base_url = base_urls.get(provider, "")

        return LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=config.get("maxTokens", 4096),
            temperature=config.get("temperature", 0.7),
        )

    def _build_prompt(self, template: str, input_data: Any, extra_context: str = "") -> str:
        """Build the final prompt from template and data."""
        # Convert input data to string representation
        if isinstance(input_data, (dict, list)):
            data_str = json.dumps(input_data, indent=2, default=str)
        else:
            data_str = str(input_data)

        # Replace placeholders
        prompt = template.replace("{{data}}", data_str)
        prompt = prompt.replace("{{input}}", data_str)

        if extra_context:
            prompt = prompt.replace("{{context}}", extra_context)
        else:
            prompt = prompt.replace("{{context}}", "")

        return prompt

    async def _call_anthropic(self, llm_config: LLMConfig, prompt: str, system: str = "") -> Dict[str, Any]:
        """Call Anthropic Claude API."""
        import httpx

        headers = {
            "Content-Type": "application/json",
            "x-api-key": llm_config.api_key,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": llm_config.model,
            "max_tokens": llm_config.max_tokens,
            "temperature": llm_config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{llm_config.base_url}/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "content": data["content"][0]["text"] if data.get("content") else "",
            "usage": {
                "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                "output_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            "model": data.get("model", llm_config.model),
        }

    async def _call_openai(self, llm_config: LLMConfig, prompt: str, system: str = "") -> Dict[str, Any]:
        """Call OpenAI API."""
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm_config.api_key}",
        }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": llm_config.model,
            "max_tokens": llm_config.max_tokens,
            "temperature": llm_config.temperature,
            "messages": messages,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{llm_config.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "content": data["choices"][0]["message"]["content"] if data.get("choices") else "",
            "usage": {
                "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
            },
            "model": data.get("model", llm_config.model),
        }

    async def _call_ollama(self, llm_config: LLMConfig, prompt: str, system: str = "") -> Dict[str, Any]:
        """Call local Ollama API."""
        import httpx

        payload = {
            "model": llm_config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": llm_config.temperature,
                "num_predict": llm_config.max_tokens,
            },
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{llm_config.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "content": data.get("response", ""),
            "usage": {
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
            },
            "model": llm_config.model,
        }

    async def _call_waddle(self, llm_config: LLMConfig, prompt: str, system: str = "") -> Dict[str, Any]:
        """Call WaddleAI API."""
        import httpx

        headers = {
            "Content-Type": "application/json",
        }
        if llm_config.api_key:
            headers["Authorization"] = f"Bearer {llm_config.api_key}"

        payload = {
            "prompt": prompt,
            "max_tokens": llm_config.max_tokens,
            "temperature": llm_config.temperature,
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{llm_config.base_url}/api/v1/generate",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "content": data.get("response", data.get("content", "")),
            "usage": data.get("usage", {}),
            "model": data.get("model", "waddle"),
        }

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """Execute the Ask AI transform."""
        import time
        start_time = time.perf_counter()

        input_data = inputs.get("in")
        extra_context = inputs.get("context", "")

        prompt_template = context.config.get("prompt", "Process this data: {{data}}")
        system_prompt = context.config.get("systemPrompt", "")
        output_format = context.config.get("outputFormat", "text")

        llm_config = self._get_llm_config(context.config)

        # Check for API key (except Ollama)
        if llm_config.provider != "ollama" and not llm_config.api_key:
            return NodeResult.failure_result(
                error=f"No API key configured for provider: {llm_config.provider}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        # Build prompt
        prompt = self._build_prompt(prompt_template, input_data, extra_context)

        # Add JSON instruction if needed
        if output_format == "json":
            prompt += "\n\nRespond with valid JSON only, no additional text."

        context.info(f"Calling {llm_config.provider} ({llm_config.model})")

        try:
            # Call appropriate provider
            if llm_config.provider == "anthropic":
                response = await self._call_anthropic(llm_config, prompt, system_prompt)
            elif llm_config.provider == "openai":
                response = await self._call_openai(llm_config, prompt, system_prompt)
            elif llm_config.provider == "ollama":
                response = await self._call_ollama(llm_config, prompt, system_prompt)
            elif llm_config.provider == "waddle":
                response = await self._call_waddle(llm_config, prompt, system_prompt)
            else:
                return NodeResult.failure_result(
                    error=f"Unknown provider: {llm_config.provider}",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )

            raw_content = response["content"]

            # Parse JSON if requested
            if output_format == "json":
                try:
                    # Try to extract JSON from response
                    content = raw_content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    parsed = json.loads(content.strip())
                except json.JSONDecodeError:
                    parsed = {"raw": raw_content, "parse_error": "Failed to parse as JSON"}
            else:
                parsed = raw_content

            context.info(f"AI response received ({response['usage'].get('output_tokens', 0)} tokens)")

            return NodeResult.success_result(
                outputs={
                    "out": parsed,
                    "raw": raw_content,
                    "usage": response["usage"],
                },
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        except Exception as e:
            context.error(f"AI call failed: {e}")
            return NodeResult.failure_result(
                error=f"AI call failed: {str(e)}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )
