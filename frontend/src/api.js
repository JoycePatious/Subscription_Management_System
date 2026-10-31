/**
 * Brightloop API Client & Service Wrappers
 * Fully wired to Django & Django REST Framework (DRF) backend
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'

export const storage = {
  getToken: () => localStorage.getItem('bl_access_token'),
  setToken: (token) => {
    if (token) localStorage.setItem('bl_access_token', token)
    else localStorage.removeItem('bl_access_token')
  },
  getRefreshToken: () => localStorage.getItem('bl_refresh_token'),
  setRefreshToken: (refresh) => {
    if (refresh) localStorage.setItem('bl_refresh_token', refresh)
    else localStorage.removeItem('bl_refresh_token')
  },
  getUser: () => {
    try {
      const u = localStorage.getItem('bl_user')
      return u ? JSON.parse(u) : null
    } catch {
      return null
    }
  },
  setUser: (user) => {
    if (user) localStorage.setItem('bl_user', JSON.stringify(user))
    else localStorage.removeItem('bl_user')
  },
  clear: () => {
    localStorage.removeItem('bl_access_token')
    localStorage.removeItem('bl_refresh_token')
    localStorage.removeItem('bl_user')
  }
}

/**
 * Core HTTP fetch wrapper with JWT Bearer authentication and automatic error handling
 */
export async function apiRequest(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`
  const token = storage.getToken()

  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(options.headers || {})
  }

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const config = {
    ...options,
    headers
  }

  let response
  try {
    response = await fetch(url, config)
  } catch (netErr) {
    throw new Error(`Network error connecting to backend: ${netErr.message}. Ensure Django server is running on port 8000.`)
  }

  // Handle Token Expiration with Automatic Refresh
  if (response.status === 401 && storage.getRefreshToken() && !options._isRetry) {
    try {
      const refreshRes = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: storage.getRefreshToken() })
      })

      if (refreshRes.ok) {
        const refreshData = await refreshRes.json()
        storage.setToken(refreshData.access)
        return apiRequest(endpoint, { ...options, _isRetry: true })
      } else {
        storage.clear()
      }
    } catch {
      storage.clear()
    }
  }

  let data = null
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    data = await response.json().catch(() => null)
  } else {
    data = await response.text().catch(() => null)
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    if (data && typeof data === 'object') {
      if (data.detail) {
        message = data.detail
      } else if (data.reason) {
        message = data.reason
      } else if (Array.isArray(data.non_field_errors)) {
        message = data.non_field_errors.join(' ')
      } else {
        const fieldErrors = Object.entries(data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(' ') : v}`)
          .join(' | ')
        if (fieldErrors) message = fieldErrors
      }
    } else if (typeof data === 'string' && data.length > 0) {
      message = data.slice(0, 150)
    }
    const error = new Error(message)
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

/**
 * Normalizes DRF paginated responses into clean arrays
 */
export function unwrapResults(data) {
  if (!data) return []
  if (Array.isArray(data)) return data
  if (Array.isArray(data.results)) return data.results
  return []
}

// ----------------------------------------------------------------------
// Dedicated Domain Services
// ----------------------------------------------------------------------

export const authApi = {
  login: async (email, password) => {
    const data = await apiRequest('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    })
    if (data.access) storage.setToken(data.access)
    if (data.refresh) storage.setRefreshToken(data.refresh)
    if (data.user) storage.setUser(data.user)
    return data
  },
  me: async () => {
    const data = await apiRequest('/auth/me/')
    if (data) storage.setUser(data)
    return data
  },
  register: async (userData) => {
    return apiRequest('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData)
    })
  },
  logout: () => {
    storage.clear()
  }
}

export const subscriptionsApi = {
  list: async () => {
    const res = await apiRequest('/subscriptions/')
    return unwrapResults(res)
  },
  get: async (id) => {
    return apiRequest(`/subscriptions/${id}/`)
  },
  previewProration: async (subscriptionId, newPlanId) => {
    return apiRequest(`/subscriptions/${subscriptionId}/preview-proration/`, {
      method: 'POST',
      body: JSON.stringify({ new_plan_id: newPlanId })
    })
  },
  changePlan: async (subscriptionId, newPlanId, immediateInvoice = true) => {
    return apiRequest(`/subscriptions/${subscriptionId}/change-plan/`, {
      method: 'POST',
      body: JSON.stringify({
        new_plan_id: newPlanId,
        immediate_invoice: immediateInvoice
      })
    })
  },
  create: async (data) => {
    return apiRequest('/subscriptions/', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }
}

export const billingApi = {
  listInvoices: async () => {
    const res = await apiRequest('/billing/invoices/')
    return unwrapResults(res)
  },
  getInvoice: async (id) => {
    return apiRequest(`/billing/invoices/${id}/`)
  },
  recordPaymentFailure: async (invoiceId, reason) => {
    return apiRequest(`/billing/invoices/${invoiceId}/record-failure/`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    })
  },
  retryPayment: async (invoiceId, options = {}) => {
    // options can include simulate_outcome: 'succeeded' | 'failed'
    return apiRequest(`/billing/invoices/${invoiceId}/retry-payment/`, {
      method: 'POST',
      body: JSON.stringify(options)
    })
  },
  getDunningHistory: async (invoiceId) => {
    return apiRequest(`/billing/invoices/${invoiceId}/dunning-history/`)
  },
  listPayments: async () => {
    const res = await apiRequest('/payments/')
    return unwrapResults(res)
  },
  recordPayment: async (data) => {
    return apiRequest('/payments/', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }
}

export const catalogApi = {
  listPlans: async () => {
    const res = await apiRequest('/plans/')
    return unwrapResults(res)
  },
  listProducts: async () => {
    const res = await apiRequest('/products/')
    return unwrapResults(res)
  }
}

export const customersApi = {
  list: async () => {
    const res = await apiRequest('/customers/')
    return unwrapResults(res)
  },
  create: async (customerData) => {
    return apiRequest('/customers/', {
      method: 'POST',
      body: JSON.stringify(customerData)
    })
  }
}

export const dashboardApi = {
  getSummary: async () => {
    return apiRequest('/dashboard/summary/')
  }
}

export const salesApi = {
  listQuotations: async () => {
    const res = await apiRequest('/quotations/')
    return unwrapResults(res)
  }
}

export const settingsApi = {
  listTaxes: async () => {
    const res = await apiRequest('/taxes/')
    return unwrapResults(res)
  },
  listDiscounts: async () => {
    const res = await apiRequest('/discounts/')
    return unwrapResults(res)
  }
}
