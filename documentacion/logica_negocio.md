# Lógica de Negocio — Distribuidora de Carnes

## Descripción del Negocio

El modelo de negocio está diseñado para la comercialización mayorista de productos cárnicos con un esquema de **crédito a plazos de 15 días sin intereses**.

### Dinámica de Operaciones

- **Venta Mayorista**: Distribución de cortes de carne procesados, pesados en kilogramos (soporta cantidades decimales, ej. 125.50 kg).
- **Crédito de 15 Días**: Cada pedido genera una cuenta por cobrar que vence exactamente 15 días después de `Fecha_pedido`.
- **Control de Saldos**: El sistema incrementa la deuda del cliente (`deuda_del_cliente`) al registrar un nuevo pedido en estado "Pendiente".
- **Gestión de Riesgo (Mora)**: Pedidos sin pagar después de 15 días se clasifican como saldo en mora.

---

## Reglas de Negocio

### Regla 1: Gestión de Estados de Pedido y Abonos

El campo `EstadoPedido` soporta los siguientes estados:

| Estado | Descripción |
|:---|:---|
| `Pendiente` | Pedido recién creado, pendiente de entrega |
| `Entregado` | Pedido entregado al cliente |
| `Pagado` / `pagado` | Pedido completamente pagado (case-insensitive) |
| `Abonado {monto}` | Pago parcial aplicado (ej. `Abonado 40.00`) |

### Regla 2: Lógica de Abonos (Distribución FIFO)

Los abonos se distribuyen automáticamente entre los pedidos pendientes usando el método **FIFO** (First In, First Out):

1. Se obtienen todos los pedidos del cliente ordenados por `Fecha_pedido` (ascendente) y `id` (ascendente).
2. Para cada pedido pendiente:
   - Se calcula el saldo restante: `total_del_pedido − monto_ya_abonado`
   - Si el monto del abono cubre el saldo → se marca como `"Pagado"`.
   - Si no lo cubre → se actualiza el estado a `"Abonado {nuevo_monto}"` y termina.
3. Se actualiza la deuda del cliente: `nueva_deuda = deuda_actual − monto_abonado`.

Implementado en: `ApplyPaymentUseCase` (`backend/app/use_cases/apply_payment.py`)

### Regla 3: Creación de Pedido con Rollback Transaccional

Al crear un pedido, se ejecuta una secuencia atómica:

1. Validar existencia del cliente.
2. Insertar cabecera del pedido (estado: `"Pendiente"`).
3. Insertar líneas de detalle en `Detalles_Pedido`.
4. Actualizar la deuda del cliente (`deuda_del_cliente += total_del_pedido`).

Si ocurre un error, se ejecutan **rollbacks compensatorios** en orden inverso.

Implementado en: `CreateOrderUseCase` (`backend/app/use_cases/create_order.py`)

### Regla 4: Mora por Vencimiento (15 Días)

Un pedido se considera **en mora (overdue)** si:
- Han transcurrido más de 15 días desde `Fecha_pedido`.
- Su estado NO es `"Pagado"`.

Implementado en: `GetClientStatementUseCase` y `GetFinancialsUseCase`

---

## Flujo de Operaciones del Sistema

```
Cliente nuevo → POST /api/v1/clientes/ (registro)
     ↓
Producto nuevo → POST /api/v1/productos/ (catálogo)
     ↓
Pedido nuevo → POST /api/v1/pedidos/ (con items)
     ├── Crea cabecera en Pedidos
     ├── Crea líneas en Detalles_Pedido
     └── Actualiza deuda_del_cliente (+)
     ↓
Abono (pago) → POST /api/v1/clientes/{id}/abonar
     ├── Distribuye FIFO entre pedidos pendientes
     └── Actualiza deuda_del_cliente (−)
     ↓
Reportes → GET /api/v1/reports/financials
         → GET /api/v1/reports/earnings?start_date=&end_date=
```

---

## Requisitos del Sistema

### Backend
- Python 3.10+
- FastAPI ≥0.110.0
- Supabase (PostgreSQL) como base de datos
- Cuenta de Supabase con las tablas: `clientes`, `Productos`, `Pedidos`, `Detalles_Pedido`

### Frontend
- Node.js v18+
- Navegador moderno (Chrome, Firefox, Edge)
- SweetAlert2 (cargado vía CDN)