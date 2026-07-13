from app.repositories.base import BaseRepository
from app.repositories.supabase_client import get_supabase_client
from app.repositories.clientes import ClientesRepository
from app.repositories.productos import ProductosRepository
from app.repositories.pedidos import PedidosRepository
from app.repositories.detalles_pedido import DetallesPedidoRepository

__all__ = [
    "BaseRepository",
    "get_supabase_client",
    "ClientesRepository",
    "ProductosRepository",
    "PedidosRepository",
    "DetallesPedidoRepository"
]
