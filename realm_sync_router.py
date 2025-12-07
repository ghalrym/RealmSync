import json
from typing import get_args

from fastapi import APIRouter, HTTPException, Request

from realm_sync_retriever import ListRequestArgs, ModelType, RealmSyncRetriever


class RealmSyncRouter(APIRouter):
    def register_retriever(
        self,
        retriever: RealmSyncRetriever[ModelType, ListRequestArgs],
    ):
        # Extract type parameters from the retriever's class
        retriever_class = type(retriever)
        model_type = None
        list_request_args_type = None

        # Get the __orig_bases__ to find the RealmSyncRetriever generic
        if hasattr(retriever_class, "__orig_bases__"):
            for base in retriever_class.__orig_bases__:
                if (
                    hasattr(base, "__origin__")
                    and base.__origin__ is RealmSyncRetriever
                ):
                    type_args = get_args(base)
                    if len(type_args) >= 2:
                        model_type = type_args[0]
                        list_request_args_type = type_args[1]
                        break

        if model_type is None or list_request_args_type is None:
            raise ValueError(
                f"Could not extract type parameters from {retriever_class}. "
                "Make sure the retriever class properly inherits from RealmSyncRetriever[ModelType, ListRequestArgs]"
            )

        @self.get("/", response_model=list[model_type])
        async def list_retriever_get(request: Request) -> list[model_type]:
            """List endpoint for GET requests (with optional body)."""
            try:
                # Try to read body if present (non-standard but supported)
                body = None
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        body_data = json.loads(body_bytes)
                        body = list_request_args_type(**body_data)
                except (json.JSONDecodeError, ValueError, TypeError):
                    # If body parsing fails, use default
                    pass

                if body is None:
                    body = list_request_args_type()

                return retriever.list(body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

        @self.post("/", response_model=model_type)
        async def create_retriever(data: model_type) -> model_type:
            try:
                return retriever.create(data)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

        @self.get("/{key}", response_model=model_type)
        async def get_retriever(key: str) -> model_type:
            try:
                return retriever.get(key)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

        @self.put("/{key}", response_model=model_type)
        async def update_retriever(key: str, data: model_type) -> model_type:
            try:
                return retriever.update(key, data)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

        @self.delete("/{key}", response_model=None)
        async def delete_retriever(key: str) -> None:
            try:
                return retriever.delete(key)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )
