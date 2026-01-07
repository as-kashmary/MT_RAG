/**
 * Document List Component
 * Table view of documents with upload (requires product selection) and delete functionality.
 * Shows product association for each document.
 */

import { useState, useEffect } from 'react';
import { documentsAPI, productsAPI } from '../services/api';
import {
    FileText,
    Upload,
    Trash2,
    Loader2,
    AlertCircle,
    RefreshCw,
    Search,
    CheckCircle,
    Package,
    ChevronRight
} from 'lucide-react';
import Modal from './ui/Modal';

function DocumentList() {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');

    // Upload modal state
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [uploadStep, setUploadStep] = useState(1); // 1: select product, 2: select file
    const [products, setProducts] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState('');
    const [uploadFile, setUploadFile] = useState(null);
    const [uploadFileName, setUploadFileName] = useState('');
    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState('');
    const [uploadSuccess, setUploadSuccess] = useState('');
    const [loadingProducts, setLoadingProducts] = useState(false);

    // Delete modal state
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [documentToDelete, setDocumentToDelete] = useState(null);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        fetchDocuments();
    }, []);

    useEffect(() => {
        if (showUploadModal) {
            fetchProducts();
        }
    }, [showUploadModal]);

    const fetchDocuments = async () => {
        setLoading(true);
        setError('');
        try {
            const data = await documentsAPI.list();
            setDocuments(data.documents || []);
        } catch (err) {
            setError('Failed to load documents');
            console.error('Documents error:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchProducts = async () => {
        setLoadingProducts(true);
        try {
            const data = await productsAPI.list();
            setProducts(data.products || []);
        } catch (err) {
            console.error('Products error:', err);
        } finally {
            setLoadingProducts(false);
        }
    };

    const handleProductSelect = (productId) => {
        setSelectedProduct(productId);
        setUploadStep(2);
    };

    const handleFileSelect = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            setUploadFile(file);
            setUploadFileName(file.name);
            setUploadError('');
        }
    };

    const handleUpload = async () => {
        if (!uploadFile || !uploadFileName.trim() || !selectedProduct) {
            setUploadError('Please select a product and file');
            return;
        }

        setUploading(true);
        setUploadError('');
        setUploadSuccess('');

        try {
            await documentsAPI.upload(uploadFile, uploadFileName, selectedProduct);
            setUploadSuccess('Document uploaded successfully!');
            fetchDocuments();
            setTimeout(() => {
                resetUploadModal();
            }, 1500);
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Failed to upload document';
            setUploadError(errorMsg);
        } finally {
            setUploading(false);
        }
    };

    const handleDeleteClick = (doc) => {
        setDocumentToDelete(doc);
        setShowDeleteModal(true);
    };

    const handleDeleteConfirm = async () => {
        if (!documentToDelete) return;

        setDeleting(true);
        try {
            await documentsAPI.delete(documentToDelete.id);
            fetchDocuments();
            setShowDeleteModal(false);
            setDocumentToDelete(null);
        } catch (err) {
            console.error('Delete error:', err);
        } finally {
            setDeleting(false);
        }
    };

    const resetUploadModal = () => {
        setShowUploadModal(false);
        setUploadStep(1);
        setSelectedProduct('');
        setUploadFile(null);
        setUploadFileName('');
        setUploadError('');
        setUploadSuccess('');
    };

    const getStatusBadge = (status) => {
        const badgeClass = `badge badge-${status}`;
        return <span className={badgeClass}>{status}</span>;
    };

    const filteredDocuments = documents.filter(doc =>
        doc.file_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (doc.product_name && doc.product_name.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const formatDate = (dateStr) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getSelectedProductName = () => {
        const product = products.find(p => p.id === selectedProduct);
        return product?.name || '';
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-dark-100">Documents</h1>
                    <p className="text-dark-400 mt-1">Manage your uploaded documents</p>
                </div>
                <button
                    onClick={() => setShowUploadModal(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <Upload className="w-5 h-5" />
                    Upload Document
                </button>
            </div>

            {/* Search Bar */}
            <div className="glass-card p-4">
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
                    <input
                        type="text"
                        placeholder="Search by document name or product..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="input-field pl-12"
                    />
                </div>
            </div>

            {/* Documents Table */}
            <div className="glass-card overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
                    </div>
                ) : error ? (
                    <div className="p-8 text-center">
                        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                        <p className="text-red-400 mb-4">{error}</p>
                        <button onClick={fetchDocuments} className="btn-secondary flex items-center gap-2 mx-auto">
                            <RefreshCw className="w-4 h-4" />
                            Retry
                        </button>
                    </div>
                ) : filteredDocuments.length === 0 ? (
                    <div className="p-8 text-center">
                        <FileText className="w-12 h-12 text-dark-500 mx-auto mb-4" />
                        <p className="text-dark-400">
                            {searchTerm ? 'No documents match your search' : 'No documents uploaded yet'}
                        </p>
                        {!searchTerm && (
                            <button
                                onClick={() => setShowUploadModal(true)}
                                className="btn-primary mt-4 inline-flex items-center gap-2"
                            >
                                <Upload className="w-4 h-4" />
                                Upload Your First Document
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Product</th>
                                    <th>Format</th>
                                    <th>Status</th>
                                    <th>Uploaded</th>
                                    <th className="text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredDocuments.map((doc) => (
                                    <tr key={doc.id}>
                                        <td>
                                            <div className="flex items-center gap-3">
                                                <FileText className="w-5 h-5 text-dark-400" />
                                                <span className="text-dark-200 font-medium">{doc.file_name}</span>
                                            </div>
                                        </td>
                                        <td>
                                            {doc.product_name ? (
                                                <div className="flex items-center gap-2">
                                                    <Package className="w-4 h-4 text-primary-400" />
                                                    <span className="text-dark-300">{doc.product_name}</span>
                                                </div>
                                            ) : (
                                                <span className="text-dark-500 italic">No product</span>
                                            )}
                                        </td>
                                        <td className="text-dark-400">{doc.file_format}</td>
                                        <td>{getStatusBadge(doc.status)}</td>
                                        <td className="text-dark-400">{formatDate(doc.uploaded_at)}</td>
                                        <td className="text-right">
                                            <button
                                                onClick={() => handleDeleteClick(doc)}
                                                className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                                title="Delete document"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Upload Modal */}
            <Modal
                isOpen={showUploadModal}
                onClose={resetUploadModal}
                title="Upload Document"
            >
                <div className="space-y-4">
                    {uploadSuccess ? (
                        <div className="flex flex-col items-center py-4">
                            <CheckCircle className="w-16 h-16 text-green-400 mb-4" />
                            <p className="text-green-400 font-medium">{uploadSuccess}</p>
                        </div>
                    ) : (
                        <>
                            {/* Progress Steps */}
                            <div className="flex items-center gap-3 mb-4">
                                <div className={`flex items-center gap-2 ${uploadStep >= 1 ? 'text-primary-400' : 'text-dark-500'}`}>
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${uploadStep >= 1 ? 'bg-primary-500 text-white' : 'bg-dark-700 text-dark-400'}`}>1</div>
                                    <span className="text-sm">Select Product</span>
                                </div>
                                <ChevronRight className="w-4 h-4 text-dark-600" />
                                <div className={`flex items-center gap-2 ${uploadStep >= 2 ? 'text-primary-400' : 'text-dark-500'}`}>
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${uploadStep >= 2 ? 'bg-primary-500 text-white' : 'bg-dark-700 text-dark-400'}`}>2</div>
                                    <span className="text-sm">Upload File</span>
                                </div>
                            </div>

                            {uploadError && (
                                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                    {uploadError}
                                </div>
                            )}

                            {/* Step 1: Select Product */}
                            {uploadStep === 1 && (
                                <div className="animate-fade-in">
                                    <label className="input-label flex items-center gap-2">
                                        <Package className="w-4 h-4 text-primary-400" />
                                        Choose Target Product
                                    </label>
                                    {loadingProducts ? (
                                        <div className="flex items-center justify-center py-8">
                                            <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
                                        </div>
                                    ) : products.length === 0 ? (
                                        <div className="text-center py-6">
                                            <Package className="w-10 h-10 text-dark-500 mx-auto mb-2" />
                                            <p className="text-dark-400 text-sm">No products available</p>
                                            <p className="text-dark-500 text-xs mt-1">Create a product first from the Products page</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-2 max-h-60 overflow-y-auto">
                                            {products.map((product) => (
                                                <button
                                                    key={product.id}
                                                    onClick={() => handleProductSelect(product.id)}
                                                    className="w-full p-3 bg-dark-800/50 hover:bg-dark-700/50 border border-dark-700 hover:border-primary-500/50 rounded-lg text-left transition-all flex items-center justify-between group"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <Package className="w-5 h-5 text-dark-400 group-hover:text-primary-400" />
                                                        <span className="text-dark-200 font-medium">{product.name}</span>
                                                    </div>
                                                    <ChevronRight className="w-4 h-4 text-dark-500 group-hover:text-primary-400" />
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Step 2: Upload File */}
                            {uploadStep === 2 && (
                                <div className="animate-fade-in">
                                    {/* Selected Product Badge */}
                                    <div className="flex items-center gap-2 p-2 bg-primary-500/10 border border-primary-500/30 rounded-lg mb-4">
                                        <Package className="w-4 h-4 text-primary-400" />
                                        <span className="text-primary-300 text-sm">Uploading to: <strong>{getSelectedProductName()}</strong></span>
                                        <button
                                            onClick={() => setUploadStep(1)}
                                            className="ml-auto text-primary-400 hover:text-primary-300 text-xs underline"
                                        >
                                            Change
                                        </button>
                                    </div>

                                    {/* File Selection */}
                                    <div>
                                        <label className="input-label flex items-center gap-2">
                                            <Upload className="w-4 h-4 text-primary-400" />
                                            Select File
                                        </label>
                                        <div className="border-2 border-dashed rounded-xl p-6 text-center transition-colors border-dark-600 hover:border-primary-500/50 cursor-pointer">
                                            <input
                                                type="file"
                                                id="file-upload"
                                                className="hidden"
                                                onChange={handleFileSelect}
                                                accept=".pdf,.txt,.docx"
                                            />
                                            <label htmlFor="file-upload" className="cursor-pointer">
                                                <Upload className="w-8 h-8 text-dark-400 mx-auto mb-2" />
                                                <p className="text-dark-200 font-medium text-sm">
                                                    {uploadFile ? uploadFile.name : 'Click to select a file'}
                                                </p>
                                                <p className="text-dark-500 text-xs mt-1">
                                                    Supports PDF, TXT, DOCX
                                                </p>
                                            </label>
                                        </div>
                                    </div>

                                    {/* File Name Input */}
                                    {uploadFile && (
                                        <div className="animate-fade-in mt-4">
                                            <label className="input-label">Document Name</label>
                                            <input
                                                type="text"
                                                value={uploadFileName}
                                                onChange={(e) => setUploadFileName(e.target.value)}
                                                className="input-field"
                                                placeholder="Enter document name"
                                            />
                                        </div>
                                    )}

                                    {/* Actions */}
                                    <div className="flex gap-3 pt-4">
                                        <button
                                            onClick={() => setUploadStep(1)}
                                            className="btn-secondary flex-1"
                                        >
                                            Back
                                        </button>
                                        <button
                                            onClick={handleUpload}
                                            disabled={uploading || !uploadFile}
                                            className="btn-primary flex-1 flex items-center justify-center gap-2"
                                        >
                                            {uploading ? (
                                                <>
                                                    <Loader2 className="w-4 h-4 animate-spin" />
                                                    Uploading...
                                                </>
                                            ) : (
                                                <>
                                                    <Upload className="w-4 h-4" />
                                                    Upload
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Cancel at Step 1 */}
                            {uploadStep === 1 && (
                                <div className="pt-2">
                                    <button
                                        onClick={resetUploadModal}
                                        className="btn-secondary w-full"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </Modal>

            {/* Delete Confirmation Modal */}
            <Modal
                isOpen={showDeleteModal}
                onClose={() => {
                    setShowDeleteModal(false);
                    setDocumentToDelete(null);
                }}
                title="Delete Document"
            >
                <div className="space-y-4">
                    <p className="text-dark-300">
                        Are you sure you want to delete <span className="text-dark-100 font-medium">"{documentToDelete?.file_name}"</span>? This action cannot be undone.
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
                                    Delete
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}

export default DocumentList;
