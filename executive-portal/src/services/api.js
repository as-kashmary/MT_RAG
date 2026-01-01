/**
 * API Service Layer
 * Connects to the FastAPI backend for all Executive Portal operations.
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
        const token = localStorage.getItem('token');
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
            localStorage.removeItem('token');
            localStorage.removeItem('executive');
            localStorage.removeItem('company');
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
     * Register a new executive and company
     * POST /executive/register
     */
    register: async (data) => {
        const response = await api.post('/executive/register', {
            company_name: data.companyName,
            name: data.name,
            email: data.email,
            password: data.password,
            industry: data.industry,
        });
        return response.data;
    },

    /**
     * Login executive
     * POST /executive/login
     */
    login: async (email, password) => {
        const response = await api.post('/executive/login', {
            email,
            password,
        });
        return response.data;
    },

    /**
     * Get current executive profile
     * GET /executive/me
     */
    getProfile: async () => {
        const response = await api.get('/executive/me');
        return response.data;
    },
};

/**
 * Admin Management API
 */
export const adminAPI = {
    /**
     * Invite a new admin
     * POST /executive/invite-admin
     */
    inviteAdmin: async (adminEmail, adminUsername) => {
        const response = await api.post('/executive/invite-admin', {
            admin_email: adminEmail,
            admin_username: adminUsername,
        });
        return response.data;
    },

    /**
     * Send admin credentials via email
     * POST /executive/send-admin-email
     */
    sendAdminEmail: async (toEmail, adminUsername, tempPassword, companyName) => {
        const response = await api.post('/executive/send-admin-email', {
            to_email: toEmail,
            admin_username: adminUsername,
            temp_password: tempPassword,
            company_name: companyName,
        });
        return response.data;
    },

    /**
     * List all admins for the company
     * GET /executive/admins
     */
    listAdmins: async () => {
        const response = await api.get('/executive/admins');
        return response.data;
    },

    /**
     * Delete an admin by ID
     * DELETE /executive/admins/{adminId}
     */
    deleteAdmin: async (adminId) => {
        const response = await api.delete(`/executive/admins/${adminId}`);
        return response.data;
    },
};

/**
 * Analytics API
 */
export const analyticsAPI = {
    /**
     * Get dashboard analytics
     * GET /analytics/dashboard
     */
    getDashboard: async () => {
        const response = await api.get('/analytics/dashboard');
        return response.data;
    },
};

export default api;
