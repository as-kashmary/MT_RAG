/**
 * API Service Layer
 * Connects to the FastAPI backend for all Admin Portal operations.
 */

import axios from 'axios';

// Base API configuration
const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('admin_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expired or invalid - clear and redirect
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

/**
 * Authentication API
 */
export const authAPI = {
    /**
     * Login admin
     * POST /admin/login
     */
    login: async (username, password) => {
        const response = await api.post('/admin/login', {
            username,
            password,
        });
        return response.data;
    },

    /**
     * Get current admin profile
     * GET /admin/me
     */
    getProfile: async () => {
        const response = await api.get('/admin/me');
        return response.data;
    },

    /**
     * Change admin password
     * POST /admin/change-password
     */
    changePassword: async (currentPassword, newPassword) => {
        const response = await api.post('/admin/change-password', {
            current_password: currentPassword,
            new_password: newPassword,
        });
        return response.data;
    },
};

/**
 * Documents API
 */
export const documentsAPI = {
    /**
     * List all documents
     * GET /admin/documents
     */
    list: async () => {
        const response = await api.get('/admin/documents');
        return response.data;
    },

    /**
     * Get document details
     * GET /admin/documents/{id}
     */
    get: async (documentId) => {
        const response = await api.get(`/admin/documents/${documentId}`);
        return response.data;
    },

    /**
     * Delete a document
     * DELETE /admin/documents/{id}
     */
    delete: async (documentId) => {
        const response = await api.delete(`/admin/documents/${documentId}`);
        return response.data;
    },

    /**
     * Upload a document
     * POST /admin/documents/upload
     * @param {File} file - File to upload
     * @param {string} fileName - Name for the document
     * @param {string} productId - ID of the product to associate with
     */
    upload: async (file, fileName, productId) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_name', fileName);
        formData.append('product_id', productId);

        const response = await api.post('/admin/documents/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Update document status
     * PATCH /admin/documents/{id}/status
     * @param {string} documentId - ID of document to update
     * @param {string} status - New status ('pending', 'successful', 'failed')
     */
    updateStatus: async (documentId, status) => {
        const response = await api.patch(`/admin/documents/${documentId}/status`, { status });
        return response.data;
    },
};

/**
 * Products API
 */
export const productsAPI = {
    /**
     * List all products for the admin's company
     * GET /admin/products
     */
    list: async () => {
        const response = await api.get('/admin/products');
        return response.data;
    },

    /**
     * Get product details
     * GET /admin/products/{id}
     */
    get: async (productId) => {
        const response = await api.get(`/admin/products/${productId}`);
        return response.data;
    },

    /**
     * Create a new product
     * POST /admin/products
     */
    create: async (data) => {
        const response = await api.post('/admin/products', data);
        return response.data;
    },

    /**
     * Update a product
     * PUT /admin/products/{id}
     */
    update: async (productId, data) => {
        const response = await api.put(`/admin/products/${productId}`, data);
        return response.data;
    },

    /**
     * Delete a product
     * DELETE /admin/products/{id}
     */
    delete: async (productId) => {
        const response = await api.delete(`/admin/products/${productId}`);
        return response.data;
    },
};

/**
 * Analytics API
 */
export const analyticsAPI = {
    /**
     * Get dashboard analytics
     * GET /admin/analytics/dashboard
     */
    getDashboard: async () => {
        const response = await api.get('/admin/analytics/dashboard');
        return response.data;
    },
};

export default api;
