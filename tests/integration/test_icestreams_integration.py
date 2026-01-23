"""Tests for IceRuns integration with IceStreams playbooks."""
import pytest


class TestIceStreamsIntegration:
    """Test IceRuns nodes within IceStreams playbooks."""

    def test_icerun_execute_node_in_playbook(self, api_client, auth_token):
        """Test IceRun Execute node in playbook."""
        # Create playbook with IceRun node
        playbook_data = {
            'name': 'Test Playbook with IceRun',
            'description': 'Playbook containing IceRun execution',
            'triggers': [
                {
                    'type': 'webhook',
                    'endpoint': '/webhook/test',
                }
            ],
            'nodes': [
                {
                    'id': 'node_1',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'test_function_id',
                        'input_mode': 'from_previous',
                    }
                }
            ],
        }

        response = api_client.post(
            '/api/v1/playbooks',
            json=playbook_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 201]

    def test_icerun_node_with_static_input(self, api_client, auth_token):
        """Test IceRun node with static input configuration."""
        playbook_data = {
            'name': 'Static Input Playbook',
            'nodes': [
                {
                    'id': 'node_1',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'test_function_id',
                        'input_mode': 'static',
                        'input_json': {
                            'user_id': 123,
                            'action': 'generate_report',
                        }
                    }
                }
            ],
        }

        response = api_client.post(
            '/api/v1/playbooks',
            json=playbook_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 201]

    def test_icerun_wait_node(self, api_client, auth_token):
        """Test IceRun Wait for Completion node."""
        playbook_data = {
            'name': 'Async Wait Playbook',
            'nodes': [
                {
                    'id': 'node_1',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'test_function_id',
                        'async': True,
                    }
                },
                {
                    'id': 'node_2',
                    'type': 'iceruns.wait_for_completion',
                    'config': {
                        'timeout_seconds': 300,
                    }
                }
            ],
        }

        response = api_client.post(
            '/api/v1/playbooks',
            json=playbook_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 201]

    def test_icerun_node_data_flow(self, api_client, auth_token):
        """Test data flow from previous node to IceRun node."""
        playbook_data = {
            'name': 'Data Flow Playbook',
            'nodes': [
                {
                    'id': 'node_transform',
                    'type': 'transform.map',
                    'config': {
                        'expression': '{"doubled": .value * 2}'
                    }
                },
                {
                    'id': 'node_icerun',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'test_function_id',
                        'input_mode': 'from_previous',
                    }
                }
            ],
            'edges': [
                {
                    'from': 'node_transform',
                    'to': 'node_icerun',
                }
            ],
        }

        response = api_client.post(
            '/api/v1/playbooks',
            json=playbook_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 201]

    def test_icerun_node_with_timeout_override(self, api_client, auth_token):
        """Test IceRun node with timeout override."""
        playbook_data = {
            'name': 'Timeout Override Playbook',
            'nodes': [
                {
                    'id': 'node_1',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'test_function_id',
                        'timeout_override': 120,
                        'input_mode': 'from_previous',
                    }
                }
            ],
        }

        response = api_client.post(
            '/api/v1/playbooks',
            json=playbook_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 201]

    def test_icerun_node_in_conditional_branch(self, api_client, auth_token):
        """Test IceRun node in conditional branch."""
        playbook_data = {
            'name': 'Conditional IceRun Playbook',
            'nodes': [
                {
                    'id': 'node_check',
                    'type': 'condition.if',
                    'config': {
                        'expression': '.value > 100',
                    }
                },
                {
                    'id': 'node_icerun',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'test_function_id',
                    }
                }
            ],
        }

        response = api_client.post(
            '/api/v1/playbooks',
            json=playbook_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 201]

    def test_icerun_node_error_handling(self, api_client, auth_token):
        """Test IceRun node with error handling."""
        playbook_data = {
            'name': 'Error Handling Playbook',
            'nodes': [
                {
                    'id': 'node_icerun',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'test_function_id',
                    }
                },
                {
                    'id': 'node_error_handler',
                    'type': 'action.notify',
                    'config': {
                        'message': 'Execution failed',
                    }
                }
            ],
        }

        response = api_client.post(
            '/api/v1/playbooks',
            json=playbook_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 201]

    def test_multiple_icerun_nodes_in_playbook(self, api_client, auth_token):
        """Test playbook with multiple IceRun nodes."""
        playbook_data = {
            'name': 'Multiple IceRun Playbook',
            'nodes': [
                {
                    'id': 'node_process',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'function_1',
                        'input_mode': 'from_previous',
                    }
                },
                {
                    'id': 'node_validate',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'function_2',
                        'input_mode': 'from_previous',
                    }
                },
                {
                    'id': 'node_store',
                    'type': 'iceruns.execute',
                    'config': {
                        'function_id': 'function_3',
                        'input_mode': 'from_previous',
                    }
                }
            ],
        }

        response = api_client.post(
            '/api/v1/playbooks',
            json=playbook_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 201]

    def test_icerun_node_palette_availability(self, api_client, auth_token):
        """Test IceRun nodes are available in node palette."""
        response = api_client.get(
            '/api/v1/playbooks/node-palette',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()

        # Check if iceruns category exists
        categories = [c for c in data.get('categories', []) if c.get('name') == 'iceruns']
        assert len(categories) > 0
