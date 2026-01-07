/**
 * Dashboard Home Component
 * Welcome page with quick stats overview.
 * Simplified to show Total Documents, Successful, and Failed counts.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { analyticsAPI } from '../services/api';
import {
    FileText,
    CheckCircle2,
    AlertCircle,
    Loader2,
    TrendingUp,
    Clock
} from 'lucide-react';

function DashboardHome() {
    const { admin } = useAuth();
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

    const stats = analytics ? [
        {
            label: 'Total Documents',
            value: analytics.total_documents,
            icon: FileText,
            color: 'from-blue-500 to-blue-600',
            bgColor: 'bg-blue-500/10',
            iconColor: '#3b82f6'
        },
        {
            label: 'Pending',
            value: analytics.document_status.pending || 0,
            icon: Clock,
            color: 'from-yellow-500 to-yellow-600',
            bgColor: 'bg-yellow-500/10',
            iconColor: '#eab308'
        },
        {
            label: 'Successful',
            value: analytics.document_status.successful,
            icon: CheckCircle2,
            color: 'from-green-500 to-green-600',
            bgColor: 'bg-green-500/10',
            iconColor: '#22c55e'
        },
        {
            label: 'Failed',
            value: analytics.document_status.failed,
            icon: AlertCircle,
            color: 'from-red-500 to-red-600',
            bgColor: 'bg-red-500/10',
            iconColor: '#ef4444'
        },
    ] : [];

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-dark-100">
                    Welcome back, <span className="gradient-text">{admin?.username || 'Admin'}</span>
                </h1>
                <p className="text-dark-400 mt-2">
                    Here's an overview of your document management status
                </p>
            </div>

            {/* Stats Grid */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
                </div>
            ) : error ? (
                <div className="glass-card p-8 text-center">
                    <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <p className="text-red-400">{error}</p>
                    <button
                        onClick={fetchAnalytics}
                        className="btn-secondary mt-4"
                    >
                        Retry
                    </button>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {stats.map((stat, index) => (
                            <div
                                key={stat.label}
                                className="stat-card animate-slide-up"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-dark-400 text-sm font-medium">
                                            {stat.label}
                                        </p>
                                        <p className="text-3xl font-bold text-dark-100 mt-2">
                                            {stat.value}
                                        </p>
                                    </div>
                                    <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                                        <stat.icon className="w-6 h-6" style={{ color: stat.iconColor }} />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Processing Rate Card */}
                    <div className="glass-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-dark-100">Processing Success Rate</h3>
                            <TrendingUp className="w-5 h-5 text-primary-400" />
                        </div>
                        <div className="flex items-end gap-4">
                            <span className="text-4xl font-bold gradient-text">
                                {analytics?.processing_rate || 0}%
                            </span>
                            <span className="text-dark-400 mb-1">of documents processed successfully</span>
                        </div>
                        <div className="mt-4 h-2 bg-dark-800 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full transition-all duration-500"
                                style={{ width: `${analytics?.processing_rate || 0}%` }}
                            />
                        </div>
                    </div>

                    {/* Recent Activity */}
                    {analytics?.recent_uploads?.length > 0 && (
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold text-dark-100 mb-4">Recent Uploads</h3>
                            <div className="space-y-3">
                                {analytics.recent_uploads.map((upload) => (
                                    <div
                                        key={upload.id}
                                        className="flex items-center justify-between p-3 bg-dark-800/30 rounded-xl"
                                    >
                                        <div className="flex items-center gap-3">
                                            <FileText className="w-5 h-5 text-dark-400" />
                                            <span className="text-dark-200">{upload.file_name}</span>
                                        </div>
                                        <span className={`badge badge-${upload.status}`}>
                                            {upload.status}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

export default DashboardHome;
