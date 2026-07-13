import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.repositories.clientes import ClientesRepository
from app.repositories.pedidos import PedidosRepository
from app.repositories.detalles_pedido import DetallesPedidoRepository
from app.repositories.productos import ProductosRepository
from app.use_cases.reporting import GetFinancialsUseCase, GetEarningsUseCase

router = APIRouter()


# Repository dependency providers
def get_clientes_repository() -> ClientesRepository:
    return ClientesRepository()


def get_pedidos_repository() -> PedidosRepository:
    return PedidosRepository()


def get_detalles_repository() -> DetallesPedidoRepository:
    return DetallesPedidoRepository()


def get_productos_repository() -> ProductosRepository:
    return ProductosRepository()


@router.get("/financials")
async def get_financials_report(
    clientes_repo: ClientesRepository = Depends(get_clientes_repository),
    pedidos_repo: PedidosRepository = Depends(get_pedidos_repository),
    detalles_repo: DetallesPedidoRepository = Depends(get_detalles_repository)
):
    """
    Retrieves global aggregates: total outstanding debts, collected cash, and overdue debt balances.
    """
    try:
        use_case = GetFinancialsUseCase(
            clientes_repo=clientes_repo,
            pedidos_repo=pedidos_repo,
            detalles_repo=detalles_repo
        )
        return await use_case.execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate financials report: {str(e)}"
        )


@router.get("/earnings")
async def get_earnings_report(
    start_date: datetime.date,
    end_date: datetime.date,
    pedidos_repo: PedidosRepository = Depends(get_pedidos_repository),
    detalles_repo: DetallesPedidoRepository = Depends(get_detalles_repository),
    productos_repo: ProductosRepository = Depends(get_productos_repository)
):
    """
    Calculates net profit of the meat wholesale business by subtracting purchase costs from resale values.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date."
        )

    try:
        use_case = GetEarningsUseCase(
            pedidos_repo=pedidos_repo,
            detalles_repo=detalles_repo,
            productos_repo=productos_repo
        )
        return await use_case.execute(start_date=start_date, end_date=end_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to calculate earnings: {str(e)}"
        )
