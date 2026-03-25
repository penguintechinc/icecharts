"""
Shared test configuration for IceStreams Worker tests.

Handles the cross-package relative import issue: some node modules
(e.g., nodes/actions/http_request.py) use relative imports like
``from ...executor.node_registry`` which fails because ``nodes/``
and ``executor/`` are sibling top-level packages with no shared parent.

The import hook below intercepts failing relative imports and retries
them as absolute imports, allowing tests to import these modules
without changing production code.
"""

import builtins
import os
import sys

worker_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if worker_root not in sys.path:
    sys.path.insert(0, worker_root)

# --- Cross-package relative import fix ---
_real_import = builtins.__import__


def _patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Intercept relative imports that cross package boundaries."""
    try:
        return _real_import(name, globals, locals, fromlist, level)
    except ImportError:
        if level > 0:
            # Retry as absolute import for cross-package references
            return _real_import(name, globals, locals, fromlist, 0)
        raise


builtins.__import__ = _patched_import
