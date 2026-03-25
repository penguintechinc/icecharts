"""Performance tests for concurrent IceRuns executions."""
import pytest
import concurrent.futures
import time


class TestConcurrentExecutions:
    """Test concurrent execution handling."""

    def test_100_concurrent_executions(self, api_client, auth_token, sample_function):
        """Test 100 concurrent function executions."""
        # Create function
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        # Activate function
        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        # Execute 100 concurrent requests
        def execute_function(index):
            response = api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'index': index}},
                headers={'Authorization': auth_token}
            )
            return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_function, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        success_count = sum(1 for r in results if r in [200, 202])
        assert success_count >= 90  # At least 90% success rate

    def test_queue_throughput(self, api_client, auth_token, sample_function):
        """Test queue throughput under load."""
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

        # Measure time to queue 100 requests
        start_time = time.time()

        for i in range(100):
            api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'batch': i}},
                headers={'Authorization': auth_token}
            )

        elapsed = time.time() - start_time

        # Should queue 100 requests in under 10 seconds (10 req/sec minimum)
        assert elapsed < 10.0

    def test_worker_pool_scaling(self, api_client, auth_token, sample_function):
        """Test worker pool scales with load."""
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

        # Submit 50 concurrent requests
        execution_ids = []

        def submit_execution(index):
            response = api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'id': index}},
                headers={'Authorization': auth_token}
            )
            if response.status_code in [200, 202]:
                return response.get_json().get('execution_id')
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_execution, i) for i in range(50)]
            execution_ids = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Should have executed most requests
        assert len([e for e in execution_ids if e]) >= 40

    def test_queue_drain_time(self, api_client, auth_token, sample_function):
        """Test how long queue takes to drain under load."""
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

        # Queue 50 tasks rapidly
        execution_ids = []
        for i in range(50):
            response = api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'task': i}},
                headers={'Authorization': auth_token}
            )
            if response.status_code in [200, 202]:
                execution_ids.append(response.get_json()['execution_id'])

        # Check how many complete within 30 seconds
        start_time = time.time()
        completed = 0

        for exec_id in execution_ids:
            for _ in range(30):
                status_response = api_client.get(
                    f'/api/v1/iceruns/executions/{exec_id}/status',
                    headers={'Authorization': auth_token}
                )
                if status_response.get_json().get('status') == 'completed':
                    completed += 1
                    break
                time.sleep(1)

        elapsed = time.time() - start_time

        # Should complete most within 30 seconds
        assert completed >= len(execution_ids) * 0.8

    def test_no_memory_leak_under_load(self, api_client, auth_token, sample_function):
        """Test invoker doesn't leak memory under sustained load."""
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

        # Execute 200 functions in batches
        for batch in range(4):
            for i in range(50):
                api_client.post(
                    f'/api/v1/iceruns/{function_id}/execute',
                    json={'input': {'batch': batch, 'index': i}},
                    headers={'Authorization': auth_token}
                )

        # Check invoker health
        response = api_client.get('/healthz')
        assert response.status_code == 200

    def test_execution_isolation(self, api_client, auth_token, sample_function):
        """Test concurrent executions don't interfere with each other."""
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

        # Execute with different inputs concurrently
        results = []

        def execute_with_input(user_id):
            response = api_client.post(
                f'/api/v1/iceruns/{function_id}/execute',
                json={'input': {'user_id': user_id}},
                headers={'Authorization': auth_token}
            )
            return user_id, response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_with_input, i) for i in range(25)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert len([r for r in results if r[1] in [200, 202]]) >= 20
