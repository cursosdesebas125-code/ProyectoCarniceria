from typing import List, Optional
from supabase import Client
from app.domain.models import Pedido, PedidoCreate, PedidoUpdate
from app.repositories.base import BaseRepository
from app.repositories.supabase_client import get_supabase_client


class PedidosRepository(BaseRepository[Pedido, PedidoCreate, PedidoUpdate]):
    """
    Supabase implementation of the BaseRepository for 'pedidos'.
    """
    def __init__(self, db_client: Optional[Client] = None):
        self.client = db_client or get_supabase_client()
        self.table_name = "Pedidos"

    async def get_by_id(self, entity_id: int) -> Optional[Pedido]:
        response = self.client.table(self.table_name).select("*").eq("id", entity_id).execute()
        if response.data and len(response.data) > 0:
            return Pedido.model_validate(response.data[0])
        return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Pedido]:
        end_range = offset + limit - 1 if limit > 0 else offset
        response = self.client.table(self.table_name).select("*").range(offset, end_range).execute()
        return [Pedido.model_validate(item) for item in response.data]

    async def create(self, schema: PedidoCreate) -> Pedido:
        data = schema.model_dump(mode="json")
        response = self.client.table(self.table_name).insert(data).execute()
        if response.data and len(response.data) > 0:
            return Pedido.model_validate(response.data[0])
        raise RuntimeError("Failed to create order in database.")

    async def update(self, entity_id: int, schema: PedidoUpdate) -> Optional[Pedido]:
        data = schema.model_dump(exclude_unset=True, mode="json")
        if not data:
            return await self.get_by_id(entity_id)

        response = self.client.table(self.table_name).update(data).eq("id", entity_id).execute()
        if response.data and len(response.data) > 0:
            return Pedido.model_validate(response.data[0])
        return None

    async def delete(self, entity_id: int) -> bool:
        response = self.client.table(self.table_name).delete().eq("id", entity_id).execute()
        return len(response.data) > 0
