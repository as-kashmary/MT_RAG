"""
Tests for embeder.py - HuggingFace Inference Embeddings.

This module tests:
- HFInferenceEmbeddings class initialization
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


class TestHFInferenceEmbeddings:
    """Tests for the HFInferenceEmbeddings class."""
    
    @patch('src.rag.embeder.InferenceClient')
    def test_initialization(self, mock_client):
        """Test HFInferenceEmbeddings initialization."""
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-api-key"
        )
        
        assert embeddings.model == "test-model"
        mock_client.assert_called_once_with(
            provider="hf-inference",
            api_key="test-api-key"
        )
    
    @patch('src.rag.embeder.InferenceClient')
    def test_embed_documents_single(self, mock_client):
        """Test embedding a single document."""
        import numpy as np
        
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.feature_extraction.return_value = np.array([0.1, 0.2, 0.3])
        mock_client.return_value = mock_instance
        
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-key"
        )
        
        result = embeddings.embed_documents(["Test document"])
        
        assert len(result) == 1
        assert result[0] == [0.1, 0.2, 0.3]
        mock_instance.feature_extraction.assert_called_once_with(
            "Test document",
            model="test-model"
        )
    
    @patch('src.rag.embeder.InferenceClient')
    def test_embed_documents_multiple(self, mock_client):
        """Test embedding multiple documents."""
        import numpy as np
        
        # Setup mock to return different embeddings for each call
        mock_instance = MagicMock()
        mock_instance.feature_extraction.side_effect = [
            np.array([0.1, 0.2]),
            np.array([0.3, 0.4]),
            np.array([0.5, 0.6])
        ]
        mock_client.return_value = mock_instance
        
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-key"
        )
        
        documents = [
            "First document",
            "Second document",
            "Third document"
        ]
        
        result = embeddings.embed_documents(documents)
        
        assert len(result) == 3
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
        assert result[2] == [0.5, 0.6]
        assert mock_instance.feature_extraction.call_count == 3
    
    @patch('src.rag.embeder.InferenceClient')
    def test_embed_documents_empty_list(self, mock_client):
        """Test embedding an empty document list."""
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-key"
        )
        
        result = embeddings.embed_documents([])
        
        assert result == []
    
    @patch('src.rag.embeder.InferenceClient')
    def test_embed_query(self, mock_client):
        """Test embedding a single query."""
        import numpy as np
        
        mock_instance = MagicMock()
        mock_instance.feature_extraction.return_value = np.array([0.5, 0.6, 0.7])
        mock_client.return_value = mock_instance
        
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="multilingual-e5-large",
            api_key="test-key"
        )
        
        result = embeddings.embed_query("What is machine learning?")
        
        assert result == [0.5, 0.6, 0.7]
        mock_instance.feature_extraction.assert_called_with(
            "What is machine learning?",
            model="multilingual-e5-large"
        )
    
    @patch('src.rag.embeder.InferenceClient')
    def test_embed_query_empty_string(self, mock_client):
        """Test embedding an empty query string."""
        import numpy as np
        
        mock_instance = MagicMock()
        mock_instance.feature_extraction.return_value = np.array([0.0, 0.0, 0.0])
        mock_client.return_value = mock_instance
        
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-key"
        )
        
        result = embeddings.embed_query("")
        
        assert result == [0.0, 0.0, 0.0]
    
    @patch('src.rag.embeder.InferenceClient')
    def test_embed_documents_long_text(self, mock_client):
        """Test embedding a very long document."""
        import numpy as np
        
        mock_instance = MagicMock()
        mock_instance.feature_extraction.return_value = np.array([0.1] * 768)
        mock_client.return_value = mock_instance
        
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-key"
        )
        
        long_document = "word " * 10000  # Very long document
        result = embeddings.embed_documents([long_document])
        
        assert len(result) == 1
        assert len(result[0]) == 768
    
    @patch('src.rag.embeder.InferenceClient')
    def test_embed_documents_unicode_text(self, mock_client):
        """Test embedding documents with unicode characters."""
        import numpy as np
        
        mock_instance = MagicMock()
        mock_instance.feature_extraction.return_value = np.array([0.2, 0.3, 0.4])
        mock_client.return_value = mock_instance
        
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-key"
        )
        
        unicode_docs = [
            "日本語テキスト",
            "中文文本",
            "Текст на русском"
        ]
        
        result = embeddings.embed_documents(unicode_docs)
        
        assert len(result) == 3
        assert mock_instance.feature_extraction.call_count == 3


class TestHFInferenceEmbeddingsErrors:
    """Tests for error handling in HFInferenceEmbeddings."""
    
    @patch('src.rag.embeder.InferenceClient')
    def test_api_error_handling(self, mock_client):
        """Test handling of API errors during embedding."""
        mock_instance = MagicMock()
        mock_instance.feature_extraction.side_effect = Exception("API rate limit exceeded")
        mock_client.return_value = mock_instance
        
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-key"
        )
        
        with pytest.raises(Exception) as exc_info:
            embeddings.embed_documents(["Test document"])
        
        assert "API rate limit exceeded" in str(exc_info.value)
    
    @patch('src.rag.embeder.InferenceClient')
    def test_network_error_handling(self, mock_client):
        """Test handling of network errors."""
        mock_instance = MagicMock()
        mock_instance.feature_extraction.side_effect = ConnectionError("Network unreachable")
        mock_client.return_value = mock_instance
        
        from src.rag.embeder import HFInferenceEmbeddings
        
        embeddings = HFInferenceEmbeddings(
            model="test-model",
            api_key="test-key"
        )
        
        with pytest.raises(ConnectionError):
            embeddings.embed_query("Test query")
