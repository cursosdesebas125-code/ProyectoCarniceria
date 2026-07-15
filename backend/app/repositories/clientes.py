from typing import List, Optional, Tuple
from app.domain.models import Cliente, ClienteCreate, ClienteUpdate
from app.repositories.base import BaseSupabaseRepository


class ClientesRepository(BaseSupabaseRepository[Cliente, ClienteCreate, ClienteUpdate]):
    """
    Supabase implementation of the BaseRepository for 'clientes'.
    """

    @property
    def table_name(self) -> str:
        return "clientes"

    @property
    def model_class(self) -> type[Cliente]:
        return Cliente

    def _numeric_fields(self) -> List[str]:
        return ["deuda_del_cliente"]

    async def list_paginated(self, limit: int = 5, offset: int = 0) -> Tuple[List[Cliente], int]:
        """
        Retrieves a page of clients along with the exact total record count.
        """
        end_range = offset + limit - 1 if limit > 0 else offset
        response = (
            self.client.table(self.table_name)
            .select("*", count="exact")
            .range(offset, end_range)
            .execute()
        )
        items = [Cliente.model_validate(item) for item in response.data]
        total_count = response.count if response.count is not None else len(items)
        return items, total_count
