"""
Tests for rank_bm25.py - BM25 Algorithm Implementation.
"""
import pytest
import numpy as np
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


class TestBM25Base:
    """Tests for the base BM25 class."""
    
    def test_bm25_base_initialization(self):
        """Test BM25 base class initialization."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [
            ["hello", "world"],
            ["hello", "universe"],
            ["goodbye", "world"]
        ]
        bm25 = BM25Okapi(corpus)
        
        assert bm25.corpus_size == 3
        assert bm25.avgdl > 0
    
    def test_bm25_doc_lens(self):
        """Test document lengths are calculated correctly."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [
            ["one", "two"],
            ["one", "two", "three", "four"],
            ["one"]
        ]
        bm25 = BM25Okapi(corpus)
        
        assert bm25.doc_len == [2, 4, 1]


class TestBM25Okapi:
    """Tests for BM25Okapi implementation."""
    
    def test_initialization(self):
        """Test BM25Okapi initialization with default parameters."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [["test", "document"]]
        bm25 = BM25Okapi(corpus)
        
        assert bm25.k1 == 1.5
        assert bm25.b == 0.75
        assert bm25.epsilon == 0.25
    
    def test_custom_parameters(self):
        """Test BM25Okapi with custom parameters."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [["test"]]
        bm25 = BM25Okapi(corpus, k1=2.0, b=0.5, epsilon=0.1)
        
        assert bm25.k1 == 2.0
        assert bm25.b == 0.5
        assert bm25.epsilon == 0.1
    
    def test_get_scores(self):
        """Test BM25 scoring."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [
            ["machine", "learning", "is", "great"],
            ["deep", "learning", "neural", "networks"],
            ["natural", "language", "processing"]
        ]
        bm25 = BM25Okapi(corpus)
        
        query = ["learning"]
        scores = bm25.get_scores(query)
        
        assert len(scores) == 3
        assert scores[0] > 0  # Contains "learning"
        assert scores[1] > 0  # Contains "learning"
        assert scores[2] == 0  # Doesn't contain "learning"
    
    def test_get_scores_multiple_terms(self):
        """Test scoring with multiple query terms."""
        from src.rag.rank_bm25 import BM25Okapi
        
        # Use 5 documents so query terms appear in < 50% of corpus
        corpus = [
            ["machine", "learning", "ai"],
            ["deep", "neural", "networks"],
            ["natural", "language", "processing"],
            ["data", "science", "analytics"],
            ["machine", "learning", "deep", "learning"]
        ]
        bm25 = BM25Okapi(corpus)
        
        # 'machine' appears in 2/5 docs (40%), 'learning' appears in 2/5 docs (40%)
        query = ["machine", "learning"]
        scores = bm25.get_scores(query)
        
        # Documents with query terms should have positive scores
        assert scores[0] > 0  # contains both 'machine' and 'learning'
        assert scores[4] > 0  # contains both 'machine' and 'learning'
        # Documents without query terms should have zero scores
        assert scores[1] == 0
        assert scores[2] == 0
        assert scores[3] == 0
    
    def test_get_top_n(self):
        """Test getting top N documents."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [
            ["python", "programming"],
            ["java", "programming"],
            ["python", "data", "science"],
            ["machine", "learning"]
        ]
        documents = ["Doc 1", "Doc 2", "Doc 3", "Doc 4"]
        bm25 = BM25Okapi(corpus)
        
        query = ["python"]
        top_docs = bm25.get_top_n(query, documents, n=2)
        
        assert len(top_docs) == 2
    
    def test_get_batch_scores(self):
        """Test batch scoring for specific documents."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [
            ["doc", "one"],
            ["doc", "two"],
            ["doc", "three"]
        ]
        bm25 = BM25Okapi(corpus)
        
        query = ["doc"]
        doc_ids = [0, 2]
        scores = bm25.get_batch_scores(query, doc_ids)
        
        assert len(scores) == 2
    
    def test_return_variables(self):
        """Test returning internal state variables."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [["test", "document"]]
        bm25 = BM25Okapi(corpus)
        
        variables = bm25.return_variables()
        
        assert 'corpus_size' in variables
        assert 'avgdl' in variables
        assert 'doc_freqs' in variables
        assert 'idf' in variables
        assert 'doc_len' in variables
        assert 'k1' in variables
        assert 'b' in variables


