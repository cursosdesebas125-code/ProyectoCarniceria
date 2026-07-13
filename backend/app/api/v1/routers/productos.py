from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.models import Producto, ProductoCreate, ProductoUpdate
from app.repositories.productos import ProductosRepository

router = APIRouter()


def get_productos_repository() -> ProductosRepository:
    """
    Dependency provider for the ProductosRepository.
    """
    return ProductosRepository()


@router.post("/", response_model=Producto, status_code=status.HTTP_201_CREATED)
async def create_producto(
    schema: ProductoCreate,
    repo: ProductosRepository = Depends(get_productos_repository)
):
    try:
        return await repo.create(schema)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create product: {str(e)}"
        )


@router.get("/", response_model=List[Producto])
async def list_productos(
    limit: int = 100,
    offset: int = 0,
    repo: ProductosRepository = Depends(get_productos_repository)
):
    return await repo.list_all(limit=limit, offset=offset)


@router.get("/{producto_id}", response_model=Producto)
async def get_producto(
    producto_id: int,
    repo: ProductosRepository = Depends(get_productos_repository)
):
    producto = await repo.get_by_id(producto_id)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto with ID {producto_id} not found"
        )
    return producto


@router.put("/{producto_id}", response_model=Producto)
async def update_producto(
    producto_id: int,
    schema: ProductoUpdate,
    repo: ProductosRepository = Depends(get_productos_repository)
):
    producto = await repo.update(producto_id, schema)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto with ID {producto_id} not found or update failed"
        )
    return producto


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_producto(
    producto_id: int,
    repo: ProductosRepository = Depends(get_productos_repository)
):
    deleted = await repo.delete(producto_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto with ID {producto_id} not found or deletion failed"
        )
    return None
