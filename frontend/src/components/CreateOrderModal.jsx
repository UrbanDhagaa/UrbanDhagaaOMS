import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Building2 } from 'lucide-react';
import { api } from '../api/client';

export default function CreateOrderModal({ isOpen, onClose, onCreated }) {
  const [customers, setCustomers] = useState([]);
  const [companyName, setCompanyName] = useState('');
  const [category, setCategory] = useState('MER');
  const [priority, setPriority] = useState('MEDIUM');
  const [poRef, setPoRef] = useState('');
  const [reqDate, setReqDate] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState([
    {
      item_name: '',
      quantity: 50,
      unit_price: 450,
      specifications: { size: 'L', color: 'Navy', print: 'Front Embroidery' },
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadCustomers();
    }
  }, [isOpen]);

  async function loadCustomers() {
    try {
      const res = await api.getCustomers({ page_size: 100 });
      setCustomers(res.items || []);
    } catch (err) {
      console.error(err);
    }
  }

  function handleAddItem() {
    setItems([
      ...items,
      {
        item_name: '',
        quantity: 50,
        unit_price: 350,
        specifications: { size: 'Standard', color: '', branding: 'Custom Logo' },
      },
    ]);
  }

  function handleRemoveItem(index) {
    if (items.length === 1) return;
    setItems(items.filter((_, i) => i !== index));
  }

  function handleItemChange(index, field, value) {
    const updated = [...items];
    updated[index][field] = value;
    setItems(updated);
  }

  // Calculate live totals — MER = 5% GST, all others = 18%
  const gstRate = category === 'MER' ? 5 : 18;
  const subtotal = items.reduce((acc, it) => acc + (Number(it.quantity) || 0) * (Number(it.unit_price) || 0), 0);
  const gst = Math.round(subtotal * (gstRate / 100));
  const total = subtotal + gst;

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    const trimmedName = companyName.trim();
    if (!trimmedName) {
      setError('Please type the customer company name.');
      return;
    }

    for (const it of items) {
      if (!it.item_name.trim()) {
        setError('All line items must have a valid item name.');
        return;
      }
    }

    setLoading(true);
    try {
      // Find if an existing customer matches the typed company name
      const matched = customers.find(
        (c) => c.company_name.toLowerCase() === trimmedName.toLowerCase()
      );

      const payload = {
        customer_id: matched ? matched.id : null,
        company_name: trimmedName,
        category,
        priority,
        customer_po_reference: poRef || null,
        requested_delivery_date: reqDate || null,
        notes: notes || null,
        items: items.map((it) => ({
          item_name: it.item_name,
          quantity: Number(it.quantity),
          unit_price: Number(it.unit_price),
          specifications: it.specifications,
          tax_rate: gstRate,
        })),
      };

      const newOrder = await api.createOrder(payload);
      onCreated(newOrder);
      setCompanyName('');
      setPoRef('');
      setReqDate('');
      setNotes('');
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-card" style={{ maxWidth: '780px' }}>
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>Create New Corporate Order</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Generates canonical sequence ID (UD-YYYY-NNNNN)
            </p>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
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

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Customer Company *</span>
                  <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>Type manually or pick</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    list="customer-suggestions"
                    className="form-input"
                    placeholder="Type Company Name (e.g. Infosys, TCS, Zomato)..."
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    required
                    autoFocus
                  />
                  <datalist id="customer-suggestions">
                    {customers.map((c) => (
                      <option key={c.id} value={c.company_name}>
                        {c.customer_code} • {c.customer_type}
                      </option>
                    ))}
                  </datalist>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Category</label>
                <select className="form-select" value={category} onChange={(e) => setCategory(e.target.value)}>
                  <option value="MER">Corporate Merchandise (Apparel/Wearables)</option>
                  <option value="GFT">Corporate Gifting (Drinkware/Electronics)</option>
                  <option value="WKT">Welcome Kits & Hampers</option>
                  <option value="MIX">Mixed Bundles</option>
                </select>
              </div>
            </div>

            <div className="grid-3">
              <div className="form-group">
                <label className="form-label">Priority</label>
                <select className="form-select" value={priority} onChange={(e) => setPriority(e.target.value)}>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Customer PO Ref</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. PO-2026-TCS-01"
                  value={poRef}
                  onChange={(e) => setPoRef(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Target Delivery Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={reqDate}
                  onChange={(e) => setReqDate(e.target.value)}
                />
              </div>
            </div>

            <div style={{ marginTop: 12, marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Order Line Items</span>
              <button type="button" className="btn btn-outline btn-sm" onClick={handleAddItem}>
                <Plus size={14} /> Add Item
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {items.map((it, idx) => (
                <div
                  key={idx}
                  className="order-item-card"
                >
                  <div className="order-item-row">
                    <div className="order-item-field order-item-name">
                      <input
                        type="text"
                        className="form-input"
                        placeholder="Product Name (e.g. Premium Cotton Polo)"
                        value={it.item_name}
                        onChange={(e) => handleItemChange(idx, 'item_name', e.target.value)}
                        required
                      />
                    </div>
                    <div className="order-item-field order-item-qty">
                      <input
                        type="number"
                        className="form-input"
                        placeholder="Qty"
                        min="1"
                        value={it.quantity}
                        onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                        required
                      />
                    </div>
                    <div className="order-item-field order-item-rate">
                      <input
                        type="number"
                        className="form-input"
                        placeholder="Rate ₹"
                        min="0"
                        step="0.01"
                        value={it.unit_price}
                        onChange={(e) => handleItemChange(idx, 'unit_price', e.target.value)}
                        required
                      />
                    </div>
                    <button
                      type="button"
                      className="btn btn-outline btn-sm order-item-del"
                      onClick={() => handleRemoveItem(idx)}
                      disabled={items.length === 1}
                      style={{ color: '#ef4444' }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Commercial Summary Banner */}
            <div className="commercial-summary-banner">
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Subtotal: </span>
                <span className="mono" style={{ fontWeight: 600 }}>₹{subtotal.toLocaleString()}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>GST ({gstRate}%): </span>
                <span className="mono" style={{ fontWeight: 600 }}>₹{gst.toLocaleString()}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>Total: </span>
                <span className="mono" style={{ fontWeight: 700, fontSize: 15 }}>₹{total.toLocaleString()}</span>
              </div>
            </div>

            <div className="form-group" style={{ marginTop: 16 }}>
              <label className="form-label">Internal Operations / Production Notes</label>
              <textarea
                className="form-textarea"
                rows="2"
                placeholder="Specific packaging, dispatch or custom branding requirements..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
