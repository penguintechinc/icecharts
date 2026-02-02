#!/usr/bin/env python3
"""Action container server for Python runtime (OpenWhisk /init and /run pattern)."""

from flask import Flask, request, jsonify
import sys
import json
import importlib.util
import os

app = Flask(__name__)

# Global state for initialized action
action_module = None
action_function = None


@app.route('/init', methods=['POST'])
def init_action():
    """Initialize action with code (OpenWhisk pattern)."""
    global action_module, action_function

    data = request.json
    code = data.get('code')  # Python source code
    handler = data.get('handler')  # e.g., "main.process"

    # Write code to file
    with open('/tmp/action.py', 'w') as f:
        f.write(code)

    # Import module
    spec = importlib.util.spec_from_file_location("action", "/tmp/action.py")
    action_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(action_module)

    # Get handler function
    module_name, func_name = handler.rsplit('.', 1)
    action_function = getattr(action_module, func_name)

    return jsonify({'status': 'ready'})


@app.route('/run', methods=['POST'])
def run_action():
    """Execute action with input (OpenWhisk pattern)."""
    global action_function

    if action_function is None:
        return jsonify({'error': 'Action not initialized'}), 400

    input_data = request.json

    try:
        result = action_function(input_data)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
