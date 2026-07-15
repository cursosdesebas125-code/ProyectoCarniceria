import datetime
import logging
from typing import List
from app.domain.models import (
    Pedido, PedidoCreate, 
    DetallesPedido, DetallesPedidoCreate, 
    ClienteUpdate, 
    OrderCreateRequest, OrderCreateResponse
)
from app.repositories.pedidos import PedidosRepository
from app.repositories.detalles_pedido import DetallesPedidoRepository
from app.repositories.clientes import ClientesRepository

logger = logging.getLogger(__name__)


class CreateOrderUseCase:
    """
    Use Case class representing the business flow for order creation.
    Encapsulates transaction-like behavior using compensatory rollbacks
    to maintain integrity across database updates in Supabase.
    """
    def __init__(
        self,
        pedidos_repo: PedidosRepository,
        detalles_repo: DetallesPedidoRepository,
        clientes_repo: ClientesRepository
    ):
        self.pedidos_repo = pedidos_repo
        self.detalles_repo = detalles_repo
        self.clientes_repo = clientes_repo

    async def execute(self, request: OrderCreateRequest) -> OrderCreateResponse:
        # Rule 2: Capture server's current date automatically inside the domain use case
        fecha_pedido = datetime.date.today()
        grand_total = sum(item.valor_del_pedido for item in request.items)

        logger.info(
            f"Initiating order creation for customer {request.idcliente}. "
            f"Items count: {len(request.items)}. Total: ${grand_total}"
        )

        # Track operations for compensation rollback
        created_pedido: Pedido = None
        created_details: List[DetallesPedido] = []
        original_debt = None
        debt_updated = False

        try:
            # 1. Fetch customer and check current outstanding balance
            cliente = await self.clientes_repo.get_by_id(request.idcliente)
            if not cliente:
                raise ValueError(f"Customer with ID {request.idcliente} does not exist.")
            original_debt = cliente.deuda_del_cliente

            # 2. Insert main order header (initial status: Pendiente)
            pedido_payload = PedidoCreate(
                idcliente=request.idcliente,
                estadopedido="Pendiente",
                fecha_pedido=fecha_pedido
            )
            created_pedido = await self.pedidos_repo.create(pedido_payload)
            logger.info(f"Order header created successfully. ID: {created_pedido.id}")

            # 3. Bulk insert details into detalles_pedido junction table
            for item in request.items:
                detalle_payload = DetallesPedidoCreate(
                    id_pedido=created_pedido.id,
                    id_producto=item.id_producto,
                    valor_del_pedido=item.valor_del_pedido,
                    cantidad_producto=item.cantidad_producto
                )
                inserted_detail = await self.detalles_repo.create(detalle_payload)
                created_details.append(inserted_detail)
                logger.info(f"Created line item for product {item.id_producto}, detail ID: {inserted_detail.id}")

            # 4. Update customer outstanding balance adding order total
            new_debt = original_debt + grand_total
            await self.clientes_repo.update(
                entity_id=request.idcliente,
                schema=ClienteUpdate(deuda_del_cliente=new_debt)
            )
            debt_updated = True
            logger.info(f"Updated customer {request.idcliente} debt from ${original_debt} to ${new_debt}.")

            return OrderCreateResponse(
                pedido=created_pedido,
                items=created_details
            )

        except Exception as err:
            logger.error(f"Order creation failed. Triggering compensatory rollback actions. Error: {str(err)}")
            await self._rollback(created_pedido, created_details, original_debt, debt_updated, request.idcliente)
            raise RuntimeError(f"Database transaction failed. All steps rolled back successfully. Reason: {str(err)}")

    async def _rollback(
        self,
        pedido: Pedido,
        details: List[DetallesPedido],
        original_debt: float,
        debt_updated: bool,
        cliente_id: int
    ):
        """
        Compensating transactions to revert changes in reverse order.
        """
        # Revert debt if updated
        if debt_updated and original_debt is not None:
            try:
                await self.clientes_repo.update(
                    entity_id=cliente_id,
                    schema=ClienteUpdate(deuda_del_cliente=original_debt)
                )
                logger.info(f"Rollback: Reverted client {cliente_id} debt to ${original_debt}")
            except Exception as e:
                logger.critical(f"Rollback critical failure: Could not revert client {cliente_id} debt. Error: {e}")

        # Delete detail line items
        for detail in details:
            try:
                await self.detalles_repo.delete(detail.id)
                logger.info(f"Rollback: Deleted order detail item ID {detail.id}")
            except Exception as e:
                logger.critical(f"Rollback critical failure: Could not delete order detail ID {detail.id}. Error: {e}")

        # Delete order header
        if pedido is not None:
            try:
                await self.pedidos_repo.delete(pedido.id)
                logger.info(f"Rollback: Deleted order header ID {pedido.id}")
            except Exception as e:
                logger.critical(f"Rollback critical failure: Could not delete order header ID {pedido.id}. Error: {e}")