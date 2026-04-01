"""
IceRuns Example: Python Hello World

This is a simple Python function that demonstrates basic IceRuns functionality.

Handler: main.handler
Entrypoint: main.py
"""


def handler(event):
    """
    Simple hello world handler.

    Args:
        event (dict): Input data containing 'name' parameter

    Returns:
        dict: Greeting message and metadata
    """
    # Get name from input, default to 'World'
    name = event.get("name", "World")

    # Validate input
    if not isinstance(name, str):
        return {"error": "name must be a string", "success": False}

    # Return result
    return {"message": f"Hello, {name}!", "input": event, "success": True}


if __name__ == "__main__":
    # Local testing
    test_event = {"name": "IceRuns"}
    result = handler(test_event)
    print(result)
