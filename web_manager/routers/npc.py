from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from web_manager.api import (
    create_in_api,
    delete_from_api,
    fetch_from_api,
    get_from_api,
    update_in_api,
)
from web_manager.routers.tempate import templates

router = APIRouter(prefix="/npc", tags=["npc"])


@router.get("/", response_class=HTMLResponse)
async def list_npcs(request: Request):
    """List all NPCs."""
    npcs = await fetch_from_api(request, "/npc/")
    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "model_name": "NPC",
            "model_name_lower": "npc",
            "items": npcs,
        },
    )


@router.get("/{id}", response_class=HTMLResponse)
async def view_npc(request: Request, id: str):
    """View a single NPC."""
    npc = await get_from_api(request, f"/npc/{id}")
    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "model_name": "NPC",
            "model_name_lower": "npc",
            "item": npc,
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_npc_form(request: Request):
    """Show create NPC form."""
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "NPC",
            "model_name_lower": "npc",
            "item": None,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "faction", "type": "text", "required": True},
                {
                    "name": "quests",
                    "type": "text",
                    "required": False,
                    "help": "Comma-separated list of quest IDs",
                },
            ],
        },
    )


@router.post("/create", response_class=RedirectResponse)
async def create_npc(
    request: Request,
    id: str = Form(...),
    name: str = Form(...),
    faction: str = Form(...),
    quests: str = Form(""),
):
    """Create a new NPC."""
    quests_list = [q.strip() for q in quests.split(",") if q.strip()] if quests else []
    npc_data = {
        "id": id,
        "name": name,
        "faction": faction,
        "quests": quests_list,
    }
    await create_in_api(request, "/npc/", npc_data)
    return RedirectResponse(
        url="/web/npc",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/{id}/edit", response_class=HTMLResponse)
async def edit_npc_form(request: Request, id: str):
    """Show edit NPC form."""
    npc = await get_from_api(request, f"/npc/{id}")
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "NPC",
            "model_name_lower": "npc",
            "item": npc,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "faction", "type": "text", "required": True},
                {
                    "name": "quests",
                    "type": "text",
                    "required": False,
                    "help": "Comma-separated list of quest IDs",
                },
            ],
        },
    )


@router.post("/{id}/edit", response_class=RedirectResponse)
async def update_npc(
    request: Request,
    id: str,
    name: str = Form(...),
    faction: str = Form(...),
    quests: str = Form(""),
):
    """Update an NPC."""
    quests_list = [q.strip() for q in quests.split(",") if q.strip()] if quests else []
    npc_data = {
        "id": id,
        "name": name,
        "faction": faction,
        "quests": quests_list,
    }
    await update_in_api(request, f"/npc/{id}", npc_data)
    return RedirectResponse(
        url=f"/web/npc/{id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{id}/delete", response_class=RedirectResponse)
async def delete_npc(request: Request, id: str):
    """Delete an NPC."""
    await delete_from_api(request, f"/npc/{id}")
    return RedirectResponse(
        url="/web/npc",
        status_code=status.HTTP_303_SEE_OTHER,
    )
