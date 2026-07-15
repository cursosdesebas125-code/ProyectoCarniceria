from typing import List
from app.domain.models import Pedido, PedidoCreate, PedidoUpdate
from app.repositories.base import BaseSupabaseRepository


class PedidosRepository(BaseSupabaseRepository[Pedido, PedidoCreate, PedidoUpdate]):
    """
    Supabase implementation of the BaseRepository for 'pedidos'.
    """

    @property
    def table_name(self) -> str:
        return "pedidos"

    @property
    def model_class(self) -> type[Pedido]:
        return Pedido