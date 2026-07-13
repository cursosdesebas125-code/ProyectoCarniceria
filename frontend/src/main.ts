declare var Swal: any;

import { api } from './services/api';
import { Cliente, Producto, OrderCreateRequest } from './types';

// ==========================================
// APPLICATION CONTROLLER
// ==========================================
class AppController {
  // Window 1 State (Clientes list pagination)
  private w1CurrentPage = 1;
  private w1Limit = 5;
  private w1TotalPages = 1;
  

  // Window 2 State (POS Catalog cache)
  private posAvailableProducts: Producto[] = [];
  private posSelectedClientData: Cliente | null = null;

  // DOM Elements - Global
  private viewWindow1 = document.getElementById('view-window1')!;
  private viewWindow2 = document.getElementById('view-window2')!;
  private viewWindow3 = document.getElementById('view-window3')!;

  private tabBtnOverview = document.getElementById('tab-btn-overview')!;
  private tabBtnPos = document.getElementById('tab-btn-pos')!;
  private tabBtnReports = document.getElementById('tab-btn-reports')!;

  // DOM Elements - Window 1 sub-view tabs and panels
  private w1TabClient = document.getElementById('w1-tab-btn-client')!;
  private w1TabProduct = document.getElementById('w1-tab-btn-product')!;
  private w1TabTable = document.getElementById('w1-tab-btn-table')!;

  private w1PanelClient = document.getElementById('w1-panel-client')!;
  private w1PanelProduct = document.getElementById('w1-panel-product')!;
  private w1PanelTable = document.getElementById('w1-panel-table')!;

  // DOM Elements - Window 1 (Management)
  private w1TableBody = document.getElementById('w1-table-body')!;
  private w1BtnPrev = document.getElementById('w1-btn-prev') as HTMLButtonElement;
  private w1BtnNext = document.getElementById('w1-btn-next') as HTMLButtonElement;
  private w1PageInfo = document.getElementById('w1-page-info')!;
  private w1FormCliente = document.getElementById('form-cliente-window1') as HTMLFormElement;
  private w1FormProducto = document.getElementById('form-producto-window1') as HTMLFormElement;
  private w1ProductTableBody = document.getElementById('w1-product-table-body')!;

  // DOM Elements - Window 2 (POS Dynamic Form)
  private posSelectCliente = document.getElementById('pos-select-cliente') as HTMLSelectElement;
  private posBtnAddRow = document.getElementById('pos-btn-add-row') as HTMLButtonElement;
  private posRowsContainer = document.getElementById('pos-rows-container')!;
  private posTotalValue = document.getElementById('pos-total-value')!;
  private posBtnSaveOrder = document.getElementById('pos-btn-save-order') as HTMLButtonElement;

  // DOM Elements - Window 3 (Reports)
  private reportsTabInquiry = document.getElementById('reports-tab-inquiry')!;
  private reportsTabGlobal = document.getElementById('reports-tab-global')!;
  private reportsContentInquiry = document.getElementById('reports-content-inquiry')!;
  private reportsContentGlobal = document.getElementById('reports-content-global')!;
  private reportsSelectCliente = document.getElementById('reports-select-cliente') as HTMLSelectElement;
  private reportsStatementBody = document.getElementById('reports-statement-body')!;
  
  private repOutstanding = document.getElementById('rep-outstanding')!;
  private repOverdue = document.getElementById('rep-overdue')!;
  private repCollected = document.getElementById('rep-collected')!;
  
  private earningsStartDate = document.getElementById('earnings-start-date') as HTMLInputElement;
  private earningsEndDate = document.getElementById('earnings-end-date') as HTMLInputElement;
  private btnCalculateEarnings = document.getElementById('btn-calculate-earnings') as HTMLButtonElement;
  private earningsResultValue = document.getElementById('earnings-result-value')!;
  private earningsResultDetails = document.getElementById('earnings-result-details')!;

  constructor() {
    this.initEvents();
    this.checkConnectivityAndLoad();
  }

