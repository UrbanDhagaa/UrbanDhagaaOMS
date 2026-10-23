import React, { useState } from 'react';
import { X } from 'lucide-react';
import { api } from '../api/client';

export default function CreateCustomerModal({ isOpen, onClose, onCreated }) {
  const [companyName, setCompanyName] = useState('');
  const [gstin, setGstin] = useState('');
  const [customerType, setCustomerType] = useState('CORPORATE');
  const [paymentTerms, setPaymentTerms] = useState('50_ADVANCE_50_DISPATCH');
  const [creditLimit, setCreditLimit] = useState(0);

  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [contactDesignation, setContactDesignation] = useState('');

  const [addressLine, setAddressLine] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [postalCode, setPostalCode] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        company_name: companyName,
        customer_type: customerType,
        gstin: gstin || null,
        payment_terms: paymentTerms,
        credit_limit: Number(creditLimit) || 0,
        contacts: contactName
          ? [
              {
                name: contactName,
                email: contactEmail || 'info@company.com',
                phone: contactPhone || '9999999999',
                designation: contactDesignation,
                is_primary: true,
              },
            ]
          : [],
        addresses: addressLine
          ? [
              {
                address_type: 'BILLING',
                address_line1: addressLine,
                city: city || 'Mumbai',
                state: state || 'Maharashtra',
                postal_code: postalCode || '400001',
                country: 'India',
                is_default: true,
              },
            ]
          : [],
      };

      const newCust = await api.createCustomer(payload);
      onCreated(newCust);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card" style={{ maxWidth: '640px' }}>
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>Add Corporate Client</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Registers client with reusable addresses and contacts
            </p>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
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
                <label className="form-label">Legal Company Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Infosys Limited"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">GSTIN (Optional)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="27AAAAA0000A1Z5"
                  value={gstin}
                  onChange={(e) => setGstin(e.target.value.toUpperCase())}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Payment Terms</label>
              <select className="form-select" value={paymentTerms} onChange={(e) => setPaymentTerms(e.target.value)}>
                <option value="100_ADVANCE">100% Advance Payment</option>
                <option value="50_ADVANCE_50_DISPATCH">50% Advance / 50% Before Dispatch</option>
                <option value="NET_15">Net 15 Days Credit</option>
                <option value="NET_30">Net 30 Days Credit</option>
              </select>
            </div>

            <h4 style={{ fontSize: 13, fontWeight: 600, marginTop: 12, marginBottom: 8 }}>Primary Contact</h4>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Contact Person Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Priya Sharma"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Contact Phone</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="+91 9876543210"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Contact Email</label>
              <input
                type="email"
                className="form-input"
                placeholder="priya.sharma@company.com"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save Customer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
