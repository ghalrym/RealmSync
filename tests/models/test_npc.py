"""Tests for NPC model."""

import pytest
from pydantic import ValidationError

from realm_sync_api.models.npc import NPC


def test_npc_creation():
    """Test creating an NPC with all required fields."""
    npc = NPC(id="npc1", name="Merchant", faction="A", quests=[])
    assert npc.id == "npc1"
    assert npc.name == "Merchant"
    assert npc.faction == "A"
    assert npc.quests == []


def test_npc_with_quests():
    """Test NPC with quest list."""
    npc = NPC(id="npc1", name="Merchant", faction="A", quests=["quest1", "quest2"])
    assert len(npc.quests) == 2
    assert "quest1" in npc.quests
    assert "quest2" in npc.quests


def test_npc_with_metadata():
    """Test that NPC can have metadata."""
    npc = NPC(id="npc1", name="Merchant", faction="A", quests=[], metadata={"level": 5})
    assert npc.metadata == {"level": 5}


def test_npc_json_serialization():
    """Test that NPC can be serialized to JSON."""
    npc = NPC(id="npc1", name="Merchant", faction="A", quests=["quest1"])
    json_str = npc.model_dump_json()
    assert "npc1" in json_str
    assert "Merchant" in json_str
    assert "quest1" in json_str


def test_npc_json_deserialization():
    """Test that NPC can be deserialized from JSON."""
    json_str = '{"id": "npc1", "name": "Merchant", "faction": "A", "quests": ["quest1"]}'
    npc = NPC.model_validate_json(json_str)
    assert npc.id == "npc1"
    assert npc.name == "Merchant"
    assert npc.quests == ["quest1"]


def test_npc_missing_field():
    """Test that NPC requires all fields."""
    with pytest.raises(ValidationError):
        NPC(id="npc1", name="Merchant", faction="A")  # Missing quests


def test_npc_empty_quests_list():
    """Test NPC with empty quests list."""
    npc = NPC(id="npc1", name="Merchant", faction="A", quests=[])
    assert isinstance(npc.quests, list)
    assert len(npc.quests) == 0
