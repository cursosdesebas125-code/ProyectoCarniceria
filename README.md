
# Sistema de Distribución de Carne a Plazos

Este proyecto implementa una plataforma full-stack modular para la gestión comercial y financiera de una empresa de distribución de carne al por mayor. El sistema destaca por su modelo de venta basado en créditos a plazos, facilitando el control de saldos y cuentas por cobrar bajo términos rigurosos de vencimiento.

---

## 1. Descripción del Negocio

El modelo de negocio está diseñado específicamente para la comercialización mayorista de productos cárnicos con un esquema de financiamiento flexible de **crédito a plazos de 15 días sin intereses**.

### Dinámica de Operaciones:
* **Venta Mayorista**: Distribución de cortes de carne procesados, pesados en kilogramos (soportando cantidades decimales, ej. 125.50 kg).
* **Crédito de 15 Días**: Cada pedido entregado a un cliente genera una cuenta por cobrar que vence exactamente 15 días después de la fecha de registro del pedido (`Fecha_pedido`).
* **Control de Saldos**: El sistema incrementa automáticamente la deuda del cliente (`Deuda_del_cliente`) al registrar un nuevo pedido en estado "Entregado".
* **Gestión de Riesgo (Mora)**: Si un pedido permanece sin pagar después del plazo establecido (15 días), se clasifica como saldo en mora, suspendiendo temporalmente la capacidad del cliente para realizar nuevos pedidos.

---

## 2. Arquitectura del Sistema (Clean Architecture)

El proyecto adopta los principios de **Clean Architecture** (Arquitectura Limpia) y la **Separación de Responsabilidades (SoC)**, asegurando que las reglas de negocio permanezcan desacopladas de los frameworks de entrega (FastAPI) y de los proveedores de bases de datos (Supabase).

### 2.1 Estructura del Backend (Python/FastAPI)

