"""Tests for models __init__.py exports."""

from realm_sync_api.models import NPC, Item, Location, Map, Player, Quest
from realm_sync_api.models._base import RealmSyncModel


def test_all_models_importable():
    """Test that all models can be imported from models package."""
    assert Item is not None
    assert Location is not None
    assert Map is not None
    assert NPC is not None
    assert Player is not None
    assert Quest is not None


def test_models_inherit_from_realm_sync_model():
    """Test that all models inherit from RealmSyncModel."""
    assert issubclass(Item, RealmSyncModel)
    assert issubclass(Location, RealmSyncModel)
    assert issubclass(Map, RealmSyncModel)
    assert issubclass(NPC, RealmSyncModel)
    assert issubclass(Player, RealmSyncModel)
    assert issubclass(Quest, RealmSyncModel)


def test_models_have_metadata():
    """Test that all models have metadata field."""
    item = Item(id="1", name="Test", type="weapon")
    location = Location(location="Test", x=0.0, y=0.0, z=0.0)
    map_obj = Map(id="1", name="Test")
    npc = NPC(id="1", name="Test", faction="A", quests=[])
    quest = Quest(id="1", name="Test", description="Test", dependencies=[])

    assert hasattr(item, "metadata")
    assert hasattr(location, "metadata")
    assert hasattr(map_obj, "metadata")
    assert hasattr(npc, "metadata")
    assert hasattr(quest, "metadata")
