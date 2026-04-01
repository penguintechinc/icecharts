#!/usr/bin/env python3
"""
Comprehensive unit tests for AskAiTransform node.

Tests cover:
- Configuration validation (prompt, provider, outputFormat, maxTokens, temperature)
- LLM provider support (Anthropic, OpenAI, Ollama, WaddleAI)
- Prompt building with variable substitution ({{data}}, {{input}}, {{context}})
- System prompt handling
- Output format handling (text vs JSON)
- Token usage reporting
- Error handling (missing API key, API errors)
- Mock LLM responses
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Any, Dict
import json

from nodes.transforms.ask_ai import AskAiTransform, LLMConfig
from nodes.base import NodeContext, NodeResult


class TestAskAiValidation:
    """Test AskAI configuration validation."""

    def test_validate_config_valid(self) -> None:
        """Test validation passes for valid configuration."""
        config = {
            "prompt": "Describe this data: {{data}}",
            "provider": "anthropic",
            "outputFormat": "text",
            "maxTokens": 1000,
            "temperature": 0.7,
        }
        errors = AskAiTransform.validate_config(config)
        assert errors == []

    def test_validate_config_missing_prompt(self) -> None:
        """Test validation fails without prompt."""
        config = {"provider": "anthropic"}
        errors = AskAiTransform.validate_config(config)
        assert any("prompt" in e.lower() for e in errors)

    def test_validate_config_invalid_provider(self) -> None:
        """Test validation fails for invalid provider."""
        config = {"prompt": "test", "provider": "invalid"}
        errors = AskAiTransform.validate_config(config)
        assert any("Invalid provider" in e for e in errors)

    def test_validate_config_invalid_output_format(self) -> None:
        """Test validation fails for invalid output format."""
        config = {"prompt": "test", "outputFormat": "invalid"}
        errors = AskAiTransform.validate_config(config)
        assert any("Invalid outputFormat" in e for e in errors)

    def test_validate_config_invalid_max_tokens(self) -> None:
        """Test validation fails for invalid maxTokens."""
        config = {"prompt": "test", "maxTokens": -1}
        errors = AskAiTransform.validate_config(config)
        assert any("maxTokens" in e for e in errors)

    def test_validate_config_max_tokens_too_large(self) -> None:
        """Test validation fails for maxTokens exceeding limit."""
        config = {"prompt": "test", "maxTokens": 100001}
        errors = AskAiTransform.validate_config(config)
        assert any("maxTokens" in e for e in errors)

    def test_validate_config_invalid_temperature(self) -> None:
        """Test validation fails for invalid temperature."""
        config = {"prompt": "test", "temperature": -0.5}
        errors = AskAiTransform.validate_config(config)
        assert any("temperature" in e.lower() for e in errors)

    def test_validate_config_temperature_too_high(self) -> None:
        """Test validation fails for temperature exceeding limit."""
        config = {"prompt": "test", "temperature": 2.5}
        errors = AskAiTransform.validate_config(config)
        assert any("temperature" in e.lower() for e in errors)

    def test_validate_config_valid_providers(self) -> None:
        """Test all valid providers pass validation."""
        for provider in ["anthropic", "openai", "waddle", "ollama"]:
            config = {"prompt": "test", "provider": provider}
            errors = AskAiTransform.validate_config(config)
            assert not any("Invalid provider" in e for e in errors)

    def test_validate_config_valid_output_formats(self) -> None:
        """Test all valid output formats pass validation."""
        for fmt in ["text", "json"]:
            config = {"prompt": "test", "outputFormat": fmt}
            errors = AskAiTransform.validate_config(config)
            assert not any("Invalid outputFormat" in e for e in errors)


class TestLLMConfig:
    """Test LLM configuration building."""

    def test_llm_config_anthropic(self) -> None:
        """Test LLM config for Anthropic provider."""
        node = AskAiTransform()
        config = {"provider": "anthropic", "model": "claude-3"}
        llm_config = node._get_llm_config(config)

        assert llm_config.provider == "anthropic"
        assert llm_config.model == "claude-3"
        assert "anthropic" in llm_config.base_url.lower()

    def test_llm_config_openai(self) -> None:
        """Test LLM config for OpenAI provider."""
        node = AskAiTransform()
        config = {"provider": "openai", "model": "gpt-4"}
        llm_config = node._get_llm_config(config)

        assert llm_config.provider == "openai"
        assert llm_config.model == "gpt-4"
        assert "openai" in llm_config.base_url.lower()

    def test_llm_config_ollama(self) -> None:
        """Test LLM config for Ollama provider."""
        node = AskAiTransform()
        config = {"provider": "ollama"}
        llm_config = node._get_llm_config(config)

        assert llm_config.provider == "ollama"
        assert llm_config.base_url is not None

    def test_llm_config_waddle(self) -> None:
        """Test LLM config for WaddleAI provider."""
        node = AskAiTransform()
        config = {"provider": "waddle"}
        llm_config = node._get_llm_config(config)

        assert llm_config.provider == "waddle"

    def test_llm_config_custom_model(self) -> None:
        """Test LLM config with custom model."""
        node = AskAiTransform()
        config = {"provider": "anthropic", "model": "custom-model"}
        llm_config = node._get_llm_config(config)

        assert llm_config.model == "custom-model"

    def test_llm_config_custom_base_url(self) -> None:
        """Test LLM config with custom base URL."""
        node = AskAiTransform()
        config = {"provider": "anthropic", "baseUrl": "https://custom.api.com"}
        llm_config = node._get_llm_config(config)

        assert llm_config.base_url == "https://custom.api.com"

    def test_llm_config_max_tokens(self) -> None:
        """Test LLM config with custom max tokens."""
        node = AskAiTransform()
        config = {"provider": "anthropic", "maxTokens": 2000}
        llm_config = node._get_llm_config(config)

        assert llm_config.max_tokens == 2000

    def test_llm_config_temperature(self) -> None:
        """Test LLM config with custom temperature."""
        node = AskAiTransform()
        config = {"provider": "anthropic", "temperature": 0.5}
        llm_config = node._get_llm_config(config)

        assert llm_config.temperature == 0.5


class TestPromptBuilding:
    """Test prompt template building."""

    def test_prompt_data_substitution_dict(self) -> None:
        """Test substituting {{data}} with dictionary."""
        node = AskAiTransform()
        template = "Process this: {{data}}"
        data = {"key": "value", "num": 42}

        prompt = node._build_prompt(template, data)
        assert '"key"' in prompt or "'key'" in prompt
        assert "value" in prompt

    def test_prompt_data_substitution_list(self) -> None:
        """Test substituting {{data}} with list."""
        node = AskAiTransform()
        template = "Analyze: {{data}}"
        data = [1, 2, 3, 4, 5]

        prompt = node._build_prompt(template, data)
        assert "1" in prompt
        assert "5" in prompt

    def test_prompt_data_substitution_string(self) -> None:
        """Test substituting {{data}} with string."""
        node = AskAiTransform()
        template = "Translate: {{data}}"
        data = "hello world"

        prompt = node._build_prompt(template, data)
        assert "hello world" in prompt

    def test_prompt_input_substitution(self) -> None:
        """Test {{input}} substitution (alias for {{data}})."""
        node = AskAiTransform()
        template = "Process input: {{input}}"
        data = {"test": "data"}

        prompt = node._build_prompt(template, data)
        assert "test" in prompt or "data" in prompt

    def test_prompt_context_substitution(self) -> None:
        """Test {{context}} substitution with extra context."""
        node = AskAiTransform()
        template = "Context: {{context}}, Data: {{data}}"
        data = "data"
        context = "user provided context"

        prompt = node._build_prompt(template, data, context)
        assert "user provided context" in prompt
        assert "data" in prompt

    def test_prompt_missing_context(self) -> None:
        """Test {{context}} without extra context."""
        node = AskAiTransform()
        template = "Context: {{context}}, Data: {{data}}"
        data = "data"

        prompt = node._build_prompt(template, data)
        # {{context}} should be replaced with empty string
        assert "Data: data" in prompt

    def test_prompt_multiple_substitutions(self) -> None:
        """Test multiple data substitutions."""
        node = AskAiTransform()
        template = "First: {{data}}, Second: {{input}}"
        data = "test"

        prompt = node._build_prompt(template, data)
        assert prompt.count("test") == 2

    def test_prompt_no_substitutions(self) -> None:
        """Test prompt with no substitution placeholders."""
        node = AskAiTransform()
        template = "Static prompt without placeholders"
        data = {"key": "value"}

        prompt = node._build_prompt(template, data)
        assert prompt == template


class TestOutputFormatting:
    """Test output format handling."""

    @pytest.mark.asyncio
    async def test_output_format_text(self) -> None:
        """Test text output format returns raw response."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Simple prompt",
            "provider": "anthropic",
            "outputFormat": "text",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        # Mock the API call
        with patch.object(node, "_call_anthropic", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": "This is the response",
                "usage": {"input_tokens": 10, "output_tokens": 20},
                "model": "test-model",
            }

            result = await node.execute(context, {"in": "test data"})
            assert result.success is True
            assert result.outputs["out"] == "This is the response"

    @pytest.mark.asyncio
    async def test_output_format_json_valid(self) -> None:
        """Test JSON output format parses valid JSON."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Return JSON",
            "provider": "anthropic",
            "outputFormat": "json",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        with patch.object(node, "_call_anthropic", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": '{"result": "success", "count": 42}',
                "usage": {"input_tokens": 10, "output_tokens": 20},
                "model": "test-model",
            }

            result = await node.execute(context, {"in": "test"})
            assert result.success is True
            assert result.outputs["out"]["result"] == "success"
            assert result.outputs["out"]["count"] == 42

    @pytest.mark.asyncio
    async def test_output_format_json_with_markdown(self) -> None:
        """Test JSON parsing from markdown code blocks."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Return JSON",
            "provider": "anthropic",
            "outputFormat": "json",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        with patch.object(node, "_call_anthropic", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": '```json\n{"result": "success"}\n```',
                "usage": {"input_tokens": 10, "output_tokens": 20},
                "model": "test-model",
            }

            result = await node.execute(context, {"in": "test"})
            assert result.success is True
            assert result.outputs["out"]["result"] == "success"

    @pytest.mark.asyncio
    async def test_output_format_json_invalid(self) -> None:
        """Test JSON format with invalid JSON response."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Return JSON",
            "provider": "anthropic",
            "outputFormat": "json",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        with patch.object(node, "_call_anthropic", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": "Not valid JSON",
                "usage": {"input_tokens": 10, "output_tokens": 20},
                "model": "test-model",
            }

            result = await node.execute(context, {"in": "test"})
            assert result.success is True
            # Should return error dict with parse_error
            assert "parse_error" in result.outputs["out"] or isinstance(
                result.outputs["out"], dict
            )


class TestProviderCalls:
    """Test provider-specific API calls."""

    @pytest.mark.asyncio
    async def test_anthropic_provider(self) -> None:
        """Test Anthropic provider call."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Test prompt",
            "provider": "anthropic",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        with patch.object(node, "_call_anthropic", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": "Response",
                "usage": {"input_tokens": 10, "output_tokens": 20},
                "model": "claude-3",
            }

            result = await node.execute(context, {"in": "test"})
            assert result.success is True
            assert mock_call.called

    @pytest.mark.asyncio
    async def test_openai_provider(self) -> None:
        """Test OpenAI provider call."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Test prompt",
            "provider": "openai",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        with patch.object(node, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": "Response",
                "usage": {"input_tokens": 10, "output_tokens": 20},
                "model": "gpt-4",
            }

            result = await node.execute(context, {"in": "test"})
            assert result.success is True
            assert mock_call.called

    @pytest.mark.asyncio
    async def test_ollama_provider(self) -> None:
        """Test Ollama provider call (no API key required)."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"prompt": "Test prompt", "provider": "ollama"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        with patch.object(node, "_call_ollama", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": "Response",
                "usage": {"input_tokens": 10, "output_tokens": 20},
                "model": "llama2",
            }

            result = await node.execute(context, {"in": "test"})
            assert result.success is True

    @pytest.mark.asyncio
    async def test_waddle_provider(self) -> None:
        """Test WaddleAI provider call."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Test prompt",
            "provider": "waddle",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        with patch.object(node, "_call_waddle", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": "Response",
                "usage": {"input_tokens": 10, "output_tokens": 20},
                "model": "waddle",
            }

            result = await node.execute(context, {"in": "test"})
            assert result.success is True


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_missing_api_key_anthropic(self) -> None:
        """Test error when API key missing for Anthropic."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Test",
            "provider": "anthropic",
            # No apiKey provided
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "test"})
        assert result.success is False
        assert "API key" in result.error

    @pytest.mark.asyncio
    async def test_missing_api_key_openai(self) -> None:
        """Test error when API key missing for OpenAI."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"prompt": "Test", "provider": "openai"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "test"})
        assert result.success is False
        assert "API key" in result.error

    @pytest.mark.asyncio
    async def test_api_call_failure(self) -> None:
        """Test handling of API call failures."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Test",
            "provider": "anthropic",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()
        context.error = MagicMock()  # Add error method mock

        with patch.object(node, "_call_anthropic", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API Error")

            result = await node.execute(context, {"in": "test"})
            assert result.success is False
            assert "AI call failed" in result.error or "API call failed" in result.error


class TestTokenUsage:
    """Test token usage reporting."""

    @pytest.mark.asyncio
    async def test_token_usage_in_output(self) -> None:
        """Test that token usage is included in output."""
        node = AskAiTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "prompt": "Test",
            "provider": "anthropic",
            "apiKey": "test-key",
        }
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        with patch.object(node, "_call_anthropic", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": "Response",
                "usage": {"input_tokens": 100, "output_tokens": 50},
                "model": "claude-3",
            }

            result = await node.execute(context, {"in": "test"})
            assert result.success is True
            assert result.outputs["usage"]["input_tokens"] == 100
            assert result.outputs["usage"]["output_tokens"] == 50


class TestNodeInterface:
    """Test node interface and metadata."""

    def test_node_inputs(self) -> None:
        """Test node input definitions."""
        inputs = AskAiTransform.inputs()
        assert len(inputs) >= 1
        input_names = {i.name for i in inputs}
        assert "in" in input_names

    def test_node_outputs(self) -> None:
        """Test node output definitions."""
        outputs = AskAiTransform.outputs()
        assert len(outputs) >= 1
        output_names = {o.name for o in outputs}
        assert "out" in output_names

    def test_node_type(self) -> None:
        """Test node type identifier."""
        assert AskAiTransform.node_type == "transform_ask_ai"

    def test_node_category(self) -> None:
        """Test node category."""
        assert AskAiTransform.category == "transforms"
