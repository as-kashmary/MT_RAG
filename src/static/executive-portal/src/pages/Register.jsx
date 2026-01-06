/**
 * Registration Page
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import { ToastContainer, useToast } from '../components/ui/Toast';

const Register = () => {
    const navigate = useNavigate();
    const { register, loading } = useAuth();
    const { toasts, addToast, removeToast } = useToast();

    const [formData, setFormData] = useState({
        companyName: '',
        name: '',
        email: '',
        password: '',
        confirmPassword: '',
        industry: '',
    });

    const [errors, setErrors] = useState({});

    const industryOptions = [
        { value: 'technology', label: 'Technology' },
        { value: 'finance', label: 'Finance & Banking' },
        { value: 'healthcare', label: 'Healthcare' },
        { value: 'retail', label: 'Retail & E-commerce' },
        { value: 'manufacturing', label: 'Manufacturing' },
        { value: 'education', label: 'Education' },
        { value: 'consulting', label: 'Consulting' },
        { value: 'other', label: 'Other' },
    ];

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
        // Clear error when user types
        if (errors[name]) {
            setErrors((prev) => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.companyName.trim()) {
            newErrors.companyName = 'Company name is required';
        }
        if (!formData.name.trim()) {
            newErrors.name = 'Your name is required';
        }
        if (!formData.email.trim()) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email';
        }
        if (!formData.password) {
            newErrors.password = 'Password is required';
        } else if (formData.password.length < 8) {
            newErrors.password = 'Password must be at least 8 characters';
        }
        if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match';
        }
        if (!formData.industry) {
            newErrors.industry = 'Please select an industry';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            addToast('Please fix the errors in the form', 'error');
            return;
        }

        try {
            await register(formData);
            addToast('Registration successful! Welcome aboard!', 'success');
            setTimeout(() => navigate('/dashboard'), 1000);
        } catch (err) {
            addToast(err.message || 'Registration failed', 'error');
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
                    <p className="text-dark-400 text-lg mb-8">
                        Create your company's isolated AI knowledge base. Secure, scalable, and enterprise-ready.
                    </p>

                    <div className="grid grid-cols-2 gap-4 text-left">
                        {[
                            { icon: '🔒', text: 'Multi-tenant isolation' },
                            { icon: '🚀', text: 'Enterprise RAG' },
                            { icon: '📊', text: 'Real-time analytics' },
                            { icon: '👥', text: 'Team management' },
                        ].map((feature, idx) => (
                            <div key={idx} className="flex items-center gap-2 text-dark-300">
                                <span>{feature.icon}</span>
                                <span className="text-sm">{feature.text}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right side - Form */}
            <div className="flex-1 flex items-center justify-center p-8 overflow-y-auto">
                <div className="w-full max-w-md py-8 animate-slide-up">
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold text-dark-100 mb-2">Create your account</h2>
                        <p className="text-dark-400">Register your company for MT-RAG</p>
                    </div>

                    <form onSubmit={handleSubmit} className="glass-card p-8 space-y-5">
                        <Input
                            label="Company Name"
                            type="text"
                            name="companyName"
                            value={formData.companyName}
                            onChange={handleChange}
                            placeholder="Acme Corporation"
                            error={errors.companyName}
                            required
                        />

                        <Input
                            label="Your Name"
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            placeholder="John Smith"
                            error={errors.name}
                            required
                        />

                        <Input
                            label="Work Email"
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="ceo@acme.com"
                            error={errors.email}
                            required
                        />

                        <Select
                            label="Industry"
                            name="industry"
                            value={formData.industry}
                            onChange={handleChange}
                            options={industryOptions}
                            placeholder="Select your industry"
                            error={errors.industry}
                            required
                        />

                        <Input
                            label="Password"
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder="••••••••"
                            error={errors.password}
                            required
                        />

                        <Input
                            label="Confirm Password"
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder="••••••••"
                            error={errors.confirmPassword}
                            required
                        />

                        <Button
                            type="submit"
                            loading={loading}
                            className="w-full"
                        >
                            Create Account
                        </Button>
                    </form>

                    <p className="text-center mt-6 text-dark-400">
                        Already have an account?{' '}
                        <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
                            Sign in
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Register;
