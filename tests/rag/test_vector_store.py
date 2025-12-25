"""
Tests for vector_store.py - Pinecone Vector Database Operations.

This module tests:
- retrieve_namespace: Check if namespace exists
- retrieve_length_of_namespace: Get vector count in namespace
- sending_to_pinecone: Upsert vectors to Pinecone
- query_pinecone: Query vectors from Pinecone
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


class TestRetrieveNamespace:
    """Tests for the retrieve_namespace function."""
    
    @pytest.mark.asyncio
    async def test_retrieve_namespace_exists(self, mock_pinecone_stats):
        """Test retrieving an existing namespace."""
        from src.rag.vector_store import retrieve_namespace
        
        result = await retrieve_namespace(mock_pinecone_stats, "test-namespace")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_retrieve_namespace_not_exists(self, mock_pinecone_stats):
        """Test retrieving a non-existent namespace."""
        from src.rag.vector_store import retrieve_namespace
        
        result = await retrieve_namespace(mock_pinecone_stats, "non-existent-namespace")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_retrieve_namespace_empty_stats(self):
        """Test with empty stats."""
        from src.rag.vector_store import retrieve_namespace
        
        empty_stats = {'namespaces': {}}
        
        result = await retrieve_namespace(empty_stats, "any-namespace")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_retrieve_namespace_error_handling(self):
        """Test error handling with invalid stats."""
        from src.rag.vector_store import retrieve_namespace
        
        # Stats without 'namespaces' key should raise exception
        invalid_stats = {}
        
        with pytest.raises(Exception):
            await retrieve_namespace(invalid_stats, "test")


class TestRetrieveLengthOfNamespace:
    """Tests for the retrieve_length_of_namespace function."""
    
    @pytest.mark.asyncio
    async def test_retrieve_length_existing_namespace(self, mock_pinecone_stats):
        """Test retrieving vector count for existing namespace."""
        from src.rag.vector_store import retrieve_length_of_namespace
        
        result = await retrieve_length_of_namespace(mock_pinecone_stats, "test-namespace")
        
        assert result == 100
    
    @pytest.mark.asyncio
    async def test_retrieve_length_another_namespace(self, mock_pinecone_stats):
        """Test retrieving vector count for another namespace."""
        from src.rag.vector_store import retrieve_length_of_namespace
        
        result = await retrieve_length_of_namespace(mock_pinecone_stats, "existing-namespace")
        
        assert result == 50
    
    @pytest.mark.asyncio
    async def test_retrieve_length_non_existent_namespace(self, mock_pinecone_stats):
        """Test retrieving vector count for non-existent namespace returns 0."""
        from src.rag.vector_store import retrieve_length_of_namespace
        
        result = await retrieve_length_of_namespace(mock_pinecone_stats, "non-existent")
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_retrieve_length_empty_namespace(self):
        """Test with namespace that has zero vectors."""
        from src.rag.vector_store import retrieve_length_of_namespace
        
        stats = {'namespaces': {'empty-namespace': {'vector_count': 0}}}
        
        result = await retrieve_length_of_namespace(stats, "empty-namespace")
        
        assert result == 0


class TestSendingToPinecone:
    """Tests for the sending_to_pinecone function."""
    
    @pytest.mark.asyncio
    async def test_sending_to_pinecone_success(self, mock_pinecone_stats, mock_pinecone_index):
        """Test successful vector upsert."""
        from src.rag.vector_store import sending_to_pinecone
        
        vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        ids = ["0", "1"]
        metadata_list = [{"text": "chunk1"}, {"text": "chunk2"}]
        namespace = "test-namespace"
        
        result = await sending_to_pinecone(
            mock_pinecone_stats,
            mock_pinecone_index,
            vectors,
            ids,
            metadata_list,
            namespace
        )
        
        assert result is None
        mock_pinecone_index.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sending_to_pinecone_with_metadata(self, mock_pinecone_stats, mock_pinecone_index):
        """Test upsert with complex metadata."""
        from src.rag.vector_store import sending_to_pinecone
        
        vectors = [[0.1] * 768]
        ids = ["doc-001"]
        metadata_list = [{"text": "chunk content", "source": "file.pdf", "page": 1}]
        
        await sending_to_pinecone(
            mock_pinecone_stats,
            mock_pinecone_index,
            vectors,
            ids,
            metadata_list,
            "test-ns"
        )
        
        call_kwargs = mock_pinecone_index.upsert.call_args[1]
        assert call_kwargs['namespace'] == "test-ns"
        assert len(call_kwargs['vectors']) == 1
    
    @pytest.mark.asyncio
    async def test_sending_to_pinecone_multiple_vectors(self, mock_pinecone_stats, mock_pinecone_index):
        """Test upserting multiple vectors at once."""
        from src.rag.vector_store import sending_to_pinecone
        
        num_vectors = 10
        vectors = [[0.1] * 768 for _ in range(num_vectors)]
        ids = [str(i) for i in range(num_vectors)]
        metadata_list = [{"text": f"chunk {i}"} for i in range(num_vectors)]
        
        await sending_to_pinecone(
            mock_pinecone_stats,
            mock_pinecone_index,
            vectors,
            ids,
            metadata_list,
            "bulk-namespace"
        )
        
        call_kwargs = mock_pinecone_index.upsert.call_args[1]
        assert len(call_kwargs['vectors']) == num_vectors
    
    @pytest.mark.asyncio
    async def test_sending_to_pinecone_error_handling(self, mock_pinecone_stats):
        """Test error handling when Pinecone fails."""
        from src.rag.vector_store import sending_to_pinecone
        
        mock_index = MagicMock()
        mock_index.upsert.side_effect = Exception("Connection timeout")
        
        with pytest.raises(Exception) as exc_info:
            await sending_to_pinecone(
                mock_pinecone_stats,
                mock_index,
                [[0.1]],
                ["0"],
                [{"text": "test"}],
                "test-ns"
            )
        
        assert "Pinecone connection failed" in str(exc_info.value)


class TestQueryPinecone:
    """Tests for the query_pinecone function."""
    
    @pytest.mark.asyncio
    async def test_query_pinecone_success(self, mock_pinecone_stats, mock_pinecone_index, mock_embedding_model):
        """Test successful query to Pinecone."""
        from src.rag.vector_store import query_pinecone
        
        result = await query_pinecone(
            mock_pinecone_stats,
            mock_pinecone_index,
            query="What is machine learning?",
            namespace="test-namespace",
            embedding_model=mock_embedding_model,
            top_k=3
        )
        
        assert len(result) == 3
        # Results should be tuples of (text, score)
        assert all(len(r) == 2 for r in result)
    
    @pytest.mark.asyncio
    async def test_query_pinecone_top_k(self, mock_pinecone_stats, mock_embedding_model):
        """Test query with different top_k values."""
        from src.rag.vector_store import query_pinecone
        
        mock_index = MagicMock()
        mock_index.query.return_value = {
            'matches': [
                {'id': str(i), 'score': 0.9 - i*0.1, 'metadata': {'text': f'Chunk {i}'}}
                for i in range(5)
            ]
        }
        
        result = await query_pinecone(
            mock_pinecone_stats,
            mock_index,
            query="test query",
            namespace="test-ns",
            embedding_model=mock_embedding_model,
            top_k=5
        )
        
        mock_index.query.assert_called_once()
        call_kwargs = mock_index.query.call_args[1]
        assert call_kwargs['top_k'] == 5
    
    @pytest.mark.asyncio
    async def test_query_pinecone_sorts_by_id(self, mock_pinecone_stats, mock_embedding_model):
        """Test that results are sorted by ID."""
        from src.rag.vector_store import query_pinecone
        
        # Return unsorted results
        mock_index = MagicMock()
        mock_index.query.return_value = {
            'matches': [
                {'id': '2', 'score': 0.9, 'metadata': {'text': 'Chunk 2'}},
                {'id': '0', 'score': 0.8, 'metadata': {'text': 'Chunk 0'}},
                {'id': '1', 'score': 0.7, 'metadata': {'text': 'Chunk 1'}},
            ]
        }
        
        result = await query_pinecone(
            mock_pinecone_stats,
            mock_index,
            query="test",
            namespace="test-ns",
            embedding_model=mock_embedding_model,
            top_k=3
        )
        
        # Should be sorted by ID: 0, 1, 2
        assert result[0][0] == 'Chunk 0'
        assert result[1][0] == 'Chunk 1'
        assert result[2][0] == 'Chunk 2'
    
    @pytest.mark.asyncio
    async def test_query_pinecone_empty_results(self, mock_pinecone_stats, mock_embedding_model):
        """Test query with no matching results."""
        from src.rag.vector_store import query_pinecone
        
        mock_index = MagicMock()
        mock_index.query.return_value = {'matches': []}
        
        result = await query_pinecone(
            mock_pinecone_stats,
            mock_index,
            query="obscure query",
            namespace="test-ns",
            embedding_model=mock_embedding_model,
            top_k=5
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_query_pinecone_error_handling(self, mock_pinecone_stats, mock_embedding_model):
        """Test error handling when query fails."""
        from src.rag.vector_store import query_pinecone
        
        mock_index = MagicMock()
        mock_index.query.side_effect = Exception("Query timeout")
        
        with pytest.raises(Exception) as exc_info:
            await query_pinecone(
                mock_pinecone_stats,
                mock_index,
                query="test",
                namespace="test-ns",
                embedding_model=mock_embedding_model,
                top_k=5
            )
        
        assert "Pinecone connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_query_pinecone_includes_metadata(self, mock_pinecone_stats, mock_embedding_model):
        """Test that query requests metadata."""
        from src.rag.vector_store import query_pinecone
        
        mock_index = MagicMock()
        mock_index.query.return_value = {'matches': []}
        
        await query_pinecone(
            mock_pinecone_stats,
            mock_index,
            query="test",
            namespace="test-ns",
            embedding_model=mock_embedding_model,
            top_k=5
        )
        
        call_kwargs = mock_index.query.call_args[1]
        assert call_kwargs['include_metadata'] is True
        assert call_kwargs['include_values'] is False
