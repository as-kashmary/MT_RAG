/**
 * Analytics Component
 * Detailed analytics view with charts and metrics.
 */

import { useState, useEffect } from 'react';
import { analyticsAPI } from '../services/api';
import Spinner from './ui/Spinner';

const Analytics = () => {
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

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Spinner size="lg" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass-card p-8 text-center">
                <p className="text-red-400 mb-4">{error}</p>
                <button
                    onClick={() => window.location.reload()}
                    className="text-primary-400 hover:text-primary-300"
                >
                    Retry
                </button>
            </div>
        );
    }

    // Calculate percentages for the chart
    const total = analytics?.total_files || 1;
    const statusData = [
        { label: 'Successful', value: analytics?.file_status_breakdown.successful || 0, color: '#22c55e' },
        { label: 'Pending', value: analytics?.file_status_breakdown.pending || 0, color: '#eab308' },
        { label: 'Processing', value: analytics?.file_status_breakdown.running || 0, color: '#3b82f6' },
        { label: 'Failed', value: analytics?.file_status_breakdown.failed || 0, color: '#ef4444' },
    ];

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-dark-100 mb-2">Analytics</h1>
                <p className="text-dark-400">
                    Comprehensive insights into your MT-RAG system usage and performance.
                </p>
            </div>

            {/* Main Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="stat-card">
                    <p className="text-dark-400 text-sm mb-1">Total Queries</p>
                    <p className="text-4xl font-bold gradient-text">{analytics?.total_queries || 0}</p>
                    <p className="text-dark-500 text-sm mt-2">All-time queries processed</p>
                </div>

                <div className="stat-card">
                    <p className="text-dark-400 text-sm mb-1">Total Documents</p>
                    <p className="text-4xl font-bold text-green-400">{analytics?.total_files || 0}</p>
                    <p className="text-dark-500 text-sm mt-2">Documents in knowledge base</p>
                </div>

                <div className="stat-card">
                    <p className="text-dark-400 text-sm mb-1">Team Admins</p>
                    <p className="text-4xl font-bold text-purple-400">{analytics?.total_admins || 0}</p>
                    <p className="text-dark-500 text-sm mt-2">Active administrators</p>
                </div>

                <div className="stat-card">
                    <p className="text-dark-400 text-sm mb-1">End Users</p>
                    <p className="text-4xl font-bold text-orange-400">{analytics?.total_users || 0}</p>
                    <p className="text-dark-500 text-sm mt-2">Registered system users</p>
                </div>
            </div>

            {/* Document Status */}
            <div className="glass-card p-8">
                <h2 className="text-xl font-semibold text-dark-100 mb-6">Document Processing Overview</h2>

                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Bar Chart */}
                    <div className="space-y-4">
                        {statusData.map((item) => {
                            const percentage = total > 0 ? (item.value / total) * 100 : 0;
                            return (
                                <div key={item.label} className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-dark-300">{item.label}</span>
                                        <span className="text-dark-100 font-medium">{item.value}</span>
                                    </div>
                                    <div className="h-3 bg-dark-800 rounded-full overflow-hidden">
                                        <div
                                            className="h-full rounded-full transition-all duration-500 ease-out"
                                            style={{
                                                width: `${percentage}%`,
                                                backgroundColor: item.color,
                                            }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Donut Chart Visualization */}
                    <div className="flex flex-col items-center justify-center">
                        <div className="relative w-48 h-48">
                            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                                {(() => {
                                    let cumulativePercent = 0;
                                    return statusData.map((item, index) => {
                                        const percent = total > 0 ? (item.value / total) * 100 : 0;
                                        const strokeDasharray = `${percent} ${100 - percent}`;
                                        const strokeDashoffset = -cumulativePercent;
                                        cumulativePercent += percent;

                                        return (
                                            <circle
                                                key={index}
                                                cx="50"
                                                cy="50"
                                                r="40"
                                                fill="transparent"
                                                stroke={item.color}
                                                strokeWidth="8"
                                                strokeDasharray={strokeDasharray}
                                                strokeDashoffset={strokeDashoffset}
                                                className="transition-all duration-500"
                                                style={{ strokeLinecap: 'round' }}
                                            />
                                        );
                                    });
                                })()}
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold text-dark-100">{total}</span>
                                <span className="text-dark-400 text-sm">Total</span>
                            </div>
                        </div>

                        {/* Legend */}
                        <div className="grid grid-cols-2 gap-4 mt-6">
                            {statusData.map((item) => (
                                <div key={item.label} className="flex items-center gap-2">
                                    <div
                                        className="w-3 h-3 rounded-full"
                                        style={{ backgroundColor: item.color }}
                                    />
                                    <span className="text-sm text-dark-300">{item.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Usage Metrics */}
            <div className="grid lg:grid-cols-2 gap-6">
                <div className="glass-card p-6">
                    <h3 className="font-semibold text-dark-100 mb-4">System Health</h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-dark-800/30 rounded-lg">
                            <span className="text-dark-300">API Status</span>
                            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-full">
                                Operational
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-dark-800/30 rounded-lg">
                            <span className="text-dark-300">Database</span>
                            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-full">
                                Connected
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-dark-800/30 rounded-lg">
                            <span className="text-dark-300">Vector Store</span>
                            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-full">
                                Active
                            </span>
                        </div>
                    </div>
                </div>

                <div className="glass-card p-6">
                    <h3 className="font-semibold text-dark-100 mb-4">Performance Metrics</h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-dark-800/30 rounded-lg">
                            <span className="text-dark-300">Avg. Query Time</span>
                            <span className="text-dark-100 font-medium">~2.3s</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-dark-800/30 rounded-lg">
                            <span className="text-dark-300">Success Rate</span>
                            <span className="text-dark-100 font-medium">
                                {analytics?.total_files > 0
                                    ? Math.round((analytics.file_status_breakdown.successful / analytics.total_files) * 100)
                                    : 0}%
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-dark-800/30 rounded-lg">
                            <span className="text-dark-300">Active Namespaces</span>
                            <span className="text-dark-100 font-medium">1</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
