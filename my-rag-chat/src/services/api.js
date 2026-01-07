// // 
// /**
//  * Production-Ready API Service Layer
//  */

// // Configuration
// const API_BASE_URL = 'http://localhost:8001'; // Ensure this matches your FastAPI port

// // Helper: Standardized Error Handling
// const handleResponse = async (response) => {
//   if (!response.ok) {
//     const errorData = await response.json().catch(() => ({}));
//     throw new Error(errorData.detail || errorData.message || 'API Request Failed');
//   }
//   return response.json();
// };

// export const authAPI = {
//   // SECURITY NOTE: Switched to POST. Sending passwords in GET URL (query params) is unsafe.
//   login: async (email, password) => {
//     return fetch(`${API_BASE_URL}/users/login`, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({ email, password })
//     }).then(handleResponse);
//   },

//   signup: async (userData) => {
//     return fetch(`${API_BASE_URL}/users/create`, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({
//         name: userData.name,
//         email: userData.email,
//         password: userData.password // Renamed from 'password_hash' to match standard practices
//       })
//     }).then(handleResponse);
//   }
// };

// export const productAPI = {
//   // Fetch the dynamic list of bots based on Company ID
//   listByCompany: async (companyId) => {
//     return fetch(`${API_BASE_URL}/products/${companyId}`, {
//       method: 'GET',
//       headers: { 'Content-Type': 'application/json' }
//     }).then(handleResponse);
//   }
// };

// export const chatAPI = {
//   // The "One-Stop Shop" Endpoint
//   sendMessage: async ({ userId, productId, message }) => {
//     return fetch(`${API_BASE_URL}/chat`, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({
//         userId,
//         productId,
//         message
//       })
//     }).then(handleResponse);
//   },

//   // PERFORMANCE: The "Fire and Forget" Warmup
//   warmup: async (userId) => {
//     // We do NOT return this promise because we don't want the UI to wait for it.
//     fetch(`${API_BASE_URL}/warmup`, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({
//         userId,
//         productId: "default", 
//         message: "warmup_signal"
//       })
//     }).catch(err => console.warn("Warmup signal failed (Non-critical):", err));
//   }
// };

// // Simple LocalStorage Manager
// export const sessionManager = {
//   saveSession: (user) => {
//     localStorage.setItem('rag_session', JSON.stringify(user));
//   },
//   getSession: () => {
//     const session = localStorage.getItem('rag_session');
//     return session ? JSON.parse(session) : null;
//   },
//   clearSession: () => {
//     localStorage.removeItem('rag_session');
//     localStorage.removeItem('rag_history');
//     localStorage.removeItem('rag_sessions');
//   },
//   isAuthenticated: () => !!localStorage.getItem('rag_session')
// };






/**
 * Production-Ready API Service Layer
 * Handles all backend communication (Auth, Products, Chat, History)
 */

// Configuration
// Ensure this matches your FastAPI port (usually 8000 or 8001)
const API_BASE_URL = 'http://localhost:8001'; 

// HELPER: Standardized Error Handling
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || 'API Request Failed');
  }
  return response.json();
};

/**
 * 1. AUTHENTICATION API
 */
export const authAPI = {
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
        password: userData.password 
      })
    }).then(handleResponse);
  }
};

/**
 * 2. PRODUCT / CONTEXT API
 */
export const productAPI = {
  // Fetch the dynamic list of bots based on Company ID
  listByCompany: async (companyId) => {
    return fetch(`${API_BASE_URL}/products/${companyId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    }).then(handleResponse);
  }
};

/**
 * 3. CHAT / RAG API
 */
export const chatAPI = {
  // The "One-Stop Shop" Endpoint
  sendMessage: async ({ userId, productId, sessionId, message }) => {
    return fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId,
        productId,
        sessionId, // New in Phase 2 (Optional for first message)
        message
      })
    }).then(handleResponse);
  },

  // PERFORMANCE: The "Fire and Forget" Warmup
  warmup: async (userId) => {
    // We do NOT return this promise because we don't want the UI to wait.
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

/**
 * 4. HISTORY API (NEW - PHASE 2)
 */
export const historyAPI = {
  // Create a new empty thread (Optional - usually handled by chatAPI automatically)
  createSession: async (userId, productId) => {
    return fetch(`${API_BASE_URL}/history/session/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, product_id: productId })
    }).then(handleResponse);
  },

  // Get Sidebar List (Recent Conversations)
  getSessions: async (userId) => {
    return fetch(`${API_BASE_URL}/history/sessions/${userId}`).then(handleResponse);
  },

  // Get Chat Messages (Lazy Load / Infinite Scroll)
  getMessages: async (sessionId, limit = 20, skip = 0) => {
    return fetch(`${API_BASE_URL}/history/messages/${sessionId}?limit=${limit}&skip=${skip}`)
      .then(handleResponse);
  }
};

/**
 * 5. SESSION MANAGER (Browser Storage)
 */
export const sessionManager = {
  // Key updated to be generic so we don't leak data between users
  STORAGE_KEY: 'rag_current_user',

  saveSession: (user) => {
    localStorage.setItem('rag_current_user', JSON.stringify(user));
  },
  
  getSession: () => {
    const session = localStorage.getItem('rag_current_user');
    return session ? JSON.parse(session) : null;
  },
  
  clearSession: () => {
    localStorage.removeItem('rag_current_user');
    // Note: We deliberately do NOT clear 'rag_dark_mode' so theme preference persists
  },
  
  isAuthenticated: () => !!localStorage.getItem('rag_current_user')
};

export default {
  authAPI,
  productAPI,
  chatAPI,
  historyAPI,
  sessionManager
};








