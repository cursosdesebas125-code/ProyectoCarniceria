# Sistema de Distribución de Carne a Plazos

Este proyecto implementa una plataforma full-stack modular para la gestión comercial y financiera de una empresa de distribución de carne al por mayor. El sistema destaca por su modelo de venta basado en créditos a plazos, facilitando el control de saldos y cuentas por cobrar bajo términos rigurosos de vencimiento.

---

## 1. Descripción del Negocio

El modelo de negocio está diseñado específicamente para la comercialización mayorista de productos cárnicos con un esquema de financiamiento flexible de **crédito a plazos de 15 días sin intereses**.

### Dinámica de Operaciones:
* **Venta Mayorista**: Distribución de cortes de carne procesados, pesados en kilogramos (soportando cantidades decimales, ej. 125.50 kg).
* **Crédito de 15 Días**: Cada pedido entregado a un cliente genera una cuenta por cobrar que vence exactamente 15 días después de la fecha de registro del pedido (`fecha_pedido`).

* **Control de Saldos**: El sistema incrementa automáticamente la deuda del cliente (`deuda_del_cliente`) al registrar un nuevo pedido en estado "Pendiente".
* **Gestión de Riesgo (Mora)**: Si un pedido permanece sin pagar después del plazo establecido (15 días), se clasifica como saldo en mora, suspendiendo temporalmente la capacidad del cliente para realizar nuevos pedidos.

---

## 2. Arquitectura del Sistema (Clean Architecture)

El proyecto adopta los principios de **Clean Architecture** (Arquitectura Limpia) y la **Separación de Responsabilidades (SoC)**, asegurando que las reglas de negocio permanezcan desacopladas de los frameworks de entrega (FastAPI) y de los proveedores de bases de datos (Supabase).

### 2.1 Estructura del Backend (Python/FastAPI)

El backend está organizado en capas modulares que aíslan la lógica del negocio:

```
backend/
├── .env.example                      # Plantilla de variables de entorno
├── requirements.txt                  # Dependencias Python
└── app/
    ├── main.py                       # Punto de entrada FastAPI + rutas legacy
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── settings.py               # Configuración: Supabase URL/Key, CORS, Host, Puerto
    ├── domain/
    │   ├── __init__.py
    │   └── models.py                 # Esquemas Pydantic (1:1 con columnas Supabase)
    ├── repositories/
    │   ├── __init__.py
    │   ├── base.py                   # Interfaz abstracta BaseRepository[T, Create, Update]
    │   ├── supabase_client.py        # Singleton del cliente Supabase
    │   ├── clientes.py               # CRUD repositorio de clientes
    │   ├── productos.py              # CRUD repositorio de productos
    │   ├── pedidos.py                # CRUD repositorio de pedidos
    │   └── detalles_pedido.py        # CRUD repositorio de detalles_pedido + list_by_pedido_id
    ├── use_cases/
    │   ├── __init__.py
    │   ├── create_order.py           # Caso de uso: creación de pedido con rollback transaccional
    │   └── reporting.py              # Casos de uso: estado de cuenta, financieros, ganancias
    └── api/
        ├── __init__.py
        └── v1/
            ├── __init__.py
            ├── api.py                # Agregador de rutas de la API v1
            └── routers/
                ├── __init__.py
                ├── clientes.py       # CRUD + abono FIFO + estado de cuenta
                ├── productos.py      # CRUD productos
                ├── pedidos.py        # CRUD + creación de pedido (usa CreateOrderUseCase)
                ├── detalles_pedido.py# CRUD + listar por pedido
                └── reports.py        # Reportes financieros globales y ganancias
```

| Capa | Ubicación | Responsabilidad |
|------|-----------|-----------------|
| **Dominio** | `domain/models.py` | Entidades Pydantic, esquemas de creación/actualización, modelos de paginación y solicitudes |
| **Casos de Uso** | `use_cases/` | Lógica de negocio orquestada: creación de pedidos con rollback, cálculos financieros, estados de cuenta |
| **Repositorios** | `repositories/` | Abstracción de persistencia sobre Supabase siguiendo el patrón Repository |
| **Controladores API v1** | `api/v1/routers/` | Endpoints REST que delegan en casos de uso y repositorios |
| **Rutas Legacy** | `main.py` | Rutas directas en FastAPI (clientes, productos, pedidos) + configuración CORS global |

