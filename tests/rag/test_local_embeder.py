"""
Tests for local_embeder.py - Local HuggingFace Embeddings.

This module tests:
- LocalEmbeddings class initialization
- _load_model: Lazy model loading
- embed_documents: Batch document embedding
- embed_query: Single query embedding
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


class TestLocalEmbeddings:
    """Tests for the LocalEmbeddings class."""
    
    def test_initialization(self):
        """Test LocalEmbeddings initialization with lazy loading."""
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="test-model-path")
        
        assert embeddings.model_name == "test-model-path"
        assert embeddings.model is None  # Lazy loading - model not loaded yet
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_load_model(self, mock_hf_embeddings):
        """Test lazy model loading."""
        mock_model = MagicMock()
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        # Model should not be loaded yet
        assert embeddings.model is None
        
        # Load the model
        embeddings._load_model()
        
        # Model should now be loaded
        assert embeddings.model == mock_model
        mock_hf_embeddings.assert_called_once_with(model_name="./models/test-model")
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_load_model_only_once(self, mock_hf_embeddings):
        """Test that model is only loaded once (cached)."""
        mock_model = MagicMock()
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        # Load multiple times
        embeddings._load_model()
        embeddings._load_model()
        embeddings._load_model()
        
        # Should only be called once
        mock_hf_embeddings.assert_called_once()
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_embed_documents(self, mock_hf_embeddings):
        """Test embedding multiple documents."""
        mock_model = MagicMock()
        mock_model.embed_documents.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        documents = ["First document", "Second document"]
        result = embeddings.embed_documents(documents)
        
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        mock_model.embed_documents.assert_called_once_with(documents)
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_embed_documents_triggers_load(self, mock_hf_embeddings):
        """Test that embed_documents triggers lazy loading."""
        mock_model = MagicMock()
        mock_model.embed_documents.return_value = [[0.1, 0.2]]
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        # Model not loaded yet
        assert embeddings.model is None
        
        # Call embed_documents which should trigger load
        embeddings.embed_documents(["Test"])
        
        # Model should now be loaded
        assert embeddings.model is not None
        mock_hf_embeddings.assert_called_once()
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_embed_query(self, mock_hf_embeddings):
        """Test embedding a single query."""
        mock_model = MagicMock()
        mock_model.embed_query.return_value = [0.7, 0.8, 0.9]
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        result = embeddings.embed_query("What is AI?")
        
        assert result == [0.7, 0.8, 0.9]
        mock_model.embed_query.assert_called_once_with("What is AI?")
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_embed_query_triggers_load(self, mock_hf_embeddings):
        """Test that embed_query triggers lazy loading."""
        mock_model = MagicMock()
        mock_model.embed_query.return_value = [0.1]
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        # Model not loaded yet
        assert embeddings.model is None
        
        # Call embed_query which should trigger load
        embeddings.embed_query("Test query")
        
        # Model should now be loaded
        assert embeddings.model is not None
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_embed_documents_empty_list(self, mock_hf_embeddings):
        """Test embedding an empty document list."""
        mock_model = MagicMock()
        mock_model.embed_documents.return_value = []
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        result = embeddings.embed_documents([])
        
        assert result == []
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_embed_query_empty_string(self, mock_hf_embeddings):
        """Test embedding an empty query string."""
        mock_model = MagicMock()
        mock_model.embed_query.return_value = [0.0, 0.0, 0.0]
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        result = embeddings.embed_query("")
        
        assert result == [0.0, 0.0, 0.0]


class TestLocalEmbeddingsIntegration:
    """Integration-style tests for LocalEmbeddings."""
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_multiple_calls_same_model(self, mock_hf_embeddings):
        """Test multiple embedding calls use the same loaded model."""
        mock_model = MagicMock()
        mock_model.embed_documents.return_value = [[0.1]]
        mock_model.embed_query.return_value = [0.2]
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/test-model")
        
        # Multiple calls
        embeddings.embed_documents(["Doc 1"])
        embeddings.embed_query("Query 1")
        embeddings.embed_documents(["Doc 2", "Doc 3"])
        embeddings.embed_query("Query 2")
        
        # Model should only be instantiated once
        assert mock_hf_embeddings.call_count == 1
    
    @patch('src.rag.local_embeder.HuggingFaceEmbeddings')
    def test_high_dimensional_embeddings(self, mock_hf_embeddings):
        """Test handling of high-dimensional embeddings (768-dim common)."""
        mock_model = MagicMock()
        mock_model.embed_documents.return_value = [[0.1] * 768]
        mock_model.embed_query.return_value = [0.2] * 768
        mock_hf_embeddings.return_value = mock_model
        
        from src.rag.local_embeder import LocalEmbeddings
        
        embeddings = LocalEmbeddings(model_name="./models/multilingual-e5-large")
        
        doc_result = embeddings.embed_documents(["Test document"])
        query_result = embeddings.embed_query("Test query")
        
        assert len(doc_result[0]) == 768
        assert len(query_result) == 768
