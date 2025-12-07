from fastapi import APIRouter

from .item import router as item_router
from .map import router as map_router
from .npc import router as npc_router
from .player import router as player_router
from .quest import router as quest_router

router = APIRouter(prefix="")
router.include_router(item_router)
router.include_router(map_router)
router.include_router(npc_router)
router.include_router(player_router)
router.include_router(quest_router)

__all__ = ["router"]