### 2.2 Estructura del Frontend (Vite + TypeScript)

```
frontend/
├── index.html                        # SPA con 3 ventanas (Admin, POS, Reportes)
├── package.json                      # Dependencias: vite, typescript
├── tsconfig.json                     # Configuración de TypeScript
├── vite.config.ts                    # Configuración de Vite
├── css/
│   └── style.css                     # Sistema de diseño (variables CSS, componentes, animaciones)
└── src/
    ├── main.ts                       # AppController: lógica completa de UI e interacción con API
    ├── services/
    │   └── api.ts                    # Cliente HTTP hacia http://localhost:8000/api/v1
    └── types/
        └── index.ts                  # Interfaces TypeScript sincronizadas con modelos Pydantic
```

### 2.3 Flujo de Comunicación

```
Frontend (Vite/TS) → services/api.ts → HTTP (fetch) → FastAPI /api/v1/... 
  → Router → UseCase → Repository → Supabase (PostgreSQL)
```

---

## 3. Configuración de CORS

El sistema tiene dos niveles de configuración CORS:

### 3.1 CORS Global (main.py — Rutas Legacy)
Configurado en `backend/app/main.py` con permisos abiertos para desarrollo:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Permitir todos los orígenes
    allow_credentials=False,
    allow_methods=["*"],       # Todos los métodos HTTP
    allow_headers=["*"],       # Todos los headers
)
```

### 3.2 CORS por Configuración (settings.py — API v1)
Gestionado mediante `backend/app/config/settings.py` con la propiedad `cors_origins`:

```python
cors_origins: Union[str, List[str]] = Field(
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
    validation_alias="CORS_ORIGINS"
)
```

El valor puede ser:
- Una lista de URLs: `["http://localhost:5173", "http://127.0.0.1:5173"]`
- Un string JSON: `'["http://localhost:5173"]'`
- Un string separado por comas: `"http://localhost:5173,http://127.0.0.1:5173"`

---

## 4. Modelo de Base de Datos (Supabase)

El modelo de datos relacional de Supabase utiliza **minúsculas estrictas y snake_case** en todas las tablas y columnas. PostgreSQL es case-sensitive para nombres entrecomillados, por lo que cualquier variación (ej. `Clientes`, `Productos`, `NombreProducto`) causaría errores.

| Tabla | Columna | Tipo de Datos | Restricciones / Descripción |
| :--- | :--- | :--- | :--- |
| **clientes** | `id`<br>`namecliente`<br>`deuda_del_cliente`<br>`estado` | int8 (PK)<br>varchar<br>numeric<br>int2 | Identificador único del cliente<br>Nombre o Razón Social<br>Saldo deudor acumulado del cliente<br>Estado comercial (1 = Activo, 0 = Inactivo) |
| **productos** | `id`<br>`nombreproducto`<br>`valordecompra`<br>`valordeventa` | int8 (PK)<br>varchar<br>numeric<br>numeric | Identificador único del corte de carne<br>Denominación comercial del producto<br>Costo de compra (por kg)<br>Precio mayorista de venta (por kg) |
| **pedidos** | `id`<br>`idcliente`<br>`estadopedido`<br>`fecha_pedido` | int8 (PK)<br>int8 (FK → clientes.id)<br>varchar<br>date | Identificador único de la transacción<br>Referencia al cliente<br>Estado (Pendiente, Entregado, Pagado/pagado, Abonado {monto})<br>Fecha de registro del pedido |
| **detalles_pedido** | `id`<br>`id_pedido`<br>`id_producto`<br>`valor_del_pedido`<br>`cantidad_producto` | int8 (PK)<br>int8 (FK → pedidos.id)<br>int8 (FK → productos.id)<br>numeric<br>numeric | Identificador de línea de detalle<br>Referencia al pedido (Cascada)<br>Referencia al producto<br>Subtotal de la línea<br>Cantidad de producto vendida (Kg) |

---

## 5. Mapeo de Columnas: Validación Cruzada Backend ↔ Frontend ↔ Supabase

Se realizó un mapeo exhaustivo de cada columna de base de datos a través de todas las capas del código para garantizar consistencia y evitar el error **PGRST204 (columna no encontrada)**.

### 5.1 Tabla: `clientes` — Mapeo 1:1 Verificado

| Columna Supabase | domain/models.py (Pydantic) | repositories/clientes.py | types/index.ts (TS) | main.ts (Frontend) |
|:---|:---|:---|:---|:---|
| `id` | `id: int` | `entity_id: int` | `id: number` | `c.id` |
| `namecliente` | `namecliente: str` | `schema.model_dump()` | `namecliente: string` | `c.namecliente` |
| `deuda_del_cliente` | `deuda_del_cliente: Decimal` | `"deuda_del_cliente"` | `deuda_del_cliente: number` | `c.deuda_del_cliente` |
| `estado` | `estado: int` | `schema.model_dump()` | `estado: ClienteEstado` | `c.estado` |

**✅ VEREDICTO: SIN DISCREPANCIAS.** Todos los campos usan minúsculas estrictas.

### 5.2 Tabla: `productos` — Mapeo 1:1 Verificado

| Columna Supabase | domain/models.py (Pydantic) | repositories/productos.py | types/index.ts (TS) | main.ts (Frontend) |
|:---|:---|:---|:---|:---|
| `id` | `id: int` | `entity_id: int` | `id: number` | `p.id` |
| `nombreproducto` | `nombreproducto: str` | `schema.model_dump()` | `nombreproducto: string` | `p.nombreproducto` |
| `valordecompra` | `valordecompra: Decimal` | `schema.model_dump()` | `valordecompra: number` | `p.valordecompra` |
| `valordeventa` | `valordeventa: Decimal` | `schema.model_dump()` | `valordeventa: number` | `p.valordeventa` |

**✅ VEREDICTO: SIN DISCREPANCIAS.** Todos los campos usan minúsculas estrictas.

### 5.3 Tabla: `pedidos` — Mapeo 1:1 Verificado

| Columna Supabase | domain/models.py (Pydantic) | repositories/pedidos.py | types/index.ts (TS) | main.ts (Frontend) |
|:---|:---|:---|:---|:---|
| `id` | `id: int` | `entity_id: int` | `id: number` | `o.id` |
| `idcliente` | `idcliente: int` | `schema.model_dump()` | `idcliente: number` | `clientId` |
| `estadopedido` | `estadopedido: str` | `schema.model_dump()` | `estadopedido: PedidoEstado` | `order.estadopedido` |
| `fecha_pedido` | `fecha_pedido: date` | `schema.model_dump()` | `fecha_pedido: string` | `order.fecha_pedido` |

**✅ VEREDICTO: SIN DISCREPANCIAS.** Todos los campos usan minúsculas estrictas.

### 5.4 Tabla: `detalles_pedido` — Mapeo 1:1 Verificado

| Columna Supabase | domain/models.py (Pydantic) | repositories/detalles_pedido.py | types/index.ts (TS) | main.ts (Frontend) |
|:---|:---|:---|:---|:---|
| `id` | `id: int` | `entity_id: int` | `id: number` | `detalle.id` |
| `id_pedido` | `id_pedido: int` | `self.table_name = "detalles_pedido"` | `id_pedido: number` | `detalle.id_pedido` |
| `id_producto` | `id_producto: int` | `select("*")` | `id_producto: number` | `item.id_producto` |
| `valor_del_pedido` | `valor_del_pedido: Decimal` | `schema.model_dump()` | `valor_del_pedido: number` | `item.valor_del_pedido` |
| `cantidad_producto` | `cantidad_producto: Decimal` | `schema.model_dump()` | `cantidad_producto: number` | `item.cantidad_producto` |

**✅ VEREDICTO: SIN DISCREPANCIAS.** Todos los campos usan minúsculas estrictas.

### 5.5 Resumen del Mapeo

| Tabla | Columnas Verificadas | Discrepancias |
|:---|---:|:---:|
| `clientes` | 4 columnas × 4 capas = **16 referencias** | ✅ **0** |
| `productos` | 4 columnas × 4 capas = **16 referencias** | ✅ **0** |
| `pedidos` | 4 columnas × 4 capas = **16 referencias** | ✅ **0** |
| `detalles_pedido` | 5 columnas × 4 capas = **20 referencias** | ✅ **0** |
| **TOTAL** | **68 referencias verificadas** | **0 discrepancias** |

---

## 6. Notas sobre el Error PGRST204

El error **PGRST204 (columna no encontrada)** de PostgREST ocurre típicamente cuando:
1. Se envía un nombre de columna que no existe en la tabla de Supabase.
2. Hay diferencias de mayúsculas/minúsculas (PostgreSQL es case-sensitive para nombres entrecomillados).
3. Se hace referencia a una columna de una tabla con alias incorrecto.

En este proyecto, **todas las columnas están alineadas 1:1 con el esquema de Supabase**. Las convenciones de nomenclatura detectadas son:

| Tabla | Estilo | Ejemplo |
|:---|---:|:---|
| `clientes` | minúsculas estrictas | `namecliente`, `deuda_del_cliente`, `estado` |
| `productos` | minúsculas estrictas | `nombreproducto`, `valordecompra`, `valordeventa` |
| `pedidos` | minúsculas estrictas | `idcliente`, `estadopedido`, `fecha_pedido` |
| `detalles_pedido` | minúsculas estrictas | `id_pedido`, `valor_del_pedido`, `cantidad_producto` |

Si se presenta el error PGRST204 en tiempo de ejecución, verificar:
- Que las columnas en Supabase tengan **exactamente** los nombres documentados (minúsculas estrictas).
- Que las tablas en Supabase se llamen `clientes`, `productos`, `pedidos`, `detalles_pedido` (todas en minúsculas).
- Que los triggers o funciones SQL en Supabase no estén renombrando columnas automáticamente.

---

## 7. Especificación de Endpoints (API v1)

Todos los endpoints se sirven bajo el prefijo `http://localhost:8000/api/v1`.

