from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.models import Pedido, PedidoCreate, PedidoUpdate, OrderCreateRequest, OrderCreateResponse
from app.repositories.pedidos import PedidosRepository
from app.repositories.clientes import ClientesRepository
from app.repositories.detalles_pedido import DetallesPedidoRepository
from app.use_cases.create_order import CreateOrderUseCase

router = APIRouter()


def get_pedidos_repository() -> PedidosRepository:
    """
    Dependency provider for the PedidosRepository.
    """
    return PedidosRepository()


def get_clientes_repository() -> ClientesRepository:
    """
    Dependency provider for the ClientesRepository.
    """
    return ClientesRepository()


def get_detalles_repository() -> DetallesPedidoRepository:
    """
    Dependency provider for the DetallesPedidoRepository.
    """
    return DetallesPedidoRepository()


@router.post("/", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_pedido(
    schema: OrderCreateRequest,
    pedidos_repo: PedidosRepository = Depends(get_pedidos_repository),
    detalles_repo: DetallesPedidoRepository = Depends(get_detalles_repository),
    clientes_repo: ClientesRepository = Depends(get_clientes_repository)
):
    print(f"Saving to Supabase: {schema}")
    try:
        use_case = CreateOrderUseCase(
            pedidos_repo=pedidos_repo,
            detalles_repo=detalles_repo,
            clientes_repo=clientes_repo
        )
        res = await use_case.execute(schema)
        print(f"Supabase Response: {res}")
        return res
    except Exception as e:
        print(f"Supabase Exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create order in Supabase: {str(e)}"
        )


@router.get("/", response_model=List[Pedido])
async def list_pedidos(
    limit: int = 100,
    offset: int = 0,
    repo: PedidosRepository = Depends(get_pedidos_repository)
):
    return await repo.list_all(limit=limit, offset=offset)


@router.get("/{pedido_id}", response_model=Pedido)
async def get_pedido(
    pedido_id: int,
    repo: PedidosRepository = Depends(get_pedidos_repository)
):
    pedido = await repo.get_by_id(pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido with ID {pedido_id} not found"
        )
    return pedido


@router.put("/{pedido_id}", response_model=Pedido)
async def update_pedido(
    pedido_id: int,
    schema: PedidoUpdate,
    repo: PedidosRepository = Depends(get_pedidos_repository)
):
    pedido = await repo.update(pedido_id, schema)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido with ID {pedido_id} not found or update failed"
        )
    return pedido


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pedido(
    pedido_id: int,
    repo: PedidosRepository = Depends(get_pedidos_repository)
):
    deleted = await repo.delete(pedido_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido with ID {pedido_id} not found or deletion failed"
        )
    return None
