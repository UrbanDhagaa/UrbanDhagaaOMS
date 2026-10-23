import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertTriangle, ArrowRight, Clock, ShieldCheck, Lock } from 'lucide-react';
import StatusBadge from './StatusBadge';
import { api } from '../api/client';

export default function OrderDetailModal({ order, isOpen, onClose, onUpdated }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const isOrderCancelled = order?.order_status === 'Cancelled';
  const [statusDim, setStatusDim] = useState(isOrderCancelled ? 'design' : 'order');
  const [newStatusVal, setNewStatusVal] = useState('In Fulfilment');
  const [statusNote, setStatusNote] = useState('');
  // Payment amount capture
  const [paymentAmount, setPaymentAmount] = useState('');

  const dimensionOptions = {
    order: ['Draft', 'Confirmed', 'In Fulfilment', 'Partially Dispatched', 'Delivered', 'Closed'],
    payment: ['Unpaid', 'Partially Paid', 'Paid', 'Overdue'],
    design: ['Not Required', 'Pending', 'In Review', 'Changes Required', 'Approved'],
    procurement: ['Not Required', 'Not Ordered', 'Ordered', 'Partially Received', 'Received'],
    production: ['Not Started', 'In Progress', 'Quality Check', 'Rework', 'Completed'],
    delivery: ['Not Dispatched', 'Partially Dispatched', 'In Transit', 'Delivered'],
  };

  useEffect(() => {
    if (isOrderCancelled && (statusDim === 'payment' || statusDim === 'order')) {
      setStatusDim('design');
      setNewStatusVal(dimensionOptions['design'][0]);
      setPaymentAmount('');
    }
  }, [order?.order_status, isOrderCancelled]);

  if (!isOpen || !order) return null;

  async function handleConfirm() {
    setLoading(true);
    setError('');
    try {
      const updated = await api.confirmOrder(order.id, 'Confirmed from Admin Panel');
      onUpdated(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel() {
    const reason = prompt('Please enter mandatory reason for cancellation:');
    if (!reason) return;

    setLoading(true);
    setError('');
    try {
      const updated = await api.cancelOrder(order.id, reason);
      onUpdated(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdateStatus(e) {
    e.preventDefault();
    if (isOrderCancelled && statusDim === 'payment') {
      setError('Payment status and amount cannot be modified because the order is cancelled.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      // If payment status is being set to Partially Paid or Paid, also create a payment record
      const needsAmount = statusDim === 'payment' && (newStatusVal === 'Partially Paid' || newStatusVal === 'Paid');
      if (needsAmount && (!paymentAmount || Number(paymentAmount) <= 0)) {
        setError('Please enter a valid payment amount.');
        setLoading(false);
        return;
      }

      const updated = await api.updateOrderStatus(order.id, statusDim, newStatusVal, statusNote);

      // Record the actual payment receipt when marking Partially Paid or Paid
      if (needsAmount && Number(paymentAmount) > 0) {
        try {
          const today = new Date().toISOString().split('T')[0];
          await api.createPayment({
            customer_id: order.customer_id || order.customer?.id,
            amount: Number(paymentAmount),
            payment_method: 'NEFT',
            received_date: today,
            notes: `Payment for order ${order.order_number}`,
            allocations: [
              { order_id: order.id, allocated_amount: Number(paymentAmount) }
            ],
          });
        } catch (payErr) {
          console.warn('Payment record creation failed:', payErr.message);
        }
      }

      onUpdated(updated);
      setStatusNote('');
      setPaymentAmount('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card" style={{ maxWidth: '850px' }}>
        <div className="modal-header">
          <div>
            <div className="modal-title-row">
              <span className="mono" style={{ fontSize: 17, fontWeight: 700 }}>
                {order.order_number}
              </span>
              <StatusBadge status={order.order_status} />
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                ({order.category})
              </span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
              Customer: <strong>{order.customer?.company_name || 'Corporate Client'}</strong>
              {order.customer_po_reference && ` • PO: ${order.customer_po_reference}`}
            </p>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {error && (
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
              {error}
            </div>
          )}

          {/* 6-Dimensional Status Matrix */}
          <div className="status-matrix-grid">
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 4 }}>
                Payment {isOrderCancelled && <span style={{ fontSize: 10, color: '#991b1b', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 2 }}><Lock size={10} /> Locked</span>}
              </div>
              <div style={{ marginTop: 4 }}>
                <StatusBadge status={order.payment_status} />
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Design
              </div>
              <div style={{ marginTop: 4 }}>
                <StatusBadge status={order.design_status} />
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Procurement
              </div>
              <div style={{ marginTop: 4 }}>
                <StatusBadge status={order.procurement_status} />
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Production
              </div>
              <div style={{ marginTop: 4 }}>
                <StatusBadge status={order.production_status} />
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Delivery
              </div>
              <div style={{ marginTop: 4 }}>
                <StatusBadge status={order.delivery_status} />
              </div>
            </div>
          </div>

          {/* Primary Action Controls */}
          <div className="order-action-controls">
            <div className="order-action-buttons">
              {order.order_status === 'Draft' && (
                <button className="btn btn-primary btn-sm" onClick={handleConfirm} disabled={loading}>
                  <CheckCircle size={14} /> Confirm Order
                </button>
              )}

              {order.order_status !== 'Cancelled' && order.delivery_status !== 'Delivered' && (
                <button
                  className="btn btn-outline btn-sm"
                  onClick={handleCancel}
                  disabled={loading}
                  style={{ color: '#ef4444' }}
                >
                  <AlertTriangle size={14} /> Cancel Order
                </button>
              )}
            </div>

            {/* Dimension Transition Form */}
            <form
              onSubmit={handleUpdateStatus}
              className="status-transition-form"
            >
              <select
                className="select-filter"
                value={statusDim}
                onChange={(e) => {
                  setStatusDim(e.target.value);
                  setNewStatusVal(dimensionOptions[e.target.value][0]);
                  setPaymentAmount('');
                }}
              >
                {!isOrderCancelled && <option value="order">Order Status</option>}
                {!isOrderCancelled && <option value="payment">Payment Status</option>}
                <option value="design">Design Status</option>
                <option value="procurement">Procurement Status</option>
                <option value="production">Production Status</option>
                <option value="delivery">Delivery Status</option>
              </select>

              <select
                className="select-filter"
                value={newStatusVal}
                onChange={(e) => setNewStatusVal(e.target.value)}
              >
                {(dimensionOptions[statusDim] || []).map((st) => (
                  <option key={st} value={st}>
                    {st}
                  </option>
                ))}
              </select>

              {/* Payment amount input — only shown when setting Partially Paid or Paid */}
              {statusDim === 'payment' && (newStatusVal === 'Partially Paid' || newStatusVal === 'Paid') && (
                <input
                  type="number"
                  className="form-input payment-amount-input"
                  placeholder="Amount received (₹)"
                  min="1"
                  step="0.01"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  required
                />
              )}

              <button type="submit" className="btn btn-outline btn-sm" disabled={loading}>
                Update
              </button>
            </form>
          </div>

          {/* Items Table */}
          <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Order Items & Specifications</h4>
          <div className="table-responsive" style={{ marginBottom: 20 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Specifications</th>
                  <th>Qty</th>
                  <th>QC Accepted</th>
                  <th>Shipped</th>
                  <th>Rate</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {(order.items || []).map((it) => (
                  <tr key={it.id}>
                    <td style={{ fontWeight: 500 }}>{it.item_name}</td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {it.specifications ? JSON.stringify(it.specifications).replace(/[{}"]/g, ' ') : 'Standard'}
                    </td>
                    <td className="mono">{it.quantity}</td>
                    <td className="mono" style={{ color: it.accepted_qc_quantity > 0 ? '#166534' : 'inherit' }}>
                      {it.accepted_qc_quantity}
                    </td>
                    <td className="mono">{it.shipped_quantity}</td>
                    <td className="mono">₹{it.unit_price}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>₹{it.total_price.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Commercial Snapshot */}
          <div className="commercial-summary-banner" style={{ marginBottom: 24 }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Subtotal: </span>
              <span className="mono">₹{order.subtotal?.toLocaleString()}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>GST ({order.gst_rate}%): </span>
              <span className="mono">₹{order.gst_amount?.toLocaleString()}</span>
            </div>
            <div>
              <span style={{ fontWeight: 600 }}>Total Order Value: </span>
              <span className="mono" style={{ fontWeight: 700, fontSize: 15 }}>₹{order.total_amount?.toLocaleString()}</span>
            </div>
          </div>

          {/* Order Transition Event History */}
          <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Audit Trail & Lifecycle Events</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 180, overflowY: 'auto' }}>
            {(order.events || []).length === 0 ? (
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No recorded events yet.</p>
            ) : (
              (order.events || []).map((ev) => (
                <div
                  key={ev.id}
                  className="audit-event-row"
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                    <Clock size={14} style={{ color: 'var(--text-muted)' }} />
                    <span className="mono" style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                      {new Date(ev.created_at).toLocaleString('en-IN', { hour12: true })}
                    </span>
                  </div>
                  <span className="audit-event-type">{ev.event_type}</span>
                  <span className="audit-event-note">{ev.note || `${ev.from_status || 'Initial'} → ${ev.to_status}`}</span>
                  <span className="audit-event-user">{ev.created_by}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
