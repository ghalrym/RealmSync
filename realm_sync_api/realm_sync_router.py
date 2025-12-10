from fastapi import APIRouter

from .realm_sync_retriever import ListRequestArgs, ModelType, RealmSyncRetriever


class RealmSyncRouter(APIRouter):
    def register_retriever(
        self,
        retriever: RealmSyncRetriever[ModelType, ListRequestArgs],
    ):
        self.get("/")(retriever.list)
        self.post("/")(retriever.create)
        self.get("/{id}")(retriever.get)
        self.put("/{id}")(retriever.update)
        self.delete("/{id}", response_model=None)(retriever.delete)
