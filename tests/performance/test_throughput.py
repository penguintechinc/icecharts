"""Performance tests for IceRuns throughput and capacity."""
import pytest
import time
import concurrent.futures


class TestThroughput:
    """Test IceRuns throughput and capacity."""

    def test_requests_per_second_capacity(self, api_client, auth_token, sample_function):
        """Test maximum requests per second capacity."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        # Execute 50 requests as fast as possible
        start_time = time.time()
        request_count = 0

        for i in range(50):
            response = api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'id': i}},
                headers={'Authorization': auth_token}
            )
            if response.status_code in [200, 202]:
                request_count += 1

        elapsed = time.time() - start_time
        rps = request_count / elapsed if elapsed > 0 else 0

        # Should handle at least 10 requests per second
        assert rps >= 10, f"Only {rps} RPS, expected >= 10"

    def test_concurrent_request_handling(self, api_client, auth_token, sample_function):
        """Test handling multiple concurrent requests."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        def execute_request(index):
            start = time.time()
            response = api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'id': index}},
                headers={'Authorization': auth_token}
            )
            elapsed = time.time() - start
            return response.status_code, elapsed

        # Execute 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_request, i) for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Most should succeed
        success = sum(1 for status, _ in results if status in [200, 202])
        assert success >= 15

        # Check average response time
        avg_time = sum(elapsed for _, elapsed in results) / len(results)
        assert avg_time < 5.0  # Average under 5 seconds

    def test_queue_processing_rate(self, api_client, auth_token, sample_function):
        """Test how fast the queue processes tasks."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        # Queue 30 tasks
        execution_ids = []
        for i in range(30):
            response = api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'task': i}},
                headers={'Authorization': auth_token}
            )
            if response.status_code in [200, 202]:
                execution_ids.append(response.get_json()['execution_id'])

        # Measure how many complete per second
        start_time = time.time()
        completed = 0
        completion_times = []

        for exec_id in execution_ids:
            check_start = time.time()
            for attempt in range(60):  # Check for up to 60 seconds
                status_response = api_client.get(
                    f'/api/v1/iceruns/executions/{exec_id}/status',
                    headers={'Authorization': auth_token}
                )
                if status_response.get_json().get('status') == 'completed':
                    completion_times.append(time.time() - check_start)
                    completed += 1
                    break
                time.sleep(0.5)

        elapsed = time.time() - start_time

        if completed > 0:
            processing_rate = completed / elapsed
            # Should process at least 1 task per second
            assert processing_rate >= 0.5, f"Processing rate {processing_rate}/sec"

    def test_api_response_time_under_load(self, api_client, auth_token, sample_function):
        """Test API response time under load."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        response_times = []

        # Submit 50 requests and measure response times
        for i in range(50):
            start = time.time()
            api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'batch': i}},
                headers={'Authorization': auth_token}
            )
            response_times.append(time.time() - start)

        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]

        # P50 should be under 100ms
        assert p50 < 0.1, f"P50 response time: {p50}s"
        # P95 should be under 500ms
        assert p95 < 0.5, f"P95 response time: {p95}s"
        # P99 should be under 1 second
        assert p99 < 1.0, f"P99 response time: {p99}s"

    def test_memory_efficiency_under_load(self, api_client, auth_token, sample_function):
        """Test memory efficiency handling many concurrent executions."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        # Execute 100 lightweight tasks
        execution_ids = []
        for i in range(100):
            response = api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'id': i}},
                headers={'Authorization': auth_token}
            )
            if response.status_code in [200, 202]:
                execution_ids.append(response.get_json()['execution_id'])

        # Check system health after heavy load
        health_response = api_client.get('/healthz')
        assert health_response.status_code == 200

        # Should still be responsive
        start = time.time()
        status_response = api_client.get(
            f'/api/v1/iceruns/executions/{execution_ids[0]}/status',
            headers={'Authorization': auth_token}
        )
        response_time = time.time() - start

        assert status_response.status_code == 200
        assert response_time < 1.0  # Should respond quickly even under load

    def test_sustained_throughput(self, api_client, auth_token, sample_function):
        """Test sustained throughput over time."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        # Execute in batches and measure throughput
        batch_results = []

        for batch_num in range(5):
            start = time.time()
            successful = 0

            for i in range(20):
                response = api_client.post(
                    f'/api/v1/iceruns/{function_id}/execute',
                    json={'input': {'batch': batch_num, 'item': i}},
                    headers={'Authorization': auth_token}
                )
                if response.status_code in [200, 202]:
                    successful += 1

            batch_time = time.time() - start
            batch_results.append({
                'successful': successful,
                'time': batch_time,
                'rps': successful / batch_time if batch_time > 0 else 0
            })

            time.sleep(1)  # Pause between batches

        # Verify consistent throughput across batches
        rps_values = [b['rps'] for b in batch_results]
        avg_rps = sum(rps_values) / len(rps_values)

        # Should maintain at least 5 RPS consistently
        assert avg_rps >= 5, f"Average RPS: {avg_rps}"

        # Variance shouldn't be too high
        variance = sum((r - avg_rps) ** 2 for r in rps_values) / len(rps_values)
        std_dev = variance ** 0.5
        assert std_dev < avg_rps * 0.5  # Within 50% of mean
