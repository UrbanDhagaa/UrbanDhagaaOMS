import React from 'react';

export default function StatusBadge({ status, type = 'order' }) {
  if (!status) return null;

  const normalized = status.toLowerCase();

  let styleClass = 'status-draft';
  if (
    normalized === 'confirmed' ||
    normalized === 'paid' ||
    normalized === 'approved' ||
    normalized === 'completed'
  ) {
    styleClass = 'status-confirmed';
  } else if (
    normalized === 'in fulfilment' ||
    normalized === 'in transit' ||
    normalized === 'in review' ||
    normalized === 'in progress' ||
    normalized === 'ordered'
  ) {
    styleClass = 'status-fulfilment';
  } else if (normalized === 'delivered') {
    styleClass = 'status-delivered';
  } else if (
    normalized === 'cancelled' ||
    normalized === 'failed' ||
    normalized === 'rejected' ||
    normalized === 'changes required'
  ) {
    styleClass = 'status-cancelled';
  } else if (
    normalized === 'partially paid' ||
    normalized === 'partially dispatched' ||
    normalized === 'partially received' ||
    normalized === 'quality check' ||
    normalized === 'rework'
  ) {
    styleClass = 'status-warning';
  } else if (normalized === 'unpaid') {
    styleClass = 'status-unpaid';
  }

  return (
    <span className={`status-pill ${styleClass}`}>
      <span className="pill-dot" />
      {status}
    </span>
  );
}
