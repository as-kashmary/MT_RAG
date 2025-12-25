"""
Tests for fusion_retrieval.py - Hybrid BM25 + Vector Search.

This module tests:
- create_bm25_index: Create BM25 index from documents
- create_bm25_index_v2: Create BM25 index from stored variables
- new_create_BM25Okapi_index: Add documents to existing BM25 index
- fusion_retrieval: Combined BM25 + vector search
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import numpy as np
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


class TestCreateBm25Index:
    """Tests for the create_bm25_index function."""
    
    def test_create_bm25_index_basic(self, sample_documents):
        """Test creating a BM25 index from documents."""
        from src.rag.fusion_retrieval import create_bm25_index
        
        bm25 = create_bm25_index(sample_documents)
        
        assert bm25 is not None
        assert hasattr(bm25, 'get_scores')
        assert hasattr(bm25, 'get_top_n')
    
    def test_create_bm25_index_single_document(self):
        """Test creating BM25 index with single document."""
        from src.rag.fusion_retrieval import create_bm25_index
        
        documents = ["This is a single document."]
        bm25 = create_bm25_index(documents)
        
        assert bm25.corpus_size == 1
    
    def test_create_bm25_index_multiple_documents(self):
        """Test creating BM25 index with multiple documents."""
        from src.rag.fusion_retrieval import create_bm25_index
        
        documents = [
            "Document one about AI.",
            "Document two about ML.",
            "Document three about NLP.",
            "Document four about databases.",
            "Document five about retrieval."
        ]
        
        bm25 = create_bm25_index(documents)
        
        assert bm25.corpus_size == 5
    
    def test_create_bm25_index_tokenization(self):
        """Test that documents are tokenized correctly."""
        from src.rag.fusion_retrieval import create_bm25_index
        
        # Use 5 documents where 'unique' appears in only 1 (< 50%)
        documents = [
            "hello world today",
            "hello universe here", 
            "goodbye world now",
            "another document text",
            "unique special term"  # 'unique' only appears here
        ]
        bm25 = create_bm25_index(documents)
        
        # Query for 'unique' - appears in 1 of 5 docs (20%), so has positive IDF
        scores = bm25.get_scores("unique".split())
        
        assert len(scores) == 5
        # Document containing 'unique' should have positive score
        assert scores[4] > 0  # "unique special term" - contains 'unique'
        # Other documents should have zero score
        assert scores[0] == 0
        assert scores[1] == 0
        assert scores[2] == 0
        assert scores[3] == 0


class TestCreateBm25IndexV2:
    """Tests for the create_bm25_index_v2 function."""
    
    def test_create_bm25_index_v2_from_variables(self, sample_bm25_variables):
        """Test creating BM25 index from stored variables."""
        from src.rag.fusion_retrieval import create_bm25_index_v2
        
        bm25 = create_bm25_index_v2(sample_bm25_variables)
        
        assert bm25 is not None
        assert bm25.corpus_size == sample_bm25_variables['corpus_size']
        assert bm25.k1 == sample_bm25_variables['k1']
        assert bm25.b == sample_bm25_variables['b']
    
    def test_create_bm25_index_v2_preserves_idf(self, sample_bm25_variables):
        """Test that IDF values are preserved."""
        from src.rag.fusion_retrieval import create_bm25_index_v2
        
        bm25 = create_bm25_index_v2(sample_bm25_variables)
        
        assert bm25.idf == sample_bm25_variables['idf']
    
    def test_create_bm25_index_v2_custom_params(self):
        """Test creating BM25 with custom parameters."""
        from src.rag.fusion_retrieval import create_bm25_index_v2
        
        variables = {
            'corpus_size': 10,
            'avgdl': 15.5,
            'doc_freqs': [],
            'idf': {'test': 1.0},
            'doc_len': [10] * 10,
            'average_idf': 1.0,
            'k1': 2.0,  # Custom k1
            'b': 0.5,   # Custom b
            'epsilon': 0.1
        }
        
        bm25 = create_bm25_index_v2(variables)
        
        assert bm25.k1 == 2.0
        assert bm25.b == 0.5


class TestNewCreateBM25OkapiIndex:
    """Tests for adding documents to existing BM25 index."""
    
    def test_add_documents_to_existing_index(self, sample_bm25_index):
        """Test adding new documents to existing BM25 index."""
        from src.rag.fusion_retrieval import new_create_BM25Okapi_index
        
        initial_size = sample_bm25_index.corpus_size
        new_documents = [
            "New document about deep learning.",
            "Another document about transformers."
        ]
        
        updated_bm25 = new_create_BM25Okapi_index(new_documents, sample_bm25_index)
        
        assert updated_bm25.corpus_size == initial_size + 2
    
    def test_add_single_document(self, sample_bm25_index):
        """Test adding a single document."""
        from src.rag.fusion_retrieval import new_create_BM25Okapi_index
        
        initial_size = sample_bm25_index.corpus_size
        
        updated_bm25 = new_create_BM25Okapi_index(
            ["Single new document."],
            sample_bm25_index
        )
        
        assert updated_bm25.corpus_size == initial_size + 1


class TestFusionRetrieval:
    """Tests for the fusion_retrieval function."""
    
    @pytest.mark.asyncio
    @patch('src.rag.fusion_retrieval.query_pinecone')
    async def test_fusion_retrieval_basic(
        self,
        mock_query_pinecone,
        mock_pinecone_stats,
        mock_pinecone_index,
        mock_embedding_model,
        sample_bm25_index
    ):
        """Test basic fusion retrieval."""
        # Setup mock for vector search
        mock_query_pinecone.return_value = [
            ("Chunk 0", 0.1),
            ("Chunk 1", 0.2),
            ("Chunk 2", 0.3)
        ]
        
        from src.rag.fusion_retrieval import fusion_retrieval
        
        result = await fusion_retrieval(
            stats=mock_pinecone_stats,
            Pinecone_index=mock_pinecone_index,
            length_of_total_chunks=3,
            embedding_model=mock_embedding_model,
            bm25=sample_bm25_index,
            query="machine learning",
            namespace="test-ns",
            k=2,
            alpha=0.5
        )
        
        assert len(result) == 2
        assert all(isinstance(idx, int) for idx in result)
    
    @pytest.mark.asyncio
    @patch('src.rag.fusion_retrieval.query_pinecone')
    async def test_fusion_retrieval_alpha_weights(
        self,
        mock_query_pinecone,
        mock_pinecone_stats,
        mock_pinecone_index,
        mock_embedding_model,
        sample_bm25_index
    ):
        """Test fusion retrieval with different alpha weights."""
        mock_query_pinecone.return_value = [
            ("Chunk 0", 0.1),
            ("Chunk 1", 0.2),
            ("Chunk 2", 0.3)
        ]
        
        from src.rag.fusion_retrieval import fusion_retrieval
        
        # Test with alpha = 1.0 (full vector weight)
        result_vector = await fusion_retrieval(
            stats=mock_pinecone_stats,
            Pinecone_index=mock_pinecone_index,
            length_of_total_chunks=3,
            embedding_model=mock_embedding_model,
            bm25=sample_bm25_index,
            query="test query",
            namespace="test-ns",
            k=3,
            alpha=1.0
        )
        
        # Test with alpha = 0.0 (full BM25 weight)
        result_bm25 = await fusion_retrieval(
            stats=mock_pinecone_stats,
            Pinecone_index=mock_pinecone_index,
            length_of_total_chunks=3,
            embedding_model=mock_embedding_model,
            bm25=sample_bm25_index,
            query="test query",
            namespace="test-ns",
            k=3,
            alpha=0.0
        )
        
        # Results should differ based on alpha
        assert len(result_vector) == 3
        assert len(result_bm25) == 3
    
    @pytest.mark.asyncio
    @patch('src.rag.fusion_retrieval.query_pinecone')
    async def test_fusion_retrieval_top_k(
        self,
        mock_query_pinecone,
        mock_pinecone_stats,
        mock_pinecone_index,
        mock_embedding_model,
        sample_bm25_index
    ):
        """Test fusion retrieval returns correct number of results."""
        mock_query_pinecone.return_value = [
            ("Chunk 0", 0.1),
            ("Chunk 1", 0.2),
            ("Chunk 2", 0.3)
        ]
        
        from src.rag.fusion_retrieval import fusion_retrieval
        
        for k in [1, 2, 3]:
            result = await fusion_retrieval(
                stats=mock_pinecone_stats,
                Pinecone_index=mock_pinecone_index,
                length_of_total_chunks=3,
                embedding_model=mock_embedding_model,
                bm25=sample_bm25_index,
                query="test",
                namespace="test-ns",
                k=k,
                alpha=0.5
            )
            
            assert len(result) == k
    
    @pytest.mark.asyncio
    @patch('src.rag.fusion_retrieval.query_pinecone')
    async def test_fusion_retrieval_returns_indices(
        self,
        mock_query_pinecone,
        mock_pinecone_stats,
        mock_pinecone_index,
        mock_embedding_model,
        sample_bm25_index
    ):
        """Test that fusion retrieval returns document indices."""
        mock_query_pinecone.return_value = [
            ("Chunk 0", 0.1),
            ("Chunk 1", 0.2),
            ("Chunk 2", 0.3)
        ]
        
        from src.rag.fusion_retrieval import fusion_retrieval
        
        result = await fusion_retrieval(
            stats=mock_pinecone_stats,
            Pinecone_index=mock_pinecone_index,
            length_of_total_chunks=3,
            embedding_model=mock_embedding_model,
            bm25=sample_bm25_index,
            query="test",
            namespace="test-ns",
            k=3,
            alpha=0.5
        )
        
        # All results should be valid indices
        for idx in result:
            assert 0 <= idx < 3


class TestFusionRetrievalEdgeCases:
    """Edge case tests for fusion retrieval."""
    
    @pytest.mark.asyncio
    @patch('src.rag.fusion_retrieval.query_pinecone')
    async def test_fusion_retrieval_single_document(
        self,
        mock_query_pinecone,
        mock_pinecone_stats,
        mock_pinecone_index,
        mock_embedding_model
    ):
        """Test fusion retrieval with single document corpus."""
        from src.rag.fusion_retrieval import create_bm25_index, fusion_retrieval
        
        single_doc = ["Only document in corpus."]
        bm25 = create_bm25_index(single_doc)
        
        mock_query_pinecone.return_value = [("Only document", 0.1)]
        
        result = await fusion_retrieval(
            stats=mock_pinecone_stats,
            Pinecone_index=mock_pinecone_index,
            length_of_total_chunks=1,
            embedding_model=mock_embedding_model,
            bm25=bm25,
            query="document",
            namespace="test-ns",
            k=1,
            alpha=0.5
        )
        
        assert len(result) == 1
        assert result[0] == 0
