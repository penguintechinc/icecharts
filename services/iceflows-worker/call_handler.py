"""
Call Handler Module - Triggers IceStreams playbooks and IceRuns functions.

This module provides the CallHandler class that orchestrates triggering of
IceStreams playbooks and IceRuns functions from IceFlows pipelines, including
template rendering, API communication, and execution status polling.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class CallResult:
    """Result of a single call execution."""

    call_id: str
    name: str
    call_type: str
    success: bool
    execution_id: Optional[str]
    status: str  # "completed", "failed", "timeout", "error"
    output: Optional[Dict[str, Any]]
    duration_seconds: float
    started_at: datetime
    finished_at: datetime
    is_blocking: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "call_id": self.call_id,
            "name": self.name,
            "call_type": self.call_type,
            "success": self.success,
            "execution_id": self.execution_id,
            "status": self.status,
            "output": self.output,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "is_blocking": self.is_blocking,
            "error_message": self.error_message,
        }


class CallHandler:
    """Handles triggering IceStreams playbooks and IceRuns functions."""

    def __init__(
        self,
        api_base_url: str,
        api_token: str,
        timeout_seconds: int = 60,
    ):
        """
        Initialize the Call Handler.

        Args:
            api_base_url: Base URL for the IceCharts API (e.g., http://api:5000)
            api_token: Service account JWT token for authentication
            timeout_seconds: Default timeout for API calls (default: 60)
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.api_token = api_token
        self.timeout_seconds = timeout_seconds
        self.session = self._create_session()

        logger.info(
            f"CallHandler initialized: api_base_url={self.api_base_url}, "
            f"timeout_seconds={self.timeout_seconds}"
        )

    def _create_session(self) -> requests.Session:
        """Create and configure requests session with auth headers."""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        })
        return session

    def execute_call(
        self,
        call_config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> CallResult:
        """
        Execute a single call.

        Args:
            call_config: Call configuration from iceflows_stage_calls table
            context: Execution context for template substitution

        Returns:
            CallResult object with execution details
        """
        started_at = datetime.utcnow()
        call_id = call_config.get("call_id", "unknown")
        name = call_config.get("name", "Unknown Call")
        call_type = call_config.get("call_type", "unknown")
        target_id = call_config.get("target_id")
        input_template = call_config.get("input_template", {})
        timeout_seconds = call_config.get(
            "timeout_seconds", self.timeout_seconds
        )
        is_blocking = call_config.get("is_blocking", True)

        logger.info(
            f"Executing call: call_id={call_id}, name={name}, "
            f"call_type={call_type}, target_id={target_id}"
        )

        execution_id = None
        status = "error"
        success = False
        output = None
        error_message = None

        try:
            if not target_id:
                raise ValueError("target_id is required in call configuration")

            if not call_type or call_type not in ["icestreams", "iceruns"]:
                raise ValueError(
                    f"Invalid call_type: {call_type}. "
                    "Must be 'icestreams' or 'iceruns'"
                )

            # Render input template with context
            input_data = self._render_template(input_template, context)
            logger.debug(f"Rendered input data: {input_data}")

            # Trigger the appropriate service
            if call_type == "icestreams":
                result = self._trigger_icestreams(target_id, input_data)
            else:  # iceruns
                result = self._trigger_iceruns(target_id, input_data)

            execution_id = result.get("execution_id")
            logger.info(
                f"Call triggered successfully: execution_id={execution_id}"
            )

            # Poll for completion if blocking
            if is_blocking:
                status_result = self._poll_execution_status(
                    execution_id,
                    call_type,
                    timeout_seconds,
                )
                status = status_result.get("status", "error")
                success = status == "completed"
                output = status_result.get("output")
                error_message = status_result.get("error_message")

                logger.info(
                    f"Polling completed: status={status}, success={success}"
                )
            else:
                # Non-blocking call is considered successful if triggered
                status = "triggered"
                success = True
                logger.info("Non-blocking call triggered successfully")

        except requests.RequestException as e:
            logger.error(f"API request failed for call {call_id}: {e}")
            error_message = f"API request failed: {str(e)}"
            status = "error"
        except ValueError as e:
            logger.error(f"Configuration error for call {call_id}: {e}")
            error_message = f"Configuration error: {str(e)}"
            status = "error"
        except Exception as e:
            logger.error(f"Unexpected error executing call {call_id}: {e}", exc_info=True)
            error_message = f"Unexpected error: {str(e)}"
            status = "error"

        finished_at = datetime.utcnow()
        duration_seconds = (finished_at - started_at).total_seconds()

        result = CallResult(
            call_id=call_id,
            name=name,
            call_type=call_type,
            success=success,
            execution_id=execution_id,
            status=status,
            output=output,
            duration_seconds=duration_seconds,
            started_at=started_at,
            finished_at=finished_at,
            is_blocking=is_blocking,
            error_message=error_message,
        )

        logger.info(
            f"Call execution finished: call_id={call_id}, success={success}, "
            f"duration={duration_seconds:.2f}s"
        )

        return result

    def execute_calls(
        self,
        call_configs: List[Dict[str, Any]],
        context: Dict[str, Any],
        trigger_phase: str = "post_merge",
    ) -> List[CallResult]:
        """
        Execute multiple calls filtered by trigger phase.

        Args:
            call_configs: List of call configurations
            context: Execution context for template substitution
            trigger_phase: Phase to filter calls ("pre_merge", "post_merge", "on_approval")

        Returns:
            List of CallResult objects
        """
        logger.info(
            f"Executing {len(call_configs)} call(s) for phase: {trigger_phase}"
        )

        results = []

        # Filter calls by trigger phase
        filtered_calls = [
            call for call in call_configs
            if call.get("trigger_on") == trigger_phase
        ]

        logger.info(
            f"Filtered to {len(filtered_calls)} call(s) for phase {trigger_phase}"
        )

        for idx, call_config in enumerate(filtered_calls):
            logger.info(
                f"Executing call {idx + 1}/{len(filtered_calls)}: "
                f"{call_config.get('name', 'Unknown')}"
            )

            result = self.execute_call(call_config, context)
            results.append(result)

            # If call is blocking and failed, log warning but continue
            if result.is_blocking and not result.success:
                logger.warning(
                    f"Blocking call {result.name} failed: "
                    f"{result.error_message}"
                )

        logger.info(
            f"All {len(filtered_calls)} call(s) completed. "
            f"Success rate: {sum(1 for r in results if r.success)}/{len(results)}"
        )

        return results

    def _trigger_icestreams(
        self,
        playbook_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Trigger an IceStreams playbook via API.

        Args:
            playbook_id: UUID of the playbook to execute
            input_data: Input data for the playbook

        Returns:
            Dictionary containing execution_id and response data

        Raises:
            RequestException: If API call fails
            ValueError: If response is invalid
        """
        endpoint = f"/api/v1/playbooks/{playbook_id}/execute"
        url = f"{self.api_base_url}{endpoint}"

        logger.info(f"Triggering IceStreams playbook: {playbook_id}")

        try:
            response = self.session.post(
                url,
                json={"input": input_data},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()
            execution_id = data.get("execution_id")

            if not execution_id:
                raise ValueError(
                    "API response missing execution_id"
                )

            logger.info(
                f"IceStreams playbook triggered: execution_id={execution_id}"
            )

            return {
                "execution_id": execution_id,
                "response": data,
            }

        except requests.RequestException as e:
            logger.error(
                f"Failed to trigger IceStreams playbook {playbook_id}: {e}"
            )
            raise

    def _trigger_iceruns(
        self,
        function_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Trigger an IceRuns function via API.

        Args:
            function_id: UUID of the function to invoke
            input_data: Input data for the function

        Returns:
            Dictionary containing execution_id and response data

        Raises:
            RequestException: If API call fails
            ValueError: If response is invalid
        """
        endpoint = f"/api/v1/iceruns/functions/{function_id}/invoke"
        url = f"{self.api_base_url}{endpoint}"

        logger.info(f"Triggering IceRuns function: {function_id}")

        try:
            response = self.session.post(
                url,
                json={"params": input_data},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()
            execution_id = data.get("execution_id")

            if not execution_id:
                raise ValueError(
                    "API response missing execution_id"
                )

            logger.info(
                f"IceRuns function triggered: execution_id={execution_id}"
            )

            return {
                "execution_id": execution_id,
                "response": data,
            }

        except requests.RequestException as e:
            logger.error(
                f"Failed to trigger IceRuns function {function_id}: {e}"
            )
            raise

    def _poll_execution_status(
        self,
        execution_id: str,
        call_type: str,
        timeout: int,
    ) -> Dict[str, Any]:
        """
        Poll for execution completion status.

        Args:
            execution_id: UUID of the execution to poll
            call_type: Type of call ("icestreams" or "iceruns")
            timeout: Maximum time to wait in seconds

        Returns:
            Dictionary with status, output, and error_message
        """
        if call_type == "icestreams":
            endpoint = f"/api/v1/playbooks/executions/{execution_id}"
        elif call_type == "iceruns":
            endpoint = f"/api/v1/iceruns/executions/{execution_id}"
        else:
            raise ValueError(f"Invalid call_type: {call_type}")

        url = f"{self.api_base_url}{endpoint}"
        start_time = time.time()
        poll_interval = 1  # Start with 1 second
        max_poll_interval = 10  # Max 10 seconds between polls

        logger.info(
            f"Polling execution status: execution_id={execution_id}, "
            f"timeout={timeout}s"
        )

        while True:
            elapsed = time.time() - start_time

            if elapsed > timeout:
                logger.warning(
                    f"Execution {execution_id} polling timed out after {timeout}s"
                )
                return {
                    "status": "timeout",
                    "error_message": f"Execution did not complete within {timeout} seconds",
                }

            try:
                response = self.session.get(url, timeout=self.timeout_seconds)
                response.raise_for_status()

                data = response.json()
                status = data.get("status")

                logger.debug(
                    f"Poll result: execution_id={execution_id}, status={status}"
                )

                # Check if execution is complete
                if status in ["completed", "failed", "error", "cancelled"]:
                    logger.info(
                        f"Execution complete: execution_id={execution_id}, "
                        f"status={status}"
                    )

                    return {
                        "status": status if status == "completed" else "failed",
                        "output": data.get("output"),
                        "error_message": data.get("error_message"),
                    }

                # Not complete yet, wait before next poll
                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, max_poll_interval)

            except requests.RequestException as e:
                logger.error(f"Error polling execution {execution_id}: {e}")

                # Continue polling on transient errors
                if elapsed + self.timeout_seconds < timeout:
                    time.sleep(poll_interval)
                    poll_interval = min(poll_interval * 1.5, max_poll_interval)
                else:
                    return {
                        "status": "error",
                        "error_message": f"API error during polling: {str(e)}",
                    }

    def _render_template(
        self,
        template: Any,
        context: Dict[str, Any],
    ) -> Any:
        """
        Recursively render template with context variable substitution.

        Substitutes {{var}} placeholders with values from context dictionary.

        Args:
            template: Template to render (string, dict, list, or other)
            context: Dictionary of variables for substitution

        Returns:
            Rendered template with substitutions applied
        """
        if isinstance(template, str):
            # Replace {{var}} patterns with context values
            result = template
            for key, value in context.items():
                pattern = f"{{{{{key}}}}}"
                result = result.replace(pattern, str(value))
            return result

        elif isinstance(template, dict):
            # Recursively render dictionary values
            return {
                key: self._render_template(value, context)
                for key, value in template.items()
            }

        elif isinstance(template, list):
            # Recursively render list items
            return [
                self._render_template(item, context)
                for item in template
            ]

        else:
            # Return non-string/dict/list values as-is
            return template

    def _make_api_request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> requests.Response:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method ("GET", "POST", etc.)
            endpoint: API endpoint (e.g., "/api/v1/playbooks")
            **kwargs: Additional arguments to pass to requests

        Returns:
            requests.Response object

        Raises:
            RequestException: If request fails
        """
        url = f"{self.api_base_url}{endpoint}"

        logger.debug(f"API request: {method} {endpoint}")

        response = self.session.request(
            method,
            url,
            timeout=kwargs.pop("timeout", self.timeout_seconds),
            **kwargs,
        )

        logger.debug(f"API response: {response.status_code}")

        return response
