from typing import List
from app.domain.models import DetallesPedido, DetallesPedidoCreate, DetallesPedidoUpdate
from app.repositories.base import BaseSupabaseRepository


class DetallesPedidoRepository(BaseSupabaseRepository[DetallesPedido, DetallesPedidoCreate, DetallesPedidoUpdate]):
    """
    Supabase implementation of the BaseRepository for 'detalles_pedido'.
    """

    @property
    def table_name(self) -> str:
        return "detalles_pedido"

    @property
    def model_class(self) -> type[DetallesPedido]:
        return DetallesPedido

    def _numeric_fields(self) -> List[str]:
        return ["valor_del_pedido", "cantidad_producto"]

    async def list_by_pedido_id(self, pedido_id: int) -> List[DetallesPedido]:
        """
        Retrieve all product detail lines associated with a specific order.
        """
        response = self.client.table(self.table_name).select("*").eq("id_pedido", pedido_id).execute()
        return [DetallesPedido.model_validate(item) for item in response.data]