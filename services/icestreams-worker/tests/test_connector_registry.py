#!/usr/bin/env python3
"""
Tests for ConnectorRegistry singleton and discover_connectors().

Tests cover:
- Registry starts empty after clear()
- register_manifest / get_manifest
- Duplicate registration raises DuplicateConnectorError
- allow_override bypasses duplicate check
- discover_connectors finds all 31 connectors
- Short-circuit if already initialized
- clear() resets state
- get_all_manifests
- is_registered
- count
- unregister
- Thread safety
- get_all_ids
"""

import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.base import AuthType, ConnectorManifest
from connectors.registry import (ConnectorNotFoundError, ConnectorRegistry,
                                 DuplicateConnectorError, discover_connectors)
from executor.node_registry import NodeRegistry

MANIFESTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "connectors",
    "manifests",
)


@pytest.fixture(autouse=True)
def clean_registries():
    """Clear both registries before and after each test."""
    ConnectorRegistry.clear()
    NodeRegistry.clear()
    yield
    ConnectorRegistry.clear()
    NodeRegistry.clear()


def _make_test_manifest(connector_id: str = "test_connector") -> ConnectorManifest:
    """Create a minimal ConnectorManifest for testing."""
    return ConnectorManifest(
        id=connector_id,
        name=f"Test {connector_id}",
        description="Test connector",
        version="1.0.0",
        vendor="test",
    )


class TestRegistryStartsEmpty:
    """Registry must be empty after clear()."""

    def test_starts_empty_after_clear(self):
        """Registry should have zero connectors after clear()."""
        assert ConnectorRegistry.count() == 0

    def test_is_not_initialized_after_clear(self):
        """Registry should not be marked initialized after clear()."""
        assert ConnectorRegistry.is_initialized() is False


class TestRegisterAndGet:
    """Basic registration and retrieval."""

    def test_register_manifest(self):
        """Registering a manifest should make it retrievable by id."""
        manifest = _make_test_manifest("alpha")
        ConnectorRegistry.register_manifest(manifest)
        retrieved = ConnectorRegistry.get_manifest("alpha")
        assert retrieved is not None
        assert retrieved.id == "alpha"
        assert retrieved.name == "Test alpha"

    def test_get_returns_none_for_unknown_id(self):
        """get_manifest should return None for unregistered connectors."""
        result = ConnectorRegistry.get_manifest("nonexistent_xyz")
        assert result is None

    def test_count_increments_on_register(self):
        """count() should increment with each registered manifest."""
        assert ConnectorRegistry.count() == 0
        ConnectorRegistry.register_manifest(_make_test_manifest("a"))
        assert ConnectorRegistry.count() == 1
        ConnectorRegistry.register_manifest(_make_test_manifest("b"))
        assert ConnectorRegistry.count() == 2

    def test_is_registered_true_after_register(self):
        """is_registered() must return True after registering."""
        ConnectorRegistry.register_manifest(_make_test_manifest("testme"))
        assert ConnectorRegistry.is_registered("testme") is True

    def test_is_registered_false_for_unknown(self):
        """is_registered() must return False for unregistered connectors."""
        assert ConnectorRegistry.is_registered("unknown_connector") is False


