"""Tests for Quest model."""

import pytest

from realm_sync_api.models.quest import Quest


def test_quest_creation():
    """Test creating a Quest with all required fields."""
    quest = Quest(
        id="quest1", name="Find Item", description="Find the magic sword", dependencies=[]
    )
    assert quest.id == "quest1"
    assert quest.name == "Find Item"
    assert quest.description == "Find the magic sword"
    assert quest.dependencies == []


def test_quest_with_dependencies():
    """Test Quest with dependencies list."""
    quest = Quest(
        id="quest1",
        name="Find Item",
        description="Find the magic sword",
        dependencies=["quest0", "quest2"],
    )
    assert len(quest.dependencies) == 2
    assert "quest0" in quest.dependencies
    assert "quest2" in quest.dependencies


def test_quest_with_metadata():
    """Test that Quest can have metadata."""
    quest = Quest(
        id="quest1",
        name="Find Item",
        description="Find the magic sword",
        dependencies=[],
        metadata={"reward": "100 gold"},
    )
    assert quest.metadata == {"reward": "100 gold"}


def test_quest_json_serialization():
    """Test that Quest can be serialized to JSON."""
    quest = Quest(
        id="quest1", name="Find Item", description="Find the magic sword", dependencies=["q1"]
    )
    json_str = quest.model_dump_json()
    assert "quest1" in json_str
    assert "Find Item" in json_str
    assert "Find the magic sword" in json_str


def test_quest_json_deserialization():
    """Test that Quest can be deserialized from JSON."""
    json_str = (
        '{"id": "quest1", "name": "Find Item", "description": "Find the magic sword", '
        '"dependencies": ["quest0"]}'
    )
    quest = Quest.model_validate_json(json_str)
    assert quest.id == "quest1"
    assert quest.name == "Find Item"
    assert quest.dependencies == ["quest0"]


def test_quest_missing_field():
    """Test that Quest requires all fields."""
    with pytest.raises(Exception):  # Pydantic validation error
        Quest(id="quest1", name="Find Item", description="Find the magic sword")
        # Missing dependencies


def test_quest_empty_dependencies():
    """Test Quest with empty dependencies list."""
    quest = Quest(
        id="quest1", name="Find Item", description="Find the magic sword", dependencies=[]
    )
    assert isinstance(quest.dependencies, list)
    assert len(quest.dependencies) == 0
