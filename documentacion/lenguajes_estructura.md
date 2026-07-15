# Lenguajes de Programación — Estructura y Uso en el Proyecto

## Visión General

El proyecto **Distribuidora de Carnes** utiliza **4 lenguajes de programación** organizados en dos entornos claramente separados: backend (Python) y frontend (TypeScript, HTML, CSS). Cada lenguaje cumple un rol específico dentro de la arquitectura Clean Architecture del sistema.

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                              │
│  TypeScript (lógica) + HTML (estructura) + CSS (estilos) │
│  ┌──────────┬──────────────┬────────────┐               │
│  │ main.ts  │  index.html  │ style.css  │               │
│  │ (clase)  │  (SPA)       │ (variables)│               │
│  └────┬─────┴──────┬───────┴─────┬──────┘               │
│       │            │             │                       │
│       ▼            ▼             ▼                       │
│  services/api.ts  types/index.ts                        │
│  (fetch HTTP)     (interfaces)                          │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (JSON)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    BACKEND                               │
│  Python (lógica + API + datos)                          │
│  ┌──────────┬──────────────┬──────────────┐             │
│  │ Routers  │  Use Cases   │ Repositories │             │
│  │ (FastAPI)│  (negocio)   │ (Supabase)   │             │
│  └──────────┴──────────────┴──────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Python (Backend)

### Rol
Lenguaje principal del backend. Se encarga de:
- Exponer la API REST mediante FastAPI
- Validar datos de entrada/salida con Pydantic
- Ejecutar la lógica de negocio (casos de uso)
- Persistir y consultar datos en Supabase

### Versión
Python ≥ 3.10 (inferido por el uso de `type[T]` y `dict[str, Any]` en el código).

### Estructura de Archivos

```
backend/
├── requirements.txt          # Dependencias (pip)
├── .env.example              # Variables de entorno
└── app/
    ├── main.py               # Bootstrap: crea la app FastAPI
    ├── config/
    │   └── settings.py       # Config tipada con Pydantic
    ├── domain/
    │   └── models.py         # Modelos Pydantic (DTOs)
    ├── repositories/
    │   ├── base.py           # Clase base abstracta + CRUD genérico
    │   ├── supabase_client.py# Cliente singleton de Supabase
    │   ├── clientes.py       # CRUD específico de clientes
    │   ├── productos.py      # CRUD específico de productos
    │   ├── pedidos.py        # CRUD específico de pedidos
    │   └── detalles_pedido.py# CRUD específico de detalles
    ├── use_cases/
    │   ├── apply_payment.py  # Lógica FIFO de abonos
    │   ├── create_order.py   # Creación de pedidos con rollback
    │   └── reporting.py      # Reportes financieros
    └── api/v1/
        ├── api.py            # Agregador de rutas
        └── routers/
            ├── clientes.py   # Endpoints de clientes
            ├── productos.py  # Endpoints de productos
            ├── pedidos.py    # Endpoints de pedidos
            ├── detalles_pedido.py  # Endpoints de detalles
            └── reports.py    # Endpoints de reportes
```

### Características de Python usadas

| Característica | Uso en el proyecto | Ejemplo |
|:---|---|:---|
| **Tipado estático** | Type hints en todas las funciones | `async def get_by_id(self, entity_id: int) -> Optional[T]:` |
| **Genéricos** | Repositorio base parametrizado | `BaseSupabaseRepository[T, CreateSchema, UpdateSchema]` |
| **Clases abstractas** | Interfaz de repositorio | `class BaseRepository(ABC, Generic[...])` |
| **Decoradores** | Rutas FastAPI, inyección de dependencias | `@router.get("/")`, `@router.post("/")` |
| **Async/Await** | Operaciones asíncronas con Supabase | `async def create(self, schema: CreateSchema) -> T:` |
| **Pydantic** | Validación de datos y serialización | `class ClienteBase(BaseModel):` |
| **Dataclasses** | Modelos de datos inmutables | `model_config = {"from_attributes": True}` |
| **Módulo logging** | Registro de eventos | `logger = logging.getLogger(__name__)` |
| **Módulo decimal** | Precisión financiera | `from decimal import Decimal` |
| **Módulo datetime** | Fechas de pedidos | `from datetime import date` |

### Convenciones de código Python

- **Nombres de clases**: PascalCase (`ClientesRepository`, `ApplyPaymentUseCase`)
- **Nombres de funciones/variables**: snake_case (`get_by_id`, `list_paginated`)
- **Nombres de constantes**: UPPER_SNAKE_CASE (`SUPABASE_URL`, `SUPABASE_KEY`)
- **Archivos**: snake_case (`clientes.py`, `apply_payment.py`)
- **Documentación**: Docstrings con triple comilla `"""..."""`

---

## 2. TypeScript (Frontend)

### Rol
Lenguaje principal del frontend. Se encarga de:
- Definir la estructura de datos (interfaces)
- Comunicarse con el backend mediante HTTP (fetch)
- Manejar la lógica de la interfaz de usuario (AppController)
- Renderizar dinámicamente el DOM