class TestDuplicateRegistration:
    """Duplicate registrations must raise DuplicateConnectorError."""

    def test_duplicate_raises_error(self):
        """Registering same connector_id twice must raise DuplicateConnectorError."""
        manifest = _make_test_manifest("dup_test")
        ConnectorRegistry.register_manifest(manifest)
        with pytest.raises(DuplicateConnectorError, match="dup_test"):
            ConnectorRegistry.register_manifest(manifest)

    def test_allow_override_permits_re_registration(self):
        """allow_override=True must allow re-registering the same id."""
        m1 = _make_test_manifest("override_me")
        m2 = ConnectorManifest(
            id="override_me",
            name="Overridden",
            description="Overridden connector",
            version="2.0.0",
            vendor="test",
        )
        ConnectorRegistry.register_manifest(m1)
        ConnectorRegistry.register_manifest(m2, allow_override=True)
        retrieved = ConnectorRegistry.get_manifest("override_me")
        assert retrieved.name == "Overridden"
        assert retrieved.version == "2.0.0"

    def test_duplicate_without_override_keeps_original(self):
        """Original manifest should remain after failed duplicate registration."""
        m1 = _make_test_manifest("keep_me")
        ConnectorRegistry.register_manifest(m1)
        m2 = ConnectorManifest(
            id="keep_me",
            name="Should Not Replace",
            description="Replacement attempt",
            version="9.9.9",
            vendor="test",
        )
        with pytest.raises(DuplicateConnectorError):
            ConnectorRegistry.register_manifest(m2)
        retrieved = ConnectorRegistry.get_manifest("keep_me")
        assert retrieved.name == "Test keep_me"


class TestDiscoverConnectors:
    """discover_connectors() should find all 31 YAML manifests."""

    def test_discover_finds_31_connectors(self):
        """discover_connectors must load exactly 31 connectors."""
        count = discover_connectors(manifests_dir=MANIFESTS_DIR, register_nodes=False)
        assert count == 31

    def test_discover_marks_initialized(self):
        """discover_connectors must mark registry as initialized."""
        discover_connectors(manifests_dir=MANIFESTS_DIR, register_nodes=False)
        assert ConnectorRegistry.is_initialized() is True

    def test_discover_short_circuits_if_initialized(self):
        """Second call to discover_connectors must not double-register."""
        count1 = discover_connectors(manifests_dir=MANIFESTS_DIR, register_nodes=False)
        count2 = discover_connectors(manifests_dir=MANIFESTS_DIR, register_nodes=False)
        assert count1 == count2
        assert ConnectorRegistry.count() == 31

    def test_discover_registers_known_connectors(self):
        """After discovery, well-known connector IDs must be registered."""
        discover_connectors(manifests_dir=MANIFESTS_DIR, register_nodes=False)
        assert ConnectorRegistry.is_registered("waddleai")
        assert ConnectorRegistry.is_registered("db_postgresql")
        assert ConnectorRegistry.is_registered("db_sqlite")

    def test_discover_with_missing_dir_returns_zero(self, tmp_path):
        """discover_connectors with nonexistent dir must return 0."""
        count = discover_connectors(
            manifests_dir=str(tmp_path / "does_not_exist"),
            register_nodes=False,
        )
        assert count == 0

    def test_discover_with_empty_dir_returns_zero(self, tmp_path):
        """discover_connectors with empty dir must return 0."""
        count = discover_connectors(
            manifests_dir=str(tmp_path),
            register_nodes=False,
        )
        assert count == 0


class TestClearRegistry:
    """clear() must reset all registry state."""

    def test_clear_removes_all_connectors(self):
        """clear() must remove all registered connectors."""
        ConnectorRegistry.register_manifest(_make_test_manifest("clear_a"))
        ConnectorRegistry.register_manifest(_make_test_manifest("clear_b"))
        assert ConnectorRegistry.count() == 2
        removed = ConnectorRegistry.clear()
        assert removed == 2
        assert ConnectorRegistry.count() == 0

    def test_clear_resets_initialized_flag(self):
        """clear() must set _initialized to False."""
        ConnectorRegistry.mark_initialized()
        assert ConnectorRegistry.is_initialized() is True
        ConnectorRegistry.clear()
        assert ConnectorRegistry.is_initialized() is False

    def test_clear_returns_count_of_cleared(self):
        """clear() return value must equal the number of connectors removed."""
        ConnectorRegistry.register_manifest(_make_test_manifest("x1"))
        ConnectorRegistry.register_manifest(_make_test_manifest("x2"))
        ConnectorRegistry.register_manifest(_make_test_manifest("x3"))
        count = ConnectorRegistry.clear()
        assert count == 3


