/**
 * Invite Admin Component
 * Allows executives to invite admins with auto-generated password and automatic email sending.
 */

import { useState } from 'react';
import { adminAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Button from './ui/Button';
import Input from './ui/Input';
import { ToastContainer, useToast } from './ui/Toast';

const InviteAdmin = () => {
    const { company } = useAuth();
    const { toasts, addToast, removeToast } = useToast();

    const [formData, setFormData] = useState({
        adminEmail: '',
        adminUsername: '',
    });
    const [loading, setLoading] = useState(false);
    const [sendingEmail, setSendingEmail] = useState(false);
    const [inviteResult, setInviteResult] = useState(null);
    const [emailSent, setEmailSent] = useState(false);

    const handleChange = (e) => {
        setFormData((prev) => ({
            ...prev,
            [e.target.name]: e.target.value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setInviteResult(null);
        setEmailSent(false);

        try {
            const result = await adminAPI.inviteAdmin(formData.adminEmail, formData.adminUsername);
            setInviteResult({ ...result, adminEmail: formData.adminEmail });
            addToast('Admin account created successfully!', 'success');
            setFormData({ adminEmail: '', adminUsername: '' });
        } catch (err) {
            addToast(err.response?.data?.detail || 'Failed to invite admin', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleSendEmail = async () => {
        if (!inviteResult) return;

        setSendingEmail(true);
        try {
            const result = await adminAPI.sendAdminEmail(
                inviteResult.adminEmail,
                inviteResult.admin_username,
                inviteResult.temp_password,
                company?.name || 'Your Company'
            );

            if (result.success) {
                setEmailSent(true);
                addToast('Email sent successfully!', 'success');
            } else {
                addToast(result.message || 'Failed to send email. Try manual option.', 'error');
            }
        } catch (err) {
            addToast(err.response?.data?.detail || 'Failed to send email. Try manual option.', 'error');
        } finally {
            setSendingEmail(false);
        }
    };

    const generateMailtoLink = () => {
        if (!inviteResult) return '#';

        const subject = encodeURIComponent(`Your ${company?.name || 'Company'} Admin Credentials`);
        const body = encodeURIComponent(
            `Hello ${inviteResult.admin_username},

You have been invited to join ${company?.name || 'our company'} as an Admin on the MT-RAG System.

Your login credentials are:
Username: ${inviteResult.admin_username}
Temporary Password: ${inviteResult.temp_password}

Please login at your earliest convenience and change your password.

Best regards,
${company?.name || 'Company'} Team`
        );

        return `mailto:${inviteResult.adminEmail || ''}?subject=${subject}&body=${body}`;
    };

    return (
        <div className="space-y-8">
            <ToastContainer toasts={toasts} removeToast={removeToast} />

            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-dark-100 mb-2">Invite Admin</h1>
                <p className="text-dark-400">
                    Add team members to manage your company's documents and knowledge base.
                </p>
            </div>

            <div className="grid lg:grid-cols-2 gap-8">
                {/* Invite Form */}
                <div className="glass-card p-8">
                    <h2 className="text-xl font-semibold text-dark-100 mb-6">Admin Details</h2>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <Input
                            label="Admin Email"
                            type="email"
                            name="adminEmail"
                            value={formData.adminEmail}
                            onChange={handleChange}
                            placeholder="admin@company.com"
                            required
                        />

                        <Input
                            label="Admin Username"
                            type="text"
                            name="adminUsername"
                            value={formData.adminUsername}
                            onChange={handleChange}
                            placeholder="john_admin"
                            required
                        />

                        <div className="pt-2">
                            <Button type="submit" loading={loading} className="w-full">
                                Generate Credentials
                            </Button>
                        </div>
                    </form>
                </div>

                {/* Result Card */}
                <div className="glass-card p-8">
                    <h2 className="text-xl font-semibold text-dark-100 mb-6">Invite Credentials</h2>

                    {inviteResult ? (
                        <div className="space-y-6">
                            {emailSent ? (
                                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-xl">
                                    <p className="text-green-400 font-medium mb-1">✓ Email Sent Successfully!</p>
                                    <p className="text-dark-400 text-sm">Credentials have been sent to {inviteResult.adminEmail}</p>
                                </div>
                            ) : (
                                <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                                    <p className="text-blue-400 font-medium mb-1">Admin Created!</p>
                                    <p className="text-dark-400 text-sm">Click "Send Email" below to send credentials.</p>
                                </div>
                            )}

                            <div className="space-y-4">
                                <div>
                                    <label className="text-sm text-dark-400">Username</label>
                                    <p className="text-lg font-mono text-dark-100 bg-dark-800/50 p-3 rounded-lg">
                                        {inviteResult.admin_username}
                                    </p>
                                </div>

                                <div>
                                    <label className="text-sm text-dark-400">Temporary Password</label>
                                    <p className="text-lg font-mono text-dark-100 bg-dark-800/50 p-3 rounded-lg">
                                        {inviteResult.temp_password}
                                    </p>
                                </div>
                            </div>

                            {!emailSent && (
                                <div className="space-y-3">
                                    <button
                                        onClick={handleSendEmail}
                                        disabled={sendingEmail}
                                        className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-300 shadow-lg hover:shadow-green-500/25 disabled:opacity-50"
                                    >
                                        {sendingEmail ? (
                                            <>
                                                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                                Sending...
                                            </>
                                        ) : (
                                            <>
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                                </svg>
                                                Send Email
                                            </>
                                        )}
                                    </button>

                                    <a
                                        href={generateMailtoLink()}
                                        className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-dark-700 text-dark-200 font-medium rounded-xl hover:bg-dark-600 transition-all duration-300"
                                    >
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                        </svg>
                                        Open Email Client (Manual)
                                    </a>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-64 text-center">
                            <div className="w-16 h-16 bg-dark-800/50 rounded-full flex items-center justify-center mb-4">
                                <svg className="w-8 h-8 text-dark-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                                </svg>
                            </div>
                            <p className="text-dark-400 mb-2">No credentials generated yet</p>
                            <p className="text-dark-500 text-sm">Fill out the form to create admin credentials</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Info Card */}
            <div className="glass-card p-6 border-l-4 border-primary-500">
                <h3 className="font-semibold text-dark-100 mb-2">How it works</h3>
                <ul className="text-dark-400 space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                        <span className="text-primary-400">1.</span>
                        Enter the admin's email and choose a username
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-primary-400">2.</span>
                        Click "Generate Credentials" to create the admin account
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-primary-400">3.</span>
                        Click "Send Email" to send credentials to the admin
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-primary-400">4.</span>
                        The admin can then login and start managing documents
                    </li>
                </ul>
            </div>
        </div>
    );
};

export default InviteAdmin;

