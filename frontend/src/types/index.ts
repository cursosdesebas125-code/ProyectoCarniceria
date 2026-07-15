/**
 * Represents a Client ('clientes' table)
 * Handles state and total outstanding debt (due to 15-day payment terms).
 */
export type ClienteEstado = 0 | 1;
export type PedidoEstado = 'Pendiente' | 'Entregado' | 'Pagado' | 'pagado' | `Abonado ${number}`;

export interface Cliente {
  id: number;
  namecliente: string;
  deuda_del_cliente: number; // numeric in Supabase
  estado: ClienteEstado; // int2 in Supabase (1 = Active, 0 = Inactive)
}

export type ClienteCreate = Omit<Cliente, 'id'>;
export type ClienteUpdate = Partial<ClienteCreate>;

/**
 * Represents a Product ('productos' table)
 * Defines inventory prices (purchase and sale value).
 */
export interface Producto {
  id: number;
  nombreproducto: string;
  valordecompra: number; // numeric in Supabase
  valordeventa: number; // numeric in Supabase
}

export type ProductoCreate = Omit<Producto, 'id'>;
export type ProductoUpdate = Partial<ProductoCreate>;

/**
 * Represents an Order ('pedidos' table)
 * Holds transaction headers.
 */
export interface Pedido {
  id: number;
  idcliente: number; // Foreign Key to 'clientes'
  estadopedido: PedidoEstado;
  fecha_pedido: string; // ISO date string (YYYY-MM-DD)
}

export type PedidoUpdate = Partial<Omit<Pedido, 'id'>>;

/**
 * Represents Order Details ('detalles_pedido' table)
 * Breaks down orders line-by-line (which products and how much was purchased).
 */
export interface DetallesPedido {
  id: number;
  id_pedido: number; // Foreign Key to 'pedidos'
  id_producto: number; // Foreign Key to 'productos'
  valor_del_pedido: number; // Total line cost (numeric)
  cantidad_producto: number; // Decimal quantity (can represent kilograms or fractional cases)
}

/**
 * Standard paginated response structure from the API
 */
export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  limit: number;
  total_items: number;
  total_pages: number;
}

export interface OrderItemCreate {
  id_producto: number;
  cantidad_producto: number;
  valor_del_pedido: number;
}

export interface OrderCreateRequest {
  idcliente: number;
  items: OrderItemCreate[];
}

export interface OrderCreateResponse {
  pedido: Pedido;
  items: DetallesPedido[];
}

/** Response emitted by the current /api/v1/pedidos/ endpoint. */
export interface PedidoSubmissionResponse {
  status: 'success';
  pedido_id: number;
}

export interface AbonoRequest {
  monto: number;
}

export interface OrdenAfectada {
  id: number;
  estado_anterior: string;
  estado_nuevo: string;
}

export interface AbonoResponse {
  status: 'success';
  mensaje: string;
  nueva_deuda: number;
  cliente: Cliente | null;
  ordenes_afectadas: OrdenAfectada[];
}

export interface ClienteStatement {
  order_id: number;
  fecha_pedido: string;
  total: number;
  days_since_created: number;
  estado: PedidoEstado;
  overdue: boolean;
}

export interface FinancialsReport {
  total_outstanding_debt: number;
  total_overdue: number;
  total_collected: number;
}

export interface EarningsReport {
  net_profit: number;
  orders_count: number;
  total_sales: number;
  total_cost: number;
}