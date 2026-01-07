"""
Shared fixtures and configuration for RAG module tests.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


# ============================================================================
# Mock Embedding Model Fixtures
# ============================================================================

@pytest.fixture
def mock_embedding_model():
    """Mock embedding model that returns deterministic embeddings."""
    mock = MagicMock()
    # Return 768-dimensional embeddings (common for models like multilingual-e5)
    mock.embed_documents.return_value = [
        [0.1] * 768,
        [0.2] * 768,
        [0.3] * 768
    ]
    mock.embed_query.return_value = [0.15] * 768
    return mock


@pytest.fixture
def mock_hf_embeddings():
    """Mock HuggingFace embeddings for local embedder tests."""
    mock = MagicMock()
    mock.embed_documents.return_value = [[0.1, 0.2, 0.3] * 256]
    mock.embed_query.return_value = [0.1, 0.2, 0.3] * 256
    return mock


# ============================================================================
# Mock External Services Fixtures
# ============================================================================

@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index for vector store tests."""
    mock = MagicMock()
    mock.upsert = MagicMock(return_value=None)
    mock.query = MagicMock(return_value={
        'matches': [
            {'id': '0', 'score': 0.95, 'metadata': {'text': 'Chunk 0 content'}},
            {'id': '1', 'score': 0.90, 'metadata': {'text': 'Chunk 1 content'}},
            {'id': '2', 'score': 0.85, 'metadata': {'text': 'Chunk 2 content'}},
        ]
    })
    return mock


@pytest.fixture
def mock_pinecone_stats():
    """Mock Pinecone stats for namespace checks."""
    return {
        'namespaces': {
            'test-namespace': {'vector_count': 100},
            'existing-namespace': {'vector_count': 50}
        }
    }


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for query classification and response generation."""
    mock = MagicMock()
    
    def mock_chat(*args, **kwargs):
        # Simulate streaming response
        yield {'message': {'content': 'Factual'}}
    
    mock.chat = mock_chat
    return mock


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        "This is the first document about machine learning.",
        "The second document discusses natural language processing.",
        "A third document covers vector databases and embeddings."
    ]


@pytest.fixture
def sample_text_content():
    """Sample text content for document processing tests."""
    return """
    This is a sample document content for testing purposes.
    It contains multiple sentences and paragraphs.
    
    The document discusses various topics including:
    - Machine learning algorithms
    - Natural language processing
    - Information retrieval systems
    
    This content is used to test semantic chunking and embedding.
    """


@pytest.fixture
def sample_pdf_content():
    """Sample PDF-like content for testing."""
    return "Page 1 content.\nPage 2 content.\nPage 3 content."


@pytest.fixture
def sample_bm25_variables():
    """Sample BM25 model variables for testing."""
    return {
        'corpus_size': 3,
        'avgdl': 10.0,
        'doc_freqs': [{'word1': 1}, {'word2': 1}, {'word3': 1}],
        'idf': {'word1': 0.5, 'word2': 0.6, 'word3': 0.7},
        'doc_len': [10, 10, 10],
        'average_idf': 0.6,
        'k1': 1.5,
        'b': 0.75,
        'epsilon': 0.25
    }


@pytest.fixture
def sample_chunks():
    """Sample text chunks for fusion retrieval tests."""
    return [
        "Machine learning is a subset of artificial intelligence.",
        "Neural networks are inspired by biological neurons.",
        "Deep learning uses multiple layers of neural networks.",
        "Natural language processing deals with text and speech.",
        "Vector databases store high-dimensional embeddings."
    ]


# ============================================================================
# BM25 Index Fixtures
# ============================================================================

@pytest.fixture
def sample_bm25_index(sample_documents):
    """Create a sample BM25 index for testing."""
    from src.rag.rank_bm25 import BM25Okapi
    tokenized_docs = [doc.split() for doc in sample_documents]
    return BM25Okapi(tokenized_docs)


# ============================================================================
# Temporary File Fixtures
# ============================================================================

@pytest.fixture
def temp_txt_file(tmp_path):
    """Create a temporary text file for testing."""
    txt_file = tmp_path / "test_document.txt"
    txt_file.write_text("This is test content for the text file.\nSecond line of content.", encoding='utf-8')
    return str(txt_file)


@pytest.fixture
def temp_pdf_file(tmp_path):
    """Create a temporary PDF file path (actual PDF creation requires external libs)."""
    pdf_file = tmp_path / "test_document.pdf"
    # Note: Actual PDF creation would require pypdf or similar
    return str(pdf_file)


@pytest.fixture
def temp_docx_file(tmp_path):
    """Create a temporary DOCX file path (actual DOCX creation requires python-docx)."""
    docx_file = tmp_path / "test_document.docx"
    return str(docx_file)


# ============================================================================
# Logger Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_logger():
    """Mock logger for testing log outputs."""
    mock = MagicMock()
    mock.info = MagicMock()
    mock.error = MagicMock()
    mock.warning = MagicMock()
    mock.debug = MagicMock()
    return mock


# ============================================================================
# Async Test Configuration
# ============================================================================

@pytest.fixture
def event_loop_policy():
    """Configure event loop for async tests."""
    import asyncio
    return asyncio.get_event_loop_policy()
