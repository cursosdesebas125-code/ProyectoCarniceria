from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.models import DetallesPedido, DetallesPedidoCreate, DetallesPedidoUpdate
from app.repositories.detalles_pedido import DetallesPedidoRepository

router = APIRouter()


def get_detalles_repository() -> DetallesPedidoRepository:
    """
    Dependency provider for the DetallesPedidoRepository.
    """
    return DetallesPedidoRepository()


@router.post("/", response_model=DetallesPedido, status_code=status.HTTP_201_CREATED)
async def create_detalle(
    schema: DetallesPedidoCreate,
    repo: DetallesPedidoRepository = Depends(get_detalles_repository)
):
    try:
        return await repo.create(schema)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create order detail: {str(e)}"
        )


@router.get("/", response_model=List[DetallesPedido])
async def list_detalles(
    limit: int = 100,
    offset: int = 0,
    repo: DetallesPedidoRepository = Depends(get_detalles_repository)
):
    return await repo.list_all(limit=limit, offset=offset)


@router.get("/pedido/{pedido_id}", response_model=List[DetallesPedido])
async def list_detalles_by_pedido(
    pedido_id: int,
    repo: DetallesPedidoRepository = Depends(get_detalles_repository)
):
    """
    Retrieve all product detail lines associated with a specific order.
    """
    return await repo.list_by_pedido_id(pedido_id)


@router.get("/{detalle_id}", response_model=DetallesPedido)
async def get_detalle(
    detalle_id: int,
    repo: DetallesPedidoRepository = Depends(get_detalles_repository)
):
    detalle = await repo.get_by_id(detalle_id)
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order detail with ID {detalle_id} not found"
        )
    return detalle


@router.put("/{detalle_id}", response_model=DetallesPedido)
async def update_detalle(
    detalle_id: int,
    schema: DetallesPedidoUpdate,
    repo: DetallesPedidoRepository = Depends(get_detalles_repository)
):
    detalle = await repo.update(detalle_id, schema)
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order detail with ID {detalle_id} not found or update failed"
        )
    return detalle


@router.delete("/{detalle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detalle(
    detalle_id: int,
    repo: DetallesPedidoRepository = Depends(get_detalles_repository)
):
    deleted = await repo.delete(detalle_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order detail with ID {detalle_id} not found or deletion failed"
        )
    return None
