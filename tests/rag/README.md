# RAG Module Tests 🧪

This directory contains comprehensive pytest test suites for all RAG (Retrieval-Augmented Generation) module components.

## 📁 Test Files Overview

| Test File | Source File | Description |
|-----------|-------------|-------------|
| `test_document_loader.py` | `document_loader.py` | Tests for PDF, TXT, DOCX file reading |
| `test_embeder.py` | `embeder.py` | Tests for HuggingFace Inference API embeddings |
| `test_local_embeder.py` | `local_embeder.py` | Tests for local HuggingFace embeddings |
| `test_semantic_chunker.py` | `semantic_chunker.py` | Tests for semantic document chunking |
| `test_vector_store.py` | `vector_store.py` | Tests for Pinecone vector operations |
| `test_fusion_retrieval.py` | `fusion_retrieval.py` | Tests for BM25 + vector hybrid search |
| `test_query_classifier.py` | `query_classifier.py` | Tests for query categorization |
| `test_response_generation.py` | `response_generation.py` | Tests for LLM response generation |
| `test_rank_bm25.py` | `rank_bm25.py` | Tests for BM25 algorithm |
| `test_main.py` | `main.py` | Tests for RAG pipeline entry point |
| `conftest.py` | - | Shared fixtures and mock objects |

---

## 🚀 How to Run Tests

### Prerequisites

```bash
# Navigate to project root
cd d:\Dotlines\MT_RAG

# Activate virtual environment
myenv\Scripts\activate  # Windows
# source myenv/bin/activate  # Linux/Mac

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov
```

### Run All RAG Tests

```bash
# Run all tests in the rag directory
pytest tests/rag/ -v

# Run with verbose output
pytest tests/rag/ -v --tb=short
```

### Run Individual Test Files

```bash
# Document Loader tests
pytest tests/rag/test_document_loader.py -v

# Embeddings tests
pytest tests/rag/test_embeder.py -v
pytest tests/rag/test_local_embeder.py -v

# Semantic Chunker tests
pytest tests/rag/test_semantic_chunker.py -v

# Vector Store tests
pytest tests/rag/test_vector_store.py -v

# Fusion Retrieval tests
pytest tests/rag/test_fusion_retrieval.py -v

# Query Classifier tests
pytest tests/rag/test_query_classifier.py -v

# Response Generation tests
pytest tests/rag/test_response_generation.py -v

# BM25 Algorithm tests
pytest tests/rag/test_rank_bm25.py -v

# Main Pipeline tests
pytest tests/rag/test_main.py -v
```

### Run Specific Test Class or Method

```bash
# Run a specific test class
pytest tests/rag/test_document_loader.py::TestReadPdfToString -v

# Run a specific test method
pytest tests/rag/test_document_loader.py::TestReadPdfToString::test_read_pdf_to_string_success -v
```

### Run with Coverage Report

```bash
# Generate coverage report
pytest tests/rag/ --cov=src/rag --cov-report=html

# View coverage report - open htmlcov/index.html in browser
```

### Run Only Async Tests

```bash
pytest tests/rag/ -v -m asyncio
```

---

## 📋 Test Categories

### Unit Tests
- `test_document_loader.py` - File reading functions
- `test_embeder.py` - Embedding methods
- `test_local_embeder.py` - Local embedding with lazy loading
- `test_semantic_chunker.py` - Chunking algorithms
- `test_rank_bm25.py` - BM25 scoring algorithm

### Integration Tests
- `test_vector_store.py` - Pinecone operations (mocked)
- `test_fusion_retrieval.py` - Hybrid search pipeline
- `test_query_classifier.py` - LLM classification (mocked)
- `test_response_generation.py` - LLM generation (mocked)

---

## 🔧 Shared Fixtures (conftest.py)

Available fixtures for all tests:

```python
# Mock embedding model
@pytest.fixture
def mock_embedding_model():
    """Returns mock with embed_documents() and embed_query() methods"""

# Mock Pinecone index
@pytest.fixture
def mock_pinecone_index():
    """Returns mock Pinecone index with upsert() and query() methods"""

# Mock Pinecone stats
@pytest.fixture
def mock_pinecone_stats():
    """Returns mock namespace statistics"""

# Sample documents
@pytest.fixture
def sample_documents():
    """Returns list of sample document strings"""

# Sample BM25 index
@pytest.fixture
def sample_bm25_index():
    """Returns pre-built BM25Okapi index"""

# Temporary text file
@pytest.fixture
def temp_txt_file(tmp_path):
    """Creates a temporary .txt file for testing"""
```

---

## 📝 Writing New Tests

### Example Test Structure

```python
import pytest
from unittest.mock import MagicMock, patch

class TestMyFeature:
    """Tests for my_feature function."""
    
    def test_basic_functionality(self):
        """Test basic case."""
        from src.rag.my_module import my_function
        
        result = my_function("input")
        assert result == "expected_output"
    
    @patch('src.rag.my_module.external_dependency')
    def test_with_mock(self, mock_dep):
        """Test with mocked dependency."""
        mock_dep.return_value = "mocked_value"
        
        from src.rag.my_module import my_function
        result = my_function("input")
        
        assert result == "expected_output"
        mock_dep.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async function."""
        from src.rag.my_module import async_function
        
        result = await async_function("input")
        assert result is not None
```

---

## ⚠️ Common Issues

### Import Errors
```bash
# Make sure you're in project root and venv is activated
cd d:\Dotlines\MT_RAG
myenv\Scripts\activate
```

### Async Test Issues
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio
```

### Module Not Found
```bash
# Run tests from project root directory
pytest tests/rag/ -v
```

---

## 📊 Expected Output

```
======================== test session starts ========================
platform win32 -- Python 3.x.x, pytest-8.x.x
collected XX items

tests/rag/test_document_loader.py::TestDetermineEncoding::test_determine_encoding_utf8 PASSED
tests/rag/test_document_loader.py::TestReadTxtToString::test_read_txt_to_string_success PASSED
tests/rag/test_embeder.py::TestHFInferenceEmbeddings::test_initialization PASSED
...

======================== XX passed in X.XXs ========================
```
