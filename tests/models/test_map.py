"""Tests for Map model."""

import pytest

from realm_sync_api.models.map import Map


def test_map_creation():
    """Test creating a Map with all required fields."""
    map_obj = Map(id="map1", name="Forest")
    assert map_obj.id == "map1"
    assert map_obj.name == "Forest"


def test_map_with_metadata():
    """Test that Map can have metadata."""
    map_obj = Map(id="map1", name="Forest", metadata={"size": "large"})
    assert map_obj.metadata == {"size": "large"}


def test_map_json_serialization():
    """Test that Map can be serialized to JSON."""
    map_obj = Map(id="map1", name="Forest")
    json_str = map_obj.model_dump_json()
    assert "map1" in json_str
    assert "Forest" in json_str


def test_map_json_deserialization():
    """Test that Map can be deserialized from JSON."""
    json_str = '{"id": "map1", "name": "Forest"}'
    map_obj = Map.model_validate_json(json_str)
    assert map_obj.id == "map1"
    assert map_obj.name == "Forest"


def test_map_missing_field():
    """Test that Map requires all fields."""
    with pytest.raises(Exception):  # Pydantic validation error
        Map(id="map1")  # Missing name
