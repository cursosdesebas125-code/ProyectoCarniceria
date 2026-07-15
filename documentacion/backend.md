# Backend — FastAPI

## Arquitectura General

El backend sigue los principios de **Clean Architecture** con separación en capas:

```
backend/
├── .env.example                    # Plantilla de variables de entorno
├── requirements.txt                # Dependencias Python
└── app/
    ├── main.py                     # Bootstrap: FastAPI + CORS + montaje de rutas
    ├── config/
    │   └── settings.py             # Configuración: Supabase URL/Key, CORS, Host, Puerto
    ├── domain/
    │   └── models.py               # Esquemas Pydantic (1:1 con columnas Supabase)
    ├── repositories/
    │   ├── base.py                 # BaseRepository (ABC) + BaseSupabaseRepository (CRUD genérico)
    │   ├── supabase_client.py      # Singleton del cliente Supabase
    │   ├── clientes.py             # Repositorio de clientes
    │   ├── productos.py            # Repositorio de productos
    │   ├── pedidos.py              # Repositorio de pedidos
    │   └── detalles_pedido.py      # Repositorio de detalles_pedido + list_by_pedido_id
    ├── use_cases/
    │   ├── apply_payment.py        # FIFO payment distribution logic
    │   ├── create_order.py         # Order creation with transactional rollback
    │   └── reporting.py            # Client statement, financials, earnings
    └── api/v1/
        ├── api.py                  # Agregador de rutas
        └── routers/
            ├── clientes.py         # CRUD + abonar + statement
            ├── productos.py        # CRUD
            ├── pedidos.py          # CRUD + create (usa CreateOrderUseCase)
            ├── detalles_pedido.py  # CRUD + list_by_pedido
            └── reports.py          # financials + earnings
```

---

## main.py — Punto de Entrada

```python
# backend/app/main.py (49 líneas)
# Funcionalidad:
# 1. Carga variables de entorno (.env)
# 2. Inicializa cliente Supabase
# 3. Configura CORS (allow_origins=["*"])
# 4. Monta api_router bajo /api/v1
```

---

## Configuración CORS

La aplicación tiene **dos niveles** de configuración CORS:

### Nivel 1: CORS Global (main.py)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Nivel 2: CORS por Configuración (settings.py)
```python
cors_origins: Union[str, List[str]] = Field(
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
    validation_alias="CORS_ORIGINS"
)
```

Soportados: lista de URLs, string JSON, o string separado por comas.

---

## Modelos de Dominio (`domain/models.py`)

### Modelo `DetallesPedido` — Campo `id` Opcional

El campo `id` en la clase `DetallesPedido` se declaró como `Optional[int] = None` para evitar errores de validación de Pydantic (`field required [type=missing]`) al procesar la respuesta de inserción devuelta por Supabase.

| Situación | Valor de `id` en la respuesta |
|:---|---|
| Inserción exitosa con `id` retornado por Supabase | `int` (el ID asignado) |
| Inserción exitosa sin `id` en la respuesta de Supabase | `None` |

```python
class DetallesPedido(DetallesPedidoBase):
    id: Optional[int] = None
```

> **Nota:** Si Supabase no retorna el `id` auto-generado, el valor será `None`. En `create_order.py` se accede a `inserted_detail.id` de forma segura.

### Modelos de Paginación

```python
class PaginatedClientes(BaseModel):
    items: List[Cliente]
    page: int
    limit: int
    total_items: int
    total_pages: int
```

### Modelos de Creación de Pedido

```python
class OrderItemCreate(BaseModel):
    id_producto: int              # ID del producto
    cantidad_producto: Decimal    # Cantidad/peso
    valor_del_pedido: Decimal     # Precio del ítem (cantidad × precio venta)

class OrderCreateRequest(BaseModel):
    idcliente: int                        # ID del cliente
    items: List[OrderItemCreate]          # Lista de productos

class OrderCreateResponse(BaseModel):
    pedido: Pedido                        # Encabezado del pedido
    items: List[DetallesPedido]           # Detalles registrados
```

