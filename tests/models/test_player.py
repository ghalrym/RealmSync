"""Tests for Player model."""

import pytest

from realm_sync_api.models.location import Location
from realm_sync_api.models.player import Player


def test_player_creation():
    """Test creating a Player with all required fields."""
    location = Location(location="Spawn", x=0.0, y=0.0, z=0.0)
    player = Player(
        id="player1", name="Test Player", server="server1", location=location, faction="A"
    )
    assert player.id == "player1"
    assert player.name == "Test Player"
    assert player.server == "server1"
    assert player.location == location
    assert player.faction == "A"


def test_player_with_metadata():
    """Test that Player can have metadata."""
    location = Location(location="Spawn", x=0.0, y=0.0, z=0.0)
    player = Player(
        id="player1",
        name="Test Player",
        server="server1",
        location=location,
        faction="A",
        metadata={"level": 10},
    )
    assert player.metadata == {"level": 10}


def test_player_json_serialization():
    """Test that Player can be serialized to JSON."""
    location = Location(location="Spawn", x=0.0, y=0.0, z=0.0)
    player = Player(
        id="player1", name="Test Player", server="server1", location=location, faction="A"
    )
    json_str = player.model_dump_json()
    assert "player1" in json_str
    assert "Test Player" in json_str


def test_player_json_deserialization():
    """Test that Player can be deserialized from JSON."""
    json_str = (
        '{"id": "player1", "name": "Test Player", "server": "server1", '
        '"location": {"location": "Spawn", "x": 0.0, "y": 0.0, "z": 0.0}, "faction": "A"}'
    )
    player = Player.model_validate_json(json_str)
    assert player.id == "player1"
    assert player.name == "Test Player"
    assert player.location.location == "Spawn"


def test_player_missing_field():
    """Test that Player requires all fields."""
    location = Location(location="Spawn", x=0.0, y=0.0, z=0.0)
    with pytest.raises(Exception):  # Pydantic validation error
        Player(id="player1", name="Test Player", server="server1", location=location)
        # Missing faction


def test_player_location_required():
    """Test that Player requires a Location object."""
    with pytest.raises(Exception):  # Pydantic validation error
        Player(
            id="player1",
            name="Test Player",
            server="server1",
            location=None,  # type: ignore
            faction="A",
        )
