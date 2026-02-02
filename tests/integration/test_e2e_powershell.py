"""End-to-end PowerShell runtime execution tests."""
import pytest


class TestPowerShellE2E:
    """End-to-end PowerShell script execution."""

    def test_powershell_hello_world(self, api_client, auth_token):
        """Test simple PowerShell hello world."""
        function_data = {
            'name': 'PowerShell Hello',
            'runtime': 'powershell',
            'entrypoint': 'handler.ps1',
            'handler': 'Invoke-Handler',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'name': 'World'}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_powershell_object_pipeline(self, api_client, auth_token):
        """Test PowerShell object pipeline processing."""
        function_data = {
            'name': 'PowerShell Pipeline',
            'runtime': 'powershell',
            'entrypoint': 'pipeline.ps1',
            'handler': 'Process-Objects',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'objects': [{'id': 1, 'name': 'obj1'}, {'id': 2, 'name': 'obj2'}]}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_powershell_json_handling(self, api_client, auth_token):
        """Test PowerShell JSON conversion."""
        function_data = {
            'name': 'PowerShell JSON',
            'runtime': 'powershell',
            'entrypoint': 'json_handler.ps1',
            'handler': 'ConvertTo-JSON',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'data': {'key': 'value', 'count': 42}}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_powershell_error_handling(self, api_client, auth_token):
        """Test PowerShell error handling."""
        function_data = {
            'name': 'PowerShell Error',
            'runtime': 'powershell',
            'entrypoint': 'main.ps1',
            'handler': 'Invoke-Main',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'error': True}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202, 400]

    def test_powershell_string_manipulation(self, api_client, auth_token):
        """Test PowerShell string operations."""
        function_data = {
            'name': 'PowerShell Strings',
            'runtime': 'powershell',
            'entrypoint': 'strings.ps1',
            'handler': 'Process-String',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'text': 'hello world', 'operation': 'ToUpper'}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_powershell_hashtable_processing(self, api_client, auth_token):
        """Test PowerShell hashtable operations."""
        function_data = {
            'name': 'PowerShell Hashtables',
            'runtime': 'powershell',
            'entrypoint': 'hashtables.ps1',
            'handler': 'Process-Hashtable',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'data': {'Name': 'Alice', 'Age': 30}}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_powershell_exit_code(self, api_client, auth_token):
        """Test PowerShell exit code."""
        function_data = {
            'name': 'PowerShell Exit',
            'runtime': 'powershell',
            'entrypoint': 'exit.ps1',
            'handler': 'Check-Status',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'success': True}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_powershell_env_variables(self, api_client, auth_token):
        """Test PowerShell environment variable access."""
        function_data = {
            'name': 'PowerShell Env',
            'runtime': 'powershell',
            'entrypoint': 'env.ps1',
            'handler': 'Get-Configuration',
            'env_vars': {
                'AZURE_SUBSCRIPTION': 'subscription-id',
                'RESOURCE_GROUP': 'my-rg',
            },
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_powershell_timeout(self, api_client, auth_token):
        """Test PowerShell timeout enforcement."""
        function_data = {
            'name': 'PowerShell Timeout',
            'runtime': 'powershell',
            'entrypoint': 'sleep.ps1',
            'handler': 'Start-Sleep-Function',
            'timeout_seconds': 5,
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'seconds': 10}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]
