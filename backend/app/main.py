from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# ✨ Cargamos las variables de entorno desde el archivo .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validación opcional para asegurarte de que las variables existan
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Faltan las variables de entorno de Supabase en el archivo .env")

print("==========================================")
print(f"--> CONECTANDO A SUPABASE DESDE .ENV")
print("==========================================")

# Conectar con Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="API Distribuidora de Carnes",
    version="1.0.0",
    docs_url="/docs"
)


# 2. CONFIGURACIÓN DE CORS REFORZADA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# --- MODELOS PYDANTIC ---
class ClienteCreate(BaseModel):
    NameCliente: str

class ProductoCreate(BaseModel):
    NombreProducto: str
    ValorDeCompra: float
    ValorDeVenta: float

class AbonoPayload(BaseModel):
    monto: float  


# ================= TABLA: clientes =================

@app.get("/api/v1/clientes/")
@app.get("/clientes/")
def obtener_clientes(page: Optional[int] = 1, limit: Optional[int] = 1000):
    try:
        print(f"--> [URL] Catálogo de clientes solicitado. Página: {page}, Límite: {limit}")
        response = supabase.schema("public").table("clientes").select("*").execute()
        
        clientes_reales = []
        if response.data:
            for c in response.data:
                clientes_reales.append({
                    "id": c.get("id"),
                    "NameCliente": c.get("NameCliente") or "Sin Nombre",
                    "Deuda_del_cliente": float(c.get("Deuda_del_cliente") or 0.0),
                    "Estado": int(c.get("Estado") or 1)
                })
        
        total_items = len(clientes_reales)
        total_pages = max(1, (total_items + limit - 1) // limit)
        
        # Paginación manual para respetar el frontend original
        inicio = (page - 1) * limit
        fin = inicio + limit
        items_paginados = clientes_reales[inicio:fin]
        
        return {
            "items": items_paginados,
            "total_items": total_items,
            "total_pages": total_pages
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

 

@app.post("/api/v1/clientes/", status_code=status.HTTP_201_CREATED)
@app.post("/clientes/", status_code=status.HTTP_201_CREATED)
def crear_cliente(payload: ClienteCreate):
    try:
        data = {
            "NameCliente": payload.NameCliente,
            "Deuda_del_cliente": 0,
            "Estado": 1
        }
        response = supabase.schema("public").table("clientes").insert(data).execute()
        return {"status": "ok", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear cliente: {str(e)}")

@app.post("/api/v1/clientes/{cliente_id}/abonar")
@app.post("/clientes/{cliente_id}/abonar")
def abonar_deuda(cliente_id: int, payload: AbonoPayload):
    try:
        print(f"--> [ABONO] Procesando abono para el cliente ID: {cliente_id}")
        monto_abono = float(payload.monto)
        if monto_abono <= 0:
            raise HTTPException(status_code=400, detail="El monto del abono debe ser mayor a cero.")
        
        # 1. Buscar el cliente actual forzando el esquema público
        res_cliente = supabase.schema("public").table("clientes").select("Deuda_del_cliente").eq("id", int(cliente_id)).execute()
        if not res_cliente.data:
            raise HTTPException(status_code=404, detail="Cliente no encontrado.")
            
        deuda_actual = float(res_cliente.data[0]["Deuda_del_cliente"] or 0.0)
        
        # Validation step: The payment amount cannot exceed the customer's total debt
        if monto_abono > deuda_actual:
            raise HTTPException(
                status_code=400, 
                detail="The payment amount cannot exceed the customer's total debt"
            )
            
        # 2. Get customer's pending orders (EstadoPedido is not 'pagado' or 'Pagado')
        res_pedidos = supabase.schema("public").table("Pedidos").select("*").eq("IDcliente", int(cliente_id)).execute()
        
        pending_orders = []
        if res_pedidos.data:
            for p in res_pedidos.data:
                estado = (p.get("EstadoPedido") or "").lower()
                if estado != "pagado":
                    pending_orders.append(p)
                    
        # Sort pending orders by Fecha_pedido ascending, then by ID ascending
        pending_orders.sort(key=lambda x: (x.get("Fecha_pedido") or "", x.get("id") or 0))
        
        monto_restante = monto_abono
        
        # 3. Distribute payment among pending orders
        for order in pending_orders:
            if monto_restante <= 0:
                break
                
            order_id = order.get("id")
            estado_actual = order.get("EstadoPedido") or ""
            
            # Fetch order details to sum the total value of the order
            res_details = supabase.schema("public").table("Detalles_Pedido").select("Valor_del_Pedido").eq("id_pedido", order_id).execute()
            order_total = 0.0
            if res_details.data:
                order_total = sum(float(d.get("Valor_del_Pedido") or 0.0) for d in res_details.data)
                
            # Parse already paid amount if the status reflects a partial balance, e.g., "Abonado 40.0"
            already_paid = 0.0
            if estado_actual.lower().startswith("abonado "):
                try:
                    already_paid = float(estado_actual.split(" ")[1])
                except Exception:
                    already_paid = 0.0
                    
            remaining_to_pay = max(0.0, order_total - already_paid)
            if remaining_to_pay <= 0:
                continue
                
            if monto_restante >= remaining_to_pay:
                # Fully paid
                monto_restante -= remaining_to_pay
                supabase.schema("public").table("Pedidos").update({"EstadoPedido": "pagado"}).eq("id", order_id).execute()
                print(f"--> Pedido #{order_id} pagado completamente.")
            else:
                # Partially paid
                new_already_paid = already_paid + monto_restante
                supabase.schema("public").table("Pedidos").update({"EstadoPedido": f"Abonado {new_already_paid:.2f}"}).eq("id", order_id).execute()
                print(f"--> Pedido #{order_id} abonado con ${monto_restante}. Total abonado: ${new_already_paid:.2f}")
                monto_restante = 0.0
                break
                
        # 4. Update the new debt in table 'clientes'
        nueva_deuda = max(0.0, deuda_actual - monto_abono)
        supabase.schema("public").table("clientes").update({"Deuda_del_cliente": nueva_deuda}).eq("id", int(cliente_id)).execute()
        print(f"--> [ÉXITO] Abono de ${monto_abono} aplicado. Nueva deuda para cliente {cliente_id}: ${nueva_deuda}")
        
        return {
            "status": "success",
            "mensaje": f"Abono de ${monto_abono} procesado.",
            "nueva_deuda": nueva_deuda
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print("❌ ERROR CRÍTICO AL ABONAR:")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# ================= TABLA: Productos =================

@app.get("/api/v1/productos/")
@app.get("/productos/")
def obtener_productos(limit: int = 1000, offset: int = 0):
    try:
        # Imprime en la terminal de Ubuntu para ver cuándo y cómo llama el frontend
        print(f"--> https://dictionary.cambridge.org/dictionary/spanish-english/espia El catálogo solicitó productos. Parámetros -> limit: {limit}, offset: {offset}")
        
        response = supabase.schema("public").table("Productos").select("*").execute()
        
        productos_reales = []
        if response.data:
            for p in response.data:
                # Única y estrictamente tus variables reales de la imagen
                productos_reales.append({
                    "id": p.get("id"),
                    "NombreProducto": p.get("NombreProducto"),
                    "ValorDeCompra": float(p.get("ValorDeCompra") or 0.0),
                    "ValorDeVenta": float(p.get("ValorDeVenta") or 0.0)
                })
        
        return productos_reales

    except Exception as e:
        print("❌ ERROR REAL EN TABLA PRODUCTOS:")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/api/v1/productos/", status_code=status.HTTP_201_CREATED)
@app.post("/productos/", status_code=status.HTTP_201_CREATED)
def crear_producto(payload: ProductoCreate):
    try:
        data = {
            "NombreProducto": payload.NombreProducto,
            "ValorDeCompra": payload.ValorDeCompra,
            "ValorDeVenta": payload.ValorDeVenta
        }
        response = supabase.schema("public").table("Productos").insert(data).execute()
        return {"status": "ok", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/v1/productos/{producto_id}")
@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int):
    try:
        supabase.schema("public").table("Productos").delete().eq("id", producto_id).execute()
        print(f"--> Producto con ID {producto_id} eliminado exitosamente.")
        return {"status": "ok", "message": "Producto eliminado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ================= TABLA: Pedidos & Detalles =================

@app.post("/api/v1/pedidos/")
@app.post("/pedidos/")
def crear_pedido(pedido: dict):
    try:
        print("--> [POS] Procesando solicitud con base en el esquema real de Supabase...")
        
        # 1. Extraer los datos enviados por el frontend
        id_cliente = pedido.get("IDcliente")
        items = pedido.get("items") or []
        
        if not id_cliente:
            raise HTTPException(status_code=400, detail="Falta el ID del cliente.")
        if not items:
            raise HTTPException(status_code=400, detail="El pedido no contiene productos.")

        # 2. INSERTAR EN LA CABECERA (Tabla: Pedidos)
        datos_cabecera = {
            "IDcliente": int(id_cliente)
        }
        
        res_pedido = supabase.schema("public").table("Pedidos").insert(datos_cabecera).execute()
        
        if not res_pedido.data:
            raise HTTPException(status_code=400, detail="No se pudo registrar la cabecera en la tabla Pedidos.")
        
        # Recuperamos el ID que generó la tabla Pedidos
        nuevo_pedido_id = res_pedido.data[0].get("id")
        print(f"--> [CABECERA] Registro en 'Pedidos' exitoso. ID de Pedido generado: #{nuevo_pedido_id}")

        total_acumulado_pedido = 0.0

        # 3. INSERTAR EN LOS DETALLES (Tabla: Detalles_Pedido)
        for item in items:
            subtotal_item = float(item.get("Valor_del_Pedido") or 0.0)
            total_acumulado_pedido += subtotal_item

            datos_detalle = {
                "id_pedido": int(nuevo_pedido_id),
                "id_producto": int(item.get("id_producto") if item.get("id_producto") is not None else 0),
                "Valor_del_Pedido": float(subtotal_item),
                "cantidad_producto": float(item.get("cantidad_producto") or 0.0)
            }
            
            print(f"--> [DEBUG DETALLE] Insertando en Detalles_Pedido: {datos_detalle}")
            supabase.schema("public").table("Detalles_Pedido").insert(datos_detalle).execute()

        # 4. ACTUALIZAR DEUDA EN LA TABLA CLIENTES (Tabla: clientes)
        # Aseguramos int(id_cliente) en los filtros para evitar cualquier incompatibilidad de tipos
        res_cliente = supabase.schema("public").table("clientes").select("Deuda_del_cliente").eq("id", int(id_cliente)).single().execute()
        deuda_actual = float(res_cliente.data.get("Deuda_del_cliente") or 0.0) if res_cliente.data else 0.0
        nueva_deuda = deuda_actual + total_acumulado_pedido
        
        supabase.schema("public").table("clientes").update({"Deuda_del_cliente": nueva_deuda}).eq("id", int(id_cliente)).execute()
        print(f"--> [AUTOMÁTICO] Tabla 'clientes' actualizada. Nueva deuda para ID {id_cliente}: ${nueva_deuda}")

        return {"status": "success", "pedido_id": nuevo_pedido_id}

    except Exception as e:
        print("❌ ERROR CRÍTICO EN EL CIRCUITO DE PEDIDOS:")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/pedidos/")
@app.get("/pedidos/")
def obtener_pedidos():
    try:
        return supabase.schema("public").table("Pedidos").select("*").execute().data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# ================= ROUTE SALVAVIDAS: Reportes Financieros =================
@app.get("/api/v1/reports/financials")
@app.get("/reports/financials")
def obtener_reportes_financieros_mock():
    try:
        print("--> Frontend solicitando reportes financieros. Enviando datos de respaldo...")
        # Le enviamos un objeto simulado con deudas y balances en 0 o vacíos 
        # para que el frontend no falle al hacer sus cálculos matemáticos.
        return {
            "total_sales": 0.0,
            "total_debts": 0.0,
            "net_profit": 0.0,
            "monthly_history": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))