  private initEvents(): void {
    // Navigation Action Toggles
    const toggleView = (view: 'window1' | 'window2' | 'window3') => {
      this.hideAllViews();
      if (view === 'window1') {
        this.viewWindow1.style.display = 'grid';
        this.tabBtnOverview.classList.add('active');
        this.switchW1Tab('client'); // Default inner sub-view
      } else if (view === 'window2') {
        this.viewWindow2.style.display = 'grid';
        this.tabBtnPos.classList.add('active');
        this.loadPOSSelectorsData();
      } else {
        this.viewWindow3.style.display = 'block';
        this.tabBtnReports.classList.add('active');
        this.initReportsView();
      }
    };

    this.tabBtnOverview.addEventListener('click', () => toggleView('window1'));
    this.tabBtnPos.addEventListener('click', () => toggleView('window2'));
    this.tabBtnReports.addEventListener('click', () => toggleView('window3'));

    // Window 1: Inner Sub-View Tab Switchers
    this.w1TabClient.addEventListener('click', () => this.switchW1Tab('client'));
    this.w1TabProduct.addEventListener('click', () => this.switchW1Tab('product'));
    this.w1TabTable.addEventListener('click', () => this.switchW1Tab('table'));

    // Window 1: Pagination Click Handlers
    this.w1BtnPrev.addEventListener('click', () => {
      if (this.w1CurrentPage > 1) {
        this.w1CurrentPage--;
        this.renderW1Table();
      }
    });

    this.w1BtnNext.addEventListener('click', () => {
      if (this.w1CurrentPage < this.w1TotalPages) {
        this.w1CurrentPage++;
        this.renderW1Table();
      }
    });

    // Window 1: Form submissions
    this.w1FormCliente.addEventListener('submit', (e) => this.handleW1ClientSubmit(e));
    this.w1FormProducto.addEventListener('submit', (e) => this.handleW1ProductSubmit(e));

    // Window 2: Dynamic Row insertion
    this.posBtnAddRow.addEventListener('click', () => this.addPOSRow());
    this.posBtnSaveOrder.addEventListener('click', () => this.handlePOSSubmitOrder());

    this.posSelectCliente.addEventListener('change', async () => {
      const clientId = parseInt(this.posSelectCliente.value);
      if (!clientId) {
        this.posSelectedClientData = null;
        this.recalculatePOSTotals();
        return;
      }

      try {
        const clientRes = await api.clientes.list(1, 1000);
        const clienteFrescesco = clientRes.items.find(c => c.id === clientId);
        if (clienteFrescesco) {
          console.log(`--> [POS FRESCO] Datos actualizados para: ${clienteFrescesco.NameCliente}, Deuda: $${clienteFrescesco.Deuda_del_cliente}`);
          this.posSelectedClientData = clienteFrescesco;
        }
      } catch (err) {
        console.error('Error al actualizar los datos del cliente en el POS:', err);
      }

      this.recalculatePOSTotals();
    });

    // Window 3: Inner switcher
    this.reportsTabInquiry.addEventListener('click', () => {
      this.reportsTabInquiry.classList.add('active');
      this.reportsTabGlobal.classList.remove('active');
      this.reportsContentInquiry.style.display = 'grid';
      this.reportsContentGlobal.style.display = 'none';
    });

    this.reportsTabGlobal.addEventListener('click', () => {
      this.reportsTabGlobal.classList.add('active');
      this.reportsTabInquiry.classList.remove('active');
      this.reportsContentGlobal.style.display = 'grid';
      this.reportsContentInquiry.style.display = 'none';
      this.loadGlobalFinancialReports();
    });

    // Window 3: Customer Inquiry Selector
    this.reportsSelectCliente.addEventListener('change', () => this.handleReportsLoadStatement());

    // Window 3: Earnings button Click
    this.btnCalculateEarnings.addEventListener('click', () => this.handleReportsCalculateEarnings());
  }

  private hideAllViews(): void {
    this.viewWindow1.style.display = 'none';
    this.viewWindow2.style.display = 'none';
    this.viewWindow3.style.display = 'none';
    this.tabBtnOverview.classList.remove('active');
    this.tabBtnPos.classList.remove('active');
    this.tabBtnReports.classList.remove('active');
  }

  /**
   * Refactors toggling of Window 1 sub-views dynamically.
   */
  private switchW1Tab(tab: 'client' | 'product' | 'table'): void {
    this.w1TabClient.classList.remove('active');
    this.w1TabProduct.classList.remove('active');
    this.w1TabTable.classList.remove('active');

    this.w1PanelClient.style.display = 'none';
    this.w1PanelProduct.style.display = 'none';
    this.w1PanelTable.style.display = 'none';

    if (tab === 'client') {
      this.w1TabClient.classList.add('active');
      this.w1PanelClient.style.display = 'block';
    } else if (tab === 'product') {
      this.w1TabProduct.classList.add('active');
      this.w1PanelProduct.style.display = 'block';
      this.renderW1ProductTable();
    } else {
      this.w1TabTable.classList.add('active');
      this.w1PanelTable.style.display = 'block';
      this.renderW1Table();
    }
  }

