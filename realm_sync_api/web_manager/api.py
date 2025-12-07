from typing import Any

import httpx
from fastapi import HTTPException, Request


def get_base_url(request: Request) -> str:
    """Get the base URL from the request."""
    return f"{request.url.scheme}://{request.url.netloc}"


async def fetch_from_api(request: Request, endpoint: str) -> Any:
    """Helper function to fetch data from the API."""
    base_url = get_base_url(request)
    async with httpx.AsyncClient() as client:
        try:
            # Use GET request - body is optional and will default to empty ListRequestArgs
            response = await client.get(f"{base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")


async def get_from_api(request: Request, endpoint: str) -> Any:
    """Helper function to get a single item from the API."""
    base_url = get_base_url(request)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")


async def create_in_api(request: Request, endpoint: str, data: dict) -> Any:
    """Helper function to create an item via the API."""
    base_url = get_base_url(request)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.post(f"{base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"API Error: {e.response.status_code} {e.response.reason_phrase} for url '{e.request.url}'",
            )
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")


async def update_in_api(request: Request, endpoint: str, data: dict) -> Any:
    """Helper function to update an item via the API."""
    base_url = get_base_url(request)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(f"{base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")


async def delete_from_api(request: Request, endpoint: str) -> None:
    """Helper function to delete an item via the API."""
    base_url = get_base_url(request)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"{base_url}{endpoint}")
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")
