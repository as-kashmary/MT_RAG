/**
 * Settings Page
 * Profile management and password change functionality.
 */

import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';
import {
    User,
    Lock,
    Building2,
    AlertCircle,
    CheckCircle,
    Loader2,
    Eye,
    EyeOff
} from 'lucide-react';

function Settings() {
    const { admin } = useAuth();

    // Password change state
    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
    });
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handlePasswordChange = (e) => {
        setPasswordData({
            ...passwordData,
            [e.target.name]: e.target.value,
        });
        setError('');
        setSuccess('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        // Validation
        if (passwordData.newPassword !== passwordData.confirmPassword) {
            setError('New passwords do not match');
            return;
        }

        if (passwordData.newPassword.length < 8) {
            setError('New password must be at least 8 characters long');
            return;
        }

        setLoading(true);

        try {
            await authAPI.changePassword(
                passwordData.currentPassword,
                passwordData.newPassword
            );
            setSuccess('Password changed successfully!');
            setPasswordData({
                currentPassword: '',
                newPassword: '',
                confirmPassword: '',
            });
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 'Failed to change password';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in max-w-2xl">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-dark-100">Settings</h1>
                <p className="text-dark-400 mt-1">Manage your profile and security</p>
            </div>

            {/* Profile Section */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-dark-100 mb-4">Profile Information</h2>

                <div className="space-y-4">
                    <div className="flex items-center gap-4 p-4 bg-dark-800/30 rounded-xl">
                        <div className="p-3 bg-primary-500/10 rounded-xl">
                            <User className="w-6 h-6 text-primary-400" />
                        </div>
                        <div>
                            <p className="text-dark-400 text-sm">Username</p>
                            <p className="text-dark-100 font-medium">{admin?.username || 'Admin'}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4 p-4 bg-dark-800/30 rounded-xl">
                        <div className="p-3 bg-primary-500/10 rounded-xl">
                            <Building2 className="w-6 h-6 text-primary-400" />
                        </div>
                        <div>
                            <p className="text-dark-400 text-sm">Company</p>
                            <p className="text-dark-100 font-medium">{admin?.company_name || 'Company'}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Change Password Section */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-dark-100 mb-4 flex items-center gap-2">
                    <Lock className="w-5 h-5 text-primary-400" />
                    Change Password
                </h2>

                {/* Alerts */}
                {error && (
                    <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3 animate-fade-in">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <p className="text-red-400 text-sm">{error}</p>
                    </div>
                )}

                {success && (
                    <div className="mb-4 p-4 bg-green-500/10 border border-green-500/30 rounded-xl flex items-center gap-3 animate-fade-in">
                        <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                        <p className="text-green-400 text-sm">{success}</p>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Current Password */}
                    <div>
                        <label htmlFor="currentPassword" className="input-label">
                            Current Password
                        </label>
                        <div className="relative">
                            <input
                                type={showCurrentPassword ? 'text' : 'password'}
                                id="currentPassword"
                                name="currentPassword"
                                value={passwordData.currentPassword}
                                onChange={handlePasswordChange}
                                className="input-field pr-12"
                                placeholder="Enter current password"
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-200"
                            >
                                {showCurrentPassword ? (
                                    <EyeOff className="w-5 h-5" />
                                ) : (
                                    <Eye className="w-5 h-5" />
                                )}
                            </button>
                        </div>
                    </div>

                    {/* New Password */}
                    <div>
                        <label htmlFor="newPassword" className="input-label">
                            New Password
                        </label>
                        <div className="relative">
                            <input
                                type={showNewPassword ? 'text' : 'password'}
                                id="newPassword"
                                name="newPassword"
                                value={passwordData.newPassword}
                                onChange={handlePasswordChange}
                                className="input-field pr-12"
                                placeholder="Enter new password"
                                required
                                minLength={8}
                            />
                            <button
                                type="button"
                                onClick={() => setShowNewPassword(!showNewPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-200"
                            >
                                {showNewPassword ? (
                                    <EyeOff className="w-5 h-5" />
                                ) : (
                                    <Eye className="w-5 h-5" />
                                )}
                            </button>
                        </div>
                        <p className="text-dark-500 text-xs mt-1">Must be at least 8 characters</p>
                    </div>

                    {/* Confirm Password */}
                    <div>
                        <label htmlFor="confirmPassword" className="input-label">
                            Confirm New Password
                        </label>
                        <input
                            type="password"
                            id="confirmPassword"
                            name="confirmPassword"
                            value={passwordData.confirmPassword}
                            onChange={handlePasswordChange}
                            className="input-field"
                            placeholder="Confirm new password"
                            required
                        />
                    </div>

                    {/* Submit Button */}
                    <div className="pt-2">
                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary flex items-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Updating...
                                </>
                            ) : (
                                <>
                                    <Lock className="w-4 h-4" />
                                    Update Password
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default Settings;