### 7.1 Clientes (`/clientes`)

| Método | Ruta | Descripción | Parámetros |
|--------|------|-------------|------------|
| `POST` | `/clientes/` | Crear un nuevo cliente | Body: `ClienteCreate` |
| `GET` | `/clientes/` | Listar clientes (paginado) | `?page=1&limit=5` |
| `GET` | `/clientes/{id}` | Obtener cliente por ID | Path: `id` |
| `PUT` | `/clientes/{id}` | Actualizar cliente | Path: `id`, Body: `ClienteUpdate` |
| `DELETE` | `/clientes/{id}` | Eliminar cliente | Path: `id` |
| `POST` | `/clientes/{id}/abonar` | Aplicar abono FIFO a pedidos pendientes con rollback transaccional | Path: `id`, Body: `AbonoRequest` → Response: `AbonoResponse` enriquecido |
| `GET` | `/clientes/{id}/statement` | Obtener estado de cuenta detallado | Path: `id` |

### 7.2 Productos (`/productos`)

| Método | Ruta | Descripción | Parámetros |
|--------|------|-------------|------------|
| `POST` | `/productos/` | Crear un nuevo producto | Body: `ProductoCreate` |
| `GET` | `/productos/` | Listar productos | `?limit=100&offset=0` |
| `GET` | `/productos/{id}` | Obtener producto por ID | Path: `id` |
| `PUT` | `/productos/{id}` | Actualizar producto | Path: `id`, Body: `ProductoUpdate` |
| `DELETE` | `/productos/{id}` | Eliminar producto | Path: `id` |

