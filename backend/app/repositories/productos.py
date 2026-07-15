from typing import List
from app.domain.models import Producto, ProductoCreate, ProductoUpdate
from app.repositories.base import BaseSupabaseRepository


class ProductosRepository(BaseSupabaseRepository[Producto, ProductoCreate, ProductoUpdate]):
    """
    Supabase implementation of the BaseRepository for 'productos'.
    """

    @property
    def table_name(self) -> str:
        return "productos"

    @property
    def model_class(self) -> type[Producto]:
        return Producto

    def _numeric_fields(self) -> List[str]:
        return ["valordecompra", "valordeventa"]