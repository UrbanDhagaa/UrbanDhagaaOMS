const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const BASE_URL = `${API_BASE}/api/v1`;


export const tokenStorage = {
  get: () => localStorage.getItem('ud_access_token'),
  set: (token) => localStorage.setItem('ud_access_token', token),
  clear: () => localStorage.removeItem('ud_access_token'),
};

async function request(endpoint, options = {}) {
  const token = tokenStorage.get();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    tokenStorage.clear();
    window.dispatchEvent(new Event('auth:unauthorized'));
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.detail || response.statusText || 'Request failed';
    throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
  }

  return data;
}

export const api = {
  // Auth
  login: (email, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  getMe: () => request('/auth/me'),
  seedAdmin: () => request('/auth/seed-admin', { method: 'POST' }),

  // Orders
  getOrders: (params = {}) => {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page);
    if (params.page_size) q.append('page_size', params.page_size);
    if (params.search) q.append('search', params.search);
    if (params.order_status) q.append('order_status', params.order_status);
    if (params.payment_status) q.append('payment_status', params.payment_status);
    if (params.delivery_status) q.append('delivery_status', params.delivery_status);
    if (params.category) q.append('category', params.category);
    return request(`/orders/?${q.toString()}`);
  },
  getOrder: (id) => request(`/orders/${id}`),
  createOrder: (payload) =>
    request('/orders/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  confirmOrder: (id, note = '') =>
    request(`/orders/${id}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    }),
  cancelOrder: (id, reason) =>
    request(`/orders/${id}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  updateOrderStatus: (id, dimension, new_status, note = '') =>
    request(`/orders/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ dimension, new_status, note }),
    }),

  // Customers
  getCustomers: (params = {}) => {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page);
    if (params.page_size) q.append('page_size', params.page_size);
    if (params.search) q.append('search', params.search);
    return request(`/customers/?${q.toString()}`);
  },
  createCustomer: (payload) =>
    request('/customers/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateCustomer: (id, payload) =>
    request(`/customers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  // Quotations
  getQuotations: () => request('/quotations/'),
  createQuotation: (payload) =>
    request('/quotations/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  acceptQuotation: (id, customerPo = '') =>
    request(`/quotations/${id}/accept`, {
      method: 'POST',
      body: JSON.stringify({ auto_confirm_order: true, customer_po_reference: customerPo }),
    }),

  // Payments
  getPayments: (params = {}) => {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page);
    if (params.page_size) q.append('page_size', params.page_size);
    return request(`/payments/?${q.toString()}`);
  },
  createPayment: (payload) =>
    request('/payments/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Invoices
  getInvoices: () => request('/invoices/'),

  // Shipments
  getShipments: () => request('/shipments/'),
  createShipment: (payload) =>
    request('/shipments/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  dispatchShipment: (id, trackingNumber) =>
    request(`/shipments/${id}/dispatch`, {
      method: 'POST',
      body: JSON.stringify({ tracking_number: trackingNumber }),
    }),
  markDelivered: (id, podUrl = '') =>
    request(`/shipments/${id}/delivered`, {
      method: 'POST',
      body: JSON.stringify({ proof_of_delivery_url: podUrl }),
    }),

  // Reports
  getDashboardKPIs: () => request('/reports/dashboard-kpis'),
};
