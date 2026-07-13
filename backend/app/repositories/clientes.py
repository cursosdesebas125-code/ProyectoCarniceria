from typing import List, Optional
from supabase import Client
from app.domain.models import Cliente, ClienteCreate, ClienteUpdate
from app.repositories.base import BaseRepository
from app.repositories.supabase_client import get_supabase_client


class ClientesRepository(BaseRepository[Cliente, ClienteCreate, ClienteUpdate]):
    """
    Supabase implementation of the BaseRepository for 'clientes'.
    """
    def __init__(self, db_client: Optional[Client] = None):
        self.client = db_client or get_supabase_client()
        self.table_name = "clientes"

    async def get_by_id(self, entity_id: int) -> Optional[Cliente]:
        response = self.client.table(self.table_name).select("*").eq("id", entity_id).execute()
        if response.data and len(response.data) > 0:
            return Cliente.model_validate(response.data[0])
        return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Cliente]:
        # Supabase range query is inclusive
        end_range = offset + limit - 1 if limit > 0 else offset
        response = self.client.table(self.table_name).select("*").range(offset, end_range).execute()
        return [Cliente.model_validate(item) for item in response.data]

    async def list_paginated(self, limit: int = 5, offset: int = 0) -> tuple[List[Cliente], int]:
        """
        Retrieves a page of clients along with the exact total record count.
        """
        end_range = offset + limit - 1 if limit > 0 else offset
        # Request count="exact" to retrieve the total matching rows before pagination limit
        response = self.client.table(self.table_name).select("*", count="exact").range(offset, end_range).execute()
        items = [Cliente.model_validate(item) for item in response.data]
        total_count = response.count if response.count is not None else len(items)
        return items, total_count

    async def create(self, schema: ClienteCreate) -> Cliente:
        # Convert schema to dict using mode='json' to serialize Decimal and custom types
        data = schema.model_dump(mode="json")
        response = self.client.table(self.table_name).insert(data).execute()
        if response.data and len(response.data) > 0:
            return Cliente.model_validate(response.data[0])
        raise RuntimeError("Failed to create client in database.")

    async def update(self, entity_id: int, schema: ClienteUpdate) -> Optional[Cliente]:
        # Filter out None fields from update
        data = schema.model_dump(exclude_unset=True, mode="json")
        if not data:
            return await self.get_by_id(entity_id)

        response = self.client.table(self.table_name).update(data).eq("id", entity_id).execute()
        if response.data and len(response.data) > 0:
            return Cliente.model_validate(response.data[0])
        return None

    async def delete(self, entity_id: int) -> bool:
        response = self.client.table(self.table_name).delete().eq("id", entity_id).execute()
        return len(response.data) > 0
