/**
 * API Integration Examples
 * Reference for integrating additional backend endpoints with frontend
 * 
 * This file demonstrates the pattern used for auth integration
 * that can be applied to other API endpoints
 */

import { sessionManager } from './api';

/**
 * Example: Query/Chat Endpoint Integration
 * 
 * Pattern:
 * 1. Add API method to api.js
 * 2. Call from component handler
 * 3. Update UI with loading state
 * 4. Handle errors gracefully
 * 5. Persist user-specific data
 */

// ============ IN api.js ============
export const chatAPI = {
  /**
   * Send a user query and get AI response
   * @param {string} userId - Current user ID
   * @param {string} query - User's query text
   * @param {string} productId - Selected product/context
   * @returns {Promise<Object>} - AI response
   */
  sendQuery: async (userId, query, productId) => {
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/chat/query`,
        {
          method: 'POST',
          body: JSON.stringify({
            user_id: userId,
            query: query,
            product_id: productId,
          }),
        }
      );

      const data = await response.json();
      return {
        success: true,
        data,
        message: 'Query processed successfully',
      };
    } catch (error) {
      console.error('Query error:', error);
      return {
        success: false,
        message: error.message || 'Failed to process query',
        error,
      };
    }
  },

  /**
   * Get user's chat history
   * @param {string} userId - Current user ID
   * @returns {Promise<Object>} - Chat history
   */
  getChatHistory: async (userId) => {
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/chat/history?user_id=${encodeURIComponent(userId)}`,
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
      console.error('History fetch error:', error);
      return {
        success: false,
        message: error.message || 'Failed to fetch history',
        error,
      };
    }
  },
};

// ============ IN Component ============
/**
 * Example: Using Query API in React Component
 */

function ChatComponent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  const handleSendQuery = async (query, productId) => {
    setLoading(true);
    setError(null);

    try {
      // Get current user from session
      const session = sessionManager.getSession();
      if (!session) {
        setError('User session not found. Please login again.');
        setLoading(false);
        return;
      }

      // Call API
      const result = await chatAPI.sendQuery(
        session.userId,
        query,
        productId
      );

      if (!result.success) {
        setError(result.message);
        setLoading(false);
        return;
      }

      // Update UI with response
      setResponse(result.data);
      setLoading(false);
    } catch (err) {
      setError('An unexpected error occurred');
      setLoading(false);
    }
  };

  return (
    <div>
      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Processing...</div>}
      {response && <div className="response">{response.text}</div>}
    </div>
  );
}

// ============ Pattern Summary ============
/**
 * Integration Pattern (Apply to Any Endpoint)
 * 
 * 1. API Layer (api.js)
 *    - Create method in appropriate API object
 *    - Handle timeout, errors, responses
 *    - Return consistent format: { success, data, message, error }
 * 
 * 2. Component Layer
 *    - Create state for loading, error, data
 *    - Get user session if needed
 *    - Call API method with proper parameters
 *    - Update UI based on response
 *    - Handle errors gracefully
 * 
 * 3. Error Handling
 *    - Show loading indicator while fetching
 *    - Display error message if failed
 *    - Allow user to retry
 * 
 * 4. Data Persistence
 *    - Store user-specific data with userId
 *    - Use localStorage for temporary data
 *    - Use backend for permanent storage
 * 
 * 5. Security
 *    - Include userId in requests
 *    - Use HTTPS in production
 *    - Validate on backend
 * 
 * Pattern Code Template:
 * 
 * // 1. In api.js
 * export const someAPI = {
 *   method: async (userId, param1, param2) => {
 *     try {
 *       const response = await fetchWithTimeout(url, options);
 *       const data = await response.json();
 *       return { success: true, data };
 *     } catch (error) {
 *       return { success: false, message: error.message };
 *     }
 *   }
 * };
 * 
 * // 2. In Component
 * const [loading, setLoading] = useState(false);
 * const [error, setError] = useState(null);
 * const [data, setData] = useState(null);
 * 
 * const handleFetch = async () => {
 *   setLoading(true);
 *   const session = sessionManager.getSession();
 *   const result = await someAPI.method(session.userId, param1);
 *   setLoading(false);
 *   if (result.success) setData(result.data);
 *   else setError(result.message);
 * };
 */

