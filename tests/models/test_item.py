"""Tests for Item model."""

import pytest

from realm_sync_api.models.item import Item


def test_item_creation():
    """Test creating an Item with all required fields."""
    item = Item(id="item1", name="Sword", type="weapon")
    assert item.id == "item1"
    assert item.name == "Sword"
    assert item.type == "weapon"


def test_item_with_metadata():
    """Test that Item can have metadata."""
    item = Item(id="item1", name="Sword", type="weapon", metadata={"damage": 10})
    assert item.metadata == {"damage": 10}


def test_item_json_serialization():
    """Test that Item can be serialized to JSON."""
    item = Item(id="item1", name="Sword", type="weapon")
    json_str = item.model_dump_json()
    assert "item1" in json_str
    assert "Sword" in json_str
    assert "weapon" in json_str


def test_item_json_deserialization():
    """Test that Item can be deserialized from JSON."""
    json_str = '{"id": "item1", "name": "Sword", "type": "weapon"}'
    item = Item.model_validate_json(json_str)
    assert item.id == "item1"
    assert item.name == "Sword"
    assert item.type == "weapon"


def test_item_missing_field():
    """Test that Item requires all fields."""
    with pytest.raises(Exception):  # Pydantic validation error
        Item(id="item1", name="Sword")  # Missing type


def test_item_different_types():
    """Test Item with different types."""
    weapon = Item(id="w1", name="Sword", type="weapon")
    armor = Item(id="a1", name="Shield", type="armor")
    assert weapon.type == "weapon"
    assert armor.type == "armor"