### Modelo de Abono

```python
class AbonoRequest(BaseModel):
    monto: Decimal   # Monto del abono a aplicar
```

---

## Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `SUPABASE_URL` | URL del proyecto Supabase | — (requerida) |
| `SUPABASE_KEY` | Clave anónima o de servicio | — (requerida) |
| `HOST` | Dirección de enlace del servidor | `0.0.0.0` |
| `PORT` | Puerto del servidor | `8000` |
| `CORS_ORIGINS` | Orígenes permitidos para CORS | `["http://localhost:5173", "http://127.0.0.1:5173"]` |

---

## Repositorios (Capa de Datos)

### BaseSupabaseRepository (base.py)

Clase abstracta genérica que implementa CRUD compartido para todos los repositorios:

| Método | Descripción |
|:---|:---|
| `get_by_id(entity_id)` | Obtener entidad por ID |
| `list_all(limit, offset)` | Listar entidades con paginación |
| `create(schema)` | Crear nueva entidad |
| `update(entity_id, schema)` | Actualizar entidad existente |
| `delete(entity_id)` | Eliminar entidad |
| `_serialize_numeric_fields(data, numeric_fields)` | Convierte campos Decimal → float para columnas `numeric` de Supabase |

Cada repositorio concreto solo debe declarar:
- `table_name` (nombre de la tabla en Supabase)
- `model_class` (clase Pydantic para validación)
- `_numeric_fields()` (campos Decimal → float)

### Repositorios Concretos

| Repositorio | Tabla | Campos Numéricos | Métodos Adicionales |
|:---|---:|:---|:---|
| `ClientesRepository` | `clientes` | `deuda_del_cliente` | `list_paginated(limit, offset)` → devuelve `Tuple[List[Cliente], int]` con conteo exacto mediante `count="exact"` |
| `ProductosRepository` | `productos` | `valordecompra`, `valordeventa` | — |
| `PedidosRepository` | `pedidos` | — | — |
| `DetallesPedidoRepository` | `detalles_pedido` | `valor_del_pedido`, `cantidad_producto` | `list_by_pedido_id(pedido_id)` → detalles por pedido |

---

## Casos de Uso (Lógica de Negocio)

| Use Case | Archivo | Función |
|:---|---:|:---|
| `ApplyPaymentUseCase` | `use_cases/apply_payment.py` | Distribución FIFO de abonos + actualización de deuda. **Rollback**: revierte cambios en órdenes y deuda si falla. **Input**: `AbonoRequest.monto`. Busca órdenes Pendiente/Abonado ordenadas por fecha+ID. |
| `CreateOrderUseCase` | `use_cases/create_order.py` | Creación atómica de pedido con rollback transaccional. **Input**: `OrderCreateRequest`. **Output**: `OrderCreateResponse`. Rollback reversa: deuda → detalles → pedido. **Regla**: `fecha_pedido` se asigna automáticamente con `datetime.date.today()`. |
| `GetClientStatementUseCase` | `use_cases/reporting.py` | Estado de cuenta por cliente (órdenes + mora a 15 días). Devuelve lista con: `order_id`, `fecha_pedido`, `estado`, `total`, `overdue`, `days_since_created`. Ordenado por fecha descendente. |
| `GetFinancialsUseCase` | `use_cases/reporting.py` | Métricas globales: `total_outstanding_debt` (suma deudas), `total_collected` (órdenes Pagado), `total_overdue` (órdenes no pagadas > 15 días). |
| `GetEarningsUseCase` | `use_cases/reporting.py` | Ganancia neta en un período. **Input**: `start_date`, `end_date`. **Output**: `total_sales`, `total_cost`, `net_profit`, `orders_count`. Fórmula: `net_profit = Σ(valor_del_pedido - cantidad_producto × valordecompra)`. Usa caché de productos para optimizar. |

---

## Endpoints de la API (v1)

Prefijo base: `http://localhost:8000/api/v1`

