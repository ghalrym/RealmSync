import json

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import create_in_api, delete_from_api, fetch_from_api, get_from_api, update_in_api
from .auth_dependency import check_auth
from .template import templates

router = APIRouter(prefix="/player", tags=["player"])


@router.get("/", response_class=HTMLResponse)
async def list_players(request: Request):
    """List all players."""
    redirect = await check_auth(request)
    if redirect:
        return redirect
    players = await fetch_from_api(request, "/player/")
    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "model_name": "Player",
            "model_name_lower": "player",
            "items": players,
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_player_form(request: Request):
    """Show create player form."""
    redirect = await check_auth(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "Player",
            "model_name_lower": "player",
            "item": None,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "server", "type": "text", "required": True},
                {"name": "faction", "type": "text", "required": True},
                {
                    "name": "location",
                    "type": "text",
                    "required": True,
                    "help": 'JSON: {"location": "string", "x": 0.0, "y": 0.0, "z": 0.0}',
                },
            ],
        },
    )


@router.post("/create", response_class=RedirectResponse)
async def create_player(
    request: Request,
    id: str = Form(...),
    name: str = Form(...),
    server: str = Form(...),
    faction: str = Form(...),
    location: str = Form(...),
):
    """Create a new player."""
    redirect = await check_auth(request)
    if redirect:
        return redirect
    try:
        location_data = json.loads(location)
    except json.JSONDecodeError:
        location_data = {"location": location, "x": 0.0, "y": 0.0, "z": 0.0}

    player_data = {
        "id": id,
        "name": name,
        "server": server,
        "faction": faction,
        "location": location_data,
    }
    await create_in_api(request, "/player/", player_data)
    web_prefix = templates.env.globals.get("web_prefix", "/web")
    return RedirectResponse(
        url=f"{web_prefix}/player",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/edit/{id}", response_class=HTMLResponse)
async def edit_player_form(request: Request, id: str):
    """Show edit player form."""
    redirect = await check_auth(request)
    if redirect:
        return redirect
    player = await get_from_api(request, f"/player/{id}")
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "Player",
            "model_name_lower": "player",
            "item": player,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "server", "type": "text", "required": True},
                {"name": "faction", "type": "text", "required": True},
                {
                    "name": "location",
                    "type": "text",
                    "required": True,
                    "help": 'JSON: {"location": "string", "x": 0.0, "y": 0.0, "z": 0.0}',
                },
            ],
        },
    )


@router.post("/edit/{id}", response_class=RedirectResponse)
async def update_player(
    request: Request,
    id: str,
    name: str = Form(...),
    server: str = Form(...),
    faction: str = Form(...),
    location: str = Form(...),
):
    """Update a player."""
    redirect = await check_auth(request)
    if redirect:
        return redirect
    try:
        location_data = json.loads(location)
    except json.JSONDecodeError:
        location_data = {"location": location, "x": 0.0, "y": 0.0, "z": 0.0}

    player_data = {
        "id": id,
        "name": name,
        "server": server,
        "faction": faction,
        "location": location_data,
    }
    await update_in_api(request, f"/player/{id}", player_data)
    web_prefix = templates.env.globals.get("web_prefix", "/web")
    return RedirectResponse(
        url=f"{web_prefix}/player/{id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/delete/{id}", response_class=RedirectResponse)
async def delete_player(request: Request, id: str):
    """Delete a player."""
    redirect = await check_auth(request)
    if redirect:
        return redirect
    await delete_from_api(request, f"/player/{id}")
    web_prefix = templates.env.globals.get("web_prefix", "/web")
    return RedirectResponse(
        url=f"{web_prefix}/player",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/{id}", response_class=HTMLResponse)
async def view_player(request: Request, id: str):
    """View a single player."""
    redirect = await check_auth(request)
    if redirect:
        return redirect
    player = await get_from_api(request, f"/player/{id}")
    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "model_name": "Player",
            "model_name_lower": "player",
            "item": player,
        },
    )
