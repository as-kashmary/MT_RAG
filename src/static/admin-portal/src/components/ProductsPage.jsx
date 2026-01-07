/**
 * Products Management Page
 * CRUD operations for products with document count display.
 */

import { useState, useEffect } from 'react';
import { productsAPI } from '../services/api';
import {
    Package,
    Plus,
    Edit3,
    Trash2,
    Loader2,
    AlertCircle,
    RefreshCw,
    FileText,
    CheckCircle
} from 'lucide-react';
import Modal from './ui/Modal';

function ProductsPage() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Create/Edit modal state
    const [showModal, setShowModal] = useState(false);
    const [editingProduct, setEditingProduct] = useState(null);
    const [productName, setProductName] = useState('');
    const [saving, setSaving] = useState(false);
    const [modalError, setModalError] = useState('');
    const [modalSuccess, setModalSuccess] = useState('');

    // Delete modal state
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [productToDelete, setProductToDelete] = useState(null);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        setLoading(true);
        setError('');
        try {
            const data = await productsAPI.list();
            setProducts(data.products || []);
        } catch (err) {
            setError('Failed to load products');
            console.error('Products error:', err);
        } finally {
            setLoading(false);
        }
    };

    const openCreateModal = () => {
        setEditingProduct(null);
        setProductName('');
        setModalError('');
        setModalSuccess('');
        setShowModal(true);
    };

    const openEditModal = (product) => {
        setEditingProduct(product);
        setProductName(product.name);
        setModalError('');
        setModalSuccess('');
        setShowModal(true);
    };

    const handleSave = async () => {
        if (!productName.trim()) {
            setModalError('Please enter a product name');
            return;
        }

        setSaving(true);
        setModalError('');
        setModalSuccess('');

        try {
            if (editingProduct) {
                await productsAPI.update(editingProduct.id, { name: productName });
                setModalSuccess('Product updated successfully!');
            } else {
                await productsAPI.create({ name: productName });
                setModalSuccess('Product created successfully!');
            }

            fetchProducts();
            setTimeout(() => {
                setShowModal(false);
                setModalSuccess('');
            }, 1500);
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Failed to save product';
            setModalError(errorMsg);
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteClick = (product) => {
        setProductToDelete(product);
        setShowDeleteModal(true);
    };

    const handleDeleteConfirm = async () => {
        if (!productToDelete) return;

        setDeleting(true);
        try {
            await productsAPI.delete(productToDelete.id);
            fetchProducts();
            setShowDeleteModal(false);
            setProductToDelete(null);
        } catch (err) {
            console.error('Delete error:', err);
        } finally {
            setDeleting(false);
        }
    };



    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-dark-100">Products</h1>
                    <p className="text-dark-400 mt-1">Manage your products and their associated documents</p>
                </div>
                <button
                    onClick={openCreateModal}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus className="w-5 h-5" />
                    Add Product
                </button>
            </div>

            {/* Products Grid */}
            <div className="glass-card overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
                    </div>
                ) : error ? (
                    <div className="p-8 text-center">
                        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                        <p className="text-red-400 mb-4">{error}</p>
                        <button onClick={fetchProducts} className="btn-secondary flex items-center gap-2 mx-auto">
                            <RefreshCw className="w-4 h-4" />
                            Retry
                        </button>
                    </div>
                ) : products.length === 0 ? (
                    <div className="p-8 text-center">
                        <Package className="w-12 h-12 text-dark-500 mx-auto mb-4" />
                        <p className="text-dark-400">No products yet</p>
                        <button
                            onClick={openCreateModal}
                            className="btn-primary mt-4 inline-flex items-center gap-2"
                        >
                            <Plus className="w-4 h-4" />
                            Create Your First Product
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
                        {products.map((product) => (
                            <div
                                key={product.id}
                                className="bg-dark-800/50 rounded-xl p-5 border border-dark-700 hover:border-primary-500/50 transition-all"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-primary-500/10 rounded-lg">
                                            <Package className="w-5 h-5 text-primary-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-dark-100 font-semibold">{product.name}</h3>
                                            {product.description && (
                                                <p className="text-dark-500 text-xs mt-0.5">{product.description}</p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex gap-1">
                                        <button
                                            onClick={() => openEditModal(product)}
                                            className="p-2 text-dark-400 hover:text-primary-400 hover:bg-primary-500/10 rounded-lg transition-colors"
                                            title="Edit product"
                                        >
                                            <Edit3 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteClick(product)}
                                            className="p-2 text-dark-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                            title="Delete product"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 text-dark-400">
                                    <FileText className="w-4 h-4" />
                                    <span className="text-sm">
                                        {product.document_count} {product.document_count === 1 ? 'document' : 'documents'}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create/Edit Modal */}
            <Modal
                isOpen={showModal}
                onClose={() => setShowModal(false)}
                title={editingProduct ? 'Edit Product' : 'Create Product'}
            >
                <div className="space-y-4">
                    {modalSuccess ? (
                        <div className="flex flex-col items-center py-4">
                            <CheckCircle className="w-16 h-16 text-green-400 mb-4" />
                            <p className="text-green-400 font-medium">{modalSuccess}</p>
                        </div>
                    ) : (
                        <>
                            {modalError && (
                                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                    {modalError}
                                </div>
                            )}

                            <div>
                                <label className="input-label">Product Name</label>
                                <input
                                    type="text"
                                    value={productName}
                                    onChange={(e) => setProductName(e.target.value)}
                                    className="input-field"
                                    placeholder="Enter product name"
                                    autoFocus
                                />
                            </div>

                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => setShowModal(false)}
                                    className="btn-secondary flex-1"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="btn-primary flex-1 flex items-center justify-center gap-2"
                                >
                                    {saving ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        editingProduct ? 'Save Changes' : 'Create Product'
                                    )}
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </Modal>

            {/* Delete Confirmation Modal */}
            <Modal
                isOpen={showDeleteModal}
                onClose={() => {
                    setShowDeleteModal(false);
                    setProductToDelete(null);
                }}
                title="Delete Product"
            >
                <div className="space-y-4">
                    <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                        <p className="text-red-400 text-sm">
                            ⚠️ Warning: Deleting this product will also delete all {productToDelete?.document_count || 0} associated documents.
                        </p>
                    </div>
                    <p className="text-dark-300">
                        Are you sure you want to delete <span className="text-dark-100 font-medium">"{productToDelete?.name}"</span>?
                    </p>
                    <div className="flex gap-3 pt-2">
                        <button
                            onClick={() => setShowDeleteModal(false)}
                            className="btn-secondary flex-1"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleDeleteConfirm}
                            disabled={deleting}
                            className="btn-danger flex-1 flex items-center justify-center gap-2"
                        >
                            {deleting ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Deleting...
                                </>
                            ) : (
                                <>
                                    <Trash2 className="w-4 h-4" />
                                    Delete Product
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}

export default ProductsPage;
