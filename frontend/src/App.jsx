import React, { useState, useEffect } from 'react';
import {
  Package,
  Layers,
  Users,
  CreditCard,
  Truck,
  FileText,
  Search,
  Plus,
  RefreshCw,
  LogOut,
  SlidersHorizontal,
  ChevronRight,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Menu,
  X
} from 'lucide-react';
import { api, tokenStorage } from './api/client';
import StatusBadge from './components/StatusBadge';
import KPICard from './components/KPICard';
import CreateOrderModal from './components/CreateOrderModal';
import OrderDetailModal from './components/OrderDetailModal';
import CreateCustomerModal from './components/CreateCustomerModal';

export default function App() {
  const [token, setToken] = useState(() => tokenStorage.get());
  const [user, setUser] = useState(() => tokenStorage.getUser());
  const [isInitializing, setIsInitializing] = useState(() => {
    return !!tokenStorage.get() && !tokenStorage.getUser();
  });
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('ud_active_tab') || 'dashboard';
  });
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  // Login form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);


  // Data states
  const [kpis, setKpis] = useState(null);
  const [orders, setOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(false);

  // Filter states
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [paymentFilter, setPaymentFilter] = useState('');
  const [deliveryFilter, setDeliveryFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  // Modals
  const [isCreateOrderOpen, setIsCreateOrderOpen] = useState(false);
  const [isCreateCustOpen, setIsCreateCustOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

  // Customer inline edits: { [customerId]: { contact_number, whatsapp_link } }
  const [customerEdits, setCustomerEdits] = useState({});

  useEffect(() => {
    const handleUnauthorized = () => {
      tokenStorage.clear();
      setToken(null);
      setUser(null);
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  useEffect(() => {
    if (activeTab) {
      localStorage.setItem('ud_active_tab', activeTab);
    }
  }, [activeTab]);

  useEffect(() => {
    if (token) {
      loadCurrentUser();
    } else {
      setIsInitializing(false);
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      refreshData();
    }
  }, [user, activeTab, search, statusFilter, paymentFilter, deliveryFilter, categoryFilter]);

  async function loadCurrentUser() {
    try {
      const me = await api.getMe();
      tokenStorage.setUser(me);
      setUser(me);
    } catch (err) {
      if (err?.status === 401) {
        tokenStorage.clear();
        setToken(null);
        setUser(null);
      } else {
        console.warn('Background auth check failed (network/server status):', err.message);
      }
    } finally {
      setIsInitializing(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    try {
      // First ensure admin is seeded if first time
      await api.seedAdmin().catch(() => {});
      const res = await api.login(email, password);
      tokenStorage.set(res.access_token);
      tokenStorage.setUser(res.user);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err) {
      setAuthError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setAuthLoading(false);
    }
  }

  function handleLogout() {
    tokenStorage.clear();
    setToken(null);
    setUser(null);
  }

  async function refreshData() {
    setLoading(true);
    try {
      if (activeTab === 'dashboard') {
        const [kpiRes, ordRes] = await Promise.all([
          api.getDashboardKPIs(),
          api.getOrders({ page_size: 10 }),
        ]);
        setKpis(kpiRes);
        setOrders(ordRes.items || []);
      } else if (activeTab === 'orders') {
        const ordRes = await api.getOrders({
          search,
          order_status: statusFilter || undefined,
          payment_status: paymentFilter || undefined,
          delivery_status: deliveryFilter || undefined,
          category: categoryFilter || undefined,
          page_size: 50,
        });
        setOrders(ordRes.items || []);
      } else if (activeTab === 'customers') {
        const custRes = await api.getCustomers({ search, page_size: 50 });
        setCustomers(custRes.items || []);
      } else if (activeTab === 'payments') {
        const payRes = await api.getPayments({ page_size: 50 });
        setPayments(payRes.items || []);
      } else if (activeTab === 'shipments') {
        const shpRes = await api.getShipments();
        setShipments(shpRes || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Save inline customer field edits
  async function saveCustomerEdit(customerId) {
    const edits = customerEdits[customerId] || {};
    try {
      await api.updateCustomer(customerId, {
        contact_number: edits.contact_number ?? undefined,
        whatsapp_link: edits.whatsapp_link ?? undefined,
      });
      refreshData();
    } catch (err) {
      console.error('Failed to save customer edits:', err.message);
    }
  }

  function setCustEditField(customerId, field, value) {
    setCustomerEdits((prev) => ({
      ...prev,
      [customerId]: { ...(prev[customerId] || {}), [field]: value },
    }));
  }

  // If verifying an existing session without cached profile
  if (isInitializing) {
    return (
      <div className="login-wrap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <img src="/logo.png" alt="UrbanDhagaa Logo" className="brand-logo" style={{ height: 40, marginBottom: 16 }} />
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)', fontSize: 14 }}>
            <RefreshCw size={18} className="spin" />
            <span>Resuming session...</span>
          </div>
        </div>
      </div>
    );
  }

  // If not logged in, render clean minimal login screen
  if (!user) {
    return (
      <div className="login-wrap">
        <div className="login-card">
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 18,
                fontWeight: 700,
                letterSpacing: '0.05em',
                marginBottom: 6,
              }}
            >
              <img src="/logo.png" alt="UrbanDhagaa Logo" className="brand-logo" style={{ height: 32 }} />
              URBANDHAGAA
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              Order Management System • Admin Portal
            </p>
          </div>

          {authError && (
            <div
              style={{
                background: 'var(--badge-cancelled-bg)',
                color: 'var(--badge-cancelled-text)',
                padding: '10px 14px',
                borderRadius: 6,
                marginBottom: 16,
                fontSize: 13,
              }}
            >
              {authError}
            </div>
          )}

          <form onSubmit={handleLogin} autoComplete="off">
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="off"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>


            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 8 }}
              disabled={authLoading}
            >
              {authLoading ? 'Signing in...' : 'Sign In to OMS'}
            </button>
          </form>
        </div>
      </div>
    );

  }

  return (
    <div className="app-container">
      {/* Mobile Sidebar Backdrop Overlay */}
      <div
        className={`sidebar-backdrop ${isMobileNavOpen ? 'active' : ''}`}
        onClick={() => setIsMobileNavOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${isMobileNavOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="brand-badge">
            <img src="/logo.png" alt="UrbanDhagaa Logo" className="brand-logo" style={{ height: 26 }} />
            URBANDHAGAA
          </div>
          <button
            className="mobile-sidebar-close"
            onClick={() => setIsMobileNavOpen(false)}
            aria-label="Close Navigation"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('dashboard');
              setIsMobileNavOpen(false);
            }}
          >
            <Layers size={17} />
            <span>Dashboard</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'orders' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('orders');
              setIsMobileNavOpen(false);
            }}
          >
            <Package size={17} />
            <span>Orders Register</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'customers' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('customers');
              setIsMobileNavOpen(false);
            }}
          >
            <Users size={17} />
            <span>Customers</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'payments' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('payments');
              setIsMobileNavOpen(false);
            }}
          >
            <CreditCard size={17} />
            <span>Payments</span>
          </button>

          <button
            className={`nav-item ${activeTab === 'shipments' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('shipments');
              setIsMobileNavOpen(false);
            }}
          >
            <Truck size={17} />
            <span>Fulfilment</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="user-badge">
            <div className="user-info">
              <span className="user-name">{user.full_name}</span>
              <span className="user-role">{user.roles?.[0]?.name || 'ADMIN'}</span>
            </div>
            <button
              onClick={handleLogout}
              className="btn btn-outline btn-sm"
              title="Logout"
              style={{ padding: 6 }}
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-bar">
          <div className="top-bar-left">
            <button
              className="mobile-menu-btn"
              onClick={() => setIsMobileNavOpen(true)}
              aria-label="Open Navigation"
            >
              <Menu size={18} />
            </button>
            <h1 className="page-title">
              {activeTab === 'dashboard' && 'Operations Dashboard'}
              {activeTab === 'orders' && 'Master Orders Register'}
              {activeTab === 'customers' && 'Customer Directory'}
              {activeTab === 'payments' && 'Payment Receipts'}
              {activeTab === 'shipments' && 'Shipment & Fulfilment'}
            </h1>
            <span className="live-badge">
              Live v1.0
            </span>
          </div>

          <div className="top-bar-actions">
            <button
              className="btn btn-outline btn-sm"
              onClick={refreshData}
              title="Refresh"
              disabled={loading}
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
            </button>

            {activeTab === 'customers' ? (
              <button className="btn btn-primary btn-sm" onClick={() => setIsCreateCustOpen(true)}>
                <Plus size={15} /> <span className="btn-label">Add Customer</span>
              </button>
            ) : (
              <button className="btn btn-primary btn-sm" onClick={() => setIsCreateOrderOpen(true)}>
                <Plus size={15} /> <span className="btn-label">New Order</span>
              </button>
            )}
          </div>
        </header>

        <main className="content-body">
          {/* DASHBOARD TAB */}
          {activeTab === 'dashboard' && (
            <div>
              {/* Executive KPI Counter Grid */}
              <div className="kpi-grid">
                <KPICard label="Total Orders" value={kpis?.total_orders} icon={Package} />
                <KPICard label="Open Orders" value={kpis?.open_orders} subtext="In active workflow" icon={Clock} />
                <KPICard
                  label="Confirmed Orders"
                  value={kpis?.confirmed_orders}
                  subtext="Ready for execution"
                  icon={CheckCircle2}
                />
                <KPICard
                  label="In Fulfilment"
                  value={kpis?.in_fulfilment_orders}
                  subtext="Production & dispatch"
                  icon={Truck}
                />
                <KPICard
                  label="Total Order Value"
                  value={kpis?.total_order_value}
                  isCurrency={true}
                  icon={TrendingUp}
                />
                <KPICard
                  label="Amount Received"
                  value={kpis?.amount_received}
                  isCurrency={true}
                  subtext="Cleared payments"
                  icon={CreditCard}
                />
                <KPICard
                  label="Outstanding Receivables"
                  value={kpis?.outstanding_receivables}
                  isCurrency={true}
                  subtext="Unpaid balances"
                  icon={AlertCircle}
                />
                <KPICard
                  label="Design Approvals Pending"
                  value={kpis?.pending_design_approvals}
                  subtext="Artwork review"
                  icon={FileText}
                />
              </div>

              {/* Recent Orders Snapshot */}
              <div className="table-card">
                <div className="table-header-controls">
                  <span style={{ fontWeight: 600, fontSize: 14 }}>Recent Active Orders</span>
                  <button className="btn btn-outline btn-sm" onClick={() => setActiveTab('orders')}>
                    View All Orders <ChevronRight size={14} />
                  </button>
                </div>

                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Order ID</th>
                        <th>Customer</th>
                        <th>Category</th>
                        <th>Order Status</th>
                        <th>Payment</th>
                        <th>Production</th>
                        <th>Delivery</th>
                        <th>Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.length === 0 ? (
                        <tr>
                          <td colSpan="8" style={{ textAlign: 'center', padding: 30, color: 'var(--text-muted)' }}>
                            No orders created yet. Click "+ New Order" to start!
                          </td>
                        </tr>
                      ) : (
                        orders.map((ord) => (
                          <tr
                            key={ord.id}
                            style={{ cursor: 'pointer' }}
                            onClick={() => setSelectedOrder(ord)}
                          >
                            <td className="mono" style={{ fontWeight: 600 }}>{ord.order_number}</td>
                            <td style={{ fontWeight: 500 }}>{ord.customer?.company_name || '—'}</td>
                            <td style={{ fontSize: 12 }}>{ord.category}</td>
                            <td><StatusBadge status={ord.order_status} /></td>
                            <td><StatusBadge status={ord.payment_status} /></td>
                            <td><StatusBadge status={ord.production_status} /></td>
                            <td><StatusBadge status={ord.delivery_status} /></td>
                            <td className="mono" style={{ fontWeight: 600 }}>₹{ord.total_amount.toLocaleString()}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* MASTER ORDERS REGISTER TAB */}
          {activeTab === 'orders' && (
            <div className="table-card">
              <div className="table-header-controls">
                <div className="search-box">
                  <Search size={15} style={{ color: 'var(--text-muted)' }} />
                  <input
                    type="text"
                    placeholder="Search by Order ID, Customer, PO..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>

                <div className="filters-row">
                  <select
                    className="select-filter"
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                  >
                    <option value="">All Categories</option>
                    <option value="MER">Merchandise (MER)</option>
                    <option value="GFT">Gifting (GFT)</option>
                    <option value="WKT">Welcome Kits (WKT)</option>
                    <option value="MIX">Mixed (MIX)</option>
                  </select>

                  <select
                    className="select-filter"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <option value="">All Order Statuses</option>
                    <option value="Draft">Draft</option>
                    <option value="Confirmed">Confirmed</option>
                    <option value="In Fulfilment">In Fulfilment</option>
                    <option value="Delivered">Delivered</option>
                    <option value="Cancelled">Cancelled</option>
                  </select>

                  <select
                    className="select-filter"
                    value={paymentFilter}
                    onChange={(e) => setPaymentFilter(e.target.value)}
                  >
                    <option value="">All Payments</option>
                    <option value="Unpaid">Unpaid</option>
                    <option value="Partially Paid">Partially Paid</option>
                    <option value="Paid">Paid</option>
                  </select>

                  <select
                    className="select-filter"
                    value={deliveryFilter}
                    onChange={(e) => setDeliveryFilter(e.target.value)}
                  >
                    <option value="">All Fulfilment</option>
                    <option value="Not Dispatched">Not Dispatched</option>
                    <option value="Partially Dispatched">Partially Dispatched</option>
                    <option value="In Transit">In Transit</option>
                    <option value="Delivered">Delivered</option>
                  </select>
                </div>
              </div>

              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Order ID</th>
                      <th>Customer</th>
                      <th>Cat</th>
                      <th>Order Status</th>
                      <th>Payment Status</th>
                      <th>Design</th>
                      <th>Production</th>
                      <th>Delivery Status</th>
                      <th>Total (INR)</th>
                      <th>Payment Remains</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.length === 0 ? (
                      <tr>
                        <td colSpan="10" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                          No matching orders found.
                        </td>
                      </tr>
                    ) : (
                      orders.map((ord) => (
                        <tr
                          key={ord.id}
                          style={{ cursor: 'pointer' }}
                          onClick={() => setSelectedOrder(ord)}
                        >
                          <td className="mono" style={{ fontWeight: 600 }}>{ord.order_number}</td>
                          <td style={{ fontWeight: 500 }}>
                            <div>{ord.customer?.company_name || '—'}</div>
                            {ord.customer_po_reference && (
                              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                PO: {ord.customer_po_reference}
                              </div>
                            )}
                          </td>
                          <td>{ord.category}</td>
                          <td><StatusBadge status={ord.order_status} /></td>
                          <td><StatusBadge status={ord.payment_status} /></td>
                          <td><StatusBadge status={ord.design_status} /></td>
                          <td><StatusBadge status={ord.production_status} /></td>
                          <td><StatusBadge status={ord.delivery_status} /></td>
                          <td className="mono" style={{ fontWeight: 600 }}>₹{Number(ord.total_amount).toLocaleString()}</td>
                          <td className="mono" style={{
                            fontWeight: 600,
                            color: (ord.payment_remaining == null || ord.payment_remaining <= 0 || ord.order_status === 'Cancelled')
                              ? 'var(--text-muted)'
                              : '#991b1b',
                          }}>
                            {(ord.order_status === 'Cancelled')
                              ? '—'
                              : ord.payment_remaining != null
                                ? `₹${Number(ord.payment_remaining).toLocaleString()}`
                                : '—'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* CUSTOMERS TAB */}
          {activeTab === 'customers' && (
            <div className="table-card">
              <div className="table-header-controls">
                <div className="search-box">
                  <Search size={15} style={{ color: 'var(--text-muted)' }} />
                  <input
                    type="text"
                    placeholder="Search company, code, GSTIN..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
              </div>

              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Customer Code</th>
                      <th>Company Name</th>
                      <th>Type</th>
                      <th>GSTIN</th>
                      <th>Payment Terms</th>
                      <th>Payment</th>
                      <th>Payment Remains</th>
                      <th>Contact Number</th>
                      <th>WhatsApp Group</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {customers.length === 0 ? (
                      <tr>
                        <td colSpan="10" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                          No customers added yet. Click "+ Add Customer" above.
                        </td>
                      </tr>
                    ) : (
                      customers.map((c) => (
                        <tr key={c.id}>
                          <td className="mono" style={{ fontWeight: 600 }}>{c.customer_code}</td>
                          <td style={{ fontWeight: 500 }}>{c.company_name}</td>
                          <td>{c.customer_type}</td>
                          <td className="mono">{c.gstin || '—'}</td>
                          <td>{c.payment_terms}</td>
                          {/* Payment column: sum of received payments from this customer */}
                          <td className="mono" style={{ color: '#166534', fontWeight: 600 }}>
                            {c.total_paid != null ? `₹${Number(c.total_paid).toLocaleString()}` : '—'}
                          </td>
                          {/* Payment Remains: outstanding balance across all active orders */}
                          <td className="mono" style={{
                            fontWeight: 600,
                            color: (c.payment_remaining == null || c.payment_remaining <= 0)
                              ? 'var(--text-muted)'
                              : '#991b1b',
                          }}>
                            {c.payment_remaining != null
                              ? c.payment_remaining > 0
                                ? `₹${Number(c.payment_remaining).toLocaleString()}`
                                : '—'
                              : '—'}
                          </td>
                          {/* Inline editable: Contact Number */}
                          <td style={{ minWidth: 160 }}>
                            <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                              <input
                                type="tel"
                                className="form-input"
                                style={{ fontSize: 12, padding: '4px 8px', flex: 1 }}
                                placeholder="+91 98765..."
                                value={
                                  customerEdits[c.id]?.contact_number !== undefined
                                    ? customerEdits[c.id].contact_number
                                    : c.contact_number || ''
                                }
                                onChange={(e) => setCustEditField(c.id, 'contact_number', e.target.value)}
                                onBlur={() => saveCustomerEdit(c.id)}
                              />
                            </div>
                          </td>
                          {/* Inline editable: WhatsApp Group Link */}
                          <td style={{ minWidth: 200 }}>
                            <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                              <input
                                type="url"
                                className="form-input"
                                style={{ fontSize: 12, padding: '4px 8px', flex: 1 }}
                                placeholder="https://chat.whatsapp.com/..."
                                value={
                                  customerEdits[c.id]?.whatsapp_link !== undefined
                                    ? customerEdits[c.id].whatsapp_link
                                    : c.whatsapp_link || ''
                                }
                                onChange={(e) => setCustEditField(c.id, 'whatsapp_link', e.target.value)}
                                onBlur={() => saveCustomerEdit(c.id)}
                              />
                              {c.whatsapp_link && (
                                <a
                                  href={c.whatsapp_link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{ fontSize: 11, color: '#25d366', whiteSpace: 'nowrap' }}
                                >
                                  Open
                                </a>
                              )}
                            </div>
                          </td>
                          <td>
                            <span className="status-pill status-confirmed">
                              <span className="pill-dot" /> {c.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* PAYMENTS TAB */}
          {activeTab === 'payments' && (
            <div className="table-card">
              <div className="table-header-controls">
                <span style={{ fontWeight: 600 }}>Receipts & Commercial Records</span>
              </div>

              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Receipt No</th>
                      <th>Customer</th>
                      <th>Method</th>
                      <th>Txn Reference</th>
                      <th>Date</th>
                      <th>Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.length === 0 ? (
                      <tr>
                        <td colSpan="7" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                          No payments recorded yet.
                        </td>
                      </tr>
                    ) : (
                      payments.map((p) => (
                        <tr key={p.id}>
                          <td className="mono" style={{ fontWeight: 600 }}>{p.receipt_number}</td>
                          <td>{p.customer_id}</td>
                          <td>{p.payment_method}</td>
                          <td className="mono">{p.transaction_reference || '—'}</td>
                          <td className="mono">{p.received_date}</td>
                          <td className="mono" style={{ fontWeight: 600 }}>₹{p.amount?.toLocaleString()}</td>
                          <td><StatusBadge status={p.status} /></td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* FULFILMENT TAB */}
          {activeTab === 'shipments' && (
            <div className="table-card">
              <div className="table-header-controls">
                <span style={{ fontWeight: 600 }}>Shipments & Dispatches</span>
              </div>

              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Shipment No</th>
                      <th>Carrier</th>
                      <th>Tracking / LR</th>
                      <th>Cartons</th>
                      <th>Dispatch Date</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shipments.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                          No shipments dispatched yet.
                        </td>
                      </tr>
                    ) : (
                      shipments.map((s) => (
                        <tr key={s.id}>
                          <td className="mono" style={{ fontWeight: 600 }}>{s.shipment_number}</td>
                          <td style={{ fontWeight: 500 }}>{s.carrier}</td>
                          <td className="mono">{s.tracking_number || '—'}</td>
                          <td>{s.carton_count}</td>
                          <td className="mono">{s.dispatch_date || 'Pending'}</td>
                          <td><StatusBadge status={s.status} /></td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Modals */}
      <CreateOrderModal
        isOpen={isCreateOrderOpen}
        onClose={() => setIsCreateOrderOpen(false)}
        onCreated={(newOrder) => {
          refreshData();
          setSelectedOrder(newOrder);
        }}
      />

      <CreateCustomerModal
        isOpen={isCreateCustOpen}
        onClose={() => setIsCreateCustOpen(false)}
        onCreated={() => refreshData()}
      />

      <OrderDetailModal
        order={selectedOrder}
        isOpen={Boolean(selectedOrder)}
        onClose={() => setSelectedOrder(null)}
        onUpdated={(updated) => {
          setSelectedOrder(updated);
          refreshData();
        }}
      />
    </div>
  );
}
