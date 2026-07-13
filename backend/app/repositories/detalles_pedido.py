from typing import List, Optional
from supabase import Client
from app.domain.models import DetallesPedido, DetallesPedidoCreate, DetallesPedidoUpdate
from app.repositories.base import BaseRepository
from app.repositories.supabase_client import get_supabase_client


class DetallesPedidoRepository(BaseRepository[DetallesPedido, DetallesPedidoCreate, DetallesPedidoUpdate]):
    """
    Supabase implementation of the BaseRepository for 'Detalles_Pedido'.
    Note the case-sensitive table name matches the Supabase schema exactly.
    """
    def __init__(self, db_client: Optional[Client] = None):
        self.client = db_client or get_supabase_client()
        self.table_name = "Detalles_Pedido"

    async def get_by_id(self, entity_id: int) -> Optional[DetallesPedido]:
        response = self.client.table(self.table_name).select("*").eq("id", entity_id).execute()
        if response.data and len(response.data) > 0:
            return DetallesPedido.model_validate(response.data[0])
        return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[DetallesPedido]:
        end_range = offset + limit - 1 if limit > 0 else offset
        response = self.client.table(self.table_name).select("*").range(offset, end_range).execute()
        return [DetallesPedido.model_validate(item) for item in response.data]

    async def create(self, schema: DetallesPedidoCreate) -> DetallesPedido:
        data = schema.model_dump(mode="json")
        response = self.client.table(self.table_name).insert(data).execute()
        if response.data and len(response.data) > 0:
            return DetallesPedido.model_validate(response.data[0])
        raise RuntimeError("Failed to create order detail in database.")

    async def update(self, entity_id: int, schema: DetallesPedidoUpdate) -> Optional[DetallesPedido]:
        data = schema.model_dump(exclude_unset=True, mode="json")
        if not data:
            return await self.get_by_id(entity_id)

        response = self.client.table(self.table_name).update(data).eq("id", entity_id).execute()
        if response.data and len(response.data) > 0:
            return DetallesPedido.model_validate(response.data[0])
        return None

    async def delete(self, entity_id: int) -> bool:
        response = self.client.table(self.table_name).delete().eq("id", entity_id).execute()
        return len(response.data) > 0

    async def list_by_pedido_id(self, pedido_id: int) -> List[DetallesPedido]:
        """
        Specialized retrieval to list details specifically belonging to a single order.
        """
        response = self.client.table(self.table_name).select("*").eq("id_pedido", pedido_id).execute()
        return [DetallesPedido.model_validate(item) for item in response.data]