El backend está organizado en capas modulares que aíslan la lógica del negocio:

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── routers/        # Capa de Presentación: Controladores HTTP y endpoints REST
│   │       └── api.py          # Agregador de rutas de la API
│   ├── config/                 # Capa de Configuración: Carga de variables de entorno y CORS
│   ├── domain/
│   │   └── models.py           # Capa de Dominio: Esquemas de validación de datos (Pydantic)
│   ├── repositories/           # Capa de Acceso a Datos: Abstracción de persistencia (Supabase)
│   ├── use_cases/              # Capa de Aplicación: Casos de uso e interactores de negocio
│   └── main.py                 # Punto de entrada de la aplicación FastAPI
└── requirements.txt
```

* **Dominio (`domain/models.py`)**: Contiene las entidades puras y esquemas de validación sin dependencias externas.
* **Casos de Uso (`use_cases/`)**: Implementa la lógica empresarial pura (ej. `CreateOrderUseCase` y cálculos de reportes analíticos), abstrayendo las transacciones y la gestión de errores mediante operaciones de compensación (rollback).
* **Repositorios (`repositories/`)**: Implementan el patrón repositorio desacoplando el acceso a la base de datos (Supabase Client).
* **Controladores (`api/v1/routers/`)**: Rutas del framework FastAPI encargadas de recibir las peticiones HTTP e inyectar los repositorios correspondientes a los casos de uso.

### 2.2 Estructura del Frontend (HTML/CSS/TypeScript)

El frontend está diseñado de forma modular, modularizando la UI y los servicios de datos:

```
frontend/
├── css/
│   └── style.css               # Sistema de Diseño: Estilos premium responsivos y animaciones
├── src/
│   ├── services/
│   │   └── api.ts              # Capa de Servicios: Cliente Fetch para consumir la API REST
│   ├── types/
│   │   └── index.ts            # Capa de Tipos: Interfaces TypeScript compartidas
│   └── main.ts                 # Controlador UI: Gestor de estado del POS, tablas y vistas
├── index.html                  # Plantilla UI: Estructura semántica del Dashboard
└── package.json
```

---

## 3. Modelo de Base de Datos (Supabase)

El modelo de datos relacional mapea exactamente el esquema de la base de datos PostgreSQL en Supabase. Las tablas y sus relaciones se describen a continuación:

| Tabla | Columna | Tipo de Datos | Restricciones / Descripción |
| :--- | :--- | :--- | :--- |
| **clientes** | `id`<br>`NameCliente`<br>`Deuda_del_cliente`<br>`Estado` | int8 (PK)<br>varchar<br>numeric<br>int2 | Identificador único del cliente<br>Nombre o Razón Social<br>Saldo deudor acumulado del cliente<br>Estado comercial (1 = Activo, 0 = Inactivo) |
| **productos** | `id`<br>`NombreProducto`<br>`ValorDeCompra`<br>`ValorDeVenta` | int8 (PK)<br>varchar<br>numeric<br>numeric | Identificador único del corte de carne<br>Denominación comercial del producto<br>Costo de compra (por kg)<br>Precio mayorista de venta (por kg) |
| **pedidos** | `id`<br>`IDcliente`<br>`EstadoPedido`<br>`Fecha_pedido` | int8 (PK)<br>int8 (FK)<br>varchar<br>date | Identificador único de la transacción<br>Referencia a `clientes.id`<br>Estado actual (Pendiente, Entregado, Pagado)<br>Fecha automática del servidor al crear el pedido |
| **Detalles_Pedido** | `id`<br>`id_pedido`<br>`id_producto`<br>`Valor_del_Pedido`<br>`cantidad_producto` | int8 (PK)<br>int8 (FK)<br>int8 (FK)<br>numeric<br>numeric | Identificador de línea de detalle<br>Referencia a `pedidos.id` (Cascada)<br>Referencia a `productos.id`<br>Subtotal de la línea (Cantidad × Precio de Venta)<br>Cantidad de producto vendida (Kg, soporta decimales) |

### Relación Muchos a Muchos (Tabla Intermedia)
La tabla **`Detalles_Pedido`** actúa como la tabla de unión intermedia para resolver la relación de Muchos a Muchos entre **`pedidos`** y **`productos`**. Esto permite que un solo pedido contenga múltiples productos y cantidades, y que un producto forme parte de múltiples pedidos en el sistema.

---

## 4. Reglas de Negocio Automatizadas

El sistema implementa de manera estricta y transparente dos reglas de negocio centrales:

### Regla 1: Multi-productos y Cálculos Reactivos
* Un pedido puede conformar una lista de múltiples cortes de carne.
* Al construir el pedido en el POS, el frontend valida que no se añadan productos duplicados en la lista de items.
* El subtotal de cada línea de producto se calcula multiplicando de forma exacta la cantidad decimal (kg) por el `ValorDeVenta` del producto.
* El total neto del pedido se calcula reactivamente en el cliente mediante un sumador acumulado (reducer) y se envía en un payload JSON unificado al backend para su almacenamiento.

### Regla 2: Automatización de Fechas y Vencimiento a 15 Días
* El backend no confía en las fechas enviadas por el cliente web. Al ingresar una petición de orden, el caso de uso `CreateOrderUseCase` captura la fecha actual del servidor (`datetime.date.today()`) y la asigna al campo `Fecha_pedido`.
* En la lógica financiera y de consultas de estados de cuenta, los pedidos que tienen un estado distinto a "Pagado" (ej. "Pendiente" o "Entregado") y cuya fecha de creación es mayor a 15 días respecto a la fecha actual del sistema son clasificados automáticamente como **Saldos en Mora/Vencidos**.

---

## 5. Guía de Instalación y Despliegue Local

Siga los siguientes pasos para configurar y ejecutar el entorno de desarrollo local para el backend y el frontend:

### Requisitos Previos:
* Python 3.10 o superior instalado.
* Node.js (v18 o superior) y npm instalados.

### 5.1 Configuración del Backend

1. Navegue al directorio del backend:
   ```bash
   cd backend
   ```
2. Cree un entorno virtual de Python:
   ```bash
   python3 -m venv .venv
   ```
3. Active el entorno virtual:
   - **En Linux/macOS**:
     ```bash
     source .venv/bin/activate
     ```
   - **En Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
4. Instale las dependencias de Python:
   ```bash
   pip install -r requirements.txt
   ```
5. Cree el archivo de variables de entorno `.env` en base al archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```
6. Abra el archivo `.env` y configure sus credenciales de la API de Supabase:
   ```env
   SUPABASE_URL=https://tu-proyecto-supabase.supabase.co
   SUPABASE_KEY=tu-anon-key-de-supabase
   ```
7. Inicie el servidor de desarrollo uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```
   El backend estará disponible en `http://localhost:8000`. Puede ver la documentación interactiva de la API en `http://localhost:8000/docs`.

### 5.2 Configuración del Frontend

1. En una nueva terminal, navegue al directorio del frontend:
   ```bash
   cd frontend
   ```
2. Instale los paquetes y dependencias de node:
   ```bash
   npm install
   ```
3. Inicie el servidor de desarrollo local de Vite:
   ```bash
   npm run start
   ```
4. Abra su navegador en la dirección web indicada:
   ```text
   http://localhost:5173
   ```