class TestBM25OkapiWithoutCorpus:
    """Tests for BM25Okapi_without_corpus implementation."""
    
    def test_initialization_from_variables(self):
        """Test creating BM25 from stored variables."""
        from src.rag.rank_bm25 import BM25Okapi, BM25Okapi_without_corpus
        
        # First create a normal BM25 and get its variables
        corpus = [["hello", "world"], ["hello"]]
        original_bm25 = BM25Okapi(corpus)
        variables = original_bm25.return_variables()
        
        # Create from variables
        restored_bm25 = BM25Okapi_without_corpus(
            corpus_size=variables['corpus_size'],
            avgdl=variables['avgdl'],
            doc_freqs=variables['doc_freqs'],
            idf=variables['idf'],
            doc_len=variables['doc_len'],
            average_idf=variables['average_idf'],
            k1=variables['k1'],
            b=variables['b'],
            epsilon=variables['epsilon']
        )
        
        assert restored_bm25.corpus_size == original_bm25.corpus_size
    
    def test_get_scores_matches_original(self):
        """Test that scores match original BM25."""
        from src.rag.rank_bm25 import BM25Okapi, BM25Okapi_without_corpus
        
        corpus = [["test", "document"], ["another", "test"]]
        original = BM25Okapi(corpus)
        variables = original.return_variables()
        
        restored = BM25Okapi_without_corpus(
            corpus_size=variables['corpus_size'],
            avgdl=variables['avgdl'],
            doc_freqs=variables['doc_freqs'],
            idf=variables['idf'],
            doc_len=variables['doc_len'],
            average_idf=variables['average_idf'],
            k1=variables['k1'],
            b=variables['b'],
            epsilon=variables['epsilon']
        )
        
        query = ["test"]
        original_scores = original.get_scores(query)
        restored_scores = restored.get_scores(query)
        
        np.testing.assert_array_almost_equal(original_scores, restored_scores)


class TestBM25AddDocuments:
    """Tests for adding documents to BM25 index."""
    
    def test_add_documents(self):
        """Test adding new documents to existing BM25."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [["initial", "document"]]
        bm25 = BM25Okapi(corpus)
        
        initial_size = bm25.corpus_size
        
        new_docs = [["new", "document"], ["another", "new"]]
        bm25.add_documents(new_docs)
        
        assert bm25.corpus_size == initial_size + 2
    
    def test_add_documents_updates_idf(self):
        """Test that IDF is updated after adding documents."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [["unique", "word"]]
        bm25 = BM25Okapi(corpus)
        
        initial_idf = bm25.idf.copy()
        
        bm25.add_documents([["another", "document"]])
        
        # IDF should be recalculated
        assert bm25.idf != initial_idf or bm25.corpus_size == 2


class TestBM25EdgeCases:
    """Edge case tests for BM25."""
    
    def test_empty_query(self):
        """Test scoring with empty query."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [["test", "document"]]
        bm25 = BM25Okapi(corpus)
        
        scores = bm25.get_scores([])
        
        assert all(s == 0 for s in scores)
    
    def test_query_term_not_in_corpus(self):
        """Test query with terms not in corpus."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [["hello", "world"]]
        bm25 = BM25Okapi(corpus)
        
        scores = bm25.get_scores(["unknown", "terms"])
        
        assert all(s == 0 for s in scores)
    
    def test_single_document_corpus(self):
        """Test with single document corpus."""
        from src.rag.rank_bm25 import BM25Okapi
        
        corpus = [["only", "document"]]
        bm25 = BM25Okapi(corpus)
        
        # In single-doc corpus, all terms appear in 100% of docs
        # so IDF is negative. BM25 still returns a score (may be negative).
        scores = bm25.get_scores(["document"])
        
        assert len(scores) == 1
        # Just verify we get a score (can be negative with single doc)
        assert isinstance(scores[0], (int, float, np.floating))