### Clientes (`/clientes`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/clientes/` | Crear cliente. **Body**: `ClienteCreate`. **Response**: `Cliente` |
| `GET` | `/clientes/` | Listar clientes paginado. **Query**: `page` (int, default=1), `limit` (int, default=5). **Response**: `PaginatedClientes` `{items, page, limit, total_items, total_pages}` |
| `GET` | `/clientes/{id}` | Obtener cliente por ID. Retorna `404` si no existe |
| `PUT` | `/clientes/{id}` | Actualizar cliente. **Body**: `ClienteUpdate`. Retorna `404` si no existe |
| `DELETE` | `/clientes/{id}` | Eliminar cliente. Retorna `204` en éxito, `404` si no existe |
| `POST` | `/clientes/{id}/abonar` | Aplicar abono FIFO. **Body**: `AbonoRequest{monto}`. Usa `ApplyPaymentUseCase`. Retorna `400` si monto > deuda |
| `GET` | `/clientes/{id}/statement` | Estado de cuenta. Usa `GetClientStatementUseCase` |

### Productos (`/productos`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/productos/` | Crear producto. **Body**: `ProductoCreate`. **Response**: `Producto` |
| `GET` | `/productos/` | Listar productos. **Query**: `limit` (int, default=100), `offset` (int, default=0). **Response**: `List[Producto]` |
| `GET` | `/productos/{id}` | Obtener producto. Retorna `404` si no existe |
| `PUT` | `/productos/{id}` | Actualizar producto. **Body**: `ProductoUpdate`. Retorna `404` si no existe |
| `DELETE` | `/productos/{id}` | Eliminar producto. Retorna `204` en éxito, `404` si no existe |

### Pedidos (`/pedidos`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/pedidos/` | Crear pedido + actualizar deuda. **Body**: `OrderCreateRequest` (`idcliente` + `items[]`). **Response**: `OrderCreateResponse` (`pedido` + `items[]`). Usa `CreateOrderUseCase` |
| `GET` | `/pedidos/` | Listar pedidos. **Query**: `limit` (int, default=100), `offset` (int, default=0) |
| `GET` | `/pedidos/{id}` | Obtener pedido. Retorna `404` si no existe |
| `PUT` | `/pedidos/{id}` | Actualizar pedido. Retorna `404` si no existe |
| `DELETE` | `/pedidos/{id}` | Eliminar pedido. Retorna `204` en éxito, `404` si no existe |

### Detalles de Pedido (`/detalles-pedido`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/detalles-pedido/` | Crear detalle. **Body**: `DetallesPedidoCreate`. **Response**: `DetallesPedido` |
| `GET` | `/detalles-pedido/` | Listar detalles. **Query**: `limit` (int, default=100), `offset` (int, default=0) |
| `GET` | `/detalles-pedido/pedido/{pedido_id}` | Detalles por pedido. Usa `list_by_pedido_id()` |
| `GET` | `/detalles-pedido/{id}` | Obtener detalle. Retorna `404` si no existe |
| `PUT` | `/detalles-pedido/{id}` | Actualizar detalle. Retorna `404` si no existe |
| `DELETE` | `/detalles-pedido/{id}` | Eliminar detalle. Retorna `204` en éxito, `404` si no existe |

### Reportes (`/reports`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/reports/financials` | Métricas globales: deuda total, cobrado, mora. Usa `GetFinancialsUseCase` |
| `GET` | `/reports/earnings` | Ganancia neta por período. **Query**: `start_date` (date), `end_date` (date). Usa `GetEarningsUseCase`. Fórmula: `net_profit = Σ(valor_del_pedido - cantidad_producto × valordecompra)` |

---

## Stack Tecnológico del Backend

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Framework | FastAPI | ≥0.110.0 |
| Servidor ASGI | Uvicorn | ≥0.28.0 |
| Validación | Pydantic / Pydantic-Settings | ≥2.6.0 / ≥2.2.0 |
| Base de Datos | Supabase (PostgreSQL) | — |
| Cliente Supabase | supabase-py | ≥2.4.0 |