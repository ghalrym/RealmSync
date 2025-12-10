from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..api import create_in_api, delete_from_api, fetch_from_api, get_from_api, update_in_api
from .template import templates

router = APIRouter(prefix="/item", tags=["item"])


@router.get("/", response_class=HTMLResponse)
async def list_items(request: Request):
    """List all items."""
    items = await fetch_from_api(request, "/item/")
    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "model_name": "Item",
            "model_name_lower": "item",
            "items": items,
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_item_form(request: Request):
    """Show create item form."""
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "Item",
            "model_name_lower": "item",
            "item": None,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "type", "type": "text", "required": True},
            ],
        },
    )


@router.post("/create", response_class=RedirectResponse)
async def create_item(
    request: Request,
    id: str = Form(...),
    name: str = Form(...),
    type: str = Form(...),
):
    """Create a new item."""
    item_data = {"id": id, "name": name, "type": type}
    await create_in_api(request, "/item/", item_data)
    return RedirectResponse(
        url="/web/item",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/edit/{id}", response_class=HTMLResponse)
async def edit_item_form(request: Request, id: str):
    """Show edit item form."""
    item = await get_from_api(request, f"/item/{id}")
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "model_name": "Item",
            "model_name_lower": "item",
            "item": item,
            "fields": [
                {"name": "id", "type": "text", "required": True},
                {"name": "name", "type": "text", "required": True},
                {"name": "type", "type": "text", "required": True},
            ],
        },
    )


@router.post("/edit/{id}", response_class=RedirectResponse)
async def update_item(
    request: Request,
    id: str,
    name: str = Form(...),
    type: str = Form(...),
):
    """Update an item."""
    item_data = {"id": id, "name": name, "type": type}
    await update_in_api(request, f"/item/{id}", item_data)
    return RedirectResponse(
        url=f"/web/item/{id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/delete/{id}", response_class=RedirectResponse)
async def delete_item(request: Request, id: str):
    """Delete an item."""
    await delete_from_api(request, f"/item/{id}")
    return RedirectResponse(
        url="/web/item",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/{id}", response_class=HTMLResponse)
async def view_item(request: Request, id: str):
    """View a single item."""
    item = await get_from_api(request, f"/item/{id}")
    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "model_name": "Item",
            "model_name_lower": "item",
            "item": item,
        },
    )
