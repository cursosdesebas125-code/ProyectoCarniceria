/**
 * Represents a Client ('clientes' table)
 * Handles state and total outstanding debt (due to 15-day payment terms).
 */
export interface Cliente {
  id: number;
  NameCliente: string;
  Deuda_del_cliente: number; // numeric in Supabase
  Estado: number; // int2 in Supabase (e.g. 1 = Active, 0 = Inactive)
}

/**
 * Represents a Product ('productos' table)
 * Defines inventory prices (purchase and sale value).
 */
export interface Producto {
  id: number;
  NombreProducto: string;
  ValorDeCompra: number; // numeric in Supabase
  ValorDeVenta: number; // numeric in Supabase
}

/**
 * Represents an Order ('pedidos' table)
 * Holds transaction headers.
 */
export interface Pedido {
  id: number;
  IDcliente: number; // Foreign Key to 'clientes'
  EstadoPedido: string; // e.g., 'Pendiente', 'Entregado', 'Pagado'
  Fecha_pedido: string; // ISO date string (YYYY-MM-DD)
}

/**
 * Represents Order Details ('Detalles_Pedido' table)
 * Breaks down orders line-by-line (which products and how much was purchased).
 */
export interface DetallesPedido {
  id: number;
  id_pedido: number; // Foreign Key to 'pedidos'
  id_producto: number; // Foreign Key to 'productos'
  Valor_del_Pedido: number; // Total line cost (numeric)
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
  Valor_del_Pedido: number;
}

export interface OrderCreateRequest {
  IDcliente: number;
  items: OrderItemCreate[];
}

export interface OrderCreateResponse {
  pedido: Pedido;
  items: DetallesPedido[];
}
