// 
/**
 * Production-Ready API Service Layer
 */

// Configuration
const API_BASE_URL = 'http://localhost:8001'; // Ensure this matches your FastAPI port

// Helper: Standardized Error Handling
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || 'API Request Failed');
  }
  return response.json();
};

export const authAPI = {
  // SECURITY NOTE: Switched to POST. Sending passwords in GET URL (query params) is unsafe.
  login: async (email, password) => {
    return fetch(`${API_BASE_URL}/users/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    }).then(handleResponse);
  },

  signup: async (userData) => {
    return fetch(`${API_BASE_URL}/users/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: userData.name,
        email: userData.email,
        password: userData.password // Renamed from 'password_hash' to match standard practices
      })
    }).then(handleResponse);
  }
};

export const productAPI = {
  // Fetch the dynamic list of bots based on Company ID
  listByCompany: async (companyId) => {
    return fetch(`${API_BASE_URL}/products/${companyId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    }).then(handleResponse);
  }
};

export const chatAPI = {
  // The "One-Stop Shop" Endpoint
  sendMessage: async ({ userId, productId, message }) => {
    return fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId,
        productId,
        message
      })
    }).then(handleResponse);
  },

  // PERFORMANCE: The "Fire and Forget" Warmup
  warmup: async (userId) => {
    // We do NOT return this promise because we don't want the UI to wait for it.
    fetch(`${API_BASE_URL}/warmup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId,
        productId: "default", 
        message: "warmup_signal"
      })
    }).catch(err => console.warn("Warmup signal failed (Non-critical):", err));
  }
};

// Simple LocalStorage Manager
export const sessionManager = {
  saveSession: (user) => {
    localStorage.setItem('rag_session', JSON.stringify(user));
  },
  getSession: () => {
    const session = localStorage.getItem('rag_session');
    return session ? JSON.parse(session) : null;
  },
  clearSession: () => {
    localStorage.removeItem('rag_session');
    localStorage.removeItem('rag_history');
    localStorage.removeItem('rag_sessions');
  },
  isAuthenticated: () => !!localStorage.getItem('rag_session')
};