#!/usr/bin/env python3
"""
Parametrized validation tests for all 31 connector YAML manifests.

Tests cover:
- Parsing without error
- Required fields (id, name, version) are non-empty
- Auth types are valid enum values
- ConfigField entries use 'field' key
- Options are flat tuples
- Trigger outputs are PortDefinition instances
- Unique connector IDs across all manifests
- PenguinTech connectors have actions
- DB connectors have consistent structure
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.base import AuthType, ConfigField, ConnectorManifest, PortDefinition

MANIFESTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "connectors",
    "manifests",
)
MANIFEST_FILES = sorted(
    [f for f in os.listdir(MANIFESTS_DIR) if f.endswith((".yaml", ".yml"))]
)

EXPECTED_MANIFEST_COUNT = 31

# Enumerate penguintech connectors by vendor field
PENGUINTECH_IDS = {
    "elder",
    "waddlebot",
    "waddleai",
    "iceshelves",
    "darwin",
    "waddleperf",
    "nest",
    "marchproxy",
    "killkrill",
    "articdbm",
    "skauswatch",
    "squawk",
    "tobogganing",
}

DB_PREFIX = "db_"


@pytest.fixture(params=MANIFEST_FILES, ids=lambda f: f.replace(".yaml", "").replace(".yml", ""))
def manifest(request):
    """Load each manifest YAML from the manifests directory."""
    return ConnectorManifest.from_yaml(os.path.join(MANIFESTS_DIR, request.param))


class TestManifestCount:
    """Verify we have the expected number of manifests."""

    def test_manifest_count(self):
        """Exactly 31 YAML manifest files must exist."""
        assert len(MANIFEST_FILES) == EXPECTED_MANIFEST_COUNT, (
            f"Expected {EXPECTED_MANIFEST_COUNT} manifests, found {len(MANIFEST_FILES)}: "
            f"{MANIFEST_FILES}"
        )


class TestManifestParsing:
    """Each manifest must parse without error and have required fields."""

    def test_parses_without_error(self, manifest):
        """ConnectorManifest.from_yaml must not raise any exception."""
        assert manifest is not None

    def test_id_is_non_empty(self, manifest):
        """Connector id must be a non-empty string."""
        assert isinstance(manifest.id, str)
        assert len(manifest.id) > 0

    def test_name_is_non_empty(self, manifest):
        """Connector name must be a non-empty string."""
        assert isinstance(manifest.name, str)
        assert len(manifest.name) > 0

    def test_version_is_non_empty(self, manifest):
        """Connector version must be a non-empty string."""
        assert isinstance(manifest.version, str)
        assert len(manifest.version) > 0

    def test_description_is_string(self, manifest):
        """Connector description must be a string (may be empty)."""
        assert isinstance(manifest.description, str)

    def test_vendor_is_string(self, manifest):
        """Connector vendor must be a string."""
        assert isinstance(manifest.vendor, str)
        assert len(manifest.vendor) > 0

    def test_color_is_hex_or_string(self, manifest):
        """Connector color must be a string."""
        assert isinstance(manifest.color, str)


class TestManifestAuthTypes:
    """Auth methods must use only valid AuthType enum values."""

    def test_auth_methods_are_tuple(self, manifest):
        """Auth methods must be stored as a tuple."""
        assert isinstance(manifest.auth_methods, tuple)

    def test_auth_type_values_are_valid(self, manifest):
        """Each auth method type must be a valid AuthType enum value."""
        valid_types = {at.value for at in AuthType}
        for auth_method in manifest.auth_methods:
            assert auth_method.type.value in valid_types, (
                f"Connector '{manifest.id}' has invalid auth type: {auth_method.type!r}. "
                f"Valid: {valid_types}"
            )

    def test_no_invalid_auth_types(self, manifest):
        """Auth types must not include connection_string or service_account."""
        forbidden = {"connection_string", "service_account"}
        for auth_method in manifest.auth_methods:
            assert auth_method.type.value not in forbidden, (
                f"Connector '{manifest.id}' uses forbidden auth type: {auth_method.type.value}"
            )


class TestConfigFieldStructure:
    """ConfigField entries must use 'field' key and have flat options."""

    def _collect_all_config_fields(self, manifest):
        """Collect all config fields from triggers, actions, and transforms."""
        fields = []
        for trigger in manifest.triggers:
            fields.extend(trigger.config_schema)
        for action in manifest.actions:
            fields.extend(action.config_schema)
        for transform in manifest.transforms:
            fields.extend(transform.config_schema)
        return fields

    def test_config_fields_are_configfield_instances(self, manifest):
        """All config schema entries must be ConfigField instances."""
        for item in self._collect_all_config_fields(manifest):
            assert isinstance(item, ConfigField), (
                f"Connector '{manifest.id}': expected ConfigField, got {type(item)}"
            )

    def test_config_fields_have_field_attribute(self, manifest):
        """Each ConfigField must have a non-empty 'field' attribute."""
        for item in self._collect_all_config_fields(manifest):
            assert hasattr(item, "field"), (
                f"Connector '{manifest.id}': ConfigField missing 'field' attribute"
            )
            assert isinstance(item.field, str) and len(item.field) > 0, (
                f"Connector '{manifest.id}': ConfigField.field must be non-empty string"
            )

    def test_config_field_options_are_flat_tuples(self, manifest):
        """Options for select fields must be flat tuples, not object arrays."""
        for item in self._collect_all_config_fields(manifest):
            assert isinstance(item.options, tuple), (
                f"Connector '{manifest.id}', field '{item.field}': "
                f"options must be tuple, got {type(item.options)}"
            )
            # Options must be flat (each element must be a primitive, not a dict/list)
            for opt in item.options:
                assert not isinstance(opt, (dict, list)), (
                    f"Connector '{manifest.id}', field '{item.field}': "
                    f"options must be flat (not dict/list), got {type(opt)}: {opt!r}"
                )

    def test_config_field_type_is_string(self, manifest):
        """Each ConfigField.type must be a string."""
        for item in self._collect_all_config_fields(manifest):
            assert isinstance(item.type, str), (
                f"Connector '{manifest.id}', field '{item.field}': "
                f"type must be string, got {type(item.type)}"
            )


class TestTriggerOutputs:
    """Trigger outputs must be PortDefinition instances."""

    def test_trigger_outputs_are_port_definitions(self, manifest):
        """All trigger outputs must be PortDefinition instances."""
        for trigger in manifest.triggers:
            for output in trigger.outputs:
                assert isinstance(output, PortDefinition), (
                    f"Connector '{manifest.id}', trigger '{trigger.id}': "
                    f"expected PortDefinition output, got {type(output)}"
                )

    def test_trigger_outputs_have_name(self, manifest):
        """Each trigger output must have a non-empty name."""
        for trigger in manifest.triggers:
            for output in trigger.outputs:
                assert isinstance(output.name, str) and len(output.name) > 0, (
                    f"Connector '{manifest.id}', trigger '{trigger.id}': "
                    f"output must have non-empty name"
                )

    def test_trigger_outputs_are_tuple(self, manifest):
        """Trigger outputs must be stored as a tuple."""
        for trigger in manifest.triggers:
            assert isinstance(trigger.outputs, tuple), (
                f"Connector '{manifest.id}', trigger '{trigger.id}': "
                f"outputs must be tuple"
            )

    def test_trigger_ids_are_non_empty(self, manifest):
        """Each trigger must have a non-empty id."""
        for trigger in manifest.triggers:
            assert isinstance(trigger.id, str) and len(trigger.id) > 0, (
                f"Connector '{manifest.id}': trigger missing non-empty id"
            )


class TestActionStructure:
    """Actions must have required fields and valid structure."""

    def test_action_outputs_are_port_definitions(self, manifest):
        """All action outputs must be PortDefinition instances."""
        for action in manifest.actions:
            for output in action.outputs:
                assert isinstance(output, PortDefinition), (
                    f"Connector '{manifest.id}', action '{action.id}': "
                    f"expected PortDefinition output, got {type(output)}"
                )

    def test_action_inputs_are_port_definitions(self, manifest):
        """All action inputs must be PortDefinition instances."""
        for action in manifest.actions:
            for inp in action.inputs:
                assert isinstance(inp, PortDefinition), (
                    f"Connector '{manifest.id}', action '{action.id}': "
                    f"expected PortDefinition input, got {type(inp)}"
                )

    def test_action_method_is_valid_http(self, manifest):
        """Action HTTP methods must be valid."""
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        for action in manifest.actions:
            assert action.method.upper() in valid_methods, (
                f"Connector '{manifest.id}', action '{action.id}': "
                f"invalid HTTP method '{action.method}'"
            )


class TestUniqueConnectorIDs:
    """Connector IDs must be unique across all manifests."""

    def test_all_connector_ids_are_unique(self):
        """No two manifests should share the same connector id."""
        ids = []
        for filename in MANIFEST_FILES:
            m = ConnectorManifest.from_yaml(os.path.join(MANIFESTS_DIR, filename))
            ids.append(m.id)
        assert len(ids) == len(set(ids)), (
            f"Duplicate connector IDs found: "
            f"{[id_ for id_ in ids if ids.count(id_) > 1]}"
        )


class TestPenguinTechConnectors:
    """PenguinTech connectors (vendor=penguintech) must have actions defined."""

    def test_penguintech_connectors_have_actions(self, manifest):
        """PenguinTech service connectors must define at least one action."""
        if manifest.vendor == "penguintech":
            assert len(manifest.actions) > 0, (
                f"PenguinTech connector '{manifest.id}' has no actions defined"
            )

    def test_penguintech_connector_has_default_url(self, manifest):
        """PenguinTech connectors should have a default URL or env var."""
        if manifest.vendor == "penguintech":
            has_url = bool(manifest.default_url) or bool(manifest.base_url_env)
            assert has_url, (
                f"PenguinTech connector '{manifest.id}' has no default_url or base_url_env"
            )


class TestDatabaseConnectors:
    """Database connectors (id starting with db_) must have consistent structure."""

    def test_db_connector_has_actions(self, manifest):
        """Database connectors must define at least one action."""
        if manifest.id.startswith(DB_PREFIX):
            assert len(manifest.actions) > 0, (
                f"DB connector '{manifest.id}' has no actions defined"
            )

    def test_db_connector_has_at_least_one_trigger(self, manifest):
        """Database connectors should have at least one trigger."""
        if manifest.id.startswith(DB_PREFIX):
            assert len(manifest.triggers) >= 1, (
                f"DB connector '{manifest.id}' has no triggers"
            )

    def test_db_connector_has_execute_query_or_equivalent(self, manifest):
        """Database connectors should have a query or execute action."""
        if manifest.id.startswith(DB_PREFIX):
            action_ids = {a.id for a in manifest.actions}
            has_query_action = any(
                "query" in aid or "execute" in aid or "select" in aid or "find" in aid
                for aid in action_ids
            )
            assert has_query_action, (
                f"DB connector '{manifest.id}' has no query/execute action. "
                f"Action IDs: {action_ids}"
            )

    def test_db_connector_vendor_is_database(self, manifest):
        """Database connectors should have vendor='database'."""
        if manifest.id.startswith(DB_PREFIX):
            assert manifest.vendor == "database", (
                f"DB connector '{manifest.id}' expected vendor='database', "
                f"got '{manifest.vendor}'"
            )
