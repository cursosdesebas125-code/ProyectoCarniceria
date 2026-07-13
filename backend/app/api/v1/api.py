from fastapi import APIRouter
from app.api.v1.routers.clientes import router as clientes_router
from app.api.v1.routers.productos import router as productos_router
from app.api.v1.routers.pedidos import router as pedidos_router
from app.api.v1.routers.detalles_pedido import router as detalles_router
from app.api.v1.routers.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(clientes_router, prefix="/clientes", tags=["Clientes"])
api_router.include_router(productos_router, prefix="/productos", tags=["Productos"])
api_router.include_router(pedidos_router, prefix="/pedidos", tags=["Pedidos"])
api_router.include_router(detalles_router, prefix="/detalles-pedido", tags=["Detalles de Pedido"])
api_router.include_router(reports_router, prefix="/reports", tags=["Informes Financieros"])
