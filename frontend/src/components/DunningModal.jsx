import React, { useState, useEffect } from 'react'
import { X, AlertTriangle, CheckCircle2, Clock, RotateCcw, ShieldAlert, ArrowRight, Activity, Terminal } from 'lucide-react'
import { billingApi } from '../api'

export default function DunningModal({ invoice, userRole, onClose, onRefresh }) {
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)

  // Simulation inputs
  const [failureReason, setFailureReason] = useState('Insufficient funds / card declined (51)')
  const [showFailureForm, setShowFailureForm] = useState(false)
  const [retryOutcome, setRetryOutcome] = useState('succeeded')

  useEffect(() => {
    if (invoice?.id) {
      loadHistory()
    }
  }, [invoice?.id])

  async function loadHistory() {
    setLoadingHistory(true)
    setError(null)
    try {
      const data = await billingApi.getDunningHistory(invoice.id)
      setHistory(data)
    } catch (err) {
      setError(err.message || 'Failed to load dunning history.')
    } finally {
      setLoadingHistory(false)
    }
  }

  async function handleRecordFailure() {
    setActionLoading(true)
    setError(null)
    setSuccessMsg(null)
    try {
      await billingApi.recordPaymentFailure(invoice.id, failureReason)
      setSuccessMsg('Payment failure recorded. 7-day grace period started & retries scheduled.')
      setShowFailureForm(false)
      await loadHistory()
      if (onRefresh) onRefresh()
    } catch (err) {
      setError(err.message || 'Failed to record payment failure.')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleRetryPayment() {
    setActionLoading(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await billingApi.retryPayment(invoice.id, {
        simulate_outcome: retryOutcome,
        reason: retryOutcome === 'failed' ? 'Card expired or declined by issuer' : ''
      })
      if (retryOutcome === 'succeeded') {
        setSuccessMsg('Payment retry SUCCEEDED! Invoice marked PAID and subscription restored to ACTIVE.')
      } else {
        setSuccessMsg('Payment retry FAILED. Attempt logged in dunning audit history.')
      }
      await loadHistory()
      if (onRefresh) onRefresh()
    } catch (err) {
      setError(err.message || 'Payment retry failed.')
    } finally {
      setActionLoading(false)
    }
  }

  const isCustomer = userRole === 'Customer'
  const isFailed = invoice?.status === 'PAYMENT_FAILED'
  const isPaid = invoice?.status === 'PAID'
  const pendingAttempts = history.filter(h => h.status === 'PENDING')

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: '720px' }} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <ShieldAlert size={20} color="#fff"/>
              <h3>Smart Dunning & Grace-Period Engine</h3>
            </div>
            <p>Automated payment recovery lifecycle for Invoice #{invoice?.number}</p>
          </div>
          <button className="modal-close-btn" onClick={onClose}><X size={18}/></button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="alert-banner error">
              <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }}/>
              <div>
                <strong>Action Error</strong>
                <p style={{ marginTop: '2px' }}>{error}</p>
              </div>
            </div>
          )}

          {successMsg && (
            <div className="alert-banner success">
              <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: '2px' }}/>
              <div>
                <strong>Lifecycle Update</strong>
                <p style={{ marginTop: '2px' }}>{successMsg}</p>
              </div>
            </div>
          )}

          {/* Invoice & Entitlement Summary Card */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '1rem',
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
            marginBottom: '1.5rem'
          }}>
            <div>
              <small style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 600 }}>Invoice Status</small>
              <div style={{ marginTop: '0.3rem' }}>
                <span className={`status-badge ${invoice?.status?.toLowerCase()}`}>
                  {invoice?.status?.replace('_', ' ')}
                </span>
              </div>
            </div>

            <div>
              <small style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 600 }}>Total Amount</small>
              <h4 style={{ color: '#fff', fontSize: '1.2rem', marginTop: '0.2rem' }}>₹{invoice?.total}</h4>
            </div>

            <div>
              <small style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 600 }}>Subscription</small>
              <div style={{ color: '#fff', fontSize: '0.9rem', fontWeight: 600, marginTop: '0.2rem' }}>
                {invoice?.subscription_number || `SUB #${invoice?.subscription}`}
              </div>
              <small style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                {invoice?.plan_name}
              </small>
            </div>

            <div>
              <small style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 600 }}>Grace Period Window</small>
              <div style={{ color: invoice?.grace_period_end ? '#fff' : 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                {invoice?.grace_period_end
                  ? new Date(invoice.grace_period_end).toLocaleDateString()
                  : 'Not in dunning'}
              </div>
              {invoice?.first_failed_at && (
                <small style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>7 days from first fail</small>
              )}
            </div>
          </div>

          {/* Dunning Controls (Staff & Admin Only) */}
          {!isCustomer && !isPaid && (
            <div style={{
              backgroundColor: 'var(--bg-deep)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '1rem 1.25rem',
              marginBottom: '1.5rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>
                  Dunning Workflow Actions (Staff / Admin)
                </span>
              </div>

              {!isFailed ? (
                <div>
                  {!showFailureForm ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        This invoice is currently <b>{invoice?.status}</b>. You can simulate a payment gateway failure to enter the 7-day grace period.
                      </p>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setShowFailureForm(true)}
                        disabled={actionLoading}
                      >
                        Record Payment Failure
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        Failure Reason:
                      </label>
                      <input
                        type="text"
                        value={failureReason}
                        onChange={e => setFailureReason(e.target.value)}
                        style={{
                          background: 'var(--bg-surface)',
                          color: '#fff',
                          border: '1px solid var(--border-medium)',
                          padding: '0.5rem',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.85rem'
                        }}
                      />
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                        <button className="btn btn-outline btn-sm" onClick={() => setShowFailureForm(false)}>
                          Cancel
                        </button>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={handleRecordFailure}
                          disabled={actionLoading}
                        >
                          {actionLoading ? 'Recording...' : 'Confirm Gateway Failure'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Simulate Outcome:</span>
                    <select
                      value={retryOutcome}
                      onChange={e => setRetryOutcome(e.target.value)}
                      disabled={actionLoading}
                      style={{
                        background: 'var(--bg-surface)',
                        color: '#fff',
                        border: '1px solid var(--border-medium)',
                        padding: '0.35rem 0.6rem',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.8rem'
                      }}
                    >
                      <option value="succeeded">Success (Restore to Active)</option>
                      <option value="failed">Decline (Advance Dunning)</option>
                    </select>
                  </div>

                  <button
                    className="btn btn-primary btn-sm"
                    onClick={handleRetryPayment}
                    disabled={actionLoading || pendingAttempts.length === 0}
                  >
                    {actionLoading ? (
                      <>
                        <div className="spinner" style={{ borderTopColor: '#000' }}/>
                        Processing Retry...
                      </>
                    ) : (
                      <>
                        <RotateCcw size={14}/>
                        Execute Next Dunning Retry
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Dunning Attempts Audit History */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>
                Automated Retry Schedule & Audit Log
              </h4>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                3-Tier Strategy (Day 1, Day 3, Day 7)
              </span>
            </div>

            {loadingHistory ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                <div className="spinner"/>
                <span>Loading dunning attempts...</span>
              </div>
            ) : history.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '2.5rem',
                backgroundColor: 'var(--bg-deep)',
                border: '1px dashed var(--border-subtle)',
                borderRadius: 'var(--radius-md)'
              }}>
                <Clock size={32} color="var(--text-muted)" style={{ margin: '0 auto 0.75rem auto', display: 'block' }}/>
                <h5 style={{ color: '#fff', marginBottom: '0.25rem' }}>No Dunning Attempts Yet</h5>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  When an invoice payment fails, the engine automatically schedules 3 retry attempts across a 7-day grace period.
                </p>
              </div>
            ) : (
              <div className="dunning-timeline">
                {history.map((attempt) => {
                  const isDone = attempt.status === 'SUCCEEDED'
                  const isFailedAttempt = attempt.status === 'FAILED'
                  const isSkipped = attempt.status === 'SKIPPED'
                  const isPending = attempt.status === 'PENDING'

                  return (
                    <div
                      key={attempt.id}
                      className={`dunning-step ${isDone ? 'succeeded' : isFailedAttempt ? 'failed' : ''}`}
                    >
                      <div className="step-marker">
                        {attempt.attempt_number}
                      </div>

                      <div className="step-body">
                        <div className="step-header">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span className="step-title">
                              Attempt #{attempt.attempt_number}
                            </span>
                            <span className={`status-badge ${attempt.status?.toLowerCase()}`}>
                              {attempt.status}
                            </span>
                          </div>
                          <span className="step-time">
                            {attempt.attempt_date
                              ? `Executed ${new Date(attempt.attempt_date).toLocaleDateString()}`
                              : `Scheduled for ${new Date(attempt.scheduled_for).toLocaleDateString()}`}
                          </span>
                        </div>

                        {attempt.failure_reason && (
                          <div className="step-desc" style={{ color: '#e5e5e5', marginTop: '0.25rem' }}>
                            Reason: {attempt.failure_reason}
                          </div>
                        )}

                        {attempt.simulated_gateway_response && Object.keys(attempt.simulated_gateway_response).length > 0 && (
                          <div style={{
                            marginTop: '0.5rem',
                            backgroundColor: 'var(--bg-deep)',
                            padding: '0.5rem 0.75rem',
                            borderRadius: 'var(--radius-sm)',
                            border: '1px solid var(--border-subtle)',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.72rem',
                            color: 'var(--text-secondary)'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem', color: 'var(--text-muted)' }}>
                              <Terminal size={12}/> Gateway Response:
                            </div>
                            <code>{JSON.stringify(attempt.simulated_gateway_response)}</code>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
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
  )
}
