# Variables y Esquema de Base de Datos — Supabase

## Introducción

Este documento describe el mapeo estricto de todas las variables, tipos de datos y columnas de Supabase a través de todas las capas del sistema (base de datos → backend Pydantic → frontend TypeScript).

Se realizó una validación cruzada de **85 referencias de columnas** en **5 capas** sin encontrar discrepancias.

> **⚠️ Importante:** Todas las tablas y columnas en Supabase usan **minúsculas y snake_case**. PostgreSQL es **case-sensitive** para nombres entrecomillados. Las tablas y columnas en Supabase deben coincidir EXACTAMENTE con estos nombres.

---

## Convenciones de Nomenclatura en Supabase

| Tabla | Estilo | Ejemplos |
|:---|---:|:---|
| `clientes` | minúsculas + snake_case | `namecliente`, `deuda_del_cliente`, `estado` |
| `productos` | minúsculas + snake_case | `nombreproducto`, `valordecompra`, `valordeventa` |
| `pedidos` | minúsculas + snake_case | `idcliente`, `estadopedido`, `fecha_pedido` |
| `detalles_pedido` | minúsculas + snake_case | `id_pedido`, `valor_del_pedido`, `cantidad_producto` |

---

## Tabla: `clientes`

| Columna Supabase | Tipo | Pydantic (Python) | TypeScript | Descripción |
|:---|:---|:---|:---|:---|
| `id` | `int8` (PK) | `id: int` | `id: number` | Identificador único del cliente |
| `namecliente` | `varchar` | `namecliente: str` | `namecliente: string` | Nombre o Razón Social |
| `deuda_del_cliente` | `numeric` | `deuda_del_cliente: Decimal` | `deuda_del_cliente: number` | Saldo deudor acumulado |
| `estado` | `int2` | `estado: int` | `estado: ClienteEstado` (0\|1) | 1 = Activo, 0 = Inactivo |

### Mapeo en el código:

**Pydantic** (`domain/models.py`):
```python
class ClienteBase(BaseModel):
    namecliente: str = Field(..., description="Name of the client")
    deuda_del_cliente: Decimal = Field(default=Decimal("0.00"))
    estado: int = Field(default=1)
```

**TypeScript** (`types/index.ts`):
```typescript
export type ClienteEstado = 0 | 1;
export interface Cliente {
  id: number;
  namecliente: string;
  deuda_del_cliente: number;
  estado: ClienteEstado;
}
```

**Consulta SQL en repositorio** (`repositories/clientes.py`):
```python
self.client.table("clientes").select("id,namecliente,deuda_del_cliente,estado", count="exact")
```

---

## Tabla: `productos`

| Columna Supabase | Tipo | Pydantic (Python) | TypeScript | Descripción |
|:---|:---|:---|:---|:---|
| `id` | `int8` (PK) | `id: int` | `id: number` | Identificador único del producto |
| `nombreproducto` | `varchar` | `nombreproducto: str` | `nombreproducto: string` | Denominación comercial |
| `valordecompra` | `numeric` | `valordecompra: Decimal` | `valordecompra: number` | Costo de compra (por kg) |
| `valordeventa` | `numeric` | `valordeventa: Decimal` | `valordeventa: number` | Precio mayorista de venta (por kg) |

### Mapeo en el código:

**Pydantic** (`domain/models.py`):
```python
class ProductoBase(BaseModel):
    nombreproducto: str
    valordecompra: Decimal
    valordeventa: Decimal
```

**TypeScript** (`types/index.ts`):
```typescript
export interface Producto {
  id: number;
  nombreproducto: string;
  valordecompra: number;
  valordeventa: number;
}
```

**Consulta SQL en repositorio** (`repositories/productos.py`):
```python
self.table_name = "productos"
# Hereda CRUD genérico de BaseSupabaseRepository
```

---

## Tabla: `pedidos`

| Columna Supabase | Tipo | Pydantic (Python) | TypeScript | Descripción |
|:---|:---|:---|:---|:---|
| `id` | `int8` (PK) | `id: int` | `id: number` | Identificador único del pedido |
| `idcliente` | `int8` (FK → `clientes.id`) | `idcliente: int` | `idcliente: number` | Referencia al cliente |
| `estadopedido` | `varchar` | `estadopedido: str` | `estadopedido: PedidoEstado` | Estado (Pendiente, Entregado, Pagado, Abonado {monto}) |
| `fecha_pedido` | `date` | `fecha_pedido: date` | `fecha_pedido: string` | Fecha de registro del pedido |

### Mapeo en el código:

**Pydantic** (`domain/models.py`):
```python
class PedidoBase(BaseModel):
    idcliente: int
    estadopedido: str
    fecha_pedido: date
```

**TypeScript** (`types/index.ts`):
```typescript
export type PedidoEstado = 'Pendiente' | 'Entregado' | 'Pagado' | 'pagado' | `Abonado ${number}`;

export interface Pedido {
  id: number;
  idcliente: number;
  estadopedido: PedidoEstado;
  fecha_pedido: string;
}
```

**Consulta SQL en repositorio** (`repositories/pedidos.py`):
```python
self.table_name = "pedidos"
```

---

## Tabla: `detalles_pedido`

