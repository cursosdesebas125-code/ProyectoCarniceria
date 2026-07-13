from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")
CreateSchema = TypeVar("CreateSchema")
UpdateSchema = TypeVar("UpdateSchema")


class BaseRepository(ABC, Generic[T, CreateSchema, UpdateSchema]):
    """
    Abstract Base Repository interface to enforce Separation of Concerns.
    Decouples domain business logic from specific database implementation details (like Supabase).
    """

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Retrieve a single entity by its unique ID.
        """
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Retrieve a paginated list of all entities.
        """
        pass

    @abstractmethod
    async def create(self, schema: CreateSchema) -> T:
        """
        Create a new entity record in the database.
        """
        pass

    @abstractmethod
    async def update(self, entity_id: int, schema: UpdateSchema) -> Optional[T]:
        """
        Update an existing entity record in the database.
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: int) -> bool:
        """
        Delete an entity record from the database. Returns True if successful.
        """
        pass