class TestGetAllManifests:
    """get_all_manifests() must return a list of all registered manifests."""

    def test_get_all_manifests_empty(self):
        """get_all_manifests() returns empty list when registry is empty."""
        result = ConnectorRegistry.get_all_manifests()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_all_manifests_contains_registered(self):
        """get_all_manifests() returns all registered manifests."""
        m1 = _make_test_manifest("all_a")
        m2 = _make_test_manifest("all_b")
        ConnectorRegistry.register_manifest(m1)
        ConnectorRegistry.register_manifest(m2)
        all_manifests = ConnectorRegistry.get_all_manifests()
        ids = {m.id for m in all_manifests}
        assert "all_a" in ids
        assert "all_b" in ids
        assert len(all_manifests) == 2

    def test_get_all_ids_returns_list_of_strings(self):
        """get_all_ids() must return a list of string IDs."""
        ConnectorRegistry.register_manifest(_make_test_manifest("id_test"))
        ids = ConnectorRegistry.get_all_ids()
        assert isinstance(ids, list)
        assert "id_test" in ids


class TestUnregister:
    """unregister() must remove specific connectors."""

    def test_unregister_removes_connector(self):
        """unregister() must remove the connector from registry."""
        ConnectorRegistry.register_manifest(_make_test_manifest("to_remove"))
        assert ConnectorRegistry.is_registered("to_remove") is True
        result = ConnectorRegistry.unregister("to_remove")
        assert result is True
        assert ConnectorRegistry.is_registered("to_remove") is False

    def test_unregister_returns_false_for_unknown(self):
        """unregister() must return False for unregistered connector."""
        result = ConnectorRegistry.unregister("never_registered_xyz")
        assert result is False

    def test_unregister_does_not_affect_others(self):
        """Unregistering one connector must not affect others."""
        ConnectorRegistry.register_manifest(_make_test_manifest("keep"))
        ConnectorRegistry.register_manifest(_make_test_manifest("remove"))
        ConnectorRegistry.unregister("remove")
        assert ConnectorRegistry.is_registered("keep") is True
        assert ConnectorRegistry.count() == 1


class TestGetInstance:
    """get_instance() must return a connector instance or raise."""

    def test_get_instance_raises_for_unknown(self):
        """get_instance() must raise ConnectorNotFoundError for unknown id."""
        with pytest.raises(ConnectorNotFoundError, match="not found"):
            ConnectorRegistry.get_instance("unknown_connector_xyz")

    def test_get_instance_returns_none_when_raise_false(self):
        """get_instance() with raise_on_missing=False returns None for unknown."""
        result = ConnectorRegistry.get_instance("unknown_xyz", raise_on_missing=False)
        assert result is None

    def test_get_instance_creates_generic_connector(self):
        """get_instance() should create a generic connector from manifest."""
        manifest = _make_test_manifest("generic_test")
        ConnectorRegistry.register_manifest(manifest)
        instance = ConnectorRegistry.get_instance("generic_test")
        assert instance is not None
        assert instance.connector_id == "generic_test"


class TestThreadSafety:
    """Registry operations must be thread-safe."""

    def test_concurrent_registrations_no_crash(self):
        """Concurrent registrations of different connectors must not crash."""
        errors = []

        def register_one(i):
            try:
                ConnectorRegistry.register_manifest(
                    _make_test_manifest(f"thread_connector_{i}")
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register_one, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert ConnectorRegistry.count() == 10

    def test_concurrent_reads_are_safe(self):
        """Concurrent reads from registry must not raise exceptions."""
        for i in range(5):
            ConnectorRegistry.register_manifest(_make_test_manifest(f"read_test_{i}"))

        results = []
        errors = []

        def read_all():
            try:
                manifests = ConnectorRegistry.get_all_manifests()
                results.append(len(manifests))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_all) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert all(r == 5 for r in results)
