#!/usr/bin/env python3
"""
Extended tests for DelayTransform node to increase coverage from 61%.

Covers:
- inputs() and outputs() class methods
- validate_config: missing, negative, over-limit, invalid-type
- execute: delayMs, delaySeconds, no delay, non-dict passthrough, zero delay
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from nodes.base import NodeContext, NodeResult
from nodes.transforms.delay import DelayTransform


def _make_context(config: dict) -> NodeContext:
    ctx = MagicMock(spec=NodeContext)
    ctx.config = config
    ctx.get_config_value = lambda k, d=None: config.get(k, d)
    ctx.log_info = MagicMock()
    ctx.log_error = MagicMock()
    ctx.log_warning = MagicMock()
    return ctx


class TestDelayInputsOutputs:
    """Test inputs/outputs class methods."""

    def test_inputs_defined(self) -> None:
        inputs = DelayTransform.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "in"
        assert inputs[0].required is True

    def test_outputs_defined(self) -> None:
        outputs = DelayTransform.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"


class TestDelayValidateConfig:
    """Test validate_config for all branches."""

    def test_no_delay_params_error(self) -> None:
        errors = DelayTransform.validate_config({})
        assert any("delayMs or delaySeconds" in e for e in errors)

    def test_delay_ms_valid(self) -> None:
        errors = DelayTransform.validate_config({"delayMs": 500})
        assert errors == []

    def test_delay_seconds_valid(self) -> None:
        errors = DelayTransform.validate_config({"delaySeconds": 1.5})
        assert errors == []

    def test_delay_ms_negative(self) -> None:
        errors = DelayTransform.validate_config({"delayMs": -1})
        assert any("non-negative" in e for e in errors)

    def test_delay_ms_exceeds_max(self) -> None:
        errors = DelayTransform.validate_config({"delayMs": 300001})
        assert any("300000" in e for e in errors)

    def test_delay_ms_invalid_type(self) -> None:
        errors = DelayTransform.validate_config({"delayMs": "not-a-number"})
        assert any("valid integer" in e for e in errors)

    def test_delay_seconds_negative(self) -> None:
        errors = DelayTransform.validate_config({"delaySeconds": -0.1})
        assert any("non-negative" in e for e in errors)

    def test_delay_seconds_exceeds_max(self) -> None:
        errors = DelayTransform.validate_config({"delaySeconds": 301})
        assert any("300" in e for e in errors)

    def test_delay_seconds_invalid_type(self) -> None:
        errors = DelayTransform.validate_config({"delaySeconds": "bad"})
        assert any("valid number" in e for e in errors)

    def test_both_provided_is_valid(self) -> None:
        """Both delayMs and delaySeconds can be provided simultaneously."""
        errors = DelayTransform.validate_config({"delayMs": 100, "delaySeconds": 1})
        assert errors == []

    def test_delay_ms_zero(self) -> None:
        errors = DelayTransform.validate_config({"delayMs": 0})
        assert errors == []

    def test_delay_seconds_zero(self) -> None:
        errors = DelayTransform.validate_config({"delaySeconds": 0})
        assert errors == []


class TestDelayExecute:
    """Test execute method for all branches."""

    @pytest.mark.asyncio
    async def test_execute_delay_ms(self) -> None:
        """delayMs configures the delay."""
        node = DelayTransform()
        ctx = _make_context({"delayMs": 1})  # 1ms — near instant

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await node.execute(ctx, {"in": {"value": 42}})

        assert result.success is True
        mock_sleep.assert_called_once()
        # Delay is 1ms = 0.001s, capped at 300s
        assert mock_sleep.call_args[0][0] == pytest.approx(0.001, abs=1e-6)

    @pytest.mark.asyncio
    async def test_execute_delay_seconds(self) -> None:
        """delaySeconds configures the delay."""
        node = DelayTransform()
        ctx = _make_context({"delaySeconds": 0.002})

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await node.execute(ctx, {"in": {"key": "val"}})

        assert result.success is True
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] == pytest.approx(0.002, abs=1e-6)

    @pytest.mark.asyncio
    async def test_execute_no_delay_config(self) -> None:
        """When no delay config is set, delay defaults to 0 and sleep is not called."""
        node = DelayTransform()
        ctx = _make_context({})

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await node.execute(ctx, {"in": {"x": 1}})

        assert result.success is True
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_zero_delay_skips_sleep(self) -> None:
        """Zero delay does not call asyncio.sleep."""
        node = DelayTransform()
        ctx = _make_context({"delayMs": 0})

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await node.execute(ctx, {"in": {}})

        assert result.success is True
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_dict_input_gets_metadata(self) -> None:
        """Dict input receives _delay metadata."""
        node = DelayTransform()
        ctx = _make_context({"delayMs": 1})

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await node.execute(ctx, {"in": {"field": "data"}})

        assert result.success is True
        out = result.outputs["out"]
        assert isinstance(out, dict)
        assert "_delay" in out
        assert out["field"] == "data"
        assert "duration_seconds" in out["_delay"]
        assert "started_at" in out["_delay"]
        assert "finished_at" in out["_delay"]

    @pytest.mark.asyncio
    async def test_execute_non_dict_input_passes_through(self) -> None:
        """Non-dict input is passed through without _delay key."""
        node = DelayTransform()
        ctx = _make_context({"delayMs": 1})

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await node.execute(ctx, {"in": "just a string"})

        assert result.success is True
        assert result.outputs["out"] == "just a string"

    @pytest.mark.asyncio
    async def test_execute_list_input_passes_through(self) -> None:
        """List input passes through without modification."""
        node = DelayTransform()
        ctx = _make_context({"delaySeconds": 0.001})

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await node.execute(ctx, {"in": [1, 2, 3]})

        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_execute_delay_ms_takes_priority_over_seconds(self) -> None:
        """delayMs is used when both delayMs and delaySeconds are present."""
        node = DelayTransform()
        ctx = _make_context({"delayMs": 2, "delaySeconds": 10})

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await node.execute(ctx, {"in": {}})

        assert result.success is True
        # delayMs=2 means 0.002 seconds (delayMs has priority)
        assert mock_sleep.call_args[0][0] == pytest.approx(0.002, abs=1e-6)

    @pytest.mark.asyncio
    async def test_execute_delay_capped_at_5_minutes(self) -> None:
        """Delay is capped at 300 seconds regardless of config."""
        node = DelayTransform()
        # Pass a large value directly via config (bypassing validate_config)
        ctx = _make_context({"delaySeconds": 9999})

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await node.execute(ctx, {"in": {}})

        assert result.success is True
        assert mock_sleep.call_args[0][0] == 300.0

    @pytest.mark.asyncio
    async def test_execute_none_input(self) -> None:
        """None input is passed through."""
        node = DelayTransform()
        ctx = _make_context({"delayMs": 1})

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await node.execute(ctx, {"in": None})

        assert result.success is True
        assert result.outputs["out"] is None

    @pytest.mark.asyncio
    async def test_execute_zero_delay_timestamps_equal(self) -> None:
        """When delay is 0, started_at and finished_at are both set."""
        node = DelayTransform()
        ctx = _make_context({"delayMs": 0})

        result = await node.execute(ctx, {"in": {"a": 1}})
        assert result.success is True
        # Even at zero delay, _delay metadata is present when input is dict
        # (zero delay path sets started_at = finished_at without sleep)
        assert "_delay" in result.outputs["out"]