### Versión
TypeScript 5.2.2 (especificado en `package.json`). Compila a ES2020.

### Estructura de Archivos

```
frontend/
├── tsconfig.json              # Configuración del compilador
├── vite.config.ts             # Configuración del bundler
├── index.html                 # Punto de entrada HTML
├── css/
│   └── style.css              # Estilos globales
└── src/
    ├── main.ts                # AppController (clase principal)
    ├── services/
    │   └── api.ts             # Cliente HTTP
    └── types/
        └── index.ts           # Interfaces de datos
```

### Características de TypeScript usadas

| Característica | Uso en el proyecto | Ejemplo |
|:---|---|:---|
| **Interfaces** | Definición de tipos de datos | `interface Cliente { id: number; NameCliente: string; }` |
| **Type Aliases** | Tipos literales y uniones | `type ClienteEstado = 0 \| 1;` |
| **Template Literal Types** | Estados dinámicos de pedido | `` type PedidoEstado = `Abonado ${number}`; `` |
| **Clases** | AppController con métodos privados | `class AppController { private w1CurrentPage = 1; }` |
| **Async/Await** | Llamadas asíncronas a la API | `const res = await api.clientes.list(1, 5);` |
| **Genéricos** | Cliente HTTP parametrizado | `async function request<T>(path: string): Promise<T>` |
| **Módulos ES** | Import/export nativos | `import { api } from './services/api';` |
| **Tipado estricto** | Validación en tiempo de compilación | `"strict": true` en tsconfig.json |
| **DOM API** | Manipulación del árbol HTML | `document.getElementById('w1-table-body')!;` |

### Convenciones de código TypeScript

- **Nombres de interfaces**: PascalCase (`Cliente`, `OrderCreateRequest`)
- **Nombres de clases**: PascalCase (`AppController`)
- **Nombres de métodos/funciones**: camelCase (`renderW1Table`, `handlePOSSubmitOrder`)
- **Nombres de variables**: camelCase (`w1CurrentPage`, `posAvailableProducts`)
- **Archivos**: snake_case (`main.ts`, `api.ts`, `index.ts`)
- **Tipado explícito**: Siempre se declaran los tipos de retorno y parámetros

### Flujo de ejecución del frontend

```
1. index.html carga
2. <script type="module" src="/src/main.ts"> se ejecuta
3. main.ts: DOMContentLoaded → new AppController()
4. AppController.initEvents() registra todos los event listeners
5. AppController.checkConnectivityAndLoad() → api.clientes.list()
6. Usuario interactúa → eventos → llamadas API → renderizado DOM
```

---

## 3. HTML (Frontend)

### Rol
Lenguaje de marcado para la estructura de la interfaz de usuario. Define:
- La SPA (Single Page Application) con 3 ventanas principales
- Los formularios, tablas y selectores
- La carga de recursos externos (CDN, CSS, TypeScript)

### Versión
HTML5 (`<!DOCTYPE html>`)

### Estructura del Documento

```html
index.html
├── <head>
│   ├── <meta charset="UTF-8">
│   ├── <meta name="viewport" content="width=device-width">
│   ├── <title>Panel de Control</title>
│   ├── <script src="sweetalert2@11"></script>  ← CDN
│   └── <link rel="stylesheet" href="/css/style.css">
├── <body>
│   ├── <header>  ← Logo + título
│   ├── <main class="container">
│   │   ├── <div class="tabs-container">  ← 3 botones de navegación
│   │   ├── <div id="view-window1">  ← Administración
│   │   │   ├── Registro de Clientes (form)
│   │   │   ├── Registro de Productos (form + tabla)
│   │   │   └── Administración de Clientes (tabla + paginación)
│   │   ├── <div id="view-window2">  ← POS
│   │   │   ├── Selector de cliente
│   │   │   └── Filas dinámicas de productos
│   │   └── <div id="view-window3">  ← Reportes
│   │       ├── Consulta de Cliente (selector + tabla)
│   │       └── Métricas Globales (tarjetas + calculadora)
│   └── <script type="module" src="/src/main.ts">
```

### Características de HTML usadas

| Característica | Uso |
|:---|---|
| **Semántica HTML5** | `<header>`, `<main>`, `<section>` |
| **Formularios** | `<form>`, `<input>`, `<select>`, `<button>` |
| **Tablas** | `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` |
| **Atributos data** | `id` para enlazar con TypeScript |
| **CDN externo** | SweetAlert2 vía `<script src="...">` |
| **Módulos ES** | `<script type="module" src="/src/main.ts">` |

---

## 4. CSS (Frontend)

### Rol
Lenguaje de estilos para la presentación visual. Implementa:
- Un sistema de diseño completo con variables CSS
- Componentes reutilizables (botones, tarjetas, tablas, badges)
- Animaciones y transiciones
- Diseño responsive con CSS Grid

### Versión
CSS3 con características modernas (variables, grid, flexbox, animaciones).

### Estructura del Archivo

