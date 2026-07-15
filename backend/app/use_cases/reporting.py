import datetime
import logging
from typing import List, Dict, Any
from app.repositories.pedidos import PedidosRepository
from app.repositories.detalles_pedido import DetallesPedidoRepository
from app.repositories.clientes import ClientesRepository
from app.repositories.productos import ProductosRepository

logger = logging.getLogger(__name__)


class GetClientStatementUseCase:
    """
    Assembles a customer's historic orders, their payment statuses,
    and identifies any overdue balance (beyond the 15-day payment term).
    """
    def __init__(
        self,
        pedidos_repo: PedidosRepository,
        detalles_repo: DetallesPedidoRepository
    ):
        self.pedidos_repo = pedidos_repo
        self.detalles_repo = detalles_repo

    async def execute(self, cliente_id: int) -> List[Dict[str, Any]]:
        # Fetch all orders
        all_orders = await self.pedidos_repo.list_all(limit=1000)
        client_orders = [o for o in all_orders if o.idcliente == cliente_id]
        
        statement_records = []
        today = datetime.date.today()

        for order in client_orders:
            # Fetch line items for this order
            details = await self.detalles_repo.list_by_pedido_id(order.id)
            order_total = sum(float(d.valor_del_pedido) for d in details)

            # Rule 2: Overdue term is exactly 15 days from fecha_pedido
            is_overdue = False
            if order.estadopedido != "Pagado":
                days_elapsed = (today - order.fecha_pedido).days
                if days_elapsed > 15:
                    is_overdue = True

            statement_records.append({
                "order_id": order.id,
                "fecha_pedido": order.fecha_pedido.isoformat(),
                "estado": order.estadopedido,
                "total": order_total,
                "overdue": is_overdue,
                "days_since_created": (today - order.fecha_pedido).days
            })

        # Sort statement by date descending
        statement_records.sort(key=lambda x: x["fecha_pedido"], reverse=True)
        return statement_records


class GetFinancialsUseCase:
    """
    Calculates aggregate metrics across all customers and orders:
    - Total outstanding debts.
    - Successfully collected balances (orders marked as Pagado).
    - Overdue/Mora balances (orders not Pagado and older than 15 days).
    """
    def __init__(
        self,
        clientes_repo: ClientesRepository,
        pedidos_repo: PedidosRepository,
        detalles_repo: DetallesPedidoRepository
    ):
        self.clientes_repo = clientes_repo
        self.pedidos_repo = pedidos_repo
        self.detalles_repo = detalles_repo

    async def execute(self) -> Dict[str, Any]:
        # 1. Total Outstanding Debt
        clients = await self.clientes_repo.list_all(limit=1000)
        total_outstanding = sum(float(c.deuda_del_cliente) for c in clients)

        # 2. Orders Aggregation
        orders = await self.pedidos_repo.list_all(limit=1000)
        
        total_collected = 0.0
        total_overdue = 0.0
        today = datetime.date.today()

        for order in orders:
            # Fetch details for the order to sum its actual registered value
            details = await self.detalles_repo.list_by_pedido_id(order.id)
            order_total = sum(float(d.valor_del_pedido) for d in details)

            if order.estadopedido == "Pagado":
                total_collected += order_total
            else:
                # Unpaid orders older than 15 days are overdue
                days_elapsed = (today - order.fecha_pedido).days
                if days_elapsed > 15:
                    total_overdue += order_total

        return {
            "total_outstanding_debt": total_outstanding,
            "total_collected": total_collected,
            "total_overdue": total_overdue
        }


class GetEarningsUseCase:
    """
    Calculates the exact net profit of the business within a timeframe by:
    Net Profit = Sum ( line_sale_value - (line_quantity * product_cost_price) )
    """
    def __init__(
        self,
        pedidos_repo: PedidosRepository,
        detalles_repo: DetallesPedidoRepository,
        productos_repo: ProductosRepository
    ):
        self.pedidos_repo = pedidos_repo
        self.detalles_repo = detalles_repo
        self.productos_repo = productos_repo

    async def execute(self, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
        orders = await self.pedidos_repo.list_all(limit=1000)
        
        # Filter orders in timeframe
        filtered_orders = [
            o for o in orders 
            if start_date <= o.fecha_pedido <= end_date
        ]

        total_sales = 0.0
        total_cost = 0.0
        
        # Cache product data to avoid repeated DB hits
        products_cache = {}

        for order in filtered_orders:
            details = await self.detalles_repo.list_by_pedido_id(order.id)
            
            for detail in details:
                total_sales += float(detail.valor_del_pedido)
                
                # Fetch product details
                prod_id = detail.id_producto
                if prod_id not in products_cache:
                    prod = await self.productos_repo.get_by_id(prod_id)
                    if prod:
                        products_cache[prod_id] = float(prod.valordecompra)
                    else:
                        products_cache[prod_id] = 0.0
                
                purchase_cost_rate = products_cache[prod_id]
                qty = float(detail.cantidad_producto)
                total_cost += qty * purchase_cost_rate

        net_profit = total_sales - total_cost

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_sales": total_sales,
            "total_cost": total_cost,
            "net_profit": net_profit,
            "orders_count": len(filtered_orders)
        }