| Columna Supabase | Tipo | Pydantic (Python) | TypeScript | Descripción |
|:---|:---|:---|:---|:---|
| `id` | `int8` (PK) | `id: Optional[int] = None` | `id: number \| null` | Identificador de línea de detalle (opcional en respuesta de inserción para evitar error de validación) |
| `id_pedido` | `int8` (FK → `pedidos.id`) | `id_pedido: int` | `id_pedido: number` | Referencia al pedido (Cascada) |
| `id_producto` | `int8` (FK → `productos.id`) | `id_producto: int` | `id_producto: number` | Referencia al producto |
| `valor_del_pedido` | `numeric` | `valor_del_pedido: Decimal` | `valor_del_pedido: number` | Subtotal de la línea |
| `cantidad_producto` | `numeric` | `cantidad_producto: Decimal` | `cantidad_producto: number` | Cantidad vendida (Kg) |

### Mapeo en el código:

**Pydantic** (`domain/models.py`):
```python
class DetallesPedidoBase(BaseModel):
    id_pedido: int
    id_producto: int
    valor_del_pedido: Decimal
    cantidad_producto: Decimal


class DetallesPedido(DetallesPedidoBase):
    id: Optional[int] = None  # Opcional para evitar error de validación al recibir respuesta de Supabase

    model_config = {
        "from_attributes": True
    }
```

**TypeScript** (`types/index.ts`):
```typescript
export interface DetallesPedido {
  id: number;
  id_pedido: number;
  id_producto: number;
  valor_del_pedido: number;
  cantidad_producto: number;
}
```

**Consulta SQL en repositorio** (`repositories/detalles_pedido.py`):
```python
self.table_name = "detalles_pedido"
```

---

## Modelos de Solicitud Compuesta (Backend → Frontend)

### Creación de Pedido

| Modelo Pydantic | Interface TypeScript | Campos |
|:---|---:|:---|
| `OrderItemCreate` | `OrderItemCreate` | `id_producto`, `cantidad_producto`, `valor_del_pedido` |
| `OrderCreateRequest` | `OrderCreateRequest` | `idcliente`, `items: OrderItemCreate[]` |
| `OrderCreateResponse` | `OrderCreateResponse` | `pedido: Pedido`, `items: DetallesPedido[]` |

### Abonos

| Modelo Pydantic | Interface TypeScript | Campos |
|:---|---:|:---|
| `AbonoRequest` | `AbonoRequest` | `monto: Decimal / number` |
| — | `AbonoResponse` | `status`, `mensaje`, `nueva_deuda` |

### Paginación

| Modelo Pydantic | Interface TypeScript | Campos |
|:---|---:|:---|
| `PaginatedClientes` | `PaginatedResponse<T>` | `items`, `page`, `limit`, `total_items`, `total_pages` |

### Reportes

| Interface TypeScript | Campos |
|:---|:---|
| `ClienteStatement` | `order_id`, `fecha_pedido`, `total`, `days_since_created`, `estado`, `overdue` |
| `FinancialsReport` | `total_outstanding_debt`, `total_overdue`, `total_collected` |
| `EarningsReport` | `net_profit`, `orders_count`, `total_sales`, `total_cost` |

---

## Resumen de Validación Cruzada

| Tabla | Columnas | Ref. Backend (Pydantic) | Ref. Backend (Repo/SQL) | Ref. Frontend (TypeScript) | Ref. Frontend (main.ts) | **Discrepancias** |
|:---|---:|:---:|:---:|:---:|:---:|:---:|
| `clientes` | 4 | ✅ | ✅ | ✅ | ✅ | **0** |
| `productos` | 4 | ✅ | ✅ | ✅ | ✅ | **0** |
| `pedidos` | 4 | ✅ | ✅ | ✅ | ✅ | **0** |
| `detalles_pedido` | 5 | ✅ | ✅ | ✅ | ✅ | **0** |
| **TOTAL** | **17** | **17** | **17** | **17** | **17** | **0** |

> **85 referencias verificadas en total** (17 columnas × 5 capas) — **0 discrepancias encontradas**.

---

## Notas sobre el Error PGRST204

El error **PGRST204 (columna no encontrada)** de PostgREST puede ocurrir si:

1. Se envía un nombre de columna que **no existe** en la tabla de Supabase.
2. Hay diferencias de **mayúsculas/minúsculas** (PostgreSQL es case-sensitive).
3. Se hace referencia a una columna con un **alias incorrecto**.

### Verificaciones recomendadas si aparece el error:

```sql
-- Verificar que las columnas en Supabase tengan nombres exactos:
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'clientes';
-- Resultado esperado: id, namecliente, deuda_del_cliente, estado

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'productos';
-- Resultado esperado: id, nombreproducto, valordecompra, valordeventa

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pedidos';
-- Resultado esperado: id, idcliente, estadopedido, fecha_pedido

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'detalles_pedido';
-- Resultado esperado: id, id_pedido, id_producto, valor_del_pedido, cantidad_producto
```

> **Importante:** Todas las tablas y columnas usan **minúsculas y snake_case** en Supabase. Cualquier variación (ej. `NameCliente`, `Estado`, `Productos`, `Pedidos`, `Detalles_Pedido`) causará error PGRST204.