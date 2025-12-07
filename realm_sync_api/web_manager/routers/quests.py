from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from realm_sync_api.web_manager.api import (
    create_in_api,
    delete_from_api,
    fetch_from_api,
    get_from_api,
    update_in_api,
)
from realm_sync_api.web_manager.routers.tempate import templates

router = APIRouter(prefix="/quest", tags=["quest"])


@router.get("/", response_class=HTMLResponse)
async def list_quests(request: Request):
    """List all quests."""
    quests = await fetch_from_api(request, "/quest/")
    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "model_name": "Quest",
            "model_name_lower": "quest",
            "items": quests,
        },
    )


@router.get("/{id}", response_class=HTMLResponse)
async def view_quest(request: Request, id: str):
    """View a single quest."""
    quest = await get_from_api(request, f"/quest/{id}")
    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "model_name": "Quest",
            "model_name_lower": "quest",
            "item": quest,
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_quest_form(request: Request):
    """Show create quest form."""
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "Quest",
            "model_name_lower": "quest",
            "item": None,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "description", "type": "textarea", "required": True},
                {
                    "name": "dependencies",
                    "type": "text",
                    "required": False,
                    "help": "Comma-separated list of quest IDs",
                },
            ],
        },
    )


@router.post("/create", response_class=RedirectResponse)
async def create_quest(
    request: Request,
    id: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    dependencies: str = Form(""),
):
    """Create a new quest."""
    deps_list = (
        [d.strip() for d in dependencies.split(",") if d.strip()]
        if dependencies
        else []
    )
    quest_data = {
        "id": id,
        "name": name,
        "description": description,
        "dependencies": deps_list,
    }
    await create_in_api(request, "/quest/", quest_data)
    return RedirectResponse(url="/web/quest", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{id}/edit", response_class=HTMLResponse)
async def edit_quest_form(request: Request, id: str):
    """Show edit quest form."""
    quest = await get_from_api(request, f"/quest/{id}")
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "Quest",
            "model_name_lower": "quest",
            "item": quest,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "description", "type": "textarea", "required": True},
                {
                    "name": "dependencies",
                    "type": "text",
                    "required": False,
                    "help": "Comma-separated list of quest IDs",
                },
            ],
        },
    )


@router.post("/{id}/edit", response_class=RedirectResponse)
async def update_quest(
    request: Request,
    id: str,
    name: str = Form(...),
    description: str = Form(...),
    dependencies: str = Form(""),
):
    """Update a quest."""
    deps_list = (
        [d.strip() for d in dependencies.split(",") if d.strip()]
        if dependencies
        else []
    )
    quest_data = {
        "id": id,
        "name": name,
        "description": description,
        "dependencies": deps_list,
    }
    await update_in_api(request, f"/quest/{id}", quest_data)
    return RedirectResponse(
        url=f"/web/quest/{id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/{id}/delete", response_class=RedirectResponse)
async def delete_quest(request: Request, id: str):
    """Delete a quest."""
    await delete_from_api(request, f"/quest/{id}")
    return RedirectResponse(url="/web/quest", status_code=status.HTTP_303_SEE_OTHER)