```
css/style.css (492 líneas)
├── 1. Import de fuente (Google Fonts: Inter)
├── 2. Variables CSS (sistema de diseño)
│   ├── Colores: --accent-meat, --accent-gold, --accent-success
│   ├── Texto: --text-primary, --text-secondary, --text-muted
│   ├── Bordes: --border-color, --border-radius-*
│   └── Sombras: --shadow-premium
├── 3. Estilos base (body, *, box-sizing)
├── 4. Header y layout
├── 5. Tarjetas métricas (metrics-grid, metric-card)
├── 6. Paneles y layout del dashboard
├── 7. Tablas (table, th, td, tr:hover)
├── 8. Badges (active, inactive, pending, completed)
├── 9. Botones (btn, btn-secondary, btn-success)
├── 10. Formularios (form-group, form-control)
├── 11. POS dinámico (pos-row-item, pos-row-subtotal)
├── 12. Tabs (tabs-container, tab-btn, tab-btn.active)
└── 13. Animaciones (@keyframes fadeIn, .fade-in)
```

### Características de CSS usadas

| Característica | Uso | Ejemplo |
|:---|---|:---|
| **Variables CSS** | Sistema de diseño centralizado | `--accent-meat: #C0392B;` |
| **CSS Grid** | Layout de paneles y métricas | `grid-template-columns: 1fr 1.5fr;` |
| **Flexbox** | Alineación de elementos | `display: flex; justify-content: space-between;` |
| **Transiciones** | Efectos hover suaves | `transition: all 0.2s ease-in-out;` |
| **Animaciones** | Entrada de elementos | `@keyframes fadeIn { from { opacity: 0; } }` |
| **Pseudo-clases** | Estados interactivos | `:hover`, `:focus`, `:disabled` |
| **Selectores anidados** | Estilos contextuales | `tr:hover td { background-color: ...; }` |
| **Google Fonts** | Tipografía Inter | `@import url('https://fonts.googleapis.com/...');` |

---

## 5. Interacción entre Lenguajes

### Flujo de Datos Completo

```
USUARIO (navegador)
    │
    ▼
┌─────────────────────────────────────────────────┐
│ HTML (index.html)                                │
│  → Renderiza la estructura visual                │
│  → Carga CSS para estilos                        │
│  → Ejecuta TypeScript (main.ts)                  │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ TypeScript (main.ts + api.ts)                    │
│  → AppController maneja eventos del DOM          │
│  → Construye payload JSON                        │
│  → Envía HTTP request (fetch)                    │
│  → Recibe respuesta JSON                         │
│  → Actualiza el DOM dinámicamente                │
└─────────────────────┬───────────────────────────┘
                      │ HTTP (JSON)
                      ▼
┌─────────────────────────────────────────────────┐
│ Python (FastAPI)                                 │
│  → Router recibe request HTTP                    │
│  → Pydantic valida el payload                    │
│  → UseCase ejecuta lógica de negocio             │
│  → Repository persiste/consulta en Supabase      │
│  → Retorna respuesta JSON                        │
└─────────────────────────────────────────────────┘
```

### Formato de Intercambio: JSON

Todos los lenguajes se comunican mediante **JSON** (JavaScript Object Notation):

```json
// Ejemplo: Crear cliente (TypeScript → Python)
// TypeScript envía:
POST /api/v1/clientes/
Body: {"NameCliente": "Distribuidora Gómez", "deuda_del_cliente": 0, "Estado": 1}

// Python recibe, procesa y responde:
201 Created
Body: {"id": 1, "NameCliente": "Distribuidora Gómez", "deuda_del_cliente": 0.0, "Estado": 1}
```

### Mapeo de Tipos entre Lenguajes

| Concepto | Python (Pydantic) | TypeScript | JSON | Supabase (PostgreSQL) |
|:---|---:|:---:|:---:|:---:|
| Entero | `int` | `number` | `1` | `int8`, `int2` |
| Decimal | `Decimal` | `number` | `0.00` | `numeric` |
| Texto | `str` | `string` | `"texto"` | `varchar` |
| Fecha | `date` | `string` (ISO) | `"2026-07-14"` | `date` |
| Booleano | `int` (0/1) | `0 \| 1` | `1` | `int2` |
| Lista | `List[T]` | `T[]` | `[...]` | — (relacional) |
| Opcional | `Optional[T]` | `T \| undefined` | `null` o ausente | `NULL` |

---

## 6. Resumen por Lenguaje

| Lenguaje | Versión | Archivos | Líneas Total | Rol Principal |
|:---|---:|:---:|:---:|:---|
| **Python** | ≥3.10 | 15 archivos `.py` | ~1,100 | API REST, lógica de negocio, persistencia |
| **TypeScript** | 5.2.2 | 3 archivos `.ts` | ~1,100 | Lógica de UI, comunicación HTTP, tipos |
| **HTML** | HTML5 | 1 archivo `.html` | 301 | Estructura visual de la SPA |
| **CSS** | CSS3 | 1 archivo `.css` | 492 | Sistema de diseño y estilos visuales |