// ============ Backend Endpoint Template ============
/**
 * Example Backend Endpoint (FastAPI)
 * 
 * from fastapi import APIRouter, Depends, HTTPException, status
 * from sqlalchemy.ext.asyncio import AsyncSession
 * 
 * router = APIRouter(prefix="/chat", tags=["chat"])
 * 
 * @router.post("/query", status_code=status.HTTP_200_OK)
 * async def send_query(
 *     user_id: str,
 *     query: str,
 *     product_id: str,
 *     db: AsyncSession = Depends(get_db)
 * ) -> dict:
 *     try:
 *         # Validate user exists
 *         user = await db.get(User, user_id)
 *         if not user:
 *             raise HTTPException(
 *                 status_code=status.HTTP_401_UNAUTHORIZED,
 *                 detail="User not found"
 *             )
 *         
 *         # Process query
 *         # ...
 *         
 *         return {
 *             "success": True,
 *             "response": "AI generated response",
 *             "context": "retrieved context"
 *         }
 *     except Exception as e:
 *         logger.error(f"Query processing error: {str(e)}")
 *         raise HTTPException(
 *             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
 *             detail=str(e)
 *         )
 * 
 * @router.get("/history", status_code=status.HTTP_200_OK)
 * async def get_history(
 *     user_id: str,
 *     limit: int = 50,
 *     db: AsyncSession = Depends(get_db)
 * ) -> list[dict]:
 *     try:
 *         # Get user's chat history from database
 *         # ...
 *         return history_list
 *     except Exception as e:
 *         raise HTTPException(
 *             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
 *             detail=str(e)
 *         )
 */

/**
 * Common Integration Scenarios
 */

// Scenario 1: Paginated Data
export async function fetchPaginatedData(endpoint, userId, page = 1, pageSize = 10) {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  url.searchParams.append('user_id', userId);
  url.searchParams.append('page', page);
  url.searchParams.append('page_size', pageSize);
  
  const response = await fetchWithTimeout(url.toString(), { method: 'GET' });
  return response.json();
}

// Scenario 2: File Upload with User Context
export async function uploadFile(userId, file, metadata = {}) {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('file', file);
  Object.entries(metadata).forEach(([key, value]) => {
    formData.append(key, value);
  });

  const response = await fetchWithTimeout(`${API_BASE_URL}/files/upload`, {
    method: 'POST',
    body: formData,
    headers: {}, // Don't set Content-Type for FormData
  });
  
  return response.json();
}

// Scenario 3: Real-time Updates with WebSocket
export function createWebSocketConnection(userId) {
  const wsUrl = `ws://localhost:8001/ws/${userId}`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => console.log('WebSocket connected');
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
  };
  ws.onerror = (error) => console.error('WebSocket error:', error);
  ws.onclose = () => console.log('WebSocket disconnected');

  return ws;
}

// Scenario 4: Polling for Long-running Operations
export async function pollForResult(taskId, userId, maxAttempts = 30) {
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/tasks/${taskId}/status?user_id=${userId}`,
      { method: 'GET' }
    );
    
    const data = await response.json();
    
    if (data.status === 'completed') {
      return { success: true, result: data.result };
    }
    
    if (data.status === 'failed') {
      return { success: false, error: data.error };
    }
    
    // Wait before next attempt
    await new Promise(resolve => setTimeout(resolve, 1000));
    attempts++;
  }
  
  return { success: false, error: 'Polling timeout' };
}

/**
 * Best Practices Checklist
 * 
 * - [ ] Always validate user session exists
 * - [ ] Include userId in all requests
 * - [ ] Handle network errors gracefully
 * - [ ] Show loading states to users
 * - [ ] Implement retry logic for failures
 * - [ ] Log errors for debugging
 * - [ ] Validate input on frontend before API call
 * - [ ] Validate input on backend
 * - [ ] Use proper HTTP status codes
 * - [ ] Return consistent response format
 * - [ ] Implement proper error messages
 * - [ ] Add request/response timeouts
 * - [ ] Implement rate limiting awareness
 * - [ ] Cache responses when appropriate
 * - [ ] Update UI optimistically where possible
 */

export default {
  fetchPaginatedData,
  uploadFile,
  createWebSocketConnection,
  pollForResult,
};
