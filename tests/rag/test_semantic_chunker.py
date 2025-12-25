"""
Tests for semantic_chunker.py - Semantic Document Chunking.

This module tests:
- SemanticChunking class initialization
- Semantic chunking with different breakpoint types
- get_chunks: Retrieving chunks
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


class TestSemanticChunking:
    """Tests for the SemanticChunking class."""
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_initialization_default_params(self, mock_chunker, mock_embedding_model):
        """Test SemanticChunking initialization with default parameters."""
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = ["Chunk 1", "Chunk 2"]
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        content = "This is test content. It has multiple sentences."
        chunking = SemanticChunking(content, mock_embedding_model)
        
        mock_chunker.assert_called_once()
        call_kwargs = mock_chunker.call_args[1]
        assert call_kwargs['embeddings'] == mock_embedding_model
        assert call_kwargs['breakpoint_threshold_type'] == 'percentile'
        assert call_kwargs['breakpoint_threshold_amount'] == 90
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_initialization_custom_breakpoint_type(self, mock_chunker, mock_embedding_model):
        """Test SemanticChunking with different breakpoint types."""
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = ["Chunk 1"]
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        content = "Test content for chunking."
        
        # Test with standard_deviation
        chunking = SemanticChunking(
            content, 
            mock_embedding_model,
            breakpoint_type='standard_deviation',
            breakpoint_amount=1.5
        )
        
        call_kwargs = mock_chunker.call_args[1]
        assert call_kwargs['breakpoint_threshold_type'] == 'standard_deviation'
        assert call_kwargs['breakpoint_threshold_amount'] == 1.5
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_initialization_interquartile(self, mock_chunker, mock_embedding_model):
        """Test SemanticChunking with interquartile breakpoint type."""
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = ["Chunk"]
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        chunking = SemanticChunking(
            "Content",
            mock_embedding_model,
            breakpoint_type='interquartile'
        )
        
        call_kwargs = mock_chunker.call_args[1]
        assert call_kwargs['breakpoint_threshold_type'] == 'interquartile'
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_initialization_gradient(self, mock_chunker, mock_embedding_model):
        """Test SemanticChunking with gradient breakpoint type."""
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = ["Chunk"]
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        chunking = SemanticChunking(
            "Content",
            mock_embedding_model,
            breakpoint_type='gradient'
        )
        
        call_kwargs = mock_chunker.call_args[1]
        assert call_kwargs['breakpoint_threshold_type'] == 'gradient'
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_get_chunks(self, mock_chunker, mock_embedding_model):
        """Test retrieving chunks after initialization."""
        expected_chunks = [
            "First semantic chunk about AI.",
            "Second semantic chunk about ML.",
            "Third semantic chunk about NLP."
        ]
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = expected_chunks
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        content = "First chunk. Second chunk. Third chunk."
        chunking = SemanticChunking(content, mock_embedding_model)
        
        result = chunking.get_chunks()
        
        assert result == expected_chunks
        assert len(result) == 3
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_get_chunks_empty_content(self, mock_chunker, mock_embedding_model):
        """Test chunking with empty content."""
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = []
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        chunking = SemanticChunking("", mock_embedding_model)
        
        result = chunking.get_chunks()
        
        assert result == []
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_get_chunks_single_sentence(self, mock_chunker, mock_embedding_model):
        """Test chunking with single sentence content."""
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = ["Single sentence content."]
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        chunking = SemanticChunking("Single sentence.", mock_embedding_model)
        
        result = chunking.get_chunks()
        
        assert len(result) == 1
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_chunker_buffer_size(self, mock_chunker, mock_embedding_model):
        """Test that chunker is initialized with correct buffer_size."""
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = []
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        SemanticChunking("Content", mock_embedding_model)
        
        call_kwargs = mock_chunker.call_args[1]
        assert call_kwargs['buffer_size'] == 1
        assert call_kwargs['add_start_index'] == False


class TestSemanticChunkingWithLargeContent:
    """Tests for SemanticChunking with larger content."""
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_large_document_chunking(self, mock_chunker, mock_embedding_model):
        """Test chunking a large document."""
        # Simulate many chunks from a large document
        expected_chunks = [f"Chunk {i}" for i in range(100)]
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = expected_chunks
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        large_content = "Sentence. " * 1000
        chunking = SemanticChunking(large_content, mock_embedding_model)
        
        result = chunking.get_chunks()
        
        assert len(result) == 100
    
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_unicode_content_chunking(self, mock_chunker, mock_embedding_model):
        """Test chunking content with unicode characters."""
        expected_chunks = [
            "日本語のテキストセグメント。",
            "English text segment.",
            "中文文本段落。"
        ]
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = expected_chunks
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        unicode_content = "日本語。English。中文。"
        chunking = SemanticChunking(unicode_content, mock_embedding_model)
        
        result = chunking.get_chunks()
        
        assert len(result) == 3
        assert "日本語" in result[0]


class TestSemanticChunkingBreakpointAmounts:
    """Tests for different breakpoint amounts."""
    
    @pytest.mark.parametrize("breakpoint_amount", [50, 75, 90, 95])
    @patch('src.rag.semantic_chunker.SemanticChunker')
    def test_various_breakpoint_amounts(self, mock_chunker, mock_embedding_model, breakpoint_amount):
        """Test chunking with various breakpoint amounts."""
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.split_text.return_value = ["Chunk"]
        mock_chunker.return_value = mock_chunker_instance
        
        from src.rag.semantic_chunker import SemanticChunking
        
        chunking = SemanticChunking(
            "Content",
            mock_embedding_model,
            breakpoint_amount=breakpoint_amount
        )
        
        call_kwargs = mock_chunker.call_args[1]
        assert call_kwargs['breakpoint_threshold_amount'] == breakpoint_amount
