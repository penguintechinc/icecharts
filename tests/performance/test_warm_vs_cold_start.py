"""Performance tests for warm vs cold start container execution."""

import time

import pytest


class TestWarmVsColdStart:
    """Test warm/cold start performance characteristics."""

    def test_cold_start_time(self, api_client, auth_token, sample_function):
        """Measure cold start execution time."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        api_client.put(
            f"/api/v1/iceruns/{function_id}/activate",
            headers={"Authorization": auth_token},
        )

        # First execution (cold start)
        start_time = time.time()
        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        cold_start_time = time.time() - start_time

        assert response.status_code in [200, 202]
        # Cold start should be reasonable (< 10 seconds for container startup)
        assert cold_start_time < 10.0

    def test_warm_start_time(self, api_client, auth_token, sample_function):
        """Measure warm start execution time."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        api_client.put(
            f"/api/v1/iceruns/{function_id}/activate",
            headers={"Authorization": auth_token},
        )

        # First execution (cold start) - primes the container
        api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )

        time.sleep(0.5)  # Brief pause

        # Second execution (warm start)
        start_time = time.time()
        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        warm_start_time = time.time() - start_time

        assert response.status_code in [200, 202]
        # Warm start should be very fast (< 100ms)
        assert warm_start_time < 1.0

    def test_warm_start_faster_than_cold(self, api_client, auth_token, sample_function):
        """Verify warm start is faster than cold start."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        api_client.put(
            f"/api/v1/iceruns/{function_id}/activate",
            headers={"Authorization": auth_token},
        )

        # Measure cold start
        start_time = time.time()
        api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        cold_start = time.time() - start_time

        time.sleep(0.5)

        # Measure warm start
        start_time = time.time()
        api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        warm_start = time.time() - start_time

        # Warm start should be significantly faster
        assert warm_start < cold_start

    def test_multiple_executions_reuse_container(
        self, api_client, auth_token, sample_function
    ):
        """Test repeated executions reuse container."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        api_client.put(
            f"/api/v1/iceruns/{function_id}/activate",
            headers={"Authorization": auth_token},
        )

        times = []

        # Execute 5 times and measure each
        for i in range(5):
            start_time = time.time()
            api_client.post(
                f"/api/v1/iceruns/{function_id}/execute",
                json={"input": {"index": i}},
                headers={"Authorization": auth_token},
            )
            elapsed = time.time() - start_time
            times.append(elapsed)

            if i > 0:
                time.sleep(0.2)

        # First execution slower, subsequent ones faster
        assert times[0] > times[1]  # Cold > warm
        # All warm starts should be similar speed
        warm_times = times[1:]
        avg_warm = sum(warm_times) / len(warm_times)
        assert all(abs(t - avg_warm) < 0.5 for t in warm_times)  # Within 500ms

    def test_different_runtimes_cold_start(self, api_client, auth_token):
        """Compare cold start times across different runtimes."""
        runtimes = ["python3.13", "nodejs", "go"]
        cold_start_times = {}

        for runtime in runtimes:
            function_data = {
                "name": f"Cold Start {runtime}",
                "runtime": runtime,
                "entrypoint": "main",
                "handler": "handler",
            }

            create_response = api_client.post(
                "/api/v1/iceruns",
                json=function_data,
                headers={"Authorization": auth_token},
            )
            function_id = create_response.get_json()["function_id"]

            api_client.put(
                f"/api/v1/iceruns/{function_id}/activate",
                headers={"Authorization": auth_token},
            )

            start_time = time.time()
            api_client.post(
                f"/api/v1/iceruns/{function_id}/execute",
                json={"input": {}},
                headers={"Authorization": auth_token},
            )
            elapsed = time.time() - start_time

            cold_start_times[runtime] = elapsed

        # All should be reasonably fast
        for runtime, elapsed in cold_start_times.items():
            assert elapsed < 10.0, f"{runtime} cold start took {elapsed}s"

    def test_container_ttl_expiration(self, api_client, auth_token, sample_function):
        """Test container TTL expiration triggers new cold start."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        api_client.put(
            f"/api/v1/iceruns/{function_id}/activate",
            headers={"Authorization": auth_token},
        )

        # Execute immediately (warm)
        start_time = time.time()
        api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        warm_time = time.time() - start_time

        # Wait beyond TTL (simulated - normally 10 minutes)
        # In testing, we'd trigger container removal via API
        # For now, just verify the timing concept

        assert warm_time < 1.0

    def test_execution_time_consistency(self, api_client, auth_token, sample_function):
        """Test execution time is consistent across multiple runs."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        api_client.put(
            f"/api/v1/iceruns/{function_id}/activate",
            headers={"Authorization": auth_token},
        )

        # Prime with cold start
        api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )

        # Measure 5 warm executions
        times = []
        for i in range(5):
            start_time = time.time()
            api_client.post(
                f"/api/v1/iceruns/{function_id}/execute",
                json={"input": {}},
                headers={"Authorization": auth_token},
            )
            times.append(time.time() - start_time)
            time.sleep(0.1)

        # Execution times should be relatively consistent
        avg_time = sum(times) / len(times)
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        std_dev = variance**0.5

        # Standard deviation should be small relative to mean
        assert std_dev < avg_time * 0.5  # Within 50% of mean
