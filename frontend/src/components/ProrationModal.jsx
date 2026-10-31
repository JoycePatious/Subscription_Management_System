import React, { useState, useEffect } from 'react'
import { X, ArrowRight, Calculator, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react'
import { subscriptionsApi } from '../api'

export default function ProrationModal({ subscription, plans, onClose, onSuccess }) {
  const [targetPlanId, setTargetPlanId] = useState('')
  const [immediateInvoice, setImmediateInvoice] = useState(true)
  const [preview, setPreview] = useState(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [executingChange, setExecutingChange] = useState(false)
  const [error, setError] = useState(null)
  const [successInfo, setSuccessInfo] = useState(null)

  // Filter out current plan from targets
  const availablePlans = plans.filter(p => p.id !== subscription?.plan)

  useEffect(() => {
    if (availablePlans.length > 0 && !targetPlanId) {
      setTargetPlanId(availablePlans[0].id)
    }
  }, [availablePlans, targetPlanId])

  useEffect(() => {
    if (!subscription || !targetPlanId) return
    loadProrationPreview(targetPlanId)
  }, [subscription, targetPlanId])

  async function loadProrationPreview(planId) {
    if (!planId) return
    setError(null)
    setLoadingPreview(true)
    try {
      const data = await subscriptionsApi.previewProration(subscription.id, planId)
      setPreview(data)
    } catch (err) {
      setError(err.message || 'Failed to calculate proration preview.')
      setPreview(null)
    } finally {
      setLoadingPreview(false)
    }
  }

  async function handleApplyChange() {
    if (!targetPlanId) return
    setError(null)
    setExecutingChange(true)
    try {
      const result = await subscriptionsApi.changePlan(subscription.id, targetPlanId, immediateInvoice)
      setSuccessInfo(result)
      if (onSuccess) onSuccess(result)
    } catch (err) {
      setError(err.message || 'Failed to apply plan change.')
    } finally {
      setExecutingChange(false)
    }
  }

  const isSuspendedOrCanceled = ['SUSPENDED', 'CANCELED'].includes(subscription?.status)

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <h3>Mid-Cycle Plan Change & Proration</h3>
            <p>Day-level mathematical proration for Subscription #{subscription?.number}</p>
          </div>
          <button className="modal-close-btn" onClick={onClose}><X size={18}/></button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="alert-banner error">
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }}/>
              <div>
                <strong>Plan Change Blocked</strong>
                <p style={{ marginTop: '2px' }}>{error}</p>
              </div>
            </div>
          )}

          {successInfo ? (
            <div className="alert-banner success" style={{ flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <CheckCircle2 size={20}/>
                <strong>Plan Change Applied Successfully!</strong>
              </div>
              <p style={{ fontSize: '0.85rem' }}>
                Subscription <b>{subscription?.number}</b> is now on <b>{successInfo.proration?.new_plan}</b>.
                Adjustment invoice <b>{successInfo.invoice?.number}</b> was generated.
              </p>
              <div className="math-breakdown-card" style={{ width: '100%', margin: 0 }}>
                <div className="math-row">
                  <span>Net Adjustment Settled:</span>
                  <span className="formula-val">₹{successInfo.proration?.adjustment}</span>
                </div>
                <div className="math-row">
                  <span>Invoice Status:</span>
                  <span className="formula-val">{successInfo.invoice?.status}</span>
                </div>
              </div>
            </div>
          ) : (
            <>
              {isSuspendedOrCanceled && (
                <div className="alert-banner error">
                  <AlertCircle size={18}/>
                  <div>
                    <strong>Cannot change plan</strong>
                    <p>This subscription has status <b>{subscription?.status}</b>. Suspended or canceled subscriptions cannot change plans.</p>
                  </div>
                </div>
              )}

              {/* Current Plan vs Target Plan */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '1rem', alignItems: 'center', marginBottom: '1.25rem' }}>
                <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <small style={{ color: 'var(--text-muted)', textTransform: 'uppercase', fontSize: '0.7rem', fontWeight: 600 }}>Current Plan</small>
                  <h4 style={{ color: '#fff', fontSize: '1.05rem', margin: '0.25rem 0' }}>{subscription?.plan_name || 'Current'}</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>₹{subscription?.plan_price || '—'} / {subscription?.plan_interval?.toLowerCase() || 'month'}</p>
                </div>

                <div style={{ color: 'var(--text-muted)', display: 'flex', justifyContent: 'center' }}>
                  <ArrowRight size={22}/>
                </div>

                <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <small style={{ color: 'var(--text-muted)', textTransform: 'uppercase', fontSize: '0.7rem', fontWeight: 600 }}>Target Plan</small>
                  <select
                    value={targetPlanId}
                    onChange={e => setTargetPlanId(e.target.value)}
                    disabled={isSuspendedOrCanceled || executingChange}
                    style={{
                      width: '100%',
                      background: 'var(--bg-deep)',
                      color: '#fff',
                      border: '1px solid var(--border-medium)',
                      padding: '0.45rem',
                      borderRadius: 'var(--radius-sm)',
                      marginTop: '0.25rem',
                      fontSize: '0.85rem',
                      cursor: 'pointer'
                    }}
                  >
                    {availablePlans.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} (₹{p.price} / {p.interval})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Calculation Preview */}
              {loadingPreview ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', padding: '2rem', color: 'var(--text-secondary)' }}>
                  <div className="spinner"/>
                  <span>Calculating exact day-level proration...</span>
                </div>
              ) : preview ? (
                <div className="math-breakdown-card">
                  <div className="math-title">
                    <span>Proration Math Breakdown</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Effective: {preview.effective_date}
                    </span>
                  </div>

                  <div className="math-row">
                    <span>Cycle Range:</span>
                    <span className="formula-val">{preview.cycle_start} → {preview.cycle_end}</span>
                  </div>

                  <div className="math-row">
                    <span>Cycle Days (Total / Used / Remaining):</span>
                    <span className="formula-val">{preview.total_days} total · {preview.used_days} used · {preview.remaining_days} remaining</span>
                  </div>

                  <div className="math-row">
                    <span>Unused Credit ({preview.old_plan}):</span>
                    <span className="formula-val" style={{ color: '#e5e5e5' }}>- ₹{preview.credit}</span>
                  </div>

                  <div className="math-row">
                    <span>Prorated Charge ({preview.new_plan}):</span>
                    <span className="formula-val" style={{ color: '#ffffff' }}>+ ₹{preview.new_charge}</span>
                  </div>

                  <div className="math-row">
                    <span>
                      {Number(preview.adjustment) >= 0 ? 'Net Upgrade Charge:' : 'Net Downgrade Credit:'}
                    </span>
                    <span className="formula-val" style={{ fontSize: '1.15rem' }}>
                      ₹{preview.adjustment}
                    </span>
                  </div>

                  <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {Number(preview.adjustment) >= 0
                      ? 'Upgrade creates an adjustment invoice for the prorated difference.'
                      : 'Downgrade creates an account credit / deferred discount line applied on next cycle.'}
                  </div>
                </div>
              ) : null}

              {/* Invoice timing toggle */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 0' }}>
                <input
                  type="checkbox"
                  id="immediateInv"
                  checked={immediateInvoice}
                  onChange={e => setImmediateInvoice(e.target.checked)}
                  disabled={isSuspendedOrCanceled || executingChange}
                  style={{ accentColor: '#ffffff', width: '16px', height: '16px', cursor: 'pointer' }}
                />
                <label htmlFor="immediateInv" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  Generate immediate adjustment invoice (due today)
                </label>
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onClose}>
            {successInfo ? 'Close' : 'Cancel'}
          </button>
          {!successInfo && (
            <button
              className="btn btn-primary"
              disabled={isSuspendedOrCanceled || !preview || executingChange || loadingPreview}
              onClick={handleApplyChange}
            >
              {executingChange ? (
                <>
                  <div className="spinner" style={{ borderTopColor: '#000' }}/>
                  Applying Change...
                </>
              ) : (
                'Confirm Plan Change'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
