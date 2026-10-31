import React, { useState, useEffect } from 'react'
import {
  LayoutDashboard, Users, Package, Repeat, FileText, CreditCard,
  Tags, Settings, Search, Bell, ArrowUpRight, Clock3, CheckCircle2,
  Wallet, ShieldAlert, Calculator, RotateCcw, Sparkles, ExternalLink,
  Lock, UserCheck, Layers, Activity, Check, Plus, AlertCircle, RefreshCw
} from 'lucide-react'
import {
  authApi, subscriptionsApi, billingApi, catalogApi,
  customersApi, dashboardApi, storage
} from './api'
import ProrationModal from './components/ProrationModal'
import DunningModal from './components/DunningModal'

const DEMO_CREDENTIALS = {
  'Admin': { email: 'admin@brightloop.io', password: 'Password123!', role: 'ADMIN', label: 'Admin (Full Access)' },
  'Staff': { email: 'staff@brightloop.io', password: 'Password123!', role: 'STAFF', label: 'Staff (Billing Operations)' },
  'Customer (Acme)': { email: 'acme@enterprise.com', password: 'Password123!', role: 'CUSTOMER', label: 'Customer: Acme Corp' },
  'Customer (Globex)': { email: 'globex@startup.io', password: 'Password123!', role: 'CUSTOMER', label: 'Customer: Globex SaaS' }
}

