/**
 * Dashboard Home Component
 * Quick overview with stats and recent activity.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { analyticsAPI } from '../services/api';
import Spinner from './ui/Spinner';

const DashboardHome = () => {
    const { user, company } = useAuth();
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const data = await analyticsAPI.getDashboard();
                setAnalytics(data);
            } catch (err) {
                setError('Failed to load analytics');
                console.error('Analytics error:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalytics();
    }, []);

    const stats = analytics ? [
        {
            label: 'Total Queries',
            value: analytics.total_queries,
            icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            ),
            color: 'primary',
        },
        {
            label: 'Active Documents',
            value: analytics.total_files,
            icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
            ),
            color: 'green',
        },
        {
            label: 'Team Admins',
            value: analytics.total_admins,
            icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
            ),
            color: 'purple',
        },
        {
            label: 'Active Users',
            value: analytics.total_users,
            icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
            ),
            color: 'orange',
        },
    ] : [];

    const colorStyles = {
        primary: 'text-primary-400 bg-primary-500/10',
        green: 'text-green-400 bg-green-500/10',
        purple: 'text-purple-400 bg-purple-500/10',
        orange: 'text-orange-400 bg-orange-500/10',
    };

    return (
        <div className="space-y-8">
            {/* Welcome Section */}
            <div>
                <h1 className="text-3xl font-bold text-dark-100 mb-2">
                    Welcome back, {user?.name?.split(' ')[0] || 'Executive'}! 👋
                </h1>
                <p className="text-dark-400">
                    Here's what's happening with {company?.name || 'your company'} today.
                </p>
            </div>

            {/* Stats Grid */}
            {loading ? (
                <div className="flex justify-center py-12">
                    <Spinner size="lg" />
                </div>
            ) : error ? (
                <div className="glass-card p-6 text-center text-red-400">
                    {error}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {stats.map((stat, index) => (
                        <div key={index} className="stat-card group">
                            <div className="flex items-center justify-between mb-4">
                                <div className={`p-3 rounded-xl ${colorStyles[stat.color]}`}>
                                    {stat.icon}
                                </div>
                            </div>
                            <p className="text-dark-400 text-sm mb-1">{stat.label}</p>
                            <p className="text-3xl font-bold text-dark-100">{stat.value}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* File Status Breakdown */}
            {analytics && (
                <div className="glass-card p-6">
                    <h2 className="text-xl font-semibold text-dark-100 mb-4">Document Processing Status</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-4 bg-yellow-500/10 rounded-xl border border-yellow-500/20">
                            <p className="text-2xl font-bold text-yellow-400">{analytics.file_status_breakdown.pending}</p>
                            <p className="text-sm text-dark-400">Pending</p>
                        </div>
                        <div className="p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
                            <p className="text-2xl font-bold text-blue-400">{analytics.file_status_breakdown.running}</p>
                            <p className="text-sm text-dark-400">Processing</p>
                        </div>
                        <div className="p-4 bg-green-500/10 rounded-xl border border-green-500/20">
                            <p className="text-2xl font-bold text-green-400">{analytics.file_status_breakdown.successful}</p>
                            <p className="text-sm text-dark-400">Successful</p>
                        </div>
                        <div className="p-4 bg-red-500/10 rounded-xl border border-red-500/20">
                            <p className="text-2xl font-bold text-red-400">{analytics.file_status_breakdown.failed}</p>
                            <p className="text-sm text-dark-400">Failed</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Quick Actions */}
            <div className="glass-card p-6">
                <h2 className="text-xl font-semibold text-dark-100 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <a
                        href="/dashboard/invite"
                        className="flex items-center gap-4 p-4 rounded-xl bg-dark-800/30 hover:bg-dark-800/50 border border-dark-700/50 hover:border-primary-500/30 transition-all duration-200 group"
                    >
                        <div className="p-3 rounded-xl bg-primary-500/10 text-primary-400 group-hover:bg-primary-500/20 transition-colors">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                            </svg>
                        </div>
                        <div>
                            <p className="font-medium text-dark-100">Invite Admin</p>
                            <p className="text-sm text-dark-400">Add team members to manage documents</p>
                        </div>
                    </a>

                    <a
                        href="/dashboard/analytics"
                        className="flex items-center gap-4 p-4 rounded-xl bg-dark-800/30 hover:bg-dark-800/50 border border-dark-700/50 hover:border-primary-500/30 transition-all duration-200 group"
                    >
                        <div className="p-3 rounded-xl bg-primary-500/10 text-primary-400 group-hover:bg-primary-500/20 transition-colors">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                        </div>
                        <div>
                            <p className="font-medium text-dark-100">View Analytics</p>
                            <p className="text-sm text-dark-400">Deep dive into system metrics</p>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    );
};

export default DashboardHome;
