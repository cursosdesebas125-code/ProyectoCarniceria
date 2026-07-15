import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel
from supabase import Client

from app.repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class BaseRepository(ABC, Generic[T, CreateSchema, UpdateSchema]):
    """
    Abstract Base Repository interface to enforce Separation of Concerns.
    Decouples domain business logic from specific database implementation details (like Supabase).
    """

    @property
    @abstractmethod
    def table_name(self) -> str:
        """The Supabase table name for this repository."""
        ...

    @property
    @abstractmethod
    def model_class(self) -> type[T]:
        """The Pydantic model class used to validate results."""
        ...

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Retrieve a single entity by its unique ID."""
        ...

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Retrieve a paginated list of all entities."""
        ...

    @abstractmethod
    async def create(self, schema: CreateSchema) -> T:
        """Create a new entity record in the database."""
        ...

    @abstractmethod
    async def update(self, entity_id: int, schema: UpdateSchema) -> Optional[T]:
        """Update an existing entity record in the database."""
        ...

    @abstractmethod
    async def delete(self, entity_id: int) -> bool:
        """Delete an entity record from the database. Returns True if successful."""
        ...


class BaseSupabaseRepository(BaseRepository[T, CreateSchema, UpdateSchema]):
    """
    Shared Supabase implementation of CRUD operations.
    All entity repositories should inherit from this to avoid code duplication.
    """

    def __init__(self, db_client: Optional[Client] = None):
        self.client = db_client or get_supabase_client()

    async def get_by_id(self, entity_id: int) -> Optional[T]:
        response = self.client.table(self.table_name).select("*").eq("id", entity_id).execute()
        if response.data:
            return self.model_class.model_validate(response.data[0])
        return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        end_range = offset + limit - 1 if limit > 0 else offset
        response = self.client.table(self.table_name).select("*").range(offset, end_range).execute()
        return [self.model_class.model_validate(item) for item in response.data]

    async def _serialize_numeric_fields(self, data: Dict[str, Any], numeric_fields: List[str]) -> Dict[str, Any]:
        """Convert Decimal fields to float for Supabase numeric columns."""
        for field in numeric_fields:
            if field in data and data[field] is not None:
                data[field] = float(data[field])
        return data

    async def create(self, schema: CreateSchema) -> T:
        data = schema.model_dump(mode="json")
        data = await self._serialize_numeric_fields(data, self._numeric_fields())
        response = self.client.table(self.table_name).insert(data).execute()
        if response.data:
            return self.model_class.model_validate(response.data[0])
        raise RuntimeError(f"Failed to create record in {self.table_name}.")

    async def update(self, entity_id: int, schema: UpdateSchema) -> Optional[T]:
        data = schema.model_dump(exclude_unset=True, mode="json")
        if not data:
            return await self.get_by_id(entity_id)
        data = await self._serialize_numeric_fields(data, self._numeric_fields())
        response = self.client.table(self.table_name).update(data).eq("id", entity_id).execute()
        if response.data:
            return self.model_class.model_validate(response.data[0])
        return None

    async def delete(self, entity_id: int) -> bool:
        response = self.client.table(self.table_name).delete().eq("id", entity_id).execute()
        return len(response.data) > 0

    def _numeric_fields(self) -> List[str]:
        """
        Override in subclasses to specify field names requiring Decimal → float conversion.
        Example: return ["deuda_del_cliente", "valordecompra"]
        """
        return []
