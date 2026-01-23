"""Scope definitions for service account authorization.

This module defines available scopes for service accounts and provides
utility functions for scope validation.

Role-Based Scope Assignments:
- Admin: All scopes including iceruns:admin, iceflows:admin
- Maintainer: Standard scopes including iceruns:read, iceruns:write, iceruns:execute, iceruns:logs,
             iceflows:read, iceflows:write, iceflows:execute, iceflows:approve
- Viewer: Read-only scopes including iceruns:read, iceruns:logs, iceflows:read
"""

from typing import List, Set

# Available scopes with descriptions
AVAILABLE_SCOPES = {
    # Drawings
    "drawings:read": "Read drawing metadata and content",
    "drawings:write": "Create and update drawings",
    "drawings:delete": "Delete drawings",
    # Exports
    "exports:create": "Generate exports (PNG, PDF, SVG, JSON)",
    "exports:read": "Download export results",
    # Templates
    "templates:read": "Read available templates",
    "templates:write": "Create and modify templates",
    # Collections
    "collections:read": "Read collections",
    "collections:write": "Manage collections",
    # Playbooks (IceStreams)
    "playbooks:read": "Read playbook metadata, canvas, and executions",
    "playbooks:write": "Create, update, and configure playbooks",
    "playbooks:delete": "Delete playbooks",
    "playbooks:execute": "Execute playbooks and manage executions",
    # IceRuns
    "iceruns:read": "View IceRuns function definitions and configurations",
    "iceruns:write": "Create and update IceRuns functions",
    "iceruns:delete": "Delete IceRuns functions",
    "iceruns:execute": "Execute IceRuns functions via API or webhook",
    "iceruns:logs": "View IceRuns execution logs and outputs",
    "iceruns:admin": "Full administrative access to IceRuns",
    # IceFlows (CI/CD Pipelines)
    "iceflows:read": "Read IceFlows pipelines, stages, and execution history",
    "iceflows:write": "Create and modify IceFlows pipelines and stages",
    "iceflows:delete": "Delete IceFlows pipelines and related resources",
    "iceflows:execute": "Trigger IceFlows pipeline executions and promotions",
    "iceflows:approve": "Approve or reject stage promotion requests",
    "iceflows:admin": "Full administrative access to IceFlows",
}

# Convenience scope groups for common use cases
SCOPE_GROUPS = {
    "integration_standard": [
        "drawings:read",
        "drawings:write",
        "exports:create",
        "templates:read",
    ],
    "drawings_full": [
        "drawings:read",
        "drawings:write",
        "drawings:delete",
    ],
    "playbooks_full": [
        "playbooks:read",
        "playbooks:write",
        "playbooks:delete",
        "playbooks:execute",
    ],
    "automation": [
        "playbooks:read",
        "playbooks:execute",
    ],
    "readonly": [
        "drawings:read",
        "exports:read",
        "templates:read",
        "collections:read",
        "playbooks:read",
    ],
    "iceruns_full": [
        "iceruns:read",
        "iceruns:write",
        "iceruns:delete",
        "iceruns:execute",
        "iceruns:logs",
    ],
    "iceruns_readonly": [
        "iceruns:read",
        "iceruns:logs",
    ],
    "iceruns_execute_only": [
        "iceruns:execute",
    ],
    "iceflows_full": [
        "iceflows:read",
        "iceflows:write",
        "iceflows:delete",
        "iceflows:execute",
        "iceflows:approve",
    ],
    "iceflows_admin": [
        "iceflows:admin",
    ],
    "iceflows_operator": [
        "iceflows:read",
        "iceflows:execute",
        "iceflows:approve",
    ],
    "iceflows_readonly": [
        "iceflows:read",
    ],
}


def is_valid_scope(scope: str) -> bool:
    """
    Check if a scope is valid.

    Args:
        scope: The scope string to validate

    Returns:
        True if the scope is valid, False otherwise
    """
    return scope in AVAILABLE_SCOPES


def validate_scopes(scopes: List[str]) -> tuple[bool, List[str]]:
    """
    Validate a list of scopes.

    Args:
        scopes: List of scope strings to validate

    Returns:
        Tuple of (is_valid, invalid_scopes)
    """
    invalid = [s for s in scopes if s not in AVAILABLE_SCOPES]
    return len(invalid) == 0, invalid


def expand_scope_group(group_name: str) -> List[str]:
    """
    Expand a scope group to its individual scopes.

    Args:
        group_name: Name of the scope group

    Returns:
        List of individual scopes in the group, or empty list if group not found
    """
    return SCOPE_GROUPS.get(group_name, [])


def get_all_scope_names() -> List[str]:
    """
    Get all available scope names.

    Returns:
        List of all available scope names
    """
    return list(AVAILABLE_SCOPES.keys())


def has_scope(token_scopes: List[str], required_scope: str) -> bool:
    """
    Check if a token has the required scope.

    Args:
        token_scopes: List of scopes from the token
        required_scope: The scope required for access

    Returns:
        True if the token has the required scope
    """
    return required_scope in token_scopes


def has_all_scopes(token_scopes: List[str], required_scopes: List[str]) -> bool:
    """
    Check if a token has all required scopes.

    Args:
        token_scopes: List of scopes from the token
        required_scopes: List of scopes required for access

    Returns:
        True if the token has all required scopes
    """
    return set(required_scopes).issubset(set(token_scopes))


def has_any_scope(token_scopes: List[str], required_scopes: List[str]) -> bool:
    """
    Check if a token has any of the required scopes.

    Args:
        token_scopes: List of scopes from the token
        required_scopes: List of scopes, any one of which grants access

    Returns:
        True if the token has at least one of the required scopes
    """
    return bool(set(token_scopes) & set(required_scopes))


def get_missing_scopes(
    token_scopes: List[str], required_scopes: List[str]
) -> List[str]:
    """
    Get the scopes that are required but missing from the token.

    Args:
        token_scopes: List of scopes from the token
        required_scopes: List of scopes required for access

    Returns:
        List of missing scopes
    """
    return list(set(required_scopes) - set(token_scopes))