### 7.3 Pedidos (`/pedidos`)

| Método | Ruta | Descripción | Parámetros |
|--------|------|-------------|------------|
| `POST` | `/pedidos/` | Crear pedido + actualizar deuda del cliente | Body: `OrderCreateRequest` |
| `GET` | `/pedidos/` | Listar pedidos | `?limit=100&offset=0` |
| `GET` | `/pedidos/{id}` | Obtener pedido por ID | Path: `id` |
| `PUT` | `/pedidos/{id}` | Actualizar pedido | Path: `id`, Body: `PedidoUpdate` |
| `DELETE` | `/pedidos/{id}` | Eliminar pedido | Path: `id` |

### 7.4 Detalles de Pedido (`/detalles-pedido`)

| Método | Ruta | Descripción | Parámetros |
|--------|------|-------------|------------|
| `POST` | `/detalles-pedido/` | Crear detalle de pedido | Body: `DetallesPedidoCreate` |
| `GET` | `/detalles-pedido/` | Listar detalles | `?limit=100&offset=0` |
| `GET` | `/detalles-pedido/pedido/{pedido_id}` | Listar detalles por pedido | Path: `pedido_id` |
| `GET` | `/detalles-pedido/{id}` | Obtener detalle por ID | Path: `id` |
| `PUT` | `/detalles-pedido/{id}` | Actualizar detalle | Path: `id`, Body: `DetallesPedidoUpdate` |
| `DELETE` | `/detalles-pedido/{id}` | Eliminar detalle | Path: `id` |

