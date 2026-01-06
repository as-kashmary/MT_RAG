/**
 * Admin Analytics Component
 * Detailed analytics view with charts and metrics.
 */

import { useState, useEffect } from 'react';
import { analyticsAPI } from '../services/api';
import {
    FileText,
    CheckCircle2,
    AlertCircle,
    Loader2,
    TrendingUp,
    PieChart as PieChartIcon,
    Clock
} from 'lucide-react';

function AdminAnalytics() {
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchAnalytics();
    }, []);

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

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass-card p-8 text-center">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <p className="text-red-400">{error}</p>
                <button onClick={fetchAnalytics} className="btn-secondary mt-4">
                    Retry
                </button>
            </div>
        );
    }

    const statusData = analytics?.document_status || { pending: 0, successful: 0, failed: 0 };
    const total = analytics?.total_documents || 0;

    // Calculate percentages for the visual chart
    const getPercentage = (value) => total > 0 ? ((value / total) * 100).toFixed(1) : 0;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-dark-100">Analytics</h1>
                <p className="text-dark-400 mt-1">Document processing insights and metrics</p>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="stat-card">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <FileText className="w-5 h-5 text-blue-400" />
                        </div>
                        <span className="text-dark-400 text-sm">Total Documents</span>
                    </div>
                    <p className="text-3xl font-bold text-dark-100">{total}</p>
                </div>

                <div className="stat-card">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-yellow-500/10 rounded-lg">
                            <Clock className="w-5 h-5 text-yellow-400" />
                        </div>
                        <span className="text-dark-400 text-sm">Pending</span>
                    </div>
                    <p className="text-3xl font-bold text-dark-100">{statusData.pending}</p>
                    <p className="text-sm text-dark-500 mt-1">{getPercentage(statusData.pending)}% of total</p>
                </div>

                <div className="stat-card">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-green-500/10 rounded-lg">
                            <CheckCircle2 className="w-5 h-5 text-green-400" />
                        </div>
                        <span className="text-dark-400 text-sm">Successful</span>
                    </div>
                    <p className="text-3xl font-bold text-dark-100">{statusData.successful}</p>
                    <p className="text-sm text-dark-500 mt-1">{getPercentage(statusData.successful)}% of total</p>
                </div>

                <div className="stat-card">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-red-500/10 rounded-lg">
                            <AlertCircle className="w-5 h-5 text-red-400" />
                        </div>
                        <span className="text-dark-400 text-sm">Failed</span>
                    </div>
                    <p className="text-3xl font-bold text-dark-100">{statusData.failed}</p>
                    <p className="text-sm text-dark-500 mt-1">{getPercentage(statusData.failed)}% of total</p>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Status Distribution */}
                <div className="glass-card p-6">
                    <div className="flex items-center gap-2 mb-6">
                        <PieChartIcon className="w-5 h-5 text-primary-400" />
                        <h3 className="text-lg font-semibold text-dark-100">Status Distribution</h3>
                    </div>

                    {/* Simple visual bar chart */}
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between mb-1">
                                <span className="text-dark-300 text-sm">Pending</span>
                                <span className="text-dark-400 text-sm">{statusData.pending}</span>
                            </div>
                            <div className="h-3 bg-dark-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-yellow-500 to-yellow-400 rounded-full transition-all duration-500"
                                    style={{ width: `${getPercentage(statusData.pending)}%` }}
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex justify-between mb-1">
                                <span className="text-dark-300 text-sm">Successful</span>
                                <span className="text-dark-400 text-sm">{statusData.successful}</span>
                            </div>
                            <div className="h-3 bg-dark-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full transition-all duration-500"
                                    style={{ width: `${getPercentage(statusData.successful)}%` }}
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex justify-between mb-1">
                                <span className="text-dark-300 text-sm">Failed</span>
                                <span className="text-dark-400 text-sm">{statusData.failed}</span>
                            </div>
                            <div className="h-3 bg-dark-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-red-500 to-red-400 rounded-full transition-all duration-500"
                                    style={{ width: `${getPercentage(statusData.failed)}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Processing Rate */}
                <div className="glass-card p-6">
                    <div className="flex items-center gap-2 mb-6">
                        <TrendingUp className="w-5 h-5 text-primary-400" />
                        <h3 className="text-lg font-semibold text-dark-100">Processing Metrics</h3>
                    </div>

                    <div className="space-y-6">
                        {/* Success Rate Circle */}
                        <div className="flex items-center gap-6">
                            <div className="relative w-32 h-32">
                                <svg className="w-full h-full transform -rotate-90">
                                    <circle
                                        cx="64"
                                        cy="64"
                                        r="56"
                                        stroke="currentColor"
                                        strokeWidth="8"
                                        fill="transparent"
                                        className="text-dark-800"
                                    />
                                    <circle
                                        cx="64"
                                        cy="64"
                                        r="56"
                                        stroke="url(#gradient)"
                                        strokeWidth="8"
                                        fill="transparent"
                                        strokeDasharray={`${(analytics?.processing_rate || 0) * 3.52} 352`}
                                        className="transition-all duration-500"
                                    />
                                    <defs>
                                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                            <stop offset="0%" stopColor="#0ea5e9" />
                                            <stop offset="100%" stopColor="#38bdf8" />
                                        </linearGradient>
                                    </defs>
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <span className="text-2xl font-bold gradient-text">
                                        {analytics?.processing_rate || 0}%
                                    </span>
                                </div>
                            </div>
                            <div>
                                <p className="text-dark-200 font-medium">Success Rate</p>
                                <p className="text-dark-400 text-sm mt-1">
                                    Based on {statusData.successful + statusData.failed} processed documents
                                </p>
                            </div>
                        </div>

                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-dark-800/30 rounded-xl">
                                <CheckCircle2 className="w-5 h-5 text-green-400 mb-2" />
                                <p className="text-dark-400 text-sm">Successful</p>
                                <p className="text-xl font-semibold text-dark-100">{statusData.successful}</p>
                            </div>
                            <div className="p-4 bg-dark-800/30 rounded-xl">
                                <AlertCircle className="w-5 h-5 text-red-400 mb-2" />
                                <p className="text-dark-400 text-sm">Failed</p>
                                <p className="text-xl font-semibold text-dark-100">{statusData.failed}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Activity */}
            {analytics?.recent_uploads?.length > 0 && (
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold text-dark-100 mb-4">Recent Activity</h3>
                    <div className="overflow-x-auto">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Document</th>
                                    <th>Status</th>
                                    <th>Uploaded</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analytics.recent_uploads.map((upload) => (
                                    <tr key={upload.id}>
                                        <td>
                                            <div className="flex items-center gap-2">
                                                <FileText className="w-4 h-4 text-dark-400" />
                                                <span className="text-dark-200">{upload.file_name}</span>
                                            </div>
                                        </td>
                                        <td>
                                            <span className={`badge badge-${upload.status}`}>
                                                {upload.status}
                                            </span>
                                        </td>
                                        <td className="text-dark-400">
                                            {new Date(upload.uploaded_at).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminAnalytics;
