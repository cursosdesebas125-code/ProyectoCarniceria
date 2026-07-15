from datetime import date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ==========================================
# CLIENTES MODELS
# ==========================================

class ClienteBase(BaseModel):
    namecliente: str = Field(..., description="Name of the client")
    deuda_del_cliente: Decimal = Field(default=Decimal("0.00"), description="Total outstanding debt of the client")
    estado: int = Field(default=1, description="Status of the client (e.g. 1 = Active, 0 = Inactive)")


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    namecliente: Optional[str] = None
    deuda_del_cliente: Optional[Decimal] = None
    estado: Optional[int] = None


class AbonoRequest(BaseModel):
    monto: Decimal


class Cliente(ClienteBase):
    id: int

    model_config = {
        "from_attributes": True
    }


# ==========================================
# PRODUCTOS MODELS
# ==========================================

class ProductoBase(BaseModel):
    nombreproducto: str = Field(..., description="Name of the product")
    valordecompra: Decimal = Field(..., description="Acquisition/purchase cost of the product")
    valordeventa: Decimal = Field(..., description="Wholesale/retail selling price")


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombreproducto: Optional[str] = None
    valordecompra: Optional[Decimal] = None
    valordeventa: Optional[Decimal] = None


class Producto(ProductoBase):
    id: int

    model_config = {
        "from_attributes": True
    }


# ==========================================
# PEDIDOS MODELS
# ==========================================

class PedidoBase(BaseModel):
    idcliente: int = Field(..., description="Foreign key to the cliente who placed the order")
    estadopedido: str = Field(..., description="Current status of the order (e.g. Pendiente, Entregado, Pagado)")
    fecha_pedido: date = Field(..., description="Date when the order was placed")


class PedidoCreate(PedidoBase):
    pass


class PedidoUpdate(BaseModel):
    idcliente: Optional[int] = None
    estadopedido: Optional[str] = None
    fecha_pedido: Optional[date] = None


class Pedido(PedidoBase):
    id: int

    model_config = {
        "from_attributes": True
    }


# ==========================================
# DETALLES PEDIDO MODELS
# ==========================================

class DetallesPedidoBase(BaseModel):
    id_pedido: int = Field(..., description="Foreign key reference to the parent Pedido")
    id_producto: int = Field(..., description="Foreign key reference to the product")
    valor_del_pedido: Decimal = Field(..., description="Subtotal price for this detail line")
    cantidad_producto: Decimal = Field(..., description="Quantity of product ordered (can be fractional for meat weight)")


class DetallesPedidoCreate(DetallesPedidoBase):
    pass


class DetallesPedidoUpdate(BaseModel):
    id_pedido: Optional[int] = None
    id_producto: Optional[int] = None
    valor_del_pedido: Optional[Decimal] = None
    cantidad_producto: Optional[Decimal] = None


class DetallesPedido(DetallesPedidoBase):
    id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


# ==========================================
# PAGINATION MODELS
# ==========================================

class PaginatedClientes(BaseModel):
    items: List[Cliente]
    page: int
    limit: int
    total_items: int
    total_pages: int


# ==========================================
# ORDER CREATION USE CASE MODELS
# ==========================================

class OrderItemCreate(BaseModel):
    id_producto: int = Field(..., description="ID of the product being ordered")
    cantidad_producto: Decimal = Field(..., description="Weight / quantity of the product")
    valor_del_pedido: Decimal = Field(..., description="Price for this line item (quantity * sale price)")


class OrderCreateRequest(BaseModel):
    idcliente: int = Field(..., description="ID of the customer placing the order")
    items: List[OrderItemCreate] = Field(..., description="List of products ordered")


class OrderCreateResponse(BaseModel):
    pedido: Pedido = Field(..., description="Main order header details")
    items: List[DetallesPedido] = Field(..., description="List of recorded detail line items")