### 7.5 Reportes (`/reports`)

| Método | Ruta | Descripción | Parámetros |
|--------|------|-------------|------------|
| `GET` | `/reports/financials` | Métricas globales: deuda total, cobrado, mora | — |
| `GET` | `/reports/earnings` | Ganancia neta en un período | `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` |

---

## 8. Modelos de Datos (Esquemas)

### 8.1 Backend — Pydantic (`domain/models.py`)

```python
# Cliente
class ClienteBase:      namecliente, deuda_del_cliente, estado
class ClienteCreate:    (hereda de ClienteBase)
class ClienteUpdate:    namecliente?, deuda_del_cliente?, estado?
class Cliente:          (hereda de ClienteBase) + id
class AbonoRequest:     monto: Decimal
class PaginatedClientes: items, page, limit, total_items, total_pages

# Producto
class ProductoBase:     nombreproducto, valordecompra, valordeventa
class ProductoCreate:   (hereda de ProductoBase)
class ProductoUpdate:   nombreproducto?, valordecompra?, valordeventa?
class Producto:         (hereda de ProductoBase) + id

# Pedido
class PedidoBase:       idcliente, estadopedido, fecha_pedido
class PedidoCreate:     (hereda de PedidoBase)
class PedidoUpdate:     idcliente?, estadopedido?, fecha_pedido?
class Pedido:           (hereda de PedidoBase) + id

# Detalle de Pedido
class DetallesPedidoBase:   id_pedido, id_producto, valor_del_pedido, cantidad_producto
class DetallesPedidoCreate: (hereda de DetallesPedidoBase)
class DetallesPedidoUpdate: id_pedido?, id_producto?, valor_del_pedido?, cantidad_producto?
class DetallesPedido:       (hereda de DetallesPedidoBase) + id

# Creación de Pedido Compuesta
class OrderItemCreate:      id_producto, cantidad_producto, valor_del_pedido
class OrderCreateRequest:   idcliente, items: List[OrderItemCreate]
class OrderCreateResponse:  pedido: Pedido, items: List[DetallesPedido]
```

### 8.2 Frontend — TypeScript (`types/index.ts`)

