import {
  AbonoRequest,
  AbonoResponse,
  Cliente,
  ClienteCreate,
  ClienteStatement,
  ClienteUpdate,
  DetallesPedido,
  EarningsReport,
  FinancialsReport,
  OrderCreateRequest,
  OrderCreateResponse,
  Pedido,
  PedidoUpdate,
  PaginatedResponse,
  Producto,
  ProductoCreate,
  ProductoUpdate,
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorBody || response.statusText}`);
  }

  if (response.status === 204) {
    return null as unknown as T;
  }

  return response.json();
}

export const api = {
  clientes: {
    list: (page = 1, limit = 5) => request<PaginatedResponse<Cliente>>(`/clientes/?page=${page}&limit=${limit}`),
    get: (id: number) => request<Cliente>(`/clientes/${id}`),
    create: (data: ClienteCreate) => request<Cliente>('/clientes/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: ClienteUpdate) => request<Cliente>(`/clientes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(`/clientes/${id}`, { method: 'DELETE' }),
    statement: (id: number) => request<ClienteStatement[]>(`/clientes/${id}/statement`),
    abonar: (id: number, data: AbonoRequest) => request<AbonoResponse>(`/clientes/${id}/abonar`, { method: 'POST', body: JSON.stringify(data) }),
  },
  productos: {
    list: (limit = 100, offset = 0) => request<Producto[]>(`/productos/?limit=${limit}&offset=${offset}`),
    get: (id: number) => request<Producto>(`/productos/${id}`),
    create: (data: ProductoCreate) => request<Producto>('/productos/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: ProductoUpdate) => request<Producto>(`/productos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(`/productos/${id}`, { method: 'DELETE' }),
  },
  pedidos: {
    list: (limit = 100, offset = 0) => request<Pedido[]>(`/pedidos/?limit=${limit}&offset=${offset}`),
    get: (id: number) => request<Pedido>(`/pedidos/${id}`),
    create: (data: OrderCreateRequest) => request<OrderCreateResponse>('/pedidos/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: PedidoUpdate) => request<Pedido>(`/pedidos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(`/pedidos/${id}`, { method: 'DELETE' }),
  },
  detallesPedido: {
    list: (limit = 100, offset = 0) => request<DetallesPedido[]>(`/detalles-pedido/?limit=${limit}&offset=${offset}`),
    getByPedido: (pedidoId: number) => request<DetallesPedido[]>(`/detalles-pedido/pedido/${pedidoId}`),
    get: (id: number) => request<DetallesPedido>(`/detalles-pedido/${id}`),
    create: (data: Omit<DetallesPedido, 'id'>) => request<DetallesPedido>('/detalles-pedido/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Omit<DetallesPedido, 'id'>>) => request<DetallesPedido>(`/detalles-pedido/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(`/detalles-pedido/${id}`, { method: 'DELETE' }),
  },
  reports: {
    financials: () => request<FinancialsReport>('/reports/financials'),
    earnings: (startDate: string, endDate: string) => request<EarningsReport>(`/reports/earnings?start_date=${startDate}&end_date=${endDate}`),
  }
};
