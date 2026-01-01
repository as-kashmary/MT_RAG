/**
 * Login Page
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { ToastContainer, useToast } from '../components/ui/Toast';

const Login = () => {
    const navigate = useNavigate();
    const { login, loading } = useAuth();
    const { toasts, addToast, removeToast } = useToast();

    const [formData, setFormData] = useState({
        email: '',
        password: '',
    });

    const handleChange = (e) => {
        setFormData((prev) => ({
            ...prev,
            [e.target.name]: e.target.value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            await login(formData.email, formData.password);
            addToast('Login successful! Redirecting...', 'success');
            setTimeout(() => navigate('/dashboard'), 1000);
        } catch (err) {
            addToast(err.message || 'Login failed', 'error');
        }
    };

    return (
        <div className="min-h-screen bg-dark-950 flex">
            <ToastContainer toasts={toasts} removeToast={removeToast} />

            {/* Left side - Branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-dark-900 to-dark-950 items-center justify-center p-12">
                <div className="max-w-md text-center animate-fade-in">
                    <div className="w-20 h-20 bg-gradient-to-br from-primary-400 to-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-glow">
                        <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <h1 className="text-4xl font-bold gradient-text mb-4">MT-RAG System</h1>
                    <p className="text-dark-400 text-lg">
                        Multi-Tenant Retrieval-Augmented Generation platform for enterprise AI knowledge bases.
                    </p>
                </div>
            </div>

            {/* Right side - Form */}
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="w-full max-w-md animate-slide-up">
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold text-dark-100 mb-2">Welcome back</h2>
                        <p className="text-dark-400">Sign in to your executive account</p>
                    </div>

                    <form onSubmit={handleSubmit} className="glass-card p-8 space-y-6">
                        <Input
                            label="Email"
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="ceo@company.com"
                            required
                        />

                        <Input
                            label="Password"
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder="••••••••"
                            required
                        />

                        <Button
                            type="submit"
                            loading={loading}
                            className="w-full"
                        >
                            Sign In
                        </Button>
                    </form>

                    <p className="text-center mt-6 text-dark-400">
                        Don't have an account?{' '}
                        <Link to="/register" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
                            Register your company
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
