/**
 * Authentication Context
 * Manages admin authentication state across the application.
 */

import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [admin, setAdmin] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing auth on mount
        const token = localStorage.getItem('admin_token');
        const savedAdmin = localStorage.getItem('admin');

        if (token && savedAdmin) {
            try {
                setAdmin(JSON.parse(savedAdmin));
            } catch (e) {
                // Invalid stored data, clear it
                localStorage.removeItem('admin_token');
                localStorage.removeItem('admin');
            }
        }
        setLoading(false);
    }, []);

    const login = (token, adminData) => {
        localStorage.setItem('admin_token', token);
        localStorage.setItem('admin', JSON.stringify(adminData));
        setAdmin(adminData);
    };

    const logout = () => {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin');
        setAdmin(null);
    };

    const isAuthenticated = () => {
        return !!admin && !!localStorage.getItem('admin_token');
    };

    const value = {
        admin,
        loading,
        login,
        logout,
        isAuthenticated,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export default AuthContext;
