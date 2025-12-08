"""Tests for RealmSyncModel base class."""

from realm_sync_api.models._base import RealmSyncModel


def test_realm_sync_model_default_metadata():
    """Test that RealmSyncModel has default empty metadata."""
    model = RealmSyncModel()
    assert model.metadata == {}


def test_realm_sync_model_custom_metadata():
    """Test that RealmSyncModel can have custom metadata."""
    metadata = {"key1": "value1", "key2": 123}
    model = RealmSyncModel(metadata=metadata)
    assert model.metadata == metadata


def test_realm_sync_model_metadata_is_dict():
    """Test that metadata is a dict."""
    model = RealmSyncModel()
    assert isinstance(model.metadata, dict)


def test_realm_sync_model_metadata_mutation():
    """Test that metadata can be mutated."""
    model = RealmSyncModel()
    model.metadata["new_key"] = "new_value"
    assert model.metadata["new_key"] == "new_value"


def test_realm_sync_model_json_serialization():
    """Test that RealmSyncModel can be serialized to JSON."""
    model = RealmSyncModel(metadata={"test": "value"})
    json_str = model.model_dump_json()
    assert "test" in json_str
    assert "value" in json_str


def test_realm_sync_model_json_deserialization():
    """Test that RealmSyncModel can be deserialized from JSON."""
    json_str = '{"metadata": {"key": "value"}}'
    model = RealmSyncModel.model_validate_json(json_str)
    assert model.metadata == {"key": "value"}