```typescript
// Cliente
Cliente               { id, namecliente, deuda_del_cliente, estado }
ClienteCreate         Omit<Cliente, 'id'>
ClienteUpdate         Partial<ClienteCreate>

// Producto
Producto              { id, nombreproducto, valordecompra, valordeventa }
ProductoCreate        Omit<Producto, 'id'>
ProductoUpdate        Partial<ProductoCreate>

// Pedido
Pedido                { id, idcliente, estadopedido, fecha_pedido }
PedidoUpdate          Partial<Omit<Pedido, 'id'>>

// DetallesPedido
DetallesPedido        { id, id_pedido, id_producto, valor_del_pedido, cantidad_producto }

// Solicitudes Compuestas
OrderItemCreate       { id_producto, cantidad_producto, valor_del_pedido }
OrderCreateRequest    { idcliente, items: OrderItemCreate[] }
OrderCreateResponse   { pedido: Pedido, items: DetallesPedido[] }

// Paginación
PaginatedResponse<T>  { items: T[], page, limit, total_items, total_pages }

// Abonos
AbonoRequest          { monto: number }
AbonoResponse         { status: 'success', mensaje: string, nueva_deuda: number, cliente: Cliente | null, ordenes_afectadas: OrdenAfectada[] }
OrdenAfectada         { id: number, estado_anterior: string, estado_nuevo: string }

// Reportes
ClienteStatement      { order_id, fecha_pedido, total, days_since_created, estado, overdue }
FinancialsReport      { total_outstanding_debt, total_overdue, total_collected }
EarningsReport        { net_profit, orders_count, total_sales, total_cost }
```

---

## 9. Reglas de Negocio y Lógica Financiera

### Regla 1: Gestión de Estados de Pedido y Abonos
* El campo `estadopedido` soporta estados tradicionales como `Pendiente`, `Entregado` y `Pagado`, además de la asignación dinámica para pagos parciales de tipo `"Abonado {monto}"` (ej. `"Abonado 40.00"`).
* Se maneja consistencia case-insensitive en la validación de pagos para prevenir desajustes operativos en reportes financieros.

### Regla 2: Lógica de Abonos (Distribución FIFO con Rollback Transaccional)
* Los abonos ingresados por los clientes no reducen el saldo de forma plana; el sistema distribuye el monto de manera automática entre los pedidos pendientes aplicando un criterio **FIFO** basado en `fecha_pedido` (ascendente) y `id` (ascendente).
* Esta lógica está implementada en el endpoint `POST /api/v1/clientes/{id}/abonar` dentro del caso de uso `ApplyPaymentUseCase` en `use_cases/apply_payment.py`.
* El algoritmo de distribución:
  1. Obtiene todos los pedidos del cliente ordenados por fecha e ID.
  2. Para cada pedido pendiente, calcula el saldo restante (total del pedido − monto ya abonado).
  3. Si el monto restante del abono cubre el saldo, marca el pedido como `"Pagado"`.
  4. Si no lo cubre, actualiza el estado a `"Abonado {nuevo_monto_cumulativo}"` (ej. `"Abonado 40.00"`) y termina.
  5. Al final, actualiza la deuda del cliente: `nueva_deuda = deuda_actual − monto_abonado`.

#### Rollback Transaccional (Saga Pattern)
* Dado que Supabase REST API no soporta transacciones cross-table nativas, el `ApplyPaymentUseCase` implementa un mecanismo de compensación manual tipo **Saga Pattern**:
  * Se rastrean todas las mutaciones exitosas en una lista `updated_orders: List[Tuple[int, str, str]]` (order_id, estado_anterior, estado_nuevo).
  * Se guarda la deuda original del cliente antes de modificarla.
  * Si **cualquier** operación falla durante el proceso, se ejecuta un rollback completo:
    * Las órdenes se restauran a su estado anterior en orden inverso.
    * La deuda del cliente se restaura a su valor original.
  * Cada operación de rollback tiene su propio try/except y logging por si falla, asegurando que el sistema se recupere incluso ante fallos secundarios.

#### Respuesta Enriquecida del Endpoint
* El endpoint `POST /api/v1/clientes/{id}/abonar` ahora devuelve un objeto JSON con los siguientes campos:

```json
{
  "status": "success",
  "mensaje": "Abono de $50000.00 procesado.",
  "nueva_deuda": 7500.0,
  "cliente": {
    "id": 1,
    "namecliente": "Eloina",
    "deuda_del_cliente": 7500.0,
    "estado": 1
  },
  "ordenes_afectadas": [
    { "id": 1, "estado_anterior": "Pendiente", "estado_nuevo": "Pagado" },
    { "id": 2, "estado_anterior": "Pendiente", "estado_nuevo": "Abonado 25000.00" }
  ]
}
```

