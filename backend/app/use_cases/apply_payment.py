import logging
from decimal import Decimal
from typing import List, Tuple

from app.domain.models import AbonoRequest, ClienteUpdate, PedidoUpdate
from app.repositories.clientes import ClientesRepository
from app.repositories.detalles_pedido import DetallesPedidoRepository
from app.repositories.pedidos import PedidosRepository

logger = logging.getLogger(__name__)


class ApplyPaymentUseCase:
    """
    Use Case for applying a customer payment (abono) to outstanding orders
    using FIFO (First In, First Out) distribution logic.

    The payment is distributed across pending orders sorted by fecha_pedido (ascending)
    and ID (ascending). The customer's total debt is reduced by the payment amount.

    All database updates (order statuses + client debt reduction) are performed
    transactionally: if any update fails, all previous updates are rolled back
    to maintain data consistency.
    """

    def __init__(
        self,
        clientes_repo: ClientesRepository,
        pedidos_repo: PedidosRepository,
        detalles_repo: DetallesPedidoRepository,
    ):
        self.clientes_repo = clientes_repo
        self.pedidos_repo = pedidos_repo
        self.detalles_repo = detalles_repo

    async def execute(self, cliente_id: int, request: AbonoRequest) -> dict:
        """
        Distribute a payment across pending orders using FIFO and update debt.

        The method tracks all successful updates and performs a full rollback
        if any operation fails, ensuring transactional consistency.

        Args:
            cliente_id: The ID of the customer making the payment.
            request: The payment amount.

        Returns:
            A dictionary with status, message, updated debt, the fresh client
            data, and a list of affected orders with their new statuses.

        Raises:
            ValueError: If the customer is not found or payment exceeds debt.
        """
        if request.monto <= 0:
            raise ValueError("El monto del abono debe ser mayor a cero.")

        cliente = await self.clientes_repo.get_by_id(cliente_id)
        if not cliente:
            raise ValueError("Cliente no encontrado.")

        if request.monto > cliente.deuda_del_cliente:
            raise ValueError("El monto del abono no puede superar la deuda actual.")

        # Track all successful mutations for potential rollback
        updated_orders: List[Tuple[int, str, str]] = []  # (order_id, previous_status, new_status)
        previous_debt = cliente.deuda_del_cliente

        try:
            remaining_amount = request.monto
            pending_orders = await self._get_pending_orders_sorted(cliente_id)

            for order in pending_orders:
                if remaining_amount <= 0:
                    break

                order_balance = await self._calculate_order_balance(order.id)
                already_paid = self._parse_already_paid(order.estadopedido)
                remaining_order_balance = max(Decimal("0"), order_balance - already_paid)

                if remaining_order_balance <= 0:
                    continue

                previous_status = order.estadopedido

                if remaining_amount >= remaining_order_balance:
                    # Full payment for this order
                    remaining_amount -= remaining_order_balance
                    new_status = "Pagado"
                else:
                    # Partial payment for this order
                    amount_applied = remaining_amount
                    new_status = f"Abonado {already_paid + amount_applied:.2f}"
                    remaining_amount = Decimal("0")

                await self.pedidos_repo.update(
                    order.id, PedidoUpdate(estadopedido=new_status)
                )
                updated_orders.append((order.id, previous_status, new_status))
                logger.info(
                    "Order #%d updated to status: %s (was: %s)",
                    order.id,
                    new_status,
                    previous_status,
                )

            # Reduce the customer's total debt by the full payment amount
            new_debt = max(Decimal("0"), cliente.deuda_del_cliente - request.monto)
            await self.clientes_repo.update(
                cliente_id, ClienteUpdate(deuda_del_cliente=new_debt)
            )

            # Fetch the fresh client data after the update
            fresh_cliente = await self.clientes_repo.get_by_id(cliente_id)

            logger.info(
                "Payment $%.2f applied to client #%d. New debt: $%.2f",
                request.monto,
                cliente_id,
                new_debt,
            )

            return {
                "status": "success",
                "mensaje": f"Abono de ${request.monto:.2f} procesado.",
                "nueva_deuda": float(new_debt),
                "cliente": fresh_cliente.model_dump(mode="json") if fresh_cliente else None,
                "ordenes_afectadas": [
                    {
                        "id": order_id,
                        "estado_anterior": prev_status,
                        "estado_nuevo": new_status,
                    }
                    for order_id, prev_status, new_status in updated_orders
                ],
            }

        except Exception as e:
            logger.error(
                "Payment application failed for client #%d ($%.2f): %s. "
                "Initiating rollback of %d order updates.",
                cliente_id,
                request.monto,
                str(e),
                len(updated_orders),
            )

            # Rollback all order status updates in reverse order
            for order_id, previous_status, _ in reversed(updated_orders):
                try:
                    await self.pedidos_repo.update(
                        order_id, PedidoUpdate(estadopedido=previous_status)
                    )
                    logger.info(
                        "Rollback: Order #%d restored to status: %s",
                        order_id,
                        previous_status,
                    )
                except Exception as rollback_error:
                    logger.error(
                        "Rollback failed for order #%d: %s",
                        order_id,
                        rollback_error,
                    )

            # Rollback the client debt to its original value
            try:
                await self.clientes_repo.update(
                    cliente_id, ClienteUpdate(deuda_del_cliente=previous_debt)
                )
                logger.info(
                    "Rollback: Client #%d debt restored to $%.2f",
                    cliente_id,
                    previous_debt,
                )
            except Exception as rollback_error:
                logger.error(
                    "Rollback failed for client #%d debt: %s",
                    cliente_id,
                    rollback_error,
                )

            raise

    async def _get_pending_orders_sorted(self, cliente_id: int) -> List:
        """
        Retrieve all non-fully-paid orders for a client, sorted by date then ID (FIFO).
        """
        all_orders = await self.pedidos_repo.list_all(limit=1000)
        pending = [
            order
            for order in all_orders
            if order.idcliente == cliente_id and order.estadopedido.lower() != "pagado"
        ]
        pending.sort(key=lambda order: (order.fecha_pedido, order.id))
        return pending

    async def _calculate_order_balance(self, order_id: int) -> Decimal:
        """Calculate the total value of an order by summing its detail lines."""
        details = await self.detalles_repo.list_by_pedido_id(order_id)
        return sum((detail.valor_del_pedido for detail in details), Decimal("0"))

    @staticmethod
    def _parse_already_paid(estado: str) -> Decimal:
        """
        Extract the already-paid amount from a partial payment status string.

        Example: "Abonado 40.00" → Decimal("40.00")
        """
        if estado.lower().startswith("abonado "):
            try:
                return Decimal(estado.split(" ", 1)[1])
            except Exception:
                pass
        return Decimal("0")