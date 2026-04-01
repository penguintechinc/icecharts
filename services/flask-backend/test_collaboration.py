#!/usr/bin/env python3
"""Simple test script for collaboration service and WebSocket handlers."""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))


def test_imports():
    """Test that all modules import correctly."""
    try:
        print("Testing imports...")

        # Test collaboration service import
        from app.services.collaboration_service import CollaborationService

        print("✓ CollaborationService imported successfully")

        # Test collaboration socket import
        # Note: This requires SocketIO to be initialized, so we'll skip full import
        # Just check the file exists and has valid syntax
        import ast

        socket_file = os.path.join(
            os.path.dirname(__file__), "app/api/v1/collaboration_socket.py"
        )
        with open(socket_file, "r") as f:
            code = f.read()
            ast.parse(code)
        print("✓ collaboration_socket.py has valid syntax")

        # Test service file syntax
        service_file = os.path.join(
            os.path.dirname(__file__), "app/services/collaboration_service.py"
        )
        with open(service_file, "r") as f:
            code = f.read()
            ast.parse(code)
        print("✓ collaboration_service.py has valid syntax")

        print("\n✅ All tests passed!")
        return True

    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
