"""Tests for Location model."""

import pytest

from realm_sync_api.models.location import Location


def test_location_creation():
    """Test creating a Location with all required fields."""
    location = Location(location="Test Location", x=1.0, y=2.0, z=3.0)
    assert location.location == "Test Location"
    assert location.x == 1.0
    assert location.y == 2.0
    assert location.z == 3.0


def test_location_float_coordinates():
    """Test that coordinates can be floats."""
    location = Location(location="Test", x=1.5, y=2.7, z=-3.2)
    assert location.x == 1.5
    assert location.y == 2.7
    assert location.z == -3.2


def test_location_inherits_metadata():
    """Test that Location inherits metadata from RealmSyncModel."""
    location = Location(location="Test", x=0.0, y=0.0, z=0.0, metadata={"custom": "data"})
    assert location.metadata == {"custom": "data"}


def test_location_json_serialization():
    """Test that Location can be serialized to JSON."""
    location = Location(location="Test Location", x=1.0, y=2.0, z=3.0)
    json_str = location.model_dump_json()
    assert "Test Location" in json_str
    assert "1.0" in json_str or "1" in json_str


def test_location_json_deserialization():
    """Test that Location can be deserialized from JSON."""
    json_str = '{"location": "Test", "x": 1.0, "y": 2.0, "z": 3.0}'
    location = Location.model_validate_json(json_str)
    assert location.location == "Test"
    assert location.x == 1.0
    assert location.y == 2.0
    assert location.z == 3.0


def test_location_missing_field():
    """Test that Location requires all fields."""
    with pytest.raises(Exception):  # Pydantic validation error
        Location(location="Test", x=1.0)  # Missing y and z
