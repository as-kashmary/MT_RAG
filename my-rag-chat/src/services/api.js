/**
 * API Service Layer
 * Handles all backend communication with proper error handling and request management
 */

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
const API_TIMEOUT = 30000; // 30 seconds

// Custom fetch with timeout and error handling
const fetchWithTimeout = async (url, options = {}) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    // Handle non-JSON responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        message: response.statusText || 'Unknown error',
      }));
      const error = new Error(errorData.detail || errorData.message || 'API request failed');
      error.status = response.status;
      error.data = errorData;
      throw error;
    }

    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - please try again');
    }
    throw error;
  }
};

/**
 * User Authentication API
 */
export const authAPI = {
  /**
   * Sign up a new user
   * @param {Object} userData - User data { name, email, password }
   * @returns {Promise<Object>} - Response with success status
   */
  signup: async (userData) => {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/users/create`, {
        method: 'POST',
        body: JSON.stringify({
          name: userData.name,
          email: userData.email,
          password_hash: userData.password, // Backend expects password_hash
        }),
      });

      const data = await response.json();
      return {
        success: true,
        data,
        message: data.message || 'Signup successful',
      };
    } catch (error) {
      console.error('Signup error:', error);
      return {
        success: false,
        message: error.message || 'Failed to create account',
        error,
      };
    }
  },

  /**
   * Log in an existing user
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} - Response with user_id on success
   */
  login: async (email, password) => {
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/users/login?email=${encodeURIComponent(email)}&password_hash=${encodeURIComponent(password)}`,
        {
          method: 'GET',
        }
      );

      const userId = await response.text();
      return {
        success: true,
        userId: userId.trim(), // Remove any whitespace
        message: 'Login successful',
      };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        message: error.message || 'Failed to log in',
        error,
      };
    }
  },
};

/**
 * Chat/Query API
 * Note: These are placeholder for future implementation
 */
export const chatAPI = {
  /**
   * Send a query and get context
   * @param {string} userId - User ID
   * @param {string} query - Query text
   * @param {string} product - Product context
   * @returns {Promise<Object>} - Context for the query
   */
  getContext: async (userId, query, product) => {
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/context_generation?user_id=${encodeURIComponent(userId)}&query=${encodeURIComponent(query)}`,
        {
          method: 'GET',
        }
      );

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('Context generation error:', error);
      return {
        success: false,
        message: error.message || 'Failed to generate context',
        error,
      };
    }
  },

  /**
   * Generate response based on context
   * @param {string} userId - User ID
   * @returns {Promise<Object>} - Generated response
   */
  getResponse: async (userId) => {
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/response_generation?user_id=${encodeURIComponent(userId)}`,
        {
          method: 'GET',
        }
      );

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('Response generation error:', error);
      return {
        success: false,
        message: error.message || 'Failed to generate response',
        error,
      };
    }
  },
};

/**
 * User Session Management
 */
export const sessionManager = {
  // Session keys for localStorage
  STORAGE_KEYS: {
    USER_ID: 'rag_user_id',
    USER_NAME: 'rag_user_name',
    USER_EMAIL: 'rag_user_email',
    SESSION_TOKEN: 'rag_session_token',
    SESSION_CREATED: 'rag_session_created',
  },

  /**
   * Save user session to localStorage
   * @param {Object} userData - User data to save { userId, name, email }
   */
  saveSession: (userData) => {
    try {
      const sessionData = {
        userId: userData.userId,
        name: userData.name || 'User',
        email: userData.email,
        createdAt: new Date().toISOString(),
      };

      localStorage.setItem(sessionManager.STORAGE_KEYS.USER_ID, sessionData.userId);
      localStorage.setItem(sessionManager.STORAGE_KEYS.USER_NAME, sessionData.name);
      localStorage.setItem(sessionManager.STORAGE_KEYS.USER_EMAIL, sessionData.email);
      localStorage.setItem(sessionManager.STORAGE_KEYS.SESSION_CREATED, sessionData.createdAt);

      console.log('Session saved:', sessionData);
      return true;
    } catch (error) {
      console.error('Error saving session:', error);
      return false;
    }
  },

  /**
   * Get current user session
   * @returns {Object|null} - User session data or null if not logged in
   */
  getSession: () => {
    try {
      const userId = localStorage.getItem(sessionManager.STORAGE_KEYS.USER_ID);
      if (!userId) return null;

      return {
        userId,
        name: localStorage.getItem(sessionManager.STORAGE_KEYS.USER_NAME),
        email: localStorage.getItem(sessionManager.STORAGE_KEYS.USER_EMAIL),
        createdAt: localStorage.getItem(sessionManager.STORAGE_KEYS.SESSION_CREATED),
      };
    } catch (error) {
      console.error('Error retrieving session:', error);
      return null;
    }
  },

  /**
   * Clear user session
   */
  clearSession: () => {
    try {
      Object.values(sessionManager.STORAGE_KEYS).forEach((key) => {
        localStorage.removeItem(key);
      });
      console.log('Session cleared');
      return true;
    } catch (error) {
      console.error('Error clearing session:', error);
      return false;
    }
  },

  /**
   * Check if user is authenticated
   * @returns {boolean}
   */
  isAuthenticated: () => {
    return !!localStorage.getItem(sessionManager.STORAGE_KEYS.USER_ID);
  },
};

export default {
  authAPI,
  chatAPI,
  sessionManager,
};
