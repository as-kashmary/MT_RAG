/**
 * Manage Admins Component
 * Allows executives (CTO/CEO) to view and delete admins from their company.
 */

import { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';
import Button from './ui/Button';
import { ToastContainer, useToast } from './ui/Toast';

const ManageAdmins = () => {
    const { toasts, addToast, removeToast } = useToast();

    const [admins, setAdmins] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [adminToDelete, setAdminToDelete] = useState(null);
    const [deleting, setDeleting] = useState(false);

    // Fetch admins on component mount
    useEffect(() => {
        fetchAdmins();
    }, []);

    const fetchAdmins = async () => {
        setLoading(true);
        try {
            const response = await adminAPI.listAdmins();
            setAdmins(response.admins || []);
        } catch (err) {
            addToast(err.response?.data?.detail || 'Failed to load admins', 'error');
        } finally {
            setLoading(false);
        }
    };

    const openDeleteModal = (admin) => {
        setAdminToDelete(admin);
        setDeleteModalOpen(true);
    };

    const closeDeleteModal = () => {
        setDeleteModalOpen(false);
        setAdminToDelete(null);
    };

    const handleDelete = async () => {
        if (!adminToDelete) return;

        setDeleting(true);
        try {
            await adminAPI.deleteAdmin(adminToDelete.admin_id);
            addToast(`Admin '${adminToDelete.username}' has been deleted`, 'success');
            setAdmins(admins.filter(a => a.admin_id !== adminToDelete.admin_id));
            closeDeleteModal();
        } catch (err) {
            addToast(err.response?.data?.detail || 'Failed to delete admin', 'error');
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div className="space-y-8">
            <ToastContainer toasts={toasts} removeToast={removeToast} />

            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-dark-100 mb-2">Manage Admins</h1>
                    <p className="text-dark-400">
                        View and manage admin accounts for your company.
                    </p>
                </div>
                <Button onClick={fetchAdmins} variant="secondary" disabled={loading}>
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh
                </Button>
            </div>

            {/* Admin List */}
            <div className="glass-card overflow-hidden">
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-16">
                        <svg className="w-8 h-8 text-primary-400 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <p className="text-dark-400">Loading admins...</p>
                    </div>
                ) : admins.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                        <div className="w-16 h-16 bg-dark-800/50 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-8 h-8 text-dark-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                            </svg>
                        </div>
                        <p className="text-dark-400 mb-2">No admins found</p>
                        <p className="text-dark-500 text-sm">Invite admins from the "Invite Admin" page</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-dark-700/50">
                                    <th className="px-6 py-4 text-left text-sm font-semibold text-dark-300">#</th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold text-dark-300">Username</th>
                                    <th className="px-6 py-4 text-left text-sm font-semibold text-dark-300">Admin ID</th>
                                    <th className="px-6 py-4 text-right text-sm font-semibold text-dark-300">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {admins.map((admin, index) => (
                                    <tr
                                        key={admin.admin_id}
                                        className="border-b border-dark-700/30 hover:bg-dark-800/30 transition-colors"
                                    >
                                        <td className="px-6 py-4 text-dark-400">{index + 1}</td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold">
                                                    {admin.username?.charAt(0)?.toUpperCase() || 'A'}
                                                </div>
                                                <span className="font-medium text-dark-100">{admin.username}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <code className="text-xs text-dark-400 bg-dark-800/50 px-2 py-1 rounded">
                                                {admin.admin_id}
                                            </code>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => openDeleteModal(admin)}
                                                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all duration-200"
                                            >
                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Total Count */}
            {!loading && admins.length > 0 && (
                <div className="text-center text-dark-400 text-sm">
                    Total: {admins.length} admin{admins.length !== 1 ? 's' : ''}
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deleteModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-dark-950/80 backdrop-blur-sm"
                        onClick={closeDeleteModal}
                    ></div>

                    {/* Modal */}
                    <div className="relative glass-card p-6 max-w-md w-full animate-fade-in">
                        <div className="flex items-start gap-4">
                            <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center flex-shrink-0">
                                <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                            </div>
                            <div className="flex-1">
                                <h3 className="text-lg font-semibold text-dark-100 mb-2">Delete Admin</h3>
                                <p className="text-dark-400 mb-4">
                                    Are you sure you want to delete <span className="font-medium text-dark-100">{adminToDelete?.username}</span>? This action cannot be undone.
                                </p>

                                <div className="flex gap-3 justify-end">
                                    <button
                                        onClick={closeDeleteModal}
                                        disabled={deleting}
                                        className="px-4 py-2 text-sm font-medium text-dark-300 hover:text-dark-100 hover:bg-dark-700/50 rounded-lg transition-all duration-200"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleDelete}
                                        disabled={deleting}
                                        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg transition-all duration-200 disabled:opacity-50"
                                    >
                                        {deleting ? (
                                            <>
                                                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                                Deleting...
                                            </>
                                        ) : (
                                            <>
                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                                Delete Admin
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ManageAdmins;
