# Frontend — Vite + TypeScript

## Estructura General

```
frontend/
├── index.html                        # SPA con 3 ventanas (Admin, POS, Reportes)
├── package.json                      # Dependencias: vite, typescript
├── tsconfig.json                     # Configuración de TypeScript
├── vite.config.ts                    # Configuración de Vite (host: true, port: 5173)
├── css/
│   └── style.css                     # Sistema de diseño (variables CSS, componentes, animaciones)
└── src/
    ├── main.ts                       # AppController: lógica completa de UI e interacción con API
    ├── services/
    │   └── api.ts                    # Cliente HTTP hacia http://localhost:8000/api/v1
    └── types/
        └── index.ts                  # Interfaces TypeScript sincronizadas con modelos Pydantic
```

---

## Comunicación con el Backend

El frontend se comunica con el backend exclusivamente a través del módulo `services/api.ts`, que expone un objeto `api` con métodos organizados por recurso:

```
api.clientes.list(page, limit)        → GET    /clientes/?page=&limit=
api.clientes.get(id)                  → GET    /clientes/{id}
api.clientes.create(data)             → POST   /clientes/
api.clientes.update(id, data)         → PUT    /clientes/{id}
api.clientes.delete(id)               → DELETE /clientes/{id}
api.clientes.statement(id)            → GET    /clientes/{id}/statement
api.clientes.abonar(id, data)         → POST   /clientes/{id}/abonar

api.productos.list(limit, offset)     → GET    /productos/?limit=&offset=
api.productos.get(id)                 → GET    /productos/{id}
api.productos.create(data)            → POST   /productos/
api.productos.update(id, data)        → PUT    /productos/{id}
api.productos.delete(id)              → DELETE /productos/{id}

api.pedidos.list(limit, offset)       → GET    /pedidos/?limit=&offset=
api.pedidos.get(id)                   → GET    /pedidos/{id}
api.pedidos.create(data)              → POST   /pedidos/
api.pedidos.update(id, data)          → PUT    /pedidos/{id}
api.pedidos.delete(id)                → DELETE /pedidos/{id}

api.detallesPedido.list(limit, offset)         → GET    /detalles-pedido/
api.detallesPedido.getByPedido(pedidoId)       → GET    /detalles-pedido/pedido/{pedido_id}
api.detallesPedido.get(id)                     → GET    /detalles-pedido/{id}
api.detallesPedido.create(data)                → POST   /detalles-pedido/
api.detallesPedido.update(id, data)            → PUT    /detalles-pedido/{id}
api.detallesPedido.delete(id)                  → DELETE /detalles-pedido/{id}

api.reports.financials()              → GET    /reports/financials
api.reports.earnings(start, end)      → GET    /reports/earnings?start_date=&end_date=
```

**Base URL:** `http://localhost:8000/api/v1`

---

## AppController (main.ts)

La clase `AppController` maneja toda la lógica de UI y se organiza en 3 ventanas (tabs):

### Ventana 1: Administración (Clientes / Productos)

| Sub-view | Función |
|:---|---|
| **Registro de Clientes** | Formulario para crear nuevos clientes (`POST /clientes/`) |
| **Registro de Productos** | Formulario para crear productos + tabla del catálogo (`POST /productos/`, `GET /productos/`) |
| **Administración de Clientes** | Tabla paginada con acciones: Abonar, Editar, Activar/Desactivar (`GET /clientes/`, `PUT /clientes/{id}`, `DELETE /clientes/{id}`) |

### Ventana 2: POS (Crear Pedido)

- Selector de cliente activo
- Filas dinámicas: selector de producto + cantidad (kg) + subtotal
- Botón "Confirmar y Guardar Pedido" → `POST /pedidos/`
- Validaciones: producto duplicado, cantidad > 0, cliente con deuda

### Ventana 3: Reportes

| Sub-view | Función |
|:---|---|
| **Consulta de Cliente** | Selector de cliente → estado de cuenta detallado (`GET /clientes/{id}/statement`) |
| **Métricas Globales** | Tarjetas: Cartera Pendiente, Balances en Mora, Total Cobrado (`GET /reports/financials`) |
| **Cálculo de Utilidades** | Selector de fechas → ganancia neta del período (`GET /reports/earnings`) |

---

## Tipos de Datos (TypeScript)

Las interfaces TypeScript en `types/index.ts` están sincronizadas 1:1 con los modelos Pydantic del backend:

```typescript
// Cliente
Cliente               { id, NameCliente, deuda_del_cliente, Estado }
ClienteCreate         Omit<Cliente, 'id'>
ClienteUpdate         Partial<ClienteCreate>

// Producto
Producto              { id, NombreProducto, ValorDeCompra, ValorDeVenta }
ProductoCreate        Omit<Producto, 'id'>
ProductoUpdate        Partial<ProductoCreate>

// Pedido
Pedido                { id, IDcliente, EstadoPedido, Fecha_pedido }
PedidoUpdate          Partial<Omit<Pedido, 'id'>>

// DetallesPedido
DetallesPedido        { id, id_pedido, id_producto, Valor_del_Pedido, cantidad_producto }

// Solicitudes Compuestas
OrderItemCreate       { id_producto, cantidad_producto, Valor_del_Pedido }
OrderCreateRequest    { IDcliente, items: OrderItemCreate[] }
OrderCreateResponse   { pedido: Pedido, items: DetallesPedido[] }

// Paginación
PaginatedResponse<T>  { items: T[], page, limit, total_items, total_pages }

// Abonos
AbonoRequest          { monto: number }
AbonoResponse         { status: 'success', mensaje: string, nueva_deuda: number }

// Reportes
ClienteStatement      { order_id, fecha_pedido, total, days_since_created, estado, overdue }
FinancialsReport      { total_outstanding_debt, total_overdue, total_collected }
EarningsReport        { net_profit, orders_count, total_sales, total_cost }
```

---

## Sistema de Diseño (CSS)

El archivo `css/style.css` implementa un sistema de diseño completo con variables CSS:

```css
:root {
  --bg-primary: #F4F6F9;
  --bg-secondary: #FFFFFF;
  --accent-meat: #C0392B;        /* Rojo carne premium */
  --accent-gold: #E67E22;         /* Naranja para mora */
  --accent-success: #27AE60;      /* Verde para pagado/activo */
  --text-primary: #2C3E50;
  --text-secondary: #5A738E;
  --border-color: #BDC3C7;
  --shadow-premium: 0 4px 16px rgba(189, 195, 199, 0.35);
}
```

Componentes incluidos: header, tarjetas métricas, paneles, tablas, badges, formularios, botones, filas dinámicas POS, tabs, animaciones.

---

## Notificaciones

El sistema utiliza **SweetAlert2** (cargado vía CDN en `index.html`):

```html
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
```

Usos: confirmaciones de creación, errores de red, edición de nombres, confirmación de eliminación, validación de abonos.

---

## Stack Tecnológico del Frontend

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Bundler | Vite | 5.x |
| Lenguaje | TypeScript | 5.x |
| Estilos | CSS vanilla (sistema de diseño propio) | — |
| Notificaciones | SweetAlert2 | CDN v11 |