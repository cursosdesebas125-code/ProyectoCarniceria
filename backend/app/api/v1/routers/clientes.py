from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.models import Cliente, ClienteCreate, ClienteUpdate, PaginatedClientes, AbonoRequest
from app.repositories.clientes import ClientesRepository
from app.repositories.pedidos import PedidosRepository
from app.repositories.detalles_pedido import DetallesPedidoRepository
from app.use_cases.reporting import GetClientStatementUseCase

router = APIRouter()


def get_clientes_repository() -> ClientesRepository:
    """
    Dependency provider for the ClientesRepository.
    Enables easy swapping and mocking of repository implementations.
    """
    return ClientesRepository()


@router.post("/", response_model=Cliente, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    schema: ClienteCreate,
    repo: ClientesRepository = Depends(get_clientes_repository)
):
    print(f"Saving to Supabase: {schema}")
    try:
        res = await repo.create(schema)
        print(f"Supabase Response: {res}")
        return res
    except Exception as e:
        print(f"Supabase Exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create client in Supabase: {str(e)}"
        )


@router.get("/", response_model=PaginatedClientes)
async def list_clientes(
    page: int = 1,
    limit: int = 5,
    repo: ClientesRepository = Depends(get_clientes_repository)
):
    if page < 1:
        page = 1
    if limit < 1:
        limit = 5

    offset = (page - 1) * limit
    items, total_count = await repo.list_paginated(limit=limit, offset=offset)
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 0

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total_items": total_count,
        "total_pages": total_pages
    }


@router.get("/{cliente_id}", response_model=Cliente)
async def get_cliente(
    cliente_id: int,
    repo: ClientesRepository = Depends(get_clientes_repository)
):
    cliente = await repo.get_by_id(cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente with ID {cliente_id} not found"
        )
    return cliente


@router.put("/{cliente_id}", response_model=Cliente)
async def update_cliente(
    cliente_id: int,
    schema: ClienteUpdate,
    repo: ClientesRepository = Depends(get_clientes_repository)
):
    cliente = await repo.update(cliente_id, schema)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente with ID {cliente_id} not found or update failed"
        )
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(
    cliente_id: int,
    repo: ClientesRepository = Depends(get_clientes_repository)
):
    deleted = await repo.delete(cliente_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente with ID {cliente_id} not found or deletion failed"
        )
    return None


# ==========================================
# STATEMENT INQUIRY ENDPOINT
# ==========================================

def get_pedidos_repository() -> PedidosRepository:
    return PedidosRepository()


def get_detalles_repository() -> DetallesPedidoRepository:
    return DetallesPedidoRepository()


@router.get("/{cliente_id}/statement")
async def get_cliente_statement(
    cliente_id: int,
    clientes_repo: ClientesRepository = Depends(get_clientes_repository),
    pedidos_repo: PedidosRepository = Depends(get_pedidos_repository),
    detalles_repo: DetallesPedidoRepository = Depends(get_detalles_repository)
):
    cliente = await clientes_repo.get_by_id(cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente with ID {cliente_id} not found"
        )
    
    use_case = GetClientStatementUseCase(
        pedidos_repo=pedidos_repo,
        detalles_repo=detalles_repo
    )
    return await use_case.execute(cliente_id)

