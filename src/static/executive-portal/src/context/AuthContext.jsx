/**
 * Authentication Context
 * Manages JWT token and user state across the application.
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [company, setCompany] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Check for existing token on mount
    useEffect(() => {
        const token = localStorage.getItem('token');
        const storedUser = localStorage.getItem('executive');
        const storedCompany = localStorage.getItem('company');

        if (token && storedUser) {
            setUser(JSON.parse(storedUser));
            if (storedCompany) {
                setCompany(JSON.parse(storedCompany));
            }
        }
        setLoading(false);
    }, []);

    const register = async (formData) => {
        setLoading(true);
        setError(null);
        try {
            const response = await authAPI.register(formData);

            // Store token and user data
            localStorage.setItem('token', response.access_token);
            localStorage.setItem('executive', JSON.stringify(response.executive));
            localStorage.setItem('company', JSON.stringify(response.company));

            setUser(response.executive);
            setCompany(response.company);

            return response;
        } catch (err) {
            const message = err.response?.data?.detail || 'Registration failed';
            setError(message);
            throw new Error(message);
        } finally {
            setLoading(false);
        }
    };

    const login = async (email, password) => {
        setLoading(true);
        setError(null);
        try {
            const response = await authAPI.login(email, password);

            // Store token and user data
            localStorage.setItem('token', response.access_token);
            localStorage.setItem('executive', JSON.stringify(response.executive));
            localStorage.setItem('company', JSON.stringify(response.company));

            setUser(response.executive);
            setCompany(response.company);

            return response;
        } catch (err) {
            const message = err.response?.data?.detail || 'Login failed';
            setError(message);
            throw new Error(message);
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('executive');
        localStorage.removeItem('company');
        setUser(null);
        setCompany(null);
    };

    const isAuthenticated = () => {
        return !!localStorage.getItem('token');
    };

    const value = {
        user,
        company,
        loading,
        error,
        register,
        login,
        logout,
        isAuthenticated,
        setError,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
