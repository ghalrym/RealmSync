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

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/", response_class=HTMLResponse)
async def list_maps(request: Request):
    """List all maps."""
    maps = await fetch_from_api(request, "/map/")
    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "model_name": "Map",
            "model_name_lower": "map",
            "items": maps,
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_map_form(request: Request):
    """Show create map form."""
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "Map",
            "model_name_lower": "map",
            "item": None,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
            ],
        },
    )


@router.post("/create", response_class=RedirectResponse)
async def create_map(
    request: Request,
    id: str = Form(...),
    name: str = Form(...),
):
    """Create a new map."""
    map_data = {"id": id, "name": name}
    await create_in_api(request, "/map/", map_data)
    return RedirectResponse(
        url="/web/map",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/edit/{id}", response_class=HTMLResponse)
async def edit_map_form(request: Request, id: str):
    """Show edit map form."""
    map_item = await get_from_api(request, f"/map/{id}")
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "Map",
            "model_name_lower": "map",
            "item": map_item,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
            ],
        },
    )


@router.post("/edit/{id}", response_class=RedirectResponse)
async def update_map(
    request: Request,
    id: str,
    name: str = Form(...),
):
    """Update a map."""
    map_data = {"id": id, "name": name}
    await update_in_api(request, f"/map/{id}", map_data)
    return RedirectResponse(
        url=f"/web/map/{id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/delete/{id}", response_class=RedirectResponse)
async def delete_map(request: Request, id: str):
    """Delete a map."""
    await delete_from_api(request, f"/map/{id}")
    return RedirectResponse(
        url="/web/map",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/{id}", response_class=HTMLResponse)
async def view_map(request: Request, id: str):
    """View a single map."""
    map_item = await get_from_api(request, f"/map/{id}")
    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "model_name": "Map",
            "model_name_lower": "map",
            "item": map_item,
        },
    )