* **`cliente`**: Objeto completo del cliente recién leído de Supabase después de la actualización (datos frescos).
* **`ordenes_afectadas`**: Array con los IDs de las órdenes modificadas, su estado anterior y su nuevo estado, permitiendo al frontend renderizar los cambios sin recalcular.

#### Sincronización Automática del Frontend
* Cuando el usuario realiza un abono desde la **Ventana 1 (Gestión de Clientes)**, el frontend ejecuta automáticamente:
  1. **`renderW1Table()`**: Refresca la tabla de clientes para mostrar la deuda actualizada.
  2. **`handleReportsLoadStatement()`**: Si el mismo cliente está seleccionado en la pestaña **Reportes → Consultar Cliente**, refresca automáticamente el estado de cuenta para reflejar los cambios de estado (ej. "Pendiente" → "Pagado") sin necesidad de recarga manual de la página.
* El modal de éxito de SweetAlert2 muestra un resumen visual de las órdenes afectadas con su transición de estados.

### Regla 3: Creación de Pedido con Rollback Transaccional
* Al crear un pedido mediante `POST /api/v1/pedidos/`, el `CreateOrderUseCase` ejecuta una secuencia atómica:
  1. Validar existencia del cliente.
  2. Insertar cabecera del pedido (estado inicial: `"Pendiente"`).
  3. Insertar líneas de detalle en `detalles_pedido`.
  4. Actualizar la deuda del cliente (`deuda_del_cliente += total_del_pedido`).
* Si ocurre un error en cualquier paso, el sistema ejecuta **rollbacks compensatorios** en orden inverso para mantener la integridad de los datos.

### Regla 4: Mora por Vencimiento (15 Días)
* Un pedido se considera **en mora (overdue)** si han transcurrido más de 15 días desde `fecha_pedido` y su estado no es `"Pagado"`.
* El cálculo se realiza en los casos de uso `GetClientStatementUseCase` y `GetFinancialsUseCase`.

---

## 10. Guía de Instalación y Despliegue Local

### Requisitos Previos:
* Python 3.10 o superior instalado.
* Node.js (v18 o superior) y npm instalados.

### 10.1 Configuración del Backend
1. Navegue al directorio del backend: `cd backend`
2. Cree y active el entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate # Linux/Mac
   ```
3. Instale dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure su archivo `.env` (use `.env.example` como plantilla):
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   HOST=0.0.0.0
   PORT=8000
   CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
   ```
5. Inicie el servidor:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
6. Acceda a la documentación interactiva en: `http://localhost:8000/docs`

### 10.2 Configuración del Frontend
1. Navegue al directorio del frontend: `cd frontend`
2. Instale paquetes:
   ```bash
   npm install
   ```
3. Inicie el entorno de desarrollo:
   ```bash
   npm run dev
   ```
4. Abra el navegador en la URL que indique Vite (por defecto `http://localhost:5173`).

---

## 11. Variables de Entorno (Backend)

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `SUPABASE_URL` | URL del proyecto Supabase (sin `/rest/v1/`) | — (requerida) |
| `SUPABASE_KEY` | Clave anónima o de servicio de Supabase | — (requerida) |
| `HOST` | Dirección de enlace del servidor FastAPI | `0.0.0.0` |
| `PORT` | Puerto del servidor FastAPI | `8000` |
| `CORS_ORIGINS` | Orígenes permitidos para CORS | `["http://localhost:5173", "http://127.0.0.1:5173"]` |

---

## 12. Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Backend Framework | FastAPI | ≥0.110.0 |
| Servidor ASGI | Uvicorn | ≥0.28.0 |
| Validación | Pydantic / Pydantic-Settings | ≥2.6.0 / ≥2.2.0 |
| Base de Datos | Supabase (PostgreSQL) | — |
| Cliente Supabase | supabase-py | ≥2.4.0 |
| Frontend Bundler | Vite | 5.x |
| Lenguaje Frontend | TypeScript | 5.x |
| Estilos | CSS vanilla (Sistema de diseño propio) | — |
| Notificaciones | SweetAlert2 | CDN v11 |