export default function App() {
  const [activeTab, setActiveTab] = useState('Overview')
  const [currentRoleKey, setCurrentRoleKey] = useState('Admin')
  const [currentUser, setCurrentUser] = useState(storage.getUser() || { email: 'admin@brightloop.io', role: 'ADMIN' })
  const [isAuthenticating, setIsAuthenticating] = useState(false)
  const [apiConnected, setApiConnected] = useState(true)

  // Domain Data States
  const [dashboardData, setDashboardData] = useState(null)
  const [subscriptions, setSubscriptions] = useState([])
  const [invoices, setInvoices] = useState([])
  const [plans, setPlans] = useState([])
  const [customers, setCustomers] = useState([])
  const [payments, setPayments] = useState([])
  const [loadingData, setLoadingData] = useState(true)
  const [dataError, setDataError] = useState(null)

  // Modal States
  const [prorationSubscription, setProrationSubscription] = useState(null)
  const [dunningInvoice, setDunningInvoice] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  // Auto-login default admin on initial mount if no token
  useEffect(() => {
    initAuth()
  }, [])

  // Refetch data whenever role/user changes
  useEffect(() => {
    if (currentUser) {
      loadAllData()
    }
  }, [currentUser])

  async function initAuth() {
    setIsAuthenticating(true)
    try {
      if (!storage.getToken()) {
        await switchRole('Admin')
      } else {
        const me = await authApi.me().catch(() => null)
        if (me) {
          setCurrentUser(me)
        } else {
          await switchRole('Admin')
        }
      }
    } catch {
      setApiConnected(false)
    } finally {
      setIsAuthenticating(false)
    }
  }

  async function switchRole(roleKey) {
    setCurrentRoleKey(roleKey)
    setIsAuthenticating(true)
    setDataError(null)
    const creds = DEMO_CREDENTIALS[roleKey]
    if (!creds) return

    try {
      const authResult = await authApi.login(creds.email, creds.password)
      setCurrentUser(authResult.user)
      setApiConnected(true)
    } catch (err) {
      setDataError(`Failed to authenticate as ${roleKey}: ${err.message}`)
      setApiConnected(false)
    } finally {
      setIsAuthenticating(false)
    }
  }

  async function loadAllData() {
    setLoadingData(true)
    setDataError(null)
    try {
      const [subsRes, invsRes, plansRes, custRes, sumRes] = await Promise.allSettled([
        subscriptionsApi.list(),
        billingApi.listInvoices(),
        catalogApi.listPlans(),
        customersApi.list(),
        dashboardApi.getSummary().catch(() => null)
      ])

      if (subsRes.status === 'fulfilled') setSubscriptions(subsRes.value)
      if (invsRes.status === 'fulfilled') setInvoices(invsRes.value)
      if (plansRes.status === 'fulfilled') setPlans(plansRes.value)
      if (custRes.status === 'fulfilled') setCustomers(custRes.value)
      if (sumRes.status === 'fulfilled' && sumRes.value) setDashboardData(sumRes.value)

      setApiConnected(true)
    } catch (err) {
      setDataError(`API Synchronization Error: ${err.message}`)
    } finally {
      setLoadingData(false)
    }
  }

  // Filter handlers
  const filteredSubscriptions = subscriptions.filter(s => {
    const matchesSearch = s.number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.plan_name?.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'ALL' || s.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const filteredInvoices = invoices.filter(inv => {
    const matchesSearch = inv.number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.customer_name?.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'ALL' || inv.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="app-container">
      {/* ==================================================================
          STICKY TOPBAR (Recurly-Inspired SaaS Navbar)
          ================================================================== */}
      <header className="top-navbar">
        <div className="nav-left">
          <div className="brand-logo" onClick={() => setActiveTab('Overview')}>
            <div className="brand-icon">B</div>
            <div className="brand-text">
              <span className="brand-title">brightloop</span>
              <span className="brand-subtitle">SUBSCRIPTION SUITE</span>
            </div>
          </div>

          <nav className="nav-links">
            {['Overview', 'Subscriptions', 'Invoices', 'Plans', 'Customers', 'Platform Architecture'].map(tab => (
              <button
                key={tab}
                className={`nav-link-btn ${activeTab === tab ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(tab)
                  setStatusFilter('ALL')
                  setSearchQuery('')
                }}
              >
                {tab === 'Overview' && <LayoutDashboard size={15}/>}
                {tab === 'Subscriptions' && <Repeat size={15}/>}
                {tab === 'Invoices' && <FileText size={15}/>}
                {tab === 'Plans' && <Tags size={15}/>}
                {tab === 'Customers' && <Users size={15}/>}
                {tab === 'Platform Architecture' && <Layers size={15}/>}
                <span>{tab}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="nav-right">
          {/* Live Backend Connection Indicator */}
          <div className="system-status">
            <span className="status-dot"/>
            <span style={{ fontSize: '0.78rem', color: '#fff', fontWeight: 500 }}>
              {apiConnected ? 'DRF API Live' : 'Connecting...'}
            </span>
          </div>

          {/* Instant Role Switcher */}
          <div className="role-switcher">
            <span className="role-switcher-label">View As</span>
            <select
              value={currentRoleKey}
              onChange={e => switchRole(e.target.value)}
              disabled={isAuthenticating}
            >
              <option value="Admin">Admin (Full Access)</option>
              <option value="Staff">Staff (Operations)</option>
              <option value="Customer (Acme)">Customer: Acme Corp</option>
              <option value="Customer (Globex)">Customer: Globex SaaS</option>
            </select>
          </div>

          {/* User Profile Pill */}
          <div className="user-badge">
            <div className="user-avatar">
              {currentUser?.username ? currentUser.username.slice(0, 2).toUpperCase() : 'BL'}
            </div>
            <div>
              <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.75rem', lineHeight: 1.1 }}>
                {currentUser?.email || 'user@brightloop.io'}
              </div>
              <small style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>
                Role: {currentUser?.role || 'ADMIN'}
              </small>
            </div>
          </div>
        </div>
      </header>

      {/* ==================================================================
          RECURLY-INSPIRED HERO SECTION (Strict Monochrome)
          ================================================================== */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-top-eyebrow">
            <span/>
            ENTERPRISE RECURRING BILLING & SMART RECOVERY
          </div>

          <h1 className="hero-headline">
            Enterprise Subscription Management & Smart Dunning Engine
          </h1>

          <p className="hero-description">
            Maximize recurring revenue and eliminate involuntary churn. Powered by our mathematical mid-cycle proration engine, automated 7-day grace dunning retries, and role-enforced Django REST Framework architecture.
          </p>

          <div className="hero-actions">
            <button className="btn btn-primary" onClick={() => setActiveTab('Subscriptions')}>
              <Repeat size={16}/>
              Explore Subscriptions
            </button>
            <button className="btn btn-secondary" onClick={() => setActiveTab('Invoices')}>
              <ShieldAlert size={16}/>
              Test Smart Dunning
            </button>
            <button className="btn btn-outline" onClick={() => loadAllData()}>
              <RefreshCw size={14} className={loadingData ? 'spin' : ''}/>
              Sync Backend
            </button>
          </div>

          {/* Recurly Benefit Grids */}
          <div className="feature-grid">
            <div className="feature-card">
              <div className="feature-icon-wrap">
                <ShieldAlert size={20}/>
              </div>
              <h3 className="feature-title">Smart Dunning Engine</h3>
              <p className="feature-desc">
                Automated 7-day grace period with spaced retries on Day 1, 3, and 7. Prevents involuntary churn and restores active entitlements immediately upon successful retry.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrap">
                <Calculator size={20}/>
              </div>
              <h3 className="feature-title">Mathematical Proration</h3>
              <p className="feature-desc">
                Day-level accuracy on upgrades and downgrades with exact Decimal calculations, unused credit balances, and automated adjustment line items.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrap">
                <Lock size={20}/>
              </div>
              <h3 className="feature-title">Strict Role Hierarchy</h3>
              <p className="feature-desc">
                Enterprise security with Django DRF permissions: Admin and Staff manage all accounts, while customers access only their owned subscriptions and invoices.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrap">
                <Activity size={20}/>
              </div>
              <h3 className="feature-title">Audit-Ready Ledger</h3>
              <p className="feature-desc">
                Atomic database transitions via transaction.atomic(), immutable DunningAttempt audit logs, and double-entry aligned invoice itemization.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ==================================================================
          MAIN WORKSPACE CONTENT
          ================================================================== */}
      <main className="main-content">
        {dataError && (
          <div className="alert-banner error">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }}/>
            <div>
              <strong>Connection / Permission Notice</strong>
              <p style={{ marginTop: '2px' }}>{dataError}</p>
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------
            TAB 1: OVERVIEW DASHBOARD
            ---------------------------------------------------------------- */}
        {activeTab === 'Overview' && (
          <div>
            <div className="workspace-header">
              <div className="workspace-title-area">
                <h2>Executive Revenue & Subscription Health</h2>
                <p>Live metrics aggregated from your Django REST Framework database</p>
              </div>
              <div className="workspace-actions">
                <button className="btn btn-secondary btn-sm" onClick={() => loadAllData()}>
                  <RefreshCw size={14}/> Refresh
                </button>
              </div>
            </div>

            {/* Metrics Row */}
            <div className="metrics-row">
              <article className="metric-card">
                <div className="metric-card-top">
                  <span>Active Subscriptions</span>
                  <Repeat size={16}/>
                </div>
                <div className="metric-value">
                  {dashboardData ? dashboardData.active_subscriptions : subscriptions.filter(s => s.status === 'ACTIVE').length}
                </div>
                <div className="metric-footer">
                  <CheckCircle2 size={13} color="#fff"/>
                  <span>Current billing cycle</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-card-top">
                  <span>Payments Received</span>
                  <Wallet size={16}/>
                </div>
                <div className="metric-value">
                  ₹{dashboardData ? Number(dashboardData.payments_received).toLocaleString() : '149.00'}
                </div>
                <div className="metric-footer">
                  <span>Recorded payments settled</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-card-top">
                  <span>Total Invoiced</span>
                  <FileText size={16}/>
                </div>
                <div className="metric-value">
                  ₹{dashboardData ? Number(dashboardData.invoiced_total).toLocaleString() : '497.00'}
                </div>
                <div className="metric-footer">
                  <span>Across confirmed invoices</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-card-top">
                  <span>At-Risk / Overdue</span>
                  <ShieldAlert size={16}/>
                </div>
                <div className="metric-value">
                  {dashboardData ? dashboardData.overdue_invoices : invoices.filter(i => i.status === 'PAYMENT_FAILED').length}
                </div>
                <div className="metric-footer">
                  <span>Monitored in 7-day grace dunning</span>
                </div>
              </article>
            </div>

            {/* Subscriptions & Invoices Quick Look Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
              {/* Recent Subscriptions */}
              <div className="panel-container" style={{ margin: 0 }}>
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Active Subscriptions</h3>
                    <p className="panel-subtitle">Subscriptions in your current scope</p>
                  </div>
                  <button className="btn btn-outline btn-sm" onClick={() => setActiveTab('Subscriptions')}>
                    View All →
                  </button>
                </div>
                <div className="table-wrapper">
                  <table className="enterprise-table">
                    <thead>
                      <tr>
                        <th>Subscription</th>
                        <th>Customer</th>
                        <th>Plan</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {subscriptions.slice(0, 4).map(sub => (
                        <tr key={sub.id}>
                          <td><strong>{sub.number}</strong></td>
                          <td>{sub.customer_name || 'Customer'}</td>
                          <td>{sub.plan_name || 'Standard Plan'}</td>
                          <td>
                            <span className={`status-badge ${sub.status?.toLowerCase()}`}>
                              {sub.status?.replace('_', ' ')}
                            </span>
                          </td>
                          <td>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => setProrationSubscription(sub)}
                            >
                              <Calculator size={13}/>
                              Prorate
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Dunning Invoices */}
              <div className="panel-container" style={{ margin: 0 }}>
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Invoices & Dunning Status</h3>
                    <p className="panel-subtitle">Payment recovery monitoring</p>
                  </div>
                  <button className="btn btn-outline btn-sm" onClick={() => setActiveTab('Invoices')}>
                    View Invoices →
                  </button>
                </div>
                <div className="table-wrapper">
                  <table className="enterprise-table">
                    <thead>
                      <tr>
                        <th>Invoice</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Grace Expiry</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invoices.slice(0, 4).map(inv => (
                        <tr key={inv.id}>
                          <td><strong>{inv.number}</strong></td>
                          <td>₹{inv.total}</td>
                          <td>
                            <span className={`status-badge ${inv.status?.toLowerCase()}`}>
                              {inv.status?.replace('_', ' ')}
                            </span>
                          </td>
                          <td style={{ fontSize: '0.78rem' }}>
                            {inv.grace_period_end
                              ? new Date(inv.grace_period_end).toLocaleDateString()
                              : '—'}
                          </td>
                          <td>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => setDunningInvoice(inv)}
                            >
                              <ShieldAlert size={13}/>
                              Dunning
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------
            TAB 2: SUBSCRIPTIONS & MID-CYCLE PRORATION
            ---------------------------------------------------------------- */}
        {activeTab === 'Subscriptions' && (
          <div className="panel-container">
            <div className="panel-header">
              <div>
                <h3 className="panel-title">Subscription Management</h3>
                <p className="panel-subtitle">Manage customer lifecycles and execute mid-cycle prorated plan changes</p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-secondary btn-sm" onClick={() => loadAllData()}>
                  <RefreshCw size={13}/> Refresh
                </button>
              </div>
            </div>

            <div className="table-toolbar">
              <div className="search-input-wrap">
                <Search size={15} color="var(--text-muted)"/>
                <input
                  placeholder="Search subscriptions or plans..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                />
              </div>

              <div className="filter-pills">
                {['ALL', 'ACTIVE', 'IN_GRACE_PERIOD', 'SUSPENDED', 'CANCELED'].map(filter => (
                  <button
                    key={filter}
                    className={`filter-pill ${statusFilter === filter ? 'active' : ''}`}
                    onClick={() => setStatusFilter(filter)}
                  >
                    {filter.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div className="table-wrapper">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>SUBSCRIPTION</th>
                    <th>CUSTOMER</th>
                    <th>CURRENT PLAN</th>
                    <th>PRICE & CYCLE</th>
                    <th>NEXT BILLING</th>
                    <th>STATUS</th>
                    <th>PRORATION ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSubscriptions.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        No subscriptions found matching the current criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredSubscriptions.map(sub => (
                      <tr key={sub.id}>
                        <td><strong>{sub.number}</strong></td>
                        <td>
                          <div>{sub.customer_name || 'Customer'}</div>
                          <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{sub.customer_email}</small>
                        </td>
                        <td><strong>{sub.plan_name || 'Standard'}</strong></td>
                        <td>₹{sub.plan_price || '—'} / {sub.plan_interval?.toLowerCase() || 'mo'}</td>
                        <td>{sub.next_billing_date || '—'}</td>
                        <td>
                          <span className={`status-badge ${sub.status?.toLowerCase()}`}>
                            {sub.status?.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => setProrationSubscription(sub)}
                          >
                            <Calculator size={13}/>
                            Change Plan & Prorate
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------
            TAB 3: INVOICES & SMART DUNNING ENGINE
            ---------------------------------------------------------------- */}
        {activeTab === 'Invoices' && (
          <div className="panel-container">
            <div className="panel-header">
              <div>
                <h3 className="panel-title">Invoices & Dunning Engine</h3>
                <p className="panel-subtitle">Payment status, 7-day grace windows, and automated 3-tier retry audit history</p>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => loadAllData()}>
                <RefreshCw size={13}/> Refresh
              </button>
            </div>

            <div className="table-toolbar">
              <div className="search-input-wrap">
                <Search size={15} color="var(--text-muted)"/>
                <input
                  placeholder="Search invoices by number or customer..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                />
              </div>

              <div className="filter-pills">
                {['ALL', 'CONFIRMED', 'PAYMENT_FAILED', 'PAID', 'DRAFT'].map(filter => (
                  <button
                    key={filter}
                    className={`filter-pill ${statusFilter === filter ? 'active' : ''}`}
                    onClick={() => setStatusFilter(filter)}
                  >
                    {filter.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div className="table-wrapper">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>INVOICE NUMBER</th>
                    <th>CUSTOMER</th>
                    <th>ISSUE DATE</th>
                    <th>DUE DATE</th>
                    <th>TOTAL</th>
                    <th>STATUS</th>
                    <th>GRACE PERIOD & DUNNING</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredInvoices.length === 0 ? (
                    <tr>
                      <td colSpan={8} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        No invoices found matching criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredInvoices.map(inv => (
                      <tr key={inv.id}>
                        <td><strong>{inv.number}</strong></td>
                        <td>
                          <div>{inv.customer_name || 'Customer'}</div>
                          <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{inv.customer_email}</small>
                        </td>
                        <td>{inv.issue_date}</td>
                        <td>{inv.due_date}</td>
                        <td><strong>₹{inv.total}</strong></td>
                        <td>
                          <span className={`status-badge ${inv.status?.toLowerCase()}`}>
                            {inv.status?.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          {inv.status === 'PAYMENT_FAILED' ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                              <span style={{ fontSize: '0.75rem', color: '#fff', fontWeight: 600 }}>
                                Grace: {inv.grace_period_end ? new Date(inv.grace_period_end).toLocaleDateString() : 'Active'}
                              </span>
                              <small style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                                3 retries scheduled
                              </small>
                            </div>
                          ) : (
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Normal</span>
                          )}
                        </td>
                        <td>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => setDunningInvoice(inv)}
                          >
                            <ShieldAlert size={13}/>
                            Manage Dunning
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------
            TAB 4: PLANS & PRICING (Recurly-Inspired Tiers)
            ---------------------------------------------------------------- */}
        {activeTab === 'Plans' && (
          <div>
            <div className="workspace-header">
              <div className="workspace-title-area">
                <h2>Product Catalog & Subscription Plans</h2>
                <p>Enterprise SaaS subscription tiers configured with automated billing intervals</p>
              </div>
            </div>

            <div className="pricing-grid">
              {plans.map((p, idx) => {
                const isGrowth = p.name.includes('Growth')
                return (
                  <div key={p.id} className={`pricing-card ${isGrowth ? 'featured' : ''}`}>
                    {isGrowth && <div className="pricing-tier-badge">Most Popular</div>}
                    <div className="pricing-plan-name">{p.name}</div>
                    <div className="pricing-plan-desc">{p.description || 'Enterprise recurring plan with automatic billing and proration'}</div>
                    <div className="pricing-amount">
                      ₹{p.price}
                      <span className="pricing-interval">/ {p.interval?.toLowerCase()}</span>
                    </div>

                    <ul className="pricing-features-list">
                      <li className="pricing-feature-item">
                        <Check size={15} color="#fff"/>
                        <span>Automatic recurring invoicing</span>
                      </li>
                      <li className="pricing-feature-item">
                        <Check size={15} color="#fff"/>
                        <span>Smart Dunning & 7-Day Grace Engine</span>
                      </li>
                      <li className="pricing-feature-item">
                        <Check size={15} color="#fff"/>
                        <span>Mid-cycle mathematical proration</span>
                      </li>
                      <li className="pricing-feature-item">
                        <Check size={15} color="#fff"/>
                        <span>Allow pause: {p.allow_pause ? 'Yes' : 'No'}</span>
                      </li>
                    </ul>

                    <button
                      className={`btn ${isGrowth ? 'btn-primary' : 'btn-outline'}`}
                      onClick={() => setActiveTab('Subscriptions')}
                    >
                      Assign to Subscription
                    </button>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------
            TAB 5: CUSTOMERS & ENTITLEMENTS
            ---------------------------------------------------------------- */}
        {activeTab === 'Customers' && (
          <div className="panel-container">
            <div className="panel-header">
              <div>
                <h3 className="panel-title">Customer Directory</h3>
                <p className="panel-subtitle">Profiles, billing addresses, and role entitlement switches</p>
              </div>
            </div>

            <div className="table-wrapper">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>COMPANY NAME</th>
                    <th>USER EMAIL</th>
                    <th>PHONE</th>
                    <th>BILLING ADDRESS</th>
                    <th>TAX IDENTIFIER</th>
                    <th>ROLE SIMULATION</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map(c => (
                    <tr key={c.id}>
                      <td><strong>{c.company_name || 'Individual Customer'}</strong></td>
                      <td>{c.user_email || '—'}</td>
                      <td>{c.phone || '—'}</td>
                      <td style={{ maxWidth: '280px', fontSize: '0.8rem' }}>{c.billing_address || '—'}</td>
                      <td><code>{c.tax_identifier || '—'}</code></td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => {
                            if (c.user_email?.includes('acme')) switchRole('Customer (Acme)')
                            else if (c.user_email?.includes('globex')) switchRole('Customer (Globex)')
                            else alert(`Switched to test context for ${c.user_email}`)
                          }}
                        >
                          <UserCheck size={13}/>
                          Login As Customer
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------
            TAB 6: PLATFORM ARCHITECTURE (Full-Stack Map)
            ---------------------------------------------------------------- */}
        {activeTab === 'Platform Architecture' && (
          <div>
            <div className="workspace-header">
              <div className="workspace-title-area">
                <h2>Full-Stack System Architecture & Business Logic Engines</h2>
                <p>Clean architectural overview of Brightloop's Django REST Framework and React stack</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
              {/* Engine 1 Card */}
              <div className="panel-container" style={{ margin: 0, padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                  <div className="feature-icon-wrap" style={{ margin: 0 }}>
                    <ShieldAlert size={20}/>
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>1. Smart Dunning Engine</h3>
                    <small style={{ color: 'var(--text-muted)' }}>billing/services/dunning_service.py</small>
                  </div>
                </div>

                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  <p style={{ marginBottom: '0.75rem' }}>
                    <b>Lifecycle:</b> When an invoice fails payment, it is marked <code>PAYMENT_FAILED</code> and the subscription enters <code>IN_GRACE_PERIOD</code> for exactly 7 days.
                  </p>
                  <p style={{ marginBottom: '0.75rem' }}>
                    <b>Retry Logic:</b> Exactly 3 automated retries are scheduled for <b>Day 1</b>, <b>Day 3</b>, and <b>Day 7</b>. Each attempt creates an immutable audit row in <code>DunningAttempt</code>.
                  </p>
                  <p>
                    <b>Entitlement:</b> Payment success immediately restores subscription to <code>ACTIVE</code>. If all 3 attempts fail after 7 days, it automatically degrades to <code>SUSPENDED</code>.
                  </p>
                </div>
              </div>

              {/* Engine 2 Card */}
              <div className="panel-container" style={{ margin: 0, padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                  <div className="feature-icon-wrap" style={{ margin: 0 }}>
                    <Calculator size={20}/>
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>2. Mathematical Proration</h3>
                    <small style={{ color: 'var(--text-muted)' }}>subscriptions/services/proration_service.py</small>
                  </div>
                </div>

                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  <p style={{ marginBottom: '0.75rem' }}>
                    <b>Day-Level Formulas:</b>
                    <br/>
                    <code>Credit = OldPrice × (RemainingDays / TotalDays)</code>
                    <br/>
                    <code>NewCharge = NewPrice × (RemainingDays / TotalDays)</code>
                    <br/>
                    <code>Adjustment = NewCharge - Credit</code>
                  </p>
                  <p style={{ marginBottom: '0.75rem' }}>
                    <b>Atomic Upgrades & Downgrades:</b> Upgrades generate an immediate draft invoice with signed line items. Downgrades apply as deferred customer credit on the next billing invoice.
                  </p>
                  <p>
                    <b>Precision:</b> Uses Python <code>Decimal</code> with <code>ROUND_HALF_UP</code> to avoid floating-point drift.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ==================================================================
          INTERACTIVE MODALS
          ================================================================== */}
      {prorationSubscription && (
        <ProrationModal
          subscription={prorationSubscription}
          plans={plans}
          onClose={() => setProrationSubscription(null)}
          onSuccess={() => {
            loadAllData()
          }}
        />
      )}

      {dunningInvoice && (
        <DunningModal
          invoice={dunningInvoice}
          userRole={currentUser?.role === 'CUSTOMER' ? 'Customer' : 'Staff'}
          onClose={() => setDunningInvoice(null)}
          onRefresh={() => {
            loadAllData()
          }}
        />
      )}
    </div>
  )
}