  private async checkConnectivityAndLoad(): Promise<void> {
    try {
      await this.renderW1Table();
      console.log('Synchronized with backend server successfully.');
    } catch (err) {
      console.error('Initial connectivity check failed:', err);
      Swal.fire({
        title: 'Error de Conexión',
        text: 'No se pudo establecer comunicación con el servidor backend.',
        icon: 'error',
        confirmButtonColor: '#c62828',
        confirmButtonText: 'Cerrar'
      });
    }
  }

  // ==========================================
  // WINDOW 1: CUSTOMERS TABLE (Sub-view B)
  // ==========================================
  public async renderW1Table(): Promise<void> {
    this.w1TableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Cargando...</td></tr>`;

    try {
      const res = await api.clientes.list(this.w1CurrentPage, this.w1Limit);
      this.w1TotalPages = res.total_pages;
      this.updateW1PaginationUI(res.total_items);
      this.populateW1TableHtml(res.items);
    } catch (err) {
      console.error('Error fetching clients page', err);
      this.w1TableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--accent-meat);">Error al recuperar datos.</td></tr>`;
    }
  }

  private updateW1PaginationUI(totalItems: number): void {
    this.w1PageInfo.innerText = `Página ${this.w1CurrentPage} de ${this.w1TotalPages} (${totalItems} clientes)`;
    this.w1BtnPrev.disabled = this.w1CurrentPage <= 1;
    this.w1BtnNext.disabled = this.w1CurrentPage >= this.w1TotalPages;
  }

  private populateW1TableHtml(clients: Cliente[]): void {
    if (clients.length === 0) {
      this.w1TableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No hay clientes registrados.</td></tr>`;
      return;
    }

    this.w1TableBody.innerHTML = '';

    clients.forEach(c => {
      const row = document.createElement('tr');
      row.className = 'fade-in';

      row.innerHTML = `
        <td><strong>${c.NameCliente}</strong></td>
        <td style="color: var(--accent-meat); font-weight: 700;">$${Number(c.Deuda_del_cliente).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
        <td>
          <span class="badge ${c.Estado === 1 ? 'active' : 'inactive'}">
            ${c.Estado === 1 ? 'Activo' : 'Desactivado'}
          </span>
        </td>
        <td>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-abonar" style="padding: 6px 12px; font-size: 0.8rem; background-color: #27ae60; color: white;">
              💸 Abonar
            </button>
            <button class="btn btn-secondary btn-editar" style="padding: 6px 12px; font-size: 0.8rem;">Editar</button>
            <button class="btn btn-status" style="padding: 6px 12px; font-size: 0.8rem; background-color: ${c.Estado === 1 ? 'rgba(192, 57, 43, 0.1)' : 'rgba(39, 174, 96, 0.1)'}; color: ${c.Estado === 1 ? 'var(--accent-meat)' : 'var(--accent-success)'};">
              ${c.Estado === 1 ? 'Desactivar' : 'Activar'}
            </button>
          </div>
        </td>
      `;

      const btnAbonar = row.querySelector('.btn-abonar') as HTMLButtonElement;
      btnAbonar.addEventListener('click', () => {
        if (typeof (window as any).registrarAbonoCliente === 'function') {
          (window as any).registrarAbonoCliente(c.id, c.NameCliente, c.Deuda_del_cliente);
        }
      });

      const btnEditar = row.querySelector('.btn-editar') as HTMLButtonElement;
      btnEditar.addEventListener('click', () => {
        if (typeof (window as any).editClientName === 'function') {
          (window as any).editClientName(c.id, c.NameCliente);
        }
      });

      const btnStatus = row.querySelector('.btn-status') as HTMLButtonElement;
      btnStatus.addEventListener('click', () => {
        if (typeof (window as any).toggleClientStatus === 'function') {
          (window as any).toggleClientStatus(c.id, c.Estado);
        }
      });

      this.w1TableBody.appendChild(row);
    });
  }

  // ==========================================
  // WINDOW 1: REGISTRY SUBMISSIONS
  // ==========================================
  private async handleW1ClientSubmit(e: Event): Promise<void> {
    e.preventDefault();
    const nameInput = document.getElementById('w1-client-name') as HTMLInputElement;
    const name = nameInput.value.trim();

    if (!name) return;

    const payload = { NameCliente: name, Deuda_del_cliente: 0, Estado: 1 };

    try {
      await api.clientes.create(payload);
      nameInput.value = '';
      this.w1CurrentPage = 1;
      
      Swal.fire({
        title: '¡Cliente Registrado!',
        text: `El cliente "${name}" ha sido guardado exitosamente.`,
        icon: 'success',
        confirmButtonColor: '#2e7d32',
        confirmButtonText: 'Aceptar'
      });

      this.switchW1Tab('table');
    } catch (err: any) {
      console.error('Error al registrar cliente en Supabase:', err);
      Swal.fire({
        title: 'Error al registrar',
        text: err.message || 'No se pudo guardar el cliente en el servidor.',
        icon: 'error',
        confirmButtonColor: '#c62828'
      });
    }
  }

  private async handleW1ProductSubmit(e: Event): Promise<void> {
    e.preventDefault();
    const nameInput = document.getElementById('w1-product-name') as HTMLInputElement;
    const costInput = document.getElementById('w1-product-cost') as HTMLInputElement;
    const saleInput = document.getElementById('w1-product-sale') as HTMLInputElement;

    const name = nameInput.value.trim();
    const cost = parseFloat(costInput.value) || 0;
    const sale = parseFloat(saleInput.value) || 0;

    if (!name || cost <= 0 || sale <= 0) {
      Swal.fire({
        title: 'Datos Inválidos',
        text: 'Por favor, introduce un nombre y valores de precio mayores a $0.',
        icon: 'warning',
        confirmButtonColor: '#ffa000'
      });
      return;
    }

    const payload = { NombreProducto: name, ValorDeCompra: cost, ValorDeVenta: sale };

    try {
      await api.productos.create(payload);
      nameInput.value = '';
      costInput.value = '';
      saleInput.value = '';

      Swal.fire({
        title: '¡Producto Guardado!',
        text: `El producto "${name}" se añadió correctamente al catálogo.`,
        icon: 'success',
        confirmButtonColor: '#2e7d32',
        confirmButtonText: 'Excelente'
      });

      this.renderW1ProductTable();
    } catch (err: any) {
      console.error('Error al registrar producto en Supabase:', err);
      Swal.fire({
        title: 'Error al guardar',
        text: err.message || 'No se pudo registrar el producto.',
        icon: 'error',
        confirmButtonColor: '#c62828'
      });
    }
  }

  public async editClientName(id: number, currentName: string): Promise<void> {
    const { value: newName } = await Swal.fire({
      title: 'Editar Nombre de Cliente',
      input: 'text',
      inputLabel: 'Nombre actual:',
      inputValue: currentName,
      showCancelButton: true,
      confirmButtonColor: '#2e7d32',
      cancelButtonColor: '#757575',
      confirmButtonText: 'Guardar',
      cancelButtonText: 'Cancelar',
      inputValidator: (value: string) => {
        if (!value || !value.trim()) {
          return '¡El nombre no puede estar vacío!';
        }
      }
    });

    if (newName === undefined) return;
    const trimmed = newName.trim();

    try {
      await api.clientes.update(id, { NameCliente: trimmed });
      
      Swal.fire({
        title: '¡Modificado!',
        text: 'Nombre de cliente actualizado.',
        icon: 'success',
        confirmButtonColor: '#2e7d32',
        timer: 1800,
        showConfirmButton: false
      });

      await this.renderW1Table();
    } catch (err: any) {
      Swal.fire({
        title: 'Error',
        text: err.message,
        icon: 'error',
        confirmButtonColor: '#c62828'
      });
    }
  }

  public async toggleStatus(id: number, currentStatus: number): Promise<void> {
    const nextStatus = currentStatus === 1 ? 0 : 1;
    const accionText = nextStatus === 1 ? 'activar' : 'desactivar';

    try {
      await api.clientes.update(id, { Estado: nextStatus });
      
      Swal.fire({
        title: `Cliente ${nextStatus === 1 ? 'Activado' : 'Desactivado'}`,
        text: `El cliente se ha logrado ${accionText} con éxito.`,
        icon: 'success',
        confirmButtonColor: '#2e7d32',
        timer: 1500,
        showConfirmButton: false
      });

      await this.renderW1Table();
    } catch (err: any) {
      Swal.fire({
        title: 'Error de Operación',
        text: err.message,
        icon: 'error',
        confirmButtonColor: '#c62828'
      });
    }
  }

  private async renderW1ProductTable(): Promise<void> {
    this.w1ProductTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Cargando...</td></tr>`;

    try {
      const products = await api.productos.list(1000);
      if (products.length === 0) {
        this.w1ProductTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No hay productos registrados.</td></tr>`;
        return;
      }

      this.w1ProductTableBody.innerHTML = products.map(p => `
        <tr class="fade-in">
          <td><strong>${p.NombreProducto}</strong></td>
          <td>$${Number(p.ValorDeCompra).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
          <td style="color: var(--accent-success); font-weight: 700;">$${Number(p.ValorDeVenta).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
          <td>
            <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem; background-color: rgba(192, 57, 43, 0.1); color: var(--accent-meat);" onclick="window.removeProduct(${p.id})">Remover</button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.error('Error fetching products list', err);
      this.w1ProductTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--accent-meat);">Error al recuperar catálogo.</td></tr>`;
    }
  }

  public async removeProduct(id: number): Promise<void> {
    const confirmacion = await Swal.fire({
      title: '¿Remover Producto?',
      text: 'Se eliminará de forma permanente del catálogo.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#c62828',
      cancelButtonColor: '#757575',
      confirmButtonText: 'Sí, remover',
      cancelButtonText: 'Cancelar'
    });

    if (!confirmacion.isConfirmed) return;

    try {
      await api.productos.delete(id);
      
      Swal.fire({
        title: '¡Removido!',
        text: 'Producto eliminado con éxito.',
        icon: 'success',
        confirmButtonColor: '#2e7d32',
        timer: 1500,
        showConfirmButton: false
      });

      await this.renderW1ProductTable();
    } catch (err: any) {
      console.error('Error al remover producto:', err);
      Swal.fire({
        title: 'Error al remover',
        text: err.message,
        icon: 'error',
        confirmButtonColor: '#c62828'
      });
    }
  }

  // ==========================================
  // WINDOW 2: POS SELECTORS & DYNAMIC ROWS
  // ==========================================

  
  private async loadPOSSelectorsData(): Promise<void> {
    this.posSelectCliente.innerHTML = '<option value="">Cargando clientes activos...</option>';
    this.posRowsContainer.innerHTML = '';
    this.posTotalValue.innerText = '$0.00';
    this.posBtnSaveOrder.disabled = true;

    try {
      const clientRes = await api.clientes.list(1, 1000);
      const activeClients = clientRes.items.filter(c => c.Estado === 1);
      this.posAvailableProducts = await api.productos.list(1000);

      if (activeClients.length === 0) {
        this.posSelectCliente.innerHTML = '<option value="">No hay clientes activos</option>';
      } else {
        this.posSelectCliente.innerHTML = '<option value="">Seleccione cliente...</option>' + 
          activeClients.map(c => `<option value="${c.id}">${c.NameCliente}</option>`).join('');
      }

      this.posRowsContainer.innerHTML = '';
      this.addPOSRow();
    } catch (err) {
      console.error('Error loading POS selectors data', err);
      Swal.fire({
        title: 'Fallo de Red',
        text: 'Error al cargar catálogo de productos o clientes.',
        icon: 'error',
        confirmButtonColor: '#c62828'
      });
    }
  }

  private addPOSRow(): void {
    const rowId = `pos-row-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    
    const rowDiv = document.createElement('div');
    rowDiv.className = 'pos-row-item';
    rowDiv.id = rowId;
    
    rowDiv.innerHTML = `
      <select class="form-control pos-row-select-prod">
        <option value="">Seleccione producto...</option>
        ${this.posAvailableProducts.map(p => `
          <option value="${p.id}">
            ${p.NombreProducto} ($${Number(p.ValorDeVenta).toFixed(2)}/kg)
          </option>
        `).join('')}
      </select>
      <input type="number" class="form-control pos-row-qty" min="0.5" step="0.5" value="0.5" placeholder="Cantidad (Kilos)">
      <span class="pos-row-subtotal">$0.00</span>
      <button type="button" class="pos-row-delete" title="Quitar línea">&times;</button>
    `;

    this.posRowsContainer.appendChild(rowDiv);

    const selectEl = rowDiv.querySelector('.pos-row-select-prod') as HTMLSelectElement;
    const qtyInput = rowDiv.querySelector('.pos-row-qty') as HTMLInputElement;
    const subtotalSpan = rowDiv.querySelector('.pos-row-subtotal') as HTMLSpanElement;
    const deleteBtn = rowDiv.querySelector('.pos-row-delete') as HTMLButtonElement;

    const onRowChange = () => {
      const prodId = parseInt(selectEl.value);
      const qty = parseFloat(qtyInput.value) || 0;

      const product = this.posAvailableProducts.find(p => p.id === prodId);
      if (product && qty > 0) {
        const rate = Number(product.ValorDeVenta);
        subtotalSpan.innerText = `$${(qty * rate).toFixed(2)}`;
      } else {
        subtotalSpan.innerText = '$0.00';
      }

      this.recalculatePOSTotals();
    };

    selectEl.addEventListener('change', onRowChange);
    qtyInput.addEventListener('input', onRowChange);

    deleteBtn.addEventListener('click', () => {
      rowDiv.remove();
      this.recalculatePOSTotals();
    });

    this.recalculatePOSTotals();
  }

  private recalculatePOSTotals(): void {
    const rows = this.posRowsContainer.querySelectorAll('.pos-row-item');
    let grandTotal = 0;
    let allValid = true;
    let hasItems = false;

    rows.forEach(row => {
      hasItems = true;
      const selectEl = row.querySelector('.pos-row-select-prod') as HTMLSelectElement;
      const qtyInput = row.querySelector('.pos-row-qty') as HTMLInputElement;

      const prodId = parseInt(selectEl.value);
      const qty = parseFloat(qtyInput.value) || 0;

      if (!prodId || qty <= 0) {
        allValid = false;
      } else {
        const product = this.posAvailableProducts.find(p => p.id === prodId);
        if (product) {
          grandTotal += qty * Number(product.ValorDeVenta);
        }
      }
    });

    this.posTotalValue.innerText = `$${grandTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    const clientSelected = this.posSelectCliente.value !== '';
    this.posBtnSaveOrder.disabled = !(clientSelected && hasItems && allValid);
  }

 private async handlePOSSubmitOrder(): Promise<void> {
    const clientId = parseInt(this.posSelectCliente.value);
    if (!clientId) {
      Swal.fire({
        title: 'Falta Cliente',
        text: 'Por favor, seleccione el cliente destinatario.',
        icon: 'warning',
        confirmButtonColor: '#ffa000'
      });
      return;
    }

    try {
      const clienteActual = this.posSelectedClientData;
      console.log("CLIENTE SELECCIONADO (Fresco):", clienteActual);

      if (clienteActual && Number(clienteActual.Estado) === 1 && Number(clienteActual.Deuda_del_cliente) > 0) {
        const confirmacionDeuda = await Swal.fire({
          title: '¡Atención: El cliente debe!',
          text: `Este cliente tiene un saldo pendiente de $${clienteActual.Deuda_del_cliente}. ¿Estás seguro de que quieres crear el pedido?`,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#2e7d32',
          cancelButtonColor: '#757575',
          confirmButtonText: 'Sí, crear pedido',
          cancelButtonText: 'Cancelar'
        });

        if (!confirmacionDeuda.isConfirmed) {
          return; 
        }
      }
    } catch (err) {
      console.error('Error al verificar el estado del cliente:', err);
    }

    const rows = this.posRowsContainer.querySelectorAll('.pos-row-item');
    if (rows.length === 0) {
      Swal.fire({
        title: 'Carrito Vacío',
        text: 'El pedido debe contener al menos un producto.',
        icon: 'warning',
        confirmButtonColor: '#ffa000'
      });
      return;
    }

    const items: { id_producto: number; cantidad_producto: number; Valor_del_Pedido: number }[] = [];
    const seenProductIds = new Set<number>();
    let validationError = '';

    rows.forEach((row, index) => {
      const selectEl = row.querySelector('.pos-row-select-prod') as HTMLSelectElement;
      const qtyInput = row.querySelector('.pos-row-qty') as HTMLInputElement;

      const prodId = parseInt(selectEl.value);
      const qty = parseFloat(qtyInput.value) || 0;

      if (!prodId) {
        validationError = `Fila #${index + 1}: Seleccione un producto.`;
      }
      if (qty <= 0) {
        validationError = `Fila #${index + 1}: Ingrese una cantidad mayor a cero.`;
      }

      if (seenProductIds.has(prodId)) {
        validationError = `El producto de la fila #${index + 1} ya está registrado en este pedido. Agregue la cantidad en una sola fila.`;
      }
      seenProductIds.add(prodId);

      const product = this.posAvailableProducts.find(p => p.id === prodId);
      if (product) {
        items.push({
          id_producto: prodId,
          cantidad_producto: qty,
          Valor_del_Pedido: qty * Number(product.ValorDeVenta)
        });
      }
    });

    if (validationError) {
      Swal.fire({
        title: 'Corrección de Pedido',
        text: validationError,
        icon: 'warning',
        confirmButtonColor: '#ffa000'
      });
      return;
    }

    const payload: OrderCreateRequest = {
      IDcliente: clientId,
      items: items
    };

    try {
      // 🚀 AQUÍ ESTÁ EL ENVÍO REAL USANDO TUS PROPIOS MÉTODOS DEL PROYECTO
      await api.pedidos.create(payload);
      
      Swal.fire({
        title: '¡Pedido Registrado!',
        text: 'El pedido se ha guardado y la deuda del cliente fue actualizada.',
        icon: 'success',
        confirmButtonColor: '#2e7d32',
        confirmButtonText: 'Aceptar'
      });

      this.clearPOSAndReturn();
    } catch (err: any) {
      console.error('Error al registrar pedido en Supabase:', err);
      Swal.fire({
        title: 'Error de Registro',
        text: err.message || 'Hubo un error al registrar el pedido.',
        icon: 'error',
        confirmButtonColor: '#c62828'
      });
    }
  }

  private clearPOSAndReturn(): void {
    this.posSelectCliente.value = '';
    this.posRowsContainer.innerHTML = '';
    this.posTotalValue.innerText = '$0.00';
    this.posBtnSaveOrder.disabled = true;
    
    this.hideAllViews();
    this.viewWindow1.style.display = 'grid';
    this.tabBtnOverview.classList.add('active');

    this.w1CurrentPage = 1;
    this.switchW1Tab('table');
  }

  // ==========================================
  // WINDOW 3: REPORTS & ANALYTICS
  // ==========================================
  private async initReportsView(): Promise<void> {
    this.reportsTabInquiry.classList.add('active');
    this.reportsTabGlobal.classList.remove('active');
    this.reportsContentInquiry.style.display = 'grid';
    this.reportsContentGlobal.style.display = 'none';

    const todayStr = new Date().toISOString().substring(0, 10);
    const prevDate = new Date();
    prevDate.setDate(prevDate.getDate() - 30);
    const prevDateStr = prevDate.toISOString().substring(0, 10);

    this.earningsStartDate.value = prevDateStr;
    this.earningsEndDate.value = todayStr;
    
    this.earningsResultValue.innerText = '$0.00';
    this.earningsResultDetails.innerText = 'Seleccione un rango de fechas para calcular la ganancia neta.';

    this.reportsSelectCliente.innerHTML = '<option value="">Cargando clientes...</option>';
    
    try {
      const res = await api.clientes.list(1, 1000);
      const allClients = res.items;

      if (allClients.length === 0) {
        this.reportsSelectCliente.innerHTML = '<option value="">No hay clientes registrados</option>';
      } else {
        this.reportsSelectCliente.innerHTML = '<option value="">Seleccione cliente...</option>' + 
          allClients.map(c => `<option value="${c.id}">${c.NameCliente}</option>`).join('');
      }
    } catch (err) {
      console.error('Error loading reports select client dropdown:', err);
    }

    this.reportsStatementBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Seleccione un cliente del listado superior.</td></tr>`;
  }

  private async handleReportsLoadStatement(): Promise<void> {
    const clientId = parseInt(this.reportsSelectCliente.value);
    if (!clientId) {
      this.reportsStatementBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Seleccione un cliente del listado superior.</td></tr>`;
      return;
    }

    this.reportsStatementBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Generando estado de cuenta...</td></tr>`;

    try {
      const statements = await api.clientes.statement(clientId);
      this.populateReportsStatementTable(statements);
    } catch (err: any) {
      console.error('Failed fetching statement from API', err);
      this.reportsStatementBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--accent-meat);">Error al recuperar el estado de cuenta.</td></tr>`;
    }
  }

  private populateReportsStatementTable(records: any[]): void {
    if (records.length === 0) {
      this.reportsStatementBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">El cliente seleccionado no registra pedidos.</td></tr>`;
      return;
    }

    this.reportsStatementBody.innerHTML = records.map(r => {
      const isOverdue = r.overdue === true;
      const termClass = isOverdue ? 'inactive' : 'active';
      const termLabel = isOverdue ? 'Vencido' : 'En Plazo';
      const statusClass = r.estado === 'Pagado' ? 'completed' : (r.estado === 'Entregado' ? 'active' : 'pending');

      return `
        <tr class="fade-in">
          <td>#${r.order_id}</td>
          <td>${r.fecha_pedido}</td>
          <td style="font-weight: 600;">$${Number(r.total).toFixed(2)}</td>
          <td>${r.days_since_created} días</td>
          <td><span class="badge ${statusClass}">${r.estado}</span></td>
          <td><span class="badge ${termClass}">${termLabel}</span></td>
        </tr>
      `;
    }).join('');
  }

  private async loadGlobalFinancialReports(): Promise<void> {
    this.repOutstanding.innerText = 'Calculando...';
    this.repOverdue.innerText = 'Calculando...';
    this.repCollected.innerText = 'Calculando...';

    try {
      const response = await api.reports.financials();
      this.repOutstanding.innerText = `$${Number(response.total_outstanding_debt).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
      this.repOverdue.innerText = `$${Number(response.total_overdue).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
      this.repCollected.innerText = `$${Number(response.total_collected).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    } catch (err) {
      console.error('Error fetching global financials from API', err);
      this.repOutstanding.innerText = 'Error';
      this.repOverdue.innerText = 'Error';
      this.repCollected.innerText = 'Error';
    }
  }

  private async handleReportsCalculateEarnings(): Promise<void> {
    const start = this.earningsStartDate.value;
    const end = this.earningsEndDate.value;

    if (!start || !end) {
      Swal.fire({
        title: 'Fechas Incompletas',
        text: 'Por favor, define ambas fechas para calcular la rentabilidad.',
        icon: 'warning',
        confirmButtonColor: '#ffa000'
      });
      return;
    }

    if (new Date(start) > new Date(end)) {
      Swal.fire({
        title: 'Fechas Erróneas',
        text: 'La fecha inicial no puede ser posterior a la fecha final.',
        icon: 'warning',
        confirmButtonColor: '#ffa000'
      });
      return;
    }

    this.earningsResultValue.innerText = 'Calculando...';
    this.earningsResultDetails.innerText = 'Consultando base de datos...';

    try {
      const response = await api.reports.earnings(start, end);
      this.earningsResultValue.innerText = `$${Number(response.net_profit).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
      this.earningsResultDetails.innerText = `Margen calculado sobre ${response.orders_count} pedidos. Ventas: $${Number(response.total_sales).toFixed(2)}, Costos: $${Number(response.total_cost).toFixed(2)}`;
    } catch (err: any) {
      console.error('Error calculating earnings from API', err);
      this.earningsResultValue.innerText = 'Error';
      this.earningsResultDetails.innerText = `Error: ${err.message}`;
      
      Swal.fire({
        title: 'Error de Reporte',
        text: 'No se pudo calcular la ganancia en este periodo.',
        icon: 'error',
        confirmButtonColor: '#c62828'
      });
    }
  }
}

// Initialize Global Controller
let appControllerInstance: AppController;
document.addEventListener('DOMContentLoaded', () => {
  appControllerInstance = new AppController();

  // Bind actions globally
  (window as any).editClientName = (id: number, currentName: string) => {
    appControllerInstance.editClientName(id, currentName);
  };

  (window as any).toggleClientStatus = (id: number, currentStatus: number) => {
    appControllerInstance.toggleStatus(id, currentStatus);
  };

  (window as any).removeProduct = (id: number) => {
    appControllerInstance.removeProduct(id);
  };

  (window as any).registrarAbonoCliente = async (clienteId: number, nombreCliente: string, deudaActual: number) => {
    // 💸 Usamos SweetAlert2 para pedir el monto en una interfaz premium
    const { value: valorIngresado } = await Swal.fire({
      title: `Abonar a ${nombreCliente}`,
      html: `Deuda actual: <strong>$${deudaActual}</strong><br><br>Ingrese el monto que va a abonar:`,
      input: 'number',
      inputPlaceholder: `Ej: ${deudaActual}`,
      inputValue: '',
      showCancelButton: true,
      confirmButtonColor: '#2e7d32', // Verde
      cancelButtonColor: '#757575',  // Gris
      confirmButtonText: 'Procesar Abono',
      cancelButtonText: 'Cancelar',
      inputValidator: (value: string) => {
        if (!value || isNaN(parseFloat(value)) || parseFloat(value) <= 0) {
          return '¡Debes ingresar un monto válido y mayor a cero!';
        }
      }
    });

    // Si el usuario canceló o cerró la ventana, nos detenemos
    if (!valorIngresado) return;

    const monto = parseFloat(valorIngresado);

    try {
      const response = await fetch(`http://localhost:8000/api/v1/clientes/${clienteId}/abonar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monto: monto })
      });

      if (response.ok) {
        const resultado = await response.json();
        
        // ✨ VENTANA DE ÉXITO PREMIUM
        Swal.fire({
          title: '¡Abono Registrado!',
          text: `Nueva deuda de ${nombreCliente}: $${resultado.nueva_deuda}`,
          icon: 'success',
          confirmButtonColor: '#2e7d32',
          confirmButtonText: 'Excelente'
        });
        
        if (appControllerInstance) {
          await appControllerInstance.renderW1Table();
        }
      } else {
        // ⚠️ ALERTA DE ERROR INTERNO
        Swal.fire({
          title: 'Error al procesar',
          text: 'El servidor recibió los datos pero no pudo aplicar el abono.',
          icon: 'warning',
          confirmButtonColor: '#dd2c00',
          confirmButtonText: 'Revisar'
        });
      }
    } catch (error) {
      console.error("Error al registrar abono:", error);
      
      // ❌ ALERTA DE ERROR DE CONEXIÓN
      Swal.fire({
        title: 'Fallo de Conexión',
        text: 'No se pudo establecer comunicación con el backend.',
        icon: 'error',
        confirmButtonColor: '#c62828',
        confirmButtonText: 'Cerrar'
      });
    }
  };
});